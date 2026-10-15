# RULING — the declaration binds a WRITER by its DESTINATION, not by its syntax; and a results-named directory that is not `<worktree>/results` is a question for the WRITE scope

**Card:** `t_5742bdac` (raised by `ocho` while drafting `t_614bf5db`; parent of both is the baseline card `t_455a539c`; the ruling it extends is `t_9d66efa4`, committed verbatim as `DECISION_results_binder_era.md`, blob sha256 `55bea450e9ff76181a3e196950b771ee5c247d2356ff5039f4b81fa51d8309f9`).
**Chair:** `tiel` (Local Chair). **Date:** 2026-10-14 PDT. Every number below was re-measured by the Chair at 16:38–16:52 on this date, from the four worktrees, not recalled from the card.

---

## 0. THE DECISION, IN ONE PARAGRAPH

**Option 1 — bring them in — for the two depth writers, and the same for `darts/darts.py` under the WRITE half of the same ruling; the counter is widened as a REQUIRED companion, not as an alternative.** Three qualifications the card's Option 1 does not contain, and each is a measurement rather than a preference:

1. **`darts/darts.py`'s new destination must be a NAMED SUBTREE of the write scope (`results_dir()/darts`), not the flat bundle level.** The two legacy depth artifacts stay declared in place inside the record (they must — see §1), so a depth or darts write at the flat level would put a second `DEPTH_TEST.json` under a different domain entry: a basename collision across entries, which the flattening tools are *required* to refuse (`AC2(b)`) and which would break the before == after equality `AC3` rests on. §3 of the ruling already sanctions exactly this shape: *"where a tool needs one cabinet's runs only, that is `results_dir()`'s subtree by name — not a new glob."*
2. **The counter counts bindings BY DESTINATION, IN ANY FORM — not by syntax.** Its number today is honest for its pattern and false for its headline (§3).
3. **These three files are not the migration card's work.** Its standing condition ("does not edit these three files; its manifest records them as `out-of-scope:<this card>`") **stands**, and the class only changes from `out-of-scope` to `deferred:<new card>` — still *declared, never silent*. A new card lands this, gated on both this card and `t_fdf55800`, because it edits files commit 0 creates.

**Option 2 alone is refused.** A residue number that moves while the bytes do not is the §5 defect (*"a description standing where a mechanism should be"*) one layer out: a green number over a live writer into the legacy record. **Option 3 is refused on the ruling's own property, re-measured here:** `AC5` states *"No byte is written into the legacy record"* and `AC11` requires the legacy record's bytes not to change. Both are properties, and both are FALSE in all four trees today (§1).

---

## 1. WHY — MEASURED, IN THE FOUR TREES

**1.1 The two depth writers bind the legacy record by an absolute literal, and the file is present in ALL FOUR trees.**

```
main               depth_test.py:27   OUT = "/home/chilly1/workspace/ocho_arena/results/DEPTH_TEST.json"
                   depth_test2.py:32  OUT = "/home/chilly1/workspace/ocho_arena/results/DEPTH_TEST2.json"
cabinet/sokoban    depth_test.py:27   the SAME absolute literal (same line numbers)
cabinet/missile-command  depth_test.py:27 / depth_test2.py:32  the SAME absolute literal
cabinet/zork       depth_test.py:27 / depth_test2.py:32  the SAME absolute literal
```

Both then **open it for writing** — `depth_test.py:182 open(OUT, "w")`; `depth_test2.py:199,223 open(OUT, "w")`. So running either from **any** of the four worktrees overwrites a file inside **main's** checkout. This is not "inside the git tree" — it is a cross-worktree write into the record every other tree has declared in place.

**1.2 §1(a)'s own argument applies verbatim, and the tree object it protects is the one re-measured here.**

```
git rev-parse main:results                  -> 0bcaaa0188b35f0bdd17e3ca824a977cac2d94a1
git rev-parse cabinet/sokoban:results       -> 0bcaaa0188b35f0bdd17e3ca824a977cac2d94a1
git rev-parse cabinet/missile-command:results -> 0bcaaa0188b35f0bdd17e3ca824a977cac2d94a1
git rev-parse cabinet/zork:results          -> 0bcaaa0188b35f0bdd17e3ca824a977cac2d94a1
git ls-files results/DEPTH_TEST.json results/DEPTH_TEST2.json   -> BOTH TRACKED
```

