#!/usr/bin/env python3
"""suite2.py — the second sitting of the multi-model window (kanban t_234b2387).

Five cabinets the first sitting did not run: Sokoban, Zork, Snake, Labyrinth, Chess. Same four
entrants, same tenancy rules, same instrument lessons. Built to
`SUITE_PREREG_EXTENSION_t_234b2387.md`, committed before the first model call of this sitting.

TWO SHAPES OF CABINET, DIFFERENT FOR A REAL REASON

  * DRIVER-OWNED (Sokoban, Zork, Snake, Chess): the registered driver launches its own `llama-server`
    and owns that process's lifetime. This wrapper cannot start the server for it. So the wrapper:
    samples the card and `/health` at the block's start, runs the driver with `--port 58701 --ngl 99`
    (the amendment registered in the extension), WATCHES the port while the driver runs — reading
    `/props` and the serving pid from the live process, not from the flag — then verifies the release
    (port refuses, card back to the sampled baseline) after the driver exits.
  * SUITE-SERVED (Labyrinth): the instrument already takes `--base-url`, so the suite serves the
    entrant exactly as it did for Mastermind and Lights Out in sitting 1.

WHAT EVERY ROW CARRIES, read rather than inferred: compute path (`-ngl`, ctx, binary path and build
line, `/props` ftype/alias/ctx/slots), serving-process identity (pid, start epoch from
`/proc/<pid>/stat` field 22 + `btime`, binary and weights size/mtime), the artifact the cabinet
wrote with its sha256, the VRAM samples, and the release evidence.

A PUBLISHED CPU ARTIFACT IS NEVER DESTROYED. Where a cell already holds one, its bytes are copied to
`suite/runs/published_cpu/` (sha256 recorded) before the GPU row is written, and the driver's own
`--overwrite-artifact` gate is given that reason verbatim.

Usage:
  python3 suite/suite2.py --entrant ministral-3b --cabinet sokoban
  python3 suite/suite2.py --entrant bonsai-9b --cabinet all
  python3 suite/suite2.py --aggregate
"""
import argparse
import glob
import hashlib
import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request

ROOT = "/home/chilly1/workspace/ocho_arena"
MODELS = "/home/chilly1/moltbook_pipeline/models"
PRISMML = "/home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server"
LLAMACPP = "/home/chilly1/llama.cpp/build/bin/llama-server"
PORT = 58701
BASE = f"http://127.0.0.1:{PORT}"
GRAPH = "/home/chilly1/workspace/chair-link/artifacts/ged_matrix.json"
CELL_SPEC = os.path.join(ROOT, "CELL_01_labyrinth.md")
OUT = os.path.join(ROOT, "suite2", "runs")
LOGS = os.path.join(ROOT, "suite2", "logs")
PUB_CPU = os.path.join(OUT, "published_cpu")

ENTRANTS = {
    "ministral-3b": {"file": "Ministral-3-3B-Instruct-2512-UD-Q4_K_XL.gguf", "binary": LLAMACPP},
    "ornith-9b": {"file": "Ornith-1.5-9B-Q4_K_M.gguf", "binary": LLAMACPP},
    "mimo-9b": {"file": "MiMo-V2.6-Distill-Qwen-9B-Q4_K_M.gguf", "binary": LLAMACPP},
    "bonsai-9b": {"file": "Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0.gguf", "binary": PRISMML},
}
ORDER = ["ministral-3b", "ornith-9b", "mimo-9b", "bonsai-9b"]
CABINETS = ["sokoban", "zork", "snake", "labyrinth", "chess"]
DRIVER = {
    "sokoban": os.path.join(ROOT, "sokoban_run.py"),
    "zork": os.path.join(ROOT, "zork_run.py"),
    "snake": os.path.join(ROOT, "snake_run.py"),
    "labyrinth": os.path.join(ROOT, "labyrinth_run.py"),
    "chess": os.path.join(ROOT, "chess_game.py"),
}
SOKOBAN_LEVELS = ["levels/01_one_push.txt", "levels/02_two_boxes.txt", "levels/03_the_corner_waiting.txt"]
ZORK_LEVELS = ["levels/zork_01_the_floor.txt", "levels/zork_02_long_crawl.txt"]
SNAKE_SEEDS = "1,7"
SNAKE_TICKS = 120
CHESS_CAP = 30
LABYRINTH_CAP = 40


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sd = load(os.path.join(ROOT, "suite", "suite.py"), "suite_driver")   # reuse, never fork


# ── process / card probes ────────────────────────────────────────────────────
def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def resident_health():
    return sd.resident_health()


def port_open(port=PORT):
    return sd.port_open(port)


