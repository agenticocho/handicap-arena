# SNAKE — the stepped harness, its baselines, and the first recorded model run

**Date:** 2026-10-17 · **Card:** t_401ee1d7 · **Author:** Ocho (CFO), owner of the cabinet
**Subject:** `snake/snake.html` — CC0 1.0, straker "Basic Games" gist `ff00b4b49669ad3dec890306d348adc4`

---

## What was missing, and what was built

The game was already downloaded. **The harness did not exist** — `sokoban_run.py` was the only entrant
driver in the tree, and snake needed a second one of a different shape: *stepped*, because the game runs a
`requestAnimationFrame` loop at 15 fps and a reasoning model cannot feed that live (measured in the sibling
cabinet at 2,314 tokens of `Thinking Process:` and no move).

| file | what it is |
|---|---|
| `snake_page.py` | **the stepped wrapper.** Holds the game's tick, seeds the RNG, dispatches a move into the game's own keydown handler, reads the live state. Stdlib only. |
| `snake_run.py` | the driver: baselines, the model arm, the artifact writer, `--verify` and `--replay`. |
| `snake_solver.py` | the deterministic baselines — a Hamiltonian cycle over the torus, and a tail-safe greedy searcher. |
| `snake_score.py` | **one definition** of the score, read out of the recorded trace alone. |
| `test_snake_harness.py` | the controls, each paired with the failure it exists to prevent. |
| `snake/snake.html` | the subject, verbatim. `snake/seeds.txt` — the seed list. `snake/SOURCE.txt` — where this copy came from and what its root digest is. |

## The subject, and a path that no longer existed

The card names `/home/chilly1/.hermes/profiles/tiel/cache/scratch/snake-arena/snake.html` (4,123 B).
**That directory has been pruned** — it is a Hermes scratch path with a 24-hour idle sweep, and it is gone.
The file was recovered from two surviving copies that agree byte for byte:

```
/home/chilly1/.hermes/profiles/tiel/cache/scratch/games-survey/src/snake.html
/home/chilly1/.hermes/workspace/snake.html
  both sha256 808a2772e668cd9fc5d837317417c4da0c0bc67a303b664c14a2959d2ffa7746   4,123 B
```

`snake/snake.html` is committed at that digest. **The instrument does not take this on trust:** every record
carries `subject.source_digest_on_disk` AND `subject.source_digest_from_live_dom` — the same inline script
read back out of the live DOM of the running page — plus `source_modified_by_harness`. Both are
`a441de57c63a66c5` and the flag is `false` in every recorded run: the harness installs two things and edits
nothing, and that claim is now checkable rather than asserted.

## How the tick is held (and why the tick length is not written down here)

`snake_page.py` injects a script into the page **before the game's own script runs** and does exactly two
things to it:

1. **`requestAnimationFrame` becomes a recorder.** The game's `loop` is captured and never scheduled by the
   browser; only the harness calls it.
2. **`Math.random` becomes `mulberry32(seed)`.** The page's only consumer is `getRandomInt`, i.e. the apple
   respawn, so `(seed, move list)` fixes the episode.

Neither touches a rule of the game. A move is a **dispatched `keydown`** (`keyCode`/`which` 37–40), so it
enters through the game's own handler — *including* the handler's no-backtrack rule (`snake.dx === 0`). The
harness never writes `snake.dx`. Every row records whether the game **accepted or refused** the move.

**The tick length is read from the game, not assumed.** `step()` calls the page's `loop()` until the page's
own throttle counter (`window.count`, which `loop()` resets) comes back to 0. With the file as shipped that
is 4 calls per tick; if the file's throttle changed, the boundary would still be the game's.

State is **read, not scraped**: `snake`, `apple`, `grid`, `canvas` and `count` are top-level `var`s in the
page. The vision projector is the documented fallback if injection were ever blocked; it is not the path
taken. (No pixels were read in any run here.)

## The score, and why the trace is a sufficient statistic for it

Definitions, all recomputable from the recorded rows alone (`snake_score.py`):