`canonicalise_filenames.py` was refused a rename inside that tree **because a rename changes `0bcaaa01`** and the declaration "the four `results` trees are one object" stops being true — that is why Option 2 was unavailable for the 22. `open(OUT, "w")` on a tracked file in the same tree is the same class of act: a write inside the record, by a file that cannot be declared legacy. §1(b): *"a writer cannot be declared legacy at all… the legacy record is declared in place **because its bytes do not move**."* Two live writers into it contradict the premise of the declaration itself.

**1.3 The honest numbers, re-measured per tree, with the counter's own two instruments run against each tree root.**

```
python3 scripts/list_results_binders.py <tree>            (the join-form counter)
  main 22   sokoban 21   missile-command 20   zork 20      <- reproduces AC1 exactly

python3 scripts/audit_results_binder_forms.py <tree>      (the form audit, column C)
  main:               darts/darts.py, depth_test.py, depth_test2.py
  sokoban:            depth_test.py, depth_test2.py
  missile-command:    depth_test.py, depth_test2.py
  zork:               depth_test.py, depth_test2.py
```

So, at **file level**, honestly counted by destination:

| tree | record binders (any form) | results-named write destination that is NOT the record | total |
|---|---|---|---|
| `main` | **24** | `darts/darts.py` → 1 file | **25** |
| `cabinet/sokoban` | **23** | — | 23 |
| `cabinet/missile-command` | **22** | — | 22 |
| `cabinet/zork` | **22** | — | 22 |

`AC1`'s **target** (0 per tree) does not change; its **before-number** does: **24/23/22/22 record binders**, not 22/21/20/20, and the two depth files are residue in *all four* trees, not only where a cabinet happens to carry them.

**1.4 Two facts that bound the edit, both measured, so no worker has to guess them.**

* **`depth_test2.py` is ALSO a library.** It is imported for its `uci`/`eval`/`fen` helpers by `source_probe3.py:19`, `source_probe4.py:21` and `acceptance_smoke.py:20`. **The destination must therefore be resolved at CALL time, never at import time** — a top-level refusal would break three importers that never write a depth artifact.
* **The drift monitor does not watch this binding.** `check_frozen_constants.py` emits *only* `LOST_CP, HOLD_CP, WINDOW, MIN_PER_EDGE` (its own `SOURCES`/`CONST_NAMES`), and `FROZEN_CONSTANTS.json` is the reference — **no output path is frozen**. `PREREG_depth_test.md` freezes the *config* ("read-only apart from its own output"), not the destination. So migrating `OUT` cannot be reported as a criterion movement, and equally cannot be justified by one.

**1.5 No reader and no published finding depends on where these artifacts live.**

`results/DEPTH_TEST*.json` is cited **only** by the binder/baseline documents themselves (`RESULTS_BINDERS_BASELINE.md`, `remaining_results_binders.txt`, `results_binders_baseline.json`, `PLAN_results_binders_migration.md`) — measured by `grep -rn DEPTH_TEST` over the tree, excluding the scripts. `canonicalise_filenames.py` already SKIPs both by name (*"not a result bundle"*), and `darts/results/*.json` is cited by nothing but `darts/DARTS_AMBIGUITIES.md`. **Nothing has to move to keep a citation working**, which is what makes declaring the existing artifacts in place the cheap branch rather than a choice against evidence.

---

## 2. THE SECOND HALF OF THE QUESTION: `darts/results` IS A WRITE-SCOPE QUESTION, AND ITS ANSWER IS DECIDED HERE

