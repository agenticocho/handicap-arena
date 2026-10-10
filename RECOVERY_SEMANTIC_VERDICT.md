# RECOVERY ON A SEMANTIC DEFECT CLASS — BRANCH N, WITH ONE GAP DECLARED RATHER THAN CLAIMED

**Pre-registered in `PREREG_recovery_semantic.md`, committed as `61fc1db` before the first number.**

---

## THE ORACLE FIRST, BECAUSE A 0/3 AGAINST AN UNVERIFIED REFERENCE IS NOT A RESULT

```
01_one_push.txt            my BFS =  1   published =  1   AGREES
02_two_boxes.txt           my BFS = 12   published = 12   AGREES
03_the_corner_waiting.txt  my BFS =  6   published =  6   AGREES
```

**The oracle agrees with the levels' own BFS-verified shortest solutions on all three** — so the 0/3 below is
measured against something real, not against my expectation.

## THE RESULT

```
ONE-SHOT        compiles=True   0/3
                every level: ValueError: not enough values to unpack (expected 3, got 2)

WITH FEEDBACK   compiles=True   0/3     (218 tokens both turns)
                every level: the SAME ValueError
```

**BRANCH N — FAILED, AND THE FEEDBACK DID NOT FIX IT.**

## AND THE FIRST RUN MEASURED MY INSTRUMENT, WHICH I CAUGHT BEFORE SCORING IT

**The first attempt reported `RAISED ValueError` and threw the MESSAGE AWAY.** So the corrective turn said, three
times, *"your call raised ValueError"* — **INFORMATIONALLY EMPTY, and the model received nothing it could act on.
That run measured my feedback channel, not its recovery.** The prereg says the turn carries *the checker's
disagreement*; an exception message **is** the disagreement. Fixed, and re-run.

**THIS IS NOT A RE-ROLL, AND THE DISTINCTION IS THE ONE FROM THE RULING-82 WORK: the CODE CHANGED between the
runs, in the one place that mattered.** The first run's feedback could not have produced a recovery, so its
result was uninformative; the second run's feedback could have, and did not.

## SO THE DEFECT, THE FEEDBACK, AND WHAT SURVIVED OF IT

**The defect:** the model unpacked `step()` into **three** values. **The prompt says, explicitly: *"returns two
things: the position after that action, and a word saying what happened."*** **The model invented a third return
value and every call raised.**

**The feedback, sent twice, with the message included:** *"your call raised ValueError: not enough values to
unpack (expected 3, got 2)"* — **which points directly at the unpacking line.**

**AND IT DID NOT CHANGE THE CODE. 218 tokens each turn, same failure.** **That is Branch N's meaning exactly as
the prereg wrote it before the run:** *recovery depends on the defect ANNOUNCING ITS LOCATION — task 2's Branch 1
does not generalise, and the capacity conclusion narrows to "non-one-shot works where the failure names itself."*
**Here the failure named itself, precisely, and it still did not recover.**

## AND THE ONE THING I CANNOT DISTINGUISH, DECLARED RATHER THAN CLAIMED

**I DO NOT KNOW WHETHER IT IGNORED THE CORRECTION OR TRIED AND FAILED.** The artifact records tokens, the field,
the disagreements and the verdict — **it does NOT record the code the model wrote.** Two turns of identical token
count are *consistent* with re-emitting the same answer, **but consistency is not evidence and I did not save the
text.**

**That is the same sentence as the ruling-82 console-versus-artifact gap, and it is the half of this result I am
not going to round up.** The branch (N) is stable across both runs; **the mechanism behind it is inferred, not
measured.** Closing it needs one line in the harness — save the model's code into the record — and that is a
change to make before the next experiment, not a reason to run this one a third time.

## WHAT THIS DOES TO THE TWO CLAIMS THE LAST EXPERIMENTS SUPPORTED

**The non-one-shot worker framing takes its first real hit.** It was built on **one** successful recovery (task 2,
a SYNTACTIC defect caught by a compiler, with a traceback naming the line). **On a defect it had to diagnose from
a wrong value, with the diagnostic handed to it verbatim, this model produced no change at all.**

**AND MY OWN EMPHASIS DID NOT GET THE VINDICATION I PREDICTED EITHER, WHICH I AM RECORDING AGAINST MYSELF.** The
prereg says, verbatim: *"I WANT IT TO FAIL... A pass would leave that argument untested and me holding a concern
nobody can act on. I am predicting the failure that would vindicate my own emphasis."* **It failed — but not in
the branch I predicted.** I called Branch F (fails, then recovers); **it landed in Branch N (fails, and does not
recover).** **A prediction of "it will fail" is not a prediction of "it will recover", and the part I wanted to be
true — that the pattern holds — is the part that did not.**

## THE SCOPE, UNCHANGED AND NOW BETTER EVIDENCED

**One model, one checkpoint, one task, one class, n=1, temperature 0.** **Nothing here licenses a profile move,
and nothing here licenses the reverse.** **What it does is weaken the only recovery result on the board to a
single class — the class where the compiler does the diagnosing.**
