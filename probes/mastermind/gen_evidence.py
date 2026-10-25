#!/usr/bin/env python3
"""gen_evidence.py — build one text evidence bundle from the toggle run's own records.

Prints to stdout. Every number in it is counted here from the JSONL, not typed.
"""
import hashlib
import json
import os

AD = "/home/chilly1/workspace/chair-link/artifacts/2026-10-25-mastermind-prompt-toggle"
PROBE = "/home/chilly1/workspace/ocho_arena/probes/mastermind/prompt_toggle_probe.py"
HARNESS = "/home/chilly1/workspace/ocho_arena/probes/mastermind/mastermind_run_onefile.py"


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


recs = [json.loads(l) for l in open(os.path.join(AD, "results.jsonl"))]
rep = [json.loads(l) for l in open(os.path.join(AD, "reproduction.jsonl"))]

print("# MASTERMIND PROMPT-TOGGLE EVIDENCE")
print("# sent 2026-10-25 by Chilly (Local Chair) to Jarvis")
print("#")
print(f"# harness         mastermind_run_onefile.py  sha256 {sha_file(HARNESS)}")
print(f"# probe           prompt_toggle_probe.py     sha256 {sha_file(PROBE)}")
print(f"# results.jsonl   {len(recs)} records  sha256 {sha_file(os.path.join(AD,'results.jsonl'))}")
print(f"# reproduction    {len(rep)} records  sha256 {sha_file(os.path.join(AD,'reproduction.jsonl'))}")
print("# seat            prism-bonsai-9b @ http://127.0.0.1:58595  --n-gpu-layers 0 (CPU)")
print("# decode          temperature 0.0, enable_thinking false, max_tokens 512, limit 10")
print("# method          each variant = shipped build_prompt() output with ONE substring")
print("#                 substituted; asserted byte-identical to the renderer on all 5 states.")
print()
print("## PER-CALL RECORDS (all 66)")
print("# state  value_mode  instruction  rep  guess        route  finish  secs  consistent  prompt_sha16")
for r in recs:
    print(f"{r['state']:6s} {r['value_mode']:10s} {str(r['instruction']):11s} {r['rep']}  "
          f"{str(r['guess']):12s} {r['route']:9s} {str(r['finish']):16s} {str(r['secs']):6s} "
          f"{str(r['consistent_with_history']):11s} {r['prompt_sha256'][:16]}")
print()
print("## REPRODUCTION OF 4 PUBLISHED TURN-2 STATES (all 12)")
print("# secret        published_t2  rep  today        matches  consistent  finish  secs  prompt_sha16")
for r in rep:
    print(f"{str(r['secret']):13s} {str(r['published_turn2']):13s} {r['rep']}  "
          f"{str(r['guess']):12s} {str(r['matches_published']):8s} "
          f"{str(r['consistent']):11s} {str(r['finish']):8s} {str(r['secs']):6s} "
          f"{r['prompt_sha256'][:16]}")
print()
print("## COUNTS (computed from the records above)")
print(f"calls {len(recs)}   no_answer {sum(1 for r in recs if r['route']=='no_answer')}")
print(f"instruction-off calls {sum(1 for r in recs if not r['instruction'])}   "
      f"of those answered {sum(1 for r in recs if not r['instruction'] and r['guess'])}")
print(f"turn-1 arms {sum(1 for r in recs if r['state']=='S1' and r['instruction'])}   "
      f"distinct turn-1 answers "
      f"{sorted({tuple(r['guess']) if r['guess'] else None for r in recs if r['state']=='S1' and r['instruction']})}")
print(f"deterministic arms (all reps identical) "
      f"{sum(1 for k in {(r['state'],r['label'],r['instr_label']) for r in recs} if len({str(r['guess']) for r in recs if (r['state'],r['label'],r['instr_label'])==k})==1)}"
      f" of {len({(r['state'],r['label'],r['instr_label']) for r in recs})}")
print(f"reproduction matches {sum(1 for r in rep if r['matches_published'])} of {len(rep)} calls")
states = {}
for r in rep:
    states.setdefault(tuple(r["secret"]), []).append(r["matches_published"])
print(f"states fully matched "
      f"{sum(1 for v in states.values() if all(v))} of {len(states)}; "
      f"states never matched {sum(1 for v in states.values() if not any(v))}")
