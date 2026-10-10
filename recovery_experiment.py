#!/usr/bin/env python3
"""THE RECOVERY EXPERIMENT -- pre-registered in PREREG_recovery.md, committed before this ran.

Asks: is task 2's failure recoverable with a CORRECTIVE TURN? Not a retry -- a retry is a question about luck.
This is a question about whether the model can act on FEEDBACK, which is what an agent loop actually does.

DIFFERS FROM TASK 2 IN EXACTLY ONE THING: a second turn carrying the REAL SyntaxError from compile(), with its
line number and message. No hint about the compound rules, no mention of string literals. THE ERROR MESSAGE IS
THE WHOLE CORRECTION, because that is what an agent loop would actually have.

    python3 recovery_experiment.py [alias]
"""
import hashlib
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban as S                                                     # noqa: E402
import local_task_compare as L                                          # noqa: E402
import local_task2_render as T                                          # noqa: E402
# THE ONE READER OF RECORD (RULING 79) -- imported, never reimplemented.
from answer_reader import read_answer                                   # noqa: E402

ALIAS = sys.argv[1] if len(sys.argv) > 1 else "brain"


def ask_messages(messages, max_tokens=1200):
    """A MULTI-TURN send. The READ still goes through the reader of record -- only the request shape differs."""
    body = json.dumps({"model": ALIAS, "messages": messages, "max_tokens": max_tokens,
                       "temperature": 0.0, "chat_template_kwargs": {"enable_thinking": False}})
    req = urllib.request.Request(L.BASE, data=body.encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=900) as r:
        j = json.loads(r.read().decode())
    ans = read_answer(j)
    ans["secs"] = round(time.time() - t0, 1)
    return ans


def score(code):
    """-> (compiles, matched, total, error_text)"""
    ns = dict(vars(S))
    try:
        exec(compile(code, "<model>", "exec"), ns)                      # noqa: S102
    except SyntaxError as e:
        return (False, 0, 0, f"SyntaxError: {e.msg} (detected at line {e.lineno})\n    {e.text or ''}")
    except Exception as e:                                              # noqa: BLE001
        return (False, 0, 0, f"{type(e).__name__}: {e}")
    fn = ns.get("render_position")
    if not callable(fn):
        return (False, 0, 0, "no render_position function defined")
    cs = T.cases()
    good = 0
    for _name, st, want in cs:
        try:
            if fn(st) == want:
                good += 1
        except Exception:                                               # noqa: BLE001
            pass
    return (True, good, len(cs), None)


def main():
    prompt = T.build_prompt()
    print("=" * 100)
    print("THE RECOVERY EXPERIMENT -- pre-registered, prediction: BRANCH 2 (patches the symptom)")
    print("=" * 100)
    print(f"  alias    {ALIAS}")
    print(f"  setting  enable_thinking=false, temperature 0.0")
    print()

    # ---- TURN 1
    a1 = ask_messages([{"role": "user", "content": prompt}])
    print(f"  TURN 1  {a1['secs']}s  {a1['completion_tokens']} tok  field={a1['field']}")
    if not a1["is_answer"]:
        print(f"  NO ANSWER ON TURN 1 -- {a1.get('why')}. Nothing about recovery is established.")
        return 4
    code1 = L.code_of(a1["text"])
    ok1, good1, total1, err1 = score(code1)
    print(f"          compiles={ok1}  cases={good1}/{total1}")
    if ok1 and good1 == total1:
        print("  TASK 2 SUCCEEDED ON TURN 1 -- there is no failure to recover from. NOT the pre-registered case.")
        return 5
    print(f"          ERROR: {err1}")
    print()

    # ---- TURN 2: THE REAL ERROR, AND NOTHING ELSE
    correction = (f"Your code failed to run. The actual error is:\n\n{err1}\n\n"
                  f"Fix your code so it works. Reply with the corrected code only, in one fenced block.")
    msgs = [{"role": "user", "content": prompt},
            {"role": "assistant", "content": a1["text"]},
            {"role": "user", "content": correction}]
    a2 = ask_messages(msgs)
    print(f"  TURN 2  {a2['secs']}s  {a2['completion_tokens']} tok  field={a2['field']}")
    if not a2["is_answer"]:
        print(f"  NO ANSWER ON TURN 2 -- {a2.get('why')}")
        print(f"  BRANCH 4 -- NO ANSWER. Nothing about recovery is established, and it is reported as that.")
        return 4
    code2 = L.code_of(a2["text"])
    ok2, good2, total2, err2 = score(code2)
    print(f"          compiles={ok2}  cases={good2}/{total2}")
    if err2:
        print(f"          ERROR: {err2}")
    print()

    # ---- THE BRANCH
    if ok2 and good2 == total2:
        branch = ("BRANCH 1 -- RECOVERED. The failure was a slip, not a limit. A LOCAL AGENT IS VIABLE AS A "
                  "NON-ONE-SHOT WORKER: run with a compile-and-feedback loop, never one-shot.")
    elif err2 and "unterminated string literal" in err2:
        branch = (f"BRANCH 2 -- PATCHED THE SYMPTOM. It fixed the line the traceback NAMED and left the SAME "
                  f"CONSTRUCT standing on the other compound rule. IT ACTED ON THE ERROR MESSAGE, NOT ON THE "
                  f"RULE.")
    else:
        branch = (f"BRANCH 3 -- STILL BROKEN, DIFFERENTLY. Feedback reached the code but not the defect.")
    print("=" * 100)
    print(f"  {branch}")
    print("=" * 100)
    print(f"  turn1  compiles={ok1} {good1}/{total1}")
    print(f"  turn2  compiles={ok2} {good2}/{total2}")
    if err1 and err2 and "unterminated string literal" in err1 and "unterminated string literal" in err2:
        print()
        print("  AND THE DISCRIMINATOR, STATED EXACTLY: the error named ONE line, and BOTH compound rules carry")
        print("  the same defect. A model that understood the RULE fixed both; a model that understood the")
        print("  MESSAGE fixed one. The error text above says which.")

    json.dump({"alias": ALIAS, "prediction": "BRANCH 2 -- patches the symptom",
               "turn1": {"field": a1["field"], "tokens": a1["completion_tokens"], "compiles": ok1,
                         "matched": good1, "total": total1, "error": err1},
               "turn2": {"field": a2["field"], "tokens": a2["completion_tokens"], "compiles": ok2,
                         "matched": good2, "total": total2, "error": err2},
               "branch": branch.split(" -- ")[0],
               "code_turn2": code2},
              open(os.path.join(HERE, "probes", "RECOVERY.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
