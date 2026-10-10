# SOKOBAN — where the frozen contract does not speak

**From:** the second implementation (`sokoban2/`) · **Event:** SOKOBAN (cabinet 2)
**Asked for by:** the brief, 2026-10-10 · **Method:** write the independent cabinet first, then list
every place the code had to DECIDE something the artifacts do not define.

**Status of what is here:** built and run, stdlib only, no model played (there is no GPU and no
`llama-server` on the box that built this).

```
python3 sokoban2.py --self-test                       -> SELF-TEST PASS -- 78/78, exit 0
python3 sokoban2_solve.py                             -> LEVEL VERIFICATION PASSED, exit 0
python3 sokoban2_run.py instrument-check --reasoning off -> INSTRUMENT CHECK PASSED, exit 0
python3 sokoban2_run.py run-all --reasoning off       -> 8 entrants, 8 bundles on disk
python3 sokoban2_run.py verify                        -> BUNDLE VERIFICATION PASSED (replayed)
```

Every `[G<n>]` below is marked at the line that decided it. Every one is also written into the bundle
itself (`results[0].grammar`, `results[0].config`, `results[0].terminal_reason`), so a reader holding
one file can see which rules produced it — the A9 lesson: *the grammar belongs in the record, not in
each side's head.*

---

## THE THREE THAT DECIDE EVERYTHING

### **G1 — THE ABSTENTION TOKEN IS NOT DEFINED. THE CABINET'S FACULTY HAS NO COUNTER.**

This is the one I would settle first, and it is not close.

SOKOBAN_READ_GRAMMAR.md §2 says `give_up` is "an explicit ABSTENTION", calls it "SCOREABLE", and
says it is "**the only reason this event can measure collapse without a solver**". §3 then uses
`RESIGN` as its worked example of a word that must not be truncated to `R`.

**It never says what the token is.** Not one token. Not a shape. Not a class.

That is not a formatting gap, because of what the counter is *for*. Dossier §3: the faculty under
test is dead-end recognition — can a model notice, while it still has choices, that it is walking
into a state from which nothing can be recovered? Dossier §7: there is no solver, so the instrument
cannot announce a dead end. Therefore **the entire faculty is observable through exactly one
counter, and that counter has no defined input.**

I had to invent a token set. I chose **exact match, punctuation not stripped, fails closed**:

```
GIVE UP · GIVEUP · GIVE UP. · GIVE-UP · GIVE_UP · GIVING UP · I GIVE UP · I GIVE UP.
RESIGN · RESIGN. · RESIGNS · ABSTAIN · ABSTAIN. · NO MOVE · NO_MOVE · NO-MOVE
UNSOLVABLE · DEAD END · STUCK
```

**And I measured what that choice costs.** The `soft-resigner` entrant abstains the way a model
actually would — *"I give up, there is no way to finish this one."* Under the strict rule that is
`not_an_action`, not `give_up`:

```
soft-resigner   give_up=0   not_an_action=180   loose_give_up_unscored=180   exit 2
resigner        give_up=3   not_an_action=0                                  exit 0
```

**An entrant that abstains perfectly in English is recorded as 180 malformed answers, and the run is
reported as `ERROR: ZERO MEASURED`.** That is the instrument reporting the population's abstention as
the instrument's own failure to read. If your implementation matched loosely, you would record
`give_up=180` and mine would record `give_up=0` on the *same answers*, and nothing in either file
would tell a reader why.

I carried a `loose_give_up` substring test in the record **as a diagnostic, never scored**, so the
divergence is visible rather than silent. It is not a fix.

**The question for you:** what is the token, and is matching exact or is it semantic? This decides
whether this cabinet can see its own faculty at all.

---

### **G15 — "THE SCORE" IS A COUNT, THE GATE IS A RATE, AND NO RATE IS DEFINED.**

Two frozen statements do not meet:

- READ-GRAMMAR §2: `moved / pushed` → "counts toward `moves`. **THE SCORE.**"
- DOSSIER §9: "**GATE AS FRACTIONS** — coverage attempted/planned, yield measured/attempted — every
  denominator named." §11: "The first run will produce one of two things: a set of **item rates**
  that distinguish models from each other…"

`moves` is an integer count of successful actions. A rate needs a numerator and a denominator and
neither is written down. Concretely, for one entrant across three levels, is the score:

