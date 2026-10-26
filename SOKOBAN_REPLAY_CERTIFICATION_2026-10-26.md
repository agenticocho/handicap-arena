# SOKOBAN — REPLAY CERTIFICATION: EVERY `SOLVED` NOW CARRIES A PLAN A SEPARATE PROCESS EXECUTES

**Card `t_5cd7649a`.** Pre-registration `PREREG_sokoban_replay_certification.md`, commit `41e12aa`, **written
and committed before the verifier existed**. Authority: the card itself, which names the instrument and the
measurement; no ruling is requested for code work.

**Landed on `main`.** The rows below were produced from:

```
driver        sokoban_run.py          74075 B  54514db62d4c86b0…   (was 64146 B dd25eb53… at the base)
verifier      sokoban_replay.py       24118 B  1dc7a6cc9ad8fac4…   NEW
enforcer      check_sokoban_replay.py 27048 B  cb2d92693a8eae12…   NEW
base rate     sokoban_base_rate.py    13982 B  79fd1fe75046e13e…   NEW
simulator     sokoban.py              24872 B  00996929972b9483…   UNCHANGED (frozen, imported, never edited)
levels        01/02/03                18/45/48 B db6ca596…/7549657f…/77d18407…   UNCHANGED
```

---

## 1 THE GAP, AND WHAT NOW CLOSES IT

`sokoban_run.py` scored a cell with `r = S.play(level, tokens)` and put `r["solved"]` in the row. **The process
that played the plan was the process that asserted the score**, and nothing re-executed it: a row saying
`solved: true` was a claim about a computation a later reader could only re-run by reconstructing the plan from
the turn list by hand.

Every row now carries three blocks, produced by two different processes:

| block | what it is | who produced it |
|---|---|---|
| `plan` | the emitted **token stream**, in order, lossless — `{tokens, actions, derivation, sha256}` | the driver |
| `replay` | the verdict of `sokoban_replay.py`, run as a **subprocess**: `{verdict, exit_code, level_sha256, moves, solves_at_ply, blocked, pushes, cross_check, refusal_reason, verifier}` | a separate process |
| `provenance` | the **compute path** and the **driver revision**: `{compute_path, driver_sha256, driver_git_commit, simulator_sha256, replay_verifier_sha256, measured_at_*}` | the driver, from the files on disk |

and **`solved` is now the conjunction** `solved_simulator_claim AND replay.verdict == VERIFIED`, with
`solved_simulator_claim` and `solved_downgraded_by_replay` beside it so the downgrade can never be silent. A row
may not claim a solve its own replay refuses; if the two ever disagree the row says `ended: solved_unverified`
and `ended_why` names why.

**The failure paths carry the blocks too, as `NOT_ATTEMPTED`.** A field that is absent on some rows and present
on others cannot be told apart from a field that was never computed — the same class as a blank class name — so
absence is not used to mean anything here.

**The verifier is not a second copy of the driver.** It has its own parser and its own transition rule, written
from the level spec; it reads the level **from disk**, never from the row; and it **cross-checks the frozen
simulator ply by ply**, comparing every intermediate board rather than only the endpoint (two interchangeable
crates can reach the same final board by different routes).

---

## 2 THE REPLAY VERDICTS — the whole corpus, re-executed

All 24 records that carry a `solved` field were replayed by the separate process. **Five claim a solve; five
VERIFY; nineteen claim no solve and nineteen are refused; zero rows disagree with their own replay.**
**Not one row file was edited** — the historical rows are certified by re-execution and stay byte-identical.

