# Certification register — eight cabinets, verified against their artifacts (2026-10-26)

**Who:** Ocho (CFO), card `t_925f606f`. **What this is:** the gate that had to pass before a single
entrant was scored. Every verdict below was reached by **running the cabinet's own control in my own
process** and by **breaking the thing the control measures to watch it go red** — not by reading the
owner's summary. Where I could not make a control fail, the cabinet is reported unmeasured.

**Method note, because it decides how strong each verdict is.** Two different kinds of evidence appear
below and they are not interchangeable:

* **closed by test** — I executed the control and read its exit status, or I induced the defect myself;
* **closed by reading** — I read the producer's code and the row it wrote; this is the weaker claim and
  is labelled as such wherever it is all I have.

Every command below was run with the exit code captured directly (`out=$(cmd 2>&1); rc=$?`) — never
through a pipe, whose status is the last stage's.

---

## 0. Which copy of each instrument is the certified one (measured, not assumed)

A certification is about a FILE. The trunk and the cabinet trees hold different revisions of several
drivers, so before scoring anything I matched the file I would run against the digest the certification
card recorded. **This is the check that caught the snake divergence.**

| cabinet | certified file (trunk unless stated) | bytes | sha256 (16) | matches the card |
|---|---|---|---|---|
| chess | `chess_game.py` @ `ce3cd21` | 44,726 | `9f16d1cb2606c002` | yes (t_3adf479b) |
| mastermind | `probes/mastermind/mastermind_run_onefile.py` @ `53d4028`/`b5da9b7` | — | `9babe6cded17025b` | yes — and the row names its own instrument digest |
| lightsout | `lightsout_cabinet.py` @ `e1040a2` | 10,193 | `8ed4eab8159410ec` | yes |
| snake | **`cabinet/snake/snake_run.py` @ `149d0d0`** | 42,349 | `c2aabbafbc9b…` | **NO on the trunk** — trunk holds `a4fc47ce447d39e2` (44,256 B), a divergent sitting-2 revision |
| labyrinth | `labyrinth_run.py` @ `502b38b` | 168,649 | `24899ca87f89a6b9` | yes |
| sokoban | `sokoban_run.py` @ `2e4ccd3` | 74,075 | `54514db62d4c86b0` | yes (and `sokoban_replay.py` `1dc7a6cc9ad8fac4`, `check_sokoban_replay.py` `cb2d92693a8eae12`) |
| zork | `zork.py` `b9701007d6e186d5`, `zork_run.py` @ `6c426e5` | 81,096 | `b26b2cfc42a0a915` | yes |
| missile-command | `scripts/check_mc_claims.py` @ `733eea3`; driver `missile_command_run.py` | — | — | yes |

**The snake divergence is a finding, not a footnote.** The trunk's `snake_run.py` accepts
`--ngl/--ctx/--parallel` and does **not** write `score.revisits`; the certified copy hardcodes
`-c 65536 -ngl 0` (CPU-only, `server_argv()` at snake_run.py:242) and **does** write it. Pass 1 of the
window ran the trunk copy. Those four blocks are reported **INSTRUMENT-FAILURE** and stand beside pass 2,
which re-ran the certified copy.

---

## 1. chess — **CERTIFIED** (closed by test)

*Required control:* `e2e4` accepted, `e4d5` rejected, reported count == the engine's own list.

* **Ran it myself** (`verify/chess_induce.py`, rc 0): `run_controls()` → all four controls PASS.
* **Made it fail** — `control_3_check` returns False on a row reporting `legal_count=5` with a 2-move
  list against an engine list of 20; False on the wrong side to move (Black's moves against a
  white-to-move FEN); False on a truncated list. Green on the engine's own row.
* **In the producing process** (closed by reading, plus the artifact): `play()` calls `run_controls()`
  *before any termination is trusted*, `_CONTROLS_PASSED` gates the `illegal-move` label, and the
  artifact carries the four controls. All four window artifacts carry them, all PASS.
