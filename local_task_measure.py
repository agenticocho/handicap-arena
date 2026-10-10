#!/usr/bin/env python3
"""TASK 1 -- CAN A LOCAL MODEL DO A REAL CABINET TASK? Measured by RUNNING its output.

TWO CORRECTIONS TO MY FIRST ATTEMPT, BOTH OF WHICH MADE IT MEASURE NOTHING:

  1  I MEASURED THE WRONG MODEL. The alias `helper` resolves to `LFM2-350M-Extract-Q4_K_M` -- a 350M
     EXTRACTION model, and the very one whose schema-echo I had already diagnosed in the Sokoban run. Its
     output was consistent with what I already knew, so the measurement added nothing. AN ALIAS NAME IS A
     CLAIM UNTIL THE ALIAS MAP IS READ.

  2  MY OWN PROMPT WAS SCHEMA-SHAPED. It listed the API as `name -> signature` LINES, and the model answered
     with a JSON SCHEMA ECHOING THOSE VERY TOKENS. That is the legend defect, in my own measurement prompt.
     The symbols are now described in PROSE SENTENCES, exactly as the cabinet's legend was fixed.

    python3 local_task_measure.py brain critic1
"""
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban as S                                                     # noqa: E402

BASE = "http://127.0.0.1:8080/v1/chat/completions"

PROMPT = """You are writing one small Python function for a Sokoban measurement harness. Reply with the code only, in one fenced block, no explanation.

Three functions are already defined and imported for you. The first parses a level written as text and returns the position it describes. The second takes a position and a single action letter, and returns two things: the position after that action, and a word saying what happened. That word is exactly one of moved, pushed, or blocked. The third takes a position and tells you whether every crate has reached a target. There is also a string named ACTIONS whose characters are the four legal action letters.

Write a function named counters that takes a level as text and a list of tokens, and returns a dictionary with exactly these five keys: moves, blocked, not_an_action, give_up, solved.

The rules are these. A token equal to one of the four action letters, in either case, is an attempt: if the second function says moved or pushed, add one to moves; if it says blocked, add one to blocked. A token equal to RESIGN, exactly and entire, adds one to give_up and ends the token list there. Any other token adds one to not_an_action and changes nothing else. Stop early once the third function says the position is finished. Set solved to that function's answer.
"""

CASES = [("levels/01_one_push.txt", "R"), ("levels/01_one_push.txt", "UUR"),
         ("levels/02_two_boxes.txt", "RRRRDLLLDRRR"), ("levels/02_two_boxes.txt", "RESIGN"),
         ("levels/03_the_corner_waiting.txt", "xyzUR")]


def ask(alias, prompt):
    body = json.dumps({"model": alias, "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": 900, "temperature": 0.0})
    req = urllib.request.Request(BASE, data=body.encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as r:
        j = json.loads(r.read().decode())
    m = (j.get("choices") or [{}])[0].get("message") or {}
    txt = (m.get("content") or "").strip() or (m.get("reasoning_content") or "").strip()
    return txt, round(time.time() - t0, 1), (j.get("usage") or {}).get("completion_tokens", 0)


def code_of(t):
    if "```" not in t:
        return t
    parts = t.split("```")
    best = ""
    for i in range(1, len(parts), 2):
        b = parts[i]
        b = b.split("\n", 1)[1] if b.lower().startswith("python") else b
        if "def counters" in b:
            return b
        best = best or b
    return best


def main():
    aliases = sys.argv[1:] or ["brain", "critic1"]
    print("=" * 100)
    print("TASK 1 -- a real cabinet task, CHECKED BY RUNNING IT against the frozen simulator")
    print("=" * 100)
    for alias in aliases:
        print(f"\n=== alias {alias!r} ===")
        try:
            txt, secs, ctok = ask(alias, PROMPT)
        except Exception as e:                                          # noqa: BLE001
            print(f"  no answer: {type(e).__name__}: {e}")
            continue
        print(f"  {secs}s, {ctok} completion tokens")
        code = code_of(txt)
        ns = {"parse": S.parse, "step": S.step, "solved": S.solved, "ACTIONS": S.ACTIONS}
        try:
            exec(compile(code, "<model>", "exec"), ns)                  # noqa: S102
            fn = ns.get("counters")
            if not callable(fn):
                print(f"  NO counters FUNCTION. It wrote: {txt[:180].replace(chr(10), ' ')}")
                continue
        except Exception as e:                                          # noqa: BLE001
            print(f"  DOES NOT COMPILE: {type(e).__name__}: {e}")
            print(f"   {code[:200].replace(chr(10), ' ')}")
            continue
        bad = 0
        for lv, toks in CASES:
            text = open(lv).read()
            w = S.play(text, list(toks))
            want = {k: w[k] for k in ("moves", "blocked", "not_an_action", "give_up", "solved")}
            try:
                g = fn(text, list(toks))
                got = {k: g.get(k) for k in want} if isinstance(g, dict) else "NOT A DICT"
            except Exception as e:                                      # noqa: BLE001
                got = f"RAISED {type(e).__name__}"
            ok = got == want
            bad += 0 if ok else 1
            print(f"    {os.path.basename(lv):30s} {toks:14s} {'MATCH' if ok else 'DIFFER'}  "
                  f"got={str(got)[:44]}")
            if not ok:
                print(f"      want={want}")
        print(f"  -> {len(CASES) - bad}/{len(CASES)} match the frozen simulator")

    print()
    print("  AND THE HONEST READING: ONE task, ONE sample per alias. It says whether a local model can")
    print("  produce a CHECKABLE function for a cabinet-shaped problem. It does NOT say a local model")
    print("  replaces the API model -- the comparison must be against the artifacts that model produced.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