def gpu_used():
    return sd.gpu_used_mib()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_server_pid(port=PORT):
    """The pid that owns the listening socket, read from /proc — not from the driver's stdout."""
    inodes = set()
    for table in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            for line in open(table).read().splitlines()[1:]:
                f = line.split()
                if len(f) < 10 or f[3] != "0A":          # 0A = LISTEN
                    continue
                if int(f[1].split(":")[1], 16) == port:
                    inodes.add(f[9])
        except OSError:
            pass
    if not inodes:
        return None
    for pid in [d for d in os.listdir("/proc") if d.isdigit()]:
        try:
            for fd in os.listdir(f"/proc/{pid}/fd"):
                tgt = os.readlink(f"/proc/{pid}/fd/{fd}")
                if tgt.startswith("socket:[") and tgt[8:-1] in inodes:
                    return int(pid)
        except (OSError, PermissionError):
            continue
    return None


def proc_identity(pid, weights):
    """Serving-process identity: start time from /proc, binary and weights from stat()."""
    ident = {"pid": pid}
    try:
        stat = open(f"/proc/{pid}/stat").read()
        after = stat.rsplit(")", 1)[1].split()
        ticks = int(after[19])
        btime = None
        for line in open("/proc/stat"):
            if line.startswith("btime "):
                btime = int(line.split()[1])
                break
        hz = os.sysconf("SC_CLK_TCK")
        start = btime + ticks / hz
        ident.update({"start_epoch": round(start, 2),
                      "start_time": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(start)),
                      "boot_id": open("/proc/sys/kernel/random/boot_id").read().strip()})
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            ident["cmdline"] = [x.decode() for x in f.read().split(b"\0") if x]
    except Exception as e:  # noqa: BLE001
        ident["error"] = repr(e)
    for label, path in (("binary", ident.get("cmdline", [None])[0]), ("weights", weights)):
        if not path:
            continue
        try:
            st = os.stat(path)
            ident[f"{label}_path"] = path
            ident[f"{label}_size"] = st.st_size
            ident[f"{label}_mtime"] = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(st.st_mtime))
        except OSError as e:
            ident[f"{label}_error"] = repr(e)
    return ident


