#!/usr/bin/env python3
"""CARD v3 — do the traps actually bite?

A card that claims to be hardened but scores the natural wrong answer as correct is worse than the
saturated card it replaced, because it looks fixed. So every item gets BOTH answers: the correct
one, and the one a competent model will actually produce.

The wrong answers below are not strawmen. Each is the outcome the item's own `trap` field predicts.
If any of them scores 1.0, the rebalance failed and this test fails.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("arena", os.path.join(HERE, "arena.py"))
A = importlib.util.module_from_spec(spec)
sys.argv = ["arena.py", "--card", "v3"]
spec.loader.exec_module(A)

ITEMS = json.load(open(os.path.join(HERE, "tasks", "v3", "01_conformance.json")))["items"]
BY_ID = {i["id"]: i for i in ITEMS}

# (item id, answer, expect_pass)
CASES = [
    # --- the correct answers. These MUST score 1.0, or the card is unfair. ---
    ("R1.1_forbidden_key_must_be_absent",
     '{"patient_id": "P-4401", "ward": "cardiology"}', True),
    ("R1.2_null_means_absent", '{"sku": "X-9"}', True),
    ("R1.3_type_under_natural_language",
     '{"quantity": 3, "unit_price": 1.5, "in_stock": true, "reference": "007"}', True),
    ("R1.4_ambiguous_nesting",
     '{"shipment_id": "S-88", "destination": {"postcode": "44101", "country": "united states"},'
     ' "carrier": "nordex"}', True),
    ("R1.5_enum_nearest_is_wrong", '{"severity": "INFO", "code": 12}', True),
    ("R1.6_array_exact_and_ordered",
     '{"legs": [{"seq": 1, "icao": "LHR"}, {"seq": 2}, {"seq": 3, "icao": "JFK"}]}', True),

    # --- the natural WRONG answers. Every one must score below 1.0. ---
    # transcribes the doctor the schema forbids
    ("R1.1_forbidden_key_must_be_absent",
     '{"patient_id": "P-4401", "ward": "cardiology", "doctor": "Reyes"}', False),
    # null where OMIT was required -- the single most likely model behaviour here
    ("R1.2_null_means_absent", '{"sku": "X-9", "discount_pct": null, "coupon": null}', False),
    # invents a zero rather than omitting
    ("R1.2_null_means_absent", '{"sku": "X-9", "discount_pct": 0}', False),
    # "three" left as a word; 1.5 written as a fraction string
    ("R1.3_type_under_natural_language",
     '{"quantity": "three", "unit_price": "1 1/2", "in_stock": "true", "reference": 7}', False),
    # leading zeros destroyed by parsing 007 as a number -- ONE field wrong, so partial not zero
    ("R1.3_type_under_natural_language",
     '{"quantity": 3, "unit_price": 1.5, "in_stock": true, "reference": 7}', False),
    # flattens the nesting
    ("R1.4_ambiguous_nesting",
     '{"shipment_id": "S-88", "postcode": "44101", "country": "united states",'
     ' "carrier": "nordex"}', False),
    # the naive enum choice
    ("R1.5_enum_nearest_is_wrong", '{"severity": "WARN", "code": 12}', False),
    # fills the middle leg instead of omitting -- null and the literal "4" are both wrong
    ("R1.6_array_exact_and_ordered",
     '{"legs": [{"seq": 1, "icao": "LHR"}, {"seq": 2, "icao": null}, {"seq": 3, "icao": "JFK"}]}',
     False),
    ("R1.6_array_exact_and_ordered",
     '{"legs": [{"seq": 1, "icao": "LHR"}, {"seq": 2, "icao": "4"}, {"seq": 3, "icao": "JFK"}]}',
     False),
    # emits two legs instead of three
    ("R1.6_array_exact_and_ordered",
     '{"legs": [{"seq": 1, "icao": "LHR"}, {"seq": 3, "icao": "JFK"}]}', False),
]


def main():
    tasks = {t["id"]: t for t in A.load_card_v3()}
    print(f"loaded v3: {len(tasks)} item tasks")
    assert len(tasks) == 6, f"expected 6 R1 items, got {len(tasks)}"
    assert all(t["card_version"] == 3 for t in tasks.values()), "card_version must be 3"
    # the wrapper, not a bare expectation -- the v2 loader's bug in reverse
    some = tasks["R1_fencing::R1.1_forbidden_key_must_be_absent"]["spec"]
    assert set(some) == {"expect", "forbid", "forbid_all_other_keys"}, \
        f"spec must be the conformance wrapper, got keys {sorted(some)}"
    assert some["forbid"], "R1.1 must forbid a key, else the trap is not expressed"

    fails = []
    for item_id, answer, expect_pass in CASES:
        it = BY_ID[item_id]
        spec_w = {"expect": it.get("expect") or {},
                  "forbid": it.get("forbid") or [],
                  "forbid_all_other_keys": bool(it.get("forbid_all_other_keys"))}
        got, why = A.score_json_schema_strict_multi(spec_w, answer)
        ok = (got == 1.0) if expect_pass else (got < 1.0)
        mark = "ok  " if ok else "FAIL"
        label = "correct answer" if expect_pass else "natural wrong answer"
        print(f"  {mark} {item_id[:38]:38} {got:4.2f}  {label:20} {why[:44]}")
        if not ok:
            fails.append(f"{item_id}: expected {'1.0' if expect_pass else '<1.0'}, got {got} "
                         f"({label}) :: {why}")

    print()
    if fails:
        print(f"{len(fails)} case(s) wrong — the card does not measure what it claims:")
        for f in fails:
            print("  - " + f)
        return 1
    print(f"all {len(CASES)} cases behave: correct answers score 1.0, "
          f"every natural wrong answer scores below it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
