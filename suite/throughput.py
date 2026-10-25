#!/usr/bin/env python3
"""throughput.py — the two clocks, per entrant, on the same served process that plays the cabinets.

The card's instrument note is explicit: server-side prompt-eval and generation rates, and the
client-side rate for the same call, differ by ~12% on this box (HTTP + queueing). A row that does
not say which clock it used is not comparable with a row that used the other. Cabinet harnesses
report client wall time per row; this probe records both clocks for the same served process, so a
row's client figure can be read against the server's own number.

Fixed request: one prompt, temperature 0.0, thinking off, max_tokens 256, one call after a warm-up
(so graph build is not billed to the measurement). Released and verified exactly like a cabinet run.
"""
import argparse
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S  # noqa: E402

PROMPT = ("Write the integers from 1 to 60 in order, separated by single spaces, "
          "and nothing else.")


def call(max_tokens=256):
    body = json.dumps({"model": "probe", "messages": [{"role": "user", "content": PROMPT}],
                       "temperature": 0.0, "max_tokens": max_tokens,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(f"{S.BASE}/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read())
    wall = time.time() - t0
    usage = d.get("usage") or {}
    timings = d.get("timings") or {}
    return {"client_wall_s": round(wall, 3),
            "client_completion_tokens": usage.get("completion_tokens"),
            "client_tok_per_s": (round((usage.get("completion_tokens") or 0) / wall, 2) if wall else None),
            "server_predicted_tok_per_s": timings.get("predicted_per_second"),
            "server_prompt_tok_per_s": timings.get("prompt_per_second"),
            "server_predicted_n": timings.get("predicted_n"),
            "server_prompt_n": timings.get("prompt_n"),
            "finish_reason": d["choices"][0].get("finish_reason"),
            "content_head": (d["choices"][0]["message"].get("content") or "")[:80]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrant", required=True)
    ap.add_argument("--ngl", type=int, default=99)
    ap.add_argument("--ctx", type=int, default=8192)
    a = ap.parse_args()
    baseline = S.gpu_used_mib()
    lease = S.start_entrant(a.entrant, a.ngl, a.ctx)
    if not lease["ok"]:
        print(json.dumps({"entrant": a.entrant, "admission": "FAILED", "detail": lease.get("tail", "")[-600:]}, indent=1))
        return 1
    rec = {"entrant": a.entrant, "at": S.now(), "baseline_mib": baseline,
           "compute_path": S.compute_path(lease, a.entrant, a.ngl, a.ctx)}
    try:
        rec["warmup"] = S.warmup()
        rec["call"] = call()
        rec["vram_pid_mib"] = S.gpu_pid_mib(lease["pid"])
        rec["vram_total_mib"] = S.gpu_used_mib()
    finally:
        rec["release"] = S.stop_entrant(lease, baseline)
    out = os.path.join(S.ROOT, "suite", "runs", f"throughput_{a.entrant}.json")
    with open(out, "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps({k: rec[k] for k in ("entrant", "warmup", "call", "release",
                                          "vram_pid_mib", "vram_total_mib")}, indent=1))
    print(f"[throughput] wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
