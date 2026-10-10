#!/usr/bin/env python3
"""RECOVERY ON A SEMANTIC DEFECT CLASS -- pre-registered in PREREG_recovery_semantic.md, committed as 61fc1db.

Task 3 passed ONE-SHOT, so recovery was never tested on a class where the compiler stays silent. This asks it
properly: BFS over STATES for the minimum number of moves to solve a level. WRONG ANSWERS COMPILE AND RETURN A
NUMBER.

Method: one-shot, then -- only if it fails -- ONE corrective turn carrying the checker's disagreement. The
reader of record is imported (ruling 79); thinking is off (the re-taken ruling), sent as the chat-template switch.

    python3 recovery_semantic.py [alias]
"""
import collections
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
LEVELS = ["levels/01_one_push.txt", "levels/02_two_boxes.txt", "levels/03_the_corner_waiting.txt"]
PUBLISHED = {"01_one_push.txt": 1, "02_two_boxes.txt": 12, "03_the_corner_waiting.txt": 6}


def oracle(level_text, cap=400000):
    """MY OWN BFS, from the FROZEN transition function. Independent of the model AND of the cabinet's solver.

    State = (player, frozenset(boxes)). A move is one player step, pushing or not -- so PUSHES and MOVES are
    different units, which is trap 1 in the prereg. Bounded, so it cannot hang.
    """
    st = S.parse(level_text)
    start = (st["player"], frozenset(st["boxes"]))
    targets = frozenset(st["targets"])
    if frozenset(st["boxes"]) == targets:
        return 0
    seen = {start}
    q = collections.deque([(start, 0)])
    expanded = 0
    while q and expanded < cap:
        (player, boxes), d = q.popleft()
        expanded += 1
        cur = dict(st, player=player, boxes=set(boxes))
        for a in S.ACTIONS:
            nxt, outcome = S.step(cur, a)
            if outcome not in ("moved", "pushed"):
                continue
            s2 = (nxt["player"], frozenset(nxt["boxes"]))
            if s2 in seen:
                continue
            if frozenset(nxt["boxes"]) == targets:
                return d + 1
            seen.add(s2)
            q.append((s2, d + 1))
    return None


PROMPT = """You are writing one small Python function for a Sokoban measurement harness. Reply with the code only, in one fenced block, no explanation.

The position is already parsed and arrives as a dictionary with these keys, and you may read them directly: walls holds a set of coordinate pairs, one for each solid wall cell. boxes holds a set of coordinate pairs, one for each crate. targets holds a set of coordinate pairs, one for each target square. player holds a single coordinate pair, the player's cell. rows and cols hold the grid size as integers. Coordinates are pairs written row first then column, counting from zero.

Four things are already defined in the module you are writing into, and you call them by these exact names.

The function `parse` takes a level written as text and returns the position it describes.

The function `step` takes a position and a single action letter, and returns two things: the position after that action, and a word saying what happened. That word is exactly one of moved, pushed, or blocked. A step that is blocked leaves the position unchanged.

The function `solved` takes a position and tells you whether every crate has reached a target.

The string `ACTIONS` contains the four legal action letters, one character each.

Write a function named `min_moves` that takes a position and returns an integer: the FEWEST number of player actions needed to reach a position where every crate is on a target. The position you are given is guaranteed to be solvable, so you never need to report that it cannot be done.

One action is one call to `step` with one letter. An action that pushes a crate counts as exactly one action, the same as an action that does not.
"""


def ask_messages(messages, max_tokens=1600):
    body = json.dumps({"model": ALIAS, "messages": messages, "max_tokens": max_tokens,
                       "temperature": 0.0, "chat_template_kwargs": {"enable_thinking": False}})
    req = urllib.request.Request(L.BASE, data=body.encode(), headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=900) as r:
        j = json.loads(r.read().decode())
    ans = read_answer(j)                            # RULING 79: the reader of record, imported.
    ans["secs"] = round(time.time() - t0, 1)
    return ans


def score(code, goldens):
    """-> (compiles, matched, total, disagreements). For a SEMANTIC class the disagreement IS a wrong integer."""
    ns = dict(vars(S))
    try:
        exec(compile(code, "<model>", "exec"), ns)                      # noqa: S102
        fn = ns.get("min_moves")
        if not callable(fn):
            return (False, 0, len(goldens), ["no min_moves function defined"])
    except Exception as e:                                              # noqa: BLE001
        return (False, 0, len(goldens), [f"{type(e).__name__}: {e}"])
    good, dis = 0, []
    for name, st, want in goldens:
        try:
            got = fn(dict(st))
        except Exception as e:                                          # noqa: BLE001
            # THE MESSAGE, NOT JUST THE TYPE. My first version sent the model "RAISED ValueError" and nothing
            # else -- INFORMATIONALLY EMPTY FEEDBACK, so the corrective turn gave it nothing to act on and the
            # run measured my channel rather than its recovery. THE PREREG SAID THE TURN CARRIES THE CHECKER'S
            # DISAGREEMENT, and an exception message IS the disagreement.
            dis.append(f"{name}: your call raised {type(e).__name__}: {e}")
            continue
        if got == want:
            good += 1
        else:
            dis.append(f"{name}: you returned {got}, the checker's independent search found {want}")
    return (True, good, len(goldens), dis)


