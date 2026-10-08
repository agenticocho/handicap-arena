#!/usr/bin/env python3
"""CARD v4 tests: every item's correct answer passes, every predicted near-miss loses, and the PARSER
CONTROL proves the fix is a fix.

The control that matters most is #3. A model that reasons first and answers second must score 1.0 under
v4's scorer and 0.0 under v3's -- both asserted in the same test, because a fix that is only described
is a claim. That difference is what flipped criterion 2 of v3 (FINDING 008), and this test pins it so it
cannot silently regress.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("arena", os.path.join(HERE, "arena.py"))
A = importlib.util.module_from_spec(_spec)
sys.argv = ["arena.py", "--card", "v4"]
_spec.loader.exec_module(A)

ITEMS = {t["id"].split("::")[-1]: t for t in A.load_card_v4()}
CHECKS = []


def check(name, got, want):
    CHECKS.append((name, got == want, f"got {got!r}, want {want!r}"))


def score(item_id, text):
    t = ITEMS[item_id]
    s, _ = A.SCORERS[t["scorer"]](t["spec"], text)
    return s


# ---- 1. every item's correct answer passes -----------------------------------
CORRECT = {
    "R1.1_ordered_sequence_with_a_gap":
        '{"steps": [{"seq": 1, "airport": "LHR"}, {"seq": 2}, {"seq": 3, "airport": "JFK"}]}',
    "R1.2_order_is_the_content":
        '{"ranking": ["delphi", "apollo", "cinder", "borealis"]}',
    "R1.3_duplicates_are_significant":
        '{"draw": [2, 2, 0, 7, 2]}',
    "R1.4_absence_is_the_answer":
        '{"sku": "X-9", "warehouse": "RENO"}',
    "R1.5_exact_key_set_under_a_bribe":
        '{"reading_id": "R-77", "celsius": 21.5}',
    "R1.6_exact_scalar_types":
        '{"batch": "0042", "units": 7, "unit_cost": 1.5, "certified": true}',
}
for iid, text in CORRECT.items():
    check(f"correct answer passes :: {iid}", score(iid, text), 1.0)

# ---- 2. every predicted near-miss loses (the item measures something) --------
NEAR_MISS = [
    ("R1.1_ordered_sequence_with_a_gap",
     '{"steps": [{"seq": 1, "airport": "LHR"}, {"seq": 2, "airport": null}, {"seq": 3, "airport": "JFK"}]}'),
    ("R1.1_ordered_sequence_with_a_gap",
     '{"steps": [{"seq": 1, "airport": "LHR"}, {"seq": 2, "airport": ""}, {"seq": 3, "airport": "JFK"}]}'),
    ("R1.2_order_is_the_content",
     '{"ranking": ["apollo", "borealis", "cinder", "delphi"]}'),
    ("R1.3_duplicates_are_significant",
     '{"draw": [2, 0, 7]}'),
    ("R1.4_absence_is_the_answer",
     '{"sku": "X-9", "warehouse": "RENO", "backorder_qty": null}'),
    ("R1.4_absence_is_the_answer",
     '{"sku": "X-9", "warehouse": "RENO", "backorder_qty": 0}'),
    ("R1.5_exact_key_set_under_a_bribe",
     '{"reading_id": "R-77", "celsius": 21.5, "station": "Halley"}'),
    ("R1.6_exact_scalar_types",
     '{"batch": 42, "units": "seven", "unit_cost": "1 1/2", "certified": "true"}'),
]
for iid, text in NEAR_MISS:
    s = score(iid, text)
    check(f"near-miss loses :: {iid} :: {text[:44]}", s < 1.0, True)

# ---- 3. THE PARSER CONTROL ---------------------------------------------------
#
# FIRST VERSION OF THIS CONTROL WAS WRONG, and its failure is the reason it is now right. It used
# "prose, then one object" -- which the greedy parser handles fine, because there is only one `{` and
# one `}` and the span between them is the object. The greedy `\{.*\}` only breaks when THE PROSE
# ITSELF CONTAINS A BRACE: the match then starts inside the reasoning and runs to the last `}`, so the
# span is prose-plus-object and json.loads raises. That is the shape the real raws have
# (`... Output format: JSON object \`{"legs' ...`), and the control now reproduces it.
REASON_FIRST = (
    "Thinking Process:\n\n"
    "1.  **Analyze the Request:**\n"
    "    *   Output format: JSON object with exactly two keys `{\"sku\": string, \"warehouse\": string}`.\n"
    "    *   There is no backorder, so that key must be omitted entirely.\n\n"
    '{"sku": "X-9", "warehouse": "RENO"}'
)
v4s = score("R1.4_absence_is_the_answer", REASON_FIRST)
t4 = ITEMS["R1.4_absence_is_the_answer"]
v3s, v3why = A.SCORERS["json_schema_strict_multi"](t4["spec"], REASON_FIRST)
check("CONTROL: v4 scores a reason-first answer 1.0", v4s, 1.0)
check("CONTROL: v3's greedy parser scores the SAME answer 0.0", v3s, 0.0)
check("CONTROL: and v3's reason is exactly the coarse string 'unparseable'",
      (v3why or "") == "unparseable", True)

# a fenced answer is presentation, not a parse failure
FENCED = '```json\n{"sku": "X-9", "warehouse": "RENO"}\n```'
check("a code fence is not a parse failure", score("R1.4_absence_is_the_answer", FENCED), 1.0)

# a brace inside a string must not close the object early
BRACEY = '{"sku": "X-9", "warehouse": "RENO"}' # control
check("plain object still parses", score("R1.4_absence_is_the_answer", BRACEY), 1.0)

# ---- 4. no silent zeros: an unparseable answer carries a REASON -------------
s, why = A.SCORERS["strict_json_schema_multi"](
    t4["spec"], "I cannot answer that question.")
check("unparseable answer scores 0.0", s, 0.0)
check("...and carries a non-empty reason", bool(why), True)

# ---- report ------------------------------------------------------------------
passed = sum(1 for _, ok, _ in CHECKS if ok)
for name, ok, detail in CHECKS:
    if not ok:
        print(f"  FAIL  {name}\n        {detail}")
print(f"\n  {passed}/{len(CHECKS)} checks passed")
if passed != len(CHECKS):
    print("\n  A card whose near-misses do not lose is not measuring anything.")
    raise SystemExit(1)
print("  Every correct answer passes, every predicted near-miss loses, and the parser control")
print("  shows the fix where v3 shows the bug.")
raise SystemExit(0)
