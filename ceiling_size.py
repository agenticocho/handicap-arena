#!/usr/bin/env python3
"""CEILING SIZING -- the Chair's first condition, measured instead of guessed.

THE CHAIR'S RULING was ON-with-a-ceiling for a code-writing cabinet, WITH TWO CONDITIONS:
  1  THE CEILING IS SIZED SO `finish_reason` IS NOT `length` -- because a cut deliberation IS
     `capped-deliberation-missing-value`, which is the failure this cabinet already published once.
  2  it is declared with its rationale rather than defaulted.

CONDITION 2 IS FREE. CONDITION 1 IS A NUMBER, AND A NUMBER PICKED BY FEELING IS A DEFAULT WEARING A
DECISION'S CLOTHES. So the ceiling is SWEPT on the same task at the same temperature and the arm's
`finish_reason` is read, not predicted.

    python3 ceiling_size.py brain
"""
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban as S                                                     # noqa: E402
import local_task_compare as L                                          # noqa: E402

CEILINGS = [1200, 2048, 4096]


def ask(alias, prompt, ceiling):
    payload = {"model": alias, "messages": [{"role": "user", "content": prompt}],
               "max_tokens": ceiling, "temperature": 0.0}
    req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=1200) as r:
        j = json.loads(r.read().decode())
    ch = (j.get("choices") or [{}])[0]
    m = ch.get("message") or {}
    txt = (m.get("content") or "").strip() or (m.get("reasoning_content") or "").strip()
    return txt, ch.get("finish_reason"), (j.get("usage") or {}).get("completion_tokens", 0), round(time.time() - t0, 1)


def main():
    alias = sys.argv[1] if len(sys.argv) > 1 else "brain"
    print("=" * 100)
    print(f"CEILING SIZING -- alias {alias!r}, same task, same temperature 0.0, ceiling swept")
    print("=" * 100)
    rows = []
    for c in CEILINGS:
        print(f"\n  ceiling {c} ...", flush=True)
        try:
            txt, fr, ctok, secs = ask(alias, L.PROMPT, c)
        except Exception as e:                                          # noqa: BLE001
            print(f"    no answer: {type(e).__name__}: {e}")
            rows.append((c, "NO ANSWER", None, None, None))
            continue
        verdict, good, total = L.score(L.code_of(txt))
        print(f"    finish_reason={fr}  {ctok} tokens  {secs}s  -> {verdict} {good}/{total}")
        rows.append((c, fr, ctok, f"{good}/{total}", secs))

    print()
    print("=" * 100)
    print("  THE SWEEP")
    print("=" * 100)
    print(f"  {'ceiling':>8s} {'finish_reason':>14s} {'tokens used':>12s} {'cases':>7s} {'wall':>7s}")
    for c, fr, ctok, cases, secs in rows:
        print(f"  {c:>8d} {str(fr):>14s} {str(ctok):>12s} {str(cases):>7s} {str(secs):>7s}")
    print()
    cut = [r for r in rows if r[1] == "length"]
    ok = [r for r in rows if r[1] == "stop"]
    if ok:
        smallest_ok = min(r[0] for r in ok)
        largest_cut = max([r[0] for r in cut], default=None)
        print(f"  THE SMALLEST CEILING THAT DID NOT GET CUT: {smallest_ok}")
        if largest_cut is not None:
            print(f"  AND THE LARGEST THAT DID: {largest_cut}  -- so the boundary is between them, and a")
            print(f"  declaration of {smallest_ok} is the first value MEASURED not to truncate THIS task.")
        print()
        print("  AND THE HONEST LIMIT: THIS IS ONE TASK. A ceiling measured not to truncate one code task is")
        print("  evidence about that task, NOT a safe constant for every cabinet job -- a longer task needs")
        print("  its own sweep. What it DOES establish is that `length` is DETECTABLE and the boundary is")
        print("  reachable, which is what makes the condition enforceable rather than aspirational.")
    else:
        print("  NO CEILING IN THE SWEEP PRODUCED finish_reason=stop. The condition cannot be met by raising")
        print("  the ceiling on this task -- THE DECLARATION SHOULD NOT BE MADE, and this is the finding.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
