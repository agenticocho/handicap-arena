#!/usr/bin/env python3
"""prompt_toggle_probe.py — does a non-semantic prompt line move this model's answer?

Motivation: a peer's measurement (2026-10-25) says the LITERAL matters and the SHAPE does not:
in his rune game, `Path so far: Fehu`, an absent value, and a fabricated real value all gave the
same answer, while only the literal `(none)` flipped it. My Mastermind renderer carries
`(no guesses yet)` -- a THIRD literal, never toggled -- so the effect cannot be inherited from his
data. This script toggles it on the seat that produced my published row.

Everything non-variant is byte-identical to the published prompt: each variant is produced by
transforming the exact string mm.build_prompt(history, turn, 10) returns, and the assertion below
fails the run if the 'as-shipped' reconstruction is not byte-identical to it.

Arms
  1. HISTORICAL VALUE, 4 states (one turn-1, three mid-game), 4 variant shapes each:
       real      -- the rendered history block, exactly as shipped
       absent    -- the value removed; the 'Guess history (...)' label line kept
       stale     -- the shipped placeholder literal `(no guesses yet)` rendered where a real
                    value exists (meaningless only at turn 1, where real == stale, so skip)
       instr-off -- the reply instruction ("What is your next guess? Reply with ONLY ...") removed
  2. LITERAL SENSITIVITY at turn 1 only: `(no guesses yet)` (shipped), `(none)` (the peer's
     literal), `(empty)` (a neutral literal that names the same state).

Decoding: temperature 0.0, thinking off, max_tokens 512 -- identical to the published row.
Determinism: 3 identical calls per arm; a 1-of-3 or 2-of-3 answer is reported as such, not
smoothed away.

Output: one JSON object per call appended to results.jsonl, then summary.json + a printed table.
"""
import hashlib
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
MAX_TOKENS = 512
REPS = 3
OUTDIR = "/home/chilly1/workspace/chair-link/artifacts/2026-10-25-mastermind-prompt-toggle"
JSONL = os.path.join(OUTDIR, "results.jsonl")

INSTR_SUFFIX = ("\n\nWhat is your next guess? Reply with ONLY 4 numbers (0-5) "
                "separated by spaces. Nothing else.")


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def variant_prompt(history, turn, value_mode, instr=True):
    """Build one variant from the shipped renderer's own output, by substitution only."""
    shipped = mm.build_prompt(history, turn, LIMIT)
    real_block = mm.render_history(history)
    if value_mode == "real":
        block = real_block
    elif value_mode == "absent":
        block = ""
    elif value_mode == "stale":
        block = "(no guesses yet)"
    elif value_mode == "none":
        block = "(none)"
    elif value_mode == "empty":
        block = "(empty)"
    else:
        raise ValueError(value_mode)
    out = shipped.replace(real_block, block, 1)
    if not instr:
        if not out.endswith(INSTR_SUFFIX):
            raise RuntimeError("reply instruction suffix not found where expected")
        out = out[: -len(INSTR_SUFFIX)]
    return out


# ── States: histories that a real game can actually reach ────────────────────
# feedback() is the harness's own; secrets are from the frozen fixture.
SECRETS = {1: (2, 2, 2, 2), 2: (2, 3, 0, 1), 3: (1, 5, 2, 5), 4: (5, 0, 2, 0)}
H1 = [((0, 1, 2, 3), *mm.feedback(SECRETS[1], (0, 1, 2, 3)))]
H2 = [((0, 1, 2, 3), *mm.feedback(SECRETS[2], (0, 1, 2, 3)))]
H3 = [((5, 5, 0, 0), *mm.feedback(SECRETS[4], (5, 5, 0, 0)))]
H4 = [((0, 0, 0, 0), *mm.feedback(SECRETS[3], (0, 0, 0, 0))),
      ((1, 1, 1, 1), *mm.feedback(SECRETS[3], (1, 1, 1, 1)))]

STATES = [("S1", "turn 1, empty history", [], 1),
          ("S2", "turn 2, 1 turn shown", H1, 2),
          ("S3", "turn 2, 1 turn shown", H2, 2),
          ("S4", "turn 2, 1 turn shown", H3, 2),
          ("S5", "turn 3, 2 turns shown", H4, 3)]


def arms():
    out = []
    # turn 1: every literal variant, plus the instruction toggle
    for vm in ("real", "absent", "none", "empty"):
        out.append(("S1", f"hist={vm}", "instr=on", [], 1, vm, True))
    out.append(("S1", "hist=shipped", "instr=off", [], 1, "real", False))
    out.append(("S1", "hist=absent", "instr=off", [], 1, "absent", False))
    # mid-game states: the four shapes the peer's design names
    for sid, _desc, hist, turn in STATES[1:]:
        for vm in ("real", "absent", "stale"):
            out.append((sid, f"hist={vm}", "instr=on", hist, turn, vm, True))
        out.append((sid, "hist=real", "instr=off", hist, turn, "real", False))
    return out


