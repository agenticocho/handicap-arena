#!/usr/bin/env python3
"""The bind's control, in both directions, WITH ZERO COST TO THE RECORD.

WHY THIS FILE EXISTS, and the defect it fixes.

The first version of this control ran `run_card.py` whole to watch the gate pass. **But passing the gate
STARTS THE WORK** -- so the control spawned servers, reached entrants, and wrote into `results/`, and those
artifacts went into a commit whose own message claimed "0 control artifacts left behind." The diff
contradicted the sentence three lines away from it.

  A CONTROL FOR A GATE MUST NOT WRITE TO THE RECORD IT CONTROLS.
  TESTING A REFUSAL IS FREE -- the refusal IS the short circuit.
  TESTING A PERMISSION IS NOT FREE, BECAUSE THE PERMISSION'S ONLY OBSERVABLE EFFECT IS THE PERMITTED WORK.
  NOBODY PRICES IN THE COST OF THE THING BEING PERMITTED.

So the gate was extracted into `game_contract_gate()` -> (ok, detail), and this control reads the DECISION.
The caller is the only thing that proceeds. **Both directions now cost nothing**, which is the only form in
which a permission can be tested at all.

The gate's own refusal direction is exercised against the real repo; the permission direction is exercised
against the real repo too, but reading only the return value -- so no entrant loop is ever entered.

Run: test_bind_control.py     -> exit 0 if both directions behave
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_card  # noqa: E402

PLANT = os.path.join(run_card.RESULTS, "ZZ_bind_control_probe.json")
PLANTED = {"harness": "handicap-arena", "results": [{"rounds": {"R9_smuggled": {"game": "CHESS"}}}]}


def fingerprint():
    """Every file under results/, with size and mtime -- so 'nothing was written' is measured."""
    out = {}
    for root, _dirs, files in os.walk(run_card.RESULTS):
        for f in files:
            p = os.path.join(root, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            out[os.path.relpath(p, run_card.RESULTS)] = (st.st_size, int(st.st_mtime))
    return out


def main():
    print("  BIND CONTROL -- both directions, reading the DECISION, never running the permitted work\n")
    fails = []

    # ---- DIRECTION 1: PERMISSION. Contract clean -> the gate must ALLOW, and nothing may be written.
    before = fingerprint()
    ok, _detail = run_card.game_contract_gate()
    after = fingerprint()
    if not ok:
        print("  FAIL  a CLEAN contract was refused -- the gate overreaches")
        fails.append("permission direction")
    else:
        print("  ok    clean contract -> gate ALLOWS")
    drifted = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    if drifted:
        print(f"  FAIL  testing PERMISSION wrote to the record: {sorted(drifted)[:4]}")
        fails.append("permission direction wrote artifacts")
    else:
        print("  ok    testing PERMISSION wrote NOTHING (measured: results/ fingerprint unchanged)")

    # ---- DIRECTION 2: REFUSAL. Plant a NEW violation -> the gate must REFUSE, and still write nothing.
    try:
        with open(PLANT, "w", encoding="utf-8") as fh:
            json.dump(PLANTED, fh)
        before = fingerprint()
        ok2, detail = run_card.game_contract_gate()
        after = fingerprint()
        if ok2:
            print("  DID NOT FIRE  a NEW violation was ALLOWED through")
            fails.append("refusal direction")
        else:
            print("  FIRES  a NEW violation -> gate REFUSES")
        if "R9_smuggled" not in detail and "declared slot table" not in detail:
            print("  FAIL  the refusal did not name the offending record")
            fails.append("refusal detail")
        else:
            print("  ok    the refusal NAMES the offending record")
        # the only drift allowed is the planted probe itself
        drifted = {k for k in (set(before) | set(after)) - {"ZZ_bind_control_probe.json"}
                   if before.get(k) != after.get(k)}
        if drifted:
            print(f"  FAIL  testing REFUSAL wrote to the record: {sorted(drifted)[:4]}")
            fails.append("refusal direction wrote artifacts")
        else:
            print("  ok    testing REFUSAL wrote NOTHING else")
    finally:
        if os.path.exists(PLANT):
            os.remove(PLANT)

    print()
    if fails:
        print(f"  {len(fails)} failure(s): {fails}")
        print("  A control that writes to the record it controls is not a control -- it is a second input.")
        return 1
    print("  BOTH DIRECTIONS BEHAVE, AND NEITHER COSTS THE RECORD ANYTHING.")
    print("  The permission's cost was the permitted work; reading the decision is what makes it free.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
