#!/usr/bin/env python3
"""TASK 1, THE COMPARISON -- one local alias, one real cabinet task, TWO REASONING SETTINGS.

MY FIRST TWO ATTEMPTS WERE BOTH INVALID, AND BOTH BECAUSE OF MY OWN INSTRUMENT:

  ATTEMPT 1  measured `helper` -- WHICH IS `LFM2-350M-Extract`, a 350M extraction model, not the 9B the
             Chair named. AN ALIAS NAME IS A CLAIM UNTIL THE ALIAS MAP IS READ. And my prompt listed the API
             as `name -> signature` lines, which is SCHEMA-SHAPED, and the model answered with a JSON schema
             echoing those tokens -- the legend defect, in my own measuring instrument.

  ATTEMPT 2  fixed the aliases, rewrote the prompt in prose -- AND OVERCORRECTED: I described the three
             functions in sentences and NEVER NAMED THEM, so the model could not call anything and every case
             raised NameError. Removing the schema shape must not remove the necessary information.

  THIS RUN   names the functions and describes them IN PROSE SENTENCES. Names are information; key-value
             LAYOUT is the trap. And it runs the SAME model twice, differing in exactly one thing: whether
             the chat template is asked to think.

AND THE FINDING THAT MOTIVATES THE COMPARISON: NO LOCAL ALIAS SETS --reasoning. Checked in the seat
definition, not recalled. So all four seats serve at the default, and the default is where Qwen burned 900
tokens on a thinking trace and produced nothing that compiles.

    python3 local_task_compare.py brain
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

Three functions are already defined and imported in the module you are writing into, and you call them by these exact names.

The function `parse` takes a level written as text and returns the position that text describes.

The function `step` takes a position and a single action letter, and returns two things: the position after that action, and a word saying what happened. That word is exactly one of moved, pushed, or blocked.

The function `solved` takes a position and tells you whether every crate has reached a target.

There is also a module-level string named `ACTIONS` whose characters are the four legal action letters.

Now write a function named `counters` that takes a level as text and a list of tokens, and returns a dictionary with exactly these five keys: moves, blocked, not_an_action, give_up, solved.

The rules are these. A token equal to one of the four action letters, in either case, is an attempt: if `step` says moved or pushed, add one to moves; if it says blocked, add one to blocked. A token equal to RESIGN, exactly and entire, adds one to give_up and ends the token list there. Any other token adds one to not_an_action and changes nothing else. Stop early once `solved` says the position is finished. Set solved to what `solved` returns.
"""

CASES = [("levels/01_one_push.txt", "R"), ("levels/01_one_push.txt", "UUR"),
         ("levels/02_two_boxes.txt", "RRRRDLLLDRRR"), ("levels/02_two_boxes.txt", "RESIGN"),
         ("levels/03_the_corner_waiting.txt", "xyzUR")]


def ask(alias, prompt, think_off):
    payload = {"model": alias, "messages": [{"role": "user", "content": prompt}],
               "max_tokens": 1200, "temperature": 0.0}
    # THE ONE THING THAT VARIES. `enable_thinking` is the chat-template switch the Qwen-family template reads;
    # the A/B showed the equivalent server-side flag is the difference between an answer and an empty cell.
    if think_off:
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    req = urllib.request.Request(BASE, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=900) as r:
        j = json.loads(r.read().decode())
    m = (j.get("choices") or [{}])[0].get("message") or {}
    txt = (m.get("content") or "").strip() or (m.get("reasoning_content") or "").strip()
    fr = (j.get("choices") or [{}])[0].get("finish_reason")
    return txt, round(time.time() - t0, 1), (j.get("usage") or {}).get("completion_tokens", 0), fr


def code_of(t):
    if "```" not in t:
        return t
    parts, best = t.split("```"), ""
    for i in range(1, len(parts), 2):
        b = parts[i]
        b = b.split("\n", 1)[1] if b.lower().startswith("python") else b
        if "def counters" in b:
            return b
        best = best or b
    return best


def score(code):
    ns = {"parse": S.parse, "step": S.step, "solved": S.solved, "ACTIONS": S.ACTIONS}
    try:
        exec(compile(code, "<model>", "exec"), ns)                      # noqa: S102
    except Exception as e:                                              # noqa: BLE001
        return f"DOES NOT COMPILE ({type(e).__name__})", 0, 0
    fn = ns.get("counters")
    if not callable(fn):
        return "no counters function", 0, 0
    bad = 0
    for lv, toks in CASES:
        text = open(os.path.join(HERE, lv)).read()
        w = S.play(text, list(toks))
        want = {k: w[k] for k in ("moves", "blocked", "not_an_action", "give_up", "solved")}
        try:
            g = fn(text, list(toks))
            got = {k: g.get(k) for k in want} if isinstance(g, dict) else "NOT A DICT"
        except Exception as e:                                          # noqa: BLE001
            got = f"RAISED {type(e).__name__}"
        if got != want:
            bad += 1
    return "compiles", len(CASES) - bad, len(CASES)


def main():
    alias = sys.argv[1] if len(sys.argv) > 1 else "brain"
    print("=" * 100)
    print(f"TASK 1 COMPARISON -- alias {alias!r}, one real cabinet task, thinking default vs thinking off")
    print("=" * 100)
    rows = []
    for label, think_off in (("thinking DEFAULT (shipped setting)", False),
                             ("thinking OFF (enable_thinking=false)", True)):
        print(f"\n=== {label} ===")
        try:
            txt, secs, ctok, fr = ask(alias, PROMPT, think_off)
        except Exception as e:                                          # noqa: BLE001
            print(f"  no answer: {type(e).__name__}: {e}")
            rows.append((label, "NO ANSWER", 0, 0, None))
            continue
        code = code_of(txt)
        verdict, good, total = score(code)
        print(f"  {secs}s  {ctok} completion tokens  finish_reason={fr}")
        print(f"  first 100 chars: {txt[:100]!r}")
        print(f"  -> {verdict}: {good}/{total} cases match the frozen simulator")
        rows.append((label, verdict, good, total, ctok))
    print()
    print("=" * 100)
    print("  THE COMPARISON")
    print("=" * 100)
    print(f"  {'setting':38s} {'verdict':26s} {'cases':>8s} {'tokens':>8s}")
    for label, verdict, good, total, ctok in rows:
        print(f"  {label:38s} {verdict:26s} {str(good) + '/' + str(total):>8s} {str(ctok):>8s}")
    print()
    print("  AND THE HONEST READING: ONE alias, ONE task, ONE sample per setting. A measurement of the")
    print("  INSTRUMENT as much as of the model -- my first two attempts were invalid because of MY prompt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