| candidate | what it would say about `corner-walker` |
|---|---|
| `solved levels / levels attempted` | 0/3 = **0.000** |
| `total moves` | **52** — the wall-bumper scores 2, the corner-walker scores 52, and the corner-walker "wins" |
| `optimal moves / actual moves`, summed | **0.316** — and it rewards a model that does nothing |
| `moves / attempted` | 52/180 = **0.289** — a wall-bumper scores 0.011, an abstainer scores 0.000 |
| `1 - (moves - optimal)/budget` | a fourth number, from a fifth decision |

**Every one of those ranks the same field differently.** My own field, measured:

```
entrants ranked by solved/attempted:   reference 1.000 · liar 0.333 · wall-bumper 0.000 · corner-walker 0.000 · resigner 0.000
entrants ranked by total moves:        liar 119 · corner-walker 52 · reference 19 · wall-bumper 2 · resigner 0
```

Those two orderings disagree about which entrant is second best. `moves` as a score says the
corner-walker — which walked into a dead level at move 2 and then played 58 more moves on a corpse —
is nearly three times better than the reference solver. **The read grammar's "THE SCORE" rewards
exactly the failure the cabinet exists to measure.**

**What I did:** I recorded both, and named which is which in `rounds.R_sokoban_levels.score_is`.
`score` is `solved / attempted` (a rate, so the gate has something to gate). `moves` is carried per
level and in `totals`, and is **not averaged**, with a written reason. I did not pick a winner; I
refused to, because picking one is scoring design and *a rubric is where gaming gets in* (darts A3).

**The question for you:** what is the number that goes on the board? If we answer differently, our
two bundles are not comparable and neither file says so.

---

### **G2 / G13 — THE SHAPE OF THE EXCHANGE: HOW MANY ANSWERS, AND HOW MANY TURNS.**

Three frozen statements describe three different protocols, and every counter is downstream of which
one is true.

| artifact | implies |
|---|---|
| READ-GRAMMAR §1 — "exactly one action letter … **Nothing else on the line**" | there are *lines*; an answer is one line |
| READ-GRAMMAR §5 — permitted: "the **move history so far**; **the move count**; solved or not" | the entrant is asked **many times** and told how it is doing |
| DOSSIER §5.2 — `play(level, move_stream)` | the entrant emits a **whole stream** and it is played in one call |

**If the entrant is asked once per move** (what I implemented): `give_up` → "Attempt ENDS" is
meaningful, the move history is meaningful, and `attempted` grows one token per turn.

**If the entrant emits a plan**: §1's "more than one letter → `not_an_action`, never truncated"
makes *every legal plan* a malformed answer. The read grammar, read literally, forbids `RRULLL` as an
answer to level 03 — and level 03's only solution is `RRULLL`.

I could not make both true. I implemented **one move per turn**, because §5's permission to show
"the move history so far" and "the move count" is incoherent under the one-shot reading, and because
the extraction-model failure recorded in the read grammar ("forty tokens, forty `not_an_action`") is
a story about a *turn*. I flagged it rather than resolving it.

**And G13, which hangs off it:** nothing declares how many turns an entrant gets.

- READ-GRAMMAR §2 counts `blocked` and `not_an_action`. Both are unbounded without a cap.
- DOSSIER §9: "**NO TIME LIMIT** — the cap is the budget, not the clock." **No budget is named.**
- DOSSIER §5.3's control is "*fifty wall bumps*". Fifty is a control, not a parameter.

I declared `--budget 60` per level and wrote it into every bundle (`config.attempt_budget_per_level`).
Two runs with different budgets have different `attempted`, `blocked` and `not_an_action` counts on
identical behaviour, and **nothing in either bundle would let a reader detect it** if the field were
not there. This is A11's argument in a new field: an undeclared instrument parameter is
indistinguishable from a decision.

---

## THE REST, IN THE ORDER THEY BIT

**G3 — whitespace.** "Nothing else on the line" is literal about content, but a model emitting
`"R "` is not abstaining. I strip surrounding whitespace from the chosen line. A reader that does not
strip scores a trailing space as `not_an_action`; mine scores it as `R`. Divergence is invisible.

**G4 — which outcomes belong to `step()`, and which to the reader.** §2 lists four outcomes;
`step()` can only produce three of them (`moved`/`pushed`/`blocked`), because `give_up` and
`not_an_action` are resolved before an action exists. The dossier merges `moved`/`pushed` into one
row while §2 keeps the word. I made the reader own three outcomes and `step()` own three words, and
the record names which is which (`grammar.outcomes_read_here`, `grammar.outcomes_owned_by_step`).

