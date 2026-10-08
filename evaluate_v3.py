#!/usr/bin/env python3
"""CARD v3 — the criterion verdict, and the FAILURE AUDIT the raw output finally makes possible.

THE BAR IS THE ONE FROZEN IN CARD_v3.md BEFORE THE RUN, quoted so it cannot drift:

  1. R1 no longer saturated      -- fewer than 60% of entries score 6/6 on R1   (v2: 26/33 = 79%)
  2. the low end is populated    -- at least 4 entries below 0.34 aggregate      (v2: 2)
  3. v2's criteria 1 and 3 STAND FAILED and are not re-scored; v3 is a new version with its own bar
  4. card_version is a hard partition; a v3 score is never pooled with v1 or v2

AND THE AUDIT THAT WAS IMPOSSIBLE UNTIL TODAY. `_first_json` parses with a GREEDY `\\{.*\\}` -- from
the first brace to the last -- so a model emitting prose around an object, or two objects, is called
"unparseable" by the regex rather than by its own behaviour. That was unanswerable while the model's
output was discarded at scoring time. It is stored now, so this script re-parses every failing raw
with a stricter, NON-GREEDY extractor and reports how many verdicts change.

If some do, the original score was a scoring bug and this is a MEASUREMENT of it, not a complaint.
"""
import glob
import json
import os
import re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
ROUND = "R1_fencing"
SEVERE = 0.34