def get_props(timeout=10):
    try:
        with urllib.request.urlopen(f"{BASE}/props", timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:  # noqa: BLE001
        return None


class Watcher(threading.Thread):
    """Samples the card and, once the driver's server is up, the serving pid and its /props."""

    def __init__(self):
        super().__init__(daemon=True)
        self.stop_flag = False
        self.samples = []
        self.pid = None
        self.props = None
        self.props_at = None

    def run(self):
        while not self.stop_flag:
            s = {"t": round(time.time(), 2)}
            try:
                s["card_mib"] = gpu_used()
            except Exception:  # noqa: BLE001
                s["card_mib"] = None
            if self.pid is None:
                self.pid = find_server_pid()
                if self.pid is not None:
                    s["server_pid"] = self.pid
            if self.pid is not None:
                try:
                    s["pid_mib"] = sd.gpu_pid_mib(self.pid)
                except Exception:  # noqa: BLE001
                    s["pid_mib"] = None
                if self.props is None and port_open():
                    p = get_props()
                    if p:
                        self.props = p
                        self.props_at = now()
            self.samples.append(s)
            time.sleep(2)

    def finish(self):
        self.stop_flag = True
        self.join(timeout=10)
        cards = [x["card_mib"] for x in self.samples if x.get("card_mib") is not None]
        pids = [x["pid_mib"] for x in self.samples if x.get("pid_mib") is not None]
        return {"samples": len(self.samples),
                "card_max_mib": max(cards) if cards else None,
                "card_min_mib": min(cards) if cards else None,
                "pid_max_mib": max(pids) if pids else None,
                "server_pid": self.pid,
                "props_at": self.props_at,
                "props": self.props}


# ── release, per load (V4) ───────────────────────────────────────────────────
def verify_release(baseline_mib, pid=None, tol=64, wait_s=90):
    port_closed = False
    t0 = time.time()
    while time.time() - t0 < wait_s:
        if not port_open():
            port_closed = True
            break
        time.sleep(0.5)
    vram = None
    t0 = time.time()
    while time.time() - t0 < wait_s:
        vram = gpu_used()
        if abs(vram - baseline_mib) <= tol:
            break
        time.sleep(1.5)
    leftover = find_server_pid()
    return {"port_closed": port_closed, "vram_mib_after": vram, "vram_baseline_mib": baseline_mib,
            "vram_delta_mib": None if vram is None else vram - baseline_mib, "tolerance_mib": tol,
            "vram_back_to_baseline": vram is not None and abs(vram - baseline_mib) <= tol,
            "listener_after": leftover,
            "pid_vram_after": sd.gpu_pid_mib(pid) if pid else 0,
            "resident_health_after": resident_health()}


# ── published-CPU preservation ───────────────────────────────────────────────
def preserve(path, reason_note):
    """Copy a published artifact aside before a GPU row is written at its cell. Bytes, not prose."""
    os.makedirs(PUB_CPU, exist_ok=True)
    dest = os.path.join(PUB_CPU, os.path.basename(path))
    shutil.copy2(path, dest)
    rec = {"original": path, "preserved_at": dest, "sha256": sha256_file(path),
           "bytes": os.path.getsize(path), "preserved": now(), "why": reason_note}
    with open(dest + ".provenance.json", "w") as f:
        json.dump(rec, f, indent=1)
    return rec


def artifact_candidates(cabinet, entrant):
    """The coordinate the driver will write to, worked out from the driver's OWN naming helpers."""
    label = entrant
    if cabinet == "sokoban":
        out = []
        for lv in SOKOBAN_LEVELS:
            name = os.path.splitext(os.path.basename(lv))[0]
            out.append(os.path.join(ROOT, "probes", f"SOKOBAN_{label}_{name}.json"))
        return out
    if cabinet == "zork":
        return [os.path.join(ROOT, "probes", f"ZORK_{label}_{os.path.splitext(os.path.basename(lv))[0]}.json")
                for lv in ZORK_LEVELS]
    return []


def driver_cmd(cabinet, entrant, level=None, extra=()):
    p = os.path.join(MODELS, ENTRANTS[entrant]["file"])
    py = sys.executable
    if cabinet == "sokoban":
        cmd = [py, DRIVER["sokoban"], "--entrant", p, "--level", level, "--cap", "40",
               "--port", str(PORT), "--ngl", "99"]
        if entrant == "bonsai-9b":
            cmd += ["--llama-server", PRISMML]
        return cmd
    if cabinet == "zork":
        cmd = [py, DRIVER["zork"], "--entrant", p, "--level", level, "--cap", "20",
               "--port", str(PORT), "--ngl", "99"]
        if entrant == "bonsai-9b":
            cmd += ["--llama-server", PRISMML]
        return cmd
    if cabinet == "snake":
        cmd = [py, DRIVER["snake"], "--entrant", p, "--seeds", SNAKE_SEEDS, "--ticks", str(SNAKE_TICKS),
               "--port", str(PORT), "--ngl", "99", "--ctx", "8192"]
        if entrant != "bonsai-9b":       # the fork is this driver's registered default binary
            cmd += ["--llama-server", LLAMACPP]
        return cmd
    if cabinet == "chess":
        cmd = [py, DRIVER["chess"], "--entrant", p, "--label", f"{entrant}-suite2",
               "--cap", str(CHESS_CAP), "--port", str(PORT), "--ngl", "99"]
        if entrant == "bonsai-9b":
            cmd += ["--llama-server", PRISMML]
        return cmd
    raise SystemExit(f"no driver for {cabinet}")


ART_RE = {"sokoban": re.compile(r"^\s*artifact\s+(\S+)", re.M),
          "zork": re.compile(r"^\s*artifact\s+(\S+)", re.M),
          "snake": re.compile(r"^\s*run\s+(\S+\.json)", re.M),
          "chess": re.compile(r"^\s*artifact:\s*(\S+)", re.M)}


def run_driver_block(entrant, cabinet, level, baseline, extra_note=None):
    """One driver-owned block: baseline -> driver(with its own server) -> release verified."""
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(LOGS, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    ensure = []
    rec = {"entrant": entrant, "cabinet": cabinet, "level": level, "block_started": now(),
           "baseline_mib_at_start": baseline, "resident_health_before": resident_health(),
           "shape": "driver-owned"}
    # PRESERVE ANY PUBLISHED CPU ARTIFACT AT THIS CELL, BEFORE THE RUN TOUCHES IT
    if extra_note:
        rec["preserved_published_rows"] = extra_note
    cmd = driver_cmd(cabinet, entrant, level)
    rec["driver_cmd"] = cmd
    logfile = os.path.join(LOGS, f"{cabinet}_{entrant}_{(level or 'cell').replace('/', '_')}_{stamp}.log")
    t0 = time.time()
    watcher = Watcher()
    watcher.start()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=10800)
        out, err, rc = p.stdout, p.stderr, p.returncode
    except subprocess.TimeoutExpired as e:
        out, err, rc = (e.stdout or ""), (e.stderr or ""), None
    if isinstance(out, bytes):
        out = out.decode("utf-8", "replace")
    if isinstance(err, bytes):
        err = err.decode("utf-8", "replace")
    wall = round(time.time() - t0, 1)
    watch = watcher.finish()
    with open(logfile, "w") as f:
        f.write(out + "\n--- stderr ---\n" + (err or ""))
    rec["driver"] = {"exit": rc, "wall_secs": wall, "log": logfile,
                     "stdout_tail": out[-3000:], "stderr_tail": (err or "")[-1500:]}
    rec["vram"] = {"card_max_mib": watch["card_max_mib"], "pid_max_mib": watch["pid_max_mib"],
                   "samples": watch["samples"]}
    m = ART_RE[cabinet].search(out)
    art = None
    if m:
        cand = m.group(1)
        art = cand if os.path.isabs(cand) else os.path.join(ROOT, cand)
        if not os.path.exists(art):
            art = None
    rec["artifact"] = art
    rec["artifact_sha256"] = sha256_file(art) if art and os.path.exists(art) else None
    if watch["server_pid"]:
        rec["serving_process"] = proc_identity(watch["server_pid"],
                                               os.path.join(MODELS, ENTRANTS[entrant]["file"]))
    rec["props"] = watch["props"]
    if watch["props"]:
        gs = watch["props"].get("default_generation_settings") or {}
        rec["compute_path"] = {
            "ngl_flag": 99, "ctx_flag": gs.get("n_ctx"),
            "props_model_path": watch["props"].get("model_path"),
            "props_model_ftype": watch["props"].get("model_ftype"),
            "props_total_slots": watch["props"].get("total_slots"),
            "props_alias": watch["props"].get("model_alias"),
            "build_line": watch["props"].get("build_info"),
            "binary_from_cmdline": rec.get("serving_process", {}).get("cmdline", [None])[0]}
    rec["release"] = verify_release(baseline, watch["server_pid"])
    rec["block_finished"] = now()
    meta = os.path.join(OUT, f"{cabinet}_{entrant}_{(level or 'cell').replace('/', '_')}_{stamp}.meta.json")
    with open(meta, "w") as f:
        json.dump(rec, f, indent=1)
    rec["meta_file"] = meta
    print(json.dumps({"cabinet": cabinet, "entrant": entrant, "level": level, "exit": rc,
                      "wall_s": wall, "artifact": art,
                      "pid_max_mib": rec["vram"]["pid_max_mib"],
                      "card_max_mib": rec["vram"]["card_max_mib"],
                      "release": {k: rec["release"][k] for k in
                                  ("port_closed", "vram_mib_after", "vram_delta_mib",
                                   "vram_back_to_baseline", "resident_health_after")}},
                     indent=1))
    return rec


# ── labyrinth: suite-served ──────────────────────────────────────────────────
def run_labyrinth_block(entrant, baseline):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(LOGS, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    rec = {"entrant": entrant, "cabinet": "labyrinth", "block_started": now(),
           "baseline_mib_at_start": baseline, "resident_health_before": resident_health(),
           "shape": "suite-served"}
    lease = sd.start_entrant(entrant, 99, 8192)
    if not lease.get("ok"):
        rec.update({"admission": "FAILED", "admission_detail": lease})
        p = os.path.join(OUT, f"labyrinth_{entrant}_ADMISSION_FAILED_{stamp}.json")
        json.dump(rec, open(p, "w"), indent=1)
        print(json.dumps({"admission": "FAILED", "entrant": entrant, "reason": lease.get("reason")}))
        return rec
    rec["admission"] = "OK"
    rec["compute_path"] = sd.compute_path(lease, entrant, 99, 8192)
    # the identity file the cell requires: its OWN fields, read from the live process
    ident = {"api_model_id": entrant,
             "quant": entrant,           # the filename's recipe; /props ftype is in compute_path
             "server_argv": rec["compute_path"]["serving_process"].get("cmdline"),
             "server_binary_digest": sha256_file(rec["compute_path"]["serving_process"]["binary_path"])}
    ident_path = os.path.join(OUT, f"labyrinth_identity_{entrant}_{stamp}.json")
    json.dump(ident, open(ident_path, "w"), indent=1)
    rec["model_identity_file"] = ident_path
    outdir = os.path.join(ROOT, "suite2", "labyrinth")
    os.makedirs(outdir, exist_ok=True)
    cmd = [sys.executable, DRIVER["labyrinth"], "--graph", GRAPH, "--symmetrisation", "min",
           "--K", "12", "--rune", "Fehu", "--cap", str(LABYRINTH_CAP), "--seed", "0",
           "--cell-spec", CELL_SPEC, "--out-dir", outdir, "--base-url", BASE,
           "--model", entrant, "--model-identity", ident_path, "--no-think"]
    rec["driver_cmd"] = cmd
    watcher = Watcher()
    watcher.pid = lease["pid"]
    watcher.start()
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    wall = round(time.time() - t0, 1)
    watch = watcher.finish()
    logfile = os.path.join(LOGS, f"labyrinth_{entrant}_{stamp}.log")
    open(logfile, "w").write(p.stdout + "\n--- stderr ---\n" + (p.stderr or ""))
    rec["driver"] = {"exit": p.returncode, "wall_secs": wall, "log": logfile,
                     "stdout_tail": p.stdout[-3000:], "stderr_tail": (p.stderr or "")[-1500:]}
    rec["vram"] = {"card_max_mib": watch["card_max_mib"], "pid_max_mib": watch["pid_max_mib"],
                   "samples": watch["samples"]}
    before = set(glob.glob(os.path.join(outdir, "*.json")))
    m = re.search(r"(/\S+\.json)|(\S+\.json)", p.stdout)
    newest = max(before, key=os.path.getmtime) if before else None
    rec["artifact"] = newest
    rec["artifact_sha256"] = sha256_file(newest) if newest else None
    rec["release"] = sd.stop_entrant(lease, baseline)
    rec["release"]["listener_after"] = find_server_pid()
    rec["block_finished"] = now()
    meta = os.path.join(OUT, f"labyrinth_{entrant}_cell01_{stamp}.meta.json")
    json.dump(rec, open(meta, "w"), indent=1)
    rec["meta_file"] = meta
    print(json.dumps({"cabinet": "labyrinth", "entrant": entrant, "exit": p.returncode,
                      "wall_s": wall, "artifact": newest,
                      "pid_max_mib": rec["vram"]["pid_max_mib"],
                      "release": {k: rec["release"][k] for k in
                                  ("port_closed", "vram_mib_after", "vram_delta_mib",
                                   "vram_back_to_baseline", "resident_health_after")}}, indent=1))
    return rec


# ── cabinet drivers ──────────────────────────────────────────────────────────
def run_sokoban(entrant, baseline):
    recs = []
    for lv in SOKOBAN_LEVELS:
        note = None
        target = os.path.join(ROOT, "probes",
                              f"SOKOBAN_{entrant}_{os.path.splitext(os.path.basename(lv))[0]}.json")
        if os.path.exists(target):
            note = preserve(target, "published CPU artifact at this cell; the GPU row is a new row, "
                                    "this copy is the record of the row that was already there")
            print(f"[preserve] {target} -> {note['preserved_at']} sha256 {note['sha256'][:16]}")
        recs.append(run_driver_block(entrant, "sokoban", lv, gpu_used() if baseline is None else baseline,
                                     extra_note=note))
    return recs


def run_zork(entrant, baseline):
    recs = []
    for lv in ZORK_LEVELS:
        note = None
        target = os.path.join(ROOT, "probes",
                              f"ZORK_{entrant}_{os.path.splitext(os.path.basename(lv))[0]}.json")
        if os.path.exists(target):
            note = preserve(target, "published CPU artifact at this cell; the GPU row is a new row")
            print(f"[preserve] {target} -> {note['preserved_at']} sha256 {note['sha256'][:16]}")
        recs.append(run_driver_block(entrant, "zork", lv, gpu_used() if baseline is None else baseline,
                                     extra_note=note))
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrant", default=None)
    ap.add_argument("--cabinet", default="sokoban",
                    help="sokoban|zork|snake|labyrinth|chess|all")
    a = ap.parse_args()
    baseline = gpu_used()
    print(f"[suite2] baseline VRAM at block start: {baseline} MiB   resident health {resident_health()}")
    cabinets = CABINETS if a.cabinet == "all" else [a.cabinet]
    entrants = [a.entrant] if a.entrant else ORDER
    all_recs = []
    for cab in cabinets:
        for e in entrants:
            print(f"\n[suite2] {cab} / {e}")
            if cab == "sokoban":
                all_recs += run_sokoban(e, None)
            elif cab == "zork":
                all_recs += run_zork(e, None)
            elif cab == "snake":
                all_recs.append(run_driver_block(e, "snake", None, gpu_used()))
            elif cab == "chess":
                all_recs.append(run_driver_block(e, "chess", None, gpu_used()))
            elif cab == "labyrinth":
                all_recs.append(run_labyrinth_block(e, gpu_used()))
    print(f"\n[suite2] wrote {len(all_recs)} block(s) under {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
