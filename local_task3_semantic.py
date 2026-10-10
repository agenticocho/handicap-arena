#!/usr/bin/env python3
"""TASK 3 -- A SEMANTIC DEFECT CLASS. Pre-registered in PREREG_task3_semantic.md, committed before this ran.

TASK 2'S DEFECT WAS SYNTACTIC: a compiler caught it, a traceback named the line, nothing ran.
TASK 3'S DEFECT IS SEMANTIC: IT COMPILES, IT RUNS, AND THE NUMBER IS WRONG. Nothing names the line, because
nothing is broken in Python's eyes. THIS IS THE CLASS THE CABINET FEARS -- a wrong value that every downstream
artefact inherits silently.

SO THE QUESTION IS NOT "can the model write code". IT IS: WHEN THE FEEDBACK IS A WRONG VALUE RATHER THAN AN
ERROR, DOES RECOVERY STILL WORK?

    python3 local_task3_semantic.py [alias]
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
from answer_reader import read_answer                                   # noqa: E402

ALIAS = sys.argv[1] if len(sys.argv) > 1 else "brain"
_MOVES = ((1, 0), (-1, 0), (0, 1), (0, -1))


def reference(st):
    """THE INDEPENDENT ORACLE -- a flood fill written HERE, from the FROZEN state, never from the model's output.

    It is deliberately NOT the cabinet's own dead-end mapper: an oracle taken from the thing being scored is not
    an oracle. It reads only `walls`, `boxes`, `player`, `rows`, `cols` -- the same frozen fields the model gets.
    """
    walls, boxes = set(st["walls"]), set(st["boxes"])
    start = st["player"]
    seen, stack = {start}, [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in _MOVES:
            n = (r + dr, c + dc)
            if n in seen or n in walls or n in boxes:
                continue
            if not (0 <= n[0] < st["rows"] and 0 <= n[1] < st["cols"]):
                continue
            seen.add(n)
            stack.append(n)
    return seen


PROMPT = f"""You are writing one small Python function for a Sokoban measurement harness. Reply with the code only, in one fenced block, no explanation.

A position is already parsed for you and arrives as a dictionary with these keys, and you may read them directly.

There is a key named walls holding a set of coordinate pairs, one for each solid wall cell.
There is a key named boxes holding a set of coordinate pairs, one for each crate.
There is a key named targets holding a set of coordinate pairs, one for each target square.
There is a key named player holding a single coordinate pair, the player's cell.
There is a key named rows holding the number of rows as an integer.
There is a key named cols holding the number of columns as an integer.

Coordinates are pairs written row first, then column, and rows and columns both count from zero. Every cell of the grid lies within those bounds.

Write a function named reachable_cells that takes a position and returns a SET of coordinate pairs: every cell the player could reach by walking, starting from the player's own cell, moving one cell at a time up, down, left or right, and without moving any crate.

