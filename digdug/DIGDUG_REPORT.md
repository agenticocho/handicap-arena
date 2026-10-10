# DIG DUG — TIER 3 CABINET: what was built, verified, run, and what the prose would have cost

**Built and run:** 2026-10-10 · **Where:** `digdug/` · **Stdlib only, Python 3.11.2**
**Contract:** `CONTRACT_DIGDUG.md`, frozen at `2026-10-10T20:32:29+00:00`,
`sha256 b48c1c6a1c912374483d82eccb91b7b2e7aff2b8fe7b52f75ffce00989560e37`, combined-tree digest
`084f8726dfc30e342bf89fc8de5c00c16bb211f6c40d0469cb4d6d502dacd748`, **26 recorded decisions**

```
python3 digdug.py --self-test                    -> SELF-TEST PASS -- 100/100                exit 0
python3 digdug_solve.py --prove                  -> LEVEL VERIFICATION PASSED                exit 0
python3 digdug_run.py run-all --reasoning off    -> 12 entrants, 12 records on disk           exit 0
python3 digdug_run.py run model --reasoning off  -> NEVER STARTED, holder probed              exit 4
python3 digdug_run.py verify                     -> BUNDLE VERIFICATION PASSED, 13 replayed    exit 0
python3 test_digdug.py results                   -> SIDE SCRIPT PASS -- 626 checks            exit 0
python3 prose_check.py                           -> PROSE CHECK PASSED, 44/44 cross-check      exit 0
```

**Honest boundary, up front: no model played.** There is no GPU (`nvidia-smi -> not runnable:
FileNotFoundError`), no `llama-server` on PATH and no `.gguf` on the filesystem. The field is twelve
**code entrants** plus the `model` entrant exercised through its admission path. Every number below
is an instrument number. What is measured is the cabinet: whether it can see the two facets, whether
it classifies each shape of failure correctly, and what the prose left open.

---

## 1. WHAT I BUILT, AND WHAT I VERIFIED INDEPENDENTLY

| file | what it is |
|---|---|
| `CONTRACT_DIGDUG.md` | **the deliverable of E.** The whole specification, written from the 91-word paragraph, with all 26 decisions marked and argued |
| `freeze.py` | writes `FROZEN.json`: the digest of the contract, of every normative file, of every level; **the runner refuses to run without it** |
| `digdug_reader.py` | **THE ONE READER OF RECORD.** The answer shape and the frozen abstention list. Imported by everything, reimplemented by nothing |
| `digdug.py` | the simulator: `step()`, `turn()`, the hazard policy, both facet functions, 100 controls |
| `digdug_solve.py` | complete search with an exact heuristic: proves the optima, **counts distinct optimal lines**, proves level 04 unsolvable, proves the destruction claims |
| `digdug_run.py` | the runner, the scorer, the bundle writer, 13 entrants, 7 exit codes |
| `test_digdug.py` | the side script: replays every bundle from its own record, 626 checks |
| `alt_reading.py` + `prose_check.py` | **the second implementation and the divergence harness** — section 4F, measured |
| `levels/*.txt` (4), `tasks/digdug_v1.json`, `results/*.json` (13) | the level set, the item set, the records |

### Verified independently — not asserted

**The optima, by complete search.** Every one is a proof, not a find: the search is complete to the
budget and the `COMPLETE` flag is set, which means "no shorter line exists".

```
01_first_blood.txt             optimal 4     distinct 1     nodes 15       COMPLETE
02_the_long_way_round.txt      optimal 12    distinct 1     nodes 258      COMPLETE
03_the_open_door.txt           optimal 7     distinct 1     nodes 28       COMPLETE
04_no_safe_line.txt            optimal None  distinct 0     nodes 2879     COMPLETE   <- no safe line
```

**Standing rule B3, exercised rather than claimed.** A uniqueness counter that only ever says `1`
is not a validator. So a probe level with six distinct optimal lines is in the self-test:

```
ok   B3: the counter reports MORE THAN ONE optimal line when there is more than one (6)
ok   B3: and it reports ONE when there is one -- level 02's safe line is unique
```

**The two destruction claims, structurally.** Not a survey of reachable states (that search blew
memory on the first attempt, on the dug-set state space — which is why the method changed):

```
01 route-proof HOLDS (990 evals)   barrier-proof MONOTONE (component 1 -> 3)
02 route-proof HOLDS (1320 evals)  barrier-proof MONOTONE (component 3 -> 4)
03 route-proof HOLDS (1452 evals)  barrier-proof MONOTONE (component 2 -> 3)
04 route-proof HOLDS (594 evals)   barrier-proof MONOTONE (component 3 -> 4)
```