**Does a results-named directory that is not `<worktree>/results` belong to the same declaration?** **Yes — under the WRITE half only.** §3's write scope is not stated as a directory *name*: it is *"`<declared root>/<this worktree's cabinet>` — the ONE path a run may write to"*, and its refusal is *"a declaration that resolves inside a git working tree or the git directory"*. `darts/darts.py:706,715` defaults `--out` to `os.path.join(os.path.dirname(__file__), "results")` — `darts.py:481 os.makedirs(args.out)`, `:482 path = os.path.join(args.out, "darts_v1_%s.json" % args.entrant)`, `:484 json.dump` — i.e. **`<worktree>/darts/results`, inside the git working tree**, in `main` only (`darts/` is absent from all three cabinets — measured).

Its **read** half is empty, and that is why it is not in the counter's remit: nothing in the tree globs that directory (only `DARTS_AMBIGUITIES.md` names it). It is a bundle-producing harness writing into a git tree, which is `AC6` (*"No new write lands inside any git tree"*) and the `results_dir()` refusal applied to a directory the refusal was not looking at.

**And `darts/results`'s five tracked bundles are RECORDS, not scratch** — the test the `logs/` ruling fixed: *a record is something a reader may treat as evidence about what happened; scratch is what a process emits about itself while it runs.* `darts_v1_reference.json`, `_instrument-check.json`, `_garbage.json`, `_liar.json`, `_never-starts.json` are the harness's own controls proving the instrument; `DARTS_AMBIGUITIES.md` cites them by path. So the ignore-rule shortcut is **out** — a `darts/results` under `.gitignore` would declare them scratch, which the classification forbids.

**DECIDED (naming is the Chair's, so no worker decides it twice):**

1. `darts/darts.py`'s `--out` **default becomes `results_dir()/darts`** — both parsers (`run` `:706`, `instrument-check` `:715`), resolved through `cabinet_root`, stored in the SAME single definition and printing the destination it used. An explicit `--out` on the command line still overrides (it is a flag, not a fallback), **but a destination that resolves inside any git working tree or the git directory must be REFUSED**, not honoured — the refusal is a property of the destination, exactly as `declared_root()` already implements it.
2. The five tracked bundles are **declared in place** in `cabinet_root.py` (a `DARTS_ARCHIVE`-style tuple with its `..._WHY`), byte-frozen, **written by nothing after this landing** — the `LEGACY_CAPTURES` treatment, with its reason stated: they are tracked control evidence cited by `darts/DARTS_AMBIGUITIES.md`, and their bytes do not move.
3. **`darts/results/` is added to `.gitignore`** so that a stray write there cannot be staged — the mechanical carrier the `logs/` ruling used, and it is mechanically checkable (`git check-ignore darts/results/x`). Tracked files stay tracked; the rule closes the directory to NEW bytes.

**The depth artifacts get the same two-part shape:** `depth_test.py` and `depth_test2.py` resolve **`results_dir()/depth`** at call time and REFUSE (exit non-zero, nothing written, remedy named) when there is no declaration or it resolves in a git tree; `results/DEPTH_TEST.json` and `results/DEPTH_TEST2.json` stay declared in place inside the legacy record (they MUST: removing them changes `0bcaaa01` and fails `test_declared_root.py` check 6, the same measurement as §1.2). The named subtree `depth/` also guarantees **no basename collision** with the legacy artifacts under the flattening tools (`AC2(b)`).

---

## 3. THE COUNTER AND THE NUMBER — WHAT "RESIDUE" COUNTS

**RULING: every binding, counted BY DESTINATION, IN ANY FORM.** A number that depends on the syntactic shape of the binding is a property of the instrument, not of the field, and this card is the proof: the counter's headline is *"scripts that bind a `<worktree>/results` directory"* while its pattern is two `os.path.join` shapes, and the form it cannot see is the form that put a live writer into the legacy record in all four trees (§1.1). §5 of the ruling already names this species — *"an exclusion list that can hide a binder is precisely a description standing where a mechanism should be"* — and a pattern that can hide a binder is the same thing with a regex for a body.

**Therefore:**

* **One detector, not two.** `scripts/audit_results_binder_forms.py` **already implements the full detection class** — it found all four blind-spot lines plus `darts/darts.py` (measured, §1.3), and it is the instrument that raised this card. The counter must **call it** (or the two must share one function), on the repo's own rule: *one definition, no second copy*.
* **Three classes, each reported per tree, each row carrying a status:**
  * **`record_binders`** — sites resolving the record / this worktree's `results` directory, in any form. Residue = the ones with no admissible status. **Target 0 in each tree.**
  * **`named_write_destinations`** — sites writing into a results-named directory that is neither the record nor the declared write scope (today: `darts/darts.py:706,715`, the parser DEFAULTS; the explicit `--out` value is a run-time argument, not a site). **Target 0 in each tree.**
  * **`log_coordinates`** — already its own class (`deferred:log-coordinate:t_c442023d` + `landed_by: 8f51ae8`); unchanged by this ruling.
* **Per-tree before/after this ruling fixes:** record binders **24 / 23 / 22 / 22 → 0 / 0 / 0 / 0**; named write destinations **1 (`main`) / 0 / 0 / 0 → 0**.
* **The manifest's class for these three files changes, and only the class:** `out-of-scope:t_5742bdac` → **`deferred:<the new card's id>`**. *Declared, never silent* — the standing condition's property is preserved; the reason it was declared a residue is now a card that lands it.
* **`AC1`'s target is unchanged; its before-number is corrected** to 24/23/22/22. A ruling may not leave a target number that was computed with a detector known to be blind to the defect the ruling exists to settle.

