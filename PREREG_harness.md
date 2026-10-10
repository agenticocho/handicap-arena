# PREREG — TASK 3 THROUGH THE AGENT HARNESS, NOT A SCRIPT

**Written and committed before the first run.** Ruling 80 (the motive) and ruling 81 (an unfired branch is not a
refutation) both apply, and the Chair asked for an embarrassing branch.

---

## THE QUESTION, AND WHY IT IS THE RIGHT ONE

**Every number reported today — the A/B aside — came from a MODEL IN A SCRIPT: one prompt, one completion, scored
by my own code. THE CHAIR'S POINT IS THAT NO CABINET PROFILE WOULD EVER BE IN THAT CONFIGURATION.**

**A cabinet agent has:**
```
a SYSTEM PROMPT it did not write
TOOL SCHEMAS in its context
its own LOOP -- it chooses what to do next, and how many times
the ability to RUN what it wrote and see the result
a context that GROWS across turns
```

**NONE OF THAT IS IN MY MEASUREMENTS. So the question is not academic: a model that writes a correct function
when asked once, in a short context, may behave differently with a system prompt, tool schemas, and a loop.**

## THE CONFOUND, NAMED BEFORE THE RUN RATHER THAN DISCOVERED AFTER

**AN AGENT CAN TEST ITS OWN WORK.** It has a terminal. If it writes the function, runs it, sees a failure, and
fixes it — **that is a PASS FOR THE LOOP, NOT FOR THE MODEL, and it must not be read as the model's one-shot
ability.** **The script measured one-shot. The harness cannot measure one-shot, because the harness IS the
loop.** They are different questions and the branches below keep them apart.

## THE METHOD

**A THROWAWAY PROFILE (`harness-test`), NOT A CABINET PROFILE.** **No cabinet profile is touched, moved, or
reconfigured — the Chair's hold stands and this experiment does not require breaking it.** The test profile is
pointed at the local runtime (`llamacpp`, `127.0.0.1:8080`, a real alias read from the seat map) and given the
same task 3 prompt, a working directory, and the tools a cabinet agent would have.

**Then the ARTEFACT IT PRODUCED is checked against the same independent flood-fill oracle, by me, from outside.**
**Not its own report of success, and not its own test.** A file on disk either agrees with the oracle or it does
not.

## THE PREDICTION

**I PREDICT BRANCH 2 — it produces a correct artefact, AND only after running it and seeing a result.**

**AND THE MOTIVE, PER RULING 80:** Branch 2 is the outcome that makes the harness ADD value — *the loop is what
makes a local model usable* — which is exactly the story I have been telling since the recovery experiment.
**I want Branch 2 because it validates the shape of the thing I have been recommending all evening.**

## THE BRANCHES

**BRANCH 1 — CORRECT ARTEFACT, NO SELF-TESTING.** It wrote it right and did not need to check.
**READING:** the harness does not degrade the model, and the script's numbers carry over to the agent
configuration.

**BRANCH 2 — CORRECT ARTEFACT, ONLY AFTER SELF-TESTING.**
**READING:** the harness ADDS the ability to self-check. **A pass for the LOOP.** The capacity case becomes
"a local agent with a checker", which is the pattern the cabinet already has. **And the confound is the finding:
this cannot be compared to the script's one-shot number, because they are different questions.**

**BRANCH 3 — FAILS, OR PRODUCES A WRONG ARTEFACT. *(THE BRANCH I WOULD BE EMBARRASSED BY.)***
**READING:** **THE HARNESS MAKES IT WORSE THAN THE SCRIPT.** That would mean the configuration I have been
calling *"the only one that matters"* is WORSE than the one I spent all day measuring in — **and every number I
reported today would be about a configuration no profile will ever be in.** My framing would be not merely
over-cautious but backwards. **I am writing that out in advance because it is the outcome that costs me most,
and it is the one I have the least incentive to look for.**

**BRANCH 4 — DOES NOT FINISH.** Budget, turns, or an unreadable answer. **No result, reported as no result** —
not as a failure. Ruling 81 applies directly: *it did not happen is not it cannot happen.*

## AND WHAT THIS CANNOT SETTLE, STATED NOW

**One task, one model, one harness run.** A pass does not license the profile move. **And the defect class the
cabinet actually fears — a COMPILING WRONG ANSWER that survives a checker — still will not have been produced by
this, because I chose the task the model already passes.** **If the agent passes a task the script passed, that
is evidence about the harness. It is not evidence about the defect class that matters, and I will not let a green
result here close a question it never touched.**