**The second implementation.** `alt_reading.py` shares no code with `digdug.py`, re-parses the level
text itself, and configured with my decisions reproduces my counters on **44/44** pairs. That is the
control that makes section 5 mean something.

**The freeze is enforced, not asserted.** A control adds a file to the normative set after the
freeze and watches the runner refuse:

```
ok   E: a normative file added after the freeze is REFUSED, not ignored
ok   E: and the tree verifies again once the probe is gone
```

And `test_digdug.py` checks the ordering from the timestamps in the records themselves: every
bundle's `generated` is at or after `frozen_at`.

### The six things "done means measured" required

| requirement | where it lives | the check that fails if it breaks |
|---|---|---|
| record written **before** the branch | `run_entrant()` writes for every entrant, including one that never started; atomic `.partial` + `os.replace` | `EXIT_WRITE_FAILED` (5); a never-started entrant still leaves a record |
| a failed load **names the holder** | `probe_holder()` — `/proc/net/tcp{,6}` LISTEN + `/proc/<pid>/fd` | the model bundle carries `holders: []` **and** the probe that found nobody, never a bare "failed to load" |
| the model's **DIGEST**, or a written reason | `results[0].weights` | the model bundle: `"NO WEIGHTS: no --model-path was given, so there is no file to digest.  This is stated rather than left empty."` |
| **which code** produced the verdict | `results[0].verdict_code` — five digests: runner, simulator, reader, solver, contract | `test_digdug.py`: "says WHICH CODE produced the verdict, by four digests" |
| the **exit code reflects the run** | a 7-row table; `1` reserved for *instrument not proven*; `6` for *not frozen* | group `[12]` **executes** the runner for all 12 entrants and asserts each code, including "no entrant's run exits 1" |
| **reasoning** and **GPU** per run | `bundle.declared.{reasoning, gpu}`, at the top of the file | `test_digdug.py` refuses a directory that declares more than one of either |

```
declared.reasoning : "off"  -- DECLARED BEFORE THE RUN; the answer is ONE CHARACTER per turn
declared.gpu.name  : null
declared.gpu.probe : "nvidia-smi -> not runnable: FileNotFoundError"
declared.gpu.note  : "NO ACCELERATOR FOUND by this probe.  This is null, not 0.00 and not 'none'"
```

---

## 2. WHAT I RAN — ENTRANT BY ENTRANT, FACET BY FACET, FROM THE SAME TRACES

One declared setting for the whole event (`reasoning: off`, one null GPU, budget 30 turns).
13 bundles, 920 KB, all replayable from their own records.

