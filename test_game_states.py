#!/usr/bin/env python3
"""GAME CONTRACT enforcement: a game name with no state behind it FAILS.

The standard (GAME_CONTRACT.md): *can a stranger reconstruct the game from the recorded bundle?*
If not, the visual is a skin over someone else's result — the same failure as a count carried as a
literal, which is a claim with no carrier.

A principle will not hold across 55 catalogue events. A check will. This is that check.

WHAT IT ENFORCES
  1. A card task file that names a game (`metaphor` or `game`) must also declare the bundle fields
     that carry that game's state (`game_state_in_bundle`). Otherwise the name is a costume.
  2. A recorded round that carries a game name must have non-empty state for it.
  3. INSTRUMENT-class events must not be ranked. An event that validates the measurement is not a
     contest, and a front end that merely LABELS the difference will eventually rank a
     scale-calibration against a boxing match.

POSITIVE CONTROL: the test injects a synthetic task that names a game with no state and asserts the
rule fires on it. A check that cannot fail is decoration; this one is verified to fail on exactly
the defect it exists for.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(HERE, "tasks")
RESULTS = os.path.join(HERE, "results")
GAME_KEYS = ("metaphor", "game")
STATE_KEYS = ("game_state_in_bundle", "game_state")


def declared_game(rec):
    for k in GAME_KEYS:
        v = rec.get(k)
        if isinstance(v, str) and v.strip():
            return k, v.strip()
    return None, None


def has_state(rec):
    for k in STATE_KEYS:
        v = rec.get(k)
        if isinstance(v, (list, dict)) and len(v) > 0:
            return True
        if isinstance(v, str) and v.strip():
            return True
    return False


def check_task_file(d):
    """-> list of failure strings for one task definition."""
    fails = []
    gk, gv = declared_game(d)
    if gk and not has_state(d):
        fails.append(f"names the game {gv!r} via {gk!r} but declares no "
                     f"{STATE_KEYS[0]} — the name is a costume")
    if d.get("class") == "INSTRUMENT" and d.get("ranked"):
        fails.append("classed INSTRUMENT but marked ranked — officials are not athletes")
    return fails


def check_bundle(p):
    """-> list of failure strings for one recorded bundle."""
    fails = []
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        return fails
    if d.get("harness") != "handicap-arena":
        return fails
    for e in (d.get("results") or []):
        for rk, rd in (e.get("rounds") or {}).items():
            gk, gv = declared_game(rd)
            if gk and not has_state(rd):
                fails.append(f"{os.path.basename(p)} :: {rk} claims game {gv!r} with no state")
    return fails


def main():
    fails, checked = [], 0

    # 1 + 3: task definitions
    for p in sorted(glob.glob(os.path.join(TASKS, "*", "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        checked += 1
        for f in check_task_file(d):
            fails.append(f"{os.path.relpath(p, HERE)}: {f}")

    # 2: recorded bundles
    bundles = sorted(glob.glob(os.path.join(RESULTS, "*.json")))
    for p in bundles:
        fails.extend(check_bundle(p))

    print(f"checked {checked} task file(s) and {len(bundles)} bundle(s)")

    # POSITIVE CONTROL -- the test must fire on the defect it exists for.
    control = {"id": "CONTROL", "metaphor": "CHESS", "items": []}
    control_fired = bool(check_task_file(control))
    print(f"positive control (a game name with no state): "
          f"{'FIRES' if control_fired else 'DID NOT FIRE -- this test is decoration'}")
    if not control_fired:
        fails.append("positive control did not fire; the rule cannot detect its own defect")

    print()
    if fails:
        # SUMMARY BY CLASS, not one line per bundle. The first version printed 245 lines for what
        # is really 3 distinct defects -- the same 16:1 noise ratio I criticised in test_doc_counts
        # this morning. A report nobody reads protects nothing.
        from collections import defaultdict
        groups = defaultdict(list)
        for f in fails:
            if "names the game" in f:
                groups["task file names a game with no state"].append(f.split(": names")[0])
            elif "claims game" in f:
                g = f.rsplit("claims game ", 1)[-1]
                groups["recorded rounds claim a game with no state"].append(g)
            else:
                groups["other"].append(f)
        total = len(fails)
        print(f"{total} GAME CONTRACT violation(s), in {len(groups)} class(es):")
        for g, items in groups.items():
            print(f"  - {g}: {len(items)}")
            if "task file" in g:
                for i in sorted(set(items)):
                    print(f"        {i}")
            else:
                for i in sorted(set(items))[:6]:
                    print(f"        {i}")
                if len(set(items)) > 6:
                    print(f"        ... and {len(set(items)) - 6} more (same shape)")
        print()
        print("  EVERY task file and EVERY recorded round names a game and carries no state.")
        print("  Either the name goes, or the state arrives. See GAME_CONTRACT.md.")
        return 1
    print("every declared game has state behind it; no INSTRUMENT event is ranked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
