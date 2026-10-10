# SOKOBAN — independent cabinet #2: what was built, verified and measured

**Built:** 2026-10-10 · **Where:** `sokoban2/` · **Stdlib only**
**Method:** built against `SOKOBAN_READ_GRAMMAR.md`, the two frozen levels and the dossier, **without
reading `sokoban/sokoban.py`**. The source was read only after the cabinet was finished and the field
was run — Part Two of `SOKOBAN2_AMBIGUITIES.md` is that diff.

```
python3 sokoban2.py --self-test                            -> SELF-TEST PASS -- 79/79            exit 0
python3 sokoban2_solve.py                                  -> LEVEL VERIFICATION PASSED          exit 0
python3 sokoban2_run.py instrument-check --reasoning off   -> INSTRUMENT CHECK PASSED            exit 0
python3 sokoban2_run.py run-all --reasoning off            -> 8 entrants, 8 records on disk      exit 0
python3 sokoban2_run.py verify                             -> BUNDLE VERIFICATION PASSED         exit 0
python3 cross_check.py                                     -> 65/75 agree with the frozen sim
```

---

## 1. WHAT I BUILT

| file | what it is |
|---|---|
| `sokoban_reader.py` | **THE ONE READER OF RECORD.** Imported by the simulator, the runner, the solver and the side script. No second copy of the token rules exists anywhere in `sokoban2/`. |
| `sokoban2.py` | the simulator: `step()`, `State`, `feed()`, `play()`, `build_prompt()`, 79 controls |
| `sokoban2_solve.py` | exhaustive BFS over `(player, boxes)` — verifies the frozen optima and supplies the dead-end **diagnostic** (never scores) |
| `sokoban2_run.py` | the runner + scorer + bundle writer: admission, per-turn prompting, execution, record-before-verdict, exit codes |
| `test_sokoban2.py` | the side script: replays **every** bundle from the record and recomputes the result |
| `cross_check.py` | the behavioural diff against the frozen simulator |
| `levels/03_the_corner_waiting.txt` | level 03 — **which did not exist in the branch** |
| `results/sokoban_v1_*.json` | 10 bundles |

### The six things "done means measured" required

| requirement | where it lives | the control that fails if it breaks |
|---|---|---|
| record written **before** the success/failure branch | `cmd_run()` calls `write_bundle()` before any `return`; atomic `.partial` + `os.replace` | `EXIT_WRITE_FAILED` (5), and `run-all` is non-constant by construction |
| a failed load **names the holder** | `probe_holder()` — `lsof`, then `/proc/net/tcp` + `/proc/<pid>/fd`. Verified: it names `pid 7214 / python3 / socket:[31624]` on a real listener | `HOLDER: a failed load names the holder or says which probe found nobody` |
| the record carries the model file's **DIGEST** | `results[0].weights.{path,name,sha256,bytes,note}` | `a model entrant carries the weights DIGEST, or states in writing why there is none` |
| the record says **which code** produced the verdict | `results[0].verdict_code.{module,function,sha256,simulator,reader,solver}` — four digests | three `PROVENANCE:` controls |
| the **exit code reflects the run** | a 6-row table; `1` reserved for *instrument not proven* | group `[11]` calls `cmd_run` for **all 8 entrants** and asserts each code |
| **reasoning** and **GPU** per run | `bundle.declared.{reasoning, gpu}`, top of file | `A11:` controls, and `test_sokoban2.py` refuses a results dir whose bundles disagree |

**The exit-code control is the one worth dwelling on.** The defect it exists for — a CLI returning a
constant `1` while the self-test reported all green — is defeated by *inspection*, not by assertion.
So group `[11]` does not read the return statements. It **executes** the runner, in process, for every
entrant, and compares the code that comes back:

```
ok   runner exits 0 for entrant 'corner-walker' (got 0)
ok   runner exits 2 for entrant 'garbage' (got 2)
ok   runner exits 4 for entrant 'never-starts' (got 4)
ok   no entrant's run exits 1 -- 1 is reserved for an UNPROVEN INSTRUMENT, not for a run that failed
ok   an unknown entrant exits 3, not 0 and not 1
ok   RECORD: the side script replays every bundle from the record and reproduces the counters
```

## What I verified independently

**The three optima — by exhaustive search, not by trusting a level file.** BFS over the whole state
space, so the answer is a proof of the optimum, not a find:

