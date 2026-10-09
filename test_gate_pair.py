#!/usr/bin/env python3
"""CONTROLS FOR THE RULED-IN GATE PAIR, AND FOR THE NULL FOOTPRINT.

TWO THINGS THIS FILE EXISTS TO PREVENT:

1. THE GATE PAIR. `coverage >= 0.95 AND measured > 0`, both sides asserted. A GATE THAT ONLY EVER FIRES IS
   BROKEN; ONE THAT NEVER FIRES IS DEAD -- the rule test_gate_satisfiable.py already follows. So there is a
   case that MUST go red (coverage 1.000 with nothing measured) and a case that MUST stay green (the same
   coverage with something measured). Asserting only the red side would make the new condition
   indistinguishable from a gate that simply refuses everything.

2. THE NULL FOOTPRINT MUST NOT THROW, AND MUST NOT BE REPLACED BY A ZERO. The port item failed at the LAST
   step on a host with no nvidia-smi, so a macOS run produced nothing. The control asserts all three
   properties: it does not throw, it SAYS the measurement is absent, and it does NOT print an invented
   `0.00 GB measured` -- because A FABRICATED NUMBER IN A BUNDLE IS WORSE THAN A MISSING ONE: IT COMPUTES.

    python3 test_gate_pair.py
"""
import contextlib
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_card                                                         # noqa: E402
import arena                                                            # noqa: E402

PASS, FAIL = [0], [0]


def ck(name, got, want):
    ok = got == want
    (PASS if ok else FAIL)[0] += 1
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        print(f"        got  {got!r}")
        print(f"        want {want!r}")


print("=" * 92)
print("[1] THE GATE PAIR -- BOTH SIDES")
print("=" * 92)

g = run_card.gate_ratios(planned=10, attempted=10, measured=0)
ck("coverage 1.000 WITH measured 0 -> coverage_ok is TRUE", g["coverage_ok"], True)
ck("...and measured_ok is FALSE", g["measured_ok"], False)
ck("...and THE GATE IS UNMET -- the side that catches total failure", g["gate_met"], False)

g2 = run_card.gate_ratios(planned=10, attempted=10, measured=9)
ck("coverage 1.000, yield 0.900, measured 9 -> measured_ok TRUE", g2["measured_ok"], True)
ck("...and the gate is MET -- the side that must NOT fire", g2["gate_met"], True)

ck("a full, complete run still passes (the gate is not stuck shut)",
   run_card.gate_ratios(10, 10, 10)["gate_met"], True)
ck("a thin field still fails on coverage",
   run_card.gate_ratios(10, 5, 5)["coverage_ok"], False)
ck("a failing yield still fails on yield",
   run_card.gate_ratios(10, 10, 5)["yield_ok"], False)
ck("...and that one is unmet overall", run_card.gate_ratios(10, 10, 5)["gate_met"], False)
ck("measured is REPORTED, not just tested", g2["measured"], 9)

print()
print("=" * 92)
print("[2] THE NULL FOOTPRINT -- print_card MUST NOT THROW AND MUST NOT INVENT A ZERO")
print("=" * 92)

res = dict(gguf="/nonexistent/model.gguf", sha256="x", footprint_gb=None, division=1, cord="slate",
           weigh_in={}, config={}, rounds={}, aggregate=0.0,
           grade={"belt": "white", "stripes": 0, "trials": 0, "rounds_won": 0, "rounds": 0},
           card_version=5, certification="test", mean_latency=None, answers_from_reasoning=0,
           footprint_null_reason="no nvidia-smi on this host (test)")

buf = io.StringIO()
threw = None
try:
    with contextlib.redirect_stdout(buf):
        arena.print_card(res)
except Exception as e:                                                  # noqa: BLE001
    threw = f"{type(e).__name__}: {e}"

ck("print_card does NOT throw on a null footprint", threw, None)
out = buf.getvalue()
ck("...and says NOT MEASURED", "NOT MEASURED" in out, True)
ck("...and carries the REASON into the record", "no nvidia-smi" in out, True)
ck("...and does NOT print an invented '0.00 GB measured'", "0.00 GB measured" in out, False)

# AND THE NON-NULL PATH STILL WORKS -- the control must not have broken the normal case.
res2 = dict(res, footprint_gb=1.23, footprint_null_reason=None, gguf="/nonexistent/ok.gguf")
buf2 = io.StringIO()
try:
    with contextlib.redirect_stdout(buf2):
        arena.print_card(res2)
    threw2 = None
except Exception as e:                                                  # noqa: BLE001
    threw2 = f"{type(e).__name__}: {e}"
ck("a MEASURED footprint still prints normally", threw2, None)
ck("...and prints its value", "1.23 GB measured" in buf2.getvalue(), True)

print()
print("=" * 92)
print("[3] THE REASON IS DERIVED FROM THE CONDITION, NOT TYPED")
print("=" * 92)
ck("footprint_absent_reason() returns something", bool(arena.footprint_absent_reason()), True)
if not shutil.which("nvidia-smi"):
    ck("host has NO nvidia-smi -> the reason SAYS SO",
       "no nvidia-smi" in arena.footprint_absent_reason(), True)
    print("        (this host has no nvidia-smi, so that branch is the one exercised here)")

# AND THE DARWIN BRANCH IS EXERCISED BY MAKING THE CONDITION TRUE, NOT BY HOPING.
#
# THIS HOST HAS nvidia-smi, so the branch above was NOT taken here -- the control would have passed
# without ever running the code a macOS bundle depends on. A CONTROL THAT ONLY RUNS WHEN THE HOST
# HAPPENS TO LACK A TOOL IS A HOPE, NOT A CONTROL. So the tool is hidden and the condition forced.
_real_which = arena.shutil.which
try:
    arena.shutil.which = lambda name, *a, **k: None if name == "nvidia-smi" else _real_which(name, *a, **k)
    ck("with nvidia-smi HIDDEN -> the reason names it",
       "no nvidia-smi" in arena.footprint_absent_reason(), True)
    ck("...and it says macOS returns none",
       "macOS" in arena.footprint_absent_reason(), True)
    ck("gpu_used_mb() returns None on that host", arena.gpu_used_mb(), None)
except Exception as e:                                                  # noqa: BLE001
    ck("forcing the Darwin branch raised", f"{type(e).__name__}: {e}", None)
finally:
    arena.shutil.which = _real_which

ck("the real host is restored", arena.shutil.which("nvidia-smi"),
   shutil.which("nvidia-smi"))

print()
print("=" * 92)
print(f"  {'ALL CONTROLS PASS' if not FAIL[0] else str(FAIL[0]) + ' FAILED'}   --   "
      f"{PASS[0]}/{PASS[0] + FAIL[0]}")
print("=" * 92)
sys.exit(1 if FAIL[0] else 0)
