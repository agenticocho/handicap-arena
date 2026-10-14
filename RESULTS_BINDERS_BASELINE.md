# THE BASELINE FOR THE `<worktree>/results` BINDERS

**Measured** 2026-10-14. **Trees:** `main @ 125b7e2c4f369a3589e8cfd99e42d5abe64b2271` (branch `main`,
clean), `cabinet/sokoban @ e3d2f32`, `cabinet/missile-command @ 1edeb68`, `cabinet/zork @ 1edeb68`.
**Task:** `t_455a539c` (child of the decision card `t_fb870bde`). **No migration is made here.**

## 0. WHAT THIS IS, AND WHAT IT IS NOT

It is the INVENTORY and the BEFORE NUMBERS. For every script that binds a `<worktree>/results`
directory it records what the script reads, what it writes, and what it publishes TODAY, with the
command that reproduces it.

It is NOT the decision. Whether these 22 move to the declared domain (`cabinet_root`) or are
declared LEGACY tools is the Chair's ruling (`t_fb870bde`). Not one of them was edited.

## 1. THE COUNT: 22 IS CONFIRMED, AND IT IS ONE TREE'S SET, NOT FOUR

The counter is now in the repo, so the number is re-derived rather than believed:

```
python3 scripts/list_results_binders.py /home/chilly1/workspace/ocho_arena
python3 scripts/list_results_binders.py /home/chilly1/workspace/ocho_arena_cabinets/sokoban
python3 scripts/list_results_binders.py /home/chilly1/workspace/ocho_arena_cabinets/missile-command
python3 scripts/list_results_binders.py /home/chilly1/workspace/ocho_arena_cabinets/zork
```

| tree | counter says | missing from the set, vs main |
|---|---|---|
| `main` | **22** | — |
| `cabinet/sokoban` | **21** | `render_state_contract.py` |
| `cabinet/missile-command` | **20** | `render_state_contract.py`, `check_format_fields.py` |
| `cabinet/zork` | **20** | same two (identical to missile-command) |

`scripts/list_results_binders.py` is VERBATIM from the `t_af6fafd9` attachment,
`sha256 f797169c843331e505a8c6375d0137a536f4112995a263685d1014e56066a982`. It takes the tree as
`argv[1]` and walks IT, so the copy in `main` measures all four trees. It prints the list to stdout
and also writes the same list to a scratch path (see the header of `remaining_results_binders.txt`).

**The three cabinet trees are SUBSETS of main's set.** No binder exists in a cabinet that is not in
main; the cabinets are missing files, they do not have extras. And the trees' `results/` are one
object, so the numbers below are the numbers in all four trees:

```
git rev-parse <ref>:results     -> 0bcaaa0188b35f0bdd17e3ca824a977cac2d94a1   on all four refs
sha256 of (path, size, bytes) over results/, all 520 files -> baf86e7bd299e8d0...  identical in all four
520 files under results/ | 317 of them *.json at its top level
  supersessions/ 151 | _cardv3_firstpass/ 42 | _invalid_cardv2_pilot/ 2 | control_artifacts/ 1
```

So `21` and `20` in a cabinet's own headline are the same inventory one tree's files can reach, not
a second measurement of a different record. Reproduce the equality in one line:

```
for T in /home/chilly1/workspace/ocho_arena /home/chilly1/workspace/ocho_arena_cabinets/{sokoban,missile-command,zork}; do
  printf "%-58s %s  files=%s\n" "$T" "$(git -C $T rev-parse HEAD:results)" "$(find $T/results -type f | wc -l)"
done
```

Four identical tree objects, 520 files each. (The `sha256 baf86e7bd299e8d0...` above is the same
equality measured over file BYTES rather than over git's tree object — a different digest of a
different encoding of the same fact; both were taken, both agree, and neither is a substitute for
the other.)

## 2. WRITERS: THREE INSIDE `results/`, NOT TWO — AND TWO MORE THE COUNTER CANNOT SEE

The card names two writers. Measured from source and confirmed by the harness's git-status delta per
run (`results_binders_baseline.json` -> `tree_delta`), there are **three** scripts in the 22 that
write into the `<worktree>/results` tree:

| script | what it writes into the tree | safe mode for a baseline |
|---|---|---|
| `annotate_superseded.py` | `results/supersessions/*.json` (151 records already on disk) | `--dry-run` |
| `chess_game.py` | `os.makedirs(HERE/results)`; `results/CHESS_GAME_*.json`; `results/CHESS_REASONING_*.txt` | none — do not run read-only |
| `canonicalise_filenames.py` | `os.rename(src, dst)` with BOTH sides under `results/` — it RENAMES bundles | dry run is the DEFAULT; `--apply` writes |

