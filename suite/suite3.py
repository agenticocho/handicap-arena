#!/usr/bin/env python3
"""suite3.py — the GPU window for card t_925f606f (Ocho, 2026-10-26).

ONE WINDOW, ONE LEASE, ONE ENTRANT RESIDENT AT A TIME.

Eight cabinets were certified (CPU-side) on 2026-10-26 by their owners. This wrapper scores ONLY
the cabinets whose certification Ocho re-verified against the producing artifact, and refuses the
rest. Per block it:

  * samples the card at the block's START (never a remembered 1,731 MiB),
  * checks the resident :58595 seat's health (it is never touched),
  * runs one cabinet with one entrant resident on :58701 (driver-owned) or suite-served,
  * watches the live process: pid from /proc, /props, argv from /proc/<pid>/cmdline, VRAM per pid,
  * verifies the release: port closed AND memory back to this block's own baseline +-64 MiB,
  * files the block record (suite3/runs/*.meta.json) BEFORE the next block starts, so a window that
    closes early still leaves every row it took.

Nothing here writes a verdict about an entrant: it records what the cabinet wrote, plus the
compute path and the serving-process identity, and it never merges a new row with an old one.
Pre-existing artifact bytes at a cell are copied to suite3/preserved/ with their digest before
the driver is allowed to replace them.

Usage:
  python3 suite3.py --cabinet chess --entrant ministral-3b
  python3 suite3.py --cabinet all --entrant all
"""
import glob
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = "/home/chilly1/workspace/ocho_arena"
MODELS = "/home/chilly1/moltbook_pipeline/models"
PRISMML = "/home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server"
LLAMACPP = "/home/chilly1/llama.cpp/build/bin/llama-server"
GRAPH = "/home/chilly1/workspace/chair-link/artifacts/ged_matrix.json"
CELL_SPEC = os.path.join(ROOT, "CELL_01_labyrinth.md")

OUT = os.path.join(ROOT, "suite3", "runs")
LOGS = os.path.join(ROOT, "suite3", "logs")
PRESERVED = os.path.join(ROOT, "suite3", "preserved")
LO_OUT = os.path.join(ROOT, "suite3", "lightsout")
LAB_OUT = os.path.join(ROOT, "suite3", "labyrinth")
WINDOW = "t_925f606f"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# reuse the sitting-2 machinery rather than forking it
S2 = _load(os.path.join(ROOT, "suite", "suite2.py"), "suite2_lib")
sd = S2.sd
PORT = S2.PORT
ENTRANTS = S2.ENTRANTS
ORDER = ["ministral-3b", "ornith-9b", "mimo-9b", "bonsai-9b"]

CABINETS = ["chess", "mastermind", "lightsout", "snake", "labyrinth", "sokoban", "zork"]

SOKOBAN_LEVELS = ["levels/01_one_push.txt", "levels/02_two_boxes.txt", "levels/03_the_corner_waiting.txt"]
ZORK_LEVELS = ["levels/zork_01_the_floor.txt", "levels/zork_02_long_crawl.txt"]
CHESS_CAP = 30
LABYRINTH_CAP = 40
SNAKE_SEEDS = "1,7"
SNAKE_TICKS = 120
# THE CERTIFIED SNAKE INSTRUMENT IS cabinet/snake @ 149d0d0, NOT the trunk copy. The trunk's
# snake_run.py (44256 B) is a DIVERGENT sitting-2 revision that does not write score.revisits;
# the cabinet's (42349 B) is the one the certification card measured. Pass 2 of this window runs
# the certified copy and pass 1 stands beside it, superseded and not merged.
SNAKE_DRIVER = "/home/chilly1/workspace/ocho_arena_cabinets/snake/snake_run.py"
SNAKE_PROBES = "/home/chilly1/workspace/ocho_arena_cabinets/snake/probes"
MM_LIMIT = 10
MM_MAXTOK = 512


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dirs():
    for d in (OUT, LOGS, PRESERVED, LO_OUT, LAB_OUT):
        os.makedirs(d, exist_ok=True)


