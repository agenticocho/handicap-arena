#!/usr/bin/env python3
"""MEASURE N -- the reasoning budget the Chair ruled the declaration must rest on.

THE CHAIR'S RULING: reasoning ON, `--reasoning-budget N` with a ceiling above it as a backstop, and
"N GETS MEASURED ON A CABINET CODE TASK BEFORE THE DECLARATION EXISTS. A declaration on a mechanism rather
than a hope."

WHY A BUDGET AND NOT A CEILING, WHICH THIS SCRIPT ALSO SHOWS: the binary's own default is
    --reasoning-budget N   token budget for thinking: -1 for unrestricted, 0 for immediate end, N>0 for budget
                                                                                          (default: -1)
so the seat's shipped state is UNRESTRICTED deliberation with nothing bounding it. The ceiling sweep then fills
whatever ceiling it is given. A budget is the only thing that bounds the thinking INDEPENDENTLY of the answer.

N IS SUPPORTED AT THE SERVER, so this walks N by launching the server once per value with
`LLAMA_ARG_THINK_BUDGET` set -- the env var reaches the same setting without changing the argv the record
already captures, so what is recorded is still what was run.

    python3 measure_reasoning_budget.py
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
import local_task_compare as L                                          # noqa: E402

MODEL = os.path.join(R.MODELS, "Tiel-Inspired-Coder-9B-UD-Q4_K_M.gguf")

# -1 IS THE SHIPPED DEFAULT and is the baseline that must be beaten; 0 is the binary's "immediate end".
BUDGETS = [-1, 0, 256, 512]


def run_one(budget, port):
    """-> (finish_reason, completion_tokens, correctness, wall, raw_head)"""
    env = dict(os.environ)
    env["LLAMA_ARG_THINK_BUDGET"] = str(budget)
    env["SOKOBAN_REASONING_TEST_ARM"] = "on"          # the declaration under test is ON-with-a-budget
    log = os.path.join(HERE, "logs", f"budget_{budget}.log")
    srv = subprocess.Popen(R.server_argv(MODEL, 8192, port), env=env,
                           stdout=open(log, "w"), stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    try:
        t0 = time.time()
        while time.time() - t0 < 600:
            if srv.poll() is not None:
                return ("SERVER_EXITED", None, None, None, f"rc={srv.returncode}")
            try:
                urllib.request.urlopen(base + "/health", timeout=3).read()
                break
            except Exception:                                           # noqa: BLE001
                time.sleep(3)
        else:
            return ("NEVER_STARTED", None, None, None, "")

        payload = {"messages": [{"role": "user", "content": L.PROMPT}],
                   "max_tokens": 4096, "temperature": 0.0}
        req = urllib.request.Request(base + "/v1/chat/completions",
                                     data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        t1 = time.time()
        with urllib.request.urlopen(req, timeout=900) as r:
            j = json.loads(r.read().decode())
        wall = round(time.time() - t1, 1)
        ch = (j.get("choices") or [{}])[0]
        # THE ONE READER OF RECORD (RULING 79). This file previously built its own answer with
        # `content or reasoning_content` and then scored it -- WHICH IS HOW ITS SIBLING REPORTED 5/5 ON A
        # THINKING TRACE.
        from answer_reader import read_answer
        ans = read_answer(j)
        if not ans["is_answer"]:
            return (ans["finish_reason"], ans["completion_tokens"],
                    f"NO ANSWER ({ans['field']})", wall, (ans.get("trace_head") or "")[:70])
        txt = ans["text"]
        ctok = ans["completion_tokens"]
        verdict, good, total = L.score(L.code_of(txt))
        return (ch.get("finish_reason"), ctok, f"{good}/{total} ({verdict})", wall, txt[:70])
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=20)
        except Exception:                                               # noqa: BLE001
            srv.kill()


def main():
    print("=" * 100)
    print("MEASURING N -- the reasoning budget, on a cabinet code task, before the declaration exists")
    print("=" * 100)
    print(f"  model   {os.path.basename(MODEL)}")
    print(f"  digest  {R.model_digest(MODEL)}")
    print(f"  budgets {BUDGETS}   (-1 is the SHIPPED DEFAULT: unrestricted)")
    print()
    rows = []
    port = 8840
    for b in BUDGETS:
        print(f"  N={b:<5} ...", flush=True)
        try:
            fr, ctok, cases, wall, head = run_one(b, port)
        except Exception as e:                                          # noqa: BLE001
            fr, ctok, cases, wall, head = (f"ERROR {type(e).__name__}", None, None, None, "")
        port += 1
        print(f"      finish_reason={fr}  tokens={ctok}  cases={cases}  wall={wall}")
        rows.append({"budget": b, "finish_reason": fr, "completion_tokens": ctok,
                     "cases": cases, "wall_s": wall, "head": head})

    out = os.path.join(HERE, "probes", "REASONING_BUDGET_N.json")
    json.dump({"model": os.path.basename(MODEL), "digest": R.model_digest(MODEL),
               "task": "counters() against a provided API, five cases, temp 0.0, max_tokens 4096",
               "rows": rows}, open(out, "w"), indent=1)

    print()
    print("=" * 100)
    print("  THE MEASUREMENT")
    print("=" * 100)
    print(f"  {'N':>6s} {'finish_reason':>14s} {'tokens':>8s} {'correctness':>22s} {'wall':>7s}")
    for r in rows:
        print(f"  {str(r['budget']):>6s} {str(r['finish_reason']):>14s} {str(r['completion_tokens']):>8s} "
              f"{str(r['cases']):>22s} {str(r['wall_s']):>7s}")
    print()
    good = [r for r in rows if r["cases"] and r["cases"].startswith("5/5")]
    if good:
        bounded = [r for r in good if r["finish_reason"] == "stop"]
        if bounded:
            n = min(r["budget"] for r in bounded)
            print(f"  THE SMALLEST BUDGET THAT WAS BOTH CORRECT AND SELF-TERMINATING: N={n}")
            print(f"  A declaration of N={n} is the first value MEASURED to leave the thinking bounded AND the")
            print("  answer intact on this task. THAT IS THE NUMBER, and it is a number about THIS task.")
        else:
            smallest = min(r["budget"] for r in good)
            print(f"  NO BUDGET PRODUCED A SELF-TERMINATING CORRECT ANSWER. The smallest correct was N={smallest}.")
            print("  SO THE DECLARATION SHOULD NOT BE MADE ON THIS EVIDENCE -- which is itself the finding.")
    else:
        print("  NO BUDGET PRODUCED A CORRECT ANSWER. THE DECLARATION SHOULD NOT BE MADE.")
    print()
    print("  ARTIFACT  probes/REASONING_BUDGET_N.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
