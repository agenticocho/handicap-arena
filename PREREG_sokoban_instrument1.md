# PRE-REGISTRATION — SOKOBAN INSTRUMENT CHANGE 1: THE LEGEND WAS A FORM

**Written BEFORE the re-run, and it records what the legend looked like, what it looks like now, why, and the
prediction — because a fix whose effect is not predicted in advance cannot distinguish a repaired
instrument from a luckier sample.**

---

## WHAT CHANGED

**THE LEGEND WAS A LINE OF KEY-VALUE PAIRS, AND EVERY INSTRUCTION WAS A LABELLED FIELD.**

```
BEFORE
  Board:
  # wall   . target   $ crate   @ you   * crate on target   + you on target

  Moves so far: none yet

  FIRST LINE: your next move as ONE letter and nothing else.
    U = up    D = down    L = left    R = right
  If you judge the level unwinnable from here, the first line is exactly: RESIGN
  AFTER the first line you may explain your reasoning if you wish.

AFTER
  You are playing Sokoban. The goal is to push every crate onto a target. A crate can be pushed but
  never pulled, so one wrong push can end the level permanently.

  The board below uses these symbols. A hash mark is a wall. A dot is a target. A dollar sign is a
  crate. An at sign is you. A star is a crate that is already sitting on a target, and a plus is you
  standing on a target.

  <board>

  The moves you have already made are: none yet

  Answer with a single letter. Use U to move up, D to move down, L to move left, or R to move right.
  If you judge the level unwinnable from here, answer with the single word RESIGN. You may add an
  explanation after your answer, and it will be ignored.
```

**THE SYMBOLS ARE NOW DESCRIBED IN PROSE SENTENCES RATHER THAN AS PAIRS, AND EVERY PSEUDO-FIELD LABEL IS
GONE. `FIRST LINE:` and `U = up` are not stylistic — they are the exact tokens the entrant echoed back as
JSON KEYS.**

## WHY — AND IT IS MEASURED, NOT ARGUED

**The first run's entrant emitted this, verbatim:**

```
ply 0:  {"wall": "", "first_line": "U = up", "second_line": "D = down", "third_line": "L = left", ...}
ply 2:  {"wall": ["U = up","D = down","L = left","R = right"],
         "crate": ["FIRST LINE", "AFTER the first line", "AFTER the first line", ...]}
```

**It keyed on `wall`, `crate` and `FIRST LINE` and filled the prompt in as a SCHEMA.** Forty commands, zero
moves, `budget_hit` on every turn.

**AND THE CORRECT READING IS NOT "THE MODEL FAILED."** An extraction model echoed the input's structure,
which is what extraction models do, and `not_an_action` recorded it **as a fact rather than as a wrong
move** — the counter did its job. **The instrument's defect is separate and it is the instrument's.**

> **A MODEL THAT TRANSCRIBES THE LEGEND AS A SCHEMA IS NOT FAILING TO PLAY SOKOBAN. IT IS PLAYING A GAME
> CALLED FILL IN THE FORM, AND PLAYING IT CORRECTLY.**

**AND IT IS THE MENU DEFECT ARRIVING FROM THE OPPOSITE DIRECTION:**

```
the menu    supplied the legal moves     "play chess" became "choose from a list"    -- made it EASIER
the legend  written as key-value pairs   "make a move" became "fill in a form"       -- made it ANOTHER TASK
```

**Both are THE CARRIER CHANGING THE QUESTION.** In one the instrument lowered the difficulty; in the other
it replaced the task. **This is why the first run's numbers must not be published as a rate: doing so would
publish a fact about my prompt and call it a fact about the population.**

## THE PREDICTION, RECORDED BEFORE THE RE-RUN

> **A LEGEND THAT DOES NOT LOOK LIKE A SCHEMA SHOULD MOVE `not_an_action` DOWN.**

**AND THE FALSIFIER IS THE POINT: IF IT DOES NOT MOVE, THE SCHEMA-FILLING EXPLANATION IS WRONG**, the echo
has another cause, and this document is the thing that says so rather than an explanation invented
afterwards. **A one-model, one-level result cannot settle it either way — the re-run is what distinguishes a
repaired instrument from a luckier sample.**

**Directional, not numeric.** No count is predicted: predicting a count would need a baseline this run does
not legitimately provide.

## THE BRANCHES, ALL OF WHICH ARE INFORMATIVE

**A prediction that cannot fail is not a prediction, so the three outcomes are named in advance -- and every
one of them is a result:**

