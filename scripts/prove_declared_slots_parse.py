#!/usr/bin/env python3
"""PROOF, not patch: would parsing the namespace from GAME_CONTRACT.md fix the v6 block?

This script writes NOTHING and touches NO frozen file. It exists because the fix the error message
recommends cannot be taken on trust: run_card.py tells the reader to AMEND GAME_CONTRACT.md, and the
question is whether that instruction can ever be true.

It answers three questions with measurements:

  1. What does GAME_CONTRACT.md's machine-readable block actually contain?
  2. What does test_game_states.py's frozen DECLARED_SLOTS actually contain?
  3. Do they disagree, and does the disagreement explain the v6 refusal exactly?

    python3 scripts/prove_declared_slots_parse.py
"""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRACT = os.path.join(HERE, "GAME_CONTRACT.md")
BEGIN = "=== DECLARED_SLOTS BEGIN ==="
END = "=== DECLARED_SLOTS END ==="


def parse_declared_slots(path):
    """The parser GAME_CONTRACT.md says exists: a flat line format between EXACT markers.

    `<key><whitespace><description>` and nothing else. No markdown table, no regex over prose -- the
    contract is explicit that a regex over a table is the greedy `{.*}` class this project already paid for.
    """
    text = open(path, encoding="utf-8").read()
    if BEGIN not in text or END not in text:
        raise ValueError(f"markers not found in {path}")
    body = text.split(BEGIN, 1)[1].split(END, 1)[0]
    slots = {}
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("```"):
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            slots[parts[0]] = parts[1].strip()
    # THE EMPTY-LIST RULE, POINTED AT THE PARSER: zero slots means every round key is undeclared and a run
    # is refused for a reason nobody stated.
    if not slots:
        raise ValueError(f"zero slots parsed from {path} -- the markers were found and the body was empty")
    return slots


def load_checker():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)          # the checker imports its own neighbours by bare name
    spec = importlib.util.spec_from_file_location("tgs", os.path.join(HERE, "test_game_states.py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules["tgs"] = m
    spec.loader.exec_module(m)
    return m


def main():
    print("=" * 98)
    print("PROOF -- could parsing the namespace from GAME_CONTRACT.md clear the v6 refusal?")
    print("=" * 98)

    parsed = parse_declared_slots(CONTRACT)
    tgs = load_checker()
    frozen = tgs.DECLARED_SLOTS

    print(f"\n[1] GAME_CONTRACT.md's machine-readable block  ({len(parsed)} slots)")
    for k in sorted(parsed):
        print(f"      {k:18s} {parsed[k][:66]}")
    print(f"\n[2] test_game_states.py DECLARED_SLOTS -- THE FROZEN COPY THE CHECK READS  ({len(frozen)})")
    for k in sorted(frozen):
        print(f"      {k:18s} {frozen[k][:66]}")

    only_contract = sorted(set(parsed) - set(frozen))
    only_frozen = sorted(set(frozen) - set(parsed))
    print(f"\n[3] the disagreement")
    print(f"      declared in the contract but NOT enforced : {only_contract}")
    print(f"      enforced but not in the contract          : {only_frozen}")

    print(f"\n[4] round keys actually present in the v6 bundles")
    rdir = os.path.join(HERE, "results")
    keys, bundles = {}, 0
    for f in sorted(os.listdir(rdir)):
        if not f.endswith(".json") or "cardv6" not in f:
            continue
        try:
            d = json.load(open(os.path.join(rdir, f), encoding="utf-8"))
        except Exception:
            continue
        for e in (d.get("results") or []):
            for rk in (e.get("rounds") or {}):
                keys.setdefault(rk, 0)
                keys[rk] += 1
        bundles += 1
    print(f"      {bundles} v6 bundles; round keys: " +
          ", ".join(f"{k} x{v}" for k, v in sorted(keys.items())))

    print(f"\n[5] WHERE DOES THE CHECKER GET ITS NAMESPACE?")
    parses = hasattr(tgs, "parse_declared_slots")
    print(f"      test_game_states.py exposes parse_declared_slots() : {parses}")
    if parses:
        try:
            live = tgs.parse_declared_slots()
            print(f"      ...and it parses {len(live)} slots from the contract")
        except Exception as e:                                    # noqa: BLE001
            print(f"      ...and it RAISED: {e}")
            live = {}
    else:
        live = frozen

    print(f"\n[6] the two copies, and the one that governs")
    print(f"      contract declares      : {sorted(parsed)}")
    print(f"      checker enforces       : {sorted(live)}")
    print(f"      disagree               : {sorted(set(parsed) ^ set(live)) or 'no -- they agree'}")

    print(f"\n[7] verdict under the GOVERNING copy")
    bad = sorted(k for k in keys if k not in live)
    print(f"      v6 round keys          : {sorted(keys)}")
    print(f"      refused                : {bad if bad else 'none -- every bundle is admitted'}")

    print("\n" + "=" * 98)
    # THE VERDICT IS DERIVED FROM THE MEASUREMENT, NOT PRESUPPOSED. The first version of this script asserted
    # a disagreement it had been written against; the repository moved and the assertion became false about
    # the code while the script kept printing it. A script whose conclusion is written into its own source is
    # the same defect as a caption nobody checks.
    if set(parsed) == set(live) and not bad:
        print("STATE: SINGLE SOURCE. The checker parses the contract and every v6 bundle is admitted.")
        rc = 0
    elif bad:
        print(f"STATE: BLOCKED. {bad} is declared in the contract and refused by the checker -- the remedy")
        print("       message sends its reader to a file the check does not read.")
        rc = 1
    else:
        print("STATE: the copies agree but the checker does not parse the contract -- they can drift again.")
        rc = 1
    print("=" * 98)
    return rc


if __name__ == "__main__":
    sys.exit(main())