def vulnerable(paths, why):
    """Copy pre-existing bytes at a cell aside BEFORE a driver may replace them. Digest recorded."""
    recs = []
    for p in paths:
        if not os.path.exists(p):
            continue
        dest_dir = os.path.join(PRESERVED, time.strftime("%Y%m%d-%H%M%S"))
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, os.path.basename(p))
        shutil.copy2(p, dest)
        rec = {"original": p, "preserved_at": dest, "sha256": sha256_file(p),
               "bytes": os.path.getsize(p), "why": why, "preserved": now()}
        with open(dest + ".provenance.json", "w") as f:
            json.dump(rec, f, indent=1)
        recs.append(rec)
        print(f"[preserve] {os.path.basename(p)} sha256 {rec['sha256'][:16]} -> {dest}")
    return recs


def label_of(entrant):
    return ENTRANTS[entrant]["file"].replace(".gguf", "")


def entry_path(cabinet, entrant, level):
    lab = label_of(entrant)
    if cabinet == "sokoban":
        return os.path.join(ROOT, "probes", f"SOKOBAN_{lab}_{os.path.splitext(os.path.basename(level))[0]}.json")
    if cabinet == "zork":
        return os.path.join(ROOT, "probes", f"ZORK_{lab}_{os.path.splitext(os.path.basename(level))[0]}.json")
    if cabinet == "chess":
        # chess_game.py writes to _root.results_dir() = /home/chilly1/workspace/cabinet_results/main,
        # which is a SIBLING of the arena tree, not inside it.
        return os.path.join("/home/chilly1/workspace/cabinet_results/main",
                            f"CHESS_GAME_{entrant}-suite3.json")
    return None


def driver_cmd(cabinet, entrant, level, overwrite=None):
    p = os.path.join(MODELS, ENTRANTS[entrant]["file"])
    py = sys.executable
    if cabinet == "chess":
        cmd = [py, os.path.join(ROOT, "chess_game.py"), "--entrant", p,
               "--label", f"{entrant}-suite3", "--cap", str(CHESS_CAP), "--port", str(PORT),
               "--ngl", "99", "--ctx", "8192", "--parallel", "1",
               "--cache-type-k", "q8_0", "--cache-type-v", "q8_0"]
        if entrant == "bonsai-9b":
            cmd += ["--llama-server", PRISMML]
        return cmd
    if cabinet == "sokoban":
        cmd = [py, os.path.join(ROOT, "sokoban_run.py"), "--entrant", p, "--level", level,
               "--cap", "40", "--port", str(PORT), "--ngl", "99", "--parallel", "1"]
        if entrant == "bonsai-9b":
            cmd += ["--llama-server", PRISMML]
        if overwrite:
            cmd += ["--overwrite-artifact", overwrite]
        return cmd
    if cabinet == "zork":
        cmd = [py, os.path.join(ROOT, "zork_run.py"), "--entrant", p, "--level", level,
               "--cap", "20", "--port", str(PORT), "--ngl", "99", "--parallel", "1"]
        if entrant == "bonsai-9b":
            cmd += ["--llama-server", PRISMML]
        if overwrite:
            cmd += ["--overwrite-artifact", overwrite]
        return cmd
    if cabinet == "snake":
        cmd = [py, SNAKE_DRIVER, "--entrant", p, "--seeds", SNAKE_SEEDS,
               "--ticks", str(SNAKE_TICKS), "--port", str(PORT), "--ngl", "99", "--ctx", "8192",
               "--parallel", "1"]
        if entrant != "bonsai-9b":
            cmd += ["--llama-server", LLAMACPP]
        if overwrite:
            cmd += ["--overwrite-artifact", overwrite]
        return cmd
    raise SystemExit("no driver for " + cabinet)


CONTROL_LINE = {
    "chess": "ALL CONTROLS PASS",
    "mastermind": "CONTROL BLOCK PASSED",
}


