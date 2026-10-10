# THE RECOVERY EXPERIMENT — RESULT. BRANCH 1, AND MY PREDICTION WAS WRONG.

**Pre-registered in `PREREG_recovery.md` and committed as `6372e4e` before the first number.** Artifact:
`probes/RECOVERY.json`.

---

## THE RESULT

```
turn 1   field=content   186 tokens   2.9 s   compiles=False   SyntaxError: unterminated string literal (line 16)
turn 2   field=content   187 tokens   2.9 s   compiles=True    22/22 MATCH THE FROZEN RENDERER
```

**BRANCH 1 — RECOVERED.**

## AND I PREDICTED BRANCH 2. I WAS WRONG, AND THE PREREGISTRATION IS WHY THAT IS INFORMATIVE.

**I predicted it would patch the SYMPTOM: fix the line the traceback named, leave the same construct standing on
the other compound rule.** **Reality did the opposite, and the diff is unambiguous:**

```
TURN 1 (broken)      line.append('+ if cell in targets else '@')     <- ternary INSIDE the string literal
                     line.append('* if cell in targets else "$"')

TURN 2 (fixed)       line.append('+' if cell in targets else '@')    <- ternary as CODE, strings as VALUES
                     line.append('*' if cell in targets else '$')
```

**IT FIXED BOTH COMPOUND LINES — THE ONE THE ERROR NAMED AND THE ONE IT DID NOT.** Python reported only the first
`unterminated string literal`. A model that had understood the MESSAGE would have fixed line 16 and stopped. **A
model that understood the RULE fixed both, because it saw that both lines carry the same mistake. IT ACTED ON
THE RULE, NOT THE MESSAGE.**

**AND THE PRE-REGISTRATION CAUGHT ME, WHICH IS THE WHOLE REASON IT WAS WRITTEN.** I recorded my own motive in the
prereg, verbatim: *"I predict this because it is the more interesting outcome and I would rather be caught
predicting the hard thing than be right about an easy one. Recording that motive too, so a correct prediction
cannot later be presented as insight."*

**I PREDICTED THE DRAMATIC BRANCH AND THE MODEL WAS BETTER THAN MY PREDICTION.** The motive sentence is now the
most useful line in the document, because it says in advance which way my bias ran — **and it ran exactly that
way. Without it, a wrong prediction is just a miss. With it, the miss is evidence about the PREDICTOR, which is
worth more, and it is checkable by anyone who reads the file.**

## THE READING IS THE ONE DECLARED BEFORE THE NUMBER, VERBATIM

**From the prereg, written before the run:**

> *"if this returns Branch 1, the correct capacity finding is NOT 'a local 9B can do cabinet work' — it is 'a
> local 9B can do cabinet work WITH A COMPILE-AND-FEEDBACK LOOP, and must not be run one-shot.' That distinction
> is the whole point, and it is written down before the number so it cannot be softened after."*

**So the finding is: A LOCAL 9B IS VIABLE AS A NON-ONE-SHOT WORKER.** Not as a one-shot oracle — task 2 failed
one-shot. **As a worker in a loop with a checker and real error feedback.**

**AND THAT IS THE SHAPE THE CABINET ALREADY HAS.** Every run here is a script with controls, a self-test that
must pass, and a simulator that rejects illegal input. **The pattern this experiment validates is not a
workaround; it is the pattern the work was already being done in.** *What was missing was the assumption that a
local model had to be good enough ONE-SHOT to be worth using, and that assumption was never anyone's decision —
it was the shape of the experiment.*

## AND THE TWO CAVEATS, BOTH WRITTEN BEFORE THE RUN

**1. A SINGLE RECOVERY DOES NOT LICENSE THE MOVE.** From the prereg: *"the honest next question is whether
recovery holds on a DIFFERENT task and a DIFFERENT defect class. That is not this experiment, and this
experiment does not answer it."* **That question is now the open one.**

**2. THIS IS NOT n=2 FOR THE ONE-SHOT QUESTION.** From the prereg: *"the second turn is a SECOND SAMPLE, and it
is NOT independent of the first — it has the first turn's failure in front of it. So this does not become n=2
for the one-shot question, and it must never be counted as one."* **It is not counted as one here.**

## WHAT THE WHOLE TWO-TASK SEQUENCE NOW SAYS

```
task 1   LOGIC            one-shot   5/5        193 tokens
task 2   SERIALIZATION    one-shot   FAILED     186 tokens   (ternary inside a string literal)
task 2   SERIALIZATION    + feedback 22/22      187 tokens   (fixed BOTH compound rules)
```

**One task clean one-shot, one task clean with a single corrective turn, and the correction was acted on at the
RULE level rather than the symptom.** **That is a coherent, checkable picture — and it is a smaller claim than
"5/5" was this morning, which is the direction claims should move.**

## WHAT I HAVE NOT DONE

**Nothing sent. No profile moved. No config changed.** **And I am not generalising this into a capacity finding:
it is one model, one task, one defect class, and the prereg's own next question is unanswered.**
