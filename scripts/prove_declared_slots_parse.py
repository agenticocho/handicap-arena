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
import glob
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)                      # root scripts: already sys.path[0]; scripts/*: required
import cabinet_root as _root


def scope(pattern="*.json"):
    """[(kind, base, [paths])] over the DECLARED domain, entry by entry. No pattern is widened,
    no directory joins by existing."""
    rows = []
    for kind, base in _root.domain():
        rows.append((kind, base, sorted(glob.glob(os.path.join(base, pattern)))))
    return rows


def print_scope(rows, pattern):
    # THE SCOPE IS PRINTED WITH THE COUNT IT CONTRIBUTED: a count without its scope is not a count.
    for kind, base, hits in rows:
        print(f"  scope  {kind:16} {len(hits):4} {pattern}  {base}")

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

    # A DIAGNOSTIC THAT TRACEBACKS IS LESS USEFUL THAN ONE THAT REPORTS. Every failure path below produces a
    # STATE line and a non-zero exit, because the one thing this script must never do is fail silently and
    # let a reader take its absence for agreement.
    try:
        parsed = parse_declared_slots(CONTRACT)
    except (ValueError, OSError) as e:
        print(f"\nSTATE: BLOCKED. The contract's declared-slot block cannot be read:\n       {e}")
        print("=" * 98)
        return 1
    try:
        tgs = load_checker()
    except Exception as e:                                        # noqa: BLE001
        print(f"\n      NOTE: the check does not even IMPORT: {type(e).__name__}: {e}")
        tgs = None
    exports_parser = hasattr(tgs, "parse_declared_slots") if tgs is not None else False
    # THE VALUE THE CHECK USES, NOT THE VALUE ITS PARSER WOULD PRODUCE.
    governing = getattr(tgs, "DECLARED_SLOTS", None) if tgs is not None else None

    print(f"\n[1] GAME_CONTRACT.md's machine-readable block  ({len(parsed)} slots)")
    for k in sorted(parsed):
        print(f"      {k:18s} {parsed[k][:66]}")
    print(f"\n[2] the value the check ENFORCES -- DECLARED_SLOTS  "
          f"({len(governing) if governing else 0})")
    for k in sorted(governing or {}):
        print(f"      {k:18s} {governing[k][:66]}")

    only_contract = sorted(set(parsed) - set(governing or {}))
    only_check = sorted(set(governing or {}) - set(parsed))
    print(f"\n[3] the disagreement")
    print(f"      declared in the contract but NOT enforced : {only_contract}")
    print(f"      enforced but not in the contract          : {only_check}")

    print(f"\n[4] round keys actually present in the v6 bundles")
    rows = scope("*cardv6*.json")
    print_scope(rows, "*cardv6*.json")
    # A FIXTURE THAT DROPS A MEMBER IS A SILENT ZERO. This sweep FLATTENS the domain into one
    # namespace, so a basename occurring in two entries would silently drop one: refused, not merged.
    seen = {}
    for kind, base, hits in rows:
        for p in hits:
            seen.setdefault(os.path.basename(p), []).append((kind, p))
    clash = {n: v for n, v in seen.items() if len(v) > 1}
    if clash:
        print(f"STATE: BLOCKED. BASENAME COLLISION across domain entries: {clash} -- a fixture that "
              f"drops a member is a silent zero. Nothing was written.")
        return 1
    keys, bundles = {}, 0
    for kind, base, hits in rows:
        for p in hits:
            try:
                d = json.load(open(p, encoding="utf-8"))
            except Exception:
                continue
            for e in (d.get("results") or []):
                for rk in (e.get("rounds") or {}):
                    keys.setdefault(rk, 0)
                    keys[rk] += 1
            bundles += 1
    print(f"      {bundles} v6 bundles; round keys: " +
          ", ".join(f"{k} x{v}" for k, v in sorted(keys.items())))

    print(f"\n[5] WHAT THE CHECK ACTUALLY ENFORCES, AND WHETHER IT IS PARSED")
    print(f"      exposes parse_declared_slots()            : {exports_parser}")
    print(f"      DECLARED_SLOTS -- the value the check uses: "
          f"{sorted(governing) if governing is not None else 'ABSENT'}")

    print(f"\n[6] the two copies, and the one that governs")
    print(f"      contract declares      : {sorted(parsed)}")
    print(f"      checker enforces       : "
          f"{sorted(governing) if governing is not None else 'ABSENT'}")
    diff = sorted(set(parsed) ^ set(governing)) if governing is not None else sorted(parsed)
    print(f"      disagree               : {diff or 'no -- they agree'}")

    print(f"\n[7] verdict under the GOVERNING copy")
    bad = sorted(k for k in keys if governing is None or k not in governing)
    print(f"      v6 round keys          : {sorted(keys)}")
    print(f"      refused                : {bad if bad else 'none -- every bundle is admitted'}")

    print("\n" + "=" * 98)
    # THE VERDICT IS DERIVED FROM THE MEASUREMENT, NOT PRESUPPOSED. The first version asserted a disagreement
    # it had been written against; the repository moved and the assertion became false about the code while
    # the script kept printing it. A script whose conclusion is written into its own source is the same defect
    # as a caption nobody checks.
    if governing is None:
        print("STATE: BLOCKED. The check declares no DECLARED_SLOTS at all -- nothing governs, so every")
        print("       round key would be refused for a reason nobody stated.")
        rc = 1
    elif diff:
        print(f"STATE: BLOCKED. The contract and the check disagree on {diff}. A reader who amends the")
        print("       contract changes nothing if the check enforces the other copy.")
        rc = 1
    elif bad:
        print(f"STATE: BLOCKED. {bad} is declared in the contract and refused by the check.")
        rc = 1
    elif not exports_parser:
        print("STATE: DRIFTABLE. The copies agree TODAY but the check does not parse the contract --")
        print("       a hardcoded copy is a copy that can drift again, unwatched.")
        rc = 1
    else:
        print("STATE: SINGLE SOURCE. The check parses the contract and every v6 bundle is admitted.")
        rc = 0
    print("=" * 98)
    return rc


if __name__ == "__main__":
    sys.exit(main())
