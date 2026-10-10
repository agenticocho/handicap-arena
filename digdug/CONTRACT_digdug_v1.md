# CONTRACT_digdug_v1.md — the frozen contract of the DIG DUG cabinet

```
contract_version: digdug_v1
event: DIG DUG
tier: 3 (the open questions ARE the content)
harness: handicap-arena
frozen: BEFORE any entrant ran, by `python3 digdug_run.py freeze`, and the
        runner REFUSES to hand a prompt to any entrant until
        CONTRACT_frozen.json exists and every digest in it matches the file on
        disk.  That is a gate (exit 6), not a caption.
codes: digdug.py (rules) / digdug_reader.py (the answer grammar) /
       digdug_solve.py (the proofs and the per-ply diagnostics) /
       digdug_run.py (the runner, the scorer, the records)
```

This document is the only place a rule of this cabinet is stated. The code
implements it; the record replays it. Where this document and the code disagree,
the CODE IS THE BUG and the disagreement is a finding to file, not a detail to
smooth over.

---

## 1. THE SOURCE PARAGRAPH — the whole of the prose

Everything below is either a restatement of this paragraph or a declared
decision about something it does not settle. The paragraph is the entirety of the
specification the brief supplies for this game, so §4 exists.

> **DIG DUG (tier 3).** A 2D grid. The player digs through soil, leaving open
> tunnels; a target is collected by moving into its cell; the level is solved
> when all targets are collected. A hazard that is not sealed behind rock can
> arrive through the tunnels. The state is the board, the dug set and the hazard
> positions. Ground the player digs becomes permanent terrain.

Six sentences. Five facts about the world and one about the state vector. What
it does not say is the content of this cabinet.

---

## 2. SECTION A — the answer grammar (the ONLY place the answer shape lives)

**R3, applied:** one answer per turn, and only the grammar states the shape. No
other file in this cabinet may declare what an answer looks like.

- **A1 — the line rule.** An answer is the single non-empty line of what the
  entrant produced. `""` → `not_an_action` (`A1.empty_answer`). `None` (the
  entrant produced nothing) → `not_an_action` (`A1.none_answer`). Two or more
  non-empty lines → `not_an_action` (`A1.multi_line`); the reader does not
  choose one of them, because choosing is scoring.
- **A2 — abstention.** The normalised line is matched EXACTLY against the
  frozen token list below. Normalisation is casefold + outer strip + internal
  whitespace collapsed to single spaces. Punctuation is NOT stripped.
  Match → `give_up`, and the attempt ends there.
- **A3 — the alphabet.** `U`, `D`, `L`, `R`, `.`. Case-insensitive. `.` is
  WAIT [D-STOP]. Anything else that is a single character →
  `not_an_action` (`A4.single_char_not_in_alphabet`).
- **A4 — WASD is NOT a synonym.** `W`/`A`/`S` are `not_an_action`
  (`A4.wasd_not_a_synonym`). This is a decision with a reason: `D` is already
  DOWN, so a synonym table would silently move a letter, and the whole point of
  `D` here is that it is the direction of digging, not of "right". A reading in
  which WASD works changes the GAME while changing no counter.
- **A5 — nothing is ever truncated.** Two or more characters that are not an
  abstention token → `not_an_action` (`A5.multi_char_never_truncated`). `"RR"`
  is not two actions and is not `"R"`. `"GIVE UP"` is not `"G"`.

The frozen abstention vocabulary is the circuit's. A duplicate paired with a
deletion is caught as a MULTISET comparison, not a length check [B3].

```
give_up_tokens:
GIVE UP
GIVEUP
GIVE UP.
GIVE-UP
GIVE_UP
GIVING UP
I GIVE UP
I GIVE UP.
RESIGN
RESIGN.
RESIGNS
ABSTAIN
ABSTAIN.
NO MOVE
NO_MOVE
NO-MOVE
UNSOLVABLE
DEAD END
STUCK
```

