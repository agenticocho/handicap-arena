# THE DIG DUG CONTRACT — frozen

**Cabinet:** `digdug/` · **Event:** DIG DUG · **Format:** A (the model is the player)
**Written:** 2026-10-10 · **Frozen by:** `digdug/freeze.py` → `digdug/FROZEN.json`
**Status:** this file is the whole specification. It was written **before any entrant ran**, and
`digdug_run.py` refuses to run an entrant unless `freeze.verify()` passes on this file's digest.

Every clause the prose did not settle is marked `[U<n>]` (the brief named the gap) or `[A<n>]`
(the prose was silent and the brief did not raise it either). Each one records **the reading
chosen** and **the reading rejected**. A defaulted setting is still a setting; there are no
defaults here, only decisions, and every one is in the register in section 6.

---

## 1. THE PROSE — the whole text this was built from, verbatim

> A grid of soil. The player moves one cell at a time, orthogonally into soil or into an
> already-dug tunnel. Moving into soil digs it. Moving into a wall is blocked. There is at least
> one target to collect and at least one hazard. A target is collected by moving into its cell.
> Underground, a hazard cannot reach the player except through tunnels, so the tunnels the player
> digs are also the routes by which a hazard can arrive. Digging is permanent — dug ground never
> returns to soil.

That is all of it. It is 91 words. It describes a grid, a move, a dig, a block, a target, a
hazard, and a permanence rule. **It does not contain a clock, an objective, a death rule, an
answer format, a turn order, or a boundary.**

### What the prose does settle

| the prose settles | the clause |
|---|---|
| the player moves one cell, orthogonally | "moves one cell at a time, orthogonally" |
| soil and already-dug tunnel are both enterable | "into soil or into an already-dug tunnel" |
| entering soil digs it | "Moving into soil digs it" |
| entering a wall does nothing | "Moving into a wall is blocked" |
| at least one target and at least one hazard exist | "at least one target … at least one hazard" |
| a target is collected by entering its cell | "collected by moving into its cell" |
| a hazard travels only through tunnels | "cannot reach the player except through tunnels" |
| digging is permanent | "dug ground never returns to soil" |

### What it does not — and this contract therefore decides

The hazard's clock. What exists at time zero. Whether a collected target is removed. Whether the
objective is a count or a set of positions. What adjacency does. Whose move resolves first.
Whether the player may stop. What "solved" means. Whether the grid wraps. Whether a hazard digs.
Whether hazards block each other. What an **answer** even looks like. All of it is in section 6.

---

## 2. THE READ GRAMMAR — the answer shape (standing rule R3)

The prose contains no answer format at all. Standing rule R3 says only the read grammar states the
ANSWER SHAPE, so this section is the only place it is stated, and `digdug/digdug_reader.py` is the
only code that implements it.

**One answer per turn. One token. One line.**

| the answer | reading | rule that fires (recorded on every ply) |
|---|---|---|
| `U` `D` `L` `R`, either case, surrounding whitespace allowed | an action | `action_letter` |
| exactly one token from the frozen list below | an abstention — **the attempt ends** | `give_up_token_exact` |
| `W` `A` `S` `D` | `not_an_action` — WASD are **not** synonyms | `wasd_not_a_synonym` |
| `WAIT`, `STAY`, `HOLD`, `PASS`, `.` | `not_an_action` — **there is no pass action** `[U5]` | `wait_is_not_an_action` |
| two or more non-empty lines | `not_an_action` — a plan is not an answer, and no line is preferred | `multi_line` |
| more than one character | `not_an_action` — **never truncated**; `RR` is not `R`, `RESIGN` is not `R` | `multi_char_no_truncation` |
| one other character | `not_an_action` | `single_char_not_an_action` |
| nothing / whitespace only | `not_an_action` | `empty_answer` |
| no answer at all | `not_an_action` | `none_answer` |

`outcome ∈ {action, give_up, not_an_action}`. `give_up` and `not_an_action` never reach the
transition function: they are resolved here, before an action exists.

### 2.1 The frozen abstention list (standing rule R1)

Matching is **exact** against the casefolded, whitespace-collapsed line. Punctuation is **not**
stripped, except where the punctuated form is itself listed: `GIVE UP.` is in the list,
`GIVE UP!` is not and reads as `not_an_action`. Failing closed on the abstention counter is a
direction; it is recorded, and the loose substring test is carried in the record as
`loose_give_up_diagnostic` and **never scored, never in a denominator, never in a verdict**.

