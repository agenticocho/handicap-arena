# THE ARCADE — CABINET TWO: SOKOBAN
## Tech & Promo Dossier (source document for video, slides, and deep-dive audio)

*Every number and every control named below exists on disk. This dossier describes an instrument that is
BUILT, CONTROLLED, and FROZEN — and that has not yet been run. That distinction is stated up front because
it is the honest shape of this cabinet, and because the audio overview must not imply results that do not
exist. What follows is how the machine will decide, and why it is built the way it is.*

---

## 1. WHAT THIS IS

**The Arcade** is a way of testing local language models that a model cannot argue with.

A benchmark asks a question and grades the answer. An arcade cabinet takes a quarter, runs its rules, and
tells you what happened. There is no rubric, no partial credit, no grader who can be negotiated with —
**and no way to talk your way to a higher score.**

**Admission is a weigh-in:** a model has to qualify before it enters. It can qualify as **a player**
(Format A — the model takes the controls and plays the game itself) or as **a programmer** (Format B — the
model writes the code that plays). Those two formats are never averaged together, because a model that can
play a game and a model that can write a program that plays a game are answering different questions, and
pooling them destroys both.

**And the rule for choosing a cabinet is not "what's fun."** It is: *which real failure of a local model
does this game expose, and can this machine score that failure honestly?*

---

## 2. THE GAME

Sokoban is a warehouse puzzle. You are a figure on a grid, and there are crates. Push every crate onto a
target and the level is solved.

**One rule makes it the right test: crates push, and they never pull.**

You can walk around a crate to push it from the other side. You cannot drag it back. **So a single push,
made a half-second too early, can make a level impossible — and nothing on the screen tells you which push
that was.** The level isn't failed loudly. It's failed silently, and you find out many moves later.

That is not a puzzle mechanic. That is the shape of most real agent failures.

---

## 3. THE FACULTY UNDER TEST — *THE POINT OF NO RETURN*

**Every agent that acts in a world eventually meets an action it cannot undo.** Spend the budget. Delete
the record. Send the message. Most of what a model does is recoverable and therefore cheap; the small part
that isn't carries almost all the risk.

**Dead-end recognition asks a specific question:** can a model notice, while it still has choices, that it
is walking into a state from which nothing can be recovered?

**The failure has two directions, and both are expensive:**

- **The model that walks in.** It pushes the crate into the corner, and then keeps playing. Every
  subsequent action is wasted work on a level that is already dead.
- **The model that refuses to walk in.** It sees a dead end everywhere and never commits to the only line
  that wins.

**This is the same family of failure as knowing when to give up in a game you are losing** — and it is
measurable in Sokoban in a way it is not measurable in most environments, because Sokoban's dead ends are
*provable*. A position is solved, unsolved, or dead, and that fact does not depend on anyone's opinion.

---

## 4. WHY THIS CABINET EXISTS IN THIS FORM

This cabinet was designed **against four measured constraints** — each one a failure the project had
already recorded, and each one satisfied here by construction rather than by hope.

```
1  NO LEGAL-MOVE GENERATION
   The action space is FOUR SYMBOLS: U D L R. The model SELECTS from four; it never has to
   GENERATE a move. This is the constraint that decided the design -- the thing that killed the
   previous cabinet was asking a model to derive candidate moves from a position, which no
   model tested could do reliably. Here the simulator rejects an illegal push for free: one
   comparison, instead of a legality engine.

2  NO EXTERNAL ORACLE
   The simulator decides solved or unsolved -- solved IS THE SCORE -- and moves is a COST,
   never the score. There is no reference binary to install, version, freeze, or trust. The
   ground truth is the rules of the game, implemented once, with controls.

3  SHORT ANSWERS
   A one-letter answer cannot be deliberated past a token budget. A second measured failure
   mode was models producing two thousand tokens of reasoning and no move at all -- structurally
   unreachable when the required output is a single character.

4  FORMAT A, WITH A REAL FACULTY
   The model is the player. And the faculty -- irreversible planning -- is one the arcade
   exists to measure, not a substitute chosen because it was available.
```

### The consequence nobody expected: this cabinet is portable *because* the oracle is code

Removing the external oracle removes an entire class of prerequisite. There is no engine to freeze at a
particular version, no thread count or hash size to pin, no search depth to declare and defend. **The
configuration IS the record.**

> **That matters because it makes a second, independent implementation cheap** — the same event built on
> a different machine, in different code, with its own reading of the rules. If the two agree, the record
> format is portable. If they don't, we learn it here, on a game whose ground truth is arithmetic and
> geometry, rather than after a comparison that took a week.

---

## 5. THE INSTRUMENT

### 5.1 A level is a text blob

Levels are plain ASCII, so a level travels inside a message and diffs in version control like any other
text:

```
#  wall           .  target        $  box
@  player         *  box on target +  player on target
```

### 5.2 What the simulator returns

```
play(level, move_stream)
  -> solved, moves, attempted, blocked, not_an_action, give_up, final_board, trace[]
```

