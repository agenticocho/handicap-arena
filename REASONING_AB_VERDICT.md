# THE REASONING A/B — RESULT. BRANCH 1: THE FLAG IS THE CARRIER.

**Pre-registered in `PREREG_reasoning_ab.md` before the first number, with its branches. Run of record:
`probes/REASONING_AB.json`.**

---

## THE RESULT, FROM THE ARTIFACT

```
entrant            level                    arm        ended                moves  unreadable  probe
Qwen3.5-4B         01_one_push              declared   SOLVED                   1        0        off
Qwen3.5-4B         01_one_push              override   budget_confounded        0        1        on
Qwen3.5-4B         02_two_boxes             declared   commands_exhausted       -        0        off
Qwen3.5-4B         02_two_boxes             override   budget_confounded        0        1        on
Qwen3.5-4B         03_the_corner_waiting    declared   commands_exhausted      12        0        off
Qwen3.5-4B         03_the_corner_waiting    override   budget_confounded        0        1        on
Qwen3.5-9B         01_one_push              declared   SOLVED                   1        0        off
Qwen3.5-9B         01_one_push              override   budget_confounded        0        1        on
Qwen3.5-9B         02_two_boxes             declared   commands_exhausted       9        0        off
Qwen3.5-9B         02_two_boxes             override   budget_confounded        0        1        on
Qwen3.5-9B         03_the_corner_waiting    declared   commands_exhausted      17        0        off
Qwen3.5-9B         03_the_corner_waiting    override   budget_confounded        0        1        on
```

**PERFECT SEPARATION, 6 CELLS AGAINST 6:**

```
every `declared` (--reasoning off) cell    unreadable 0, and the entrant MOVED
every `override` (--reasoning on)  cell    budget_confounded, unreadable 1, moves 0
```

**BRANCH 1 — the flag IS the carrier. Readable with it, unreadable without.**

## AND THE MECHANISM IS EXACTLY THE ONE PREDICTED, NOT MERELY A DIFFERENCE

**Under `--reasoning on` the entrant deliberates into the token ceiling and NEVER REACHES AN ANSWER:**

```
turn 0   token ''   gen_tokens 64   finish_reason length
         answer_field 'capped-deliberation-missing-value'   missing_value True   raw ''
budget   turns 1, turns_that_hit_the_ceiling 1, all_turns_capped true
         reading: "BUDGET-CONFOUNDED -- every answer was cut off at the ceiling"
```

**That is the Chair's Ornith signature — 2314 tokens and no commitment — reproduced in this cabinet on
different weights, and it is the reason the cell is empty rather than wrong.** *The model did not fail to
answer; the harness cut it off before it began to.*

## THE PROBE AGREED IN ALL TWELVE CELLS, INDEPENDENTLY OF THE GAME

```
declared arm   probe observed = off   (2-3 tokens on a one-token question)
override arm   probe observed = on    (64 tokens, finish_reason length, empty answer)
```

**The probe costs one request and would have told us this BEFORE any game turn.** It is now wired into every
cell, and **it is the field that makes this A/B's conclusion checkable by someone who does not trust the
game's own counters.**

## AND THE ENTRANT-SIDE BUG THIS RUN FOUND, WHICH HAD TO BE FIXED BEFORE THE RESULT MEANT ANYTHING

**`ended: commands_exhausted` was being reported for a run that used ONE command.** The run ended on the first
empty answer, and the termination said it had used its allocation. **THAT IS NOT COSMETIC: it changes the
DENOMINATOR, and a rate over `attempted` can be improved by quitting early — the exact thing the Chair said
not to let this A/B become.**

**FIXED:** a run whose every command was a HARNESS-PRODUCED empty now ends as **`budget_confounded`** with a
written `ended_why`. **And `missing_values` is a new field, because inside `unreadable` there is a subset the
harness produced** — both are non-answers and both sit INSIDE the denominator (A6), but *"the model answered
badly"* and *"we cut it off"* are different findings and one has already been published as the other.

## SCOPE, STATED SO THE RESULT CANNOT BE READ AS MORE THAN IT IS

**Two entrants, three levels, n=1 per cell, two arms, ONE instrument configuration apart.** **THIS IS A
DEMONSTRATION, NOT A FIELD.** Two entrants cannot establish a population-level effect, and the separation is
clean enough that the temptation to generalise is the specific risk.

**AND THE OVERRIDE IS AN EXPERIMENT ARM, NOT A DECLARATION.** A result from it does not change this cabinet's
declared setting — **changing the declaration is a separate act, in the PREREG, with its own reason.** The
declared setting stands: `off`, because every cabinet here asks for a short answer.

**WHAT THIS ESTABLISHES: for these two entrants on these three levels, the launch flag is causally
responsible for whether an answer exists at all. WHAT IT DOES NOT: that it would hold at 4B vs 9B size
beyond them, that it explains the earlier Qwen improvement in population run 2 (that run differed in more
than one way), or anything about the three entrants that never started.**