The list is the **union** of the two lists the two Sokoban cabinets froze for themselves — those
two agreed on 3 of 22 abstention-shaped probes — plus four words a model uses for a level with no
safe line. `freeze.py --write-tokens` regenerates this block from the code, and the runner
compares the block to the code's scored list before it will run: **the grammar's list and the
code's list are one list, checked, not one list written down twice.**

<!-- ABSTENTION-TOKENS:START -->
# generated from digdug_reader.GIVE_UP_TOKENS by freeze.py
# --write-tokens.  Do not edit by hand: the runner compares
# this block to the code's scored list (standing rule R1).
`RESIGN`
`RESIGNS`
`RESIGNED`
`GIVEUP`
`SURRENDER`
`IQUIT`
`QUIT`
`FORFEIT`
`GIVE UP`
`GIVE UP.`
`GIVE-UP`
`GIVE_UP`
`GIVING UP`
`I GIVE UP`
`I GIVE UP.`
`ABSTAIN`
`ABSTAIN.`
`NO MOVE`
`NO_MOVE`
`NO-MOVE`
`UNSOLVABLE`
`DEAD END`
`STUCK`
`IMPOSSIBLE`
`NO SAFE LINE`
`CANNOT SOLVE`
`CANNOT SOLVE.`
`CAN NOT SOLVE`
`I STOP`
`STOP`
`STOP.`
<!-- ABSTENTION-TOKENS:END -->

### 2.2 What the entrant is shown

The legend in prose, the level name, the targets left, the turn number and the turn cap, the
board, the move history so far, the answer shape, and the frozen token list. It is **not** shown
`min_moves_to_complete`, the hazard's intended move, or whether a safe line still exists. Those
are the instrument's diagnostics; showing them would measure the instrument's advice instead of
the entrant's planning. The prompt is prose — no schema, no JSON, no key-value framing — and
`check_prompt_legal()` is a control, not a comment.

---

## 3. THE TRANSITION FUNCTION — `step()`, frozen

```
step(state, action) -> (new_state, word)
```

**TWO values. Not three.**

* `new_state` is a **NEW** `State`. `step()` **never mutates** the state it was given `[A2]`.
  Purity is pinned because the second Sokoban cabinet found it unpinned and the two
  implementations split on it — one returned a state and was pure, the other returned a
  coordinate and mutated in place. Both satisfied the words. A wrong *type* produces a plausible
  wrong number for a whole run; a wrong arity at least raises on the first call.
* `word ∈ {dug, moved, blocked, collected}`.
* **Bounds are checked HERE** `[B2]` `[U9]`. Out of bounds is `blocked` — never an exception, and
  never a walk off the edge of the board.
* An action outside `{U,D,L,R}` **raises** `ValueError` `[A6]`. It is never folded into `blocked`,
  because `blocked` counts a legal letter aimed at rock and a programming error must not inflate a
  real counter.
* The player's move does **not** advance the turn counter. `turn()` does.

**Word precedence** `[A7]`: a move that opens soil *and* collects a target says `collected`, and
the dig is still reported in `events`. Words are facts about the move, not ranks.

```
turn(state, action) -> (new_state, word, events)      word may also be "killed"
```

The turn resolves in this order, and the order is the contract:

1. **the player's move** — `step()`.
2. **collection** — a target in the entered cell is collected and **removed** `[U3]`. Collecting
   the **last** target ends the attempt **before the hazard clock ticks** `[U6]` `[U7]`.
3. **the hazard clock** — one tick, **every** hazard, **simultaneously** from a single pre-move
   snapshot `[U1]` `[U8]`.
4. **the death check** — a hazard in the player's cell kills `[U4]`.

A **blocked** move still costs the turn and still ticks the clock `[A8]`.

**The counters come from the state change, not from the word** `[A17]`. `dug + moved + blocked`
partitions the action answers exactly, and `collected` counts a subset of them. The first build of
this cabinet counted the word instead: a move that killed the player reported `killed`, so the cell
it dug on the way in never reached `dug` and the wall it bumped never reached `blocked` — while the
board inside the same record showed both. A second implementation found it, on 11 of 44 pairs.

### 3.1 The hazard policy — `[U1]`, and it is load-bearing