---

## 4. WHAT MUST NOT CHANGE (the standing conditions, carried)

* `t_fdf55800` **does not edit** `depth_test.py`, `depth_test2.py` or `darts/darts.py`. Its manifest carries them `deferred:<new card>`. *(The standing condition is honoured; only the class moves.)*
* **No byte is written into the legacy record** (`AC5`) and the legacy record's bytes do not change (`AC11`): `0bcaaa01…` must still be the object of `<ref>:results` for all four refs after every landing.
* `cabinet_root.py`'s **single definition** stays single: no per-script copy of the root, no second declared root for `darts` or `depth`, no fallback to `<worktree>/…` anywhere.
* The writers' **refusal** behaviour (`run_card.py`, and the three migrated writers) is not touched; this ruling ADDS refusal sites, it never removes one.
* `check_frozen_constants.py`'s four thresholds and `FROZEN_CONSTANTS.json` are untouched; the migration of an output path is not a criterion movement (§1.4).
* **No published number moves.** The new destinations are named subtrees, so the readers' non-recursive top-level globs stay at 317 / 72 / 63 / 38 (`AC3`'s equality is a measurement, not a promise). A delta there is a finding and stops the landing.
* `--out` given explicitly on a command line is a legitimate override to a declared, outside-git destination; it is not a licence to write into a git tree.

---

## 5. LANDING — WHAT THE NEW CARD DOES, IN ORDER

**One new card, assignee `ocho`, `parents=[t_5742bdac, t_fdf55800]`** (the second parent is required: commit 0 creates the counter, the manifest and the guard, and this card edits all three). **Five commits, one per band, independently revertible; `git revert` is the rollback.**

0. **The ruling, verbatim, in the repo** — `DECISION_results_binder_residue.md`, copied from this file and verified by blob sha256 (the `AC10` convention). Its hash rides in the card, not in prose.
1. **The counter/guard widening** (after commit 0 of `t_fdf55800` has landed): the counter adopts the form audit's detector, reports the three classes per tree, prints the manifest path and hash it read, and exits non-zero while residue > 0. Guard checks added: a `darts/results` or absolute-literal binder absent from the manifest FAILS; a manifest row claiming `migrated` whose site still resolves the record FAILS; the classes count independently.
2. **`depth_test.py`** — resolve `results_dir()/depth` at call time; REFUSE with the remedy named; print the destination it wrote. Before/after: the artifact is regenerated into the declared subtree; `results/DEPTH_TEST.json` unchanged (its bytes must not move).
3. **`depth_test2.py`** — same, plus the **import edge**: `source_probe3.py`, `source_probe4.py`, `acceptance_smoke.py` still import it successfully (this is the control for the call-time rule); the three artifacts it writes at `:199,:223` land in the subtree.
4. **`darts/darts.py`** — `--out` default `results_dir()/darts` at `:706,:715`; destination printed; a destination inside a git tree REFUSED; `darts/results/` added to `.gitignore`; the five bundles declared in place in `cabinet_root.py` with their `_WHY`.

