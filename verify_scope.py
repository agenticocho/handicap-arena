#!/usr/bin/env python3
"""Verify Chilly's four disagreements (D1-D4) and the no-raw finding, MEASURED not accepted.

D4 is the one that decides the verdict: if the correction is scoped to the unparseable-class items only,
Qwen3.5-2B stays at 0.3333 and criterion 2 PASSES (4 below 0.34). The 3 comes from also re-scoring the
two items whose reason string was OVERWRITTEN to TRUNCATED. So this script partitions the failing
items by class and recomputes the count under each scope, and separately checks whether the truncated
raws contain THE ITEM'S ANSWER (which is what would justify re-scoring them) or merely a stray fragment.
"""
import glob
import importlib.util
import json
import os
import re
import sys

HERE = "/home/chilly1/workspace/ocho_arena"
_spec = importlib.util.spec_from_file_location("_a", os.path.join(HERE, "arena.py"))
A = importlib.util.module_from_spec(_spec)
sys.argv = ["a", "--card", "v3"]
_spec.loader.exec_module(A)
TASKS = {t["id"].split("::")[-1]: t for t in A.load_card_v3()}


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
    rows = []
    for p in sorted(glob.glob(os.path.join(HERE, "results", "*cardv3*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if d.get("harness") != "handicap-arena":
            continue
        for e in (d.get("results") or []):
            rd = (e.get("rounds") or {}).get("R1_fencing") or {}
            if rd:
                rows.append((os.path.basename(p), e, rd))

    # ---- classify every failing item -----------------------------------------
    failing, no_raw = [], []
    for f, e, rd in rows:
        for iid, it in (rd.get("items") or {}).items():
            sc = it.get("score") or 0
            if sc >= 1.0:
                continue
            raw = it.get("raw")
            raws = raw if isinstance(raw, list) else ([raw] if raw else [])
            reason = it.get("reason") or ""
            cls = ("unparseable" if "unparseable" in reason else
                   "no_json" if "no json" in reason.lower() else
                   "truncated" if "TRUNCATED" in reason else
                   "other")
            if not raws:
                no_raw.append((f, iid, reason[:40], sc))
                continue
            new, _ = 0.0, None
            t = TASKS.get(iid)
            for r in raws:
                o = strict(r)
                if o is None:
                    continue
                ns, _w = A.SCORERS[t["scorer"]](t["spec"], json.dumps(o))
                new = max(new, ns)
                break
            failing.append({"file": f, "iid": iid, "old": sc, "new": new,
                            "cls": cls, "reason": reason[:46], "raw": raws[0][:90]})

    print(f"D3a  failing items (excluding no-raw): {len(failing)}")
    print(f"D3b  items with NO RAW STORED AT ALL : {len(no_raw)}")
    for f, iid, rsn, sc in no_raw:
        print(f"       {f[:40]:40} {iid[:34]:34} score={sc} reason={rsn!r}")

    from collections import Counter
    by_cls = Counter(x["cls"] for x in failing)
    print(f"\n     failing items by CLASS: {dict(by_cls)}")
    lit = sum(1 for x in failing if "unparseable" in x["reason"])
    print(f"     literal 'unparseable' string: {lit}   (+1 'no json object' = {by_cls['no_json']} "
          f"-> the '15' was a class UNION, as Chilly said)")

    # ---- D2: how many re-score higher, over ALL vs within the unparseable class
    all_up = [x for x in failing if x["new"] > x["old"]]
    unp = [x for x in failing if x["cls"] == "unparseable"]
    unp_up = [x for x in unp if x["new"] > x["old"]]
    print(f"\nD2   items that re-score HIGHER, over all failing items : {len(all_up)}")
    print(f"     items that re-score HIGHER, within unparseable class : {len(unp_up)}")
    print(f"     -> the gap is the {len(all_up) - len(unp_up)} truncated-class item(s), as Chilly said")

    # ---- D1: exactly 0.00 -> 1.00, over all vs excluding truncated ----------
    exact_all = [x for x in all_up if x["old"] == 0.0 and x["new"] >= 1.0]
    exact_unp = [x for x in unp_up if x["old"] == 0.0 and x["new"] >= 1.0]
    print(f"\nD1   items moving exactly 0.00 -> 1.00, all classes      : {len(exact_all)}")
    print(f"     ...excluding the truncated class                    : {len(exact_unp)}")
    for x in exact_all:
        print(f"       [{x['cls']:12}] {x['iid'][:36]:36} {x['file'][:34]}")

    # ---- D3: are the truncated items items on ONE entry? -------------------
    trunc = [x for x in failing if x["cls"] == "truncated"]
    print(f"\nD3c  truncated-class ITEMS: {len(trunc)}   distinct ENTRIES: {len({x['file'] for x in trunc})}")
    for x in trunc:
        print(f"       {x['file'][:42]:42} {x['iid'][:34]:34} {x['old']:.2f} -> {x['new']:.2f}")

    # ---- THE DECIDING QUESTION: do the truncated raws hold THE ITEM'S ANSWER?
    print("\nTHE DECIDING QUESTION -- does the truncated raw contain the ITEM'S OWN ANSWER?")
    for x in trunc:
        t = TASKS.get(x["iid"])
        print(f"  {x['iid']}")
        print(f"    raw : {x['raw']!r}")
        if t:
            print(f"    spec: {json.dumps(t['spec'])[:150]}")

    # ---- D4: the below-0.34 count under each SCOPE -------------------------
    def count_below(scope):
        n = 0
        for f, e, rd in rows:
            items = rd.get("items") or {}
            tot = 0.0
            for iid, it in items.items():
                sc = it.get("score") or 0
                x = next((y for y in failing if y["file"] == f and y["iid"] == iid), None)
                if x and scope(x):
                    sc = max(sc, x["new"])
                tot += sc
            if items and tot / len(items) < 0.34:
                n += 1
        return n

    print("\nD4   below-0.34 count under each SCOPE (bar is >= 4):")
    b_rec = count_below(lambda x: False)
    b_narrow = count_below(lambda x: x["cls"] == "unparseable")
    b_wide = count_below(lambda x: True)
    print(f"       recorded (no correction)            : {b_rec}   {'PASS' if b_rec >= 4 else 'FAIL'}")
    print(f"       NARROW -- unparseable class only    : {b_narrow}   "
          f"{'PASS' if b_narrow >= 4 else 'FAIL'}")
    print(f"       WIDE   -- all classes with a raw    : {b_wide}   "
          f"{'PASS' if b_wide >= 4 else 'FAIL'}")
    print("\n  A verdict that flips on the scope of its own correction is CONDITIONAL, and the scope")
    print("  must be stated as a choice rather than presented as the result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