def run_driver_block(cabinet, entrant, level, baseline, preserved=None):
    ensure_dirs()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    rec = {"window": WINDOW, "cabinet": cabinet, "entrant": entrant, "level": level,
           "block_started": now(), "baseline_mib_at_start": baseline,
           "resident_health_before": sd.resident_health(), "shape": "driver-owned",
           "preserved_preexisting": preserved or []}
    overwrite = None
    if preserved:
        overwrite = (f"GPU window {WINDOW}: re-measuring this cell under the instrument certified on "
                     f"2026-10-26. The pre-existing record(s) are preserved with their digests under "
                     f"suite3/preserved/ and are reported BESIDE this row, never merged into it.")
    cmd = driver_cmd(cabinet, entrant, level, overwrite=overwrite)
    rec["driver_cmd"] = cmd
    logfile = os.path.join(LOGS, f"{cabinet}_{entrant}_{(level or 'cell').replace('/', '_')}_{stamp}.log")
    watcher = S2.Watcher(os.path.join(MODELS, ENTRANTS[entrant]["file"]))
    watcher.start()
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
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
    if watch.get("identity"):
        rec["serving_process"] = watch["identity"]
    elif watch["server_pid"]:
        rec["serving_process"] = S2.proc_identity(watch["server_pid"],
                                                  os.path.join(MODELS, ENTRANTS[entrant]["file"]))
    rec["props"] = watch["props"]
    if watch["props"]:
        gs = watch["props"].get("default_generation_settings") or {}
        rec["compute_path"] = {
            "ngl_flag": 99, "ctx_flag": gs.get("n_ctx"),
            "props_model_path": watch["props"].get("model_path"),
            "props_model_ftype": watch["props"].get("model_ftype"),
            "props_total_slots": watch["props"].get("total_slots"),
            "build_line": watch["props"].get("build_info"),
            "binary_from_cmdline": (rec.get("serving_process") or {}).get("cmdline", [None])[0]}
    # what the cabinet's own process said about its controls
    line = CONTROL_LINE.get(cabinet)
    rec["controls_in_producing_process"] = (line in out) if line else None
    rec["release"] = S2.verify_release(baseline, watch["server_pid"])
    rec["block_finished"] = now()
    # the artifact: computed path, existence, digest, and that it was written DURING this block
    art = entry_path(cabinet, entrant, level)
    if cabinet == "snake":
        # snake_run.py writes ONE artifact per seed, not one per block: resolve the set and keep it
        lab = label_of(entrant)
        arts = [os.path.join(SNAKE_PROBES, f"SNAKE_{lab}_s{s}.json") for s in SNAKE_SEEDS.split(",")]
        rec["artifacts"] = [{"path": x, "exists": os.path.exists(x),
                             "sha256": sha256_file(x) if os.path.exists(x) else None,
                             "mtime_epoch": os.path.getmtime(x) if os.path.exists(x) else None}
                            for x in arts]
        rec["artifact_exists"] = all(a["exists"] and a["mtime_epoch"] >= t0 - 2 for a in rec["artifacts"])
        rec["artifact"] = None
        rec["artifact_set"] = arts
    if not (art and os.path.exists(art)):
        # fallback: read the coordinate the driver PRINTED, resolved against the arena root
        m = re.search(r"^\s*artifact:?\s+(\S+\.json)", out, re.M)
        if m:
            cand = m.group(1)
            cand = cand if os.path.isabs(cand) else os.path.normpath(os.path.join(ROOT, cand))
            if os.path.exists(cand):
                art = cand
    rec["artifact"] = art
    rec["artifact_exists"] = bool(art and os.path.exists(art))
    if rec["artifact_exists"]:
        rec["artifact_sha256"] = sha256_file(art)
        rec["artifact_mtime"] = time.strftime("%Y-%m-%dT%H:%M:%S%z",
                                              time.localtime(os.path.getmtime(art)))
        rec["artifact_written_in_block"] = os.path.getmtime(art) >= t0 - 2
    meta = os.path.join(OUT, f"{cabinet}_{entrant}_{(level or 'cell').replace('/', '_')}_{stamp}.meta.json")
    with open(meta, "w") as f:
        json.dump(rec, f, indent=1)
    rec["meta_file"] = meta
    print(json.dumps({"cabinet": cabinet, "entrant": entrant,
                      "level": os.path.basename(level) if level else None,
                      "exit": rc, "wall_s": wall,
                      "artifact_exists": rec["artifact_exists"],
                      "card_max_mib": rec["vram"]["card_max_mib"],
                      "pid_max_mib": rec["vram"]["pid_max_mib"],
                      "controls": rec["controls_in_producing_process"],
                      "release": {k: rec["release"][k] for k in
                                  ("port_closed", "vram_mib_after", "vram_delta_mib",
                                   "vram_back_to_baseline", "resident_health_after")}}, indent=1))
    return rec


