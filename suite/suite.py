#!/usr/bin/env python3
"""suite.py — the sequenced GPU window for kanban t_c4fa298e.

One entrant resident at a time on a private port, cabinets run sequentially, release verified
mechanically (no listener, VRAM back to the baseline sampled at suite start).

Every number filed by this driver is read from a command's own output: the harness's own
stdout/row file for the model result, `/props` for model identity, `nvidia-smi` for VRAM
attribution. Nothing is inferred from a flag the driver passed.

Usage:
  python3 suite/suite.py --check-admission                     # load/health/props/release per entrant
  python3 suite/suite.py --entrant bonsai-9b --cabinet mastermind,lightsout
  python3 suite/suite.py --report                              # aggregate filed rows into tables
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

ROOT = "/home/chilly1/workspace/ocho_arena"
MODELS = "/home/chilly1/moltbook_pipeline/models"
LLAMACPP = "/home/chilly1/llama.cpp/build/bin/llama-server"
PRISMML = "/home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server"
PORT = 58701
BASE = f"http://127.0.0.1:{PORT}"
RESIDENT_HEALTH = "http://127.0.0.1:58595/health"
OUTDIR = os.path.join(ROOT, "suite", "runs")
LOGDIR = os.path.join(ROOT, "suite", "logs")

ENTRANTS = {
    "ministral-3b": {"file": "Ministral-3-3B-Instruct-2512-UD-Q4_K_XL.gguf", "binary": LLAMACPP},
    "ornith-9b": {"file": "Ornith-1.5-9B-Q4_K_M.gguf", "binary": LLAMACPP},
    "mimo-9b": {"file": "MiMo-V2.6-Distill-Qwen-9B-Q4_K_M.gguf", "binary": LLAMACPP},
    "bonsai-9b": {"file": "Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0.gguf", "binary": PRISMML},
}

MM_RUNNER = os.path.join(ROOT, "probes/mastermind/mastermind_run_onefile.py")
MM_FIXTURE = os.path.join(ROOT, "probes/mastermind/mastermind_secrets_16.txt")
LO_RUNNER = os.path.join(ROOT, "suite/cabinets/lightsout_param.py")


# ── process-level probes ─────────────────────────────────────────────────────
def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def gpu_used_mib():
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True, check=True).stdout
    return int(out.strip().splitlines()[0])


def gpu_pid_mib(pid):
    """VRAM the driver's own server pid is attributed. Read, never inferred."""
    out = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory",
                          "--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 2 and parts[0] == str(pid):
            return int(parts[1])
    return 0