| row | claim | plan (tokens) | moves | blocked | solves at ply | verdict | rc |
|---|---|---|---|---|---|---|---|
| Ministral-3-3B · 01 | **true** | `R` | 1 | 0 | 1 | **VERIFIED** | 0 |
| Ornith-1.5-9B · 01 | **true** | `D R` | 1 | **1** | 2 | **VERIFIED** | 0 |
| Bonsai-2-4B · 01 | **true** | `R` | 1 | 0 | 1 | **VERIFIED** | 0 |
| Bonsai-2-9B · 01 | **true** | `R` | 1 | 0 | 1 | **VERIFIED** | 0 |
| granite-3.3-2b · 01 | **true** | `U U R` | 1 | **2** | 3 | **VERIFIED** | 0 |
| Mellum-12B · 02 | false | `""` | 0 | 0 | — | REFUSED `not_solved` | 3 |
| Mellum-12B · 03 | false | `R` | 1 | 0 | — | REFUSED `not_solved` | 3 |
| MiMo-9B · 01 / 02 / 03 | false | `""` / `RR` / `RRR` | 0/2/3 | 0 | — | REFUSED `not_solved` | 3 |
| Ministral-3B · 02 / 03 | false | `R` / `R` | 1 | 0 | — | REFUSED `not_solved` | 3 |
| Ornith-9B · 02 / 03 | false | `""` / `RDDD` | 0/1 | 0 | — | REFUSED `not_solved` | 3 |
| Qwen3.5-9B · 01 | false | `""` | 0 | 0 | — | REFUSED `not_solved` | 3 |
| Qwythos-9B · 02 / 03 | false | 40×`R` | 4/3 | **36/37** | — | REFUSED `not_solved` | 3 |
| Bonsai-2-4B · 02 / 03 | false | `R` / `R` | 1 | 0 | — | REFUSED `not_solved` | 3 |
| Bonsai-2-9B · 02 / 03 | false | 11×`R` / 8×`R` | 4/3 | 6/5 | — | REFUSED `not_solved` | 3 |
| Triumvirate · 02 / 03 | false | 9×`R` / 31×`R` | 4/3 | 5/28 | — | REFUSED `not_solved` | 3 |
| granite-3.3-2b · 03 | false | `URRR` | 4 | 0 | — | REFUSED `not_solved` | 3 |

**THE TWO ROWS THAT MATTER MOST ARE THE TWO THE OLD SCORE COULD NOT CHECK.** `['D','R']` and `['U','U','R']`
both solve level 01 — and both contain **blocked attempts before the push**. A verifier that trimmed the plan to
"the successful actions", or that assumed the solve is at ply 0, would have agreed with three rows and been
**wrong about two**. This is why the plan is stored as the token stream and not as a move string.

Level 01 separates nothing — it is one push at every size — so five of five solves on it is not a capability
result either. It is, however, the only level on which any row in this cabinet has ever claimed a solve, which
is exactly why the claim needed a verifier: **the entire existing solved corpus is one-push rows.**

---

## 3 THE MUTATIONS — each caught, with its non-zero exit

The card names three. All three fire. Every verdict below is the separate process's own exit code.

**M1 — a plan STEP mutated.** The last ply of each known-good plan was flipped (`R→U`, `R→U`, `U→D`):

```
01_one_push        R→U    REFUSED rc 3  (not_solved)
02_two_boxes       R→U    REFUSED rc 3  (not_solved)
03_the_corner_waiting U→D REFUSED rc 3  (not_solved)
```

**M2 — a BOX POSITION mutated.** Every one-cell box move on every level was generated *keeping the level a
level* (a box written onto a `.` becomes `*`, not `$`), and each mutation was replayed with the **same plan**:

```
01_one_push          1 mutation   0 refused by replay   1 SURVIVED
02_two_boxes         6 mutations  3 refused by replay   3 SURVIVED
03_the_corner_waiting 3 mutations 2 refused by replay   1 SURVIVED
```

**AND THE SURVIVORS ARE THE FINDING, NOT A FAILURE — the first fixture this file carried was one of them.** My
first M2 moved level 02's lower crate from (3,3) to (3,4) and expected a refusal; **the 12-move plan still solved
the level**, because the crate now needs two pushes and the plan's third push is simply blocked, landing it on
the target anyway. A mutation the plan survives is not a control. So the harness now *classifies* every mutation
and reports the survivors by coordinate instead of quietly swapping in one that fires. **Level 01 admits no
firing mutation at all**: its crate has exactly one free neighbour and it is the target, so a one-cell move
either puts the crate *on* the target (the level is solved before the plan starts, and `R` keeps it solved) or is
impossible. That impossibility is declared in the harness (`M2_EXPECT_REFUSAL`), so a mutation that *stops*
firing on levels 02/03 is still caught while a mutation that *cannot* fire is not demanded.

**M3 — a CLAIMED SOLVE changed, both directions.**