def run_suite_served_block(cabinet, entrant, baseline):
    """Mastermind and Lights Out: the suite owns the server, so the tenancy is ours to apply."""
    ensure_dirs()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    rec = {"window": WINDOW, "cabinet": cabinet, "entrant": entrant, "level": None,
           "block_started": now(), "baseline_mib_at_start": baseline,
           "resident_health_before": sd.resident_health(), "shape": "suite-served"}
    lease = sd.start_entrant(entrant, 99, 8192)
    if not lease.get("ok"):
        rec.update({"admission": "FAILED", "admission_detail": lease})
        p = os.path.join(OUT, f"{cabinet}_{entrant}_ADMISSION_FAILED_{stamp}.json")
        json.dump(rec, open(p, "w"), indent=1)
        print(json.dumps({"cabinet": cabinet, "entrant": entrant, "admission": "FAILED",
                          "reason": lease.get("reason"), "tail": (lease.get("tail") or "")[-600:]}))
        return rec
    rec["admission"] = "OK"
    rec["compute_path"] = sd.compute_path(lease, entrant, 99, 8192)
    try:
        with open(f"/proc/{lease['pid']}/cmdline", "rb") as f:
            srv_argv = [x.decode() for x in f.read().split(b"\0") if x]
    except OSError:
        srv_argv = list(lease.get("cmd") or [])
    rec["server_argv_from_proc"] = srv_argv
    rec["serving_process"] = S2.proc_identity(lease["pid"], os.path.join(MODELS, ENTRANTS[entrant]["file"]))
    rec["props"] = lease.get("props")
    watcher = S2.Watcher()
    watcher.pid = lease["pid"]
    watcher.start()
    logfile = os.path.join(LOGS, f"{cabinet}_{entrant}_{stamp}.log")
    art = None
    if cabinet == "mastermind":
        art = os.path.join(OUT, f"MASTERMIND_ROW_{entrant}_{stamp}.json")
        cmd = [sys.executable, os.path.join(ROOT, "probes/mastermind/mastermind_run_onefile.py"),
               "--fixture", os.path.join(ROOT, "probes/mastermind/mastermind_secrets_16.txt"),
               "--base", f"http://127.0.0.1:{PORT}", "--model", entrant,
               "--limit", str(MM_LIMIT), "--max-tokens", str(MM_MAXTOK), "--out", art]
    elif cabinet == "lightsout":
        art = os.path.join(LO_OUT, f"LIGHTOUT_ROW_{entrant}_{stamp}.jsonl")
        cmd = [sys.executable, os.path.join(ROOT, "suite/cabinets/lightsout_param.py"),
               "--base", f"http://127.0.0.1:{PORT}", "--model", entrant, "--out", art]
    else:
        raise SystemExit("no suite-served driver for " + cabinet)
    rec["driver_cmd"] = cmd
    rec["artifact"] = art
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    wall = round(time.time() - t0, 1)
    out, err = p.stdout, p.stderr or ""
    watch = watcher.finish()
    with open(logfile, "w") as f:
        f.write(out + "\n--- stderr ---\n" + err)
    rec["driver"] = {"exit": p.returncode, "wall_secs": wall, "log": logfile,
                     "stdout_tail": out[-3000:], "stderr_tail": err[-1500:]}
    rec["vram"] = {"card_max_mib": watch["card_max_mib"], "pid_max_mib": watch["pid_max_mib"],
                   "samples": watch["samples"]}
    line = CONTROL_LINE.get(cabinet)
    rec["controls_in_producing_process"] = (line in out) if line else None
    rec["artifact_exists"] = os.path.exists(art)
    if rec["artifact_exists"]:
        rec["artifact_sha256"] = sha256_file(art)
        rec["artifact_written_in_block"] = os.path.getmtime(art) >= t0 - 2
    # lightsout: claim vs state, scored by the cabinet's own recomputed-truth scorer
    if cabinet == "lightsout" and rec["artifact_exists"]:
        sp = subprocess.run([sys.executable, os.path.join(ROOT, "lightsout_cabinet.py"),
                             "--score", art], capture_output=True, text=True)
        rec["claim_vs_state"] = {"exit": sp.returncode, "out": sp.stdout[-2000:],
                                 "err": sp.stderr[-800:]}
    rec["release"] = sd.stop_entrant(lease, baseline)
    rec["release"]["listener_after"] = S2.find_server_pid()
    rec["block_finished"] = now()
    meta = os.path.join(OUT, f"{cabinet}_{entrant}_cell_{stamp}.meta.json")
    with open(meta, "w") as f:
        json.dump(rec, f, indent=1)
    rec["meta_file"] = meta
    print(json.dumps({"cabinet": cabinet, "entrant": entrant, "exit": p.returncode,
                      "wall_s": wall, "artifact_exists": rec["artifact_exists"],
                      "controls": rec["controls_in_producing_process"],
                      "card_max_mib": rec["vram"]["card_max_mib"],
                      "release": {k: rec["release"].get(k) for k in
                                  ("port_closed", "vram_mib_after", "vram_delta_mib",
                                   "vram_back_to_baseline", "resident_health_after")}}, indent=1))
    return rec


