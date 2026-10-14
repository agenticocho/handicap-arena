# PLAN — migrating the 22 `<worktree>/results` binders to the declared domain

**Implements:** the Chair's ruling on `t_9d66efa4` — **Option 1 (migrate)**, verbatim at
`DECISION_results_binder_era.md` in this repo.
**Ruling source:** `/home/chilly1/.hermes/profiles/tiel/governance/rulings/2026-10-14-results-binders-era-is-the-mechanism.md`,
sha256 `55bea450e9ff76181a3e196950b771ee5c247d2356ff5039f4b81fa51d8309f9`, 23419 bytes
(sha256 **re-computed by this card** at 2026-10-14T23:18Z, matches).
**Drafted by:** `t_614bf5db` (ocho, planner). **Executed by:** `t_fdf55800` (ocho).
**Before numbers:** `t_455a539c` — `RESULTS_BINDERS_BASELINE.md` + `results_binders_baseline.json` +
`remaining_results_binders.txt`, all committed at `7c16ea3`; taken at `main@125b7e2`.
**No script was edited by the drafting card.** The only files it adds are the ruling (verbatim) and
this plan.

**Read this in this order:** §1 (base, and why the base is not what you think) → §2 (the two scopes,
with the exact code idiom) → §3 (the manifest + guard, commit 0) → §4 (the 22, one row each) →
§5 (landing order + per-commit commands) → §6 (regression set after EVERY landing) → §7 (rollback) →
§8 (what must not change) → §9 (carried, not decided here) → §10 (AC1-AC11 → where each is satisfied).

---

## 1. BASE — the plan is written against a moving tree, and this is measured, not assumed

**BASE, read at drafting time (measured):** `main` = `8f51ae8` (“DECIDED: logs/ IS SCRATCH — and the
log coordinate is declared PER BUNDLE”), `cabinet/sokoban` = `9aa5a21`,
`cabinet/missile-command` = `cabinet/zork` = `07d8815`. **The `logs/` landing (`t_c442023d`) is IN** —
its decision is `DECISION_logs_are_scratch.md`, its edge list is `LOG_EDGES.json`, its guard is
`test_declared_root.py` **section 7** (25 ok → 40 ok, 0 FAIL, measured by the card that landed it),
and it re-pointed `check_run.py`’s log candidate and `chess_game.py`’s log dir. **That is why this
plan’s two log edges are already resolved**, and why they are carried as
`deferred:log-coordinate:t_c442023d` **with `landed_by: 8f51ae8`** rather than re-decided here
(§3.2, §4 rows 3 and 4). Re-read the heads yourself before landing — a commit hash quoted in a plan
is a coordinate, not content:

```
for b in main cabinet/sokoban cabinet/missile-command cabinet/zork; do echo "$b $(git rev-parse --short $b)"; done
```

**Why this section exists at all —** while this plan was being drafted, at **2026-10-14T23:18:02Z**,
`main`’s working tree in `/home/chilly1/workspace/ocho_arena` was **dirty with that same card’s work
in flight** (`t_c442023d`, the `logs/` ruling’s card, same profile, different session):

```
git status --porcelain        (measured)
 M .gitignore                 M cabinet_root.py   (+159 lines: worktrees/log_dir/log_path/log_for,
 M arena.py                                         LEGACY_CAPTURES, LOGS_ARE, DECISION_logs_are_scratch.md)
 M cabinet_root.py             M check_run.py      (its log candidate :112 -> _root.log_path(HERE))
 M check_run.py                M chess_game.py     (its log dir :593 -> _root.log_dir(HERE))
 M chess_game.py               M reconcile_and_backfill.py
 M cost_probe.py               M run_card.py
 M measure_reasoning_budget.py
```

Verified in that (now landed) diff: `domain()`, `domain_paths()`, `domain_find()`, `results_dir()`,
`in_domain()` are **byte-untouched** — only new functions were added. The two scopes this plan uses
are unchanged by it. `cabinet_root.py`'s working-tree sha256 at that instant: `6e7454479009…`
(12 hex); the landed commit's version is the one to read — see the rule below.

**Rules that follow, and they are the first thing the implementer does:**

1. **`BASE` = the commit that carries `t_c442023d`’s landing** — measured at drafting: `main`
   `8f51ae8`, `cabinet/sokoban` `9aa5a21`, `cabinet/missile-command` and `cabinet/zork` `07d8815`
   (each cabinet has its own cherry-pick hash: **there is no single BASE for all four trees, and the
   manifest records one per tree**). Record it in the manifest and in every commit trailer.
   **Do not take “before” numbers in the live tree**: a number taken in a moving tree is a number
   about no tree.
2. **Every line number in §4 is a coordinate at `BASE`, not content.** Line numbers resolve to
   whatever sits there when read. `t_c442023d` moved **two** of the 22, and the shift is measured
   (counter output at `7c16ea3` → at `8f51ae8`): `check_run.py` `[78, 112]` → **`[80]`** (its
   `results/card_run.log` candidate is gone — resolved by that card), `chess_game.py`
   `[573, 595, 630]` → **`[574, 599, 634]`**. Re-derive the whole list at `BASE` before starting, and
   locate each site by its quoted line, never by the number. Measured at `8f51ae8`, `main`
   (`python3 scripts/list_results_binders.py /home/chilly1/workspace/ocho_arena`, 22 files):

