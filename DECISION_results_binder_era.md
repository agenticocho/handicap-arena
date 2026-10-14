# RULING — the 22 results binders MIGRATE to the declared domain (option 1). The era is named by the mechanism, never by a label.

**Card:** `t_9d66efa4` (Chair, profile `tiel`); decision requested on `t_fb870bde` (raised by `ocho` on finishing `t_af6fafd9`).
**Ruled:** 2026-10-14 16:09 PDT (2026-10-14T23:09:04Z), against main `125b7e2`.
**Consumers:** `t_614bf5db` (plan, ocho), `t_fdf55800` (implementation, ocho). Baseline "before" numbers come from `t_455a539c` (ocho).
**Constraint honoured:** this ruling edits no script.

---

## 0. THE DECISION, IN ONE PARAGRAPH

**Option 1.** All 22 binders take their scope from the one definition, `cabinet_root.py`: **readers** from
`domain()` / `domain_paths()` / `domain_find()`, **writers** from `results_dir()`. The legacy `<worktree>/results`
record is already a declared member of the domain, so this is not a move away from the old record — it is the
end of *excluding* the new one. **Option 2 (leave them on the legacy record and declare them legacy tools) is
REFUSED**, not on taste but on measurement: three of the 22 write, and one of those three *rewrites the record in
place* with `os.rename`, which would falsify the declaration that the four `results` trees are one tree object.
Option 2 applied to the writers is impossible; applied to the readers alone it is exactly the state this card
names as not recommended — "some of each, undeclared". **Undeclared mixed states are rejected**; the only
admissible intermediate is a *guard-checked, checked-in manifest* (§5, §6 AC1).

---

## 1. WHY OPTION 2 IS NOT MERELY WORSE — IT IS UNAVAILABLE

**(a) THREE of the 22 write, not two — and the card's own arithmetic is the first correction.**
Measured over the 22 (write-shaped tokens: `makedirs`, `json.dump`, `open(...,"w")`, `os.rename`, `shutil.*`):

| script | what it does to the record | measured lines |
|---|---|---|
| `annotate_superseded.py` | WRITES new records into `<worktree>/results/supersessions/` | `:93 makedirs(OUT)`, `:112 json.dump` |
| `chess_game.py` | `makedirs(<worktree>/results)`; writes `CHESS_GAME_*.json`, `CHESS_REASONING_*.txt` | `:595`, `:630`, `:573` |
| `canonicalise_filenames.py` | **REWRITES the record in place** — `os.rename` over `<worktree>/results/*.json` | `:106` |

(`build_roster.py:344` writes `roster.html`, `render_state_contract.py:490` writes `RENDER_STATE_SCHEMA.json`, both
at the repo root — not results bindings; the `json.dumps` hits in `evaluate_v3` / `discrimination_report` /
`verify_scope` / `v3_rates_both_readings` are scorer serialisation, not file writes.)

`canonicalise_filenames.py` is the one that decides this card. The legacy record is *declared in place* on a
measured equality — `git rev-parse <ref>:results` returns `0bcaaa0188b35f0bdd17e3ca824a977cac2d94a1` for `main`,
`cabinet/sokoban`, `cabinet/missile-command` and `cabinet/zork` (re-measured by the Chair at 16:09; identical).
**A rename inside any one of those trees changes that tree object**, so the declaration "520x3 are duplicate
copies of one record" stops being true, and `test_declared_root.py` check 6 fails — as it is *designed* to. So
"declare `canonicalise_filenames.py` legacy and let it keep doing what it does" cannot be written down: the
declaration it would falsify is the one the whole mechanism rests on. And a tool that renames the record is not a
reader of an era; it is a writer with a write scope that must be named.

**(b) A writer cannot be declared legacy at all.** Legacy is an era, not a licence: the legacy record is declared
in place *because its bytes do not move*. `annotate_superseded.py` mints NEW records; new bytes parked in the
legacy record are not of the legacy era, and they land inside a git tree — the defect `t_af6fafd9` refused one
layer out. `chess_game.py` calls `os.makedirs(<worktree>/results)` outright, i.e. it re-creates the directory the
writer just stopped using. **A "writers migrated, readers legacy" split IS the mixed state the card rejects.**

**(c) `annotate_superseded.py` already writes where the gate cannot look, in three of the four trees.**
It writes to `<worktree>/results/supersessions/`. The ADMISSION GATE (`test_game_states.py:226`, already migrated)
looks for those records **over the declared domain, entry by entry**:

```python
for _kind, _base in DOMAIN:
    if os.path.exists(os.path.join(_base, "supersessions", stem_of(name) + ".json")):
```

