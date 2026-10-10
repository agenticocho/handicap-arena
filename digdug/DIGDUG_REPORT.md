# DIGDUG_REPORT.md — the DIG DUG cabinet: what was built, what ran, what it measured

Cabinet: **DIG DUG** (`digdug_v1`), tier 3 of the handicap-arena circuit — the
tier whose content is the questions the source paragraph leaves open.
Branch `arena/e5bd42b9-handicap-arena`. Everything below was produced on this
box: Python 3.11.2, 2 CPUs, no accelerator, no model weights, no server.
Stdlib only, no dependencies added.

---

## 1. THE FILES, AND WHAT EACH ONE IS FOR

| file | lines | role |
|---|---|---|
| `digdug.py` | 1821 | **the rules.** `parse_level` (validator), `State`, `step`, `resolve_turn`, `advance_hazards`, `feed`, `terminal_reason`, `summarise`, `build_prompt`, `Policy`+`FROZEN`, `DECISIONS`, `self_test` (68 controls, groups [0][R1-X][1][2][3][4][W3][5][6][7][8]) |
| `digdug_reader.py` | 361 | **the one reader of record.** The answer grammar, the frozen 19-token abstention list, `Reading.RULES`, `grammar_as_record()`, `parse_give_up_tokens_from_contract()` |
| `digdug_solve.py` | 675 | **the proofs.** `graph()` (full reachable set, win states as leaves), `verify_level`, `certain_no`, `count_shortest_plans`, `Diagnostics.row()` (both facets per ply), `[M1]`/`[M2]` monotonicity checks, `refuse()` |
| `digdug_run.py` | 2225 | **the runner, the scorer, the freeze gate, the record.** 13 entrants, 7 exit codes, `instrument_check`, `facet_rows`, holder and GPU probes |
| `digdug_readings.py` | 482 | **the shadow table** — 16 readings × 5 levels, and 4 clause probes. Part of the instrument: the check refuses to pass without it |
| `test_digdug.py` | 363 | **the replay.** Rebuilds every item from its recorded raws through `feed`, per ply, and re-derives R1/R2/B1/B2/B3/§6 from the record |
| `CONTRACT_digdug_v1.md` | 289 | the frozen contract: the paragraph, section A (the only place the answer shape lives), the 14 clauses, the 7 `[UNDER-SPECIFIED]` marks, the exit-code table |
| `DIGDUG_DECISIONS.md` / `SECTION_4F.md` | 144 / 208 | the arguments, and the two facets with their numbers |
| `levels/*.txt` | 5 files | the item set, 3–6 rows each |
| `tasks/digdug_v1.json` | 113 | the item set **written by the solver**, not by hand |
| `results/*.json` | 14 | 13 bundles + `shadow_readings.json` |

One reader, imported by the runner and the tests and never reimplemented. One
`resolve_turn`, shared by the game and the solver, so a verified optimum is a
statement about the game the entrant played rather than about a second
implementation of it.

## 2. THE FREEZE, AS A GATE

`CONTRACT_frozen.json`, written 2026-10-10T20:47:18Z, digests the contract, the
reader, the simulator, the solver, the runner, the readings module and all five
level files. `cmd_run` calls `freeze_state()` **before it builds a single
prompt**, and exits **6 (CONTRACT NOT FROZEN)** if any digest has drifted.

```
contract   2d5679d0064f   reader  6be849338e25   readings a0efae8dab4e
simulator  f77c2b142b07   solver  7445589976a0   runner  c507c7160070
levels     a896a90e 36dd8f0d 19c3bba3 5e40bfd3 ed5e9afb (01..05)
```

The gate was wrong once and the fix is in the file: the first version iterated
`manifest["files"]`, a key the writer never wrote, so the loop never ran, `ok`
stayed `True`, and the check passed having compared nothing. `[FZ]` in
`instrument_check` now asserts (a) that the gate compared all 11 artifacts, (b)
that a tampered digest is refused, (c) that a manifest with a hole in it is
refused, and (d) that a run driven against the tampered manifest exits 6. A gate
without a control that closes it is a caption.

## 3. THE ITEM SET — five levels, every number proved before the field ran

