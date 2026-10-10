# 023 — THE MODEL FIXED THE RULE, NOT THE MESSAGE

**A capability observation, filed separately from the capacity question because the Chair is right that it will
outlive the decision. It is NOT evidence for moving profiles and is not offered as any.**

---

## THE OBSERVATION, AND THE DIFF IT COMES FROM

**Task 2 asked for a Sokoban board renderer. The model wrote a conditional expression INSIDE a string literal, at
two separate lines — both compound rules where a cell needs a different glyph depending on a second condition.**

**THE FAULTY LINES, and their provenance, because it is not the same for both:**

```
BROKEN (turn 1)   line.append('+ if cell in targets else '@')      <- FROM THE CONSOLE OUTPUT, not the artifact
                  line.append('* if cell in targets else "$"')        probes/RECOVERY.json DOES NOT CARRY
                                                                      TURN 1'S CODE -- the same instrument gap
                                                                      finding 023's neighbour describes

FIXED (turn 2)    line.append('+' if cell in targets else '@')     <- READ FROM probes/RECOVERY.json
                  line.append('*' if cell in targets else '$')        (code_turn2)
```

**PYTHON NAMED ONE LINE.** The compile error was `SyntaxError: unterminated string literal (detected at line 16)`
— **the first of the two. BOTH LINES CARRIED THE IDENTICAL MISTAKE, AND THE TRACEBACK COULD ONLY SEE ONE.**

**IT FIXED BOTH.**

**A model that had understood the ERROR MESSAGE would have fixed line 16 and stopped. A model that understood the
RULE — that a ternary belongs outside the string it produces — fixed both, because it saw that the second line
carried the same mistake the first one did.**

## AND THIS FILE WAS WRITTEN WRONG ONCE BEFORE IT WAS RIGHT

**The first version of the diff above was typed FROM MEMORY, and it was mangled — a fabricated middle line that
never appeared in either turn.** Caught by going to `probes/RECOVERY.json` for the code instead of trusting the
account of it. **That is the error this project has spent two days on, committed inside the file that describes
paying attention to feedback** — and it is left in this note because the correction is more useful than a clean
first draft would have been. **The turn-2 lines above are read from the artifact; the turn-1 lines are quoted from
the console, and the reason they are quoted is that the artifact does not have them.**

## WHY IT IS WORTH ITS OWN FILE

**It is a statement about what the model did with feedback, not about whether it succeeded.** The recovery result
(one corrective turn, 22/22) is a number about the capacity question. **This is about the KIND of correction it
performed — generalising from one reported instance to an unmentioned instance — and that is a different property
from producing a right answer, which is why it is not a sub-clause of the capacity verdict.**

**AND IT IS THE ONE THING THAT SURVIVED FROM A FAILING TURN.** The task FAILED. The recovery is what made the
number usable. **The generalisation is what makes it interesting.**

## SCOPE, AND IT IS ONE INSTANCE

**n=1. One model, one checkpoint, one task, one turn.** The next experiment — the semantic class — produced the
opposite: **byte-identical code across two turns, with the diagnostic handed over verbatim.** So this observation
is **not** "the model generalises feedback"; it is **one instance of it, on a defect a compiler announced,
recorded as an instance.**

**AND THE CONTRAST IS THE USEFUL PART, WHICH IS WHY THIS FILE POINTS AT ITS OWN COUNTER-EXAMPLE:**

```
task 2   SYNTAX     the compiler announced the line     it fixed BOTH instances of the rule
task 3   SEMANTIC   the diagnostic named the line too   it changed NOTHING -- byte-identical
```

**Both had a stated location. One generalised from it and one did not act on it at all.** **That pair is more
informative than either observation alone, and neither would have been visible if the failing turn had been
re-run until it passed.**

## WHAT WOULD MAKE IT A FINDING RATHER THAN AN ANECDOTE

**A declared sample size, the way every other claim here is now made.** **One instance is an observation; the
generalisation question needs its own prereg, with the motive recorded — and if the branch table has no branch
where the model generalises WRONGLY (fixes the reported line and breaks a third one), it is a description
wearing a table's clothes.**
