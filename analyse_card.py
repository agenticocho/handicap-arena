#!/usr/bin/env python3
"""Per-round diagnosis of the card: is anything discriminating?

REWRITTEN 2026-10-07 FOR THE card_version PARTITION.

The previous version pooled v1 and v2 bundles into one table and printed:

    graded entries: 75
    R1_fencing   mean win rate 118.7%

I FIRST DIAGNOSED THIS AS POOLING, AND THAT DIAGNOSIS WAS WRONG. Pooling the two cards measures
82.4% -- under 100%. The actual cause is a HARDCODED DENOMINATOR: the line was
`sum(k*v) / (3*n)`, i.e. wins divided by 3, applied to v2 rounds that carry 6 items. v1's 3-item
rounds were fine; v2's 6-item rounds were divided by 3 and so reported up to 200%.

COROLLARY, AND IT MATTERS MORE THAN THE BUG: my first guard tested "rate > 100%" and would NOT
have caught the original defect, which sat at 82.4%. A guard that cannot fail on the bug it was
written for is decoration -- it makes a run LOOK verified. Replaced with the invariant that
actually holds: ONE items-per-round within a card, asserted.

The consequence that IS real: pooled, this script silently compared a 3-item measurement with a
6-item one, which is precisely what clause 3 of FRONTEND_CONTRACT_ACCEPTANCE.md forbids. I wrote
the clause and my own tool broke it.
"""
import glob, json, os, sys
from collections import Counter, defaultdict

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
ORDER = ["White", "Yellow", "Orange", "Green", "Blue", "Purple", "Brown", "Black"]


def load():
    """Group entries BY CARD VERSION. Two cards are two measurements and are never pooled."""
    by_card = defaultdict(list)
    for p in sorted(glob.glob(os.path.join(RESULTS, "*.json"))):
        try:
            d = json.load(open(p))
        except Exception:
            continue
        if d.get("harness") != "handicap-arena":
            continue
        for r in (d.get("results") or []):
            r["_file"] = os.path.basename(p)
            # `card_version` lives on the ENTRY row, not the bundle. It is PRESENT on all 33 v2
            # rows and ABSENT on all 42 v1 rows. Defaulting absent -> 1 is how v1 is identified,
            # but the two cases must stay distinguishable, so absent gets its OWN key rather
            # than being silently folded into 1.
            by_card[r.get("card_version", "ABSENT")].append(r)
    return by_card


def analyse(card, entries):
    print("=" * 78)
    if card == "ABSENT":
        print(f"CARD version ABSENT — {len(entries)} graded entries")
        print("  These rows carry NO card_version field at all. They are the v1 bundles. Treating")
        print("  'absent' as '1' is convenient but NOT the same claim -- a front end that does it")
        print("  silently cannot tell a v1 row from a row whose field was lost.")
    else:
        print(f"CARD v{card} — {len(entries)} graded entries")
    print("=" * 78)
    belts = Counter((e.get("grade") or {}).get("belt", "?") for e in entries)
    print("  belts: " + "  ".join(f"{b} {belts.get(b,0)}" for b in ORDER if belts.get(b)))

    rounds = defaultdict(list)
    for e in entries:
        for rk, rd in (e.get("rounds") or {}).items():
            rounds[rk].append(rd)

    print()
    print(f"  {'round':12s} {'items':>5} {'zero':>5} {'part':>5} {'full':>5}  {'win rate':>9}  verdict")
    for rk in sorted(rounds):
        rds = rounds[rk]
        trials = {r.get("trials") or 0 for r in rds}
        # THE INVARIANT THAT ACTUALLY HOLDS: one items-per-round within a card. The original bug
        # was a hardcoded /3 applied to 6-item rounds; a "rate > 100%" guard does not catch it,
        # because pooling puts the rate at 82.4%. This does.
        assert len(trials) == 1, (
            f"{rk}: {len(trials)} different items-per-round in one card ({sorted(trials)}) — "
            f"this table is mixing measurements that must not be compared.")
        n_items = int(sorted(trials)[0]) if trials else 0
        zero = sum(1 for r in rds if (r.get("wins") or 0) == 0)
        full = sum(1 for r in rds if (r.get("wins") or 0) >= n_items)
        part = len(rds) - zero - full
        won = sum(r.get("wins") or 0 for r in rds)
        tot = sum(r.get("trials") or 0 for r in rds)
        rate = won / tot if tot else 0
        assert rate <= 1.0001, (
            f"{rk}: win rate {rate:.1%} exceeds 100% — a denominator is wrong somewhere.")
        # a round discriminates only if it is neither always-passed nor always-failed
        frac_full = full / len(rds) if rds else 0
        frac_zero = zero / len(rds) if rds else 0
        verdict = ("SATURATED" if frac_full > 0.60 else
                   "FLOOR" if frac_zero > 0.60 else "discriminates")
        print(f"  {rk:12s} {n_items:5d} {zero:5d} {part:5d} {full:5d}  {rate:9.1%}  {verdict}")

    print()
    print("  failure modes per round:")
    for rk in sorted(rounds):
        cap = sum((r.get("finish_reasons") or {}).get("length", 0) for r in rounds[rk])
        tot = sum(r.get("trials") or 0 for r in rounds[rk])
        won = sum(r.get("wins") or 0 for r in rounds[rk])
        other = max(0.0, tot - won - cap)
        print(f"    {rk:12s} token-cap {cap:6.1f}   other {other:6.1f}   (of {tot:.0f} trials)")

    aggs_raw = [e.get("aggregate") or 0 for e in entries]
    # The aggregate is stored TWO WAYS in the bundles: an older path wrote it rounded to 4dp
    # (0.8889), a newer one wrote the raw float (0.8888666666666666). Those are the SAME
    # measurement, so a raw distinct-count is partly counting the writer rather than the models.
    # Report both, and treat the normalised figure as the real one.
    norm = [round(a, 4) for a in aggs_raw]
    dist_raw, dist_norm = Counter(aggs_raw), Counter(norm)
    print()
    print(f"  aggregate: {len(dist_norm)} distinct (normalised) / {len(dist_raw)} raw, "
          f"across {len(entries)} entries")
    if len(dist_raw) != len(dist_norm):
        print(f"    NOTE: {len(dist_raw) - len(dist_norm)} of the raw buckets are STORAGE-FORM "
              f"duplicates -- the same value written rounded and unrounded.")
    for v, n in sorted(dist_norm.items(), reverse=True)[:14]:
        print(f"    {v:6.4f}  {n:3d}  " + "#" * n)


def main():
    by_card = load()
    if not by_card:
        print("no graded bundles found")
        return
    for card in sorted(by_card, key=str):
        analyse(card, by_card[card])
        print()
    if len(by_card) > 1:
        print("=" * 78)
        print("NOTE: those sections are SEPARATE ON PURPOSE. The cards are different measurements")
        print("      (different items per round), so they are never pooled, never averaged")
        print("      together, and never ranked against each other. See clause 3 of")
        print("      FRONTEND_CONTRACT_ACCEPTANCE.md — and note that this script violated that")
        print("      clause until 2026-10-07, silently, while printing 118.7%.")


if __name__ == "__main__":
    main()