def main():
    os.makedirs(OUTDIR, exist_ok=True)

    # self-check: as-shipped reconstruction is byte-identical to the renderer
    for _sid, _d, hist, turn in STATES:
        assert variant_prompt(hist, turn, "real", True) == mm.build_prompt(hist, turn, LIMIT), \
            f"reconstruction drifted at {_sid}"
    p1 = variant_prompt([], 1, "real", True)
    print(f"reconstruction byte-identical to renderer on all {len(STATES)} states  OK")
    print(f"turn-1 prompt len {len(p1)} sha256 {sha(p1)}")
    print(f"published row's prompt_sha256 "
          f"{json.load(open(os.path.join(HERE, 'rows_9b.json')))['run']['prompt_sha256']}")

    call = mm.http_model(BASE, MODEL, None, MAX_TOKENS, True)
    plan = arms()
    print(f"arms {len(plan)}  reps {REPS}  calls {len(plan)*REPS}")
    exists = [json.loads(l) for l in open(JSONL)] if os.path.exists(JSONL) else []
    if exists:
        print(f"resuming: {len(exists)} calls already recorded in {JSONL}")
    ok = {(r["state"], r["label"], r["instr_label"], r["rep"])
          for r in exists}
    fh = open(JSONL, "a")
    n = 0
    for sid, vlabel, ilabel, hist, turn, vm, instr in plan:
        prompt = variant_prompt(hist, turn, vm, instr)
        for rep in range(1, REPS + 1):
            n += 1
            if (sid, vlabel, ilabel, rep) in ok:
                print(f"  {n:3d}/{len(plan)*REPS} {sid} {vlabel:14s} {ilabel:9s} rep{rep} "
                      f"-> already recorded, skipped")
                continue
            t0 = time.time()
            r = call(prompt)
            parsed = mm.parse_guess(r["content"])
            guess = parsed["strict"] or parsed["normalized"]
            rec = {"state": sid, "value_mode": vm, "instruction": instr, "label": vlabel,
                   "instr_label": ilabel, "turn": turn, "rep": rep,
                   "prompt_len": len(prompt), "prompt_sha256": sha(prompt),
                   "guess": list(guess) if guess else None,
                   "route": ("strict" if parsed["strict"] else
                             "normalized" if parsed["normalized"] else "no_answer"),
                   "legal": bool(guess and all(0 <= g < mm.COLOURS for g in guess)),
                   "consistent_with_history": (
                       None if guess is None else
                       all(mm.feedback(guess, g) == (e, p) for g, e, p in hist)),
                   "raw": r["content"][:400], "finish": r["finish"],
                   "secs": r["secs"], "tokens": r["tokens"],
                   "reasoning_chars": len(r["reasoning"]),
                   "wall": round(time.time() - t0, 2),
                   "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            print(f"  {n:3d}/{len(plan)*REPS} {sid} {vlabel:14s} {ilabel:9s} rep{rep} "
                  f"-> {rec['guess']} {rec['route']} {rec['finish']} {rec['secs']}s")
    fh.close()

    # ── summarize ───────────────────────────────────────────────────────────
    recs = [json.loads(l) for l in open(JSONL)]
    key = lambda r: (r["state"], r["label"], r["instr_label"])
    table = {}
    for r in recs:
        table.setdefault(key(r), []).append(r["guess"])
    summary = {"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "base": BASE, "model": MODEL, "limit": LIMIT, "max_tokens": MAX_TOKENS,
               "reps": REPS, "calls": len(recs), "arms": []}
    print("\n=== per-arm answers (3 reps) ===")
    print(f"{'state':6s} {'history':14s} {'instr':9s}  answers               deterministic")
    for k in sorted(table):
        answers = table[k]
        det = len({tuple(a) if a else None for a in answers}) == 1
        summary["arms"].append({"state": k[0], "history": k[1], "instr": k[2],
                                "answers": answers, "deterministic_3of3": det})
        print(f"{k[0]:6s} {k[1]:14s} {k[2]:9s}  {str(answers):22s} {det}")

    # distinct answer per state, across history variants (same instruction setting)
    print("\n=== does the history line move the answer? (per state, instr=on) ===")
    summary["history_effect"] = {}
    for sid, _desc, hist, turn in STATES:
        vals = {f"hist={v}": table.get((sid, f"hist={v}", "instr=on")) for v in
                ("real", "absent", "stale", "none", "empty") if (sid, f"hist={v}", "instr=on") in table}
        firsts = {k: (v[0] if v else None) for k, v in vals.items()}
        moved = len({tuple(x) if x else None for x in firsts.values()}) > 1
        summary["history_effect"][sid] = {"answers": firsts, "answer_moved": moved}
        print(f"  {sid}: {firsts}   moved={moved}")

    print("\n=== does the reply instruction move the answer? (real history) ===")
    summary["instruction_effect"] = {}
    for sid, _desc, hist, turn in STATES:
        on = table.get((sid, "hist=real", "instr=on"))
        off = table.get((sid, "hist=real", "instr=off"))
        moved = (on[0] if on else None) != (off[0] if off else None)
        summary["instruction_effect"][sid] = {
            "instr_on": on[0] if on else None, "instr_off": off[0] if off else None,
            "answer_moved": moved}
        print(f"  {sid}: on={on[0] if on else None}  off={off[0] if off else None}  moved={moved}")

    bad = [r for r in recs if r["route"] == "no_answer" or not r["finish"] == "stop"]
    print(f"\nno_answer {len(bad)} of {len(recs)} calls")
    with open(os.path.join(OUTDIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(f"wrote {os.path.join(OUTDIR, 'summary.json')}")


if __name__ == "__main__":
    main()