```
a VERIFIED plan relabelled solved=false   -> verifier rc 0 VERIFIED, claim_matches_verdict FALSE   (caught)
an UNSOLVED plan relabelled solved=true   -> verifier rc 3 REFUSED row_claims_solved_but_plan_does_not
                                             enforcer over a corpus holding it: rc 1
                                             same corpus with the claim restored: rc 0
```

The last two lines matter as much as the first: **the enforcer's rc 1 is caused by the mutation and not by the
copy, the directory, or the run** — the identical corpus with the claim restored exits 0.

**THE CROSS-CHECK CAN FIRE.** `SOKOBAN_REPLAY_FAULT=independent-step` breaks this file's own transition on
purpose (a push moves the crate and leaves the player behind). The verdict becomes `CROSS_CHECK_DISAGREES`,
rc **5**, `fault_injected` names the fault, and the same plan without the fault is VERIFIED — so the difference
is the fault and nothing else. Without this arm the per-ply cross-check would be decoration.

**THE DRIVER'S OWN FUNCTION, NOT A COPY OF IT.** `solve_certificate()` — the function `run()` calls on every
loaded cell — was exercised on a real historical row: it returns `solved=True`, `replay=VERIFIED`, and a plan
identical to the row's own turn stream; `provenance.compute_path == "cpu"` with the driver's on-disk digest; and
the row **as written** round-trips through `sokoban_replay.py --row` to the same verdict. A claim the replay
refuses is downgraded: `solved=False`, `ended="solved_unverified"`, `solved_downgraded_by_replay` naming the
reason.

---

## 4 THE BASE RATE, RE-DERIVED IN-CABINET

Not by running the peer's script. `sokoban_base_rate.py` enumerates **every word of length 1..8 over the frozen
action order U D L R** — Σ 4^L = **87 380** — repeats each word to the cap to form a **periodic plan**, and
replays it against the three frozen levels with the verifier's transition rule.

Two countings, both printed, because the peer published two numbers and they are two readings of one thing:

- **GENEROUS** — the level is solved at any ply of the repeated plan.
- **STRICT** — the *first* solve falls exactly on a period boundary.

```
cap 40 (the cabinet's own --cap)       GENEROUS   STRICT   shortest period that clears it
  01_one_push                           77540      3280     1   (R)
  02_two_boxes                            198        24     7   (UURDDRL)
  03_the_corner_waiting                    76        28     6   (RULDLU)
  all three (GENEROUS)                      0

best by the peer's ranking (strict, generous, then shortest period):
  RULDLU   period 6   strict 1/3   generous 2/3          <- reproduced exactly
```

**THE FIVE PEER NUMBERS REPRODUCE BYTE FOR BYTE**: 87 380 · 77 540 · 198 · 76 · 0, and the best plan is
`RULDLU`, period 6, 1/3 strict and 2/3 generous. 77 540 is not a coincidence: level 01 is one push, every non-`R`
move from its start is blocked, so a word clears it **iff it contains an `R`** — Σ(4^L − 3^L) = 77 540, which the
harness now asserts rather than observes.

**AND THE CARD'S OWN PREMISE IS WRONG ON ONE POINT, MEASURED.** The card says *"a fixed six-move cycle clears
level 01 alone"*. It does not: `RULDLU` clears **01** (at ply 1, inside its first period) **and 03** (at ply 6,
exactly on its period boundary) — **two of three**, and the level it cannot touch is **02**. `strict 1/3 ·
generous 2/3` is exactly that: only 03's solve lands on the boundary.

**IS `RULDLU` OPTIMAL? Both answers, because they are different questions:**

- **By coverage, yes.** The shortest period that clears *two* levels is **6, and exactly one word attains it —
  `RULDLU`**. Nothing of period ≤ 5 clears two levels, and nothing of period ≤ 8 clears all three.
- **By the period needed to clear level 01, no.** Period **1** (`R`) clears 01. `RULDLU`'s period 6 is the
  optimum for level **03** — the same 6 the solver proves optimal by complete enumeration — not for 01.

**AND A PERIODIC PLAN IS NOT A SOLVE CERTIFICATE, which the two tools disagree about on purpose.** The
shortest cycle that clears 02 has period **7** (`UURDDRL`) but solves at **ply 24** of a 40-ply repetition, after
wandering; the verifier **refuses** that 40-ply repetition as `solved_before_the_plan_ended`. The base rate
measures coverage of the periodic universe; a certificate requires the plan to *end* at the solve. `RULDLU` on
03 is both — solve at ply 6, period 6 — which is precisely why it is the one cycle that is also a plan.

