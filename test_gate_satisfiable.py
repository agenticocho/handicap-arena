#!/usr/bin/env python3
"""CONTROL for CARD_v5.md's gate. READ-ONLY: it writes NOTHING.

A control for a gate must not write to the record it controls. This one only reads.

WHAT IT EXISTS FOR. The gate's first implementation divided COVERAGE by the ADMITTED set (46) while
CARD_v5.md froze `attempted / planned` (38). A COMPLETE, CORRECT run therefore scored 0.826 and FAILED
ITS OWN GATE -- `an instrument that could not pass`, which is v4's defect wearing the opposite mask
(v4's gate could not be met on a thinned field; this one could not be met on a correct one).

A gate needs BOTH controls. A gate that only ever fires is not strict, it is broken; a gate that never
fires is not lenient, it is dead. Cases 1 and 4 are the two directions.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_card as rc

HERE = os.path.dirname(os.path.abspath(__file__))
fails = []


def check(name, got, want):
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}"
          + ("" if ok else f"   got {got!r}, want {want!r}"))
    if not ok:
        fails.append(name)


print("=" * 92)
print("CONTROL -- CARD_v5.md gate: it must be able to PASS, and able to FAIL")
print("=" * 92)

# 1 ----------------------------------------------------------------- POSITIVE
# A complete run of the planned population. THIS IS THE CASE THAT WAS BROKEN.
g = rc.gate_ratios(planned=38, attempted=38, measured=38)
print("\n1. a COMPLETE, CORRECT run (38/38/38) -- the case the first implementation failed")
check("coverage == 1.000", round(g["coverage"], 3), 1.0)
check("yield    == 1.000", round(g["yield"], 3), 1.0)
check("gate MET", g["gate_met"], True)

# 2 ------------------------------------------------------ NEGATIVE: interrupted
g = rc.gate_ratios(planned=38, attempted=30, measured=30)
print("\n2. an INTERRUPTED run (30 of 38 attempted)")
check("coverage 0.789", round(g["coverage"], 3), 0.789)
check("gate UNMET", g["gate_met"], False)
check("fails on COVERAGE, not yield", (g["coverage_ok"], g["yield_ok"]), (False, True))

# 3 -------------------------------------------- NEGATIVE: population cannot run
g = rc.gate_ratios(planned=38, attempted=38, measured=28)
print("\n3. a POPULATION THAT CANNOT RUN (28 of 38 measured)")
check("yield 0.737", round(g["yield"], 3), 0.737)
check("gate UNMET", g["gate_met"], False)
check("fails on YIELD, not coverage", (g["coverage_ok"], g["yield_ok"]), (True, False))

# 4 -------------------------- NEGATIVE: v4's OWN FIELD, so the gate is not a rubber stamp
# The closed v4 verdict: 46 attempted, 38 measured, no exclusions (the eight were still in the field).
g = rc.gate_ratios(planned=46, attempted=46, measured=38)
print("\n4. v4's OWN FIELD as the negative control (46 attempted, 38 measured)")
check("coverage 1.000 -- the field COMPLETED, it did not thin", round(g["coverage"], 3), 1.0)
check("yield 0.826 -- BELOW the 0.85 floor", round(g["yield"], 3), 0.826)
check("gate UNMET -- v4 is still refused by this gate", g["gate_met"], False)

# 5 --------------------------------- THE DENOMINATOR: planned, NOT admitted
# With v5's real numbers these differ, and only one of them can be met.
g_planned = rc.gate_ratios(planned=38, attempted=38, measured=38)
g_admitted = rc.gate_ratios(planned=46, attempted=38, measured=38)
print("\n5. the denominator that was wrong (planned 38 vs admitted 46, same run)")
check("dividing by PLANNED is met", g_planned["gate_met"], True)
check("dividing by ADMITTED is UNMET -- the defect", g_admitted["gate_met"], False)
check("the two genuinely differ", round(g_planned["coverage"], 3) != round(g_admitted["coverage"], 3), True)

# 6 ------------------------------ SHARED DEFINITION: no second implementation
print("\n6. the runner SHARES this rule rather than re-implementing it")
src = open(os.path.join(HERE, "run_card.py"), encoding="utf-8").read()
check("run_card.py calls gate_ratios()", "gate_ratios(" in src, True)
# The printing block must not recompute a ratio itself.
block = src[src.index("DENOMINATORS"):src.index("DENOMINATORS") + 1200]
check("the summary block does NOT recompute a ratio inline",
      bool(re.search(r"_\w+\s*=\s*\w+\s*/\s*\w+", block)), False)

# 7 -------------------------------- THE CARD IS THE SOURCE: frozen text still says planned
print("\n7. CARD_v5.md's frozen formula, read from the card")
card = open(os.path.join(HERE, "CARD_v5.md"), encoding="utf-8").read()
check("the card states COVERAGE over `planned`", "attempted / planned" in card, True)
check("the card states YIELD over `attempted`", "measured  / attempted" in card, True)
check("the card's floors are 0.95 and 0.85", ("0.95" in card and "0.85" in card), True)

print("\n" + "=" * 92)
print(f"{'ALL CONTROLS PASS' if not fails else str(len(fails)) + ' CONTROL(S) FAILED'}"
      f"   -- {18 - len(fails)}/18 assertions")
print("=" * 92)
sys.exit(1 if fails else 0)