| entrant | solved | **score** | dug | blocked | emitted | consumed | n/a/a | give_up | **F1** barrier / budget-ruin | **F2** died | verdict | exit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **reference** (complete search) | 3/3 | **1.000** | 23 | 0 | 23 | 23 | 0 | 0 | – / – | – | SCORED | 0 |
| **static-planner** (plans once, at t=0) | 2/3 | 0.667 | 13 | 0 | 13 | 13 | 0 | 0 | **02** / – | **02** | SCORED | 0 |
| **hazard-blind** (re-plans, no hazards) | 2/3 | 0.667 | 13 | 0 | 13 | 13 | 0 | 0 | **02** / – | **02** | SCORED | 0 |
| **wanderer** (digs ground that does not help) | 2/3 | 0.667 | 20 | 0 | 20 | 20 | 0 | 0 | **01** / – | **01** | SCORED | 0 |
| **survivor** (never merges, never aims) | 2/3 | 0.667 | 18 | 23 | 41 | 41 | 0 | 0 | – / **02** | – | SCORED | 0 |
| **ring-runner** (opens the door, then runs) | 1/3 | 0.333 | 15 | 27 | 45 | 45 | 0 | 0 | **02,03** / **01** | **02** | SCORED | 0 |
| **liar** (plays 01's plan everywhere) | 1/3 | 0.333 | 12 | 1 | 13 | 13 | 0 | 0 | **02,03** / – | **02,03** | SCORED | 0 |
| **wall-bumper** (always `U`) | 0/3 | 0.000 | 0 | 90 | 90 | 90 | 0 | 0 | – / **01,02,03** | – | SCORED | 0 |
| **resigner** (`RESIGN`, a frozen token) | 0/3 | 0.000 | 0 | 0 | 3 | 3 | 0 | 3 | – / – | – | SCORED | 0 |
| **garbage** (junk every turn) | 0/3 | – | 0 | 0 | 90 | 90 | 90 | 0 | – / – | – | **ERROR: ZERO MEASURED** | **2** |
| **soft-resigner** (abstains in English) | 0/3 | – | 0 | 0 | 90 | 90 | 90 | 0 | – / – | – | **ERROR: ZERO MEASURED** | **2** |
| **never-starts** | – | – | – | – | – | – | – | – | – | – | **ENTRANT NEVER STARTED** | **4** |
| **model** | – | – | – | – | – | – | – | – | – | – | **ENTRANT NEVER STARTED** | **4** |

*F1 columns: `01`/`02`/`03` are the levels. "barrier" = `barrier_lost_at_turn` fired; "budget-ruin"
= `budget_ruin_at_turn` fired. F2 = the level it died on. **Both columns were read off the same
trace object**, and every bundle records that fact per level (`C8 both facets cite ONE trace`,
checked 626 times).*

### The three readings of the same run that matter

**1. The faculty, caught on level 02 at turn 2.** Four entrants die there, and the record says why
in the entrant's own terms rather than in mine:

```
hazard-blind  02  died_at_turn 2   kill_path [[1,4],[1,3]]   cells dug by the player: 1 of 2
                first_kill_cell_dug_at_turn 2   dig_to_death_turns 0
                barrier_lost_at_turn 2   <- the same ply, on the same trace
```

The player's **second dig** opened `(1,3)` beside the hazard's pocket and the hazard walked in on
the same turn. The 8-move route is a death; the only safe line is 12 moves around a rock spine. The
board never says so. The instrument does, on the ply it happened.

**2. Facet 1 without facet 2 — and facet 1 on a level it still WON.** `ring-runner` on level 03:

```
03_the_open_door.txt   barrier_lost_at_turn 3   ...   terminal SOLVED   turns_used 13
```

It dug the one cell that connects the hazard's pocket to its own ground, permanently destroyed the
last safe line at turn 3, was never caught, and collected the target at turn 13. **The ground it
needed was consumed and it got away with it.** That single line is the argument for reading the two
facets separately: a death-centred instrument would have recorded a clean solve.

**3. Facet 1b needs no hazard at all.** `wall-bumper` and `survivor` are budget-ruined on every
level: the shortest completion exceeds the answers left. Nothing ever threatened them. A cabinet
that measures only deaths cannot see this failure.

### The control level, and what it proves about the reader

Level 04 has **no safe line** (proved exhaustively), so the only correct answer on it is to stop.

| entrant | gave_up | was_right | terminal |
|---|---|---|---|
| reference | 1 | **True** | GAVE_UP |
| resigner | 1 | **True** | GAVE_UP |
| **soft-resigner** | 0 | **False** | BUDGET_EXHAUSTED — 30 × `multi_char_no_truncation` |
| the other nine | 0 | False | KILLED or BUDGET_EXHAUSTED |

`soft-resigner` answers *"I give up, there is no way to finish this one."* — a correct answer, in
English, on the one level where it is the only correct answer. Under the frozen exact-match rule it
is 30 malformed answers and the run exits 2, `ERROR: ZERO MEASURED`. The
`loose_give_up_diagnostic` flag is `true` on all 30 plies, **recorded and never scored**, so the
divergence is visible instead of silent. This is standing rule R1's failure mode reproduced on
purpose: **the instrument's inability to read an abstention is filed as an error, not laundered
into a score of 0.00.**

### Standing rules, where each one is in the record

- **R1** — the token list is frozen in one place; `freeze.py --write-tokens` generates the
  contract's block from the code and the runner compares them before it will run:
  `R1: the CONTRACT's token list EQUALS the code's scored list (31 tokens)`. Every ply names the
  rule that fired (`action_letter`, `give_up_token_exact`, `multi_char_no_truncation`, …). Loose
  match is a diagnostic only.
- **R2** — the gate is `solved / attempted_emitted`; moves are a cost, carried per level and in
  totals, never averaged. The other reading (`solved / answers_emitted`) is recorded beside it.
- **R3** — one answer per turn, stated only in the read grammar and in the prompt. No reading makes
  a correct answer a failure: on level 04 the correct answer (an abstention) is recorded as
  `give_up`, not as `not_an_action`.
- **B1** — `answers_emitted`, `answers_consumed` and `answers_after_end` are three numbers, and
  `test_digdug.py` asserts `emitted = consumed + after_end` on every bundle.
- **B2** — bounds are checked inside `step()`; enclosure is measured per level and is `true` on all
  four; a deliberately unenclosed board is a control that exercises the check.
- **B3** — the solver counts distinct optimal lines (6 on the probe level, 1 on each scored level),
  and the token list is validated for uniqueness, not just length.

---

## 3. THE THREE THINGS IN THE CONTRACT I HAD TO GUESS AT

Twenty-six decisions are in the register. These three are the ones I would settle first, because
everything else is downstream of them.

### 1. `[U1]` The hazard has no clock in the prose, and the clock decides every death

"A hazard cannot reach the player except through tunnels" says where it can go and nothing about
when. **Chosen:** one cell per player turn, along a shortest tunnel path, ties by `U,D,L,R`,
simultaneously for all hazards, and it never digs. **Rejected:** an own clock at rate 1:2 (whether
the hazard arrives then depends on the parity of the turn you opened the corridor, and nothing in
the record would say which parity the run used); a random walk (unreproducible, so a bundle could
not be replayed and the cabinet could not certify); one-step greedy (oscillates in a straight
corridor and never arrives). **Measured:** flipping this one clause changes 2 pairs in the field —
`liar`/03 and `wanderer`/01 go from KILLED to UNSOLVED.

### 2. `[U2]` What exists at time zero — and the literal reading deletes the faculty

"A grid of soil" plus "cannot reach the player except through tunnels" has a literal consequence
nobody would intend: **a hazard standing in soil is not in a tunnel, so it can never move at all.**
**Chosen:** the player's cell and every hazard's cell are tunnels at t=0. **Rejected:** the literal
reading, under which the hazard is decoration and the cabinet measures nothing. **Measured:** this
clause is settled by the field — under the literal reading the short route on level 02 stops being
a death, because the hazard in the pocket cannot leave it.

### 3. `[A11]`/`[R3]` The prose contains no answer at all

Ninety-one words about a game, and not one about what the player says. **Chosen:** one token per
turn from `{U,D,L,R}` or a frozen 31-token abstention list; exact match, punctuation not stripped;
never truncated; no pass action; the cap is on answers emitted. **Rejected:** a permissive reader
(first line, first letter) and a two-token list. **Measured:** the permissive reader turns
`"move right please"` into `R` and a garbage entrant **solves level 01**; the two-token list turns
the reference solver's correct abstention on level 04 into a malformed answer. Both change the
score, not just the trace.

*(A fourth, found only by diffing two implementations: `[A17]` — whether the counters come from the
word or from the state change. Eleven of 44 pairs disagreed, and mine was the wrong one. See §5.)*

---

## 4. THE FROZEN CONTRACT, WITH EVERY UNDER-SPECIFIED CLAUSE MARKED

`CONTRACT_DIGDUG.md` is the contract; this is the register. `[U<n>]` = the prose is silent and the
brief named the gap. `[A<n>]` = the prose is silent and the brief did not raise it either.

```
step(state, action) -> (new_state, word)      TWO values.  PURE [A2].  word in
                                              {dug, moved, blocked, collected}
turn(state, action) -> (new_state, word, events)
   1. the player's move            2. collection -- the LAST target ends the
                                      attempt BEFORE the clock [U6][U7]
   3. the hazard clock, all hazards simultaneously [U1][U8]
   4. the death check: same cell only [U4]
```

| id | the clause the prose did not settle | chosen | rejected |
|---|---|---|---|
| U1 | the hazard's clock | 1 cell/turn, shortest tunnel path, ties `U,D,L,R` | own clock at 1:2; random walk; 1-step greedy |
| U2 | what exists at t=0 | the player's and every hazard's cell is a tunnel | hazards stand in soil → they can never move |
| U3 | the collected target | removed; the objective is the **count** | persists; a positional objective |
| U4 | adjacency, and whose move resolves first | only the **same cell** kills; order pinned in §3 | adjacent = death (makes the prose's tunnel sentence redundant) |
| U5 | may the player stop | **no pass**; abstention ends the attempt | `WAIT` as a turn (stalling until the cap) |
| U6 | what "solved" means | all targets collected, alive, on that turn | a designated exit cell; survive N turns |
| U7 | the collecting turn | the objective is awarded **before** the clock | the turn resolves in full (kills the winning move) |
| U8 | several hazards | simultaneous from one snapshot | sequential in index order |
| U9 | the boundary | bounded, **no wrap**, out of bounds is `blocked` in `step()` | a torus; raising an exception |
| A1 | do hazards dig | never | they dig (makes the prose's own sentence false) |
| A2 | is `step()` pure | pure, returns a NEW state | mutating in place |
| A3 | what makes a level malformed | 7 enumerated conditions | fail-soft parsing |
| A4 | ragged rows | padded with **rock**, fact recorded | padded with soil (invents ground) |
| A5 | level 04 | a **CONTROL**, not scored | scoring a level whose correct answer is to stop |
| A6 | an unresolved letter to `step()` | raises | folded into `blocked` |
| A7 | word precedence | `collected` > `dug` > `moved`, detail in `events` | one word, detail lost |
| A8 | a blocked move | costs the turn, ticks the clock | free (makes a wall-bumper immortal) |
| A9 | the completion distance | exact (a dig costs one move and never blocks) | a heuristic |
| A10 | hazards sharing a cell | allowed, they do not block each other | they block (would make U8 observable) |
| A11 | the abstention list | 31 tokens, union of both Sokoban lists, exact | 2 tokens; loose matching |
| A12 | the answer shape | one token per turn | a plan; one line of many |
| A13 | the prompt | states the shape and the token list; never shows a diagnostic | showing `solvable_after` |
| A14 | the budget | **30 turns**, declared, in every bundle | undeclared (two runs not comparable) |
| A15 | the gate | `solved / attempted_emitted` (levels that emitted) | `solved / answers_emitted` (recorded beside it) |
| A16 | scoring against a plan | never; the answer is executed | comparing to the solver's plan |
| A17 | the counters | from the **state change** | from the word (off by one on every fatal move) |

The freeze covers all of it: `freeze.verify()` fails if a decision marker exists in the code that
the contract does not record, and the runner exits **6 NOT FROZEN** rather than run an entrant
against an unfrozen spec.

---

## 5. SECTION 4F — WHAT THE PROSE WOULD HAVE MADE ME GET WRONG

**Full text: `DIGDUG_PROSE_TRAPS.md`.** Produced by building a second implementation of the same
paragraph that chose the opposite reading on every open clause, verifying it reproduces my counters
under identical decisions (**44/44** pairs agree), then replaying the field's answer streams
through it and flipping one clause at a time. Under the fully literal reading **23 of those 44 pairs
differ**, on identical answers — two cabinets, same model, different numbers.

**The headline: the paragraph does not describe a destructive search.** "Moves into soil **or into
an already-dug tunnel**" plus "moving into soil digs it" means the tunnel is the *most* reusable
ground on the board — enterable forever, one move to enter, exactly what soil costs. **The
traversable graph only grows, so a route can never be consumed.** Proved over 4,356 distance
evaluations: the distance to a target does not depend on the dug set at all.

So the brief's own gloss — *"the tunnel you dug is ground you cannot re-use"* — is false under the
prose it came from. What you cannot re-use is the soil's function as a **barrier**. That is a real
permanent destruction, and it is the only one, which forces the consequence:

> **The two facets this tier demands are nested, not independent.** A death requires the components
> to have merged, so facet 2 ⊆ facet 1. Checked on all 11 deaths in the field. Making them
> independent needs a mechanic the paragraph does not contain (falling rocks, collapsing tunnels, a
> dig budget). I did not invent one; I measured the consequence and split facet 1 into a barrier
> half and a hazard-free budget half.

**How each open clause was arbitrated:**

```
SETTLED BY THE FIELD        :  8   U1 U2 U4 A1 A8 A11 A13 A17
SETTLED BY A PROBE ONLY     :  4   U5 U7 U9 A6      (the field never reached them)
NOT SETTLEABLE BY ANY RUN   :  2   U3 (render only)  U8 (moot under A10)
STILL OPEN, NO CARRIER      :  0
```

Three of them move the **score**, not just the trace — which is what makes them dangerous, because
two cabinets would publish different rankings from identical answers:

```
U4 adjacency kills      ring-runner  solved 1/3 -> 0/3
A1 hazards dig          ring-runner  solved 1/3 -> 0/3
A13 permissive reader   garbage      solved 0/3 -> 1/3   (a junk emitter SOLVES a level)
```

**And three defects in my own build, all caught by executing it:**

1. **`[A17]` a counter that disagreed with the board in the same record.** The counters read the
   word, so a fatal move lost its dig and its block from the tally while the printed board showed
   both. Off by one on every death. **Found by the second implementation, on 11 of 44 pairs** — not
   by reading my own code, and the self-test passed while it was wrong.
2. **A runner that never stops asking.** The cap was on game turns, and the clock only advances on
   an action, so an entrant emitting only malformed answers hung the field (900 s, no output).
   Fixed: the cap is on answers emitted `[A14]`.
3. **My own contract contained a rule the contract makes impossible.** The first draft made a
   "swap-through" a death; under the frozen order the hazard targets the player's *post-move* cell,
   so the state cannot occur. A control found nothing to construct. An unreachable rule in a
   specification is a bug no test can ever find, because the test cannot build the input.

---

## 6. WHAT I THINK IS WRONG — IN THE FROZEN ARTIFACTS, AND IN MINE

**In the brief's framing.**
1. *"The tunnel you dug is ground you cannot re-use"* contradicts the prose it summarises, and the
   contradiction is exactly about the faculty under test. Under the prose, digging never removes a
   route. Either the prose gains a destructive mechanic or the tier's stated faculty is the hazard
   graph, not the traversal graph. **Measured, §5.**
2. *"TWO FACETS"* cannot be two independent mechanics under this prose; they are nested. The
   cabinet measures both, and says so, rather than presenting them as orthogonal.

**In the standing rules.**
3. **R2's denominator is ambiguous.** `solved / attempted_emitted` — attempted *what*? B1 defines
   emitted/consumed for **answers**, so the natural reading is answers; but a per-answer denominator
   makes a 12-move solve score 0.083 and rewards doing nothing. I declared **levels that emitted at
   least one answer** as the gate, recorded the per-answer reading beside it in every bundle, and
   note that on this field the two do **not** rank the entrants differently (both put `reference`
   first and the zero-solvers last) — so the ambiguity is recorded but not yet costly. It would be
   on a field with a solver that flails.
4. **R1's "loose-match is a diagnostic" is right and it is not enough.** `soft-resigner` is the
   proof: a correct answer recorded as 30 malformed ones, and the run correctly reported as an
   ERROR. The rule prevents a wrong score; it does not prevent the instrument from being unable to
   see its own faculty. That needs a decision about semantic matching, not a diagnostic.

**In my own frozen artifacts.**
5. **Levels 01 and 03 do not punish a hazard-blind planner.** Measured: `hazard-blind` and
   `static-planner` solve both and die only on 02. With equal speeds and pre-hazard collection, a
   hazard can only kill a player that *approaches* it, so only a level whose short route approaches
   the pocket discriminates. **Level 03 carries facet 1a instead** — it is the level where the
   barrier can be lost without death — but it is not a second discriminating level. A fourth scored
   level is needed; I did not add one to a set I had already frozen and proved.
6. **Level 04 is doing two jobs.** It is the unsolvability proof and the abstention test. If an
   entrant dies on it (nine of twelve do) the record cannot distinguish "did not recognise the dead
   end" from "walked into the hazard before deciding". Two control levels would separate them.
7. **`U8` is recorded as a decision and is not one.** Under `[A10]` (hazards do not block each
   other) index order cannot change any hazard's move. The register should say so, and now does, in
   `DIGDUG_PROSE_TRAPS.md` F2 — but the contract row still reads like a live choice.
8. **My own side script produced 33 false failures before I read one.** Its
   first build asserted `items[level]["enclosed"]`; the record carries that
   measurement at `results[0].levels[level].enclosed`. The failures were real
   signal and my reading of them was wrong — which is the same mistake class as
   trusting a prose paragraph. It now reads the recorded path, and also
   re-digests every level file against the digest the bundle names.
9. **The `survivor` entrant solves 2 of 3 levels.** It was built as a "survives but does not solve"
   control and it does not behave like one, because on this level set fleeing happens to run past
   the targets. The control is weaker than its name; the number is honest.

---

## WHAT I DID NOT DO

- **No model played.** No GPU, no server, no weights on this host. The `model` entrant is built, its
  admission path is exercised, the holder probe ran and named nothing, and the record says so in
  writing. **No number in this report is a model number.**
- **I did not add a fourth scored level**, and I did not change a level after freezing it.
- **I did not invent a destructive mechanic** to make the two facets independent. The prose does not
  contain one; the report measures that instead.
- **I did not resolve R2's denominator by fiat.** Both readings are in every bundle; the gate is
  declared and named.
- **Nothing outside `digdug/` was touched.** `git status` shows only this directory.