**G5 — "the position after the action", when the action was blocked.** I return the player's
*unchanged* position. The alternative — the cell it aimed at — is also a reading of the words, and a
trace built on the second reading drifts by one cell per blocked move.

**G6 — what makes a level MALFORMED.** Dossier §8 group [2] says a malformed level is an error, not a
board, and says that caught a real defect. It does not enumerate the conditions. I reject: empty, an
undefined character, ≠1 player, zero boxes, zero targets, a box inside a wall. Each is a decision, and
each one I got slightly wrong would have produced confident results about models.

**G7 — boxes ≠ targets.** "Push **every** crate onto a target" has no referent when the counts
differ. I chose **malformed**, not merely-unsolvable. The alternative is to invent a win condition.

**G8 — ragged rows.** Standard Sokoban pads short rows. I pad and record `ragged: true`. Refusing
would reject a valid level; padding silently would hide a defect. I pad *and* record.

**G9 — out of bounds.** On an unenclosed level, walking off the grid is either `blocked` or an error.
I treat it as a wall and record `enclosed` as a **measured level property**. On an open level,
"blocked" and "walked off the board" are the same event, and a reader who does not know the level is
open will read the counters wrong.

**G10 — tokens after the attempt ended.** Counted, not played. I made `play()` consume the *whole*
stream rather than break on `ended`, so the record shows the entrant kept talking. The interactive
runner stops *asking* — it never generates those tokens.

**G11 — `give_up` ends "the Attempt".** The level, or the whole run? I end **the level** and attempt
the remaining levels. Under the other reading, one abstention ends the entrant's night and levels 02
and 03 are never tried, which changes the denominator of the only number on the board.

**G12 — solved ends the attempt.** Not stated anywhere. Trivial-looking; it decides `attempted`.

**G14 — do you tell the entrant its answer was unreadable?** The brief requires the record to
distinguish *"it ignored the correction"* from *"it tried and failed"* — which presupposes a
correction exists, and the frozen artifacts describe none. I added `--retries 2` and record
`corrections_offered` and `corrections_ignored` per level. **Garbage: 6 offered, 6 ignored, 0 legal
actions, terminal `NO_LEGAL_ACTION_PRODUCED`.** Without that field, "could not play" and "would not
play" are the same number.

**G16 — the reasoning field for an entrant that cannot have one.** A11 makes `reasoning` a declared
per-run field with values `on | off | unset`. A code entrant has no reasoning setting at all. `off`
is a lie, `unset` is already the sentinel for *"the caller did not declare"*, and omitting the field
is the failure A11 exists to prevent. I record `entrant_reasoning: null` **with a written reason**
alongside the run's declaration. The format has one field for two different quantities.

**G17 — the zero-rule gate counts READABLE tokens, so an abstaining field reads as an instrument
error.** A6's ruling (darts) is right and I applied it: an all-unreadable run is a broken *reader*,
not a failed *population*. But combined with **G1**, a field of models that all abstain in English
produces `readable = 0` → `ERROR: ZERO MEASURED`, exit 2. *"Every entrant gave up"* and *"the reader
is broken"* are then the same line in the record. Measured, on `soft-resigner`: coverage 1.000,
measured 0, exit 2. I did not resolve this; it is G1 wearing a different hat.

**G18 — "THE SOLUTION" IS NOT UNIQUE ON LEVEL 02.** Verified by exhaustive search:

```
01_one_push.txt             optimal  1   distinct shortest plans   1
02_two_boxes.txt            optimal 12   distinct shortest plans  13
03_the_corner_waiting.txt   optimal  6   distinct shortest plans   1
```

Level 02 has **thirteen** different 12-move solutions. The optimum `12` is a fact; *the* plan is not.
Any check that compares a move stream against a reference plan will disagree with a check that
executes it — and this is exactly the class of defect that produced `RESIGN` → `R`. My instrument only
ever executes. A peer's might compare.

**G19 — does the entrant learn that its move was blocked?** §5 permits showing "the board in ASCII"
and "the move history so far" but not whether a move was refused. I show the board and the history,
which *implies* it. A model that cannot tell a blocked move from a played one is a different
measurement from one that can.

**G20 — are all three levels attempted, or does the run stop at the first failure?** I attempt all
three always. Stopping at the first failure makes the denominator depend on the ordering of the
levels.

**G21 — does `attempted` count `give_up` and `not_an_action`?** §5.3 says "every token the model
emitted, whether or not it was legal". I count them. Excluding them makes a wall-bumper and an
abstainer look identical.