The player's own starting cell counts as reachable, so it is in the answer. A wall cell is not reachable.
"""


def cases():
    """22 goldens: every intermediate state of the three verified solutions, plus the three initial boards."""
    out = []
    for lv in ("levels/01_one_push.txt", "levels/02_two_boxes.txt", "levels/03_the_corner_waiting.txt"):
        st = S.parse(open(os.path.join(HERE, lv)).read())
        out.append((f"{os.path.basename(lv)}:initial", st, reference(st)))
        cur = st
        for i, a in enumerate(VERIFIED[os.path.basename(lv)]):
            nxt, outcome = S.step(cur, a)
            if outcome in ("moved", "pushed"):
                cur = nxt
            out.append((f"{os.path.basename(lv)}:after {VERIFIED[os.path.basename(lv)][:i + 1]}",
                        cur, reference(cur)))
    return out


VERIFIED = {"01_one_push.txt": "R", "02_two_boxes.txt": "RRRRDLLLDRRR",
            "03_the_corner_waiting.txt": "RULDLU"}


def ask_messages(messages, max_tokens=1200):
    body = json.dumps({"model": ALIAS, "messages": messages, "max_tokens": max_tokens,
                       "temperature": 0.0, "chat_template_kwargs": {"enable_thinking": False}})
    req = urllib.request.Request(L.BASE, data=body.encode(), headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=900) as r:
        j = json.loads(r.read().decode())
    ans = read_answer(j)                            # RULING 79: the reader of record, imported.
    ans["secs"] = round(time.time() - t0, 1)
    return ans


def score(code, cs):
    """-> (compiles, matched, total, disagreements). A DISAGREEMENT IS THE FEEDBACK -- a wrong value, no traceback."""
    ns = dict(vars(S))
    try:
        exec(compile(code, "<model>", "exec"), ns)                      # noqa: S102
        fn = ns.get("reachable_cells")
        if not callable(fn):
            return (False, 0, len(cs), ["no reachable_cells function defined"])
    except Exception as e:                                              # noqa: BLE001
        return (False, 0, len(cs), [f"{type(e).__name__}: {e}"])
    good, dis = 0, []
    for name, st, want in cs:
        try:
            got = fn(st)
            got_set = set(map(tuple, got)) if got is not None else None
        except Exception as e:                                          # noqa: BLE001
            got_set = None
            dis.append(f"{name}: RAISED {type(e).__name__}")
            continue
        if got_set == want:
            good += 1
        elif len(dis) < 4:
            extra = sorted(got_set - want) if got_set else []
            missing = sorted(want - got_set) if got_set else []
            dis.append(f"{name}: got {len(got_set) if got_set is not None else '?'} cells, want {len(want)}"
                       f"{'; EXTRA ' + str(extra[:4]) if extra else ''}"
                       f"{'; MISSING ' + str(missing[:4]) if missing else ''}")
    return (True, good, len(cs), dis)


def main():
    cs = cases()
    print("=" * 100)
    print("TASK 3 -- SEMANTIC DEFECT CLASS. Prediction: BRANCH 2 (fails one-shot, recovers on the report)")
    print("=" * 100)
    print(f"  alias    {ALIAS}")
    print(f"  setting  enable_thinking=false, temperature 0.0")
    print(f"  cases    {len(cs)}  (independent flood-fill oracle, computed from the frozen state)")
    print()

    a1 = ask_messages([{"role": "user", "content": PROMPT}])
    print(f"  ONE-SHOT  {a1['secs']}s  {a1['completion_tokens']} tok  field={a1['field']}")
    if not a1["is_answer"]:
        print(f"  NO ANSWER -- {a1.get('why')}   BRANCH 5")
        return 5
    code1 = L.code_of(a1["text"])
    ok1, good1, total, dis1 = score(code1, cs)
    print(f"            compiles={ok1}  {good1}/{total}")
    for d in dis1[:3]:
        print(f"            {d}")
    if ok1 and good1 == total:
        print()
        print("  BRANCH 1 -- PASSES ONE-SHOT. *** THE BRANCH I SAID WOULD EMBARRASS ME. ***")
        print("  MY NON-ONE-SHOT FRAMING IS UNNECESSARY FOR THIS CLASS.")
        json.dump({"branch": "BRANCH 1", "one_shot": f"{good1}/{total}", "tokens": a1["completion_tokens"]},
                  open(os.path.join(HERE, "probes", "TASK3_SEMANTIC.json"), "w"), indent=1)
        return 0

    # ---- THE CORRECTIVE TURN: A WRONG VALUE, NOT AN ERROR. Nothing names a line.
    report = "\n".join(f"  {d}" for d in dis1[:4])
    correction = ("Your function ran without errors but returns the wrong answer. The checker compared your "
                  "result against an independent implementation on every test case and reports:\n\n"
                  f"{report}\n\nEach line is one board, the number of cells you returned, the number the "
                  "checker expected, and which cells differ. Fix your code so it agrees on every case. "
                  "Reply with the corrected code only, in one fenced block.")
    print()
    print("  ---- THE CORRECTIVE TURN CARRIES THE DISAGREEMENT, NOT A TRACEBACK ----")
    for ln in report.splitlines():
        print(f"    {ln}")
    a2 = ask_messages([{"role": "user", "content": PROMPT},
                       {"role": "assistant", "content": a1["text"]},
                       {"role": "user", "content": correction}])
    print()
    print(f"  WITH FEEDBACK  {a2['secs']}s  {a2['completion_tokens']} tok  field={a2['field']}")
    if not a2["is_answer"]:
        print(f"  NO ANSWER ON TURN 2 -- {a2.get('why')}   BRANCH 5")
        return 5
    code2 = L.code_of(a2["text"])
    ok2, good2, total2, dis2 = score(code2, cs)
    print(f"                 compiles={ok2}  {good2}/{total2}")
    for d in dis2[:3]:
        print(f"                 {d}")
    print()
    print("=" * 100)
    if ok2 and good2 == total2:
        print("  BRANCH 2 -- FAILS ONE-SHOT, RECOVERS ON THE CHECKER'S REPORT.")
        print("  Recovery generalises from a traceback to a WRONG VALUE.")
        br = "BRANCH 2"
    elif good2 > good1:
        print("  BRANCH 3 -- PARTIAL: it improved the reported cases without fixing the rule.")
        print("  IN A SEMANTIC CLASS A PARTIAL FIX SHIPS. This is the dangerous branch.")
        br = "BRANCH 3"
    else:
        print("  BRANCH 4 -- FAILS, AND THE FEEDBACK DID NOT FIX IT.")
        br = "BRANCH 4"
    print("=" * 100)
    print(f"  one-shot      {good1}/{total}")
    print(f"  with feedback {good2}/{total2}")
    json.dump({"branch": br, "one_shot": f"{good1}/{total}", "with_feedback": f"{good2}/{total2}",
               "disagreements_one_shot": dis1[:4], "disagreements_after": dis2[:4],
               "tokens": [a1["completion_tokens"], a2["completion_tokens"]]},
              open(os.path.join(HERE, "probes", "TASK3_SEMANTIC.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
