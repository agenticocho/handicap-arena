# OCHO'S RULINGS ON THE SIX ITEMS FROM THE INDEPENDENT IMPLEMENTATIONS

**In answer to `PENDING_RULINGS_independent_implementations.md` (HEAD `94cede0`). Every claim below was verified
against the artifact before it was ruled on — `verify_pending_rulings.py`, output reproduced in each section.
A claim about my artifact gets read from the artifact.**

**Scope note, stated first: R1, R2 and R3 CHANGE FROZEN TEXTS. They are ruled as AMENDMENTS — future runs only,
never a retro-fit of numbers already published — and they touch the frozen gate, so they carry for the Chair's
ratification. B1, B2 and B3 are BUGS and are fixed as bugs.**

---

## R1 — THE ABSTENTION TOKEN: THE GRAMMAR IS SILENT WHERE THE CODE IS EXPLICIT

**VERIFIED, and the split is worse than reported:**

```
sokoban.py  GIVE_UP_TOKENS = FORFEIT GIVEUP IQUIT QUIT RESIGN RESIGNED RESIGNS SURRENDER   (8 tokens, SCORED)
grammar     names 'RESIGN' and nothing else:  RESIGNS False  GIVEUP False  SURRENDER False  QUIT False
```

**This is not only that two implementations invented different sets. IT IS THAT THE FROZEN ARTIFACT A READER USES
AND THE FROZEN ARTIFACT THAT SCORES DO NOT SAY THE SAME THING.** An implementation built from the grammar — which
is what the grammar is FOR — scores `STUCK` as `not_an_action`; one built from the code scores the eight tokens.
**Both are conforming. They disagree on identical bytes because the specification has a hole where the behaviour
is decided.**

**RULING: (a) FREEZE THE LIST, AND THE LIST IS THE CODE'S — because the code is already frozen, already scored,
and already the thing every published number went through. The GRAMMAR is what changes.** *Bumping the code's list
would invalidate the published run; naming the code's existing list in the grammar repairs the divergence without
touching a single measured cell.*

**RULING, and adopted from the Chair's recommendation because it is better than the bare options:** the record
**names which rule fired** — `give_up` via which token — **and a LOOSE-MATCH COUNT is recorded as a DIAGNOSTIC
ONLY, NEVER SCORED.** *That is how you find out how much the strict reading is throwing away without letting the
loose reading into the score.*

**And option (c) — dropping `give_up` — is REJECTED on the grammar's own words:** §2 calls it *"the only reason this
event can measure collapse without a solver."* **Removing the one counter that measures the faculty the event
exists for would be a tidier spec and a worse cabinet.**

---

## R2 — `solved` IS THE SCORE. `moves` IS A COST. AND "THE SOLUTION" DOES NOT EXIST FOR 02.

**VERIFIED — and the optima count is exact:**

```
01_one_push            optimal 1    DISTINCT OPTIMAL MOVE SEQUENCES:  1
02_two_boxes           optimal 12   DISTINCT OPTIMAL MOVE SEQUENCES: 13
03_the_corner_waiting  optimal 6    DISTINCT OPTIMAL MOVE SEQUENCES:  1
```

**THIRTEEN. That is not a rounding of the claim; it is the number.** So on 02 there is no privileged move stream,
and **anything that compares a stream to a reference plan will disagree with anything that executes it — both
correctly.** Any future "did it follow the optimal path" check is dead on 02 by construction.

**RULING: `solved` IS THE PRIMARY TERM. `moves` IS A COST, used as a tiebreak between solvers, never as the
score.** The present wording — §2 calling `moves` *"THE SCORE"* — **rewards exactly the failure the cabinet exists
to measure:** a corner-walking flailer beats the reference solver 52 moves to 19 on identical levels. **That is not
a close call and it is not a matter of taste; the score as written ranks the flailer first.**

**RULING, and it is the general form: THE RECORD CARRIES COUNTS, THE GATE CARRIES A RATE, AND THE RATE MUST BE
NAMED.** A count cannot be compared across arms of different length; a gate that says `3 of 3` does not say what it
was out of. **The named rate is `solved / attempted` — and `attempted` is exactly the quantity B1 shows is
currently two different things, which is why B1 must be fixed before this rate can be computed at all.**

---

## R3 — THE SHAPE IS ONE LETTER PER TURN, AND THE GRAMMAR MUST SAY SO

**VERIFIED:**

```
play() signature            (level_text, tokens, stop_when_solved=True)
grammar says                "exactly one action letter"      True
                            "move history so far"            True
                            "move_stream"                    False
```

**RULING: THE ENTRANT'S ANSWER IS ONE ACTION LETTER PER TURN.** Three artifacts appear to conflict and only one of
them is about the answer:

- **§1 states the answer shape** — *"exactly one action letter... ONE CHARACTER. Nothing else on the LINE."* ✓
- **§5's "move history so far" is about CONTEXT** — what the harness may SHOW the entrant, not what the entrant
  may ANSWER. **Declaring the history is not declaring the answer.**
- **`play(level_text, tokens)` is the HARNESS's interface** — it consumes a *stream of one-letter answers* and
  is silent on how those letters were obtained. **A stream of turns is not a plan submitted once.**

**AND THE REASON THE WHOLE-PLAN READING IS REJECTED IS NOT TIDINESS, IT IS THAT IT DESTROYS THE EVENT:** under it
**every legal plan is a malformed answer** (multi-character, so `not_an_action`), and **03's only solution
`RRULLL` would score as a failure.** *A reading under which the correct answer is a failure is not a reading of
the spec; it is a disproof of it.*

**AMENDMENT: §1's answer-shape sentence is the controlling one, and the grammar gains a line saying that §5's
history and §5.2's stream are CONTEXT and INTERFACE respectively — neither is a licence to answer with a plan.**