| level | what it is | proven (exhaustive in all five cases) |
|---|---|---|
| `01_first_dig.txt` | the floor: one pearl, one letter | win, **opt 1**, **1** line, 2 states |
| `02_the_shortcut.txt` | the direct line digs the hazard's road and dies on ply 4 | win, **opt 7**, **1** line, 54 states, plan `URLDDRR` |
| `03_ground_you_cannot_reuse.txt` | a rock lattice, four equal optima | win, **opt 7**, **4** lines, 152 states, plan `DRULUUR` |
| `04_the_only_door.txt` | three cells of pre-dug tunnel, a hazard standing in the only soil left | **PROVEN LOST**, 4 states, **0** lines |
| `05_the_photo_finish.txt` | the last pearl is collected on the ply a hazard would have stepped onto the player | win, **opt 4**, **1** line, 11 states, plan `URRR` |

`proof_grade = exhaustive` means the frontier emptied by itself: every reachable
state was expanded, nothing was dropped by a cap. It is the difference between
"this level cannot be won" and "my search gave up", and it is why 04 exists as a
three-cell cavern rather than as an open field — on open fields this cabinet
cannot prove anything, and says so (`bounded:K`, `unexpanded_states`, and
`certain_no()` returning `set()` instead of a verdict). R2's "say how many":
1 / 1 / 4 / **0** / 1.

## 4. THE FIELD — 12 code entrants, one declared setting (`reasoning=off`)

| entrant | what it is | score | won | moves | exit |
|---|---|---|---|---|---|
| `reference` | the oracle: a proven-optimal line, `GIVE UP` on the proven loss | 0.8 | 4 | 19 | 0 |
| `slack-maximiser` | wins, then maximises margin, then is short | 0.8 | 4 | 19 | 0 |
| `beeline` | re-plans every turn toward the nearest pearl, ignores hazards | 0.6 | 3 | 18 | 0 |
| `static-planner` | one committed route planned on the ply-0 map | 0.6 | 3 | 18 | 0 |
| `plan-emitter` | emits the whole proven optimal plan as its answer | 0.2 | 1 | 1 | 0 |
| `liar` | legal letters, a 2-step cycle | 0.0 | 0 | 30 | 0 |
| `waiter` | `.` every turn | 0.0 | 0 | 42 | 0 |
| `wall-bumper` | `L` at rock every turn | 0.0 | 0 | 1 | 0 |
| `resigner` | `GIVE UP` on every level, winnable or not | 0.0 | 0 | 0 | 0 |
| `garbage` | prose, always | 0.0 | 0 | 0 | **2** |
| `soft-resigner` | "I give up, a hazard is already in my tunnel" | 0.0 | 0 | 0 | **2** |
| `never-starts` | a load that fails | — | 0 | 0 | **4** |

Score is `solved / levels-emitted` (R2). `moves` is a cost and is never averaged:
the ceiling on this item set is **0.8, not 1.0**, because 04 is provably lost —
and the reference bundle shows 19 moves at that ceiling while `beeline` needs 18
to score 0.6, which is what the two columns are for.

