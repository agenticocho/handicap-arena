#!/usr/bin/env python3
"""addendum.py — is the published (0,1,2,3) mode reproducible on today's seat, at the exact
turn-2 state the published row reached?

The placeholder `(no guesses yet)` exists ONLY in turn-1 prompts (render_history returns it only
when history is empty). So the question "did the placeholder cause the (0,1,2,3) x132 mode" has a
structural half and a reproducibility half. This script measures the second: it replays the exact
turn-2 prompt for four published games (history taken from the published row itself, rendered by the
shipped renderer) 3 times each, and compares with what the published row answered.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mastermind_run_onefile as mm  # noqa: E402

BASE = "http://127.0.0.1:58595"
MODEL = "prism-bonsai-9b"
LIMIT = 10
OUT = ("/home/chilly1/workspace/chair-link/artifacts/"
       "2026-10-25-mastermind-prompt-toggle/reproduction.jsonl")

d = json.load(open(os.path.join(HERE, "rows_9b.json")))
call = mm.http_model(BASE, MODEL, None, 512, True)

fh = open(OUT, "a")
for row in d["rows"][:4]:
    guess1 = tuple(row["guesses"][0])
    ex, pa = row["feedback"][0]
    history = [(guess1, ex, pa)]
    prompt = mm.build_prompt(history, 2, LIMIT)
    published_t2 = row["guesses"][1] if len(row["guesses"]) > 1 else None
    print(f"\nsecret {row['secret']}  published turn-1 {list(guess1)} fb {(ex, pa)}")
    print(f"  turn-2 prompt sha256 {mm.sha256_text(prompt)[:16]}  len {len(prompt)}")
    print(f"  published turn-2 answer {published_t2}")
    for rep in (1, 2, 3):
        r = call(prompt)
        p = mm.parse_guess(r["content"])
        g = p["strict"] or p["normalized"]
        rec = {"secret": row["secret"], "published_turn2": published_t2,
               "prompt_sha256": mm.sha256_text(prompt), "rep": rep,
               "guess": list(g) if g else None, "raw": r["content"][:200],
               "finish": r["finish"], "secs": r["secs"],
               "consistent": (None if g is None else
                              all(mm.feedback(g, h) == (e, p2) for h, e, p2 in history)),
               "matches_published": (list(g) == published_t2 if g else False)}
        fh.write(json.dumps(rec) + "\n")
        fh.flush()
        print(f"    rep{rep} -> {rec['guess']}  matches_published={rec['matches_published']}"
              f"  consistent={rec['consistent']}  {r['finish']} {r['secs']}s")
fh.close()
print(f"\nwrote {OUT}")
