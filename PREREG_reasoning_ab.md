# PRE-REGISTRATION — THE REASONING A/B. WRITTEN BEFORE THE FIRST NUMBER.

**Ruled and authorised by the Chair. The design, the prediction and the branches are frozen here, and the run
that follows is scored under exactly these.**

---

## WHY THIS RUN EXISTS

**Population run 2 produced a TRUE NUMBER AND NO MECHANISM.** Both Qwen entrants went from producing nothing
readable (`unreadable` 43 and 40) to solving a level (`unreadable` 0, solved 1) — **and the declared reasoning
setting is the only config change.** But **the launch argv changed and a third level was added at the same
moment**, so the honest sentence is *what changed*, not *why*.

**A true number with no mechanism is the state that kills projects.** This run is the single highest-value
step available, because it converts one into the other.

## THE PRE-REGISTERED PREDICTION

> **IF THE FLAG CARRIES THE EFFECT, THE QWEN ENTRANTS PRODUCE READABLE OUTPUT UNDER THE DECLARED SETTING AND
> REVERT TO UNREADABLE UNDER THE OVERRIDE.**

## AND THE BRANCHES — ALL THREE ARE INFORMATIVE, AND ONE OF THEM COSTS US

```
BRANCH 1   readable WITH the flag, unreadable WITHOUT   -> THE FLAG IS THE CARRIER. Report it, and note
                                                           the sample is TWO ENTRANTS, not a field.
BRANCH 2   readable BOTH ways                           -> the flag is NOT the carrier; the third level
                                                           or something else is. REPORT WHICH.
BRANCH 3   unreadable BOTH ways                         -> READABLE output never depended on the flag, and
                                                           the earlier improvement has another cause
                                                           entirely. THIS IS THE BRANCH THAT COSTS US
                                                           SOMETHING, AND ONLY IF UNSTATED.
```

**A prediction that cannot fail is not a prediction.** The falsifier is Branch 3, and it is written down
before the run for the same reason the legend A/B's was: **that table is the only reason a clean result was
not published as a confirmation it was not.**

## THE DESIGN — WHAT IS HELD FIXED AND WHAT VARIES

```
FIXED     the entrants (the two Qwen models), the three verified levels, the command cap, the token
          ceiling, temperature 0.0, ctx, ngl, the legend arm (new), the reader, the simulator
VARIES    EXACTLY ONE THING: --reasoning off (declared) vs --reasoning on (override)
```

**THE CONTROL COMES FIRST AND IT HAS ALREADY PASSED — the argv check, run before any model loaded:**

```
declared   REASONING 'off'  argv ['--reasoning','off']  source "declared in PREREG_sokoban.md"  changed False
override   REASONING 'on'   argv ['--reasoning','on']   source "override (experiment arm)"       changed True
```

**THE ARGV IS THE EVIDENCE, NOT THE FLAG NAME.** If the override had not changed the launch argv, **the A/B
would have been a comparison between two runs with different STORIES rather than different settings.**
Verified first, and it is recorded here because it is the precondition for the run meaning anything.

## THE THREE THINGS HELD WHILE THIS RUNS

```
1  UNREADABLE IS INSIDE THE DENOMINATOR (A6) -- a non-pass, on its own line, with never_started SEPARATE.
   AND THE COUNTS PRINT BESIDE THE RATES: a rate over `attempted` can be improved by quitting early, and
   this run is not going to be the one where that happens.

2  config.reasoning_argv and config.reasoning_changed_from_declaration are the fields that make this a
   CONTROLLED comparison. Both travel on every cell, and the arm is in the FILENAME so no artifact is
   overwritten by its own other arm (FINDING 018/020).

3  observed_is_an_inference: TRUE STAYS ON. The probe already lied once by naming a length measurement
   `observed: on` for a model that was ECHOING A SCHEMA, not deliberating. The summary prose must not do
   the same thing one level up.
```

## SCOPE, STATED BEFORE THE RESULT SO IT CANNOT BE READ INTO IT

**Two entrants, three levels, n=1 per cell, two arms.** **EVEN ON BRANCH 1 THIS IS A DEMONSTRATION, NOT A
FIELD.** Two entrants cannot establish a population-level effect, and the verdict will say so rather than
letting a clean result imply one.

**AND THE OVERRIDE IS AN EXPERIMENT ARM, NOT A DECLARATION.** A result from it does not change the cabinet's
declared setting; **changing the declaration is a separate act, in the PREREG, with its own reason.**