```
eaten       apples eaten over the episode  (the page RESETS on self-collision rather than ending)
best_life   the longest the snake got, in apples = max(maxCells - 4): the arcade reading
deaths      self-collisions the page performed
```

The trace carries, per tick: the full state before and after (head, direction, body cells, length,
`maxCells`, apple, and **the page's own `Math.random` call counter**), a digest of each state, the move
requested, whether the game accepted it, and how many `loop()` calls the tick took.

Three independent readings of the same events are compared **every tick**:

* `maxCells` — +1 per apple, back to 4 on a reset;
* the **random counter** — every respawn is exactly two `Math.random` calls, and the page consumes them in
  only two places, eating and resetting;
* the apple's cell — it cannot move without a respawn.

The case that forces the random counter rather than the length is real and reachable: if the head eats the
apple and the respawn lands **on the snake's own body**, the page increments `maxCells` twice and then
resets, all inside one tick, so the length readings cannot count the eat. That fixture is a control in
`test_snake_harness.py`, not a worry.

**The sufficiency claim is measured in two different ways, and the difference matters:**

* `--verify FILE` — recompute the score from the bundle's own trace and compare it with the score the
  bundle states. No browser.
* `--replay FILE` — **re-enter the run**: same seed, same move list, the real page, and the state chain must
  come back **digest for digest**. This is the difference between a trace and a story about a trace.

Both were run against a baseline bundle and a model bundle; both reproduce.

## The seed list

`snake/seeds.txt` = **1, 7, 13, 42**, frozen. Measured, not assumed: the board, the start cell (10,10) and
the first apple (320,320) are fixed by the file, so **a seed reaches the game only through an apple
respawn**. The clearest evidence is in the model run below — its four seeds produced the *identical* state
chain, because that run never ate an apple and therefore never consumed a random number.

## The baselines, on that list, at 120 ticks each

| baseline | total apples | per seed (1, 7, 13, 42) | deaths | note |
|---|---|---|---|---|
| `cycle` | **0** | 0, 0, 0, 0 | 0 | follows a Hamiltonian cycle. Provably cannot die; a *lap* machine — the first apple is 20 cells away but the cycle needs ~273 ticks to arrive. |
| `cycle-shortcut` | **18** | 4, 5, 4, 5 | 0 | cycle + shortcut inside the free window between head and tail. |
| `greedy-safe` | **33** | 9, 8, 8, 8 | 0 | BFS to the apple, screened by "can I still reach my tail". The floor a model should be read against on a short horizon. |

The cycle is constructed, not searched, and `selftest()` asserts for every size tried that it covers each
cell exactly once, that every consecutive pair (cyclically) is a legal move on the torus, and — for the
board the game ships — that **the game's own opening direction lies along the cycle**, so the follower is
safe from its first tick rather than after a transient.

`greedy-safe` is a heuristic with a known failure mode and it is shipped with its deaths recorded (zero
here). No baseline here is a proof that the entrant is being measured against an optimal player; they are
floors.

## The first recorded model run

`Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0` on the **PrismML fork** (`bin/cuda/llama-server`, digest
`3c7090fb24b84615`, mainline refused/garble for this family — the binary trap), `-c 65536 -ngl 0`, mmproj
loaded, `--reasoning off` (declared, with a reason: a one-letter answer; the probe confirms thinking OFF —
"2+2" answered in 2 tokens), temperature 0, server seed 42, `max_tokens 64`. Load 6–10 s. Model digest
`5ddb268245634001`.

| arm (legend order) | seed | apples | turns | answer | per-turn | gen tokens |
|---|---|---|---|---|---|---|
| `prose` (U D L R) | 1, 7, 13, 42 | **0** | 120 each | `R` on 120/120 | 0.92–1.19 s | 2 |
| `order` (D R U L) | 1 | **0** | 120 | `D` on 120/120 | 0.88 s | 2 |
| `first` (R U D L) | 1 | **0** | 120 | `R` on 120/120 | 0.93 s | 2 |

**The model is beaten by every baseline at the same horizon, and it is not close: 0 apples in 480 turns,
with `not_an_action` 0 and `missing_values` 0** — the answers were all legal, immediate, and never the
apple's direction.

### What the constant answer is, and what it is not

Four seeds × 120 turns, on four different boards, and the entrant returned the same letter on every turn.
Before reading that as a capability result, it has to survive three controls, and it did:

* **The question really changes.** 25 distinct prompts in the first 25 turns (a straight walk on a
  width-25 wrapping board is periodic with period 25 — a measurement of the board, and the reason 120 turns
  contain 29 distinct questions rather than 120). The entrant gave **one answer to 29 distinct questions.**
* **It is not the harness repeating itself** — the boards, the head cell and the stated heading all move.
* **It is not the game's input layer** — `accepted` is true on every turn; the letters were applied.

**And it tracks the legend, not the board.** Permuting the order in which the four controls are named moves
the constant answer (`U D L R` → `R`; `D R U L` → `D`; `R U D L` → `R`) while the board and every state are
identical at tick 0. The rules I tested against it are eliminated:

```
"the last control named"     prose R (last) survives, order says L but the run said D   DEAD
"the first control named"    first R (first) survives, prose says U but the run said R  DEAD
"the alphabetically first"   D: order survives, first says D but the run said R         DEAD
"echo of the heading"        prose/first say R, but order said D                        DEAD
```

**What remains, stated as the measurement rather than as a theory: the entrant's answer is a CONSTANT that
is a function of the prompt's wording and NOT of the board.** Three arms with n=1 each eliminate the four
rules above and nothing more; a fourth arm could still find one, and the honest count of what this run
establishes is *that the tool does not play snake and its letters come from the question's phrasing*.

## The controls

`python3 test_snake_harness.py` — 18 checks, exit 1 on any failure. Two of them found real things while
being written, and both are kept rather than tidied:

* **The tampered-move control passed when it had to fail**, and the reason is a property of the subject:
  `snake.html` ignores a reversal along the axis the snake is already moving on, so swapping a move for its
  opposite is a **no-op** — a tamper that changes nothing. The control now edits to a **perpendicular turn**
  (derived from the direction the trace says the snake was moving) and fails the replay as it must.
* **The "the question varies" control failed at 29 distinct prompts out of 120**, and that was correct
  behaviour — the period-25 walk above. It now asserts the two things separately: the question is not
  constant, *and* the answer was constant across distinct questions.

## How to run

```bash
python3 snake_run.py --self-test                                   # wrapper + solver controls
python3 snake_run.py --baseline greedy-safe --ticks 120            # the floor on the frozen seed list
python3 snake_run.py --entrant <gguf> --ticks 120                  # the model arm (fork binary by default)
python3 snake_run.py --legend order --entrant <gguf> --seeds 1     # the second arm of the legend A/B
python3 snake_run.py --verify probes/SNAKE_<agent>_s1.json         # score from the bundle alone
python3 snake_run.py --replay probes/SNAKE_<agent>_s1.json         # re-enter the run in the real page
python3 test_snake_harness.py                                      # all controls
```

One artifact per episode at `probes/SNAKE_<agent>_s<seed>.json` (a non-default legend arm adds
`_leg-<arm>` — the sibling cabinet's FINDING 024, where the arm lived only in the log name), plus a run
index `probes/SNAKE_RUN_<agent>_<utc>.json`. **The writer refuses to overwrite a record it did not take**
unless `--overwrite-artifact REASON` is given, and the reason is written into the replacement beside the
digest of what it replaced — that gate fired twice during this work and both replacements say why.

## What is NOT established

* **One model, one size.** Three Bonsai sizes exist; only the 4B was recorded. The 2B refuses or crashes on
  this family's fork per the sibling dossier, and the 9B is untried here. This is a first run, not a series.
* **No oracle.** Unlike the sibling cabinet's levels, snake has no solved reference, so `best_life` and
  `eaten` are floors against heuristics, not against optimality.
* **The baselines' safety is argued, not proven** for `greedy-safe` and `cycle-shortcut` (0 deaths on 4
  seeds each); only `cycle` has a proof, and it pays for it in score.
* **The reason for the constant answer is not identified** — three arms eliminated four rules and produced
  no rule. The claim is scoped to what was measured.
