#!/usr/bin/env python3
"""Why is the card saturated? Measure before designing.

The field: 42 graded models, 22 of them at 9/9. Hardening the card without knowing WHICH round
stops discriminating would replace a card that works in three rounds with a guess in three
rounds. So: per-round pass rates, per-round failure modes, and a direct test of my hypothesis
that R1 fencing is the capping round.

Reports, per round:
  * the distribution of wins (0..3)
  * the failure mode when a trial fails (token cap / unparseable / no answer)
  * how much of the 9/9-vs-6/9 gap each round actually explains
"""
import glob, json, os, sys
from collections import Counter, defaultdict

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
ROUNDS = ["R1_fencing", "R2_chess", "R3_pitstop"]


def load():
    out = []
    for p in sorted(glob.glob(os.path.join(RESULTS, "*.json"))):
        try:
            d = json.load(open(p))
        except Exception:
            continue
        if d.get("harness") != "handicap-arena":
            continue
        for r in (d.get("results") or []):
            r["_file"] = os.path.basename(p)
            out.append(r)
    return out


def main():
    entries = load()
    print(f"graded entries: {len(entries)}")
    belts = Counter((e.get("grade") or {}).get("belt", "?") for e in entries)
    print("belts:", dict(belts))

    # ---- per-round win distribution ----
    print("\n=== per-round win distribution (each round is 3 trials) ===")
    per_round = defaultdict(Counter)
    for e in entries:
        for rk in ROUNDS:
            rd = (e.get("rounds") or {}).get(rk) or {}
            per_round[rk][rd.get("wins", 0)] += 1
    print(f"  {'round':12s} {'0/3':>6} {'1/3':>6} {'2/3':>6} {'3/3':>6}   {'mean win rate':>13}  {'discriminates?':>14}")
    for rk in ROUNDS:
        c = per_round[rk]
        n = sum(c.values())
        mean = sum(k * v for k, v in c.items()) / (3 * n) if n else 0
        # a round discriminates only if it is neither always-passed nor always-failed
        sat = "SATURATED" if c.get(3, 0) / n > 0.6 else ("FLOOR" if c.get(0, 0) / n > 0.6 else "discriminates")
        print(f"  {rk:12s} {c.get(0,0):6d} {c.get(1,0):6d} {c.get(2,0):6d} {c.get(3,0):6d}   "
              f"{mean:13.1%}  {sat:>14}")

    # ---- failure modes per round ----
    print("\n=== failure modes, per round (where a trial did not pass) ===")
    for rk in ROUNDS:
        caps = unpar = other = 0
        for e in entries:
            rd = (e.get("rounds") or {}).get(rk) or {}
            fr = rd.get("finish_reasons") or {}
            trials = rd.get("trials") or 0
            cap = fr.get("length", 0)
            caps += cap
            unpar += max(0, trials - rd.get("wins", 0) - cap)
        print(f"  {rk:12s} token-cap {caps:3d}   other-failure {unpar:3d}")

    # ---- which round separates 9/9 from 6/9? ----
    print("\n=== where the 9/9 and 6/9 groups actually differ ===")
    groups = defaultdict(list)
    for e in entries:
        agg = e.get("aggregate")
        if agg is None:
            continue
        key = "9/9" if agg > 0.99 else ("6/9" if abs(agg - 2 / 3) < 0.01 else "other")
        groups[key].append(e)
    for gname in ("9/9", "6/9", "other"):
        g = groups.get(gname) or []
        if not g:
            continue
        rates = {}
        for rk in ROUNDS:
            tot = sum((e.get("rounds") or {}).get(rk, {}).get("trials", 0) for e in g)
            won = sum((e.get("rounds") or {}).get(rk, {}).get("wins", 0) for e in g)
            rates[rk] = won / tot if tot else 0
        print(f"  {gname:5s} (n={len(g):2d})  " +
              "  ".join(f"{rk}={rates[rk]:6.1%}" for rk in ROUNDS))

    # ---- the direct test of my hypothesis ----
    print("\n=== hypothesis test: is R1 the cap on the 6/9 group? ===")
    n6 = groups.get("6/9") or []
    if n6:
        for rk in ROUNDS:
            zero = sum(1 for e in n6 if (e.get("rounds") or {}).get(rk, {}).get("wins", 0) == 0)
            print(f"  {rk}: {zero}/{len(n6)} of the 6/9 group scored ZERO on it")
        worst = Counter()
        for e in n6:
            lows = [rk for rk in ROUNDS if (e.get("rounds") or {}).get(rk, {}).get("wins", 0) == 0]
            worst[",".join(lows) if lows else "none at zero"] += 1
        print("  which round(s) each 6/9 model zeroed:", dict(worst))

    # ---- what does the per-round task actually ask? show the shapes ----
    print("\n=== per-round aggregate stats across the field ===")
    for rk in ROUNDS:
        kinds = Counter()
        lats = []
        for e in entries:
            rd = (e.get("rounds") or {}).get(rk) or {}
            kinds[rd.get("kind", "?")] += 1
        print(f"  {rk:12s} kinds={dict(kinds)}")


if __name__ == "__main__":
    main()