A substring test for "looks like an abstention" exists in the reader as
`loose_give_up_diagnostic`. It is a DIAGNOSTIC. It is never scored, never folded
into `give_up`, and its volume is reported in every bundle under
`loose_give_up_unscored` so the loss the strict rule incurs stays visible
instead of living in two files as an argument. [R1]

Outcomes are split by ownership, because the paragraph names six game facts and
no vocabulary [D-WORDS]:

| who produces it | values |
|---|---|
| the reader (`A1`–`A5`) | `action`, `give_up`, `not_an_action` |
| the transition function `step()` | `moved`, `dug`, `collected`, `waited`, `blocked` |
| hazard resolution (not `step()`) | `armed`, `killed`, `unharmed` |

`step(state, action) -> ((row, col), word)`. It mutates, it raises on an action
outside the alphabet, and **it checks its own bounds** [B2]. `enclosed` is a
MEASURED per-level property in the bundle, not an assumption in a level file.

---

## 3. THE FROZEN CLAUSES

`FROZEN = Policy()` in `digdug.py`. Every field is a clause §4 decides. A shadow
reading is a different `Policy`, never a mutated global.

| clause | frozen value | rejected reading | decided by |
|---|---|---|---|
| `hazard_clock` | `per_player_turn` | `every_2_player_turns`, `never` | [D-CLOCK] |
| `hazard_terrain` | `tunnels_only` | `soil_too` | [D-T0] |
| `hazard_tiebreak` | `reading_order` | `reverse_reading_order` | [D-TIEBREAK] |
| `player_into_hazard` | `blocked` | `killed`, `pass_through` | [D-BLOCK] |
| `resolve_order` | `player_first` | `simultaneous` | [D-ADJ] |
| `end_on_solve_first` | `True` | `False` (+ `death_beats_solve`) | [D-END] |
| `wait_legal` | `True` | `False` | [D-STOP] |
| `objective` | `all_targets` | `survive_n` | [D-OBJ] |
| `target_persistence` | `removed` | `persists_as_marker` | [D-TARGET] |
| `bounds` | `blocked` | `raises` | [D-BOUNDS] |
| `wrap` | `False` | `True` | [D-WRAP] |
| `hazard_blocks_hazard` | `True` | `False` | [D-HAZCOLL] |
| blocked-but-legal letter | costs the turn, advances the clock | costs nothing | [D-BLOCKED-TURN] |
| the state key of the proof | `(player, tunnels, targets, hazards)`, no clock | — | see §5 |

---

## 4. THE UNDER-SPECIFIED CLAUSES — 7 bullets, each with what it costs

The brief's list, in its order. Each is marked here, argued in
`DIGDUG_DECISIONS.md`, carried into every bundle as `contract.clauses_frozen_for_this_run`
plus `contract.decisions_index`, and MEASURED under the rejected reading in
`digdug_readings.py`. "Marked" is not a synonym for "resolved": a mark is what
makes a decision visible after the fact.

1. **`[UNDER-SPECIFIED: hazard motion]`** — the paragraph says a hazard "can
   arrive", never when it moves, how fast, or on whose turn. Frozen:
   one cell per consumed turn, after the player, and only if the move brings it
   strictly closer [D-CLOCK]. Cost: this clause alone decides whether a run is a
   puzzle or a countdown.
2. **`[UNDER-SPECIFIED: hazard route]`** — "not sealed behind rock" is not a
   definition of the ground a hazard walks on. Frozen: a hazard's road is the
   dug set and nothing else, so at time zero NOTHING moves [D-T0]. Cost: under
   `soil_too` level 03 and level 05 are **proven lost** instead of won — the
   reading in which a hazard tunnels through undisturbed earth turns two
   winnable items into two losses. Measured, in `SECTION_4F.md` item 3.