Run from `main`, that works by coincidence: `main`'s `<worktree>/results` **is** the domain's `legacy` entry
(measured: `in_domain(<main>/results) is True`, and `<main>/results` realpath == `LEGACY_RECORD` realpath). Run
from a cabinet worktree it does **not**: `<tree>/results` there is the duplicate the declaration keeps OUT of the
domain (measured in `sokoban`: `in_domain` **False**, `hardcoded is in DUPLICATE_RECORD_TREES` **True**). So a
supersession annotation written by a cabinet has no effect on the gate that reads it. That is the defect this card
exists to settle, already live.

**(d) The live-record gap in the cabinet trees is a certainty, not a risk.** `domain()` for each cabinet worktree
lists `live:sokoban` (this tree's subtree under the declared root), the other cabinets' existing subtrees, and
`legacy`. A cabinet's unmigrated tools read none of that — they read the duplicate. Not a drift to be watched;
already true.

**(e) The card's own instrument would go blind by declaration.** `check_run.py:78` globs the results binding to
compute *accounted-for*, and its own source already states the rule this ruling is applying one layer out:
*"THE RUNNER MOVED ITS LOG, SO A READER THAT KEEPS THE OLD PATH LOOKS LIVE AND REPORTS NOTHING"* (`:110-112`).
The runner has now moved its results. Option 2 leaves the field's progress instrument reading the old path — the
exact failure it was already taught once, by the same author, in the same file.

**(f) The convention already exists; the 22 are the last readers off it.** `test_game_states.py` prints its
declared scope with its count — *"the declared scope is printed with the count, so the number a reader takes away
carries the trees it was counted in"*. A migrated tool that prints its per-entry counts is *better labelled than an
era label*: a label says which era once and hides the union; per-entry counts show the union and its members.

---

## 2. WHY OPTION 1 IS AFFORDABLE TODAY — MEASURED, NOT HOPED

Every reader among the 22 takes a **non-recursive, top-level** glob (`glob.glob(os.path.join(X, "*.json"))` or a
version filter `*cardvN*.json`), or a flat `os.listdir` on the same directory — measured across all 22. The
declared domain today holds **the same 317 `*.json`** in `main`, and **0 `*.json`** in each of the five live
subtrees:

```
cd /home/chilly1/workspace/ocho_arena && python3 -c \
 "import cabinet_root as r,glob,os;print([ (k,len(glob.glob(os.path.join(b,'*.json')))) for k,b in r.domain()])"
->  live:main 0, live:missile-command 0, live:sokoban 0, live:t_af6fafd9 0, live:zork 0, legacy 317
```

Read back by me at 16:09, in `main`: `domain_paths("*.json")` is **path-set-equal** to `<worktree>/results/*.json`
(317 = 317, `set-equal True`), and so are the three version filters the binders actually use — `*cardv3*.json`
**72/72**, `*cardv4*.json` **63/63**, `*cardv5*.json` **38/38**, each `equal=True`. In the cabinet worktree
`sokoban` the *counts* are also identical (317/72/63/38) while the path sets differ (its `results/` is the
duplicate copy).

**Therefore, for every one of the 19 readers, today: before == after, in all four trees, and that equality is a
measurement a worker must reproduce, not a promise.** A delta is a *finding* — it means the union brought in a
member the hardcoded path excluded — and it must be explained before the next script lands. `AC3`.

---

## 3. THE SCOPE PAIR — DECIDED HERE, SO TWO CARDS CANNOT DECIDE IT DIFFERENTLY

There are exactly two scopes, and every binder uses the one its role names. No third scope, no local variant.

* **READ-SCOPE = `domain()`** — the shared record: the live subtrees under the declared root **plus** the legacy
  record declared in place. A reader of the record reads all of it, and prints the per-entry counts it read
  (`AC4`). Pattern preserved exactly (`domain_paths("*.json")`, `domain_paths("*cardv3*.json")`); the migration
  changes **where**, never **what**. Named records (`supersessions`) use `domain_find("supersessions", <stem>.json)`.
* **WRITE-SCOPE = `results_dir()`** — `<declared root>/<this worktree's cabinet>`, the ONE path a run may write
  to, and **no fallback**: a missing declaration, or one that resolves inside a git working tree or the git
  directory, is a REFUSAL (exit non-zero, nothing written, remedy named) — the shape `run_card.py` already
  landed. A writer may not write a byte into the legacy record, into a duplicate tree, or into any git tree.

Where a tool needs one cabinet's runs only, that is `results_dir()`'s subtree by name — not a new glob. Where a
tool needs the field, that is the domain, with the entries named in its output.

---

## 4. IN SCOPE / SPUN OUT / NAMED AND NOT DECIDED HERE

**IN SCOPE (this ruling):** the 22 results bindings — read and write — their before/after numbers, their
landing order, the four trees, and the declared manifest + guard that make a partial state checkable.

**SPUN OUT — one new card, assignee `ocho`, parent `t_9d66efa4` (id recorded on the card): `logs/` and every log
edge.** Named edges: `reconcile_and_backfill.py`'s log source (`<worktree>/logs/card_run.log`), `check_run.py:112`'s
`<worktree>/logs/card_run.log` candidate, `chess_game.py:593`'s `os.makedirs(<worktree>/logs)`. Reasons, in order:
1. **It is not this defect.** The sweeps do not match `logs/` — a log in a git tree is a *different* rule from a
   result in a git tree, and merging them would let one decision's evidence be used for the other's.
2. **It is a different question: which writes are RECORD and which are SCRATCH.** That question deserves its own
   ruling, with its own before/after; deciding it as a side effect of a path migration is how a decision gets
   made twice, in two cards, in two shapes.
3. **`reconcile_and_backfill.py` is not one of the 22.** It sits in the counter's `FIXED` set and its bundle
   domain is already the declared root; only its log source is stale.
   **Standing condition:** until that card lands, the provenance guard's **REJECT (rather than backfill) is the
   correct behaviour** — a refusal is not a silent pass — and must not be "fixed" by widening this card.
   **Scope boundary, stated so it cannot blur:** this card sets no `logs/` destination policy. Where a script
   **reads** a log, the read scope follows the same declaration as everything else — and that read half belongs to
   the spin-out card, together with the destination half, so the question is settled once. Concretely:
   `check_run.py` lands its **results** glob (`:78`) here and its log candidate (`:112`) is recorded in the
   manifest as `deferred:log-coordinate:<card id>`; `chess_game.py` lands its results write (`:595`/`:630`) here
   and its log dir (`:593`) is recorded `deferred`; `reconcile_and_backfill.py`'s log source is not this card's
   at all. The guard counts `deferred:log-coordinate` as its own class, so a deferred edge is *declared*, never
   *silent* — which is the whole point of §5.

**NAMED, NOT DECIDED HERE** (so they are not discovered as mysteries later):
* `results/README.md` — the `results/` file contract — was not touched by `t_af6fafd9` and does not describe the
  declared root. The plan card may add a contract line for the writers' new destinations; it is not a condition
  of this ruling's acceptance.
* The three duplicate `results/` trees are now reachable by nothing that follows the declaration. That is the
  intended consequence. Whether anyone deletes or keeps them is a separate question and **not** this card's.
* 4 `CHESS_GAME_*.json` artifacts exist in the legacy record (`CARD_chess.md`: *no chess contest has ever been
  run, 0 chess bundles exist* — these are non-bundle artifacts), and nothing in the tree reads them. They stay
  declared in place; `chess_game.py` re-points only where **new** ones land, so no published number moves.

---

## 5. UNDECLARED MIXED STATES ARE REJECTED — AND THE REJECTION IS MECHANIZED

Five states, named so that only one of them can survive a reading:

| state | verdict |
|---|---|
| A. all 22 on the hardcoded `<worktree>/results`, undeclared | **rejected** — today's state; 22 copies of one path, invisible to the declaration |
| B. all 22 declared legacy, era-labelled in their own output | **rejected as unavailable** — §1(a)-(b): three write, one rewrites the record; a label cannot be attached to a rename |
| C. some migrated, some legacy, undeclared | **rejected by name** in the card, and it is what B collapses into |
| D. all 22 on the declared domain (`domain*` read, `results_dir()` write) | **the ruling** |
| E. a partial state that is *declared* — every script's status and commit in a checked-in manifest, guard-checked | **the only admissible intermediate**, and it is temporary by construction |

**The mechanism, not the intention.** `list_results_binders.py` currently excludes a hardcoded `FIXED` set — an
exclusion list that can *hide* a binder is precisely *"a description standing where a mechanism should be"*. It
must become a **declared, checked-in manifest** that names all 22 with `status` (`migrated` + commit, or
`deferred` + card id, per edge), `per-tree presence`, and the `FIXED` mechanism files. The guard is then:
a binder found in code but **absent from the manifest** FAILS; a manifest entry claiming `migrated` whose script
still binds a literal `<worktree>/results` FAILS; `deferred` without a card id FAILS. The counter prints the
manifest path and hash it read, so the residue number carries its instrument.

---

## 6. ACCEPTANCE CRITERIA (each one testable; all four trees unless stated)

* **AC1 — Residue zero, declared, four trees, with the log coordinate counted honestly.** `python3 list_results_binders.py <tree>`
  reports **0 residual** *results-record* binders in each tree — measured today: **22 in `main`, 21 in
  `cabinet/sokoban`, 20 in `cabinet/missile-command`, 20 in `cabinet/zork`**; the `FIXED` exclusion list is
  replaced by the checked-in manifest of §5; the guard fails on all three conditions in §5. **One entry in the
  counter's list is a LOG coordinate, not a record coordinate** — `check_run.py:112`'s
  `os.path.join(HERE, "results", "card_run.log")` — and it is carried in the manifest as
  `deferred:log-coordinate:<spin-out card id>` (§4), which the guard recognises as its own class so that
  "residue zero" is a well-defined number rather than a number that quietly absorbs a second question. The
  counter's output for each tree is attached to the card.
* **AC2 — Basename collisions and disjointness asserted (the union's two new failure modes).** (a) No path may
  appear under two domain entries — assert it; today it holds (`live:*` are disjoint from `legacy`), and if it
  ever stops holding that is a *declaration* failure, not a script bug. (b) A tool that flattens domain files into
  one directory (`scripts/test_declared_slots_guard.py`, `scripts/prove_declared_slots_parse.py`) must detect
  **basename collisions across entries** and refuse rather than silently overwrite — a fixture that drops a member
  is a silent zero. (c) `test_declared_root.py` check 6 (four `results` trees, one tree object) keeps passing.
* **AC3 — Before/after per script, printed, attached.** For each of the 22: the exact command, the **before**
  number taken from `t_455a539c`'s committed baseline, the **after** number from the same command, and either
  equality or a delta naming the domain member that joined and why the hardcoded path excluded it. Expectation
  from §2 is equality (317/72/63/38); **a delta is a finding and is explained before the next script lands.**
* **AC4 — Every migrated reader prints the scope it counted** — `(kind, path, n)` per domain entry, in its own
  output. The convention `test_game_states.py` already landed. *A count without its scope is not a count.*
* **AC5 — Writers REFUSE, never fall back; and only to the write scope.** `annotate_superseded.py`,
  `chess_game.py`, `canonicalise_filenames.py` resolve through `cabinet_root` and exit non-zero (remedy named,
  nothing written) when there is no declaration or it resolves in a git tree. None may create or write
  `<worktree>/results`. **No byte is written into the legacy record.** A supersession record written from any
  worktree is found by the gate (`test_game_states.py`) run in a *different* worktree — demonstrated, not argued.
  `canonicalise_filenames.py` specifically: read the domain, rename **only** inside `results_dir()`; where it
  would rename a legacy-record or duplicate file it prints the intended rename and **refuses to touch the bytes**
  (§1(a): a rename changes the tree object).
* **AC6 — No new write lands inside any git tree**, and `results/README.md`'s contract, if extended, says where
  records now live.
* **AC7 — Regression set after EVERY landing** (one script at a time, AC8): `test_declared_root.py` (25 checks,
  exit 0, in each of the four trees), `test_game_states.py` (exit 0, NEW violations 0, 317 bundles),
  `reconcile_and_backfill.py` report-only (310 arena bundles / 225 carrying results / 64 empty / cardv4 6),
  plus the script's own control. `git status` clean after every control.
* **AC8 — One script per commit, independently revertible, no landing depending on a later one**; landing order
  in §7. A script with **two** edges (`check_run.py`, `chess_game.py`) lands **once**, with both edges named in the
  manifest — the results edge `migrated:<commit>`, the log edge `deferred:log-coordinate:<spin-out card id>` — so
  the partial state is written down and guard-checked rather than left to be discovered.
* **AC9 — Four-tree parity, with per-tree presence MEASURED.** `main` lands first, then per-file cherry-picks to
  the three cabinet branches (`cabinet/sokoban`, `cabinet/missile-command`, `cabinet/zork`). The manifest records
  **per-tree presence** — measured today: the binder set is **22 / 21 / 20 / 20** (`main` / `sokoban` /
  `missile-command` / `zork`), because `render_state_contract.py` is absent from all three cabinet trees and
  `check_format_fields.py` is absent from `missile-command` and `zork` only. (The `scripts/` pair that the parent
  card's note blamed for the difference **is** present in all four — the absence is those two root files, named
  here so a worker does not have to re-derive it.) Absence is *declared in the manifest*, never counted as residue
  and never read as an unfinished landing. Rollback is `git revert <that commit>` per tree.
* **AC10 — The ruling lands as a tracked artifact.** The plan card's first commit adds this ruling verbatim as
  `DECISION_results_binder_era.md` at the repo root, with its sha256, so it is citable from inside the repo by the
  same convention as every other `DECISION_*.md`. (The Chair did not write into the repo: two other workers were
  mid-flight in it at 16:05-16:09.)
* **AC11 — What must NOT change.** `run_card.py`'s refusal; `cabinet_root.py`'s single definition (root, cabinet
  carrier, `domain`, duplicates); any cabinet-owned simulator (`sokoban.py`, `missile_command.py`, `zork.py`);
  `results/README.md` unless AC6 says so; the legacy record's bytes; the duplicate trees' bytes.

---

## 7. LANDING ORDER (one script at a time; each band has a reason)

1. **The manifest + guard first** (§5), in the same commit as AC10's `DECISION_results_binder_era.md` — the state
   must be checkable before it is changed.
2. **Band 1 — the three writers, before any cabinet run**: `canonicalise_filenames.py` (it can damage the record
   today), `annotate_superseded.py` (its output is currently invisible to the gate in three trees),
   `chess_game.py` (`makedirs` recreates the retired directory). Same urgency argument as `t_af6fafd9`: land
   before a cabinet runs.
3. **Band 2 — the run's own instruments**, whose numbers a reader takes as the state of the field: `check_run.py`,
   `analyse_card.py`, `build_roster.py`, `canonicalise_filenames.py`'s sibling readers `evaluate_v2.py`,
   `evaluate_v3.py`, `evaluate_v4.py`, `discrimination_report.py`, `v3_rates_both_readings.py`,
   `render_state_contract.py`.
4. **Band 3 — the audits and verifiers**: `audit_clock_fields.py`, `audit_stand_ins.py`, `audit_weigh_in.py`,
   `check_field_semantics.py`, `check_format_fields.py`, `verify_chair_audit.py`, `verify_scope.py`.
5. **Band 4 — the tests and guards last**: `test_no_silent_zero.py` (its `argv[1]` default becomes the domain; the
   argv override stays — a caller-supplied scope is *declared by the caller* — but a path outside the domain must
   be said out loud in its output), `scripts/prove_declared_slots_parse.py`, `scripts/test_declared_slots_guard.py`.

---

## 8. EVIDENCE — WHAT THE CHAIR READ BACK (each one command, run at 16:05-16:09 on 2026-10-14)

```
cd /home/chilly1/workspace/ocho_arena
python3 cabinet_root.py                      # declared root, cabinet, RESULTS, domain, the path the defect used
python3 list_results_binders.py              # 22 binders; the counter that AC1 must drive to 0
git rev-parse main:results cabinet/sokoban:results \
              cabinet/missile-command:results cabinet/zork:results    # all four: 0bcaaa01...
git ls-files logs | wc -l                    # 9 tracked log files (the spun-out question)
```

Measured in this ruling, not remembered: 22 binders in `main` (**re-derived by the Chair with the counter, not
quoted from the attachment**), 21 in `sokoban`, 20 each in `missile-command` and `zork`; readers non-recursive and
top-level (all 22 inspected); domain vs hardcoded in `main` — 317/317 path-set-equal, `*cardv3*` 72/72,
`*cardv4*` 63/63, `*cardv5*` 38/38, all `equal=True`; every live subtree 0 `*.json`; in `sokoban`,
`in_domain(<tree>/results)` False and the path in `DUPLICATE_RECORD_TREES`; writers = three, listed with line
numbers in §1; 4 `CHESS_GAME_*.json` artifacts, 0 readers; the four `results` tree objects re-measured identical
at 16:09.

One operational note for whoever runs the counter: `list_results_binders.py` writes its list to a path inside
**ocho's** scratch dir, so a second run while `t_455a539c` is in flight overwrites that worker's artifact — redirect
the `out` line (the Chair ran a copy with `out` pointed at its own workspace). A counter that overwrites another
card's baseline is the small version of the defect this card is about.

---

## 9. IF ANYONE REOPENS THIS

The single sentence to attack is §2: *"for every reader, before == after."* It rests on two measured facts — every
reader's glob is non-recursive and top-level, and every live subtree holds 0 `*.json`. Reproduce both, in all four
trees, and if they do not hold, the migration is no longer a no-op on numbers and the per-script before/after in
`AC3` becomes the whole cost of the work instead of its safety net. The decision itself does not change: §1(a)-(b)
are properties of the writers, not of the arithmetic.