**CAP SENSITIVITY (a reading, not an assertion; the assertions are taken at cap 40):**

```
   cap    01     02    03  all three
    12  77540      0    72          0
    24  77540     22    76          0
    40  77540    198    76          0
    64  77540    198    76          0
    96  77540    198    76          0
```

**P11 predicted the peer's `198`/`76` would reproduce at at most one cap. That prediction FAILED, and it failed
in the direction that makes the peer's numbers stronger:** the counts are cap-invariant from 40 upward and move
only below it (a cap too tight to let a cycle finish). So `198` and `76` are a property of the periodic plans at
the cabinet's declared cap, not an artefact of a particular budget.

---

## 5 COMPUTE PATH AND DRIVER REVISION, PER ROW

Every row now carries `provenance`, and the failure paths carry it too:

```
compute_path               cpu
compute_path_note          "Sokoban's score is a SEARCH over a frozen simulator -- no model call computes it.
                            The model emits one letter per turn; sokoban.play() scores the stream and
                            sokoban_replay.py certifies it, both on CPU. The serving process's own compute
                            path is recorded separately in config.n_gpu_layers."
driver_file / driver_bytes sokoban_run.py / B
driver_sha256              54514db62d4c86b0…        <- what actually determines the score
driver_git_commit          recorded per row, beside driver_git_dirty (restricted to the driver, the
                           simulator and the verifier) and driver_git_source
simulator_sha256           00996929972b9483…        <- the frozen rule
replay_verifier_sha256     1dc7a6cc9ad8fac4…        <- the second opinion
measured_at_unix / _local  per row
```

**Why both a commit and a digest.** The card's own measurement is the reason: the live driver was 64 146 B
`dd25eb53…` while the peer measured 35 909 B `2d3da54d…` at `2bb33058` — and the commits-behind count has already
moved from 301 (card) to **302** (re-derived here) because other agents commit to this tree while a worker runs.
A commit names a tree that moves; **a digest names the bytes that produced the score.** Both travel, and the
dirty list is restricted to the three driver-relevant files so that an unrelated agent's edit does not appear as
a defect in this cabinet's row.

---

## 6 THE CONTROLS: WHAT FIRED, AND WHAT REPAIRED

Repo controls, **rc before → after**: `sokoban.py --self-test` 0→0 (49/49) · `sokoban_solver.py` 0→0 (67/67) ·
`sokoban_report.py --self-test` 0→0 · `check_conformance_census.py` 0→0 · `check_report_buckets.py` 0→0 ·
`make_conformance_package.py` 0→0 · `test_no_silent_zero.py` **1→1** · `test_declared_root.py` **1→1**. The last
two were already failing at the base and were not touched; they are named so neither their failure nor a repair
could be spent as evidence here. New: `check_sokoban_replay.py` 24/24 controls, rc 0 · `sokoban_base_rate.py`
9/9 assertions, rc 0.

**THE FIELD CENSUS FIRED, EXACTLY AS PRE-REGISTERED (P12).** With the driver emitting five new names and the
census carriers untouched, `check_conformance_census.py` returned **rc 1** naming them:

```
DIRECTION 1 -- EMITTED BY THE WRITER, UNNAMED BY THE PACKAGE:
  plan  provenance  replay  solved_downgraded_by_replay  solved_simulator_claim      (sokoban_run.py:989)
```

It then returned **rc 0** once the five were declared in `make_conformance_package.py`'s `FORMAT` and in the
package's `LIST 1` (now 57 names, identical in both carriers). **That firing is the control working, not
breakage: it is what stops the record widening silently, and it is the reason this change could not have landed
quietly.** The census's own five-arm control (`check_conformance_census_control.py`) passes rc 0, which is what
establishes that the check can fail for the right reason.

---

## 7 WHAT THIS STILL CANNOT SEPARATE

Stated because a certification that lists only what it proves is the defect this project files.

1. **The second opinion is mine too.** The verifier has its own parser and transition rule, and it is compared
   ply by ply against the frozen simulator — but both are written by the same hand reading the same spec. A
   shared *misreading* of Sokoban's rules would survive the cross-check. What is ruled out is a coding slip in
   one implementation, a plan trimmed of its blocked moves, a level taken from the row instead of the disk, and a
   score asserted by the process that played it. What is not ruled out is that the rules themselves were
   transcribed wrong twice the same way.