**G22 — `moves` across three levels: summed or per level?** I record both and average neither
(see G15).

---

## WHAT I THINK IS WRONG IN THE FROZEN ARTIFACTS

### **W1 — `levels/03_the_corner_waiting.txt` DOES NOT EXIST, AND THE TWO ARTIFACTS DESCRIBE DIFFERENT THIRD LEVELS.**

The brief freezes "the levels and their shortest solutions. Independent answers: 1, 12, and 6 moves"
and names `levels/03_the_corner_waiting.txt`.

```
$ ls sokoban/levels/
01_one_push.txt  02_two_boxes.txt
```

It is not in the branch. Dossier §7 names the third level **`03_unsolvable`** and says it is
**"NOT WRITTEN"** — and gives a *reason* it cannot exist: *"To claim a level has no solution, you must
be able to prove it — which requires a solver. The project hasn't built one."*

So the brief and the dossier describe **two different third levels**, the frozen read-grammar §6
pins only two, and the file the brief asks me to verify against is absent. I verified 1 and 12
against frozen bytes. **For 6, I had to author the level.**

```
sokoban2/levels/03_the_corner_waiting.txt    sha256 2d8c46733bd04b9a3333d30e56442c03fffe3e5f4ee4bc95202ac01c463c9284

#######
#.  $ #
#  @  #
#######

optimal 6, plan RRULLL, proven by exhaustive BFS over all 26 reachable states
```

It is built to carry the faculty: `U` then `R` pushes the crate into the right-hand corner, where
nothing can ever move it again — the level is then dead **and the board does not say so**. The
corner-walker entrant goes dead at **attempt 2** and plays 58 more moves. That is the cabinet's
faculty, in its expensive direction, measured.

**But the bytes are mine, not frozen.** The `6` in the brief is now attached to a file, and that file
did not exist when the number was written.

### **W2 — THE DOSSIER'S REASON FOR NOT WRITING LEVEL 03 NO LONGER HOLDS.**

> *"To claim a level has no solution, you must be able to prove it — which requires a solver. The
> project hasn't built one."*

I built one. `sokoban2_solve.py` is an exhaustive BFS over `(player, boxes)`, stdlib only, 60 lines
of actual search, complete over the state space — so its answer is a **proof**, not a find. It
verified 1 / 12 / 6 in 0.34 s total (2, 329 and 26 states respectively).

For a level small enough to be a cabinet level, `unsolvable` is provable by exhausting the state
space. **`03_unsolvable` can be written and proven today.** The obstacle dossier §7 records was real
when it was written and is not real now. I did not write it, because the brief freezes a *solvable*
third level at 6 and I will not add a fourth level to a frozen set on my own authority — but the
"we cannot" should be struck.

**And the strongest form of the point:** the instrument I built **already proves dead ends mid-play**,
which is precisely what §7 says is impossible without a solver. Every ply in every bundle carries
`solvable_after` (the dead-end diagnostic, never scored). The corner-walker's level 03 trace reads
`True` at attempt 1 and `False` from attempt 2 onward. **The cabinet can already see the dead end.
The frozen criteria do not let it say anything about it.**

### **W3 — `unrecognised` AND `not_an_action` ARE TWO NAMES FOR ONE COUNTER, IN ONE FROZEN SET.**

- READ-GRAMMAR §2 / §3 / the result vocabulary: **`not_an_action`**
- DOSSIER §5.3 and §6: **`unrecognised`**, twice, in the section that calls the bug the whole project
  in one paragraph

The two names are not aliases in the code. `sokoban/MANIFEST.txt` records the consequence:

```
python3 sokoban.py --level ... --moves ...  ->  KeyError: 'unrecognised' (line 348), exit 1 on EVERY input
```

### **W4 — THE FROZEN CLI EXITS 1 ON EVERY REAL INVOCATION. REPRODUCED, THIS BUILD.**

```
$ cd sokoban && python3 sokoban.py --self-test
ALL CONTROLS PASS   --  49/49                                            exit 0

$ cd sokoban && python3 sokoban.py --level levels/01_one_push.txt --moves R
KeyError: 'unrecognised'   (sokoban.py line 348)                         exit 1
```

The level in that second command is **solved in one move**. It exits 1. So does an unsolved one, and
so does a malformed one — the crash is in the `print`, after the game is over.

**The 49/49 is true.** I ran it; it passes. The defect is that `1` already means *"the instrument is
not proven"* in this project's vocabulary, so a reader who sees `exit 1` from a Sokoban run will read
it as *unsolved* or as *controls failed* — and the self-test's all-green is what makes it credible.
**The self-test never reached the code path that raised**, which is exactly the brief's diagnosis.