3. **`[UNDER-SPECIFIED: "solved"]`** — the paragraph defines collection and
   then says the level is solved "when all targets are collected", which is a
   conjunction with no deadline and no interaction with dying. Frozen: `solved`
   ends the run BEFORE hazard resolution moves anything [D-END]. Cost: it
   decides level 01 and level 05, and on level 01 it decides whether the FLOOR of
   the scale is playable at all.
4. **`[UNDER-SPECIFIED: standing still]`** — nothing in the paragraph says the
   player must move, and nothing says a hazard may not arrive while the player
   waits. Frozen: `.` is a legal action that CONSUMES a turn [D-STOP]. Cost:
   `waiter` dies on level 04 by doing nothing, which is the proof that WAIT is
   not a pause in the clock; and no optimal plan in this item set contains `.`,
   which is the measurement that says the choice was not forced the other way.
5. **`[UNDER-SPECIFIED: adjacency to a hazard]`** — can the player step onto a
   hazard's cell? Frozen: the cell is a living wall, the letter is legal, and it
   BLOCKS [D-BLOCK]. Cost: a blocked letter is a `word` in the record, so this
   clause is visible per ply rather than inferred from a loss.
6. **`[UNDER-SPECIFIED: two hazards, one cell]`** — the paragraph permits more
   than one hazard and never says what happens when two want the same cell.
   Frozen: the first in reading order takes it [D-TIEBREAK], and the search is
   deterministic without a seed because of it [§5].
7. **`[UNDER-SPECIFIED: ground that returns]`** — "permanent terrain" says
   tunnels do not close; it says nothing about the target's cell, the frame, or
   whether an open tunnel is a resource. Frozen: `removed` on collect, a rock
   frame with no wrap, and a monotone traversable set [D-TARGET][D-WRAP][D-BOUNDS].
   Cost: this is the clause that makes FACET 1 *not* be "the map gets smaller",
   and `SECTION_4F.md` item 1 records the proof that it never does — control
   [M1] asserts the player's reachable set NEVER shrinks, over every reachable
   state of every level, to depth 12.

---

## 5. WHY THE STATE KEY IS ENOUGH, AND WHY A SEED IS NOT NEEDED

`snapshot() = (player, frozenset(tunnels), frozenset(targets_left),
frozenset(hazard positions))`. No clock field, because:

- `hazard_clock = per_player_turn` and `resolve_order = player_first` make the
  hazard's move a FUNCTION of the consumed-turn count, which is the length of the
  stream — so the count is recoverable and adds nothing;
- the tunnel set is monotone (a ply adds a cell or changes nothing), so
  cycles in the state graph require the player to move, not the world to change;
- every hazard decision is a total order (reading order, row-major), so
  determinism needs no PRNG and `seed` does not appear in this contract. If a
  future clause ever consults a RNG, `refuse()` in `digdug_solve.py` raises
  rather than producing a number that looks like a proof over a state key that is
  no longer complete.

Under `hazard_clock = every_2_player_turns` the key is still complete (the
parity is a function of `consumed`), but under `every_2_turns_of_any_actor` or a
randomised tie-break it is NOT, and the solver refuses. That asymmetry is why
the clause is in §3 and not in a comment.

---

## 6. THE SCORING RULES, APPLIED HERE

- **R1** — the abstention list above is frozen and equals the code's scored
  list; `digdug.py --self-test` [0] checks it as a multiset; `loose_give_up` is
  a diagnostic and never scored. Every `rule` the reader emits is one of
  `Reading.RULES`, and the bundle carries `rules_fired` ⊆ `rules_declared`.
- **R2** — `solved` IS the score: `score = levels solved / levels on which an
  answer was EMITTED`. `moves` is a COST, carried per item and in `totals`,
  never averaged into anything. Both `attempted_emitted` and
  `attempted_consumed` are in the record. Where an item has several optimal
  lines the count is in the item set (`distinct_shortest_plans`), and it is a
  solver output, not a claim: 01 → 1, 02 → 1, 03 → 4, 04 → **0** (proven lost),
  05 → 1.