One cell per player turn, **through tunnels only**, along a **shortest path** to the player's
current cell, ties broken by the fixed direction order `U, D, L, R`. **Hazards never dig**
`[A1]` — a hazard in sealed soil waits there until the player opens a way in, which is the whole
reason the tunnels the player digs are also the routes by which a hazard can arrive. Hazards may
share a cell with each other and do not block each other `[A10]`.

Rejected, with reasons, in section 6. Without a frozen policy the words "the hazard arrives" have
no referent, and two cabinets would report different deaths on identical answers.

### 3.2 The board

```
#  rock        impassable, undiggable, forever
%  soil        impassable until dug; digging it opens it permanently
   tunnel      already open at t=0
P  the player  its cell is a TUNNEL at t=0                 [U2]
H  a hazard    its cell is a TUNNEL at t=0                 [U2]
T  a target buried in soil        *  a target in an open tunnel
X  the player and a hazard in one cell — the last frame of a dead run
```

Malformed, and an **error, never a board** `[A3]`: empty text; a character outside the seven
glyphs; not exactly one player; zero targets `[U3]`; zero hazards `[U3]`; fewer than 3 rows or 3
columns; a player with no playable neighbour. Ragged rows are **padded with rock**, not soil, and
the fact is recorded on the level `[A4]`. Enclosure — every border cell rock — is **MEASURED**,
recorded per level, and the runner refuses to score a level that measures `false` `[B2]`.

---

## 4. WHAT "SOLVED" MEANS — `[U6]`

**Solved = every target collected, and the player alive on the turn it collected the last one.**

Rejected: *reach a designated cell* (the prose names no exit and has no glyph for one — inventing
one adds a mechanic the paragraph does not contain); *survive N turns* (that rewards an entrant
that never moves, and `N` would be a second undeclared parameter); *collect a designated target*
(the prose says "at least one target", so which one?).

The objective is the **COUNT**, not the positions `[U3]`: targets are fixed at parse time, they do
not move, and a collected target is **removed** from the board while its cell stays a tunnel.
Rejected: a target that persists after collection — under that reading the board cannot tell an
entrant what is left, and the render is a lie.

---

## 5. THE TWO FACETS — one run, one trace (standing demand D)

Both are computed by `digdug.facets_from_trace(level, trace, budget)` from **one list object** —
the trace of the run — and both results are stamped with that list's digest, so a reader can check
the claim rather than take it. A second event is not a second facet; there is no second event here.

### FACET 1 — search under destruction. *"Did the plan consume the ground it needed?"*

| number | what it is | provable? |
|---|---|---|
| `barrier_lost_at_turn` (1a) | the first turn at which the player's own digging put it in the **same connected tunnel component** as a hazard. Digging is permanent, so once true it is true forever: the soil that was keeping the hazard out is gone for the rest of the run. | yes — connectivity on the recorded map, monotone by construction |
| `budget_ruin_at_turn` (1b) | the first turn at which the shortest possible completion is longer than the turns left. Moving into soil costs exactly one move, the same as moving through a tunnel, and digging never blocks, so on a single-target level this is the **exact** rock-free distance to the target `[A9]`. | yes — exact, not a heuristic, and it needs no hazard at all |

1a and 1b are different failures. **1b needs no hazard.** An entrant that wanders, digging a
corridor that leads nowhere, loses the level without ever meeting anything.

### FACET 2 — hazard-aware planning. *"Did the route it dug open a path for the hazard that killed it?"*

Read off the death record on the same trace: `died_at_turn`, the killing hazard's `kill_path`,
`kill_path_cells_dug_by_player`, `kill_path_cells_pre_existing`,
`first_kill_cell_dug_at_turn`, `dig_to_death_turns`. A death through a corridor that was open at
`t=0` is recorded as such — that is a level defect, not an entrant failure, and the numbers say
which it was.

### What the running proved about the two facets

Under this prose the two facets are **not independent mechanics, and they cannot be**: digging
never removes a route (soil costs one move either way and dug ground stays open), so the *only*
destructive resource in the game is the soil barrier between the player and a hazard. Facet 2 is
therefore a **strict subset** of facet 1 — a death requires the components to have merged — while
1b is the one destructive failure that needs no hazard. `digdug.destruction_reachability_proof()`
walks every reachable state of every level to establish the first claim, and it is a control in
the self-test. See `DIGDUG_PROSE_TRAPS.md` §F4.

---

## 6. THE DECISION REGISTER

`[U<n>]` = the prose is silent and the brief named the gap. `[A<n>]` = the prose is silent and the
brief did not raise it either. Every row: the reading chosen, the reading rejected, and what turns
on it.