* **The count anchor is external**: 20 legal moves at startpos and 29 after 1.e4 e5 are published chess
  constants asserted independently of the engine call — that is what stops control 3 being a tautology
  (its *row* is still built from `legal_moves`, so it confirms agreement, not engine correctness).
* **What it cannot separate** (owner's measured position, carried): a model still deliberating at the
  token cap from one that committed no move; and `illegal-move` sits outside `CARD_chess.md`'s frozen
  taxonomy — it needs ratification before those rows are scored.
* **Reading hazard I hit and then resolved, kept in the record:** the window's ministral row says
  `illegal-move … the model's first line is 'e2e4' … IS NOT a legal move`, while the same artifact's
  control_1 shows `e2e4` **is** legal at startpos and row 0 shows it **played**. Both are true: the
  illegal move fired at **ply 1**, where Black answered `e2e4` again and nothing sits on e2. The
  reason string names neither the ply nor the FEN, so the artifact reads as a self-contradiction until
  the rows are counted. **Recommended to the owner:** put the ply and FEN in the termination reason.

## 2. mastermind — **CERTIFIED** (closed by test)

*Required control:* a control block proven both passing **and** failing.

* `python3 probes/mastermind/test_mastermind_controls.py` → rc 0, twelve OK lines. Each of the five
  controls is exercised in **both** directions: scripted arm 16/16 and 0/16 when broken; broken arm 0/16
  and 16/16 when consistent; disagreements 0 and 1 when a stored flag is flipped; 10 distinct per-turn
  digests and a constant digest detected; per-state null `[1.0, 0.482, 0.198]` and a constant null
  detected.
* **In the producing process:** the runner calls `run_control_block()` before row production and
  **aborts at exit 2** if it fails (`mastermind_run_onefile.py:487-493`). All four window blocks printed
  `CONTROL BLOCK PASSED`; their summaries report `stored_vs_recomputed_disagreements = 0` and 10
  distinct prompt digests.
* **What it cannot separate:** whether a model reads feedback (ignition) or emits a fixed opening book.
  The control certifies the instrument, not the model.

## 3. lightsout — **CERTIFIED** (closed by test)

*Required control:* truth recomputed at load; four mutations caught (two of which historically survived).

* `python3 lightsout_cabinet_control.py` → rc 0: unmutated copies pass (rc 0); board-id mutation,
  `correct` field A1→B2, prose answer cell A1→C3, whole-file substitution — **all four refused, rc 1**.
* **In the producing process** (closed by reading + the rows): `arm2_3x3_same_conditions.py` recomputes
  `truth = solve_set(b)` at load, asserts the solution is unique, **asserts the fixture's `correct` label
  equals the computed solution**, and derives the verdict from the presses applied to the board. Every
  window row carries a recomputed `truth`; the claim/state split is visible in the result: **16/16
  claimed SOLVED, 0–1 of 16 actually cleared**.
* **Honest limit about my own check:** the cabinet's `--controls` block is a *separate* process from the
  producer; what is in-process is the truth recomputation, which is the property that matters here.
* **What it cannot separate:** a deliberating model from one that committed no move; and a label that is
  right by luck from one recomputed right. 3x3 cannot exercise unsolvability at all — every board is
  solvable; only 4x4 can.

## 4. snake — **CERTIFIED WITH A PROVENANCE FINDING**

*Required control:* seed-sensitivity + apple reachability, or label levels unscoreable.

* `snake_seed_sensitivity.py` rc 0: **the control has a genuine contrast** — the eating policy's chain
  digest differs across seeds 1/7 (`05ec38c631bad848` 9 apples vs `20b384451cbb894a` 8 apples), and the
  non-eating policy's digest is identical (`af12a0c5d14ce52f`, 0 apples both). Without the eating arm the
  test would certify a constant.
* `snake_reachability.py` rc 0: first apple reachable in 20 computed steps against a cap of 120; all four
  seeds SCORABLE; `unscoreable_levels: []`.
* `snake_digest_claim.py` rc 0: bonsai GPU chain == published CPU chain (`7f46665eb1a91edf`) — and the
  file says in its own words that equality is **not** evidence of capability (0 apples both).
* **The finding:** the certification lives in `cabinet/snake @ 149d0d0`, not on the trunk. Pass 1 of the
  window ran the trunk copy and produced rows **without** `score.revisits`; those rows are
  INSTRUMENT-FAILURE. Pass 2 ran the certified copy (`c2aabbaf…`), whose rows carry
  `score.revisits` (e.g. 95 of 120 ticks). The certified driver is **CPU-only by
  construction** (`-c 65536 -ngl 0`), so snake is scored as a CPU cabinet in this window — see §7 of the
  window report for the tenancy deviation this creates.
* **Coverage, stated rather than rounded up:** the certified pass completed for **2 of 4 entrants**
  (ministral 75 s, ornith 454 s). mimo did not complete a two-seed block in 16 minutes and was stopped;
  bonsai was not started. Those two are reported **unmeasured**, and their pass-1 trunk-copy rows stand
  beside them as INSTRUMENT-FAILURE.
* **What it cannot separate:** whether a model reads the board or emits a constant; and a 0-apple episode
  makes chain equality uninformative about the model.

## 5. labyrinth — **CERTIFIED** (closed by test, including an induction I wrote)

*Required control:* legal / blocked / UNATTRIBUTABLE separated per row, plus a position census.

* `labyrinth_control.py` rc 0 and `labyrinth_run.py --self-test` rc 0 (corridor: 40 legal / 40 distinct;
  wall-pusher: 40 blocked / 0 legal; `Zorgblat` → `not_an_action`).
* **I made it fail** (`verify/labyrinth_induce.py`, rc 0): with `neighbours()` returning ∅ the corridor
  control goes red (`blocked=1, distinct=0`, `pass=false`); with a fully connected graph the wall-pusher
  goes red (`39 blocked / 1 legal`, `pass=false`); restoring the function bit-identically returns the
  control to `pass=true` with a row **equal** to the unmutated one.
* **In the producing rows:** every row carries `legal`, `blocked`, `UNATTRIBUTABLE`, `distinct_positions`,
  `revisit_count` and `counts_basis`; there is no aggregate that hides the unattributable class.
* **Sequencing defect of mine, kept in the record:** pass 1 refused all four entrants with **exit 11 —
  "identity card … is missing quant"** in 0.1 s, no artifact, no model call. That was my wrapper, not the
  cabinet; the cabinet failed closed with a named exit code before spending a token. Pass 2 fixed it.
* **What it cannot separate:** a blocked proposal from a model that named a non-neighbour rune by intent;
  UNATTRIBUTABLE only covers tokens outside the 24-rune alphabet; deliberating-at-cap from no move.

## 6. sokoban — **CERTIFIED** (closed by test)

*Required control:* every SOLVED carries a replayable plan that a separate process re-executes
(+ mutation test).

* `python3 check_sokoban_replay.py` → rc 0, **24/24 controls**. The corpus itself is the strongest
  evidence: **19 REFUSED / 5 VERIFIED, 0 disagreements** — the verifier refuses real plans, not only
  mutants, and every claim matches its replay.
* **In the producing rows:** all 12 window rows carry `plan` + `replay` + `provenance`;
  `solved` is the conjunction (`solved_simulator_claim AND replay == VERIFIED`). Two entrants solved
  level 01 and replayed VERIFIED; the rest were REFUSED and counted not-solved.
* **What changed because of it** (this is the instrument doing work): sitting 2 recorded bonsai-9b as
  **solved=True on level 01**; under the replay verifier that same cell is **REFUSED**. A published
  solve did not survive re-execution.
* **What it cannot separate:** a second opinion that shares the same reading of the spec; the census grain
  is the block (inner keys of plan/replay/provenance are not censused); five solved rows, one level.

## 7. zork — **CERTIFIED** (closed by test)

*Required control:* accepted / rejected / unattributable commands; progress from world state, not prose.

* `zork.py --self-test` rc 0 (**175/175**), `zork_controls.py` rc 0 (**93/93**),
  `zork_run.py --self-test` rc 0 (**64/64**). Several of those assertions are explicitly
  "THE OLD CALL WOULD HAVE MISMATCHED" — i.e. the fix is proven to be visible.
* **In the producing rows:** `attribution = {accepted, rejected, UNATTRIBUTABLE}` counted per row, with
  `attribution_checked_against_counts: true`; progress is read from the room graph
  (`rooms_visited` / `rooms_reachable_from_start`), not from the transcript.
* **What it cannot separate:** a shared misreading between the parser and the replayer; `host_block()`
  carries no hostname, so two identically configured boxes are byte-identical in the records.

## 8. missile-command — **CERTIFIED, CPU-side** (closed by test)

*Required control:* name the 115th check, make it fire or delete it; honest denominator.

* `scripts/check_mc_claims.py` **bare → 12/12 rc 0**; `--denominator → 13/13 rc 0`;
  `--denominator --mutations → 17/17 rc 0`. The card's "17/17" reproduces **only under the invocation the
  audit's own guard line names** (`run_guarded.sh mc-claims … --denominator --mutations`); a reader who
  runs it bare sees 12/12 and may think the count is wrong. Recorded as a reporting hazard, not a defect.
* **The mutation matrix fires**: M1–M8/M10 caught by named checks; **M9 (a self-consistent substitution
  on one of the 10 unshared cells) survives and is asserted as the residual**. The demoted check (#114,
  P2 token-for-token replication) is shown falsifiable **both ways**.
* **A boundary I measured and did not assume:** the checker reads a **fixed archive of 22 declared
  coordinates**, not a directory. After the window's eight MC rows it still reports `0 disagreements of
  22 measured rows`: the four cells for mimo-9b/bonsai-9b were re-read (their records were replaced) and
  still agree, while the four new ministral-3b/ornith-9b cells sit **outside** the audited population and
  are not covered by it.
* **Build fact that matters for the tenancy:** this cabinet's frozen compute path is `-ngl 0` (CPU). A
  CPU `llama-server` still allocates a CUDA context — measured **+364 MiB** on the card while an MC block
  ran. "CPU-only" does not mean "the card is untouched."
* **What it cannot separate** (owner's wording, carried): differing token stream vs changed entrant
  bytes; a self-consistent substitution on the 10 unshared cells; a model from a four-line program
  (a trivial policy reaches 100% of the optimum on mc_01 and 50% on mc_02); one run from another (n=1);
  entrant bytes from a file of the same size.

---

## Summary of the gate

| cabinet | verdict | the control I watched fail |
|---|---|---|
| chess | CERTIFIED | control 3 red on wrong count/list/side/truncation |
| mastermind | CERTIFIED | every control demonstrated in both directions (rc 0) |
| lightsout | CERTIFIED | 4 mutations refused, unmutated passes (rc 0) |
| snake | CERTIFIED, provenance finding | eating-vs-non-eating contrast; certified copy ≠ trunk |
| labyrinth | CERTIFIED | my two inductions go red, restore bit-identical |
| sokoban | CERTIFIED | 24/24 controls; 19 of 24 real plans REFUSED |
| zork | CERTIFIED | 175/175, 93/93, 64/64, old-call-mismatch assertions |
| missile-command | CERTIFIED (CPU) | 17/17 under its own invocation; M9 residual asserted |

**Nothing was refused on certification grounds.** What was refused is in the window report: four
labyrinth blocks (my defective identity card), four snake pass-1 blocks (uncertified trunk copy, and the
certified copy does not accept the tenancy flags), and nothing else.
