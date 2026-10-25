#!/usr/bin/env python3
"""Post-run checks: published row's own answer distribution vs today's, seat identity, consistency."""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mastermind_run_onefile as mm  # noqa: E402

d = json.load(open(os.path.join(HERE, "rows_9b.json")))
print("PUBLISHED rows_9b.json (started %s, ended %s)" % (d["run"]["started"], d["run"]["ended"]))
t1 = Counter(tuple(r["guesses"][0]) for r in d["rows"] if r["guesses"])
print(f"  turn-1 answers: {sum(t1.values())} of {len(d['rows'])} games  {t1.most_common(4)}")
allg = Counter(tuple(g) for r in d["rows"] for g in r["guesses"])
print(f"  all guesses: {sum(allg.values())}  {allg.most_common(3)}")
print(f"  won_at: {[r['won_at'] for r in d['rows']]}")
cons = [c for r in d["rows"] for c in r["consistent"] if c is not None]
print(f"  consistency {sum(1 for c in cons if c)}/{len(cons)} answered turns")

print("\nTODAY, same prompt bytes, same seat:")
recs = [json.loads(l) for l in open("/home/chilly1/workspace/chair-link/artifacts/"
                                    "2026-10-25-mastermind-prompt-toggle/results.jsonl")]
s1 = [r for r in recs if r["state"] == "S1" and r["label"] == "hist=real"]
for r in s1:
    print(f"  rep{r['rep']} prompt_sha256 {r['prompt_sha256'][:16]} -> {r['guess']} at {r['at']}")

print("\nmid-game arms where the answer moved (real vs absent vs stale):")
for r in recs:
    if r["state"] in ("S3", "S5") and r["instruction"]:
        print(f"  {r['state']} {r['label']:14s} rep{r['rep']} -> {r['guess']} "
              f"consistent_with_history={r['consistent_with_history']} "
              f"legal={r['legal']} route={r['route']}")

print("\ninstruction-off raw text (first 160 chars), one per state:")
seen = set()
for r in recs:
    if r["instruction"] or r["state"] in seen:
        continue
    seen.add(r["state"])
    print(f"  {r['state']} finish={r['finish']} tokens={r['tokens']} raw={r['raw'][:160]!r}")

print("\nany instruction-off call that produced a legal guess:",
      [ (r["state"], r["guess"]) for r in recs if not r["instruction"] and r["guess"] ])