### U — the seven the brief named, plus two in the same family

**`[U1]` Does a hazard move per player turn, or on its own clock?**
**CHOSEN:** one cell per player turn, in lockstep, along a shortest tunnel path, ties by
`U,D,L,R`. **REJECTED:** an own clock at rate 1:2 — under it, whether the hazard arrives on a
given corridor depends on the parity of the turn the player opened it, and nothing in the record
would say which parity the run used. Also rejected: a random walk (unreproducible, so a bundle
could not be replayed and the cabinet could not certify) and one-step greedy (a greedy hazard
oscillates in a straight corridor and never arrives). **Turns on it:** every death in the cabinet.

**`[U2]` Does a hazard's route exist before any tunnel does — and what happens at time zero?**
**CHOSEN:** the player's cell and every hazard's cell are **tunnels at t=0**; everything else is
soil. So at t=0 a hazard's route exists only if its own tunnel cells already connect to the
player's, and a level where they do is flagged `hazard_reachable_at_start`. **REJECTED:** a
literal reading of "a grid of soil" that puts the hazards *in soil* — under it a hazard can never
move at all, because it may only travel through tunnels and it has none, so the entire faculty is
unmeasurable and the hazard is decoration. **Turns on it:** whether the hazards can move.

**`[U3]` Is a collected target removed, and is the objective the count or the positions?**
**CHOSEN:** removed from the board (its cell stays a tunnel), objective = **the count** — all
targets collected. A level with zero targets or zero hazards is **malformed**, because the prose
requires at least one of each. **REJECTED:** a target that persists (the board then cannot show
what is left), and an objective over positions (positions are fixed, so a positional objective is
the same test with more failure modes).

**`[U4]` What happens when the player and a hazard occupy adjacent cells — whose turn resolves
first?**
**CHOSEN:** adjacency is **nothing**. Only the **same cell** kills, and the order is pinned in
§3: player moves → collection → hazard clock → death check. So a player that moves *into* a
hazard's cell dies immediately, a hazard that moves *into* the player's cell kills, and a player that moves
**into a hazard's cell** dies even though that hazard never moves — the check runs after the
clock. A "swap-through", each ending in the other's cell, **cannot occur under this order**: the
hazard always targets the player's post-move cell, so if it steps into the player's old cell the
player has already left it. That clause was in the first draft of this contract; a control removed
it before any entrant ran. **REJECTED:**
"adjacent = death", which would make the prose's own sentence about tunnels redundant (a hazard
could kill through solid soil) and would turn the game into a distance test with no routes in it.

**`[U5]` May the player stop, and is stopping a turn?**
**CHOSEN:** there is **no pass action**. The only way to stop is to abstain, and an abstention
**ends the attempt**. **REJECTED:** a `WAIT` that costs a turn — under a lockstep clock a wait
changes nothing but the budget, it makes every level a stalling game whose only termination is the
cap, and it doubles the answer alphabet for a move that cannot help. `WAIT` therefore reads as
`not_an_action` under its own named rule, so the divergence is visible in the record.

**`[U6]` What does "solved" mean?**
**CHOSEN:** all targets collected, alive, on the collecting turn. **REJECTED:** a designated exit
cell, surviving N turns, collecting one designated target — see section 4.

**`[U7]` On the collecting turn, does the hazard clock still tick?**
**CHOSEN:** **no** — collection ends the attempt before the clock. **REJECTED:** the full turn
resolving, which would kill a player that collects the last target next to a hazard and would
force every optimal line to include a wasted escape move. This is the sharpest edge in the
contract: on level 02 it is the difference between a 12-move solve and no solve at all.

**`[U8]` Do multiple hazards move in index order, or together?**
**CHOSEN:** together, from one pre-move snapshot. **REJECTED:** sequential in index order, under
which the order the hazards happen to be written in the level file decides who takes a contested
cell — two files with the same board are then different games.

**`[U9]` Does the grid wrap, and is unbounded movement blocked or an error?**
**CHOSEN:** bounded, **no wrap**; out of bounds is `blocked`, checked in the transition function.
Enclosure is measured per level and an unenclosed level is refused by the runner, but the bounds
check stays in `step()` because that is where it belongs. **REJECTED:** a torus — under it
"underground" stops meaning anything and a hazard can arrive from behind the player through a
border nobody drew; and raising on out-of-bounds, which would turn an entrant's ordinary move
into a harness crash.