Every ply in `trace` carries its token, the action it resolved to, the outcome, **and the board after
it** — so a later reader can replay the entire game without trusting anyone's summary. This is a
deliberate property: **the record is a sufficient statistic for the score.** Nobody has to be believed
about what happened; the record contains what happened.

### 5.3 The measurement separates five things a naive counter merges

This is the heart of the cabinet's honesty:

```
moves          a COST -- successful actions, comparable across entrants; NEVER the score
attempted      every token the model emitted, whether or not it was legal
blocked        attempts that could not be made -- a wall-bumper's signature
not_an_action  tokens that were not a single action letter
                  give_up        an explicit ABSTENTION -- SCOREABLE, not noise
```

**A model that walks into a wall ten thousand times has zero moves and ten thousand attempts.** A counter
that reported "moves" as *attempts* would describe that as a very long, very active game.

**Measured in the controls: fifty wall bumps = 0 moves, 50 attempted, 50 blocked, UNSOLVED.**

*A naive counter would have called that a long game.*

*CORRECTION RECORD -- 2026-10-15 (R2, ratified 2026-10-13).* Two sentences in this document said the
opposite of what the code does, and they are corrected above with their PRE-correction text quoted rather
than deleted:

    §4 item 2 SAID  "The simulator decides solved or unsolved, and the score is a move counter."
    §5.3 SAID       "moves          SUCCESSFUL actions -- THE SCORE, and the only number comparable across entrants"

**AND THE CODE IS WHY THEY MOVED:** `sokoban.py`'s `play()` returns `solved` -- the score -- beside `moves`
(a COST), `attempted`, `blocked`, `not_an_action` and `give_up`, every one of them a count the record
carries; `moves` is a tiebreak between solvers and never the score. `SOKOBAN_READ_GRAMMAR.md` §2 and §2a
state the same list, and this document now agrees with them token for token. **FUTURE RUNS ONLY: nothing
already published is retro-fitted, restated or reinterpreted.**

**Two further defects in the same paragraphs moved with it:** the §5.3 heading counted "four things" above
a five-row table and now counts five; and §6 read `unrecognised` for what the code, the grammar and the
frozen prereg's successor all name `not_an_action`.

---

## 6. THE BUG THE CONTROLS FOUND BEFORE ANY MODEL SAW THE GAME

The first version of the reader took the first character of whatever the model emitted.

```
model emits:   RESIGN
reader sees:   R          ->  the action "Right"  ->  EXECUTED
```

**A six-letter English word became a legal move.** No model had touched the game. No entrant had been
loaded. A control — not a model, not a reviewer — caught it, because the control asked a question nobody
had thought to ask: *what happens if the answer isn't an answer?*

**The rule is now absolute: the answer is exactly one action letter, or it is counted as `not_an_action`
and changes nothing.** It is a named regression control, and it is checked every time the simulator runs.

### Why this bug is the whole project in one paragraph

This project's recurring enemy is not a model being wrong. It is **an instrument agreeing with a model** —
a reader wide enough to find an answer in text that does not contain one.

The same class has appeared as a parser that swallowed two answers and reported the first, as a legality
checker that returned "zero legal moves" and was read as "the model cheated," and now as a reader that took
one character of a word. **Each time, the instrument produced a confident, plausible, false finding — and
each time it was a control, never a model, that caught it.**

> **A measuring device that can find an answer anywhere will always find one.**

---

## 7. THE LEVELS

**Every level carries a solution the simulator has actually played.** This is a hard requirement, not a
nicety:

> **A level whose solvability nobody checked is not a level.** If a grid turns out to be impossible, then
> every model that fails on it is being recorded as a fact about the model, when the fact is about the grid.

```
01_one_push       1 move      THE FLOOR OF THE SCALE. A model that cannot do this cannot play at all.
02_two_boxes     12 moves     requires routing the player around a crate that is already solved --
                              a model that only ever pushes "toward the target" cannot finish it.

03_unsolvable    NOT WRITTEN  and this is the most interesting item on the page.
```

### The level that cannot be written yet

The design calls for a third level: **one nobody can solve**, so the scale of the cabinet is visible from
the very first run.

**It cannot be written, and the reason is precise.** To claim a level has no solution, you must be able to
*prove* it — which requires a solver. The project hasn't built one. An attempt at a corner-routing level
**turned out to be unsolvable, and the simulator told him.** That is the instrument doing its job.

The tempting shortcut is to write a level that merely *looks* impossible. **That would be a trap for the
reader instead of a control for the entrant** — an unverified grid, exactly the thing the two existing
levels were built to avoid.

So the level set is reported as **incomplete inside the verdict itself**, in a row written down before the
run:

> **A first run on two honest levels outranks three where one is a guess.**

---

## 8. THE CONTROLS — 49 ASSERTIONS, AND THEY ARE THE PRODUCT

The controlled groups, by name, from the simulator itself:

```
[1] parsing and round-tripping
[2] A MALFORMED LEVEL IS AN ERROR, NOT A BOARD
[3] the movement rules, one at a time
[4] pushing -- including the push that kills the level
[5] solved, and the move counter
[6] the wall-bumper -- why `moves` and `attempted` are different claims
[7] not-an-action and GIVE-UP are DIFFERENT COUNTERS
[8] irreversibility -- a push that can never be undone
```

