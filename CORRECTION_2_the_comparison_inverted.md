# THE CORRECTION IS ITSELF CORRECTED — AND IT REVERSES THE RULING BUILT ON IT

**Retracting my retraction. The bug I found was worse than I described: it did not only invent a 5/5, it
INVERTED the comparison, and the Chair then ruled on the inverted version.**

---

## THE SAME MEASUREMENT, RUN THROUGH THE FIXED READER

```
setting                                  field                                  cases   tokens   finish
thinking DEFAULT (as the seat ships)     capped-deliberation-missing-value      NO ANSWER  1200   length
thinking OFF (enable_thinking=false)     content                                5/5        193   stop
```

## WHAT I REPORTED, AND WHAT IS TRUE

| | I said | TRUE |
|---|---|---|
| the 5/5 | "the model did the task, 5/5" | **the DEFAULT arm's THINKING TRACE was scored** |
| thinking OFF | "made it WORSE — 0/5, it invented its own API" | **thinking OFF produced THE CORRECT ANSWER, 5/5** |
| the DEFAULT arm | "5/5, correct" | **NO ANSWER AT ALL — the ceiling ate the deliberation** |

**AND THE THIRD ROW IS THE ONE THAT MATTERS: the DEFAULT arm has NO ANSWER TO SCORE. At 1200 tokens it hit the
ceiling. The earlier sweep ran 1200, 2048 AND 4096 and reported `length` EVERY TIME — so the seat does not
answer at any of those sizes either. It saturates in deliberation and never reaches an answer field.**

**`content` is EMPTY. There was never a 5/5. There was a trace, and I scored the code inside it.**

## AND SO THE CHAIR'S ORIGINAL INSTINCT WAS RIGHT TWICE OVER

**His first ruling was `thinking OFF` for a cabinet agent writing a simulator. I "corrected" it with a `0/5`
produced by the same bug. He accepted the correction — reasonably, on the numbers I gave him — and ruled
`ON-with-a-ceiling`. THE CORRECTION WAS AN ARTIFACT, AND THE RULING RESTS ON IT:**

> *"0/5 against 5/5 is not a close call."* — Decision 2.

**Those are the inverted numbers. The real comparison is `NO ANSWER` against `5/5`, WITH THINKING OFF WINNING.**

**THE ACTUAL MEASUREMENT SAYS: ON THIS SEAT, FOR THIS TASK, THINKING OFF IS THE ONLY CONFIGURATION THAT
ANSWERS AT ALL — and it answers correctly, in 193 tokens and 3.4 seconds, against 1200 tokens and NO ANSWER
with the shipped default.**

**`Action(Enum)` — the "it invented its own API" finding I built an argument on — came from a REAL `0/5` on a
THINKING-OFF arm in the *first* comparison. That arm's `content` was a real answer and it was really wrong.
But it is ONE wrong answer, and it was the arm whose mechanism I then wrongly generalised. I turned a single
bad sample into a rule about deliberation, when the honest reading was: the model sometimes ignores a
provided interface, and that is not a property of the reasoning setting.**

## THE MECHANISM, AND WHY THE SWITCH MATTERS FOR THE DECLARATION

**Measured across the whole investigation, three settings, one model, one task:**

```
seat default       (no flag, no kwarg)        NO ANSWER      thinks to the ceiling, never reaches content
server --reasoning on  + budget               answers        1/5 to 3/5, budgets 0/256/512/-1
chat-template enable_thinking=false           answers 5/5    193 tokens, 3.4 s, stop
```

**SO THE TWO SWITCHES ARE NOT EQUIVALENT — the Chair asked for exactly this distinction and the answer is: they
are not. `--reasoning on` at the server and `enable_thinking` in the chat template produce DIFFERENT BEHAVIOUR
on this model, and only the chat-template switch produced a fully correct answer.**

**AND THAT SETTLES THE SEAT PROBLEM HE RAISED.** *"Declare the seat's reasoning setting in `llama-swap.yaml`,
where it can be read"* — but a SEAT IS SHARED, and the setting travels with the TASK. **Declaring one setting per
seat would make two tasks needing different settings fight over one seat. `chat_template_kwargs` travels with
the REQUEST, so it travels with the TASK — which is where the setting belongs.** **The seat declaration should
say what the seat DEFAULTS to; the task's declaration should name the switch it actually sends.**

## AND THE CAPACITY CASE IS RE-ESTABLISHED, ON BETTER EVIDENCE THAN BEFORE

**A local 9B answered a cabinet-shaped code task correctly: 5/5 against the frozen simulator, 193 completion
tokens, 3.4 seconds, ZERO API tokens, with the answer in the `content` field where an answer belongs.**

**Scope, unchanged and stated: temperature 0.0, so this is DETERMINISTIC and reproducible rather than sampled —
n=1 per setting is n=1 per PROMPT, and the generality limit is TASKS, not trials. One task, one alias.**

## WHAT I HAVE NOT DONE

**Nothing sent. No profile moved. No config changed.** **And the Chair's decision 2 needs re-taking on the
corrected numbers, not on mine from an hour ago.**
