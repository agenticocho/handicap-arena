#!/usr/bin/env python3
"""REPLAY EVERY p* WITNESS FROM THE PUBLISHED TABLE. A witness that is not replayed is a claim.

Reads probes/PSTAR_TABLE_2026-11-05.json, rebuilds each witness stream from its own word and budget,
and re-enters the SIMULATOR (not the search) to confirm the outcome. Prints one line per board.
"""
import json
import os
import sys

REPO = "/home/chilly1/workspace/ocho_arena"
sys.path.insert(0, REPO)

import degenerate_gate as D
import missile_command as M
import zork as Z

T = json.load(open(os.path.join(REPO, "probes/PSTAR_TABLE_2026-11-05.json")))
bad = 0

for row in T["rows"]:
    if row["event"] == "snake":
        continue                                   # replayed through the page below, not the simulator
    ok = False
    path = os.path.join(REPO, row["board"])
    text = open(path, encoding="utf-8").read()
    if row["event"] == "missile":
        word, budget = row["witness"].split(" "), row["budget"]
        stream = D._repeat(word, budget)
        rec = M.play(text, stream)
        ok = rec["cities_surviving"] == row["score"]
        print(f"{row['event']:8s} {row['board']:34s} p*={row['p_star']}  stream={stream}  "
              f"-> cities {rec['cities_surviving']}/{rec['cities_total']}  "
              f"counts fired={rec['counts']['fired']} passed={rec['counts']['passed']}  "
              f"{'REPRODUCES' if ok else 'DOES NOT REPRODUCE'}")
    elif row["event"] == "zork":
        word, budget = row["witness"].split(" ; "), row["budget"]
        stream = D._repeat(word, budget)
        rec = Z.play(text, stream)
        ok = rec["finished"] is True
        print(f"{row['event']:8s} {row['board']:34s} p*={row['p_star']}  stream={stream[:20]}...  "
              f"-> finished={rec['finished']} commands_consumed={rec['commands_consumed']}  "
              f"terminal={rec.get('terminal')}  {'REPRODUCES' if ok else 'DOES NOT REPRODUCE'}")
    if not ok:
        bad += 1

print(f"\n{len([r for r in T['rows'] if r['event'] != 'snake'])} witnesses replayed, {bad} did not reproduce")
sys.exit(1 if bad else 0)