def main():
    goldens = []
    for lv in LEVELS:
        text = open(os.path.join(HERE, lv)).read()
        n = oracle(text)
        pub = PUBLISHED[os.path.basename(lv)]
        goldens.append((os.path.basename(lv), S.parse(text), n))
        flag = "AGREES" if n == pub else f"*** DISAGREES WITH THE PUBLISHED {pub} ***"
        print(f"  oracle {os.path.basename(lv):30s} {n} moves   {flag}")
    print()

    a1 = ask_messages([{"role": "user", "content": PROMPT}])
    print(f"  ONE-SHOT  {a1['secs']}s  {a1['completion_tokens']} tok  field={a1['field']}")
    if not a1["is_answer"]:
        print(f"  NO ANSWER -- {a1.get('why')}   BRANCH Z")
        return 5
    code1 = L.code_of(a1["text"])
    ok1, good1, total, dis1 = score(code1, goldens)
    print(f"            compiles={ok1}  {good1}/{total}")
    for d in dis1[:3]:
        print(f"            {d}")
    if ok1 and good1 == total:
        print()
        print("  BRANCH P -- PASSES ONE-SHOT. *** THE BRANCH I WROTE DOWN AS THE ONE I WOULD BE EMBARRASSED BY. ***")
        print("  The semantic class did not trip it. My emphasis on the compiling-wrong-answer class would have")
        print("  TWO NULLS behind it, one of them an experiment written specifically to produce a failure.")
        json.dump({"branch": "BRANCH P", "one_shot": f"{good1}/{total}", "oracle": [g[2] for g in goldens]},
                  open(os.path.join(HERE, "probes", "RECOVERY_SEMANTIC.json"), "w"), indent=1)
        return 0

    report = "\n".join(f"  {d}" for d in dis1[:4])
    correction = ("Your function ran without errors but returns a wrong answer. The checker solved each level "
                  "independently and compared:\n\n" + report +
                  "\n\nEach line is one level, what you returned, and what an independent search found. Fix your "
                  "code so it agrees on every level. Reply with the corrected code only, in one fenced block.")
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
        print(f"  NO ANSWER ON TURN 2 -- {a2.get('why')}   BRANCH Z")
        return 5
    code2 = L.code_of(a2["text"])
    ok2, good2, total2, dis2 = score(code2, goldens)
    print(f"                 compiles={ok2}  {good2}/{total2}")
    for d in dis2[:3]:
        print(f"                 {d}")
    print()
    if ok2 and good2 == total2:
        print("  BRANCH F -- FAILED ONE-SHOT WITH A WRONG INTEGER, RECOVERED ON THE CHECKER'S DISAGREEMENT.")
        print("  Recovery generalises from a traceback to a WRONG VALUE. The non-one-shot worker pattern holds")
        print("  across two defect classes.")
        br = "BRANCH F"
    elif good2 > good1:
        print("  BRANCH S -- PATCHED THE REPORTED CASE ONLY. *** THE DANGEROUS ONE -- IN A SEMANTIC CLASS IT SHIPS. ***")
        br = "BRANCH S"
    else:
        print("  BRANCH N -- FAILED, AND THE FEEDBACK DID NOT FIX IT.")
        br = "BRANCH N"
    print(f"  one-shot {good1}/{total}   with feedback {good2}/{total2}")
    # THE CODE, INTO THE RECORD. This is the gap I declared rather than claimed when this experiment first ran:
    # the artifact carried tokens, field, disagreements and verdict -- AND NOT WHAT THE MODEL WROTE, so
    # "it ignored the correction" and "it tried and failed" were INDISTINGUISHABLE, and the mechanism behind
    # Branch N was INFERRED rather than measured. One line, and the next run's mechanism is checkable.
    #
    # It closes the same hole ruling 82 closed, in the other direction: there, the FAILURE path wrote no record;
    # here, the record omits the ARTEFACT THE VERDICT IS ABOUT. Both are the failure path being the one where
    # the record matters most.
    json.dump({"branch": br, "one_shot": f"{good1}/{total}", "with_feedback": f"{good2}/{total2}",
               "disagreements_one_shot": dis1[:4], "disagreements_after": dis2[:4],
               "oracle": {g[0]: g[2] for g in goldens},
               "code_one_shot": code1, "code_after_feedback": code2,
               "code_changed_between_turns": code1.strip() != code2.strip(),
               "code_note": "THE MODEL'S CODE, so 'ignored the correction' and 'tried and failed' are "
                            "DISTINGUISHABLE. Without this the mechanism behind a failed branch is inferred."},
              open(os.path.join(HERE, "probes", "RECOVERY_SEMANTIC.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
