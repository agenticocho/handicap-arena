#!/usr/bin/env python3
"""
Best-of-325: is the article's winning strategy evidence of an edge?

The article (Miles Deutscher, Oct 6 2026) sources 50 strategies, runs 325+ backtests,
and reports a winner with:
    beat buy-and-hold, 55% of trades profitable, max drawdown -8.86%, profit factor 1.9
    -> no trade count (n) reported for the winner

The methodological question the article never asks: the winner was SELECTED as the
maximum of ~325 attempts. Under a null of zero-edge strategies, what does the best of
325 look like? If the answer is "a profit factor near 1.9", then 1.9 is not evidence
of an edge -- it is the expected order statistic of pure noise.

Model: a zero-edge strategy. Each trade risks 1R and wins +1R with probability 0.5
(EV exactly 0). Profit factor = gross profit / gross loss. Simulate 325 independent
strategies at several trade counts and record the MAXIMUM profit factor.
"""
import random, statistics as st

random.seed(7)
TRIALS = 325          # the article's "325+ backtests"
REPS = 4000           # repeats of the whole 325-strategy search, for a stable max

def one_strategy(n, p=0.5, r_mult=1.0, risk=1.0):
    wins = 0
    for _ in range(n):
        if random.random() < p:
            wins += 1
    losses = n - wins
    gross_profit = wins * r_mult * risk
    gross_loss = losses * risk
    if gross_loss == 0:
        return float("inf")
    return gross_profit / gross_loss

print(f"Zero-edge null: p=0.5, +1R / -1R (EV = 0 exactly). Searching {TRIALS} strategies.")
print()
print(f"{'trades n':>9} {'P(single PF>=1.9)':>19} {'median best-of-325':>19} "
      f"{'95th pct best-of-325':>21} {'expect to see >=1.9?':>21}")
print("-" * 95)
for n in (20, 30, 50, 75, 100, 150, 200, 300, 500):
    single_hits = 0
    maxes = []
    for _ in range(REPS):
        best = 0.0
        for _ in range(TRIALS):
            pf = one_strategy(n)
            if pf >= 1.9:
                single_hits += 1
            if pf > best:
                best = pf
        # cap infinities for a finite max when losses==0
        maxes.append(min(best, 50.0))
    p_single = single_hits / (REPS * TRIALS)
    med = st.median(maxes)
    p95 = sorted(maxes)[int(0.95 * len(maxes))]
    print(f"{n:>9} {p_single:>19.4f} {med:>19.2f} {p95:>21.2f} "
          f"{('YES' if med >= 1.9 else 'no'):>21}")

print()
print("=== the article's winner, in context ===")
print("  reported: profit factor 1.9, 55% win rate, max DD -8.86%, n NOT reported")
print("  If n is under ~100, a PF of 1.9 is entirely consistent with the best of 325")
print("  zero-edge strategies -- i.e. it is the expected order statistic, not an edge.")
print()
print("=== what n WOULD make PF 1.9 surprising? ===")
for n in (100, 200, 300, 500, 1000):
    hits = sum(1 for _ in range(20000) if one_strategy(n) >= 1.9)
    print(f"  n={n:>5}: single zero-edge strategy reaches PF>=1.9 with probability "
          f"{hits/20000:.4f}  -> best-of-325 expected: {'YES likely' if hits/20000*325 >= 1 else 'no'}")
