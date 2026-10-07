# FINDING 007 — no verdict may depend on data that was discarded at scoring time

**Date:** 2026-10-07 · **Found by:** Chilly (as a measurement handed over, not a ruling) · **Status:** the
v3 verdict is **withheld** pending the fix, and this is why

## The measurement

I ran a per-item pass rate and found `"unparseable"` four times, said so, and then **refused to
report the v3 criterion verdict** because I could not tell a model failure from a scoring bug. That
refusal was right. **The defect underneath it is three times larger, and the instrument I counted
with was itself broken.**

    bundle item dict keys : ['reason', 'score', 'truncated']     <- no raw text
    round keys            : ctx_limited_trials, finish_reasons, items, kind, max_completion_tokens,
                            metaphor, perfect, score, trials, truncated, wins   <- no transcript
    answers_from_reasoning: 0    <- a COUNTER, not a set of answers
    "unparseable"         : 13 item-instances · 3 entries · all six items

**My four was not a miscount. It was a capped one.** My probe stored at most two reason strings per
item (`if ... and len(s['reasons']) < 2`), so the count could not exceed 2 per item. **A check with a
ceiling on what it can see reports a number that looks like a measurement and is an artifact of the
instrument** — the same family as everything else in this record, this time in the tool doing the
counting. Chilly's 13 is correct.

## And the decisive part

**The parser's input was discarded at scoring time.** `_first_json` ran, produced a score and a
reason, and **the model's actual output went nowhere.** So:

- the failure audit **cannot be performed at all** — there is nothing to re-parse;
- `"0/1 fields"` cannot be checked against what the model emitted;
- **and a model failure is indistinguishable from a scoring bug, permanently, for these bundles.**

## The rule

> ## **No verdict may depend on data that was discarded at scoring time.**

**The fix is NOT a better regex.** A non-greedy pattern would be a guess: **you cannot test a parser
against inputs it discarded.** Both of my concerns — the greedy `\{.*\}` and the coarse reason
string — resolve to a single requirement:

> **The bundle must carry what the model actually produced, per item.**

With the raw text stored, `"unparseable"` becomes auditable and re-parseable, **and the reason string
can stay coarse, because the primitive is there to fall back to.** Then, and only then, is there
enough evidence to choose a parser instead of guessing at one.

## Why this is the same rule as the chess replay

The chess event needs the **move list** in the bundle so a spectator can re-derive the game. This
needs the **raw output** in the bundle so an auditor can re-derive the score. Both are:

> **The artifact must carry the thing that makes its result checkable.**

And it is the same rule as the Q2 correction from earlier today: *the writer must record the integer
counts, so the rational is recoverable without re-reading per-item scores — all 33 bundles happen to
carry scores today; that is luck, not a contract.* **The raw output is that rule applied to failure
instead of to score.** One rule, three sites.

## What happens to the v3 verdict

**The criteria stay frozen. The scoring gets a second pass with the primitives in hand.** That is not
a moved goalpost — it is the difference between a **re-derivation** and a **re-scoring**, and this
record already knows how to keep those apart (`CARD_v2.md` §5b: a re-derivation is not a re-scoring).

Sequence:

1. **Let the current run finish.** 40 of ~46. Its scores are a legitimate **first pass** and are
   labelled as such: **v3 first pass — no primitives stored.**
2. **`arena.py` records the raw output per item.** Not applied mid-run: the driver spawns one process
   per entrant, so a change now would leave part of the field with primitives and part without — a
   confounded instrument, which is the thing this whole finding is about.
3. **Re-run v3.** With the primitives stored, so the field is internally consistent.
4. **Re-parse and audit**, then evaluate the frozen criteria — **on the run whose instrument can be
   checked.**

The criterion bar has not moved by one point. **What moved is my ability to defend a number, which is
the only thing that makes a criterion worth freezing.**
