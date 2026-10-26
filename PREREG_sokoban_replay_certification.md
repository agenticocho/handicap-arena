# PRE-REGISTRATION — EVERY `SOLVED` MUST CARRY A PLAN A SEPARATE PROCESS REPLAYS, AND THE REPLAY MUST BE ABLE TO REFUSE

**Written BEFORE the verifier exists**, in the house form of `PREREG_sokoban_instrument1/2/3/4.md` and
`PREREG_sokoban_report_bucket_enforcer.md`, and for the same reason: **a check whose firing is not predicted
in advance cannot be distinguished from a check that happens to pass.**

**Card:** `t_5cd7649a`, authorised by Mike 2026-10-26. The card names the files to be written
(`sokoban_replay.py`, its checker) and the measurement to be re-derived; the subject is an instrument, not a
model, so no ruling is requested here.

**Base, measured before this file was written** (tree clean at the paths below; the repo's two pre-existing
control failures are listed rather than tidied away):

```
main (local)        b5da9b7   (HEAD when this file was written; other agents commit to this tree concurrently
                              and that is why every row will carry its OWN driver digest, not "the engine")
sokoban_run.py      64146 B   dd25eb53874056e15bd2ec8dd626e9f78d25253cd0dd508eb0c29f821f93c8b6
sokoban.py          24872 B   00996929972b9483223bf54f4dcef007162134289c5cdb76a58533ac875e8a7c
sokoban_solver.py   33371 B   2dbd53c4790c52f67b22e9e8af3a4eb674d48b0815c444ff650846b6f26e4a9e
sokoban_report.py   13088 B   04966f23fcaa91e6326e55f658b7e3fef1462c00fb5d55e856537e46d8b0f8d4
sokoban_batch.py    13663 B   d6604f398b6f6afb9e84998d4a1f3417427af22a914f170b24eeb183d6dee75c
check_conformance_census.py 36076 B  ff4b8d20bb1a054fb2d38650ec3d27f7afe7899814ff6bd7b6ee65e9488f3da6
SOKOBAN_CONFORMANCE_PACKAGE.md 16085 B  b63996d2fb8939562261d699e18d53ccd5d4710a670e8084b413a08234f416d6
levels/01_one_push.txt          18 B  db6ca59655f0d7d1f1ce48e36e0b0c90a3bca5158b96a31a7a4fe37006a6a313
levels/02_two_boxes.txt         45 B  7549657f1768607cefab6d892b1756b1cabf23f51144a7679d76f331b38a57d7
levels/03_the_corner_waiting.txt 48 B 77d18407a001da292b2f1dcf8054ed40ddc2038563f23b96861a362c78cf23d6
sokoban_replay.py   DOES NOT EXIST -- the digest of a file that does not exist is not predicted
check_sokoban_replay.py  DOES NOT EXIST
sokoban_base_rate.py     DOES NOT EXIST
```

**Repo controls at this base, measured** (`python3 <file>`, rc in brackets):
`sokoban.py --self-test` [0] · `sokoban_solver.py` [0] · `sokoban_report.py --self-test` [0] ·
`check_conformance_census.py` [0] · `check_report_buckets.py` [0] · `make_conformance_package.py` [0] ·
`test_no_silent_zero.py` [**1**] · `test_declared_root.py` [**1**]. The last two were already failing before
this card touched anything; they are named here so that neither their failure nor their repair can be spent
as evidence about this change.

---

## 0 THE TWO GAPS, MEASURED RATHER THAN QUOTED

**G1 — `solved` IS ASSERTED BY THE PROCESS THAT PLAYED IT.** `sokoban_run.py:815` computes
`r = S.play(level, tokens)` and the row carries `r["solved"]` as the score. Nothing else re-executes it. The
row keeps `turns[].token` — so the plan is *recoverable* — but no field names it, no second process executes
it, and no row carries a verdict. A row that says `solved: true` is therefore a claim about a computation
nobody can re-run without reconstructing the plan from the turn list by hand. **That is the defect class the
card names: the rate would be measuring the driver's optimism.**

