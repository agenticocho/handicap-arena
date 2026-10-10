# N — THE SWEEP IS IN, AND IT SAYS TWO THINGS

**Run twice. The first run predates the reader fix; this one is through the single reader of record (ruling 79).**

---

## 1. THE ANSWER THE CHAIR ASKED FOR: N CANNOT BE DECLARED ON THIS TASK

```
 N     finish_reason   tokens   correctness                        wall
-1     stop              179   1/5 (compiles)                     25.4 s     <- the shipped default
 0     length           4096   0/0 (DOES NOT COMPILE (SyntaxError)) 586.2 s
256    stop              192   0/5 (compiles)                     26.3 s
512    stop              178   0/5 (compiles)                     24.7 s

NO BUDGET PRODUCED A CORRECT ANSWER. THE DECLARATION SHOULD NOT BE MADE.
```

**That branch was pre-registered in the script before it ran, so it produced "don't" without anyone having to be
brave about it.** **The honest answer to "measure N" is that there is no N to declare: every budget I measured
either leaves the model unable to answer at all (N=0) or produces a wrong answer (N=256, N=512), and the shipped
default produces 1/5.**

**THIS IS A FINDING, NOT A FAILURE — and it is the outcome I told the Chair to expect before sending it.**

## 2. AND THE FINDING I DID NOT EXPECT, WHICH MATTERS MORE: THE BUDGETED ARMS ARE NOT REPRODUCIBLE

**I ran this sweep before, in the same configuration on the same machine. Compare:**

```
        FIRST RUN (before the reader fix)      THIS RUN (through the reader)
-1      stop    179 tok   1/5                  stop    179 tok   1/5          <- IDENTICAL
 0      stop    189 tok   3/5 (compiles)       length  4096 tok  SyntaxError  <- ENTIRELY DIFFERENT
256     stop    196 tok   1/5                  stop    192 tok   0/5          <- DIFFERENT
512     stop    558 tok   0/5                  stop    178 tok   0/5          <- DIFFERENT
```

**THE UNBUDGETED ARM REPRODUCED EXACTLY. THE BUDGETED ARMS DID NOT.**

**AND THE DIFFERENCE IS NOT MY READER.** The reader cannot change `finish_reason` — it does not write it, it
reports it. **N=0 was `stop` with the answer present in the first run and is `length` at the full ceiling in the
second. THE MODEL GENUINELY BEHAVED DIFFERENTLY.** **That is why this is worth reporting and not explaining away.**

## AND SO I HAVE TO RETRACT A CLAIM I HAVE MADE ALL DAY

**I have said repeatedly, including in delivered verdicts: *temperature 0, so the answer is DETERMINISTIC and
reproducible — n=1 per setting is n=1 per PROMPT, not a sample.***

**THAT IS NOT TRUE FOR A BUDGETED ARM, AND THE SWEEP IS THE PROOF: the same setting, the same weights, the same
machine, the same task, two runs, `stop` with an answer versus `length` at the ceiling with a compile error.**

**The claim survives for the unbudgeted arms — N=-1 reproduced to the token — and that is exactly what makes the
distinction visible rather than a blanket "nothing is reproducible".**

**THE MECHANISM I WOULD OFFER, AND IT IS A HYPOTHESIS FROM n=2:** a reasoning budget CUTS the deliberation at a
point that depends on how the tokens arrive — so the cut lands in a different place on different runs, and what
follows differs. **An unbudgeted arm has no cut to land differently.** **UNSTATED, n=2, and it would need its own
pre-registered experiment to become anything more than a guess.**

## THE CONSEQUENCE FOR THE DECLARATION, WHICH IS NOW DOUBLY DEAD

**Even if some budget HAD produced a correct answer, it could not have been declared on this evidence** — because
a declaration rests on a measurement that repeats, and the budgeted measurements do not. **The first problem was
"no N works here". The second is "an N measured here would not have meant what it looks like it means."**

## WHAT I DID, AND WHAT I DID NOT DO

**READ-ONLY on the machine.** No lease released, no process killed, no policy changed, no profile moved, nothing
sent. **The sweep ran CPU-only precisely so the VRAM tenancy could not confound it — and this is the one
measurement on this box that a warm seat cannot block.**