- **R3** — one answer per turn. The grammar states the shape. The reading in
  which the model emits the whole plan (a provably optimal `URLDDRR` for 02) is
  a reading under which the correct answer is a failure: this cabinet therefore
  REJECTED it and shipped `plan-emitter` as a code entrant so the sentence is a
  measurement in the record, not an argument in a document.
- **B1** — emitted and consumed are different numbers and both are recorded.
  `wall-bumper` is the exhibit: 10 emitted, 0 consumed on 04, and the score
  denominator uses the first.
- **B2** — bounds are checked IN `step()`, and the record reports the result as
  `enclosed_measured` per level. No workaround lives in the reader or the
  runner.
- **B3** — validation is UNIQUENESS, not count: two players, no player, two
  hazards sharing a cell, a pearl on a tunnel, a board whose rows differ in
  length, a level with no hazard, a 1-wide corridor — all refused as
  `MalformedLevel`, and `--self-test` [2] drives each one.
- **§6 of the brief** — the record is written BEFORE the verdict branch
  (`write_bundle` is called before the exit code is chosen); a failed load names
  the HOLDER via a `/proc` socket-inode probe or says which probe found nobody;
  a model's DIGEST is recorded or the reason there is none; the bundle records
  WHICH CODE produced the verdict, with digests; the exit code comes from the
  run; and one declared reasoning setting and GPU apply per event.

---

## 7. THE ITEM SET

Five levels, every optimum produced by `digdug_solve.verify_level` BEFORE any
entrant ran, and re-proved by `digdug_run.py levels` and by the instrument check.
`tasks/digdug_v1.json` is written from the solver, never by hand.

| file | what it is | proven |
|---|---|---|
| `01_first_dig.txt` | the FLOOR: one pearl, one hazard one cell away, one letter of a solution. Also the exhibit that [D-END] is load-bearing. | winnable, optimum **1**, **1** optimal line, exhaustive (2 states) |
| `02_the_shortcut.txt` | the race: the direct line digs into the hazard's road and dies on ply 4; the optimum goes around and takes 7. | winnable, optimum **7**, **1** optimal line, exhaustive (54 states) |
| `03_ground_you_cannot_reuse.txt` | the cavern with four optimal lines and a rock lattice that makes a committed static plan choose badly. | winnable, optimum **7**, **4** optimal lines, exhaustive (152 states) |
| `04_the_only_door.txt` | the pearl behind a single door with a hazard standing in it. The ONLY correct answer is an abstention. | **PROVEN LOST**, exhaustive (4 states), 0 optimal lines |
| `05_the_photo_finish.txt` | the level [D-END] decides: the last pearl is collected on the ply a hazard would have stepped onto the player. | winnable, optimum **4**, **1** optimal line, exhaustive (11 states) |

These are the numbers as measured on the frozen reading. `bounds` is `blocked`,
`wrap` is off, and every level is rock-framed because [D-WRAP] and [D-BOUNDS]
say so, so enclosure is a theorem and `enclosed_measured` is True for all five —
checked, not written.

---

## 8. EXIT CODES

```
exit_codes:
0  SCORED               measured > 0 and the harness is sound
1  INSTRUMENT NOT PROVEN self-test / instrument-check / level-verification
                         failure. NO ENTRANT RUN MAY EMIT IT: control [X] proves
                         that by driving every entrant and checking the codes.
2  ZERO MEASURED         a run with nothing readable is an ERROR, never a
                         verdict
3  USAGE                 unknown entrant, bad arguments
4  NEVER_STARTED          the entrant never loaded -- counted separately from
                         played-and-failed, because they are different claims
5  RECORD NOT WRITTEN     a run with no record is not a run
6  CONTRACT NOT FROZEN    no entrant plays against a contract that is not frozen
                         against disk
```

`run-all` returns 0 unless a record failed to write. It does not return "0 if
solved else 1": an entrant scoring zero is a RESULT, and mixing the two would
make a model's failure look like a broken harness.