def run_labyrinth_block(entrant, baseline):
    """Labyrinth is driver-owned but takes --base-url, so the suite serves the entrant."""
    ensure_dirs()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    rec = {"window": WINDOW, "cabinet": "labyrinth", "entrant": entrant, "level": "cell_01",
           "block_started": now(), "baseline_mib_at_start": baseline,
           "resident_health_before": sd.resident_health(), "shape": "suite-served"}
    lease = sd.start_entrant(entrant, 99, 8192)
    if not lease.get("ok"):
        rec.update({"admission": "FAILED", "admission_detail": lease})
        json.dump(rec, open(os.path.join(OUT, f"labyrinth_{entrant}_ADMISSION_FAILED_{stamp}.json"), "w"),
                  indent=1)
        print(json.dumps({"cabinet": "labyrinth", "entrant": entrant, "admission": "FAILED",
                          "reason": lease.get("reason")}))
        return rec
    rec["admission"] = "OK"
    rec["compute_path"] = sd.compute_path(lease, entrant, 99, 8192)
    try:
        with open(f"/proc/{lease['pid']}/cmdline", "rb") as f:
            srv_argv = [x.decode() for x in f.read().split(b"\0") if x]
    except OSError:
        srv_argv = list(lease.get("cmd") or [])
    rec["server_argv_from_proc"] = srv_argv
    rec["serving_process"] = S2.proc_identity(lease["pid"], os.path.join(MODELS, ENTRANTS[entrant]["file"]))
    rec["props"] = lease.get("props")
    ident = {"api_model_id": entrant, "server_argv": srv_argv,
             "server_binary_digest": sha256_file(srv_argv[0])}
    # labyrinth's identity spec §3 requires quant; derived from the weights basename, as sitting 2 did
    stem = ENTRANTS[entrant]["file"].replace(".gguf", "")
    ident["quant"] = next((p for p in stem.split("-") if re.match(r"^(UD-)?(PQ|IQ|Q)\d", p)), "undeclared")
    ident_path = os.path.join(OUT, f"labyrinth_identity_{entrant}_{stamp}.json")
    json.dump(ident, open(ident_path, "w"), indent=1)
    rec["model_identity_file"] = ident_path
    before = set(glob.glob(os.path.join(LAB_OUT, "*.json")))
    cmd = [sys.executable, os.path.join(ROOT, "labyrinth_run.py"), "--graph", GRAPH,
           "--symmetrisation", "min", "--K", "12", "--rune", "Fehu", "--cap", str(LABYRINTH_CAP),
           "--seed", "0", "--cell-spec", CELL_SPEC, "--out-dir", LAB_OUT,
           "--base-url", f"http://127.0.0.1:{PORT}", "--model", entrant,
           "--model-identity", ident_path, "--no-think"]
    rec["driver_cmd"] = cmd
    watcher = S2.Watcher()
    watcher.pid = lease["pid"]
    watcher.start()
    logfile = os.path.join(LOGS, f"labyrinth_{entrant}_{stamp}.log")
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    wall = round(time.time() - t0, 1)
    out, err = p.stdout, p.stderr or ""
    watch = watcher.finish()
    with open(logfile, "w") as f:
        f.write(out + "\n--- stderr ---\n" + err)
    rec["driver"] = {"exit": p.returncode, "wall_secs": wall, "log": logfile,
                     "stdout_tail": out[-3000:], "stderr_tail": err[-1500:]}
    rec["vram"] = {"card_max_mib": watch["card_max_mib"], "pid_max_mib": watch["pid_max_mib"],
                   "samples": watch["samples"]}
    new = [x for x in set(glob.glob(os.path.join(LAB_OUT, "*.json"))) - before]
    art = max(new, key=os.path.getmtime) if new else None
    rec["artifact"] = art
    rec["artifact_exists"] = bool(art)
    if art:
        rec["artifact_sha256"] = sha256_file(art)
        rec["artifact_written_in_block"] = os.path.getmtime(art) >= t0 - 2
    rec["controls_in_producing_process"] = None  # labyrinth's control is a separate CPU process
    rec["release"] = sd.stop_entrant(lease, baseline)
    rec["release"]["listener_after"] = S2.find_server_pid()
    rec["block_finished"] = now()
    meta = os.path.join(OUT, f"labyrinth_{entrant}_cell01_{stamp}.meta.json")
    with open(meta, "w") as f:
        json.dump(rec, f, indent=1)
    rec["meta_file"] = meta
    print(json.dumps({"cabinet": "labyrinth", "entrant": entrant, "exit": p.returncode,
                      "wall_s": wall, "artifact": art,
                      "release": {k: rec["release"].get(k) for k in
                                  ("port_closed", "vram_mib_after", "vram_delta_mib",
                                   "vram_back_to_baseline", "resident_health_after")}}, indent=1))
    return rec