Measured on the corpus that exists: **five rows claim `solved: true`**, all on `01_one_push`, and their
recoverable plans are not uniform —

```
Ministral-3-3B   ['R']          moves 1  blocked 0
Ornith-1.5-9B    ['D', 'R']     moves 1  blocked 1     <- a BLOCKED first move, then the push
Bonsai-2-4B      ['R']          moves 1  blocked 0
Bonsai-2-9B      ['R']          moves 1  blocked 0
granite-3.3-2b   ['U', 'U', 'R'] moves 1 blocked 2     <- two blocked moves, then the push
```

So a verifier that trims the plan to "the successful actions", or that assumes the solve is at ply 0, would
agree with three rows and be wrong about two. **The plan a verifier replays must be the emitted stream, with
its blocked attempts kept.**

**G2 — THE DRIVER IS NAMED BY A NOUN.** The card's own measurement: the live `sokoban_run.py` is 64 146 B
`dd25eb53…`; the copy a peer measured is 35 909 B `2d3da54d…` at `2bb33058`, **302 commits behind HEAD**
(re-derived here: `git rev-list --count 2bb33058..HEAD` = 302, not the card's 301 — the count moved because
the tree moved, and it will move again). Rows today name `config.server_argv` and `server_binary_digest`, which
identify the **serving** process, and nothing about the **driver that computed the score**.

---

## 1 WHAT WILL BE BUILT — THREE FILES, ONE ROW SHAPE, ONE CONTROL SUITE

**`sokoban_replay.py` — the separate replay verifier.** Its own parser and its own transition rule, written
from the level spec, sharing no state with `sokoban.py`; then a **cross-check** against the frozen
simulator's `play()`, because two implementations that agree are a stronger statement than one that is
trusted. It reads **the level from disk**, never from the row under test. Verdicts and exit codes:

```
VERIFIED                  0   the plan replays to a solved board, at its LAST ply, and the frozen
                               simulator's final board agrees
REFUSED                   3   well-formed input, the plan does not verify -- with a NAMED reason
USAGE / NOT A LEVEL       2   a level that is not a level has no solvability
CROSS-CHECK DISAGREES     5   the independent replay and the frozen simulator reach different boards
```

**`sokoban_run.py`** gains exactly one block of work: every row carries

```
plan      {tokens, actions, derivation, sha256}          the replayable plan, lossless
replay    {verdict, exit_code, level_sha256, moves, solves_at_ply, blocked, pushes,
           verifier_sha256, refusal_reason, ...}          THE SEPARATE PROCESS'S VERDICT
provenance{compute_path, driver_file, driver_bytes, driver_sha256, driver_git_commit,
           driver_git_dirty, simulator_sha256, measured_at_*}   COMPUTE PATH AND DRIVER REVISION
```

and **`solved` becomes `solved_by_simulator AND replay.verdict == VERIFIED`**, with the simulator's own claim
kept beside it as `solved_simulator_claim` and `solved_downgraded_by_replay` naming the reason when the two
disagree. A row may not claim a solve its own replay refuses.

**`sokoban_base_rate.py`** — the base rate re-derived **in-cabinet**, not by running the peer's script.

**`check_sokoban_replay.py`** — the enforcer and the mutation harness: it re-executes the verifier over the
whole corpus and over four mutations, and exits non-zero if any control that must fire does not.

---

## 2 PREDICTIONS — EACH ONE CAN FAIL, AND THE FAILURE IS THE FINDING

**P1** All five historical `solved: true` rows VERIFY (rc 0), **including `['D','R']` and `['U','U','R']`**,
with `blocked` 1 and 2 respectively and `moves` 1 on each. *Fails if the verifier trims blocked attempts or
requires the solve at ply 0.*

**P2** Changing **one plan step** in a verified plan yields rc 3 and a refusal whose reason names the ply.
*Fails if the verifier accepts a mutated plan.*

**P3** Moving **one box** in a copy of the level and replaying the SAME plan yields rc 3. *Fails if the level is
taken from anywhere but the file on disk.*

**P4** A row whose `solved` is flipped to `true` over a plan that does not solve is caught by the enforcer with
**rc 1**, and by the verifier with rc 3 and reason `row_claims_solved_but_plan_does_not`.