```
ok   01_one_push.txt             optimal  1  (claim  1)    2 states   plan R
ok   02_two_boxes.txt            optimal 12  (claim 12)  329 states   plan DDRRRRULLURR
ok   03_the_corner_waiting.txt   optimal  6  (claim  6)   26 states   plan RRULLL
ok   the solver's branch rule and step() agree on every cell and every action
```

Levels 01 and 02 are read **in place** from `sokoban/levels/` — not copied, because a copy drifts — and
checked against `sokoban/MANIFEST.txt` by digest (control group `[0]`, both pass).

**The frozen simulator's own claim, run not read:** `python3 sokoban/sokoban.py --self-test` →
`ALL CONTROLS PASS -- 49/49`, exit 0. **The 49 is true.**

**Level 02 has thirteen distinct 12-move solutions.** The optimum is a fact; *the plan* is not. This
instrument only ever executes an answer, never compares it to a reference plan.

---

## 2. WHAT I RAN

**No model played.** The box has no GPU and no `llama-server` (`nvidia-smi` absent, no `.gguf`
anywhere on the filesystem). So the field is **code entrants** — each a different shape of failure the
instrument must classify correctly — plus the `model` entrant, which is exercised through its
admission path and fails honestly. Every run declared `reasoning: off` (the answer is one character —
a format-carry task, not multi-step arithmetic) and every bundle carries that declaration.

| entrant | solved | tried | **score** | moves | attempted | blocked | not_an_action | after_end | give_up | corr. ignored | readable | verdict | exit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **reference** (optimal solver) | 3 | 3 | **1.000** | 19 | 19 | 0 | 0 | 0 | 0 | 0 | 3 | SCORED | 0 |
| **liar** (legal letters, never solves) | 1 | 3 | **0.333** | 119 | 124 | 5 | 0 | 0 | 0 | 0 | 3 | SCORED | 0 |
| **corner-walker** (walks into the dead end) | 0 | 3 | **0.000** | 52 | 180 | 128 | 0 | 0 | 0 | 0 | 3 | SCORED | 0 |
| **wall-bumper** (`L` forever) | 0 | 3 | **0.000** | 2 | 180 | 178 | 0 | 0 | 0 | 0 | 3 | SCORED | 0 |
| **resigner** (exact token, abstains) | 0 | 3 | **0.000** | 0 | 3 | 0 | 0 | 0 | 3 | 0 | 3 | SCORED | 0 |
| **garbage** (prose) | 0 | 3 | 0.000 | 0 | 180 | 0 | 180 | 0 | 0 | **6** | **0** | **ERROR: ZERO MEASURED** | **2** |
| **soft-resigner** (abstains in English) | 0 | 3 | 0.000 | 0 | 180 | 0 | 180 | 0 | 0 | **6** | **0** | **ERROR: ZERO MEASURED** | **2** |
| **never-starts** (rc=2, no weights) | 0 | 0 | — | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **ERROR: POPULATION NEVER STARTED** | **4** |
| **model** (no server, no file) | 0 | 0 | — | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **ERROR: POPULATION NEVER STARTED** | **4** |

Per level, the terminal reason is named, not inferred:

```
reference       01:SOLVED                02:SOLVED            03:SOLVED
liar            01:SOLVED                02:BUDGET_EXHAUSTED  03:BUDGET_EXHAUSTED
corner-walker   01:WALL_BUMPED_ONLY      02:WALL_BUMPED_ONLY  03:BUDGET_EXHAUSTED
wall-bumper     01:WALL_BUMPED_ONLY      02:WALL_BUMPED_ONLY  03:BUDGET_EXHAUSTED
resigner        01:GAVE_UP               02:GAVE_UP           03:GAVE_UP
garbage         01:NO_LEGAL_ACTION_PRODUCED  (x3)
soft-resigner   01:NO_LEGAL_ACTION_PRODUCED  (x3)
```

### Three numbers from that table that are the actual findings

**1. The wall-bumper is the dossier's control, confirmed.** 180 attempts, 178 blocked, **2 moves, 0
solved**. A counter that reported `moves` as `attempted` would call it a very long, very active game.

**2. The dead-end faculty is measurable, and it is measured.** The `corner-walker` on level 03:

```
attempt 1  U  moved   solvable_after = True
attempt 2  R  pushed  solvable_after = False    <- the crate is in the corner. Nothing can move it again.
attempt 3..60                                    <- it plays 58 more moves on a corpse
```

The board never says so. The instrument does — `solvable_after` is on **every ply** in **every**
bundle, recorded by an exhaustive solver, and **never scored**. The cabinet can already see the dead
end; the frozen criteria give it nothing to say about it.

