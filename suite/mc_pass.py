#!/usr/bin/env python3
"""mc_pass.py — the missile-command cells for card t_925f606f, run as DECLARED CPU blocks.

Why a separate pass rather than a block inside the GPU window: `missile_command_run.py` starts its
own server with `-ngl 0` BY CONSTRUCTION (the cabinet's frozen compute path, measured at
missile_command_run.py:340-420), so putting it inside the lease would have been a CPU load wearing a
GPU row's clothes. It is recorded here as what it is: compute path CPU, no lease held, :58595 never
touched, and the card sampled before/after each cell to show the GPU did not move.

Existing records at a cell are copied aside with their digest before the driver replaces them.

Usage: python3 suite/mc_pass.py --entrant all --state all
"""
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

MC = "/home/chilly1/workspace/ocho_arena_cabinets/missile-command"
MODELS = "/home/chilly1/moltbook_pipeline/models"
PRISMML = "/home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server"
OUT = "/home/chilly1/workspace/ocho_arena/suite3/runs"
LOGS = "/home/chilly1/workspace/ocho_arena/suite3/logs"
PRES = "/home/chilly1/workspace/ocho_arena/suite3/preserved"
WINDOW = "t_925f606f"
PORT = 58712
STATES = ["levels/mc_01_one_shot.txt", "levels/mc_02_scarcity.txt"]
ENTRANTS = {
    "ministral-3b": ("Ministral-3-3B-Instruct-2512-UD-Q4_K_XL.gguf", None),
    "ornith-9b": ("Ornith-1.5-9B-Q4_K_M.gguf", None),
    "mimo-9b": ("MiMo-V2.6-Distill-Qwen-9B-Q4_K_M.gguf", None),
    "bonsai-9b": ("Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0.gguf", PRISMML),
}


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def gpu_used():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True).stdout.strip().splitlines()
        return int(out[0])
    except Exception:  # noqa: BLE001
        return None


def resident_health():
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:58595/health", timeout=5) as r:
            return r.status
    except Exception as e:  # noqa: BLE001
        return f"error:{e}"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrant", default="all")
    ap.add_argument("--state", default="all")
    a = ap.parse_args()
    ents = list(ENTRANTS) if a.entrant == "all" else a.entrant.split(",")
    states = STATES if a.state == "all" else a.state.split(",")
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(LOGS, exist_ok=True)
    for ent in ents:
        fn, binary = ENTRANTS[ent]
        label = fn.replace(".gguf", "")
        for st in states:
            stem = os.path.splitext(os.path.basename(st))[0]
            art = os.path.join(MC, "probes", f"MC_{label}_{stem}.json")
            pres = None
            if os.path.exists(art):
                d = os.path.join(PRES, time.strftime("%Y%m%d-%H%M%S"))
                os.makedirs(d, exist_ok=True)
                dest = os.path.join(d, os.path.basename(art))
                shutil.copy2(art, dest)
                pres = {"original": art, "preserved_at": dest, "sha256": sha(art),
                        "bytes": os.path.getsize(art), "preserved": now()}
                json.dump(pres, open(dest + ".provenance.json", "w"), indent=1)
            cmd = [sys.executable, os.path.join(MC, "missile_command_run.py"),
                   "--entrant", os.path.join(MODELS, fn), "--state", st, "--port", str(PORT)]
            if binary:
                cmd += ["--llama-server", binary]
            if pres:
                cmd += ["--overwrite-artifact",
                        f"GPU/CPU window {WINDOW}: re-measuring this cell under the checker certified "
                        f"2026-10-26. The pre-existing record (sha256 {pres['sha256'][:16]}...) is "
                        f"preserved at {pres['preserved_at']} and is reported BESIDE this row."]
            stamp = time.strftime("%Y%m%d-%H%M%S")
            logf = os.path.join(LOGS, f"mc_{ent}_{stem}_{stamp}.log")
            base, health_before = gpu_used(), resident_health()
            t0 = time.time()
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            wall = round(time.time() - t0, 1)
            open(logf, "w").write(p.stdout + "\n--- stderr ---\n" + (p.stderr or ""))
            rec = {"window": WINDOW, "cabinet": "missile-command", "entrant": ent,
                   "level": f"levels/{os.path.basename(st)}", "block_started": now(),
                   "shape": "cpu-only (the cabinet's frozen compute path, -ngl 0)",
                   "lease_held": False, "gpu_baseline_mib": base,
                   "resident_health_before": health_before,
                   "preserved_preexisting": pres, "driver_cmd": cmd,
                   "driver": {"exit": p.returncode, "wall_secs": wall, "log": logf,
                              "stdout_tail": p.stdout[-3000:], "stderr_tail": (p.stderr or "")[-1500:]},
                   "artifact": art, "artifact_exists": os.path.exists(art)}
            if rec["artifact_exists"]:
                rec["artifact_sha256"] = sha(art)
                rec["artifact_written_in_block"] = os.path.getmtime(art) >= t0 - 2
                dd = json.load(open(art))
                cfg = dd.get("config") or {}
                rec["compute_path"] = {"ngl": cfg.get("n_gpu_layers"),
                                       "server_argv": cfg.get("server_argv"),
                                       "ctx": cfg.get("ctx"),
                                       "reading": "read from the artifact's own config block"}
            rec["gpu_after_mib"] = gpu_used()
            rec["resident_health_after"] = resident_health()
            rec["block_finished"] = now()
            meta = os.path.join(OUT, f"missile-command_{ent}_{stem}_{stamp}.meta.json")
            json.dump(rec, open(meta, "w"), indent=1)
            print(json.dumps({"entrant": ent, "state": stem, "exit": p.returncode, "wall_s": wall,
                              "artifact": os.path.exists(art), "gpu": [base, rec["gpu_after_mib"]],
                              "health": [health_before, rec["resident_health_after"]]}))


if __name__ == "__main__":
    main()