**Per-script before/after, printed and attached, per `AC3`:** for each of the three, the exact command, the destination resolved before and after, the exit code, and the statement that `results/DEPTH_TEST*.json` / `darts/results/*.json` are byte-identical (`git status` clean for those paths) after the run. **Regression set after EVERY landing (`AC7`):** `test_declared_root.py` (exit 0, four trees), `test_game_states.py` (exit 0, NEW violations 0), `reconcile_and_backfill.py` report-only (310 arena bundles / 225 carrying results / 64 empty / cardv4 6), `check_frozen_constants.py` (exit 0), plus the three importers of `depth_test2`. **`AC9` parity:** `darts/` is absent from all three cabinets, so that file's change is parity by declaration of absence (as `render_state_contract.py` already is), and the depth files are in all four trees, so they land in all four — the counter and the manifest must **travel** before a cabinet can run the new guard (the plan's §3.6 finding, still true: `scripts/list_results_binders.py` is absent from all three cabinets — re-measured here).

---

## 6. EVIDENCE READ BACK (each one a command run by the Chair on 2026-10-14)

```
for t in main sokoban missile-command zork; do grep -n "^OUT" $t/depth_test.py $t/depth_test2.py; done
  -> 27 / 32, the SAME absolute literal naming main's record, in all four trees
grep -n "open(OUT" depth_test.py depth_test2.py      -> 182 / 199,223  (writers, not readers)
grep -n "args.out|makedirs|json.dump" darts/darts.py  -> 481,482,484 (run) ; 568,571 (instrument-check)
sed -n '706,715p' darts/darts.py                      -> --out default = dirname(__file__)/results
git rev-parse <ref>:results (main, cabinet/sokoban, cabinet/missile-command, cabinet/zork)
  -> 0bcaaa0188b35f0bdd17e3ca824a977cac2d94a1  (identical)
git ls-files results/DEPTH_TEST.json results/DEPTH_TEST2.json   -> both tracked
git ls-files darts/results                                       -> 5 tracked darts_v1_*.json
git rev-parse main:darts/results                                 -> 15f4edb527a655299f3db5a030f8ae7950016ba0
python3 <copy of> scripts/list_results_binders.py <tree>  -> 22 / 21 / 20 / 20
python3 <copy of> scripts/audit_results_binder_forms.py <tree>  -> the three / two / two / two blind files
grep -rn DEPTH_TEST . (excluding the scripts)   -> only the baseline + plan documents cite the path
grep -n "depth_test2" source_probe3.py source_probe4.py acceptance_smoke.py -> imported as a library
grep -n "CONST_NAMES|SOURCES" check_frozen_constants.py -> four thresholds only; no output path frozen
ls /home/chilly1/workspace/cabinet_results/*/   -> 5 subtrees, all empty (the write scope is empty today)
find results -mindepth 1 -maxdepth 1 -type d    -> _invalid_cardv2_pilot, _cardv3_firstpass,
                                                   supersessions, control_artifacts  (named-subtree precedent)
ls <cabinet>/scripts/list_results_binders.py    -> absent in all three cabinets
```

---

## 7. NAMED, NOT DECIDED HERE

* **Whether the two legacy depth artifacts are ever re-run at all.** They were NOT RUN by the baseline card either (they spawn Stockfish; re-running them from any tree would have mutated the record under measurement). This ruling moves where a re-run *would* land; it does not schedule one, and the recorded artifacts stay the published ones.
* **The four `CHESS_GAME_*`-class non-bundle artifacts** inside the record remain as `t_9d66efa4` §4 left them — declared in place, not this card's.
* **The three duplicate `results/` trees' eventual deletion** — still not this card's, and still not this ruling's.
* **`darts` has no cabinet.** If a darts cabinet is ever created, `darts/results`'s declaration and the `named_write_destinations` class have to be re-read per tree rather than assumed.