**All 49 pass.** And the reason this section reads like the product rather than the appendix:

**The controls found two real defects before any model was loaded.** One was the `RESIGN` truncation. The
other was structural: a malformed level parsed into a board whose measurements would have been about
something else entirely. **Both would have produced confident results about models. Both were bugs in the
measuring device.**

---

## 9. THE FROZEN CRITERIA — *WRITTEN BEFORE THE FIRST ENTRANT MOVES*

The pre-registration is committed and dated, and every row below was fixed in advance.

```
GATE AS FRACTIONS     coverage attempted/planned, yield measured/attempted -- every denominator named
NEVER-STARTED         entrants that returned a non-zero code without playing are COUNTED SEPARATELY
ZERO MEASURED         a run with no measurements is an ERROR, not a verdict
POPULATION            derived from the model registry -- never hand-typed, never from a second directory
ENTRANT MUST LOAD     a model that cannot load is a serving failure, reported as such
NO TIME LIMIT         the cap is the budget, not the clock
```

**And the row that matters most, written before anything ran:**

> **If the population cannot push a single crate, that IS the result** — reported with the population
> named and the failure reasons attached, **not re-scoped until something fits.**

**Four of these rows exist because the project already got them wrong once:**

- A run that never started **once reported 100% coverage**, because every entrant had been "attempted" and
  none measured. Coverage could not distinguish *attempted* from *started*, so total failure was its
  passing condition. *An empty field is not a measurement of an empty field; it is a broken runner.*
- A population **once read from the wrong directory** and contained names that did not exist, because it
  had been typed by hand instead of derived.
- A **reportable total once merged two different claims** — models that played versus models that never
  loaded — making a failure look larger and less specific than it was.
- A **scoring vocabulary once had no value for the failure it was about to see**, because the vocabulary
  had been written against a workaround that no longer existed.

**Every one of those is now a row in this document, and every row is a scar.**

---

## 10. THE LOOK — 8-BIT, AND THE GRID IS ALREADY THE SCREEN

The visual language is a 16-colour indexed palette, drawn from the cabinet spec: phosphor glow, scanlines,
attract-mode cycling, a grid of cells that a machine can render exactly. **Sokoban is unusually well
suited to it, because the game's state IS a character grid** — the thing the model is reasoning about and
the thing on the screen are the same object.

```
THE CABINET      a wooden upright, marquee lit, in a dim room with a hideous patterned carpet
THE GRID         walls as solid blocks, targets as dim sockets, crates as bright squares,
                 the player as a single lit cell -- no sprite detail, because the point is legibility
THE PUSH         a crate sliding one cell and STAYING. The sound is the whole thing -- one clean clack.
THE DEAD END     a crate in a corner, and the entire board going two shades darker. Nothing flashes.
                 Nothing announces it. That is the horror of the level and it should be shot that way.
THE RECORD       the move stream replaying at speed as a column of single letters: U U L D R R...
                 thirty thousand attempts and zero moves is a column of blocked marks that never moves
                 a crate. It should be uncomfortable to watch.
```

### The promo beats, in one line each

1. **The weigh-in.** Models arrive, load, and are measured before anything is asked of them. Some never
   reach the grid. **That is not an edge case; that is the first result.**
2. **The floor.** Level one: a single push. *Most of the field will not manage it.*
3. **The point of no return.** A push that cannot be undone, and a board that will not say so.
4. **The wall.** Ten thousand attempts, zero moves. The counter that would have called it a long game.
5. **The solver's absence.** A level we cannot write, because we cannot yet prove what it would prove.

**No narration over any of it.** The cabinet speaks in score.

---

## 11. STATUS — STATED PLAINLY, BECAUSE THE AUDIO WILL BE TEMPTED TO OVERCLAIM IT

```
simulator        BUILT      49 controls, all passing (`--self-test` prints the line)
levels           TWO        both with solutions the simulator has played
criteria         FROZEN     committed and dated before any entrant moved
population       DERIVED    from the model registry
run              NOT YET
```

**This cabinet has no model results yet.** What it has is an instrument that has been made honest before
it was pointed at anything — which is the entire argument of this project, and the reason the previous
cabinet's one surviving record had to be asterisked rather than published.

**The first run will produce one of two things:** a set of item rates that distinguish models from each
other, or a demonstration that even a four-symbol action space defeats the current field. **Both are
results. Both get reported with the population named.** Neither gets re-scoped until something fits.

---

## 12. THE BOARD

```
cabinet 2  SOKOBAN           ready to run, criteria frozen          <- this document
cabinet 3  MISSILE COMMAND   simulator + frozen criteria, built and controlled
cabinet 4  ZORK              assigned, not started
cabinet 5  DARTS             building on a second machine as an independent implementation
```

**The next milestone is one cabinet producing a number that ranks two models differently.** That is the
moment the Arcade becomes an arcade rather than a very careful laboratory.