def load(card=3):
    rows = []
    for p in sorted(glob.glob(os.path.join(RESULTS, f"*cardv{card}*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if d.get("harness") != "handicap-arena":
            continue
        for e in (d.get("results") or []):
            e["_file"] = os.path.basename(p)
            rows.append(e)
    return rows


def strict_first_json(text):
    """A NON-GREEDY extractor, for auditing the greedy one. Returns the first complete object."""
    if not text:
        return None
    t = text.strip()
    # strip code fences -- a fence is not a parse failure
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1).strip()
    start = t.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(t)):
            ch = t[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(t[start:i + 1])
                    except Exception:
                        break
        start = t.find("{", start + 1)
    return None


def main():
    rows = load(3)
    if not rows:
        print("no card-v3 bundles with results")
        return 1

    # ---- the round under test -------------------------------------------------
    r1 = []
    for e in rows:
        rd = (e.get("rounds") or {}).get(ROUND) or {}
        if rd:
            r1.append((e, rd))
    n = len(r1)
    full = sum(1 for _, rd in r1 if (rd.get("wins") or 0) >= (rd.get("trials") or 0))
    # COMPARE THE PRIMITIVE, NOT THE RENDERING. `aggregate` is stored rounded to 4dp, so a decision on
    # it is a decision on a rendering. `wins`/`trials` live on the ROUND row, which is the second element
    # of each tuple -- the first version of this line read `e["rd"]` off the ENTRY dict and was wrong.
    below = sum(1 for _, rd in r1 if (rd.get("wins") or 0) / (rd.get("trials") or 1) < SEVERE)
    pct_full = full / n if n else 0

    print("=" * 78)
    print(f"CARD v3 — {len(rows)} bundles carrying a measurement; {n} have {ROUND}")
    print("=" * 78)

    print()
    print("--- CRITERION 1: R1 no longer saturated (needs < 60% at 6/6) ---")
    print(f"    {full}/{n} score 6/6  =  {pct_full:.1%}    (v2 was 79%)")
    ok1 = pct_full < 0.60
    print(f"    {'PASS' if ok1 else 'FAIL'}")

    print()
    print(f"--- CRITERION 2: low end populated (needs >= 4 below {SEVERE}) ---")
    print(f"    {below} entries below {SEVERE}    (v2 had 2)")
    ok2 = below >= 4
    print(f"    {'PASS' if ok2 else 'FAIL'}")

    print()
    print("--- CRITERION 3: v2's 1 and 3 STAND FAILED, not re-scored ---")
    print("    PASS by construction: this report does not touch v2's numbers.")

    print()
    print("--- CRITERION 4: card_version is a hard partition ---")
    cvs = Counter(e.get("card_version") for e in rows)
    print(f"    card_version in this report: {dict(cvs)}")
    ok4 = set(cvs) == {3}
    print(f"    {'PASS' if ok4 else 'FAIL — pooled with another card'}")

    print()
    print("--- PER-ITEM PASS RATE (is the round measuring six things or one?) ---")
    per = defaultdict(lambda: [0, 0])
    for _, rd in r1:
        for iid, it in (rd.get("items") or {}).items():
            per[iid][1] += 1
            if (it.get("score") or 0) >= 1.0:
                per[iid][0] += 1
    for iid in sorted(per):
        got, tot = per[iid]
        bar = "#" * int(24 * got / tot)
        verdict = "SATURATED" if got / tot > 0.85 else ("FLOOR" if got / tot < 0.15 else "spreads")
        print(f"    {iid[:42]:42} {got:2}/{tot:2} {bar:24} {verdict}")

    # ---- THE AUDIT: does the greedy parser change any verdict? ----------------
    print()
    print("--- THE AUDIT: re-parse every failing item's stored raw with a STRICT extractor ---")
    changed, unparseable, recovered = [], 0, 0
    for e, rd in r1:
        for iid, it in (rd.get("items") or {}).items():
            raw = it.get("raw")
            raws = raw if isinstance(raw, list) else ([raw] if raw else [])
            if not raws or (it.get("score") or 0) >= 1.0:
                continue
            reason = (it.get("reason") or "")
            if "unparseable" not in reason and "no json" not in reason:
                continue
            unparseable += 1
            for r in raws:
                if strict_first_json(r) is not None:
                    recovered += 1
                    changed.append((e["_file"], iid, r[:70]))
                    break
    print(f"    items whose verdict was `unparseable`: {unparseable}")
    print(f"    of those, the strict extractor FINDS a JSON object: {recovered}")
    if not recovered:
        print("    -> no verdict changes: the greedy parser was not the cause of these failures.")
        print()
        print("=" * 78)
        verd = {"1 saturation": ok1, "2 low end": ok2, "4 partition": ok4}
        print("VERDICT: " + "  ".join(f"{k}={'PASS' if v else 'FAIL'}" for k, v in verd.items()))
        print("The bar does not move to accommodate the result. A re-derivation is not a re-scoring.")
        return 0

    # FINDING AN OBJECT IS NOT PASSING THE ITEM. The first version of this audit stopped at
    # "the extractor finds JSON" and printed "THE GREEDY PARSER WAS THE FAILURE" -- which is a
    # narrower claim dressed as a wider one: it says the parse succeeded, not that the ANSWER was
    # right. A re-parse must be RE-SCORED before it can say anything about the score.
    import importlib.util
    import sys as _sys
    _spec = importlib.util.spec_from_file_location("arena", os.path.join(HERE, "arena.py"))
    A = importlib.util.module_from_spec(_spec)
    _sys.argv = ["arena.py", "--card", "v3"]
    _spec.loader.exec_module(A)

    tasks = {t["id"].split("::")[-1]: t for t in A.load_card_v3()}
    rescored, to_score = 0, []
    for e, rd in r1:
        for iid, it in (rd.get("items") or {}).items():
            if (it.get("score") or 0) >= 1.0:
                continue
            raw = it.get("raw")
            raws = raw if isinstance(raw, list) else ([raw] if raw else [])
            if not raws:
                continue
            t = tasks.get(iid)
            if not t:
                continue
            for r in raws:
                obj = strict_first_json(r)
                if obj is None:
                    continue
                new, why = A.SCORERS[t["scorer"]](t["spec"], json.dumps(obj))
                if new > (it.get("score") or 0):
                    rescored += 1
                    to_score.append((iid, it.get("score") or 0, new, (it.get("reason") or "")[:34]))
                break

    print()
    print(f"    RE-SCORED, not merely re-parsed: {rescored} item(s) would score HIGHER")
    if to_score:
        print("    (the greedy parser cost these points outright, and the raw proves it)")
        for iid, old, new, why in to_score[:10]:
            print(f"       {iid[:38]:38} {old:.2f} -> {new:.2f}   [was: {why}]")
    else:
        print("    -> the parser found objects the scorer still rejects: those failures are REAL,")
        print("       and the earlier 'greedy parser was the failure' line was too strong.")

    # THE CORRECTED VERDICT, ON CORRECTED INPUTS.
    #
    # A correction that RAISES scores can push entries back to 6/6 (criterion 1) and lift them off the
    # floor (criterion 2) -- so the verdict above, computed on the RECORDED scores, is not final. The
    # bar does not move; the INPUTS are corrected and the same bar is applied to them. Reporting only
    # the recorded verdict would be choosing the number that reads better, which is the whole thing
    # this record keeps catching.
    fixed = {}
    for e, rd in r1:
        for iid, it in (rd.get("items") or {}).items():
            raw = it.get("raw")
            raws = raw if isinstance(raw, list) else ([raw] if raw else [])
            t = tasks.get(iid)
            if not raws or not t:
                continue
            for r in raws:
                obj = strict_first_json(r)
                if obj is None:
                    continue
                new, _why = A.SCORERS[t["scorer"]](t["spec"], json.dumps(obj))
                if new > (it.get("score") or 0):
                    fixed[(e["_file"], iid)] = new
                break

    def corrected(rd, fname):
        wins, trials = 0.0, 0
        for iid, it in (rd.get("items") or {}).items():
            trials += 1
            wins += fixed.get((fname, iid), it.get("score") or 0)
        return wins, trials

    c_full = c_below = 0
    for e, rd in r1:
        w, t_ = corrected(rd, e["_file"])
        if t_ and w >= t_:
            c_full += 1
        agg = (w / t_) if t_ else 0
        if agg < SEVERE:
            c_below += 1
    print()
    print("--- THE VERDICT ON CORRECTED INPUTS (the bar, unmoved) ---")
    print(f"    1. saturation : {c_full}/{n} = {c_full / n:.1%} at 6/6   "
          f"{'PASS' if c_full / n < 0.60 else 'FAIL'}   (recorded: {pct_full:.1%})")
    print(f"    2. low end    : {c_below} below {SEVERE}            "
          f"{'PASS' if c_below >= 4 else 'FAIL'}   (recorded: {below})")
    if (c_full / n < 0.60) != ok1 or (c_below >= 4) != ok2:
        print()
        print("    *** THE CORRECTION CHANGES THE VERDICT. The recorded scores were understated by a")
        print("        measured amount, and the bar is the bar. The corrected result is the result. ***")

    print()
    print("=" * 78)
    # THE SUMMARY REPORTS THE CORRECTED RESULT, because the corrected result IS the result. Printing
    # the recorded verdict here while the block above showed it flipping would be two numbers for one
    # question -- the defect this whole day keeps finding.
    ok1c = (c_full / n) < 0.60
    ok2c = c_below >= 4
    verd = {"1 saturation": ok1c, "2 low end": ok2c, "4 partition": ok4}
    print("VERDICT (on corrected inputs): "
          + "  ".join(f"{k}={'PASS' if v else 'FAIL'}" for k, v in verd.items()))
    print(f"  recorded scores would have said: 1={'PASS' if ok1 else 'FAIL'} "
          f"2={'PASS' if ok2 else 'FAIL'} 4={'PASS' if ok4 else 'FAIL'}")
    print("The bar does not move to accommodate the result. A re-derivation is not a re-scoring --")
    print("and a corrected INPUT is not a moved bar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