### A — the ones the prose did not raise and neither did the brief

**`[A1]` Hazards never dig.** Follows from "cannot reach the player except through tunnels", but
the prose never says it, and a hazard that digs makes that sentence false.

**`[A2]` `step()` is pure; the state it is given is never mutated.** The second Sokoban cabinet
found this unpinned and the two implementations split on it.

**`[A3]` What makes a level malformed.** Seven conditions, listed in §3.2. A malformed level is
an error, never a board: a board parsed out of a malformed level measures something else.

**`[A4]` Ragged rows are padded with rock, not soil** — padding with soil would invent diggable
ground outside the author's board.

**`[A5]` Level 04 is a CONTROL and is not scored.** It has no safe line (proven by exhaustive
search), so the only correct answer on it is an abstention; scoring it would punish a correct
answer, which standing rule R3 calls a disproof of the spec.

**`[A6]` `step()` raises on an unresolved letter** rather than folding it into `blocked`.

**`[A7]` Word precedence:** `collected` over `dug` over `moved`, with the full detail in `events`.

**`[A8]` A blocked move costs the turn** and ticks the clock. Otherwise a wall-bumper is immortal
and `blocked` stops being a cost.

**`[A9]` `min_moves_to_complete` is exact**, because a dig costs one move and never blocks. This
is what lets facet 1b say RUINED rather than PROBABLY RUINED.

**`[A10]` Hazards may share a cell and do not block each other.**

**`[A11]` The abstention token list is a UNION of the two Sokoban lists plus four**, exact
matched, with the loose test carried as an unscored diagnostic. See §2.1.

**`[A12]` The answer shape is one token per turn.** The prose contains no answer format at all.

**`[A13]` The prompt states the answer shape and the frozen token list, and never shows the
instrument's diagnostics.**

**`[A14]` The turn budget is 30 per level.** An instrument parameter, declared here and written
into every bundle. 30 is 2.5×–7.5× the proven optima; it is not a discovery, and two runs with
different budgets are not comparable — `attempted`, `blocked` and facet 1b all move with it.

**`[A15]` The gate is `solved / attempted_emitted` (standing rule R2)**, where
`attempted_emitted` is **levels on which the entrant emitted at least one answer**. `moves` is a
**cost**, carried per level and in totals, and never averaged. The alternative reading of R2 —
`solved / answers_emitted` — is also recorded, per entrant, and the report says whether the two
rank the field differently. **`[B1]`** `answers_emitted` and `answers_consumed` are different
numbers and both are in the record; tokens emitted after the attempt ended are counted in
`answers_after_end` and are **not** folded into `not_an_action`.

**`[A17]` The counters come from the state change, not from the word** — see section 3.

**`[A16]` The score does not compare an answer stream to a reference plan.** The solver's plan is
recorded as a fact about the level and is never used to judge an entrant. Level 02's optimum is a
fact; "the plan" is not.

---

## 7. THE LEVELS

| file | role | targets | hazards | optimum | distinct optimal lines |
|---|---|---|---|---|---|
| `levels/01_first_blood.txt` | scored — the floor of the scale | 1 | 1, sealed | 4 | 1 |
| `levels/02_the_long_way_round.txt` | scored — the short route meets the hazard head-on; a longer route lives | 1 | 1, in an open pocket | 12 | 1 |
| `levels/03_the_open_door.txt` | scored — the barrier is one dig wide, and the map has a ring | 1 | 1, sealed behind one cell | 7 | 1 |
| `levels/04_no_safe_line.txt` | **CONTROL — not scored.** No safe line exists (exhaustive proof). The only correct answer is an abstention `[A5]`. | 1 | 1 | **none** | 0 |

Every optimum is proved by exhaustive BFS over the whole state space by `digdug_solve.py` before
any entrant runs, with the number of **distinct** optimal lines counted, not just the length
(standing rules R2 and B3). A level whose search hits the state cap is reported INCOMPLETE and the
runner refuses to score it.

---

## 8. THE FREEZE

`freeze.py` writes `FROZEN.json`: the sha256 of this file, of every normative code file, of the
item set and of every level, plus a combined digest, the decision register, and the state of the
token lists. `digdug_run.py` calls `freeze.verify()` before it will run anything and exits **6
(NOT FROZEN)** if the tree is not the frozen tree — including if a decision marker exists in the
code that this file does not record. "Frozen before any entrant ran" is therefore a precondition
of every bundle, not a sentence in a report.