def run_cabinet(cabinet, entrant):
    recs = []
    if cabinet == "sokoban":
        for lv in SOKOBAN_LEVELS:
            paths = [entry_path("sokoban", entrant, lv)]
            pres = vulnerable(paths, f"GPU window {WINDOW}: pre-existing record at this cell")
            recs.append(run_driver_block("sokoban", entrant, lv, sd.gpu_used_mib(), pres))
    elif cabinet == "zork":
        for lv in ZORK_LEVELS:
            paths = [entry_path("zork", entrant, lv)]
            pres = vulnerable(paths, f"GPU window {WINDOW}: pre-existing record at this cell")
            recs.append(run_driver_block("zork", entrant, lv, sd.gpu_used_mib(), pres))
    elif cabinet == "snake":
        lab = label_of(entrant)
        paths = [os.path.join(SNAKE_PROBES, f"SNAKE_{lab}_s{s}.json") for s in SNAKE_SEEDS.split(",")]
        pres = vulnerable(paths, f"GPU window {WINDOW}: pre-existing snake episodes at this coordinate")
        recs.append(run_driver_block("snake", entrant, None, sd.gpu_used_mib(), pres))
    elif cabinet == "chess":
        paths = [entry_path("chess", entrant, None)]
        pres = vulnerable(paths, f"GPU window {WINDOW}: pre-existing chess row at this label")
        recs.append(run_driver_block("chess", entrant, None, sd.gpu_used_mib(), pres))
    elif cabinet in ("mastermind", "lightsout"):
        recs.append(run_suite_served_block(cabinet, entrant, sd.gpu_used_mib()))
    elif cabinet == "labyrinth":
        recs.append(run_labyrinth_block(entrant, sd.gpu_used_mib()))
    return recs


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cabinet", default="all")
    ap.add_argument("--entrant", default="all")
    a = ap.parse_args()
    cabs = CABINETS if a.cabinet == "all" else [c.strip() for c in a.cabinet.split(",")]
    ents = ORDER if a.entrant == "all" else [e.strip() for e in a.entrant.split(",")]
    ensure_dirs()
    t_start = now()
    print(f"=== WINDOW {WINDOW} start {t_start} cabinets={cabs} entrants={ents} ===")
    for cab in cabs:
        for ent in ents:
            print(f"--- {cab} / {ent} {now()} ---")
            run_cabinet(cab, ent)
    print(f"=== WINDOW {WINDOW} end {now()} ===")


if __name__ == "__main__":
    main()
