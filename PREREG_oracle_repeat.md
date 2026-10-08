# PRE-REGISTRATION — THE ORACLE REPEAT

**Written 2026-10-08, while both v4 and v5 bundles exist and before the paired comparison was computed.**
**Instrument:** the transcript's own — *"write down what they expected the score to be before they looked
at the board."* Pre-registration, turned on our own oracle.

---

## THE QUESTION

Chilly's: *how far does an entrant's own score move when nothing changes?* — because *"the referee requires
just as much scrutiny as the fighters,"* and **one number decides what every verdict this project has
issued is worth.**

**AND THE RUN TO ANSWER IT DOES NOT NEED TO BE STARTED. IT IS ALREADY RUNNING.**

**Measured, before proposing anything:** no entrant has two **measured** v4 records — the v4 re-runs
re-ran *failures*, not measurements (8 entrants have more than one v4 record; **0 have more than one that
measured**). **But 38 entrants have measured records on different cards**, and **v5 re-measures v4's items
at v4's config** (`ctx 8192`, `mt 3000`, `n_gpu_layers` auto-fit, `temperature 0.0` — read from the
bundle's own `config` block).

**So as `arena-v5.service` completes each entrant, that entrant carries a paired observation: the same
items, the same config, the same box, two independent runs.** The repeat measurement is arriving tonight,
free, inside the run already in flight. **No second run, no new card, no new pre-registration — which was
the proposal's own best argument, turned all the way around.**

---

## THE EXPECTATION, FROZEN BEFORE THE COMPARISON

**The sampler is GREEDY.** `temperature: 0.0` is the default *and is recorded in every bundle's config*;
the code states the consequence twice (`arena.py:511`, `:1168`): *"at temperature 0, repeated trials of one
prompt are copies of a measurement."*

**SO THE PRE-REGISTERED EXPECTATION IS EXACT REPRODUCTION. FOR EVERY ITEM. FOR EVERY ENTRANT.**

> **expected difference = 0.000 for every (entrant, item) pair.**

**This is a strong claim and it is deliberately falsifiable.** It is not "small" and it is not "within
tolerance" — **a greedy decoder on the same binary with the same prompt should produce the same tokens.**

---

## WHAT A NON-ZERO DIFFERENCE WOULD MEAN — DECIDED NOW, SO IT CANNOT BE EXPLAINED AWAY LATER

**If the expectation holds**, the claim licensed is exactly: **this harness, at this config, on this box,
is DETERMINISTIC.** Nothing more.

**If it does not hold**, there are three candidates and they are distinguishable:

1. **GPU floating-point non-determinism at a near-tie.** cuBLAS reduction orders are not guaranteed stable,
   so a logit gap in the last bits can flip an `argmax`. **This is the only source a greedy re-run can
   legitimately reveal.** Tell: a difference confined to items whose answer sat near a token boundary.
2. **A scoring change between the harness revisions.** **Checked, not assumed:** v5 changed the *runner*
   (record sweep, admission gate, the clock, the ratio printer) and the *card version stamp*. **The scoring
   path is untouched** — so a scoring-drift explanation must be **demonstrated, not asserted**, and
   `git diff 8c97dd2..8d6c9be -- arena.py` is where it would show.
3. **A real defect in one of the two runs.** The interesting one, and the reason to run this at all.

---

## THE BLIND SPOT, NAMED BEFORE THE RESULT SO IT CANNOT BE OVER-READ

**A re-run with the same code reproduces every SYSTEMATIC defect PERFECTLY.**

Every defect this project has found — the stand-in family, an empty bundle read as success, the greedy
`{.*}` parser, the caption contradicting its own table, the denominator that silently changed — **is
systematic.** A deterministic harness reproduces all of them **exactly**, and reports a difference of zero
while doing it.

> **A ZERO RESULT LICENSES: "the harness is deterministic."**
> **IT DOES NOT LICENSE: "the harness is correct."**
>
> **Those are different sentences, and only one of them is the sentence this project keeps failing on.**

**So the result may not be reported as a clean bill of health for the oracle.** Its correct reading is:
*the referee gives the same answer twice; whether the answer is right is a separate question that this
experiment does not touch.*

---

## THE SHAPE OF THE CLAIM IT SUPPORTS — STATED SO IT IS NOT OVERSOLD

**One comparison per entrant is a DIFFERENCE, not a VARIANCE.** 38 paired differences at one repeat each
can establish *"did any score ever move"*; they cannot estimate a standard deviation, and **must not be
reported as one.**

**The honest form of the finding, whichever way it lands:**

> *N of M item records reproduced their previous value exactly, under a greedy decoder where exact
> reproduction was the pre-registered expectation. The K that did not are listed with their token gaps.*

**A list, not a sigma.** And **every non-zero stays in the record** — no item is dropped for having moved.

---

## DISCLOSURE — WHAT I HAD ALREADY SEEN WHEN I WROTE THIS

**Honesty about the pre-registration's own timing**, since the rule binds the author too: before writing
this file I had read **one** v5 score from the running journal — `Qwen3.5-2B-UD-Q4_K_XL` → `0.72`, and one
v4 value for a different entrant. **The expectation above is not derived from those.** It follows from
`temperature: 0.0` and nothing else — **which is why it is a *prediction* rather than a retrospective.**

**It is recorded here rather than omitted, because a pre-registration that does not say what its author had
already seen is a caption, not a criterion.**
