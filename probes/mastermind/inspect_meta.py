#!/usr/bin/env python3
"""One-shot probe: reproduce the published prompt digest, then time ONE call to the live 9B seat.

Writes nothing; prints only what it measured.
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

d = json.load(open(os.path.join(HERE, "rows_9b.json")))
run = d["run"]
print("PUBLISHED RUN META")
for k in ("instrument_sha256", "fixture", "fixture_sha256", "fixture_games", "model",
          "base", "max_tokens", "thinking", "limit", "prompt_sha256", "rowset_sha256",
          "started", "ended"):
    print(f"  {k:20s} {run.get(k)}")
print(f"  rows {len(d['rows'])}")
print(f"  instrument file sha256 now {mm.sha256_file(os.path.join(HERE, 'mastermind_run_onefile.py'))}")

p1 = mm.build_prompt([], 1, 10)
print(f"\nPROMPT_DIGEST build_prompt([],1,10) len {len(p1)} sha256 {mm.sha256_text(p1)}")
print("PROMPT REPR:")
print(repr(p1))

call = mm.http_model(BASE, MODEL, None, 512, True)
t0 = time.time()
r = call(p1)
print(f"\nONE CALL wall {time.time()-t0:.1f}s -> secs {r['secs']} finish {r['finish']} tokens {r['tokens']}")
print(f"  content {r['content']!r}")
print(f"  reasoning_chars {len(r['reasoning'])}")
print(f"  parsed {mm.parse_guess(r['content'])}")
