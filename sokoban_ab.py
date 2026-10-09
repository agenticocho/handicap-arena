#!/usr/bin/env python3
"""SOKOBAN A/B -- ONE ENTRANT, TWO LEGENDS, SAME LEVELS. The controlled test of the prediction.

WHY THIS EXISTS. The re-run gave granite-3.3-2b a clean result (`U`, blocked 40, not_an_action 0) and gave
LFM2-350M UNCHANGED (40 not_an_action, `{`). granite IMPROVED -- but improving is not being disadvantaged,
because THE OLD LEGEND WAS NEVER PUT TO granite. A RESULT WITH NO CONTROL IS AN OBSERVATION, NOT A
DIFFERENCE. So the old legend comes back as a control: the defect is measured, its size is known, and the
only open question is whether THIS entrant was affected by it.

WHAT IS HELD FIXED: the entrant, the two verified levels, the command cap, max_tokens, temperature, the
reader, the simulator. WHAT VARIES: the legend, and nothing else.

THE ORDER IS INTERLEAVED AND RECORDED. All-old then all-new would let a warming machine or a cached prompt
look like an arm effect. The order is written into the artifact so a reader can check it rather than trust it.

    python3 sokoban_ab.py --entrant granite-3.3-2b-instruct-critical-thinking.Q5_K_M.gguf
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban_run as R                                                 # noqa: E402

LEVELS = ["levels/01_one_push.txt", "levels/02_two_boxes.txt"]
ARMS = ["old", "new"]


def control_the_arms():
    """A CONTROL ON THE A/B ITSELF: the two arms must be PROVABLY DIFFERENT.

    If PROMPT_OLD and PROMPT_NEW produced the same text, this experiment would measure nothing and report
    a tidy null as though it were a finding. So the templates are compared BEFORE any model is loaded, and
    the two digests are printed. This is the same rule as a legality checker asserting the start position
    has twenty moves: A COMPARISON THAT CANNOT SHOW A DIFFERENCE IS NOT A COMPARISON.
    """
    os.environ["SOKOBAN_LEGEND"] = "old"
    d_old = R.legend_digest()
    os.environ["SOKOBAN_LEGEND"] = "new"
    d_new = R.legend_digest()

    os.environ["SOKOBAN_LEGEND"] = "old"
    t_old = R.prompt_for("<BOARD>", [])
    os.environ["SOKOBAN_LEGEND"] = "new"
    t_new = R.prompt_for("<BOARD>", [])

    print("=" * 96)
    print("CONTROL ON THE A/B ITSELF -- THE ARMS MUST DIFFER")
    print("=" * 96)
    print(f"  old legend digest   {d_old}")
    print(f"  new legend digest   {d_new}")
    print(f"  ARMS DIFFER         {d_old != d_new}")
    print(f"  templates differ    {t_old != t_new}")
    print(f"  old mentions FIRST LINE   {'FIRST LINE' in t_old}")
    print(f"  new mentions FIRST LINE   {'FIRST LINE' in t_new}")
    print(f"  old has key-value pairs   {'# wall' in t_old}")
    print(f"  new has key-value pairs   {'# wall' in t_new}")
    if d_old == d_new or t_old == t_new:
        print("  *** THE ARMS ARE IDENTICAL -- THIS EXPERIMENT WOULD MEASURE NOTHING. ABORTING. ***")
        return False
    print("  -> the arms differ, and the differing tokens are the ones the model echoed. Proceeding.")
    print()
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrant", default="granite-3.3-2b-instruct-critical-thinking.Q5_K_M.gguf")
    ap.add_argument("--cap", type=int, default=40)
    ap.add_argument("--port", type=int, default=8760)
    a = ap.parse_args()

    ent = a.entrant if os.path.exists(a.entrant) else os.path.join(R.MODELS, a.entrant)
    if not os.path.exists(ent):
        print(f"  ENTRANT ABSENT: {a.entrant}")
        return 2
    if not control_the_arms():
        return 3

    print(f"  entrant {os.path.basename(ent)}")
    print(f"  levels  {[os.path.basename(x) for x in LEVELS]}")
    print(f"  arms    {ARMS}   cap {a.cap}   max_tokens {R.MAX_TOKENS}")
    print()

    # INTERLEAVED: level 1 old, level 1 new, level 2 old, level 2 new. Recorded, not assumed.
    order = [(lv, arm) for lv in LEVELS for arm in ARMS]
    rows = []
    port = a.port
    for i, (lv, arm) in enumerate(order):
        os.environ["SOKOBAN_LEGEND"] = arm
        print(f"  [{i+1}/{len(order)}] {os.path.basename(lv):22s} arm={arm:4s} digest={R.legend_digest()} ...",
              flush=True)
        r = R.run(ent, os.path.join(HERE, lv), a.cap, port)
        port += 1
        r["order"] = i
        rows.append(r)
        if not r.get("loaded"):
            print(f"        DID NOT LOAD -- {r['why']}")
        else:
            print(f"        ended={r['ended']:18s} moves={r['moves']:3d} attempted={r['attempted']:3d} "
                  f"blocked={r['blocked']:3d} not_an_action={r['not_an_action']:3d} give_up={r['give_up']}")

    out = os.path.join(HERE, "probes", "SOKOBAN_AB.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"entrant": os.path.basename(ent), "cap": a.cap, "max_tokens": R.MAX_TOKENS,
               "order": [f"{os.path.basename(l)}/{arm}" for l, arm in order], "cells": rows},
              open(out, "w"), indent=1)
    print()
    print(f"  artifact -> {os.path.relpath(out, HERE)}")

    # DERIVED FROM THE ARTIFACT AT READ TIME, not accumulated above -- the FINDING 018 rule.
    print()
    print("=" * 96)
    print("FROM THE ARTIFACT, NOT FROM THIS SCRIPT'S MEMORY")
    print("=" * 96)
    d = json.load(open(out))
    for lv in LEVELS:
        ln = os.path.basename(lv).replace(".txt", "")
        print(f"  {ln}")
        for arm in ARMS:
            c = [r for r in d["cells"] if r["level"] == ln and r.get("legend") == arm]
            if not c:
                continue
            c = c[0]
            if not c.get("loaded"):
                print(f"    {arm:4s}  DID NOT LOAD -- {c['why']}")
                continue
            tok = [t["token"] for t in (c.get("turns") or [])][:3]
            print(f"    {arm:4s}  moves={c['moves']:3d} attempted={c['attempted']:3d} blocked={c['blocked']:3d} "
                  f"not_an_action={c['not_an_action']:3d} give_up={c['give_up']}  first tokens {tok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
