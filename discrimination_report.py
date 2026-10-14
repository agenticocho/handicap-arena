#!/usr/bin/env python3
"""Where does v3's discrimination actually live? Corrected pass rate per item.

Written because criterion 2 FAILED and the failure is informative: the round no longer saturates the
STRONG models, and an item-level view says whether it separates the WEAK ones or whether they pile up
on a floor. An item that 90% of the field passes tells you nothing; an item that 10% passes tells you
almost nothing either. Discrimination lives in the middle band.
"""
import glob
import importlib.util
import json
import os
import re
import sys
from collections import defaultdict

# THE ABSOLUTE LITERAL IS GONE. It made this report read MAIN's record from ANY worktree -- a
# number about main, printed by a reader in a cabinet. The scope is the DECLARED DOMAIN of the tree
# the reader is sitting in, which is the same record object today (one tree object, four copies) and
# stops being able to lie the moment that stops being true.
HERE = os.path.dirname(os.path.abspath(__file__))
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

_spec = importlib.util.spec_from_file_location("_a", os.path.join(HERE, "arena.py"))
A = importlib.util.module_from_spec(_spec)
sys.argv = ["a", "--card", "v3"]
_spec.loader.exec_module(A)
TASKS = {t["id"].split("::")[-1]: t for t in A.load_card_v3()}

LO, HI = 0.15, 0.85


def strict(text):
    if not text:
        return None
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1).strip()
    i = t.find("{")
    while i != -1:
        d, s, e = 0, False, False
        for j in range(i, len(t)):
            c = t[j]
            if s:
                if e:
                    e = False
                elif c == "\\":
                    e = True
                elif c == '"':
                    s = False
                continue
            if c == '"':
                s = True
            elif c == "{":
                d += 1
            elif c == "}":
                d -= 1
                if d == 0:
                    try:
                        return json.loads(t[i:j + 1])
                    except Exception:
                        break
        i = t.find("{", i + 1)
    return None


def main():
    per = defaultdict(lambda: [0, 0])
    _rows = scope("*cardv3*.json")
    print_scope(_rows, "*cardv3*.json")
    for p in [p for _k, _b, hits in _rows for p in hits]:
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if d.get("harness") != "handicap-arena":
            continue
        for e in (d.get("results") or []):
            rd = (e.get("rounds") or {}).get("R1_fencing") or {}
            for iid, it in (rd.get("items") or {}).items():
                s = it.get("score") or 0
                raw = it.get("raw")
                raws = raw if isinstance(raw, list) else ([raw] if raw else [])
                t = TASKS.get(iid)
                if raws and t:
                    for r in raws:
                        o = strict(r)
                        if o is None:
                            continue
                        ns, _ = A.SCORERS[t["scorer"]](t["spec"], json.dumps(o))
                        s = max(s, ns)
                        break
                per[iid][1] += 1
                if s >= 1.0:
                    per[iid][0] += 1

    print("corrected per-item pass rate (discrimination band = %.0f%%-%.0f%%):" % (LO * 100, HI * 100))
    disc = 0
    for iid in sorted(per):
        g, t = per[iid]
        f = g / t
        band = "DISCRIMINATES" if LO <= f <= HI else ("SATURATED" if f > HI else "FLOOR")
        if band == "DISCRIMINATES":
            disc += 1
        print(f"  {iid:40} {g:2}/{t:2} = {f:5.1%}  {band}")
    print(f"\ndiscriminating items: {disc} of {len(per)}")
    print("A round whose items all sit at the top measures 'who is good'; all at the bottom measures")
    print("'who is bad'. Only the middle separates, and criterion 2 is the middle's absence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
