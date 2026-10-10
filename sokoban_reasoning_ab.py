#!/usr/bin/env python3
"""THE REASONING A/B -- does the launch flag carry the effect, or was it something else?

PRE-REGISTERED in PREREG_reasoning_ab.md before the first number, with its branches. This is the runner.

FIXED: the two Qwen entrants, the three verified levels, the command cap, the token ceiling, temperature
0.0, ctx, ngl, the legend arm, the reader, the simulator, the box.
VARIES: exactly one thing -- `--reasoning off` (the DECLARED setting) vs `--reasoning on` (the OVERRIDE).

THE CONTROL RAN FIRST AND IS ASSERTED AGAIN HERE: if the override does not change the launch argv, this is a
comparison between two runs with different STORIES, and it measures nothing.

    python3 sokoban_reasoning_ab.py
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban_run as R                                                 # noqa: E402

ENTRANTS = ["Qwen3.5-4B-UD-Q4_K_XL.gguf", "Qwen3.5-9B-Q4_K_M.gguf"]
LEVELS = ["levels/01_one_push.txt", "levels/02_two_boxes.txt", "levels/03_the_corner_waiting.txt"]
ARMS = [("declared", "", "off"), ("override", "on", "on")]
CAP = 40


def arm_env_value(override):
    return override


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8810)
    a = ap.parse_args()

    out = os.path.join(HERE, "probes", "REASONING_AB.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    print("=" * 100)
    print("THE REASONING A/B -- pre-registered in PREREG_reasoning_ab.md")
    print("=" * 100)
    print(f"  entrants  {ENTRANTS}")
    print(f"  levels    {[os.path.basename(l) for l in LEVELS]}")
    print(f"  arms      {[(n, v) for n, _, v in ARMS]}")
    print(f"  cells     {len(ENTRANTS) * len(LEVELS) * len(ARMS)}")
    print()

    # ---- THE CONTROL, BEFORE ANY MODEL LOADS.
    print("  CONTROL -- the override must change the LAUNCH ARGV, or this measures nothing:")
    argv_by_arm = {}
    for name, override, want in ARMS:
        os.environ["SOKOBAN_REASONING_TEST_ARM"] = override
        # re-read the module-level constants the way the server does
        import importlib
        importlib.reload(R)
        argv_by_arm[name] = list(R.reasoning_argv())
        print(f"    {name:9s} REASONING={R.REASONING!r}  argv={argv_by_arm[name]}  "
              f"source={R.reasoning_source()!r}  changed={R.reasoning_changed_from_declaration()}")
    if argv_by_arm["declared"] == argv_by_arm["override"]:
        print("  *** THE ARGV IS IDENTICAL IN BOTH ARMS -- THE A/B WOULD MEASURE NOTHING. ABORTING. ***")
        return 3
    print("    -> the argv differs. Proceeding.")
    print()

    rows = []
    port = a.port
    for lv in LEVELS:
        for ent in ENTRANTS:
            for name, override, want in ARMS:
                os.environ["SOKOBAN_REASONING_TEST_ARM"] = override
                import importlib
                importlib.reload(R)
                ent_p = ent if os.path.exists(ent) else os.path.join(R.MODELS, ent)
                print(f"  {os.path.basename(lv):24s} {ent[:22]:24s} arm={name:9s} "
                      f"argv={R.reasoning_argv()} ...", flush=True)
                r = R.run(ent_p, os.path.join(HERE, lv), CAP, port)
                port += 1
                r["arm"] = name
                r["arm_want"] = want
                rows.append(r)
                if not r.get("loaded"):
                    print(f"      NEVER_STARTED -- {r.get('why')}")
                else:
                    print(f"      ended={r.get('ended', '?'):18s} moves={r.get('moves', 0):3d} "
                          f"blocked={r.get('blocked', 0):3d} unreadable={r.get('unreadable', 0):3d} "
                          f"probe={((r.get('reasoning_probe') or {}).get('observed'))}")
                # ONE WRITER, EVERY TIME: a crash mid-run leaves a readable partial rather than nothing.
                json.dump({"prereg": "PREREG_reasoning_ab.md", "entrants": ENTRANTS,
                           "levels": LEVELS, "cap": CAP,
                           "argv_by_arm": argv_by_arm, "cells": rows}, open(out, "w"), indent=1)

    print()
    print("=" * 100)
    print("FROM THE ARTIFACT, NOT FROM THIS SCRIPT'S MEMORY")
    print("=" * 100)
    d = json.load(open(out))
    print(f"  {'entrant':24s} {'level':24s} {'arm':10s} {'unreadable':>10s} {'solved':>7s} {'moves':>6s}")
    for c in d["cells"]:
        if not c.get("loaded"):
            continue
        print(f"  {c['entrant'][:24]:24s} {c['level'][:24]:24s} {c.get('arm'):10s} "
              f"{c.get('unreadable', 0):10d} {str(c.get('solved')):>7s} {c.get('moves', 0):6d}")

    print()
    print("  === THE BRANCH ===")
    for e in ENTRANTS:
        got = {}
        for arm in ("declared", "override"):
            sub = [c for c in d["cells"] if c.get("loaded") and c["entrant"].startswith(e[:12])
                   and c.get("arm") == arm]
            got[arm] = sum(c.get("unreadable", 0) for c in sub)
        readable_decl = got["declared"] == 0
        readable_over = got["override"] == 0
        if readable_decl and not readable_over:
            b = "BRANCH 1 -- the flag IS the carrier (readable with it, unreadable without)"
        elif readable_decl and readable_over:
            b = "BRANCH 2 -- the flag is NOT the carrier; something else is"
        else:
            b = "BRANCH 3 -- READABLE output never depended on the flag"
        print(f"    {e[:24]:26s} unreadable declared={got['declared']:3d} override={got['override']:3d}  {b}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