2. **The census's grain is the block.** `plan`, `replay` and `provenance` are censused **by name**; their inner
   keys (`plan.tokens`, `replay.verdict`, `provenance.driver_sha256`) are *not* — there is no `SITE` for them, so
   a rename *inside* one of those blocks would not be caught by `check_conformance_census.py`. That is the next
   enforcer this cabinet needs, and it is named here rather than left for a reader to discover.
3. **The historical rows are certified retrospectively.** Their `plan`/`replay` fields do not exist; the enforcer
   reconstructs the plan from `turns[].token`. That is honest — the files are byte-identical — but it means a
   historical row is certified by *this* instrument today, not by the instrument that wrote it.
4. **Five solved rows, one level, one push.** Nothing in this cabinet has ever demonstrated a multi-move solve by
   a model. The certificate makes a `SOLVED` unfalsifiable-proof; **it does not make one more likely**, and the
   frontier is still 0 of any level beyond 01.
5. **The base rate is a universe, not a rate.** It covers periodic plans of period ≤ 8 at cap 40 and says nothing
   about non-periodic plans or longer periods. `198` is not a solve rate for models; it is the size of the set of
   six-to-eight-letter cycles that eventually clear level 02.
6. **One mutation cannot be made to fire** (level 01's box), declared in the harness with the geometric reason.
7. **No model was run.** No new entrant rows, no GPU, no lease: the certification is CPU-only code work, as the
   card requires.

---

## 8 THE PRE-REGISTRATION, SCORED

| # | prediction | verdict |
|---|---|---|
| P1 | all five solved rows VERIFY, including the two with blocked leading moves | **PASS** — 5/5 rc 0, `blocked` 1 and 2 |
| P2 | a mutated plan step → rc 3 naming the ply | **PASS** — 3/3 levels |
| P3 | a mutated box position, same plan → rc 3 | **PASS with a correction** — 5 of 10 mutations fire; 5 are *survivors* the plan still solves (the first fixture was one), now classified and printed |
| P4 | a flipped claimed solve → enforcer rc 1, verifier rc 3 | **PASS** — both directions |
| P5 | known-good plan on each level verifies | **PASS** — 1, 12, 6 moves |
| P6 | the cross-check agrees, and can fire (rc 5) | **PASS** — fault arm rc 5, clean arm rc 0 |
| P7 | universe 87 380; level 01 = 77 540 = Σ(4^L−3^L) | **PASS** |
| P8 | `RULDLU` clears 01 at ply 1 and 03 at ply 6 — so **the card's "01 alone" is false** | **PASS** — and the card's premise is corrected: 2 of 3, not 1 |
| P9 | `RULDLU` is not optimal by period (period 1 clears 01) | **PASS** — and it *is* optimal by coverage (period 6, unique) |
| P10 | zero words clear all three | **PASS** — 0 at every cap tested |
| P11 | the peer's 198/76 reproduce at at most one cap | **FAILED** — they are cap-invariant from 40 upward; the peer's numbers are *stronger* than predicted |
| P12 | the census enforcer fires on the five new names, then goes green | **PASS** — rc 1 naming all five, rc 0 after declaration |
| P13 | no frozen level is edited | **PASS** — digests unchanged |

**Two things this measurement got wrong, named rather than tidied:** the first M2 fixture did not fire and the
first level-01 mutation *could not* fire (P3), and P11 was simply wrong about cap-dependence (P11). Both were
found by controls that were allowed to fail.

---

## 9 WHAT A READER SHOULD NOW BE ABLE TO DO

- Take any row this driver writes and re-execute its solve **without asking the driver**:
  `python3 sokoban_replay.py --row probes/<row>.json` → rc 0 only if the plan really solves that level.
- Take any corpus and find every row whose claim its own plan does not support:
  `python3 check_sokoban_replay.py --corpus probes` → rc 1 if any row overstates or understates.
- Re-derive the rung's base rate in-cabinet, with the assertions that make it checkable:
  `python3 sokoban_base_rate.py` → rc 1 if the period-6 result or the 77 540 identity stops holding.
- Read, on every future row, which **compute path** and which **driver bytes** produced the number.