**3. `soft-resigner` is the instrument's own finding, not the entrant's.** It abstains perfectly, in
English, on all three levels. It is recorded as **180 `not_an_action` and 0 `give_up`**, and the run is
reported as `ERROR: ZERO MEASURED`. An entrant that did exactly what the cabinet's faculty asks for is
filed as the instrument failing to read. The `loose_give_up_unscored: 180` diagnostic is carried
alongside, unscored, so a reader can see the divergence.

### Ordering note

`run-all` → `model` → `verify` → `instrument-check` → `verify`. `instrument-check` internally runs the
simulator self-test, which runs all eight entrants and re-runs `verify_all`, so the last `verify`
covers all ten bundles. **All ten declare `reasoning: off` and the same (null) GPU** — `test_sokoban2.py`
refuses the directory otherwise, because two bundles for one event declaring different instruments are
not the same measurement.

---

## 3. THE THREE THINGS IN THE CONTRACT I HAD TO GUESS AT

Full arguments, evidence and the remaining ~20 items are in `SOKOBAN2_AMBIGUITIES.md`.

### 1. **The abstention token is not defined — and it is the cabinet's only counter for its own faculty.**

`give_up` is "an explicit ABSTENTION", "SCOREABLE", and "the only reason this event can measure
collapse without a solver" (§2). §3 uses `RESIGN` as its example. **No token is ever given.**

I invented a set. The frozen implementation invented a different one. Of 22 abstention-shaped probes,
**only `RESIGN`, `RESIGNS` and `GIVEUP` are common to both.** `QUIT`, `SURRENDER`, `FORFEIT`,
`RESIGNED` are abstentions there and `not_an_action` here. `ABSTAIN`, `NO MOVE`, `DEAD END`, `STUCK`,
`UNSOLVABLE`, `I GIVE UP` are abstentions here and `not_an_action` there. **A model writing `STUCK`
scores `give_up` on my instrument and `not_an_action` on yours, from identical bytes.** Measured, on
the field: `resigner` → `give_up 3`; `soft-resigner` → `give_up 0, not_an_action 180`.

This is first because it is not a formatting gap. Dossier §7 says there is no solver, so the board
cannot announce a dead end — therefore **the entire faculty is observable through exactly one counter,
and that counter has no defined input.**

### 2. **"THE SCORE" is a count, the gate is a rate, and no rate is defined.**

§2: `moves` is "THE SCORE". §9: "GATE AS FRACTIONS". §11: "a set of **item rates**". `moves` is an
integer. A rate needs a numerator and a denominator and neither is written down.

Five defensible candidates rank my own field five ways. **The read grammar's "THE SCORE" rewards
exactly the failure the cabinet exists to measure**: by `moves`, the corner-walker (52) — dead at move
2, 58 more moves on a corpse — beats the reference solver (19) by nearly 3×. I recorded both
(`score = solved/attempted` for the gate; `moves` per level and in totals, never averaged) and named
which is which. I did not pick a winner; choosing one is scoring design, and *a rubric is where gaming
gets in*.

### 3. **The shape of the exchange: how many answers, and how many turns.**

§1 says "exactly one action letter … nothing else **on the line**" (there are lines). §5 permits the
entrant to see "the **move history so far**; **the move count**; solved or not" (it is asked many
times). §5.2 is `play(level, move_stream)` (it emits a whole plan at once). Under the third reading,
§1's "more than one letter → `not_an_action`" makes **every legal plan** a malformed answer — and level
03's only solution is `RRULLL`.

I implemented **one move per turn** and flagged it. Hanging off it: **no budget is declared**
(§9 says "the cap is the budget, not the clock"; §5.3's control is "fifty wall bumps" — fifty is a
control, not a parameter). I declared 60 per level and wrote it into every bundle.

### …and a fourth, found only by diffing, which is the most concrete of all

**`step()`'s first return value: a POSITION, or a STATE? Pure, or mutating?**

The brief freezes **"the position after the action"**. The frozen code returns a **state dict** and is
**pure**. Mine returns a **coordinate** and **mutates**.

```
frozen step -> (dict, 'pushed')     keys: boxes, cols, player, rows, targets, walls
mine   step -> ((1, 2), 'pushed')   mutates in place: True
```

Both return two values. Both satisfy "not three". **They are not interchangeable.** The brief's note
— "an entrant got this wrong once and every call raised" — is about the *arity*, and a wrong arity
raises on the first call. **A wrong *type* produces a plausible wrong number for the entire run.**
Neither of us could have seen this from inside our own implementation.