`canonicalise_filenames.py` is the correction: it is not "a reader that happens to be near the
record", it moves files INSIDE `results/`. In dry run it proposes **208 rename(s)**, 7 `SKIP (not a
result bundle)`, and many `[COLLISION: target exists]` where the canonical name is already present.

The other 19 of the 22 read only. Three write, but NOT into `results/`:

* `build_roster.py` -> `roster.html` at the tree root
* `render_state_contract.py` -> `RENDER_STATE_SCHEMA.json` at the tree root
* `scripts/test_declared_slots_guard.py` -> only inside its own `tempfile.mkdtemp()` fixture

### Writers the counter does not see (`scripts/audit_results_binder_forms.py`)

```
depth_test.py:27   OUT = "/home/chilly1/workspace/ocho_arena/results/DEPTH_TEST.json"
depth_test2.py:32  OUT = "/home/chilly1/workspace/ocho_arena/results/DEPTH_TEST2.json"
```

Both bind by ABSOLUTE path, from ANY worktree, and both WRITE main's legacy record. They are not in
the 22 because the counter's patterns are `os.path.join(...)` forms. Under the card's own wording
("scripts that bind a `<worktree>/results` directory") a strict reading gives **24 on main / 23 on
sokoban / 22 on the two other cabinets** — the counter's 22 is exact for its pattern and narrower
than its headline. Named, not silently added.

Adjacent, and deliberately NOT folded in: `darts/darts.py:706,715` — `--out` defaults to
`<worktree>/darts/results` (5 tracked `darts_v1_*.json`). Missed twice over: the form
(`dirname(__file__)`, not `dirname(abspath(__file__))`) and the directory (not the worktree root's
`results/`). It is the same question as `logs/`.

## 3. THE BASELINE, PER BINDER

Run from a worktree whose `results/` is the legacy record. Exit code and stdout hash for every run
are in `results_binders_baseline.json`; the harness that produced them refuses to start on a dirty
tree and records the tree delta per run.

| binder | reads | writes | published today (baseline) | exit |
|---|---|---|---|---|
| `analyse_card.py` | `results/*.json` | — | CARD v2 — 33 graded entries; belts White 2 / Yellow 3 / Orange 9 / Green 19; win rates R1 89.9% SATURATED, R2 61.6%, R3 75.8%; aggregate 6 distinct / 6 raw | 0 |
| `annotate_superseded.py` | `results/*.json` + `test_game_states` | `results/supersessions/*.json` | dry run: **151 bundle(s) claim a game with no state**; 151 records already on disk | 0 |
| `audit_clock_fields.py` | `results/*cardv4*.json` | — | inspects `BTL-4-IQ2_XXS_cardv4_autofit_neutral_ctx8192_mt3000.json` field by field; no aggregate count published | 0 |
| `audit_stand_ins.py` | `results/*cardv4*.json` | — | 38 measured v4 entries; **38/38 store `aggregate` rounded to 4dp**; 17 lost precision; 21 no-op; 0 at full precision | 0 |
| `audit_weigh_in.py` | `results/*.json` | — | bundles **310** / entries **225**; 225 with a division; 221 with BOTH; 4 never offloaded | 0 |
| `build_roster.py` | `results/*.json` | `roster.html` (root) | **225 entries, 17 controlled pairs**, 111,551 bytes regenerated — the COMMITTED file says **42 bundles / 42 entries** | 0 |
| `canonicalise_filenames.py` | `results/*.json` | `os.rename` inside `results/` (`--apply`) | DRY RUN: **208 rename(s)**, 7 SKIP | 0 |
| `check_field_semantics.py` | one bundle; `results/*cardv5*.json` | — | 11 quantity-named fields; 3 **MISLEADING** (`gen_tokens`, `secs`, `trials`) | 0 |
| `check_format_fields.py --all` | `results/*.json` | — | 317 bundles: **PASS 0, GRANDFATHERED 316, PROBLEMS 1** (`Qwen3.5-4B-UD-Q4_K_XL_cardv5_...`) | **1** |
| `check_run.py v3` | `results/*cardv3*.json`, `results/card_run.log` | — | expected 59, bundle files 72, **MEASURED 38**, never ran 8, no pid -> **STATE: UNKNOWN** | **1** |
| `chess_game.py` | — | `results/CHESS_GAME_*.json`, `CHESS_REASONING_*.txt`, mkdir | NOT RUN (spawns `llama-server`); on disk: 4 `CHESS_GAME_*.json`, 1 `CHESS_VOID_*`, 2 `CHESS_RUN_*.out` | NOT RUN |
| `discrimination_report.py` | `results/*cardv3*.json` | — | 6 item rates over 38; **discriminating items: 2 of 6** (R1.2 60.5%, R1.6 39.5%) | 0 |
| `evaluate_v2.py` | `results/*.json` | — | 33 graded entries; 85 empty/scratched; belts W2 Y3 O9 G19 | 0 |
| `evaluate_v3.py` | `results/*cardv3*.json` | — | 38 bundles carrying a measurement; **12/38 score 6/6 = 31.6% (v2 was 79%) PASS** | 0 |
| `evaluate_v4.py` | `results/*cardv4*.json` | — | **NO VERDICT — field closed and short: 38 measured of ~46 expected**; 8 entrants empty in EVERY copy | **1** |
| `render_state_contract.py` | `results/*.json` | `RENDER_STATE_SCHEMA.json` (root) | **310 bundles / 225 entries**; 3 event kinds (code_repair 30, structured_output 138, tool_selection 30); schema sha `8c2db374566c` — committed file says **234 / 151** | 0 |
| `test_no_silent_zero.py` | `results/*.json` (argv[1] overridable) | — | **1494 item records in 310 bundles**; FAIL 64 empty bundles with no failure record; FAIL 1 zero with no reason | **1** |
| `v3_rates_both_readings.py` | `results/*cardv3*.json` | — | 6 items, both readings; deltas +2.6, +2.6, +2.6, +2.6, **+7.9**, +0.0 | 0 |
| `verify_chair_audit.py` | `results/*.json` | — | Green 19 entries; aggregate range **0.7222 .. 1.0000** (the claim was 0.833-1.000) | 0 |
| `verify_scope.py` | `results/*cardv3*.json` | — | D3a 59 failing items; D3b **1 with NO raw at all**; classes {unparseable 14, no_json 1, other 34, truncated 10}; D2 9 re-score higher | 0 |
| `scripts/prove_declared_slots_parse.py` | `results/` (one v6 bundle), `GAME_CONTRACT.md`, `test_game_states.py` | — | **STATE: SINGLE SOURCE**; 4 slots agree; 38 v6 bundles, key `R1_conformance x37`; refused: none | 0 |
| `scripts/test_declared_slots_guard.py` | `results/` (one v6 bundle) | tempfile fixture only | **2 FAILED — 3/5**: control [1] wants `('SINGLE SOURCE',0)` got `('BLOCKED',1)`; control [3] wants `('DRIFTABLE',1)` got `('BLOCKED',1)` | **1** |
| `depth_test.py` *(blind spot)* | Stockfish | ABSOLUTE write to main's `results/DEPTH_TEST.json` | NOT RUN; artifact: `crossings_at_risk 0`, `crossings_far 0`, config `{Stockfish 19, threads 1, hash 64, d_ref 18, d_alt 12, window 60}` | NOT RUN |
| `depth_test2.py` *(blind spot)* | Stockfish | ABSOLUTE write to main's `results/DEPTH_TEST2.json` | NOT RUN; artifact: `admissible False`, `which INADMISSIBLE`, `near_lost 0`, `near_hold 0` | NOT RUN |

Two self-tests of these tools also pass and are part of their baseline:
`check_field_semantics.py --self-test` -> `ALL CONTROLS PASS -- 10/10`;
`check_format_fields.py --self-test` -> `ALL CONTROLS PASS -- 22/22`.

## 4. TWO PUBLISHED ARTIFACTS ARE STALE, MEASURED

Both are tracked files at the tree root, and both disagree with what their own generator produces
from the record they read:

* `roster.html` — committed: `built 2026-10-07 04:37 UTC, 42 bundles - 42 entries`.
  Regenerating from the same record: **225 bundles / 225 entries, 17 controlled pairs**.
* `RENDER_STATE_SCHEMA.json` — committed: `bundles 234, entrant_entries 151`.
  Regenerating: **310 / 225**.

This matters to the migration precisely: these two are the tools whose numbers a reader is most
likely to quote, and their committed renderings already lag their own inputs by 183 and 76 bundles.
Regenerate with `python3 build_roster.py` and `python3 render_state_contract.py` — from a scratch
worktree, or accept a modified working tree.

## 5. TWO OF THE 22 ALREADY REFUSE FROM A DETACHED WORKTREE

`annotate_superseded.py` imports `test_game_states` (the admission gate), and the gate imports
`cabinet_root`; `scripts/prove_declared_slots_parse.py` loads the gate by file path. From a
DETACHED HEAD both therefore abort before doing any work:

```
REFUSING: cannot tell which cabinet this worktree is: <tree> is on a detached HEAD, or is not a
git work tree at all (`git rev-parse --abbrev-ref HEAD` -> 'HEAD'). ... NOTHING WAS WRITTEN.
```

Measured as a controlled difference: identical commands in a detached-HEAD worktree of `main` gave
exit 1 (both tools) and in a worktree of the same commit on a named branch gave exit 0 with the
numbers in §3. So the `cabinet_root` mechanism ALREADY reaches two of the 22 through an import, and
any migration that points the rest at `cabinet_root` changes their behaviour in every detached
worktree — including the ones this repo creates for tasks.

## 6. WHAT WAS NOT RUN, AND WHY

* `chess_game.py` — spawns `llama-server` on `--port` and plays a full game against a served
  entrant. Its WRITE set is read from source and its published artifacts are counted instead.
* `depth_test.py`, `depth_test2.py` — they run Stockfish and write to an ABSOLUTE path INSIDE the
  LIVE main tree. Running them would mutate the record under measurement; their published artifacts
  (`results/DEPTH_TEST*.json`) are quoted instead.
* `build_roster.py` and `render_state_contract.py` WERE run, but in a scratch worktree of the same
  commit, because their output is a tracked file at the tree root. The scratch tree's `results/` was
  byte-identical to main's (same manifest hash), and both regenerated files differ from the
  committed ones exactly as §4 records.

## 7. HOW TO REPRODUCE THE WHOLE BASELINE

```
# 1. the inventory, four trees
python3 scripts/list_results_binders.py /home/chilly1/workspace/ocho_arena
python3 scripts/list_results_binders.py /home/chilly1/workspace/ocho_arena_cabinets/sokoban
python3 scripts/list_results_binders.py /home/chilly1/workspace/ocho_arena_cabinets/missile-command
python3 scripts/list_results_binders.py /home/chilly1/workspace/ocho_arena_cabinets/zork

# 2. the counter's blind spots, independently
python3 scripts/audit_results_binder_forms.py /home/chilly1/workspace/ocho_arena

# 3. the numbers: a scratch worktree at the same commit, ON A BRANCH (a detached HEAD makes two of
#    the tools refuse, and the refusal would be measured as their baseline)
git -C /home/chilly1/workspace/ocho_arena worktree add -b baseline/<task> <scratch>/tree main
cd <scratch>/tree
python3 analyse_card.py ; python3 audit_clock_fields.py ; python3 audit_stand_ins.py
python3 audit_weigh_in.py ; python3 build_roster.py ; python3 canonicalise_filenames.py
python3 check_field_semantics.py ; python3 check_field_semantics.py --self-test
python3 check_format_fields.py --all ; python3 check_format_fields.py --self-test
python3 check_run.py v3 ; python3 discrimination_report.py ; python3 evaluate_v2.py
python3 evaluate_v3.py ; python3 evaluate_v4.py ; python3 render_state_contract.py
python3 test_no_silent_zero.py ; python3 v3_rates_both_readings.py ; python3 verify_chair_audit.py
python3 verify_scope.py ; python3 scripts/prove_declared_slots_parse.py
python3 scripts/test_declared_slots_guard.py ; python3 annotate_superseded.py --dry-run
```

Exit codes, stdout sha256 and the per-run tree delta are in `results_binders_baseline.json`. The
`tree_delta` field is how a writer is MEASURED rather than believed: after `build_roster.py` and
`render_state_contract.py` the tree shows `M roster.html` and `M RENDER_STATE_SCHEMA.json` and
nothing else; after the 19 readers and both dry runs, nothing.

## 8. ACCEPTANCE, CHECKED AGAINST THIS CARD

* **The list is reproducible** — the counter is committed verbatim (`scripts`), takes the tree as an
  argument, and the four commands above reproduce 22 / 21 / 20 / 20.
* **Writers are called out** — §2, with the correction that there are three inside `results/`
  (`canonicalise_filenames.py` added), plus two absolute-path writers the counter cannot see and one
  adjacent different directory (`darts/results`).
* **Baseline numbers are stored** — §3 and `results_binders_baseline.json`, every number carrying the
  exit code and stdout hash of the command that produced it.
* **No migrations are made** — no binder was edited; the only new files are the artifacts of this
  measurement (`remaining_results_binders.txt`, this file, `results_binders_baseline.json`,
  `scripts/list_results_binders.py`, `scripts/audit_results_binder_forms.py`).
