#!/usr/bin/env python3
"""snake_pass.py — snake under the CERTIFIED driver (cabinet/snake @ 149d0d0), as declared CPU blocks.

WHY THIS IS A SEPARATE PASS AND NOT A GPU BLOCK
  The trunk's snake_run.py (44256 B, a4fc47ce...) is a DIVERGENT sitting-2 revision: it accepts
  --ngl/--ctx/--parallel and does not write score.revisits. The CERTIFIED driver is
  cabinet/snake/snake_run.py (42349 B, commit 149d0d0): it hardcodes `-c 65536 -ngl 0` in
  server_argv() -- CPU-only, by construction -- and writes score.revisits.
  So the cabinet the card gates on CANNOT be run on the GPU under the standing tenancy without
  editing another cabinet's certified instrument, which is not this card's to authorise.
  It is run here as what it is: CPU compute path, the driver's own registered launch, one entrant
  resident at a time, and the card sampled before/after to show the GPU did not move.

Existing episode records at a coordinate are copied aside with their digest before replacement.
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = "/home/chilly1/workspace/ocho_arena"
CAB = "/home/chilly1/workspace/ocho_arena_cabinets/snake"
DRIVER = os.path.join(CAB, "snake_run.py")
PROBES = os.path.join(CAB, "probes")
MODELS = "/home/chilly1/moltbook_pipeline/models"
PRISMML = "/home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server"
OUT = os.path.join(ROOT, "suite3", "runs")
LOGS = os.path.join(ROOT, "suite3", "logs")
PRES = os.path.join(ROOT, "suite3", "preserved")
WINDOW = "t_925f606f"
PORT = 58714
SEEDS = "1,7"
TICKS = 120
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


def gpu():
    try:
        return int(subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                  capture_output=True, text=True).stdout.strip().splitlines()[0])
    except Exception:  # noqa: BLE001
        return None


def health():
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
    a = ap.parse_args()
    ents = list(ENTRANTS) if a.entrant == "all" else a.entrant.split(",")
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(LOGS, exist_ok=True)
    for ent in ents:
        fn, binary = ENTRANTS[ent]
        label = fn.replace(".gguf", "")
        arts = [os.path.join(PROBES, f"SNAKE_{label}_s{s}.json") for s in SEEDS.split(",")]
        pres = []
        for art in arts:
            if os.path.exists(art):
                d = os.path.join(PRES, time.strftime("%Y%m%d-%H%M%S"))
                os.makedirs(d, exist_ok=True)
                import shutil
                dest = os.path.join(d, os.path.basename(art))
                shutil.copy2(art, dest)
                pres.append({"original": art, "preserved_at": dest, "sha256": sha(art),
                             "bytes": os.path.getsize(art), "preserved": now()})
                json.dump(pres[-1], open(dest + ".provenance.json", "w"), indent=1)
        cmd = [sys.executable, DRIVER, "--entrant", os.path.join(MODELS, fn),
               "--seeds", SEEDS, "--ticks", str(TICKS), "--port", str(PORT)]
        if binary:
            cmd += ["--llama-server", binary]
        if pres:
            cmd += ["--overwrite-artifact",
                    f"window {WINDOW}: re-measuring this coordinate under the CERTIFIED driver "
                    f"(cabinet/snake @ 149d0d0). The pre-existing episode(s) " +
                    ", ".join(f"sha256 {p['sha256'][:16]}..." for p in pres) +
                    " are preserved under suite3/preserved/ and are reported beside this row."]
        stamp = time.strftime("%Y%m%d-%H%M%S")
        logf = os.path.join(LOGS, f"snake_certified_{ent}_{stamp}.log")
        base, hb = gpu(), health()
        t0 = time.time()
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=5400)
        wall = round(time.time() - t0, 1)
        open(logf, "w").write(p.stdout + "\n--- stderr ---\n" + (p.stderr or ""))
        rec = {"window": WINDOW, "cabinet": "snake", "entrant": ent, "level": None,
               "block_started": now(), "shape": "cpu-only (certified driver: -c 65536 -ngl 0)",
               "lease_held": False, "gpu_baseline_mib": base, "resident_health_before": hb,
               "driver_path": DRIVER, "driver_sha256": sha(DRIVER),
               "preserved_preexisting": pres, "driver_cmd": cmd,
               "driver": {"exit": p.returncode, "wall_secs": wall, "log": logf,
                          "stdout_tail": p.stdout[-3000:], "stderr_tail": (p.stderr or "")[-1500:]},
               "artifacts": [], "artifact": None}
        for art in arts:
            e = {"path": art, "exists": os.path.exists(art)}
            if e["exists"]:
                e["sha256"] = sha(art)
                e["mtime_epoch"] = os.path.getmtime(art)
                e["written_in_block"] = os.path.getmtime(art) >= t0 - 2
            rec["artifacts"].append(e)
        rec["artifact_exists"] = all(x["exists"] and x.get("written_in_block") for x in rec["artifacts"])
        rec["artifact_set"] = arts
        rec["gpu_after_mib"] = gpu()
        rec["resident_health_after"] = health()
        rec["block_finished"] = now()
        # release evidence: the port must be closed and the card back to the baseline it started at
        rec["release"] = {"port_closed": subprocess.run(
            ["bash", "-c", f"ss -ltn | grep -q ':{PORT} '"], capture_output=True).returncode != 0,
            "vram_mib_after": rec["gpu_after_mib"], "vram_baseline_mib": base,
            "vram_back_to_baseline": (base is not None and rec["gpu_after_mib"] is not None
                                      and abs(rec["gpu_after_mib"] - base) <= 64),
            "resident_health_after": rec["resident_health_after"]}
        meta = os.path.join(OUT, f"snake_{ent}_cell_{stamp}.meta.json")
        json.dump(rec, open(meta, "w"), indent=1)
        print(json.dumps({"entrant": ent, "exit": p.returncode, "wall_s": wall,
                          "artifacts": rec["artifact_exists"], "gpu": [base, rec["gpu_after_mib"]],
                          "release": rec["release"], "meta": meta}))


if __name__ == "__main__":
    main()