**P5** A known-good plan on **each of the three levels** verifies rc 0 — `01` in 1, `02` in 12, `03` in 6 moves.
Both directions are asserted: a verifier that always refuses fails this, a verifier that always accepts fails
P2/P3/P4.

**P6** The independent replay and the frozen simulator agree on every plan VERIFIED, **and the cross-check can
fire**: a declared fault-injection hook (`SOKOBAN_REPLAY_FAULT=independent-step`), which is reported in the
verdict as `fault_injected`, makes them disagree and yields **rc 5**. *Fails if the cross-check is decorative.*

**P7** The in-cabinet universe is **87 380** words = Σ_{L=1..8} 4^L, and the number clearing level 01 is
**77 540** = Σ_{L=1..8} (4^L − 3^L), because level 01 is one push and every non-`R` move from its start is
blocked — so a word clears `01` **iff it contains an `R`**. *Fails if the two numbers differ, which would mean
the peer's universe was not the words of length ≤ 8.*

**P8** `RULDLU` clears **level 01 at ply 1 and level 03 at ply 6**. Therefore the card's premise — *"a fixed
six-move cycle clears level 01 alone"* — is **FALSE as stated**: it clears **two of three**, level 02 being the
one it cannot touch. The peer's `strict 1/3 · generous 2/3` is reproduced by reading **STRICT = the plan is
solved exactly at a period boundary** (03 only: ply 6) and **GENEROUS = solved at any ply** (01 and 03).

**P9** `RULDLU` is **not optimal by period**: the minimum period that clears level 01 is **1** (`R` repeated).
The harness prints the measured minimum period per level and per two-of-three set, and names the shortest plan
that attains the best coverage. *Fails if `R` does not clear 01, i.e. if the level is not the one-move level
the whole cabinet says it is.*

**P10** **Zero** words clear all three levels — at any cap in {40, 64, 200}. *If this fails, the peer's `0` is
overturned and that is reported first, before anything else in this card.*

**P11** The peer's `02: 198` and `03: 76` are **cap-dependent** and will reproduce at **at most one** cap in
{40, 64, 200}; the reproducing cap is printed, and the counts are not reported without it. *Fails if they are
cap-invariant, which would make the peer's numbers stronger than I predict.*

**P12** The cabinet's own field-census enforcer (`check_conformance_census.py`, rc 0 at this base) **will fire
on the three new names** — `plan`, `replay`, `provenance` — with rc 1 before they are named in
`SOKOBAN_CONFORMANCE_PACKAGE.md` and `make_conformance_package.py`. Its firing is evidence, not breakage: it is
the control that exists to stop the record widening silently. It returns to rc 0 only after the names and their
blocks are declared. *Fails if it stays green while the writer emits new keys, which would mean it does not
read this writer.*

**P13** No frozen level is edited: the three level digests above are unchanged after every run, re-hashed at the
end of the card.

---

## 3 WHAT THIS CARD WILL NOT DO

- It will **not re-score or rewrite any historical row.** The five solved rows stay byte-identical; they are
  *certified by re-execution* in the report, and the report says so in those words rather than implying their
  files already carry a verdict they do not carry.
- It will **not run a model.** The certification is CPU-only, as the card requires: a search, not a model call.
  The one end-to-end row this card writes is produced by the real driver under an explicit control flag that
  refuses any entrant name but its own and files into `probes/controls/` with `kind: "control-scripted"`, so it
  can never be read as a model measurement.
- It will **not** touch `prism-brain` / `:58595`, any GPU, or any lease. `--ngl` stays at its declared 0.
- It will **not** edit `sokoban.py` or the levels. The frozen simulator is imported, never changed.

## 4 DISPOSAL, DECLARED IN ADVANCE

A dated **NOTE is APPENDED** to `SOKOBAN_FRONTIER_RESULTS.md` (the results file for this cabinet). Nothing in
that file is edited. The census package and the split gain the three names **only after the enforcer has been
seen to fire on them** (P12), and the landing note records both the firing and the repair.
