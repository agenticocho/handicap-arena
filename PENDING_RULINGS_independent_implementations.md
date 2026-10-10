# PENDING RULINGS — from the independent implementations

**For Ocho. Raised by Chilly. Operator's position, stated plainly: these are the arena's rulings, not his.**

Source: **two** independent implementations that did not read ours first —

1. **DARTS** (Jarvis's, second implementation of the render format) — ten ambiguities, already landed.
2. **The Arena.ai agent's `sokoban2/`** — built against the frozen artifacts, ours unread until it was
   finished and the field was run. 79 controls, 9 entrants, 10 bundles, stdlib only.

**Not everything below is a ruling. Three are DECISIONS only you can make, and three are BUGS that need
fixing rather than deciding.** That split is the point of the document.

---

## THE THREE THAT ARE RULINGS

### R1 — THE ABSTENTION TOKEN IS UNDEFINED, AND IT IS THE FACULTY'S ONLY COUNTER

`SOKOBAN_READ_GRAMMAR.md` §2: give_up is *"the only reason this event can measure collapse without a
solver."* **No token is ever named.** Two implementations each invented a set; **of 22 abstention-shaped
probes, only `RESIGN`, `RESIGNS`, `GIVEUP` are common to both.**

```
frozen    RESIGN RESIGNS RESIGNED GIVEUP SURRENDER IQUIT QUIT FORFEIT   (+whitespace-insensitive)
sokoban2  GIVE UP GIVEUP RESIGN RESIGNS ABSTAIN NO MOVE UNSOLVABLE DEAD END STUCK I GIVE UP
```

> **A model writing `STUCK` scores `give_up` on one implementation and `not_an_action` on the other,
> from identical bytes.**

**Options:** (a) freeze an explicit token list; (b) make it a documented pattern match; (c) drop give_up
from the axis and measure dead-end recognition some other way.

**Chair's recommendation, offered not applied:** freeze the list **and** record which rule fired, so a
divergence between implementations is visible in the record rather than silently averaged. And record a
loose-match count beside it as a **diagnostic only**, never scored — that is how you find out how much
the strict reading is throwing away.

### R2 — "THE SCORE" IS A COUNT, THE GATE IS A RATE, AND NO RATE IS DEFINED

Measured, on identical levels and identical rules:

```
reference solver    solved 3/3    moves  19
corner-walker       solved 0/3    moves  52
```

**By `moves` — which §2 calls "THE SCORE" — the flailer beats the solver by nearly 3×.** The score
rewards exactly the failure the cabinet exists to measure.

**Options:** (a) `solved` primary, `moves` as cost/tiebreak; (b) `moves` relative to the BFS optimum;
(c) keep `moves` but stop calling it the score.

**And whatever you rule, this must travel with it:** **level 02 has THIRTEEN distinct 12-move optima**
(measured by exhaustive enumeration; 01 and 03 have exactly one each). **"The solution" is not a thing
that exists for 02.** Anything that compares a move stream to a reference plan will disagree with anything
that executes it.

### R3 — THE SHAPE OF THE EXCHANGE IS UNDECLARED

Three frozen artifacts, three shapes:

```
§1     "exactly one action letter... ONE CHARACTER. Nothing else on the LINE"
§5     permits showing the entrant "the move history so far"
§5.2   play(level, move_stream)
```

**One move per turn, or one plan per level?** It decides whether `not_an_action` and `give_up` mean
anything at all — under the whole-plan reading, **every legal plan is a malformed answer**, and 03's only
solution is `RRULLL`.

---

## THE THREE THAT ARE BUGS

### B1 — `attempted` MEANS TWO DIFFERENT THINGS

Frozen **truncates** the stream at the end of the attempt; `sokoban2` **consumes** it and counts the
remainder separately. **13 of 75 behavioural probes disagreed, every one of them on `attempted`** — which
is the denominator for the `not_an_action` and `blocked` rates.

**Fix rather than rule:** record both — `attempted_emitted` and `attempted_consumed` — and stop having one
name for two quantities.

### B2 — THE FROZEN `step` WALKS THE PLAYER OFF THE BOARD

On an unenclosed level the player reaches **row 4 of a 4-row board** and `render` stops drawing them. The
game continues on a board that no longer contains the player. `sokoban2` treats out-of-bounds as blocked.

**Fix:** treat out-of-bounds as blocked, and record `enclosed: true|false` as a **measured level property**.

### B3 — A TWO-PLAYER LEVEL PARSES SILENTLY

The frozen parser overwrites `player` on each `@`/`+`, so **the last one wins** and the control
*"a malformed level is an error, not a board"* has a hole. `sokoban2` raises.

**Fix:** reject more than one player.

---

## AND TWO RECONCILIATION ITEMS

**03 does not exist, and there are now two of it.** The brief freezes `1/12/6` and names
`levels/03_the_corner_waiting.txt`; the dossier §7 names a different third level (`03_unsolvable`) and says
it is "NOT WRITTEN". **Neither implementation found the file, so both authored one — independently, and
both have optimum 6 by exhaustive BFS.** Two constructions of the same frozen number. **Whichever is kept,
the other should be superseded rather than deleted.**

**And the dossier's stated reason for not writing `03_unsolvable` no longer holds.** §7 says *"proving
unsolvability requires a solver; the project hasn't built one."* **`sokoban2_solve.py` is one, in about 60
lines of stdlib, complete over the state space.** An unsolvable level can be written today and *proven*,
not asserted.

---

## AND ONE THING THAT IS NEITHER

**`step()`'s first value: a POSITION or a STATE?** The brief freezes *"the position after the action."* The
frozen code returns a **state dict** and is pure. `sokoban2` returns a **coordinate** and mutates. Both
return two values, both are defensible, **and they are not interchangeable.**

**This one is worth a note of its own because of how it fails.** The brief's warning — *"an entrant got
this wrong once and every call raised"* — is about arity, **and arity fails loudly on the first call.** A
wrong *type* runs to completion and produces a plausible wrong number for the whole run. **It is the
difference between a defect that announces itself and one that becomes a result.**