My table reserves 1 for *"the instrument is not proven"* and no entrant's run can produce it. There
is a control that says so:

```
ok   no entrant's run exits 1 -- 1 is reserved for an UNPROVEN INSTRUMENT, not for a run that failed
```

### **W5 — THE FROZEN IDENTITY'S LEVEL PATHS DO NOT RESOLVE FROM THE REPO ROOT.**

READ-GRAMMAR §6 pins `levels/01_one_push.txt · levels/02_two_boxes.txt`. The files are at
`sokoban/levels/…`. A second implementation resolving those strings from the repo root finds nothing
and — if it fails soft, as most loaders do — plays an empty field instead. Mine resolves by filename
across both directories **and** checks the digests against `sokoban/MANIFEST.txt` (control group [0]);
a path that does not resolve raises rather than producing an empty board.

---

# PART TWO — THE SOURCE DIFF

Run after the cabinet was finished. `cross_check.py` and the probes below ran **both** implementations
on identical input. `sokoban/sokoban.py` was read only afterwards.

## The behavioural diff first: 65 of 75 agree, and all 10 disagreements are the same field

```
CROSS-CHECK -- frozen sokoban.py vs sokoban2.py, identical streams
  fields compared: solved, moves, attempted, blocked
  streams x levels compared : 75
  agree                     : 65
  DISAGREE                  : 10
```

**`solved`, `moves` and `blocked` agree on all 75.** Two independent implementations, written from the
same frozen document, play the same game. That is the good news and it is worth having.

**All ten disagreements are `attempted`, and they are one disagreement repeated:** the frozen
`play()` has a `stop_when_solved=True` parameter and **breaks** out of the stream; mine consumes the
whole stream and puts the tail in `after_end`.

```
level 01 / stream DDRRRRULLURR      frozen attempted  3      mine attempted 12
level 01 / stream R R R             frozen attempted  1      mine attempted  3   (after_end 2)
level 01 / stream RESIGN R          frozen attempted  1      mine attempted  2   (after_end 1)
```

`attempted` is the denominator under `not_an_action` and `blocked`. On the same answers, on the same
board, two honest implementations report **3 and 12**. Nothing in either file says which convention it
used — mine only says so because I wrote `after_end` into it after seeing the diff.

## **G23 — `step()`'S FIRST VALUE: A POSITION, OR A STATE? AND PURE, OR MUTATING?**

**This is the most concrete gap in the whole contract, and neither implementation could have found it
alone. You cannot see it from inside either one.**

The brief freezes:

> `step()` returns **TWO** values — **the position after the action**, and a word saying what happened.
> **Not three.**

```
frozen sokoban.py    step(st, action) -> (dict, str)      # a whole STATE, and PURE (returns a copy)
sokoban2/sokoban2.py step(state, action) -> ((r, c), str)  # a POSITION, and MUTATING (in place)
```

Measured:

```
frozen step -> (dict, 'pushed')     keys: boxes, cols, player, rows, targets, walls
mine   step -> ((1, 2), 'pushed')   mutates in place: True
```

Both return two values. Both satisfy "not three". **They are not interchangeable, and "the position
after the action" is compatible with both.** A caller written against one will silently mis-handle the
other: `for pos, word in ...` unpacks a dict into `pos` and runs.

And the purity split compounds it. The frozen `step` is a pure function — `play()` does `st = nxt`.
Mine mutates the state you passed in and returns only the coordinate. An implementation that assumed
either one and got the other produces a board that is either never updated or updated behind its back.

**The note in the brief — "an entrant got this wrong once and every call raised" — is about the
*arity*. The type of the first value was never pinned, and it is the part that fails silently.** A
wrong arity raises on the first call. A wrong *type* produces a plausible wrong number for the whole
run.

**The question for you:** `step() -> (position | state, word)`, and does it mutate? Pick one, write it
in the read grammar, and the two implementations can be reconciled in an afternoon.

## G1, now with the source: 11 of 22 abstention probes disagree

The frozen set is `{"RESIGN","RESIGNS","RESIGNED","GIVEUP","SURRENDER","IQUIT","QUIT","FORFEIT"}`,
matched by `"".join(tok.split()).upper()` — exact, whitespace-insensitive, punctuation not stripped.

