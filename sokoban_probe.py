#!/usr/bin/env python3
"""THE ONE-TOKEN PROBE, RUN TWICE: SAME WEIGHTS, REASONING OFF AND ON.

This is the two-second test, executed rather than described. It answers the question the Chair's finding
raises for OUR cabinets: is the 64-token ceiling being eaten by reasoning, and does the launch flag change it?

    python3 sokoban_probe.py granite-3.3-2b-instruct-critical-thinking.Q5_K_M.gguf
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban_run as R                                                 # noqa: E402

QA = [
    ("2 + 2? just the number", "What is 2 + 2? Reply with just the number and nothing else."),
    ("one letter", "Reply with exactly one character and nothing else: the letter A."),
]


def serve(entrant, reasoning, port):
    argv = ([R.LLAMA, "-m", entrant, "-c", "4096", "-ngl", "0", "--port", str(port), "--no-webui",
             "--reasoning", reasoning])
    log = os.path.join(HERE, "logs", f"PROBE_{os.path.basename(entrant)[:24]}_{reasoning}.log")
    os.makedirs(os.path.dirname(log), exist_ok=True)
    proc = subprocess.Popen(argv, stdout=open(log, "w"), stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    t0 = time.time()
    while time.time() - t0 < 600:
        if proc.poll() is not None:
            return None, f"server exited rc={proc.returncode}", proc
        try:
            urllib.request.urlopen(base + "/health", timeout=3).read()
            return base, None, proc
        except Exception:                                               # noqa: BLE001
            time.sleep(3)
    return None, "no /health in 600 s", proc


def ask(base, q, max_tokens):
    body = json.dumps({"messages": [{"role": "user", "content": q}], "max_tokens": max_tokens,
                       "temperature": 0.0})
    req = urllib.request.Request(base + "/v1/chat/completions", data=body.encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        j = json.loads(r.read().decode())
    ch = (j.get("choices") or [{}])[0]
    msg = ch.get("message") or {}
    return {"content": (msg.get("content") or "").strip(),
            "reasoning_content_len": len((msg.get("reasoning_content") or "")),
            "completion_tokens": (j.get("usage") or {}).get("completion_tokens", 0),
            "finish_reason": ch.get("finish_reason")}


def main():
    ent = sys.argv[1] if len(sys.argv) > 1 else "granite-3.3-2b-instruct-critical-thinking.Q5_K_M.gguf"
    p = ent if os.path.exists(ent) else os.path.join(R.MODELS, ent)
    if not os.path.exists(p):
        print(f"  ENTRANT ABSENT: {ent}")
        return 2
    port = 8790
    print("=" * 100)
    print("THE ONE-TOKEN PROBE -- same weights, reasoning OFF then ON")
    print("=" * 100)
    print(f"  entrant {os.path.basename(p)}")
    print(f"  ceilings tested: 64 (the cabinet's current) and {R.MAX_TOKENS} (same)")
    print()

    results = {}
    for reasoning in ("off", "on"):
        base, err, proc = serve(p, reasoning, port)
        port += 1
        if err:
            print(f"  reasoning {reasoning:3s}  DID NOT START -- {err}")
            results[reasoning] = None
            continue
        print(f"  reasoning {reasoning:3s}  (the flag passed: --reasoning {reasoning})")
        for label, q in QA:
            for cap in (64, 512):
                try:
                    r = ask(base, q, cap)
                except Exception as e:                                  # noqa: BLE001
                    print(f"      {label:22s} cap {cap:4d}  ERROR {type(e).__name__}")
                    continue
                capped = r["finish_reason"] == "length"
                print(f"      {label:22s} cap {cap:4d}  tokens {r['completion_tokens']:4d}  "
                      f"finish {str(r['finish_reason']):8s} {'CAPPED' if capped else '':8s} "
                      f"content={r['content'][:28]!r} reasoning_field={r['reasoning_content_len']}B")
        results[reasoning] = True
        proc.terminate()
        try:
            proc.wait(timeout=30)
        except Exception:                                               # noqa: BLE001
            proc.kill()
        print()

    print("  READ IT THIS WAY: if a one-token question costs hundreds of tokens with reasoning ON and one or")
    print("  two with it OFF, then THE SETTING IS THE CAUSE and a 64-token ceiling measures the DELIBERATION")
    print("  rather than the ANSWER. That is the difference between 'could not answer' and 'was cut off'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
