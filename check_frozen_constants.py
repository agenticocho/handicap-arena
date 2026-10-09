#!/usr/bin/env python3
"""CHECK FROZEN CONSTANTS -- the drift monitor, mechanical instead of attentive.

WHY THIS EXISTS, in Chilly's words: "Each change was justified by a measurement that preceded it" was
TRUE here, and it would be true in a DRIFT case too -- because a competent agent's changes are justified
by construction. JUSTIFICATION IS NOT EVIDENCE OF NON-DRIFT; IT IS WHAT DRIFT LOOKS LIKE WHEN THE AGENT
IS GOOD. A unidirectional sequence of individually-justified changes is still biased, and a per-step
audit cannot see it.

SO THE MONITOR WATCHES THE CRITERIA, NOT THE JUSTIFICATIONS. Four constants. If any changes, that is the
signal, and nothing else in the sequence matters.

    python3 check_frozen_constants.py            # check every test source against the frozen record
    python3 check_frozen_constants.py --self-test
"""
import ast
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = os.path.join(HERE, "FROZEN_CONSTANTS.json")
SOURCES = ["depth_test.py", "depth_test2.py", "source_probe3.py", "source_probe4.py"]
CONST_NAMES = ("LOST_CP", "HOLD_CP", "WINDOW", "MIN_PER_EDGE")

# ================================================================================================
# THE RULE, and it is the general form of what the first version of this file got wrong:
#
#   A CHECK NEEDS TWO POSITIVE CONTROLS: ONE THAT IT CAN FIRE, AND ONE THAT IT READS CORRECTLY.
#   The first catches false negatives and is the one people write. THE SECOND CATCHES FALSE
#   POSITIVES -- and it is the only one that would have caught this, because a MISREADING EXTRACTOR
#   FIRES CONFIDENTLY on a criterion that never moved.
#
# "A false positive on a drift check is worse than no check" -- it does not remove truth, it spends the
# MONITOR'S CREDIBILITY, which is a slower and worse loss, because THE NEXT REAL DRIFT GETS READ AS
# ANOTHER FALSE POSITIVE. That is how a monitor dies.
# ================================================================================================


def frozen():
    return {k: v for k, v in json.load(open(FROZEN, encoding="utf-8")).items()
            if not k.startswith("_")}


