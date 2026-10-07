#!/usr/bin/env python3
"""Test the v2 scorers on answers I already know the verdict for, BEFORE any model is run.

A scorer I have not exercised is a scorer I cannot trust, and today's whole record is full of
instruments that answered a different question than the one asked. So: for each v2 scorer, feed
it a correct answer, a near-miss, a wrong answer, and -- for the two items designed to be won by
DOING NOTHING -- the answer that a model will most want to give instead.

The two null-items are the point of the card. If a guessed tool scores well, the trap is not a
trap and criterion 4 of CARD_v2.md is unreachable.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arena import (score_json_schema_multi, score_tool_call_multi,  # noqa: E402
                   score_code_repair_multi, load_card_v2, regroup_v2)

# LOAD THE REAL ITEMS. The first version of this test carried its own inline copies of the
# specs, which drifted from tasks/v2/*.json within the hour -- it was still asserting against a
# spec I had already fixed. A test that duplicates the source of truth tests the duplicate.
ITEMS = {t["id"].split("::")[-1]: t for t in load_card_v2()}

fails = []


def ck(name, cond, extra=""):
    print(f"  [{'x' if cond else ' '}] {name}" + (f"   {extra}" if extra else ""))
    if not cond:
        fails.append(name)


print("=== R1 fencing (json_schema_multi, PARTIAL CREDIT) ===")
spec = {"amount_cents": 1250, "currency": "eur"}
s, why = score_json_schema_multi(spec, '{"amount_cents": 1250, "currency": "EUR"}')
ck("perfect answer scores 1.0", s == 1.0, f"got {s} ({why})")
s, _ = score_json_schema_multi(spec, '{"amount": 1250, "currency": "eur"}')
ck("near-miss field name scores 0.5, not 0", abs(s - 0.5) < 1e-9, f"got {s} -- partial credit works")
s, _ = score_json_schema_multi(spec, '{"amount": 1250, "currency": "usd"}')
ck("two fields wrong scores 0.0", s == 0.0, f"got {s}")
s, _ = score_json_schema_multi({"readings": [{"sensor": "A", "value": 12},
                                             {"sensor": "B", "value": 12.5}]},
                               '{"readings":[{"sensor":"A","value":12},{"sensor":"B","value":12.5}]}')
ck("array/nested deep-equality works", s == 1.0, f"got {s}")
s, _ = score_json_schema_multi({"count": 3, "ratio": 0.5, "active": True},
                               '{"count":"3","ratio":"1/2","active":"true"}')
ck("string-where-number expected scores 0.0", s == 0.0, f"got {s}")

print("\n=== R2 chess (tool_call_multi) -- including the NO-TOOL-CORRECT trap ===")
s, why = score_tool_call_multi({"tool": "get_weather", "arguments": {"city": "lisbon"}},
                               '{"tool":"get_weather","arguments":{"city":"Lisbon"}}')
ck("correct tool + args scores 1.0", s == 1.0, f"got {s}")
s, _ = score_tool_call_multi({"tool": "get_weather", "arguments": {"city": "lisbon"}},
                             '{"tool":"get_weather","arguments":{}}')
ck("right tool, no args scores 0.5", abs(s - 0.5) < 1e-9, f"got {s}")

# THE TRAP: correct answer is null
TRAP = {"expect": {"tool": None}}
s, why = score_tool_call_multi(TRAP, '{"tool": null}')
ck("declining correctly scores 1.0", s == 1.0, f"got {s} ({why})")
s, why = score_tool_call_multi(TRAP, '{"tool": "get_weather", "arguments": {"city": "lisbon"}}')
ck("GUESSING a plausible tool scores 0.0  <- the trap bites", s == 0.0, f"got {s} ({why})")
s, _ = score_tool_call_multi(TRAP, '{"tool": "send_email", "arguments": {}}')
ck("guessing any other tool also scores 0.0", s == 0.0)

s, _ = score_tool_call_multi({"tool": "charge_card", "arguments": {"amount_cents": 4250}},
                             '{"tool":"charge_card","arguments":{"amount_cents":42.5}}')
ck("unit error ($ for cents) scores < 1.0", s < 1.0, f"got {s}")

print("\n=== R3 pitstop (code_repair_multi, EXECUTED) ===")
s, why = score_code_repair_multi(ITEMS["R3.1_floor"]["spec"],
                                 "def total(xs):\n    t = 0\n    for x in xs:\n        t = t + x\n    return t")
ck("correct fix passes its cases", s == 1.0, f"got {s} ({why})")
s, why = score_code_repair_multi(ITEMS["R3.1_floor"]["spec"], "def total(xs):\n    return sum(xs)")
ck("a DIFFERENT valid fix also passes (executed, not string-matched)", s == 1.0, f"got {s} ({why})")
s, why = score_code_repair_multi(ITEMS["R3.1_floor"]["spec"], "def total(xs):\n    return xs[0]")
ck("a wrong fix fails", s == 0.0, f"got {s}")
s, why = score_code_repair_multi(ITEMS["R3.2_must_not_break_others"]["spec"],
                                 "def absdiff(a, b):\n    return b - a")
ck("operand-swap fix FAILS the other case  <- must-not-break-others works", s == 0.0, f"got {s}")
s, why = score_code_repair_multi(ITEMS["R3.2_must_not_break_others"]["spec"],
                                 "def absdiff(a, b):\n    return abs(a - b)")
ck("the real fix passes all three cases", s == 1.0, f"got {s} ({why})")

MUT = ITEMS["R3.3_silent_mutation"]["spec"]
s, why = score_code_repair_multi(MUT, "def double_all(xs):\n    return [x * 2 for x in xs]")
ck("a NON-mutating fix PASSES the mutation item", s == 1.0, f"got {s} ({why})")
s, why = score_code_repair_multi(
    MUT,
    "def double_all(xs):\n    for i in range(len(xs)):\n        xs[i] = xs[i] * 2\n    return xs")
ck("silent MUTATION is detected (return value correct, input is not)", s == 0.0, f"got {s} ({why})")

CALLER = ITEMS["R3.5_bug_is_in_the_caller"]["spec"]
s, why = score_code_repair_multi(
    CALLER, "def parse_and_average(values):\n    return average([float(v) for v in values])")
ck("writing the CALLER passes", s == 1.0, f"got {s} ({why})")
s, why = score_code_repair_multi(
    CALLER, "def average(xs):\n    return sum(float(x) for x in xs) / len(xs)")
ck("'FIXING' average instead fails  <- the caller trap bites", s == 0.0, f"got {s} ({why})")

# THE SECOND TRAP: correct answer is to change nothing
s, why = score_code_repair_multi(ITEMS["R3.6_already_correct"]["spec"],
                                 "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n"
                                 "    if x > hi:\n        return hi\n    return x")
ck("returning correct code UNCHANGED scores 1.0", s == 1.0, f"got {s} ({why})")
s, why = score_code_repair_multi(ITEMS["R3.6_already_correct"]["spec"],
                                 "def clamp(x, lo, hi):\n    return max(lo, min(x, hi))")
ck("INVENTING a rewrite scores 0.0  <- the trap bites", s == 0.0, f"got {s} ({why})")

print("\n=== the loader and the regroup ===")
items = load_card_v2()
rounds = sorted({t["round_id"] for t in items})
ck("18 items across 3 rounds", len(items) == 18 and len(rounds) == 3,
   f"{len(items)} items / {len(rounds)} rounds")
ck("every item has a prompt, scorer and spec",
   all(t.get("prompt") and t.get("scorer") and t.get("spec") for t in items))
fake = {t["id"]: {"score": 1.0 if i % 2 else 0.0, "kind": t["kind"],
                  "metaphor": t["metaphor"], "truncated": False}
        for i, t in enumerate(items)}
reg = regroup_v2(fake)
ck("regroup folds 18 items into 3 rounds", len(reg) == 3, f"{list(reg)}")
ck("each round has 6 items", all(len(r["items"]) == 6 for r in reg.values()))
ck("round score is the mean of its items",
   all(abs(r["score"] - sum(i["score"] for i in r["items"].values()) / 6) < 1e-9
       for r in reg.values()))

print()
print("FAILURES: " + (", ".join(fails) if fails else "none"))
sys.exit(1 if fails else 0)