def port_open(port=PORT, host="127.0.0.1"):
    s = socket.socket()
    s.settimeout(0.5)
    try:
        s.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def get_json(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def resident_health():
    try:
        with urllib.request.urlopen(RESIDENT_HEALTH, timeout=5) as r:
            return r.status
    except Exception as e:  # noqa: BLE001
        return f"ERR:{type(e).__name__}"


class Sampler(threading.Thread):
    """Samples card-level and per-pid VRAM while the cabinet runs."""

    def __init__(self, pid):
        super().__init__(daemon=True)
        self.pid, self.stop_flag, self.samples = pid, False, []

    def run(self):
        while not self.stop_flag:
            try:
                self.samples.append({"t": time.time(), "total_mib": gpu_used_mib(),
                                     "pid_mib": gpu_pid_mib(self.pid)})
            except Exception:  # noqa: BLE001
                pass
            time.sleep(2)

    def stop(self):
        self.stop_flag = True
        self.join(timeout=5)
        return self.samples


# ── the entrant lease ────────────────────────────────────────────────────────
def start_entrant(name, ngl, ctx=8192):
    spec = ENTRANTS[name]
    path = os.path.join(MODELS, spec["file"])
    os.makedirs(LOGDIR, exist_ok=True)
    logpath = os.path.join(LOGDIR, f"{name}_ngl{ngl}_{time.strftime('%Y%m%d-%H%M%S')}.log")
    cmd = [spec["binary"], "-m", path,
           "--host", "127.0.0.1", "--port", str(PORT),
           "--n-gpu-layers", str(ngl),
           "--ctx-size", str(ctx),
           "--cache-type-k", "q8_0", "--cache-type-v", "q8_0",
           "--parallel", "1",
           "--alias", name,
           "--log-verbosity", "3"]
    log = open(logpath, "wb")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
    deadline = t0 + 180
    while time.time() < deadline:
        if proc.poll() is not None:
            log.close()
            tail = open(logpath, "rb").read()[-2500:].decode("utf-8", "replace")
            return {"ok": False, "reason": "process_exited", "exit": proc.returncode,
                    "log": logpath, "tail": tail, "cmd": cmd, "secs": round(time.time() - t0, 1)}
        if port_open():
            try:
                h = get_json(f"{BASE}/health", timeout=3)
                if h.get("status") in ("ok", "no slot available"):  # loaded, ready
                    props = get_json(f"{BASE}/props", timeout=10)
                    return {"ok": True, "pid": proc.pid, "log": logpath, "cmd": cmd,
                            "props": props, "load_secs": round(time.time() - t0, 1),
                            "proc": proc, "logfh": log}
            except Exception:  # noqa: BLE001
                pass
        time.sleep(0.5)
    proc.terminate()
    log.close()
    return {"ok": False, "reason": "health_timeout", "log": logpath, "cmd": cmd,
            "tail": open(logpath, "rb").read()[-2500:].decode("utf-8", "replace")}


def stop_entrant(lease, baseline_mib):
    """V4: stop, prove the port is closed, prove VRAM returned to baseline."""
    proc = lease["proc"]
    proc.terminate()
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=15)
    lease["logfh"].close()
    t0 = time.time()
    port_closed = False
    while time.time() - t0 < 60:
        if not port_open():
            port_closed = True
            break
        time.sleep(0.5)
    # tolerance is noise on the card, not exactness: the resident seats' allocator moves a few MiB.
    # The check exists to catch a leaked multi-GB entrant, so 64 MiB (0.8% of the card) is the bar,
    # and the measured delta is always recorded rather than absorbed.
    TOL_MIB = 64
    vram = None
    t0 = time.time()
    while time.time() - t0 < 90:
        vram = gpu_used_mib()
        if vram is not None and abs(vram - baseline_mib) <= TOL_MIB:
            break
        time.sleep(1.5)
    return {"port_closed": port_closed, "vram_mib_after": vram,
            "vram_baseline_mib": baseline_mib,
            "vram_delta_mib": None if vram is None else vram - baseline_mib,
            "tolerance_mib": TOL_MIB,
            "vram_back_to_baseline": vram is not None and abs(vram - baseline_mib) <= TOL_MIB,
            "pid_vram_after": gpu_pid_mib(lease["pid"]),
            "resident_health_after": resident_health(),
            "release_secs": round(time.time() - t0, 1)}


def proc_identity(pid, binary, modelfile):
    """Who served the row: the PROCESS, not just the model name.

    A row is a snapshot of a process. The published Mastermind rows were produced by a seat whose
    process had already been replaced by 2026-10-23 15:06:57 (measured: this box), so a re-run today
    is a new row, not a reproduction, unless the process and binary are shown equal. Everything here
    is read: starttime from /proc/<pid>/stat with the kernel's own btime and CLK_TCK, binary and
    weights identity from stat() (size/mtime are the fields that stay stable on this box; a
    multi-GB digest is NOT reproducible here and is not quoted).
    """
    info = {}
    try:
        stat = open(f"/proc/{pid}/stat").read()
        after = stat.rsplit(")", 1)[1].split()
        ticks = int(after[19])                      # field 22 (starttime), 0-based 19 after comm
        btime = None
        for line in open("/proc/stat"):
            if line.startswith("btime "):
                btime = int(line.split()[1]); break
        hz = os.sysconf("SC_CLK_TCK")
        if btime is None:
            raise RuntimeError("btime not found in /proc/stat")
        start_epoch = btime + ticks / hz
        info["pid"] = pid
        info["start_epoch"] = round(start_epoch, 2)
        info["start_time"] = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(start_epoch))
        info["uptime_at_start_s"] = ticks / hz
        info["boot_id"] = open("/proc/sys/kernel/random/boot_id").read().strip()
        info["lstart_ps"] = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)],
                                           capture_output=True, text=True).stdout.strip()
    except Exception as e:  # noqa: BLE001
        info["error"] = repr(e)
    for label, path in (("binary", binary), ("weights", modelfile)):
        try:
            st = os.stat(path)
            info[f"{label}_path"] = path
            info[f"{label}_size"] = st.st_size
            info[f"{label}_mtime"] = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(st.st_mtime))
        except Exception as e:  # noqa: BLE001
            info[f"{label}_error"] = repr(e)
    return info