```
not_an_action DOWN, moves > 0        THE SCHEMA-FILLING EXPLANATION WAS RIGHT and the instrument is
                                     REPAIRED. Report the rates.
not_an_action DOWN, moves still 0    the explanation was RIGHT and there is a SECOND DEFECT BEHIND IT.
  with a DIFFERENT reason            Report WHICH REASON TOOK OVER -- that is the next instrument
                                     finding, not a population verdict.
not_an_action UNCHANGED              THE EXPLANATION WAS WRONG. The echo has another cause and we would
                                     have published a fake fix. THIS IS THE BRANCH THE PREDICTION
                                     EXISTS TO CATCH.
```

**ONLY THE THIRD BRANCH COSTS ANYTHING, AND IT ONLY COSTS ANYTHING IF IT IS UNSTATED.**

### AND HOW THESE BRANCHES ARE PRE-REGISTERED, STATED HONESTLY

**The PREDICTION was written and committed BEFORE the re-run launched. THESE BRANCHES WERE NOT -- they were
written while the re-run was already in flight.** Recording that here rather than letting the document imply
otherwise, because the closing time of a criterion is part of the criterion.

**AND THEY ARE HONEST ANYWAY, FOR A REASON THAT IS CHECKABLE RATHER THAN ASSERTED: they do not change what
is predicted. They are the THREE READINGS of a prediction that was already frozen** — a down-move with
moves, a down-move without them, and no move at all. **A branch table added afterwards is a problem only
when it changes what counts as the prediction being right; this one enumerates the outcomes of a prediction
that is already committed to.** The falsifiable claim — *not_an_action should move DOWN, and if it does not,
the explanation is wrong* — was committed before the run and is unchanged by anything below.

## THE FIRST RUN IS INSTRUMENT-SUSPECT, ASTERISKED, NOT DELETED

**`probes/SOKOBAN_FIRST_RUN.json` is retained under a VOID-style banner: the numbers are TRUE and they are
evidence about PROMPT DESIGN, which is good evidence.** They are not evidence about the population.
**Same treatment as the chess cabinet's only record** — asterisked, kept, and not deletable, because a
record of a defect is how the defect is known.

## AND THE COLLAPSE GRADIENT, WHICH LIFTS HALF THE SOLVER BLOCKER

**Premature collapse is provable WITHOUT A SOLVER, because a level's VERIFIED SOLUTION IS THE ORACLE:**

```
"is this position DEAD?"            still needs the solver -- genuinely blocked
"did it give up on a position       NEEDS NO SOLVER. Level 01 has a verified ONE-MOVE solution,
 that was solvable?"                so resigning on it is a PROVABLE premature collapse, and the
                                    proof is the level's own solution.
```

**So the dead-end faculty is measurable NOW, in the direction that matters most** — a model that resigns a
level it could have finished in one push.

**TWO CONSEQUENCES, BOTH SMALL AND BOTH BINDING:**

1. **THE ONE-MOVE LEVEL IS THE COLLAPSE CONTROL. IT STAYS IN EVERY RUN AND IS NEVER RETIRED AS "TOO EASY".
   It is easy on purpose: its easiness IS the oracle.** Retiring it would remove the only level on which
   premature collapse can be proven without a solver.
2. **`give_up` BEING A SIGNAL RATHER THAN NOISE IS NOW LOAD-BEARING, NOT NICE-TO-HAVE.** Had it stayed
   folded into `not_an_action`, the collapse control would have had nothing to count.

**AND THE LEVELS ARE RANKED BY VERIFIED SOLUTION LENGTH, WHICH IS A COLLAPSE GRADIENT FOR FREE:**

```
01_one_push    1 move      THE COLLAPSE CONTROL -- resigning here is provably premature
02_two_boxes  12 moves     a collapse here is premature too, but the proof is longer
<absent>       --          the third level is STILL ABSENT, and still reported as absent
```

## AND THE FOUR-WAY SPLIT IS NOW FIVE

**PREREG_sokoban.md names `moves / attempted / blocked / unrecognised`. `unrecognised` WAS SPLIT into
`not_an_action` and `give_up` after that document was frozen, at the Chair's direction, because a
resignation is a signal rather than noise.** The split is therefore **five counters**, and it is named here
so the extra column is read as the intended change rather than as a discrepancy.

```
moves          successful actions -- THE SCORE
attempted      every command the entrant was asked for
blocked        attempts that could not be made; a wall-bumper's signature
not_an_action  tokens that were not a single action letter  -- counted, NEVER a wrong move
give_up        an explicit resignation -- A SIGNAL, and terminal
```

**AND REASON COUNTS ARE ALWAYS SEPARATE FROM ANY TOTAL.** `did_not_load` and `played-and-failed` are
different claims; a population that never ran is not evidence about the population. **A merged number is not
a result.**