---

## 4. WHAT I THINK IS WRONG IN THE FROZEN ARTIFACTS

### **`levels/03_the_corner_waiting.txt` does not exist, and the two artifacts describe different third levels.**

```
$ ls sokoban/levels/
01_one_push.txt  02_two_boxes.txt
```

The brief freezes "1, 12, and 6 moves" and names `03_the_corner_waiting.txt`. Dossier §7 names the
third level **`03_unsolvable`** and says it is **"NOT WRITTEN"**. The read grammar §6 pins two.

**I verified 1 and 12 against frozen bytes. For 6, I had to author the level.**

```
sokoban2/levels/03_the_corner_waiting.txt   sha256 2d8c46733bd04b9a3333d30e56442c03fffe3e5f4ee4bc95202ac01c463c9284
#######
#.  $ #
#  @  #
#######
optimal 6, plan RRULLL — proven by exhaustive BFS over all 26 reachable states
```

It carries the faculty by construction: `U` then `R` puts the crate in the right-hand corner where
nothing can ever move it again. **The `6` is now attached to bytes. But the bytes are mine, not
frozen** — and they did not exist when the number was written.

### **The dossier's reason for not writing level 03 no longer holds.**

> *"To claim a level has no solution, you must be able to prove it — which requires a solver. The
> project hasn't built one."*

I built one in ~60 lines of stdlib. It verified 1 / 12 / 6 in 0.34 s total (2, 329, 26 states). For a
level small enough to be a cabinet level, *unsolvable* is provable by exhausting the state space.
**`03_unsolvable` can be written and proven today.** I did not write it — the brief freezes a
*solvable* third level and I will not add a fourth to a frozen set on my own authority — but the "we
cannot" should be struck.

### **The frozen CLI exits 1 on every real invocation. Reproduced here.**

```
$ python3 sokoban/sokoban.py --self-test
ALL CONTROLS PASS   --  49/49                                    exit 0

$ python3 sokoban/sokoban.py --level levels/01_one_push.txt --moves R
KeyError: 'unrecognised'   (sokoban.py line 348)                 exit 1
```

That second command solves the level. The crash is in the `print`, **after the game is over**. So `1`
already carries two other meanings in this project — *unsolved* and *controls failed* — and the
all-green self-test is what makes it credible. The `49/49` is true; the CLI is the part that is broken
and the self-test is the part that never reached it.

### **`unrecognised` and `not_an_action` are two names for one counter, in one frozen set.**

Read grammar: `not_an_action`. Dossier §5.3 and §6: `unrecognised` — including in the section that
calls the bug the whole project in one paragraph. `sokoban/MANIFEST.txt` records the consequence and
`PROPOSED-FIX-line348.diff` is the one-line fix, applied to "a separate labelled copy, not here".

### **The frozen instrument can lose the player off the edge of its own board.**

On an unenclosed level, out-of-bounds is not a wall, so it is walkable (see G9 in Part Two). The
player reaches row 4 of a 4-row board; `render()` iterates `range(rows)`, so it is simply not drawn.
**The game continues on a board that no longer contains the player.**

### **A level with two players parses silently.**

The frozen `parse()` overwrites `player` for each `@`, so the **last** one wins. Dossier §8 group [2]
is titled "A MALFORMED LEVEL IS AN ERROR, NOT A BOARD".

---

## 5. WHAT I DID NOT DO

- **No model played.** No GPU, no server, no weights. The `model` entrant is built and its admission
  path is exercised, but no number in this report is a model number.
- **I did not pick the score.** Five candidates rank my own field five ways; choosing one is your call,
  not mine.
- **I did not resolve any ambiguity by peeking.** Where the contract does not speak, the code decides,
  marks the decision `[G<n>]`, writes it into the bundle, and argues it in
  `SOKOBAN2_AMBIGUITIES.md`. If you rule differently, each one is a one-line change plus a re-run.
- **I did not change anything frozen.** `sokoban/` is untouched; `git status` shows only `sokoban2/`.

## Where to start

**Settle G1.** It is the only counter that can see the faculty, and right now it cannot see anything.
Two implementations disagree on 11 of 22 abstention-shaped words, from identical bytes.

**Then G23** — `step() -> (position | state, word)`; pure or mutating. It is a one-line amendment to the
read grammar and it is the difference between two implementations that can be reconciled and two that
cannot.

**Then G15** — until the score is defined, this cabinet cannot produce the milestone dossier §12
names, because the number is still being chosen.