The exit codes: **no entrant run emitted 1** (that code is the instrument's own),
2 fired for both zero-measured runs at coverage 1.000, 4 for the entrant that
never loaded, 6 for a run against a drifted manifest. `run-all` returns 0 unless
a record failed to write (5).

The model entrant (`--entrant model --model-path …`) was **not** run: there are
no weights, no server and no GPU on this host. It is a real code path — llama.cpp
`/completion`, `content` preferred and `reasoning_content` used only if that is
where the answer came back, with the choice recorded — and its admission path is
what `never-starts` exercises: `probe_holder()` reads `/proc/net/tcp` for the
LISTEN socket's inode and maps it to a pid and cmdline through `/proc/<pid>/fd`,
and when it finds nobody it records *which probe ran and found nobody* rather
than "nothing is holding it". Its `weights.sha256` is null with the reason
printed, never 0 and never a filename standing in for a digest. `declared.gpu`
is null with the `nvidia-smi` probe named. Code entrants are marked
`instrument: "code"`, `on_board: false`, `certification: "REFERENCE RUN — not an
entrant, not for the board"`, and no table in this repository pools them with a
model's.

## 5. THE REPLAY

```
$ python3 test_digdug.py
replaying 13 bundle(s) from .../digdug/results
  649 checks, 0 failures
REPLAY PASSED
```

Every item is rebuilt from its recorded raw answers through `feed`, and the
counters, the final board, the named terminal reason and **each individual ply's
(word, position, outcome)** must come back identical. The bundle must have been
scored by the code on disk now (four digests), by the frozen contract
(`frozen_utc ≤ generated`), and its level digests must match the level files.
The score recomputes; `give_up` counts only exact tokens; `loose_give_up_unscored`
is re-derived and proven not to be in `give_up`; `emitted == consumed + after_end
+ over_budget` on every item; exit codes are re-derived from the record; a bundle
whose `moves` beat the proven optimum, or that solved 04, would fail here — which
is where a bad *proof* would be caught rather than a bad run.

## 6. WHAT THE CABINET FOUND ABOUT ITSELF

Nine things, all of them found by execution, and each one is still visible in the
file that fixed it:

1. **The chase was written backwards.** `hazard_distances` BFS'd out of the
   hazard instead of out of the player, so a pursuer standing next to its quarry
   found no strictly-closer neighbour, called it `boxed_in`, and never killed
   anyone. Every conclusion drawn before the fix — including "entombment is
   unreachable" — was void. The docstring on the function says so.
2. **`reachable_cells()` had a copy of the boundary rule in the wrong order:**
   it added the neighbour to `seen` under its *unwrapped* key, so any
   `wrap=True` reading sent the flood fill off the edge forever and the process
   died for memory. The frozen reading cannot reach it. The rule is now one
   function, `neighbour()`, used by `step`, both BFSs, the hazard's own step and
   the solver, and `D-NEIGHBOUR` records that it was found as a bug.
3. **A word that belonged to the wrong owner.** Under the rejected
   `player_into_hazard=killed` reading the engine returned `blocked` for a move
   that *moved the player and killed them*, contaminating the `blocked` counter
   with a shadow reading. There is now a sixth step word,
   `entered_hazard`, which the frozen reading can never emit.
4. **The freeze gate passed while comparing nothing** (see §2).
5. **`F2_safe_alternatives_at_arming_ply` was never populated** — the guard read
   `state.arming_ply`, which does not exist; the engine carries `armed_at`. Two
   zeros (`deaths_with_a_safe_alternative`, `arms_with_no_safe_alternative`) were
   quietly reporting a wiring bug. Fixed; the numbers are in §7 of SECTION_4F.
6. **`F1_committed_to_dug_ground` is degenerate on this item set** (pearls live in
   soil, so a tunnel-only completion never exists). Kept, reported beside the
   measure that is not, rather than swapped for the flattering one.
7. **`threat_gain = None` for "no road" erased most negative-balance plies.** No
   road on either side is *zero gain*; a road that *opens* has no magnitude in
   steps and is an event, not a number.
8. **`[D-T0]`'s sentence was too strong.** "At time zero nothing moves and nobody
   dies" is refuted by 04, whose authored `_` tunnels arm the hazard at distance
   2 before the first answer. The decision text now states the measured scope.
9. **`facet_rows` aggregation silently summed a subset** — `min_slack` over the
   two items that had one. Every facet aggregate now carries
   `<field>__items` and an explicit note that an absent field is not a zero.

Plus one limit of the runner, reported instead of fixed: `after_end` and
`over_budget` are structurally 0 in a driven run because the runner stops asking
a level the moment the attempt ends, so B1's two numbers coincide for every
entrant and the divergence is only reachable in `--self-test`.

## 7. THE SHADOW READINGS (`digdug_readings.py`, `results/shadow_readings.json`)

16 readings × 5 levels, and the number that matters is not the optimum, it is
what the *contract's own optimal line* does under the rejected rule:

| rejected reading | what it does to this item set |
|---|---|
| `hazard_terrain=soil_too` | **03 (opt 7) and 05 (opt 4) become PROVEN LOSSES**; 02 loses its exhaustive grade |
| `end_on_solve_first=False` | **01 — the floor of the whole scale — becomes unwinnable** (`opt None`, its one-letter plan ends `KILLED_BY_HAZARD`); so does 05 |
| `end_on_solve_first=False, death_beats_solve=False` | **INERT on all five**: the rejected reading collapses onto the frozen one unless you also reject the half inside it |
| `resolve_order=simultaneous` | 02's **optimum moves from 7 to 5**: an ordering clause changes how short the best plan is, not just who dies |
| `hazard_clock=never` | 02's optimum 7→5 and 03's grade → `bounded:13`; three runs end `STREAM_ENDED_UNFINISHED` instead of dead; and `ENTOMBED_BY_A_LIVING_WALL` appears — only here (probe P2) |
| `hazard_clock=every_2_player_turns` | separates on 04 alone, and *enables* `[D-BLOCK]`'s measurement (P1: `blocked` ends `WALLED_IN_ONLY`, `killed` ends `KILLED_BY_HAZARD`) |
| `wrap` / `bounds=raises` | inert on framed levels; decisive on an unframed one (P3: frozen never solves, wrap wins, `raises` throws out of `step`) |
| `objective=survive_n`, `target_persistence=persists_as_marker` | **REFUSED by the solver** — the state key carries no clock / stops tracking the objective. Reported as *not provable*, never as a zero |
| `tiebreak`, `hazard_blocks_hazard`, `player_into_hazard` | **INERT HERE**, and P1/P4 say why (a theorem about the chase; a needed fork; a player who must survive beside two hazards) |

Seven of the sixteen rows are not inert: five change a named terminal reason or
a proven optimum, and two more are refused by the solver before it could produce
a number. The other nine say `INERT HERE`, and `never` for `[D-TIEBREAK]` is a
*decision* that was never forced, not a finding. That is the argument for freezing the clauses — and the
argument for marking them in the contract, since six of them were not decided by
the paragraph at all.

## 8. WHAT WOULD BREAK THIS CABINET (and what is still open)

* **A model has not played it.** Every number here is from a code entrant. The
  model path is exercised at admission and in its failure modes, not at the
  board. Until a weights-bearing host runs `--entrant model --reasoning off`
  twice (ON and OFF, one setting per event), the cabinet's *purpose* is unmet
  even though its instrument is proven.
* **Caution is free on this item set.** The `slack-maximiser` never paid a turn
  for margin, so this set cannot price safety. A 6th level where the safe line
  is strictly longer than the optimal line would close that gap, and its optimum
  would have to be proved at `bounded:K` (the state space of a level designed for
  that is bigger than 45000).
* **Three clauses are untestable here** (`[D-BLOCK]`, `[D-TIEBREAK]`,
  `[D-HAZCOLL]`) — decided, argued, and unfalsified by any level this validator
  accepts. The probes say what a level would have to look like.
* **The strict token list costs 50 of 50.** `loose_give_up_unscored` across the
  field is **50**, and every one of them belongs to `soft-resigner` — the one
  entrant that abstains the way a model does, in a sentence. Its run is
  `ERROR: ZERO MEASURED`; `resigner`, which types `GIVE UP`, is SCORED with
  `give_up = 5` including the correct abstention on the proven-loss level. So
  the frozen list is not a benign strictness: on the evidence of this field it
  loses *every* natural abstention it meets, and the cabinet's most interesting
  item (04, where abstention is the only right answer) is exactly the item a
  prose-abstaining model gets zero for. R1 says the list is frozen and the loose
  match is a diagnostic, never scored — so this is reported as the cost of a rule
  this tier was told to freeze, not as a licence to unfreeze it. What a real
  model does here is the open question, and it is the one this box cannot answer.

## 9. REPRODUCE

```bash
cd digdug
python3 digdug.py --self-test                      # 68 controls
python3 digdug_run.py freeze-check                 # 11 digests vs disk; exit 1 on drift
python3 digdug_run.py levels                       # re-prove all five optima
python3 digdug_run.py instrument-check --out results --reasoning off
python3 digdug_run.py run-all --reasoning off --out results
python3 digdug_run.py readings                     # the shadow table + 4 probes
python3 test_digdug.py                             # replay every bundle: 649 checks
python3 digdug_run.py exit-codes
```

Order is not cosmetic: `freeze` then `tasks` then the field, because an optimum
derived after seeing the answers is not a proof, it is a caption. A run driven
before `freeze` exits 6 and the harness is glad about it.