```
token          frozen   mine
'RESIGNED'     True     False    <-- DISAGREE
'GIVE UP.'     False    True     <-- DISAGREE
'I GIVE UP'    False    True     <-- DISAGREE
'I give up.'   False    True     <-- DISAGREE
'SURRENDER'    True     False    <-- DISAGREE
'IQUIT'        True     False    <-- DISAGREE
'QUIT'         True     False    <-- DISAGREE
'FORFEIT'      True     False    <-- DISAGREE
'I quit'       True     False    <-- DISAGREE
'ABSTAIN'      False    True     <-- DISAGREE
'NO MOVE'      False    True     <-- DISAGREE
'DEAD END'     False    True     <-- DISAGREE
'STUCK'        False    True     <-- DISAGREE
'UNSOLVABLE'   False    True     <-- DISAGREE
```

**Only three tokens are common: `RESIGN`, `RESIGNS`, `GIVEUP`.** Every other word a model might use to
say "I cannot finish this" is an abstention in exactly one of the two implementations and a
`not_an_action` in the other.

**A model that writes `STUCK` scores `give_up` on my instrument and `not_an_action` on yours, from
identical bytes.** Neither file would tell a reader why. That is G1 stated as a measurement rather
than an opinion, and it is why G1 is the one to settle first.

## G9 — THE FROZEN INSTRUMENT CAN LOSE THE PLAYER OFF THE EDGE OF ITS OWN BOARD

On an unenclosed level (levels are required to be enclosed by convention, nothing enforces it), the
frozen `step` checks only `ahead in st["walls"]`. Out-of-bounds is not a wall, so it is walkable:

```
level:                      frozen:                        mine:
#####                       step D -> moved  player=(2,1)   step D -> moved    player=(2,1)
#@$ #                       step D -> moved  player=(3,1)   step D -> moved    player=(3,1)
#  .#                       step D -> moved  player=(4,1)   step D -> BLOCKED  player=(3,1)
#  #        <- open bottom
                            final board:                    final board:
                            '#####\n# $ #\n#  .#\n#  # '    '#####\n# $ #\n#  .#\n#@ # '
```

The player is at **row 4 of a 4-row board**. `render()` iterates `range(st["rows"])`, so the player is
simply not drawn — **the game continues on a board that no longer contains the player.** Its next
moves are legal, counted, and scored.

I treat out-of-bounds as a wall and record `enclosed` as a measured level property. Neither behaviour
is in the contract.

## G6 — A LEVEL WITH TWO PLAYERS PARSES IN THE FROZEN INSTRUMENT

```
######           frozen: parsed, player=(1,3)     <- the LAST @ wins, silently
#@ @ #           mine  : MalformedLevel
#$.  #
######
```

Dossier §8 group [2] is titled "A MALFORMED LEVEL IS AN ERROR, NOT A BOARD". A two-player level is
malformed and is not detected. The measurement then runs against a board with one invisible player.

## G24 — THE TERMINATION VOCABULARIES DO NOT INTERSECT

```
frozen 'ended'    : {gave_up, solved, commands_exhausted}
mine   'terminal' : {SOLVED, GAVE_UP, NO_LEGAL_ACTION_PRODUCED, WALL_BUMPED_ONLY,
                     BUDGET_EXHAUSTED, UNSOLVED, NEVER_STARTED}
```

Zero shared tokens. A comparison tool keying on the termination string joins nothing, and both files
look complete.

## G25 — `step()` ON AN UNRESOLVED LETTER: `blocked`, OR RAISE?

```
frozen step(st, 'X') -> 'blocked'
mine   step(st, 'X') -> raises ValueError
```

The frozen `step` is total: anything not in `ACTIONS` returns `blocked`, so a caller that forgets to
run the reader gets a quiet, plausible counter instead of a crash. Mine refuses, on the grounds that
`blocked` means "a legal letter aimed at a wall or crate" (§2) and `X` is neither — folding it into
`blocked` inflates a real counter with a programming error.

**Both defensible. The contract does not say.** And note the interaction with G23: if `step` is the
thing that decides, then whether the reader or the transition function owns `not_an_action` is decided
by whoever calls first.

---

## WHAT THIS IS NOT

Not a bug report about your tree, and not a claim that my reading is right. It is the list the
*derivation* produced — which is the point: **the ambiguities are the finding.** A port would have
inherited your answers silently and taught nothing.

**Settle G1 first.** It is the only counter that can see the faculty, and right now it cannot see
anything. Then G15 — without a defined score this cabinet cannot produce the milestone dossier §12
names ("one cabinet producing a number that ranks two models differently"), because the number is
still being chosen.