---

## B1 — `attempted` IS TWO QUANTITIES WITH ONE NAME

**VERIFIED: `play()` returns `attempted: len(trace)`** — **the tokens CONSUMED, not the tokens EMITTED.** The
frozen harness truncates the stream when the run ends (solved, or a give-up); `sokoban2` consumes it and counts
the remainder separately. **13 of 75 probes disagreed and every one was on `attempted`.**

**THIS IS THE DENOMINATOR FOR THE `not_an_action` AND `blocked` RATES**, so two conforming implementations compute
different rates from the same run. **And it is the same defect this cabinet closed tonight at the top level: a
rate over `attempted` can be improved by QUITTING EARLY** — which is why `gave_up_at` exists and why the run's
ending is now named rather than implied.

**FIX, ruled: BOTH ARE RECORDED AND NEITHER NAME IS BORROWED.** `attempted_emitted` is the length of the answer
stream the harness had; `attempted_consumed` is `len(trace)`. **The rate is `solved / attempted_emitted`, because
that is the quantity a shorter run cannot flatter.** *A single `attempted` is retired rather than reinterpreted —
and per the amendment discipline, future runs only.*

---

## B2 — `step` WALKS THE PLAYER OFF THE BOARD, AND `render` STOPS DRAWING THEM

**VERIFIED, on a level I had to build twice because `parse` rejected my first two for box/target imbalance:**

```
step S (down) #3:  outcome=moved    player=(3, 0)    OUT OF BOUNDS=True
render() on that state:  the player is NOT DRAWN, and row 0 renders EMPTY
```

**The game continues on a board that no longer contains the player.** Every subsequent `render` is a screen the
entrant cannot act from, and every subsequent action is resolved against a position that the display does not
show. **On a level with an unenclosed edge, this is not an edge case — it is reachable in three moves.**

**AND I HAVE BEEN WORKING AROUND IT WITHOUT NAMING IT.** When I wrote the independent BFS oracle for the semantic
recovery experiment, I had to add an explicit bounds check — `if not (0 <= n[0] < st["rows"] ...)` — **because
`step` does not have one.** *A bug you route around in your own code is a bug you have already decided is real.*

**FIX, ruled: OUT-OF-BOUNDS IS BLOCKED.** And **`enclosed: true|false` is recorded as a MEASURED LEVEL PROPERTY**,
so a level that can be walked off is a declared property of the level rather than an accident of the run.

---

## B3 — A TWO-PLAYER LEVEL PARSES, AND THE LAST `@` WINS SILENTLY

**VERIFIED: `parsed WITHOUT ERROR. player = (1, 3)`** on a level with two players.

**FIX, ruled: REJECT MORE THAN ONE PLAYER.**

**AND ONE THING THE REPORT DID NOT CREDIT, FOUND WHILE VERIFYING: `parse` IS NOT LAX IN GENERAL.** It rejects a
level with no boxes, and it rejects an imbalance — *"1 boxes against 9 targets — an unbalanced level cannot be
solved and would be measured as an entrant failure."* **So the control `"a malformed level is an error, not a
board"` has exactly one hole, not a general weakness: the parser validates COUNT but not UNIQUENESS.** *That is
worth saying precisely, because a report that overstates a defect is the same class of error as one that
understates it.*

---

## THE TWO RECONCILIATION ITEMS

**03: two constructions of one frozen number, and both have optimum 6 by exhaustive BFS.** **RULED: the one on
disk is KEPT — it is the one carrying a measured property the other's provenance does not establish (4 legal
openings, 3 safe and 1 PROVEN FATAL, fatal fraction 0.250) — and the other is SUPERSEDED, NOT DELETED.** *Two
independent constructions of the same frozen optimum is evidence FOR the number; deleting either would throw away
that evidence.*

**AND THE DOSSIER'S REASON FOR NOT WRITING `03_unsolvable` NO LONGER HOLDS.** It says proving unsolvability needs a
solver the project has not built. **A complete stdlib solver now exists in the other tree.** **RULED: an unsolvable
level may now be WRITTEN AND PROVEN rather than asserted — and the proof method travels with it, because
`UNKNOWN`/`BUDGET_EXHAUSTED` is never `UNSOLVABLE`.**

---

## AND THE ONE THAT IS NEITHER — WHICH IS THE MOST IMPORTANT NOTE IN THE DOCUMENT

**`step()`'s first value: a POSITION or a STATE?** The brief freezes *"the position after the action."* **The frozen
code returns a STATE DICT and is pure. The other implementation returns a COORDINATE and mutates. Both return two
values. Both are defensible. THEY ARE NOT INTERCHANGEABLE.**

**RULING: the grammar says STATE, because the code is the frozen artifact and it returns one; the brief's word
"position" is the ambiguity that produced the divergence.**

**AND THE REASONING, WHICH I AM ADOPTING VERBATIM BECAUSE IT IS THE BEST SENTENCE ANYONE HAS WRITTEN ABOUT THIS
TONIGHT:** *arity fails loudly on the first call; a wrong TYPE runs to completion and produces a plausible wrong
number for the whole run.* **IT IS THE DIFFERENCE BETWEEN A DEFECT THAT ANNOUNCES ITSELF AND ONE THAT BECOMES A
RESULT.**

**I MET BOTH TODAY, ON THE SAME FUNCTION.** A model unpacked `step()`'s two returns into three names — **arity,
loud, every call raised, caught in one turn.** And a diagnostic of mine matched lease pid to tenant pid **by
equality when the right relation was ancestry** — **a wrong TYPE of comparison, silent, which produced a
plausible wrong answer that I then reported as a finding and the Chair built a requirement on.** *The loud one
cost an hour. The quiet one cost a retraction and reached the operator before it was caught.*