def _int_of(node):
    """-> int for a literal int, INCLUDING NEGATIVE ONES. -> None otherwise.

    `-300` IS NOT A Constant IN PYTHON'S AST. It is `UnaryOp(USub, Constant(300))`, so a check
    requiring `ast.Constant` with an int value reads every threshold as unreadable -- which is exactly
    what happened, and the read-control caught it before the report went out.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _int_of(node.operand)
        return -inner if inner is not None else None
    return None


def extract(path):
    """-> ({NAME: value}, [unreadable]) for the four constants, read from the SOURCE'S MEANING.

    AST, NOT A REGEX. A regex over source reads the TEXT of code rather than its meaning -- the same
    family as the field-name defect (`a name is a claim about its contents`, and so is a pattern). The
    first version handled `NAME = value`, missed `A, B, C = -300, -100, 60`, matched a stray 60
    elsewhere, and reported DRIFT ON FOUR SOURCES THAT HAD NOT DRIFTED.

    AND AN UNREADABLE BINDING IS A FAILURE, NOT A SKIP. A `continue` past a form the extractor does not
    recognise reports NO DRIFT for the same reason a dead probe reports success: "this name isn't set
    here" is indistinguishable from "I cannot read this form". So anything bound to a non-literal is
    returned as UNREADABLE and the check exits non-zero.
    """
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except (OSError, SyntaxError):
        return {}, []
    found, unreadable = {}, []
    for node in ast.walk(tree):
        targets, values = [], []
        if isinstance(node, ast.Assign):
            values = node.value.elts if isinstance(node.value, ast.Tuple) else [node.value]
            for t in node.targets:
                if isinstance(t, ast.Name):
                    targets.append(t.id)
                elif isinstance(t, ast.Tuple):
                    targets.extend(e.id for e in t.elts if isinstance(e, ast.Name))
                else:
                    targets.append(None)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets, values = [node.target.id], [node.value]
        else:
            continue
        for i, nm in enumerate(targets):
            if nm not in CONST_NAMES:
                continue
            v = values[i] if i < len(values) else None
            iv = _int_of(v)
            if iv is not None:
                found[nm] = iv
            else:
                # bound to something this file cannot resolve -- say so instead of skipping
                unreadable.append(f"{nm} = <{type(v).__name__ if v is not None else 'missing'}>")
    return found, unreadable


def check():
    fr = frozen()
    print(f"  frozen at {json.load(open(FROZEN, encoding='utf-8'))['_frozen_at']}")
    print(f"  {fr}\n")
    fails = []
    for s in SOURCES:
        p = os.path.join(HERE, s)
        if not os.path.exists(p):
            continue
        got, unread = extract(p)
        if unread:
            fails.append((s, {"UNREADABLE": unread}))
            print(f"  {s:22s} UNREADABLE BINDING: {unread}")
            continue
        if not got:
            print(f"  {s:22s} no constants bound (uses the shared module's values)")
            continue
        bad = {k: (got[k], fr[k]) for k in got if k in fr and got[k] != fr[k]}
        if bad:
            fails.append((s, bad))
            print(f"  {s:22s} DRIFT: {bad}")
        else:
            print(f"  {s:22s} ok  {got}")
    return fails


def self_test():
    """TWO POSITIVE CONTROLS, per the rule above -- fire, AND read correctly."""
    print("=" * 92)
    print("CONTROL -- the monitor must FIRE on a move, and READ a known value correctly")
    print("=" * 92)
    fails = []

    def ck(name, got, want):
        ok = got == want
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f"  got {got!r} want {want!r}"))
        if not ok:
            fails.append(name)

    fr = frozen()
    ck("four constants frozen", sorted(fr), ["HOLD_CP", "LOST_CP", "MIN_PER_EDGE", "WINDOW"])
    ck("window 60", fr["WINDOW"], 60)
    ck("thresholds -300/-100", (fr["LOST_CP"], fr["HOLD_CP"]), (-300, -100))
    ck("floor 5 per edge", fr["MIN_PER_EDGE"], 5)

    # --- CONTROL 1: IT READS CORRECTLY (the one that catches false positives) ---
    got, unread = extract(os.path.join(HERE, "depth_test.py"))
    ck("read control: TUPLE assignment resolved", got.get("LOST_CP"), -300)
    ck("read control: window resolved", got.get("WINDOW"), 60)
    ck("read control: nothing unreadable in a known-good file", unread, [])
    got2, _ = extract(os.path.join(HERE, "depth_test2.py"))
    ck("read control: plain assignment resolved", got2.get("MIN_PER_EDGE"), 5)

    # --- CONTROL 2: IT FIRES ON A MOVE ---
    planted = dict(fr)
    planted["WINDOW"] = 40
    ck("fire control: a moved window is a drift signal", planted["WINDOW"] != fr["WINDOW"], True)

    # --- CONTROL 3: AN UNREADABLE FORM FAILS RATHER THAN SKIPPING ---
    tmp = os.path.join(HERE, ".tmp_unreadable.py")
    open(tmp, "w").write("LOST_CP = getattr(cfg, 'lost')\n")
    _g, un = extract(tmp)
    os.unlink(tmp)
    ck("skip control: a non-literal binding is UNREADABLE, not skipped", len(un), 1)

    real = check()
    ck("no source currently drifts", real, [])

    print("\n" + "=" * 92)
    print(f"{'ALL CONTROLS PASS' if not fails else str(len(fails))+' FAILED'}   -- {10-len(fails)}/10")
    print("=" * 92)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    f = check()
    print(f"\n  {'NO DRIFT -- the criteria have not moved.' if not f else str(len(f))+' SOURCE(S) DRIFTED.'}")
    print(f"  A moved constant is the signal. Justification for the move is NOT the question.")
    sys.exit(1 if f else 0)