```
analyse_card.py [28]        annotate_superseded.py [36]   audit_clock_fields.py [19]
audit_stand_ins.py [28]     audit_weigh_in.py [30]        build_roster.py [186]
canonicalise_filenames.py [28]  check_field_semantics.py [155]  check_format_fields.py [38]
check_run.py [80]           chess_game.py [574, 599, 634] discrimination_report.py [64]
evaluate_v2.py [12]         evaluate_v3.py [26]           evaluate_v4.py [34]
render_state_contract.py [70]  test_no_silent_zero.py [26] v3_rates_both_readings.py [67]
verify_chair_audit.py [17]  verify_scope.py [62]
scripts/prove_declared_slots_parse.py [101]   scripts/test_declared_slots_guard.py [75, 77]
```
3. **Take every measurement in a scratch worktree of `BASE`, ON A BRANCH** — a detached HEAD makes
   two of the 22 refuse (`annotate_superseded.py`, `scripts/prove_declared_slots_parse.py`, through
   the gate's `cabinet_root` import), and the refusal would be measured as their baseline:

   ```
   git -C /home/chilly1/workspace/ocho_arena worktree add -b wt/t_fdf55800 <scratch>/tree <BASE>
   cd <scratch>/tree
   python3 -c "import cabinet_root as r; print(r.domain())"    # the scope, before anything else
   ```

   **Measured side effect, expected and harmless:** `run_card.py:120` does
   `os.makedirs(RESULTS, exist_ok=True)`, so simply **importing** `run_card` (which
   `test_declared_root.py` check 4 does) creates `<declared root>/<this scratch branch's last path
   segment>` — a live domain entry with 0 files. It appears in every scope print while your scratch
   worktree exists. Tidy up when you remove the worktree:

   ```
   git -C <repo> worktree remove --force <scratch>/tree && git -C <repo> branch -D wt/t_fdf55800
   rmdir /home/chilly1/workspace/cabinet_results/<scratch-branch-name>   # 0 files; else STOP and look
   ```
   (This card created and removed exactly one such entry, `live:t_614bf5db-base`, while re-measuring.)

4. **"Before" is already in the repo, and this card re-measured it at `7c16ea3`** (a scratch worktree
   on a branch, 21 commands, exit code + stdout sha256 compared with `results_binders_baseline.json`):
   **18 of 21 reproduce byte-for-byte.** Three do not, and they cannot:
   `build_roster.py` (`:329` stamps `datetime.now(utc)`), `evaluate_v4.py` (`:139` prints
   `as of <now>.isoformat()`), `test_no_silent_zero.py` (`:71` prints the absolute `RESULTS` path,
   which differs per tree). **For those three, compare the NUMBER LINES with the clock/path token
   masked, never the whole-stdout hash.** Masking recipe, used everywhere below:

   ```
   diff <(sed -E 's/[0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9:.+-]+/<CLOCK>/g' before.txt | grep -v '^  scope  ') \
        <(sed -E 's/[0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9:.+-]+/<CLOCK>/g' after.txt  | grep -v '^  scope  ')
   ```
   empty = every published number is unchanged. **Anything else is a FINDING** (ruling `AC3`): name
   the domain member that joined and why the hardcoded path excluded it, **before the next script
   lands**.

---

## 2. THE TWO SCOPES — decided in the ruling; do not invent a third

| role | scope | call |
|---|---|---|
| reader of the record | **the declared domain** | `cabinet_root.domain()` / `domain_paths(pattern)` / `domain_find(*parts)` |
| writer of a result | **one path, or a REFUSAL** | `cabinet_root.results_dir()` — never a fallback |
| writer of a LOG (not this card) | declared by `t_c442023d` | `log_dir()` / `log_path()` |

**The reader idiom** (the gate's own shape, `test_game_states.py:244-252`: a LIST, never a walk;
the scope is printed **with the count it contributed** — `AC4`; a count without its scope is not a
count):

```python
import os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)                      # root scripts: already sys.path[0]; scripts/*: required
import cabinet_root as _root


def scope(pattern="*.json"):
    """[(kind, base, [paths])] over the DECLARED domain, entry by entry. No pattern is widened,
    no directory joins by existing."""
    rows = []
    for kind, base in _root.domain():
        rows.append((kind, base, sorted(glob.glob(os.path.join(base, pattern)))))
    return rows


def print_scope(rows, pattern):
    for kind, base, hits in rows:
        print(f"  scope  {kind:16} {len(hits):4} {pattern}  {base}")
```

and every reader replaces its single `glob.glob(os.path.join(RESULTS, ...))` with
`[p for _k, _b, hits in scope(<pattern>) for p in hits]`. **Pattern preserved exactly** — the
migration changes **where**, never **what**.

**The writer idiom** (`AC5`): resolve once, at the point of use, and let the refusal propagate —
`cabinet_root.Refusal` is a `SystemExit`, so it exits non-zero, prints the remedy, writes nothing.
`RESULTS = os.path.join(HERE, "results")` must **not exist as a live line** in any of the 22 (the
guard checks this textually, §3-G2).

**`AC2` — the union's two new failure modes, asserted:**

* **(a) disjointness.** `[b for _k, b in domain()]` must have no repeated `realpath`, and no path may
  be reachable under two entries. Today it holds (each live subtree holds 0 `*.json`, the legacy
  record holds 317, measured in all four trees below); **if it ever stops holding that is a
  DECLARATION failure, not a script bug** — stop and take it to the Chair.
* **(b) basename collisions across entries**, in the two tools that FLATTEN the domain into one
  place (`scripts/prove_declared_slots_parse.py`, `scripts/test_declared_slots_guard.py`).
  A fixture that drops a member is a silent zero. Minimum shape:

  ```python
  seen = {}
  for kind, base, hits in scope("*.json"):
      for p in hits:
          seen.setdefault(os.path.basename(p), []).append((kind, p))
  clash = {n: v for n, v in seen.items() if len(v) > 1}
  if clash:
      print(f"STATE: BLOCKED. BASENAME COLLISION across domain entries: {clash} -- a fixture that "
            f"drops a member is a silent zero. Nothing was written.")
      return 1
  ```

**Re-measured by this card at `BASE`, all four trees** (`domain_paths` vs `<worktree>/results/*.json`):

```
tree                                    *.json    cardv3  cardv4  cardv5   path-set-equal?
main                                   317/317    72/72   63/63   38/38   True   (its results/ IS the legacy record)
cabinet/sokoban                        317/317    72/72   63/63   38/38   FALSE  (its results/ is the declared DUPLICATE)
cabinet/missile-command                317/317    72/72   63/63   38/38   FALSE  (same)
cabinet/zork                           317/317    72/72   63/63   38/38   FALSE  (same)
live subtrees (every one)                0          -       -       -
```

**So: `before == after` by NUMBER in all four trees; set-equality holds only in `main`, where
`<worktree>/results` *is* the legacy record.** In a cabinet, the paths change (its own copy is
excluded by the declaration, as intended) while every count is identical. `AC3` is satisfied by
number equality per script, plus the named exception above.

---

## 3. COMMIT 0 — the manifest + the guard + the ruling, FIRST (ruling §5, §7.1, `AC1`, `AC10`)

The state must be checkable **before** it is changed. Commit 0 lands, in this order inside one commit:

**3.1 `DECISION_results_binder_era.md`** — the ruling file **verbatim**, at the repo root, with its
sha256 printed in this plan and carried in the manifest. Byte-for-byte copy; verify with
`sha256sum` against `55bea450e9ff76181a3e196950b771ee5c247d2356ff5039f4b81fa51d8309f9` (23419 bytes).
Do **not** edit, reflow, or "improve" it: it is the citation, not a summary of one.

**3.2 `RESULTS_BINDERS_MANIFEST.json`** at the repo root — the counter's hardcoded `FIXED`
exclusion list becomes a **declared, checked-in manifest**. An exclusion can *hide* a binder; a
declaration cannot. Shape (every field below is read by the guard):

```json
{
  "what_this_is": "The declared manifest of every <worktree>/results binding and its status. Replaces the counter's hardcoded FIXED exclusion list.",
  "ruling": {"file": "DECISION_results_binder_era.md",
             "sha256": "55bea450e9ff76181a3e196950b771ee5c247d2356ff5039f4b81fa51d8309f9",
             "card": "t_9d66efa4"},
  "built_against": {"base_commit": "<BASE>", "measured_at": "<ISO8601Z>",
                    "counter_sha256": "<sha256 of scripts/list_results_binders.py at BASE>"},
  "scope_pair": {"read": "cabinet_root.domain()/domain_paths()/domain_find()",
                 "write": "cabinet_root.results_dir() -- REFUSAL, no fallback"},
  "status_classes": ["migrated:<commit>", "deferred:<card-id>", "deferred:log-coordinate:<card-id>",
                     "out-of-scope:<card-id>", "fixed:<reason>"],
  "entries": [
    {"script": "analyse_card.py", "role": "reader", "pattern": "*.json",
     "presence": {"main": true, "cabinet/sokoban": true,
                  "cabinet/missile-command": true, "cabinet/zork": true},
     "edges": [{"kind": "results-read", "status": "migrated:<commit>"}]}
  ],
  "declared_absent": {"render_state_contract.py": ["cabinet/sokoban", "cabinet/missile-command", "cabinet/zork"],
                      "check_format_fields.py": ["cabinet/missile-command", "cabinet/zork"]},
  "fixed_mechanism_files": [{"path": "cabinet_root.py", "why": "the one declaration"},
                            {"path": "run_card.py", "why": "the writer, with the refusal"},
                            {"path": "test_game_states.py", "why": "the admission gate reads the domain"},
                            {"path": "reconcile_and_backfill.py", "why": "sweep 1"},
                            {"path": "test_bind_control.py", "why": "bind control"},
                            {"path": "test_declared_root.py", "why": "the declarations' own controls"}]
}
```

Entries: **all 22** (§4) **plus** the three carried-residue scripts
(`depth_test.py`, `depth_test2.py`, `darts/darts.py` — `out-of-scope:t_5742bdac`, see §9). Two
scripts carry **two** edges and are listed once (`AC8`): `check_run.py` (results-read + `log-coordinate`)
and `chess_game.py` (results-write + `log-coordinate`). `AC1`'s single log coordinate,
`check_run.py`'s `results/card_run.log` candidate, is `status: "deferred:log-coordinate:t_c442023d"`;
**if `t_c442023d` has landed by then, cite its commit in a `landed_by` field and leave the class
alone** — a deferred edge is *declared*, never *silent*.

**3.3 the guard — `test_declared_root.py` section 8**, following the shape the `logs/` landing put in
**section 7** (`LOG_EDGES.json`: “*a list of edges that nothing checks is a resolution, not a
mechanism*”). One file holds the declarations' controls, and it already runs in all four trees for
`AC7`. (A separate `scripts/check_results_binders_manifest.py` is acceptable **only** if section 8
calls it — two places that must be run by hand is how a guard stops being run.)
**It must re-use the counter's detection, not copy it** (a copy drifts from the thing it copied):
`scripts/list_results_binders.py` gains an importable `find_binders(root) -> [(rel, [lines])]`, and
the guard loads it by path — the `importlib.util.spec_from_file_location` idiom
`scripts/prove_declared_slots_parse.py:56` already uses for the gate. Fails (non-zero, reason
printed) on:

* **G1** a binder found by the counter in any of the four trees and **absent from `entries`** — the
  "hide a binder" defect, mechanized.
* **G2** an entry whose edge says `migrated:<commit>` while a **live (non-comment) line** of the file
  still matches the counter's `<worktree>/results` pattern — a manifest that claims a landing that
  did not happen. (`<commit>` must also exist: `git cat-file -e <commit>`.)
* **G3** any `deferred:*` / `out-of-scope:*` status **with no card id** (`t_[0-9a-f]+`).
* **G4** `presence` / `declared_absent` disagreeing with the filesystem.
* **G5** `DECISION_results_binder_era.md` absent, or its sha256 ≠ `ruling.sha256`.
* **G6** a `migrated:<commit>` entry whose text does not contain `import cabinet_root`.
* **G7** (the counter, not the guard) prints **the manifest path and the sha256 it read**, so the
  residue number carries its instrument.
* **G8** cross-manifest agreement: every `deferred:log-coordinate:*` edge in *this* manifest appears
  in `LOG_EDGES.json`'s `migrated` list, and vice versa. Two manifests that can disagree about the
  same file are one manifest too many — this is a five-line check, and it is the reason the log edges
  can be carried here without being re-decided here.

**3.4 `scripts/list_results_binders.py`** — `FIXED = {...}` is deleted; the manifest is read
(`--manifest`, default `<repo>/RESULTS_BINDERS_MANIFEST.json`). Output per tree: one line per hit with
its manifest class, then the headline `N results-record binders still bind <worktree>/results`, then
`manifest <path> sha256 <...>`. **Exit non-zero while that N > 0**: residue zero must be a number the
tool *exits* on, not a number a reader eyeballs. `scripts/audit_results_binder_forms.py`'s
`COUNTER_FIXED` moves to the same manifest in the same commit (two readers of one declaration).
Note in the commit message: the counter's `sha256 f797169c…` in `remaining_results_binders.txt`'s
header is **superseded by this commit**, and the manifest records the old and new hashes.

**3.5 `test_declared_root.py`** — extend the existing textual regression guard
(`:181-185`, which today covers three files) to take its file list **from the manifest** (every entry
with `migrated:<commit>`): text contains `import cabinet_root` **and** no live
`RESULTS = os.path.join(HERE, "results")` line. One mechanism, two checks, no second list. Add the
`AC10`/`G5` assertion (DECISION file present, hash matches). Keep the existing 25 checks passing.

**Commit 0 command — pathspec, never `-A`** (a sibling card shares this working tree; `git add -A`
would sweep its half-landed work into your commit, and its `git add -A` could sweep these files into
its commit — so write, add and commit in one motion):

```
git add DECISION_results_binder_era.md PLAN_results_binders_migration.md \
        RESULTS_BINDERS_MANIFEST.json scripts/list_results_binders.py \
        scripts/audit_results_binder_forms.py test_declared_root.py
git commit -m "COMMIT 0: the state is checkable before it is changed -- manifest + guard + the ruling (AC1, AC10)" \
  -- DECISION_results_binder_era.md PLAN_results_binders_migration.md \
     RESULTS_BINDERS_MANIFEST.json scripts/list_results_binders.py \
     scripts/audit_results_binder_forms.py test_declared_root.py
```

(The guard is section 8 of `test_declared_root.py`, which is already in the list — no extra script.)

**3.6 THE INSTRUMENTS MUST TRAVEL, AND ON THE CABINETS THEY ARE NOT THERE YET (measured).**
`scripts/list_results_binders.py` and `scripts/audit_results_binder_forms.py` were added by
`t_455a539c` **on `main` only** — measured at `8f51ae8`, running the counter **inside** a cabinet tree
fails outright:

```
$ cd /home/chilly1/workspace/ocho_arena_cabinets/sokoban && python3 scripts/list_results_binders.py .
python3: can't open file '.../cabinet/sokoban/scripts/list_results_binders.py': [Errno 2] No such file or directory
```

The counter can still measure a cabinet *because `main`'s copy walks a tree handed to it as
`argv[1]`* — but the **guard cannot run in a cabinet** without the manifest and the counter's
detection beside it, and `AC7` runs `test_declared_root.py` in all four trees. So the cabinets get a
small commit **before** any per-script landing, containing exactly:
`scripts/list_results_binders.py`, `scripts/audit_results_binder_forms.py`,
`RESULTS_BINDERS_MANIFEST.json`, `DECISION_results_binder_era.md`, `PLAN_results_binders_migration.md`
(new files there → `git checkout main -- <paths>` then commit; no hand-resolved conflict, which is
what one-owner-per-file exists to avoid). `RESULTS_BINDERS_BASELINE.md`,
`results_binders_baseline.json` and `remaining_results_binders.txt` **stay on `main`** and are
declared as such in the manifest: one baseline serves all four trees because the record is one tree
object, and the manifest says which tree it was measured in.

**3.7 `results/README.md` — the `AC6` contract line must NOT go there.** `results/README.md` is
**tracked and inside the legacy record**: editing it changes `git rev-parse <ref>:results` away from
`0bcaaa01…` and **breaks `test_declared_root.py` check 6** — the very declaration the writers depend
on (§1(a) of the ruling). Put the writers' new destination in a root-level file
(`CABINET_STRUCTURE.md`'s existing addendum is the natural home, one owner per file) or in the
manifest's `scope_pair`. **Named here because the ruling's §4 offers "the plan card may add a contract
line" without naming the file, and the obvious file is the one file that cannot take it.**

---

## 4. THE 22, ONE ROW EACH

`role` · sites at `7c16ea3` · the edit · **before** (command → number, exit, stdout sha256 prefix) ·
**after** (expectation). All "before" values are from `results_binders_baseline.json`; the ones
marked ✔ were **re-produced by this card at `7c16ea3`** (exit code and stdout sha256 identical).
Run everything in a scratch worktree of `BASE`, on a branch.

### Band 1 — the three WRITERS, before any cabinet run (ruling §7.2)

**1. `canonicalise_filenames.py`** · writer (rename) + reader · sites `:28` `RESULTS`, `:58` glob,
`:89` collision probe, `:99` `src,dst`.
*Edit:* read scope = domain(); **`WRITE = _root.results_dir()` resolved once**; for every candidate
whose directory is not `WRITE`, print the intended rename and **refuse to touch the bytes** —
`  REFUSED (not the write scope): <have> -> <want>`. `--apply` with no in-scope candidate writes
**nothing at all** (no empty `RENAME_MANIFEST.json`, no dirty tree). Collision probe read against the
in-scope directory only.
*Before:* `python3 canonicalise_filenames.py` → DRY RUN, **208 rename(s)**, 7 SKIP (4
`CHESS_GAME_*/CHESS_VOID_*`, `DEPTH_TEST.json`, `DEPTH_TEST2.json`), exit **0**, sha `f2585f61fdfc07f0` ✔.
*After:* still **208 proposals** (the domain holds the same 317), 7 SKIP, plus
`write scope: <declared ROOT>/<cabinet>` and `208 outside the write scope, 0 applied`; exit 0;
`git status` clean. **This is the one that must land first: today `--apply` rewrites the record in
place and changes the tree object.**

**2. `annotate_superseded.py`** · writer (`results/supersessions/*.json`) · sites `:36` `RESULTS`,
`:37` `OUT`, `:70` glob (inside `bundles_with_game_names`, which also imports the gate).
*Edit:* read scope = domain() for the bundle sweep; `OUT = os.path.join(_root.results_dir(),
"supersessions")`; `os.makedirs(OUT, exist_ok=True)` only there; refusal propagates (exit non-zero,
nothing written, remedy named).
*Before:* `python3 annotate_superseded.py --dry-run` → **151 bundle(s) claim a game with no state**;
151 records already on disk; exit **0**, sha `c862a76ce6e29993` ✔.
*After:* **151** (equal), records on disk still **151** (`ls results/supersessions | wc -l`), exit 0.
*Then the `AC5` demonstration, not an argument:* write **one** record from a **cabinet** worktree and
read it back from `main` — the gate must find it (`test_game_states.py`'s supersession lookup walks
`DOMAIN`). Before the migration the cabinet's write lands in the cabinet's duplicate and `main`'s gate
does **not** see it (measured in the ruling §1(c)). Expect: cabinet exit 0, file at
`<declared ROOT>/<cabinet>/supersessions/<stem>.json`; `main`'s gate reports one fewer "claims game"
bundle. **Delete the demonstration file afterwards** (it is in the declared root, not a git tree, so
nothing reverts it for you) and record the removal.

**3. `chess_game.py`** · writer · sites at `8f51ae8`: `:574` `REASONING_OUT` (a module global —
`global REASONING_OUT` at `:565`, consumed at `:455`/`:457`/`:469` — keep that shape and assign it from
`results_dir()` at the same point), `:599` `os.makedirs(os.path.join(HERE, "results"))`,
`:634` `CHESS_GAME_*.json`; `:597-598` the LOG dir is **`t_c442023d`'s and is already landed**
(`_root.log_dir(HERE)`) — **do not touch those two lines**.
*Edit:* `RES = _root.results_dir()`; `os.makedirs(RES, exist_ok=True)`; both outputs under `RES`.
*Control (it is NOT RUN in any baseline — it spawns `llama-server`):* measure the **refusal** and the
write set instead:
```
python3 chess_game.py --entrant /nonexistent.gguf            # expect exit 2, "ENTRANT ABSENT", nothing written
CABINET_RESULTS=$(pwd)/results python3 chess_game.py --entrant /nonexistent.gguf
                                                            # expect exit 1, "REFUSING", nothing written
git status --porcelain                                       # expect: no change from either run
```
*Before:* NOT RUN; published artifacts counted instead — 4 `CHESS_GAME_*.json` + 1 `CHESS_VOID_*` +
2 `CHESS_RUN_*.out` in the legacy record, **0 readers**, nothing moved by this migration (ruling §4).
*After:* both controls as above; no byte under `<worktree>/results`.
*Manifest:* two edges — results-write `migrated:<commit>`, log
`deferred:log-coordinate:t_c442023d` + `landed_by: 8f51ae8` (`G8` checks it against `LOG_EDGES.json`).

### Band 2 — the run's own instruments (ruling §7.3)

**4. `check_run.py`** · reader · at `8f51ae8`: `:80` the results pattern (**yours**); the log
candidate at old `:112` is **gone** (`t_c442023d` re-pointed it to `_root.log_path(HERE)`;
`LOG_EDGES.json` carries it as migrated) — **not yours, do not re-edit it**.
*Edit:* the pattern becomes the domain loop + `print_scope`.
*Before, **re-measured by this card at `8f51ae8`** (main, clean tree, read-only):* expected entrants
59, bundle files **72**, ENTRANTS MEASURED **38**, never ran 8, `STATE: UNKNOWN — 46 of 59`, exit
**1**. Numbers **identical** to the filed baseline; stdout sha differs (`26ce82eed983b8d1…` vs
`c35e66ed6628e9ad…`) **only in the `last progress: 436578s ago` line** — a clock token. This is the
masking rule of §1.4 demonstrated on the one script another card moved.
*Manifest:* results-read `migrated:<commit>`; log coordinate
`deferred:log-coordinate:t_c442023d` + `landed_by: 8f51ae8`.

**5. `analyse_card.py`** · reader · `:28` `RESULTS`, `:35` glob.
*Before:* 33 graded entries; belts W2 Y3 O9 G19; R1 89.9% SATURATED, R2 61.6%, R3 75.8%; aggregate
6 distinct / 6 raw; exit **0**, sha `32499b44304ce79d` ✔. *After:* equal (317/72/63/38 path-set).

**6. `build_roster.py`** · reader, and a writer at the **tree root** (`roster.html`) · `:186` glob.
**Clock-bearing output (`:329`) — mask, do not hash.**
*Before:* regenerated **225 bundles / 225 entries**, 17 controlled pairs; exit **0**; tree delta
` M roster.html`. The **committed** `roster.html` is stale (42/42) — pre-existing, `§4` of the
baseline, and **not** this card's number to fix.
*After:* same counts, same exit; tree delta still exactly ` M roster.html`. Run it in a scratch
worktree (its output is tracked at the root).

**7. `evaluate_v2.py`** · reader · `:12` `RESULTS`, `:20` glob.
*Before:* 33 graded entries; 85 empty/scratched; belts W2 Y3 O9 G19; exit **0**, sha `b4c5934726791dec` ✔.

**8. `evaluate_v3.py`** · reader · `:26`, `:33` (`f"*cardv{card}*.json"`).
*Before:* 38 bundles carrying a measurement; **12/38 = 31.6%** score 6/6 (v2 was 79%); exit **0**,
sha `6b0ab5056cdebb30` ✔.

**9. `evaluate_v4.py`** · reader · **TWO glob sites: `:43` and `:286`** (the second is the one a
one-site migration misses). **Clock-bearing output (`:139`) — mask.**
*Before:* **NO VERDICT — 38 measured of ~46 expected**; 8 entrants empty in EVERY copy; exit **1**.
*After:* same verdict, same exit 1. Exit 1 is the correct state here — do not "fix" it.

**10. `discrimination_report.py`** · reader · `:17` **`HERE = "/home/chilly1/workspace/ocho_arena"`
(ABSOLUTE)**, `:64` glob. *Edit:* the absolute literal goes; scope from the domain.
*Before:* 6 item rates over 38; **discriminating items 2 of 6** (R1.2 60.5%, R1.6 39.5%); exit **0**,
sha `7d05c6dbb359077c` ✔. *After:* equal. **Also measure it from a cabinet worktree**: today the
absolute `HERE` makes it read `main`'s record from any tree; after the migration it reads the tree's
own declared domain. Counts must be identical (one record object), paths different — a finding to
state, not a delta.

**11. `v3_rates_both_readings.py`** · reader · `:20`, `:67` (`*cardv3*.json`).
*Before:* 6 items, both readings; deltas +2.6, +2.6, +2.6, +2.6, **+7.9**, +0.0; exit **0**,
sha `2304ca750e932c5c` ✔.

**12. `render_state_contract.py`** · reader + root-level writer (`RENDER_STATE_SCHEMA.json`, `:71`) ·
`:70` `RESULTS`, `:126` glob. **Absent from all three cabinet trees** → main-only landing, declared.
*Before:* **310 bundles / 225 entries**; 3 event kinds (code_repair 30, structured_output 138,
tool_selection 30); schema sha `8c2db374566c`; exit **0**, sha `b839c2e0635ef248` ✔; tree delta
` M RENDER_STATE_SCHEMA.json`. Committed file is stale (234/151) — pre-existing, not ours.
*After:* same counts; tree delta still exactly ` M RENDER_STATE_SCHEMA.json`.

### Band 3 — the audits and verifiers (ruling §7.4)

**13. `audit_clock_fields.py`** · reader · `:19`, `:30` (`*cardv4*.json`). *Before:* inspects
`BTL-4-IQ2_XXS_cardv4_autofit_neutral_ctx8192_mt3000.json` field by field; publishes no aggregate
count, so the baseline is that filename plus its PRESENT/ABSENT lists; exit **0**, sha `22c89f08122f6c8a` ✔.

**14. `audit_stand_ins.py`** · reader · `:28`, `:33` (`*cardv4*.json`). *Before:* 38 measured v4
entries; **38/38** rounded to 4dp; 17 lost precision; 21 no-op; 0 at full precision; exit **0**,
sha `4645e3b1d5186554` ✔.

**15. `audit_weigh_in.py`** · reader · `:30` — the join is **inline**
(`glob.glob(os.path.join(HERE, "results", "*.json"))`), not via a `RESULTS` constant. *Before:*
bundles **310** / entries **225**; 225 with a division; 221 with BOTH; 4 never offloaded; exit **0**,
sha `c673809a53c60c86` ✔.

**16. `check_field_semantics.py`** · reader · `:24` `HERE`, `:155` `*cardv5*.json` (module level,
`NEWEST = max(..., key=getmtime)`) — the mtime ordering is over the domain, which today only the
legacy entry populates. *Before:* 11 quantity-named fields; **3 MISLEADING** (`gen_tokens`, `secs`,
`trials`); exit **0**, sha `3ad8e1fa9ccc73cb` ✔; `--self-test` → **10/10** (must still pass).

**17. `check_format_fields.py`** · reader · `:38` `RESULTS`, `:183` glob (`--all`).
**Absent from `missile-command` and `zork`** → not landed there, declared in `declared_absent`.
*Before:* `--all` → **317 bundle(s); PASS 0; GRANDFATHERED 316; PROBLEMS 1**
(`Qwen3.5-4B-UD-Q4_K_XL_cardv5_autofit_neutral_ctx8192_mt3000.json`, 5 problems incl. a `footprint_gb`
ZERO); exit **1**, sha `65b1f78f2341383c` ✔. Exit **1 before and after** — that is the state, not a
regression. `--self-test` → **22/22** (must still pass).

**18. `verify_chair_audit.py`** · reader · `:17`, `:23`. *Before:* Green 19 entries; aggregate range
**0.7222 .. 1.0000** (the claim was 0.833-1.000); exit **0**, sha `9dff65cfca4e958d` ✔.

**19. `verify_scope.py`** · reader · `:17` **`HERE = "/home/chilly1/workspace/ocho_arena"`
(ABSOLUTE)**, `:62` (`*cardv3*.json`). *Before:* D3a **59** failing items; D3b **1 with NO raw at
all**; classes {unparseable 14, no_json 1, other 34, truncated 10}; D2 9 re-score higher; exit **0**,
sha `57808391d9d84993` ✔. *After:* equal — and measure it from a cabinet worktree too, as for #10.

### Band 4 — the tests and guards last (ruling §7.5)

**20. `test_no_silent_zero.py`** · reader · `:26` `RESULTS = sys.argv[1] if len(sys.argv) > 1 else
os.path.join(HERE, "results")`. *Edit:* the **default** becomes the domain; the **argv override
stays** — a caller-supplied scope is declared by the caller — but a path that is **outside the
declared domain must be said out loud in the output**
(`  scope  DECLARED BY THE CALLER, OUTSIDE THE DECLARED DOMAIN: <path>`), and the printed scope is
per entry, replacing the single `, {RESULTS}` at `:71`. *Before:* **1494 item records in 310
bundles**; FAIL 64 empty bundles with no failure record; FAIL 1 zero with no reason; exit **1**; stdout
hash not comparable across trees (it prints the tree's path) — compare the two FAIL counts.
*After:* 1494 / 310 / 64 / 1 unchanged, exit 1.

**21. `scripts/prove_declared_slots_parse.py`** · reader (flattening: `os.listdir(rdir)`) · `:22`
`HERE` (repo root), `:101` `rdir`, `:103` listdir. *Edit:* the v6 sweep reads the domain, one entry
at a time, with the **basename-collision refusal** of §2(b). *Before:* `STATE: SINGLE SOURCE`; 4 slots
agree; **38 v6 bundles**, key `R1_conformance x37`; refused: none; exit **0**, sha `122d6ee1e289b183` ✔.
*After:* identical STATE and numbers from the domain.

**22. `scripts/test_declared_slots_guard.py`** · reader of one v6 bundle (`:75`, `:77`) + a
`tempfile` fixture (`:54`,`:55` — those two `results` names are the *sandbox's*, and stay; only the
**source** moves to the domain). *Before:* **2 FAILED — 3/5** (control [1] wants
`('SINGLE SOURCE',0)` got `('BLOCKED',1)`; control [3] wants `('DRIFTABLE',1)` got `('BLOCKED',1)`),
exit **1**, sha `c49ece8e7d965387` ✔ — and this is **pre-existing**: the baseline measured it
IDENTICAL in `main`. **Do not "fix" it in this card**; the before/after statement is "exit 1 with the
same two control failures". If you touch it at all, only the fixture's *source* path changes.

---

## 5. LANDING ORDER — one script per commit, each independently revertible (`AC8`)

Reasons are the ruling's; the ordering constraints this card adds are marked **ORDER**.

1. **Commit 0** (§3) — manifest + guard + ruling. Nothing lands before the state is checkable.
2. **Band 1 — the three writers, before any cabinet run**: `canonicalise_filenames.py`,
   `annotate_superseded.py`, `chess_game.py`. Same urgency as `t_af6fafd9`.
   **ORDER:** land `canonicalise_filenames.py` **first** (it can damage the record today).
   **ORDER:** `chess_game.py` — a sibling card (`t_c442023d`) **edited the same file** (its log dir) and
   has now landed (`8f51ae8`); the file is clean. Base on `BASE`, change only `:574`/`:599`/`:634`, and
   leave `:597-598` alone. **Before editing it, re-read the file and `git status`** — if another card
   has opened it again, **comment on both cards** rather than editing a file another worker holds.
3. **Band 2 — the run's own instruments**: `check_run.py`, `analyse_card.py`, `build_roster.py`,
   `evaluate_v2.py`, `evaluate_v3.py`, `evaluate_v4.py`, `discrimination_report.py`,
   `v3_rates_both_readings.py`, `render_state_contract.py` (main only — absent from the cabinets).
   **ORDER:** `check_run.py` — same sibling card touched it (its log candidate); it has landed, its
   log block is not yours, and its results glob at `:80` is.
4. **Band 3 — audits and verifiers**: `audit_clock_fields.py`, `audit_stand_ins.py`,
   `audit_weigh_in.py`, `check_field_semantics.py`, `check_format_fields.py` (main + `sokoban` only),
   `verify_chair_audit.py`, `verify_scope.py`.
5. **Band 4 — tests and guards last**: `test_no_silent_zero.py`,
   `scripts/prove_declared_slots_parse.py`, `scripts/test_declared_slots_guard.py`.

**Per-landing commit shape** (same pathspec discipline as commit 0 — this working tree is shared):

```
git add <script> && git commit -m "<script>: scope from the declared domain (deferred:t_fdf55800 -> migrated)" -- <script>
BASE_AFTER=$(git rev-parse HEAD)     # paste into RESULTS_BINDERS_MANIFEST.json as migrated:<commit>
```

then a **separate tiny commit** that flips that entry to `migrated:<BASE_AFTER>` and re-runs the
guard (the manifest must not be edited inside the script's commit — one script per commit, and the
guard's own change is its own revertible step). Update the counters' `counter_sha256`/`measured_at`
only in commit 0 and in the final `residue zero` commit.

**`AC9` — four-tree parity, per file, after `main` is complete:**

* **First: the travel commit** (§3.6) — the counter, the form auditor, the manifest, the ruling and
  this plan, to all three cabinet trees (`main` = `8f51ae8`, `cabinet/sokoban` = `9aa5a21`,
  `cabinet/missile-command` = `cabinet/zork` = `07d8815` at drafting time; re-read before landing).
  Without it the cabinets' `test_declared_root.py` cannot run its new section 8.
* `cabinet/sokoban` (21 binders, missing `render_state_contract.py`)
* `cabinet/missile-command` (20, missing `render_state_contract.py`, `check_format_fields.py`)
* `cabinet/zork` (20, same two)
* Per-script commits touch **one file each**, so: `git cherry-pick -x <commit>` where the file exists;
  where the manifest declares `declared_absent`, **skip it for that tree and say so** — absence is
  declared, never counted as residue and never read as an unfinished landing.
* Re-derive per-tree presence at `BASE` before you start (it is measured, not inherited):
  `for T in <four trees>; do python3 scripts/list_results_binders.py $T; done` → **22 / 21 / 20 / 20**.
* `git status --porcelain` clean in all four trees between landings.

---

## 6. REGRESSION SET AFTER **EVERY** LANDING (`AC7`)

```
# in each of the four trees, after every landing (report-only mode for the sweep)
python3 test_declared_root.py      # expect exit 0 in all four (25 checks)
python3 test_game_states.py        # expect exit 0; "checked 6 task file(s) and 317 bundle(s)";
                                   # NEW violations 0; HISTORICAL (superseded) 301
python3 reconcile_and_backfill.py  # report only: 310 arena bundles / 225 carrying results / 64 empty
                                   # / cardv4 6. Do NOT run its write path: the provenance guard's
                                   # REJECT is still REJECT (17, unchanged after t_c442023d).
python3 <the script you just landed>   # its own control: before == after per §4 row, exit code equal,
                                       # masked diff empty
git status --porcelain             # expect: clean (or exactly the declared root-level writer delta:
                                   # ` M roster.html` / ` M RENDER_STATE_SCHEMA.json`)
python3 scripts/list_results_binders.py <tree>   # residue N decreases by exactly 1 per landing;
                                                 # exit non-zero while N > 0; prints manifest path + sha256
                                                 # (its guard is section 8 of test_declared_root.py, already
                                                 # run above -- do not keep a second place to run by hand)
```

**Re-measured by this card at `7c16ea3` (scratch worktree, on a branch; `7c16ea3` is the commit
before the `logs/` landing, so re-measure the same four lines at `BASE` before landing anything):**
`test_declared_root.py` exit **0**; `test_game_states.py` exit **0**, 317 bundles, 0 new violations,
301 historical; `reconcile_and_backfill.py` exit **0** (report-only). The whole 21-command before-set
left the tree with exactly ` M roster.html` and ` M RENDER_STATE_SCHEMA.json` — **no other byte
moved**. If that stops being true, that is a finding, not noise.

---

## 7. ROLLBACK

* **One script:** `git revert <that commit>` in each tree where it landed (that is the whole reason
  for one script per commit, `AC8`). Then flip the manifest entry back to `deferred:t_fdf55800`,
  re-run §6, and record the revert commit in the manifest's edge.
* **Commit 0:** `git revert` it — this restores `scripts/list_results_binders.py`'s hardcoded `FIXED`
  set, deletes the manifest and the guard, and removes `DECISION_results_binder_era.md`. Only do this
  if the migration itself is abandoned; revert the bands **first**, or the counter has no manifest to
  read.
* **Cabinet branches:** revert in the same per-file shape; a `cherry-pick -x`'d commit reverts
  cleanly with `git revert -m` is **not** needed (no merges were made).
* **Nothing here is a data rollback:** the legacy record's bytes and the duplicate trees' bytes are
  never touched (`AC11`), so reverting a script cannot lose a measurement.

---

## 8. WHAT MUST NOT CHANGE (`AC11`)

`run_card.py`'s refusal shape; `cabinet_root.py`'s single definition (root, cabinet carrier,
`domain`, duplicates) — *read it, do not edit it* (`t_c442023d` landed its log functions there in
`8f51ae8`; do not race a later card for it); any cabinet-owned simulator (`sokoban.py`,
`missile_command.py`, `zork.py`);
`results/README.md` **and every tracked byte under `results/`** (see §3.7); the duplicate trees;
`logs/` and every log edge (**`t_c442023d`'s**, landed in `8f51ae8`, declared in `LOG_EDGES.json` —
this card inherits them as `deferred:log-coordinate` and does not touch them; the provenance guard's
REJECT is still REJECT, 17, unchanged).

---

## 9. CARRIED, NOT DECIDED HERE

* **`depth_test.py:27` / `depth_test2.py:32`** — writers into **main's legacy record by ABSOLUTE
  path**, from any worktree, invisible to the counter's join-forms; strict reading gives **24 on
  main** rather than 22. Routed to the Chair as **`t_5742bdac`** (created by this card).
  **Manifest status here: `out-of-scope:t_5742bdac`** — declared, never silent.
* **`darts/darts.py:706,715`** — `--out` defaults to `<worktree>/darts/results` (5 tracked
  `darts_v1_*.json`); the same `t_5742bdac`.
* **`results/README.md`** — cannot take the `AC6` contract line (§3.7); the destination line goes to
  a root-level doc.
* **The three duplicate `results/` trees** — now unreachable by anything that follows the
  declaration. That is the intended consequence; whether they are deleted is **not** this card's
  question.
* **4 `CHESS_GAME_*.json` artifacts** in the legacy record (0 readers): declared in place;
  `chess_game.py` re-points only where **new** ones land, so no published number moves.
* **Stale tracked renderings** (`roster.html` 42/42 vs 225/225; `RENDER_STATE_SCHEMA.json` 234/151 vs
  310/225) — pre-existing, measured by the baseline; a separate question with a separate fix.

---

## 10. ACCEPTANCE — `AC1`-`AC11` → the step that satisfies each

| AC | satisfied by |
|---|---|
| AC1 residue zero, declared, four trees | §3.2-3.4 (manifest + guard + counter exit non-zero) ; §5 per-tree counts 22/21/20/20 ; the log coordinate declared as its own class |
| AC2 collisions / disjointness / check 6 | §2(a),(b) ; §6 (`test_declared_root.py` exit 0 in four trees) |
| AC3 before/after per script | §1.4 masking recipe + every §4 row's before/after, attached to `t_fdf55800` |
| AC4 scope printed with the count | §2 `print_scope` idiom, in every migrated reader |
| AC5 writers refuse, only to the write scope; no byte in the legacy record | §2 writer idiom + §4 rows 1-3, incl. the cross-worktree supersession demonstration |
| AC6 no new write in a git tree (+ contract line) | §3.7 (the destination line goes outside `results/`) + §4 rows 1-3 |
| AC7 regression after every landing | §6, with the base values re-measured by this card |
| AC8 one script per commit, independently revertible | §5 commit shape ; §7 rollback |
| AC9 four-tree parity, presence measured | §5 parity block ; §3.2 `declared_absent` |
| AC10 the ruling lands as a tracked artifact | §3.1 (+ `G5` in the guard) |
| AC11 what must not change | §8 |

**Card constraint honoured:** this plan edited no script. Its own commit adds exactly
`DECISION_results_binder_era.md` (the ruling verbatim) and this file.
