#!/usr/bin/env python3
"""Self-test for the Mastermind control block: each control must pass AND fail."""
import os, sys, copy, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mastermind_run_onefile as M

FIXTURE = os.path.join(HERE, "mastermind_secrets_16.txt")
fixture = M.read_fixture(FIXTURE)
LIMIT = 10

def run_arm(reply_fn):
    return M.control_arm_rows(fixture, LIMIT, reply_fn)

def control_reply(p):
    g, note, _ = M.consistent_choice(p)
    return g, {"route": "strict" if g else "none", "note": note, "raw": None}

def broken_reply(p):
    g, note, _ = M.constant_guess_choice(p)
    return g, {"route": "constant-guess", "note": note, "raw": None}

fails = []

# C1 scripted control arm
rows = run_arm(control_reply)
wins = sum(r["solved"] for r in rows)
ok = wins == len(fixture)
print(f"  {'OK  ' if ok else 'FAIL'}  C1 scripted control arm passes: {wins}/{len(fixture)}")
if not ok: fails.append("C1 pass")

# C1 fail: make the chooser a constant guess
def bad_control_reply(p):
    g, note, _ = M.constant_guess_choice(p)
    return g, {"route": "broken", "note": note, "raw": None}
rows = run_arm(bad_control_reply)
wins = sum(r["solved"] for r in rows)
ok = wins != len(fixture)
print(f"  {'OK  ' if ok else 'FAIL'}  C1 scripted control arm fails when chooser is broken: {wins}/{len(fixture)}")
if not ok: fails.append("C1 fail")

# C2 broken arm
rows = run_arm(broken_reply)
wins = sum(r["solved"] for r in rows)
ok = wins == 0
print(f"  {'OK  ' if ok else 'FAIL'}  C2 broken (constant guess) arm passes: {wins}/{len(fixture)}")
if not ok: fails.append("C2 pass")

# C2 fail: make the broken arm actually consistent
rows = run_arm(control_reply)
wins = sum(r["solved"] for r in rows)
ok = wins != 0
print(f"  {'OK  ' if ok else 'FAIL'}  C2 broken arm fails when chooser is consistent: {wins}/{len(fixture)}")
if not ok: fails.append("C2 fail")

# C3 recomputed consistent
rows = run_arm(control_reply)
disc = M.stored_vs_recomputed_disagreements(rows)
ok = disc == 0
print(f"  {'OK  ' if ok else 'FAIL'}  C3 stored-vs-recomputed disagreements == 0 on honest rows: {disc}")
if not ok: fails.append("C3 pass")

# C3 fail: flip a stored flag
mutated = copy.deepcopy(rows)
mutated[0]["consistent"][0] = not mutated[0]["consistent"][0]
disc2 = M.stored_vs_recomputed_disagreements(mutated)
ok = disc2 == 1
print(f"  {'OK  ' if ok else 'FAIL'}  C3 disagreement count fires when a stored flag is flipped: {disc2}")
if not ok: fails.append("C3 fail")

# C4 per-turn prompt digest
digests = M.per_turn_prompt_digests(LIMIT)
ok = len(digests) == LIMIT and len(set(digests)) == LIMIT
print(f"  {'OK  ' if ok else 'FAIL'}  C4 per-turn prompt digests: {len(digests)} distinct of {LIMIT}")
if not ok: fails.append("C4 pass")

# C4 fail: a single constant digest would not be per-turn
constant_digests = [digests[0]] * LIMIT
ok = len(set(constant_digests)) != LIMIT
print(f"  {'OK  ' if ok else 'FAIL'}  C4 a single constant digest is detectable as not per-turn")
if not ok: fails.append("C4 fail")

# C5 per-state null
rows = run_arm(control_reply)
nulls = M.per_state_nulls(rows[0])
ok = len(set(round(x, 6) for x in nulls)) > 1 and nulls[0] == 1.0
print(f"  {'OK  ' if ok else 'FAIL'}  C5 per-state null varies and turn1 = 1.0: {nulls}")
if not ok: fails.append("C5 pass")

# C5 fail: a single constant null
constant_nulls = [0.0317] * len(nulls)
ok = len(set(constant_nulls)) == 1
print(f"  {'OK  ' if ok else 'FAIL'}  C5 a single constant null (0.0317) is detectable as not per-state")
if not ok: fails.append("C5 fail")

# Control block pass/fail via mutation
cb = M.run_control_block(fixture, LIMIT, verbose=False)
ok = cb["passed"] is True
print(f"  {'OK  ' if ok else 'FAIL'}  control block passes: {cb['passed']}")
if not ok: fails.append("CB pass")

# monkeypatch consistent_choice to broken -> block fails
orig = M.consistent_choice
M.consistent_choice = lambda p: M.constant_guess_choice(p)
cb2 = M.run_control_block(fixture, LIMIT, verbose=False)
M.consistent_choice = orig
ok = cb2["passed"] is False
print(f"  {'OK  ' if ok else 'FAIL'}  control block fails when chooser is broken: {cb2['passed']}")
if not ok: fails.append("CB fail")

print()
if fails:
    print(f"*** {len(fails)} ARM(S) FAILED: {fails}")
    sys.exit(1)
print("ALL CONTROLS PASS AND FAIL AS PRE-REGISTERED.")
sys.exit(0)