def compute_path(lease, name, ngl, ctx):
    props = lease["props"]
    return {"entrant": name, "binary": ENTRANTS[name]["binary"],
            "ngl_flag": ngl, "ctx_flag": ctx,
            "cache_k": "q8_0", "cache_v": "q8_0", "parallel_flag": 1,
            "props_model_path": props.get("model_path"),
            "props_model_ftype": props.get("model_ftype"),
            "props_n_ctx": (props.get("default_generation_settings") or {}).get("n_ctx"),
            "props_total_slots": props.get("total_slots"),
            "props_alias": props.get("model_alias"),
            "build_line": props.get("build_info"),
            "serving_process": proc_identity(lease["pid"], ENTRANTS[name]["binary"],
                                             os.path.join(MODELS, ENTRANTS[name]["file"]))}


def warmup():
    body = json.dumps({"model": "x", "messages": [{"role": "user", "content": "Reply with the word ok."}],
                       "temperature": 0.0, "max_tokens": 8,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(f"{BASE}/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read())
    timings = d.get("timings") or {}
    return {"warmup_secs": round(time.time() - t0, 2),
            "server_tok_per_s": timings.get("predicted_per_second"),
            "completion_tokens": (d.get("usage") or {}).get("completion_tokens"),
            "content": (d["choices"][0]["message"].get("content") or "")[:60]}


# ── cabinets ────────────────────────────────────────────────────────────────
def run_mastermind(name, out_json):
    cmd = [sys.executable, MM_RUNNER, "--fixture", MM_FIXTURE, "--base", BASE,
           "--model", name, "--limit", "10", "--max-tokens", "512", "--out", out_json]
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    return {"cabinet": "mastermind", "exit": p.returncode,
            "accepted": p.returncode in (0, 5),
            "exit_meaning": {0: "self-checks passed", 5: "answered turn inconsistent with feedback (expected for models)"}.get(p.returncode, "UNEXPECTED"),
            "wall_secs": round(time.time() - t0, 1),
            "stdout": p.stdout[-4000:], "stderr": p.stderr[-2000:], "out": out_json}


def run_lightsout(name, out_jsonl):
    cmd = [sys.executable, LO_RUNNER, "--base", BASE, "--model", name, "--out", out_jsonl]
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    return {"cabinet": "lightsout", "exit": p.returncode, "accepted": p.returncode == 0,
            "wall_secs": round(time.time() - t0, 1),
            "stdout": p.stdout[-4000:], "stderr": p.stderr[-2000:], "out": out_jsonl}


# ── one entrant, one cabinet: the whole lease lifecycle ──────────────────────
def run_cabinet_block(name, cabinet, ngl, ctx, baseline_mib):
    os.makedirs(OUTDIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    lease = start_entrant(name, ngl, ctx)
    rec = {"entrant": name, "cabinet": cabinet, "started": now(),
           "baseline_mib_at_start": baseline_mib, "resident_health_before": resident_health()}
    if not lease["ok"]:
        rec.update({"admission": "FAILED", "admission_detail": lease})
        with open(os.path.join(OUTDIR, f"{cabinet}_{name}_ADMISSION_FAILED_{stamp}.json"), "w") as f:
            json.dump(rec, f, indent=1)
        return rec

    rec["admission"] = "OK"
    rec["compute_path"] = compute_path(lease, name, ngl, ctx)
    if cabinet == "mastermind":
        out = os.path.join(OUTDIR, f"mastermind_{name}_{stamp}.json")
    else:
        out = os.path.join(OUTDIR, f"lightsout_{name}_{stamp}.jsonl")
    rec["out"] = out
    included = (rec["compute_path"]["props_n_ctx"] == ctx
                and rec["compute_path"]["props_total_slots"] == 1
                and (rec["compute_path"]["props_model_path"] or "").endswith(ENTRANTS[name]["file"]))
    rec["instrument_checks"] = {"n_ctx_from_props_matches_flag": rec["compute_path"]["props_n_ctx"] == ctx,
                               "slots_is_1": rec["compute_path"]["props_total_slots"] == 1,
                               "props_model_is_expected_file": (rec["compute_path"]["props_model_path"] or "").endswith(ENTRANTS[name]["file"])}
    sampler = Sampler(lease["pid"])
    sampler.start()
    try:
        rec["warmup"] = warmup()
        result = run_mastermind(name, out) if cabinet == "mastermind" else run_lightsout(name, out)
    except Exception as e:  # noqa: BLE001
        result = {"cabinet": cabinet, "exit": None, "accepted": False, "error": repr(e)}
    samples = sampler.stop()
    rec["result"] = result
    rec["vram_during_run_mib"] = {"max_total": max([s["total_mib"] for s in samples], default=None),
                                  "max_pid": max([s["pid_mib"] for s in samples], default=None),
                                  "samples": len(samples)}
    rec["release"] = stop_entrant(lease, baseline_mib)
    rec["finished"] = now()
    # VRAM attributable to this entrant = peak pid minus nothing; the entrant is the only new pid
    path = os.path.join(OUTDIR, f"{cabinet}_{name}_{stamp}.meta.json")
    with open(path, "w") as f:
        json.dump(rec, f, indent=1)
    rec["meta_file"] = path
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrant", default=None)
    ap.add_argument("--cabinet", default="mastermind,lightsout")
    ap.add_argument("--ngl", type=int, default=99)
    ap.add_argument("--ctx", type=int, default=8192)
    ap.add_argument("--baseline", type=int, default=None)
    ap.add_argument("--check-admission", action="store_true")
    a = ap.parse_args()

    baseline = a.baseline if a.baseline is not None else gpu_used_mib()
    print(f"[suite] baseline VRAM at suite start: {baseline} MiB  resident health {resident_health()}")
    cabinets = [c for c in a.cabinet.split(",") if c]

    if a.check_admission:
        for name in (ENTRANTS if not a.entrant else [a.entrant]):
            print(f"\n[suite] admission test {name} @ -ngl {a.ngl}")
            lease = start_entrant(name, a.ngl)
            if not lease["ok"]:
                print(f"  ADMISSION FAILED: {lease['reason']}")
                print("  tail:", lease["tail"][-600:].replace("\n", "\n        "))
                if lease.get("proc") is None:
                    print("  (no lease to release)")
                continue
            print(json.dumps(compute_path(lease, name, a.ngl, 8192), indent=1))
            print("  warmup:", json.dumps(warmup()))
            print("  vram pid:", gpu_pid_mib(lease["pid"]), "MiB   total:", gpu_used_mib(), "MiB")
            print("  release:", json.dumps(stop_entrant(lease, baseline)))
        return 0

    if not a.entrant:
        raise SystemExit("--entrant required unless --check-admission")
    summary = []
    for cab in cabinets:
        print(f"\n[suite] {a.entrant} / {cab} @ -ngl {a.ngl} ctx {a.ctx}")
        rec = run_cabinet_block(a.entrant, cab, a.ngl, a.ctx, baseline)
        print(json.dumps({k: rec.get(k) for k in ("admission", "result", "release",
                                                  "vram_during_run_mib")}, indent=1)[:4000])
        summary.append(rec)
    print(f"\n[suite] wrote {len(summary)} meta file(s) under {OUTDIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
