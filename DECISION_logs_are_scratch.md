# DECISION — `logs/` IS **SCRATCH**, AND THE LOG COORDINATE IS DECLARED PER BUNDLE

**Card:** `t_c442023d` (assignee `ocho`), spun out of the ruling on `t_9d66efa4` §4, ruling sha256
`55bea450e9ff76181a3e196950b771ee5c247d2356ff5039f4b81fa51d8309f9`.
**Decided:** 2026-10-14, against main `7c16ea3`.
**Constraint honoured:** the results record is untouched. No results binder, no `results/` path, no
`results_dir()`, no `cabinet_root.py` single definition and no cabinet-owned simulator was moved. The
one file this card and `t_fdf55800` both touch is `chess_game.py`, and only its **log** lines
(`:593`, `:594`) — its **results** lines (`:595`, `:630`) belong to `t_fdf55800` and are untouched here.

---

## 1. THE DECISION, AND IT IS ONE CLASSIFICATION FOR THE WHOLE DIRECTORY

**`logs/` is SCRATCH. All of it. There is no record class in `logs/`, and no writer may put one
there.**

It is not a close call, because **the repository had already said so in its own words and by its own
mechanism** before this card was written:

```
.gitignore            *.log            an ignore rule -- a declaration carried by the repo, checkable
                                        with git check-ignore, covering every .log under logs/
FINDING 020           "...A LOG IS NOT A RECORD FORMAT, and this result survived by luck."
probes/SOKOBAN_RUN_20261009-1247_NEW_LEGEND_RECOVERED_FROM_LOG.json
                      "THIS RECORD WAS RECOVERED FROM logs/sokoban_rerun.out ... the per-turn traces
                       are LOST, because a log is not a record format. A record that does not say
                       where it came from is the thing this week has been about, so this one says."
```

Read those two lines together and the classification falls out. The one time a log carried a
published number, **the record was not the log** — the record is the file re-minted in `probes/` with
its source named; the log was the raw material, and the traces in it were lost.

### 1.1 THE WRITE DOES NOT MOVE — AND THAT IS THE DECISION, NOT AN OMISSION

A **record** must sit outside every git tree, because a sweep that can reach it will eventually
rewrite it. That is why `arena.cabinetResults` exists and why `results_dir()` **refuses** rather than
falling back. **Scratch's obligation is the inverse: it must be unable to ENTER the record.**

So there is no `arena.cabinetLogs`, and adding one would be worse than useless:

* it would buy nothing the ignore rule does not already buy; and
* it would buy one thing that is actively wrong — **a missing scratch declaration would refuse a run
  over a diagnostic file.** `run_card.py`'s own header states the sibling rule, two rules above the
  one this project spent the day enforcing: **"SCRATCH, NEVER ABORT."** A diagnostic that can stop a
  run has been promoted to a gate.
* measured, the results-era argument does not even apply here: the sweeps cannot reach `logs/` —
  `cabinet_root.in_domain(<worktree>/logs/anything)` is **False**, asserted by
  `test_declared_root.py` section 5 on this very directory.

**What replaces the current write is a RESOLVED COORDINATE, not a new destination:**

```
BEFORE   run_card.py        log = os.path.join(ARENA, "logs", "card_run.log")     # writer's own location
         arena.py           os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
         chess_game.py      os.makedirs(os.path.join(HERE, "logs"))
         cost_probe.py      os.path.join(HERE, "logs", f"COST_PROBE_{label}.log")
         measure_reasoning_backfill…  os.path.join(HERE, "logs", f"budget_{budget}.log")
         check_run.py       [<HERE>/logs/card_run.log, <HERE>/results/card_run.log]
         reconcile_and_backfill.py    LOG = os.path.join(HERE, "logs", "card_run.log")

AFTER    cabinet_root.log_dir(repo)   = <the worktree repo sits in>/logs      # ONE definition
         cabinet_root.log_path(repo)  = …/logs/card_run.log                   # the run journal
         cabinet_root.log_for(bundle) = the journal the WRITER of that bundle wrote  # per bundle
```

**THE DIRECTORY IS UNCHANGED AND THE RULE IS NOW THE DIRECTORY RATHER THAN AN EXTENSION.** The tree
could absorb a capture because the ignore rule named `*.log` and nothing else — `git add -A` staged
anything else, **and did: nine captures are tracked because of that gap.** The gap is live, not
historical: `scripts/run_guarded.sh` writes `<workdir>/logs/<UNIT>.out`. `.gitignore` now ignores
`logs/` **whole**.

### 1.2 THE NINE TRACKED FILES: DECLARED IN PLACE, AND NOTHING WRITES THEM

`cabinet_root.LEGACY_CAPTURES` names all nine, with the reason, in the repository:

```
logs/arena_v6.out        logs/cost_probe_wide.out   logs/reasoning_ab.out
logs/sokoban_ab.out      logs/sokoban_first_run.out logs/sokoban_pop2.out
logs/sokoban_pop3.out    logs/sokoban_repeat.out    logs/sokoban_rerun.out
```

**They are not deleted and they are not moved, because a PUBLISHED FINDING CITES ONE OF THEM BY
PATH.** `FINDINGS/018` (`logs/sokoban_rerun.out    summary says solved 1`), `FINDINGS/019` (*"its
numbers survive in `logs/sokoban_rerun.out`"*, *"read from `logs/sokoban_rerun.out`"*),
`NEXT_WINDOW.md:50` and `SOKOBAN_VERDICT_1.md:13` all name that path. A move would leave four
citations with no carrier.

So their status is **`in-place`**, and that word is added to this card's two-status vocabulary
deliberately, with its reason: **a byte-frozen declaration is neither a migration nor a deferral** —
it is the same treatment `LEGACY_RECORD` (520 files) and `DUPLICATE_RECORD_TREES` (3 trees) already
get in this same file. What changes for them is only that **the rule now closes behind them**: a
tenth capture cannot be committed unnoticed, because `test_declared_root.py` section 7 fails on any
tracked file under `logs/` that is not in `LEGACY_CAPTURES`.

**THE COUNT IS READ PER TREE, NEVER TYPED.** Measured: `main` and `cabinet/sokoban` track **9**;
`cabinet/missile-command` and `cabinet/zork` track **6** (they lack `reasoning_ab.out`,
`sokoban_pop2.out`, `sokoban_pop3.out`). The `logs` tree object is `a60a5c6d…` on main/sokoban and
`0817e5a4…` on missile-command/zork — i.e. these git trees are **not** copies of one record, unlike
the `results/` trees, and nothing in the decision depends on their being equal.

---

## 2. THE READ HALF: THE EXACT ADMISSIBLE COORDINATE, PER BUNDLE

**The admissible log coordinate for a bundle is the journal of the tree that OWNS THE BUNDLE'S
DECLARED DOMAIN ENTRY** — because that is the tree the writer ran in:

| the bundle sits in | domain entry | the admissible journal |
|---|---|---|
| a live subtree under the declared root | `live:<cabinet>` | `<the worktree on the branch whose last component is <cabinet>>/logs/card_run.log` |
| the record declared in place | `legacy` | `/home/chilly1/workspace/ocho_arena/logs/card_run.log` (`cabinet_root.LEGACY_LOGS`, declared in place) |

`cabinet_root.log_for(bundle)` is that table, in one place, read from git at every call. It is **not**
"`logs/` relative to whoever is reading", and there is **no fallback to the reader's own journal when
the declared one is missing** — the coordinate is declared whether or not a file is there, and a
reader that substitutes its own has re-created the defect.

The cabinet name is matched against `cabinet()` — `branch.split("/")[-1]` — **the same rule that
decided where that worktree's results went**, so this is not a second copy of the cabinet mapping.
Consequence, and it is the point: a card worktree on `wt/t_af6fafd9` resolves by the same rule with
no new entry (measured in section 3).

### 2.1 `reconcile_and_backfill.py` — **RE-POINTED, NOT RULED OUT OF SCOPE**

`cabinet_root` was already its domain. Only its log source was stale, and stale in the exact shape
`check_run.py:110-112` was taught once already by the same author: *"THE RUNNER MOVED ITS LOG, SO A
READER THAT KEEPS THE OLD PATH LOOKS LIVE AND REPORTS NOTHING."*

```
BEFORE   LOG = os.path.join(HERE, "logs", "card_run.log")          # one coordinate for the whole
                                                                    # sweep, derived from the reader
         "source_log": "logs/card_run.log"                          # a relative literal naming no
                                                                    # tree, in a domain that holds
                                                                    # several
AFTER    no module constant; journals resolved per bundle via cabinet_root.log_for(p), and the
         record carries the RESOLVED path in source_log
```

**THE PROVENANCE GUARD IS UNTOUCHED, AND THE STANDING CONDITION STANDS.** Only a line that itself
reports `scored=False` is admissible; a stem collision that reports success is still **REJECTED, not
backfilled** — measured after the landing, still 17 rejections from main. **The guard was not widened
and the results card was not widened.** What changed is only *which file the guard is allowed to
read*, and *that the answer no longer depends on where the reader is sitting*.

### 2.2 AND THE MEASUREMENT THAT IS THE WHOLE CARD

```
$ cd <tree> && python3 reconcile_and_backfill.py        # report-only

BEFORE                                     main    sokoban  missile-command  zork
  log lines available as SOURCE              90        0            0          0
  with an admissible log line                31        0            0          0
  WITHOUT one (left alone)                   33       64           64         64
  REJECTED by the provenance guard           17        0            0          0

AFTER (see §3)                              main    sokoban  missile-command  zork
  log lines available as SOURCE              90       90           90         90
  with an admissible log line                31       31           31         31
  WITHOUT one (left alone)                   33       33           33         33
  REJECTED by the provenance guard           17       17           17         17
```

**ONE DECLARED DOMAIN, THE SAME 64 SILENT BUNDLES, AND AN ANSWER THAT DEPENDED ON WHERE THE READER
WAS SITTING.** From a cabinet, the sweep found **nothing to read at all** and would have left all 64
bundles alone — the REJECT the standing condition permits, but arrived at by blindness rather than by
judgement. `log_for` makes the four trees agree, which is what a declaration is for.

---

## 3. THE EDGE LIST — MIGRATED, DECLARED, OR THE GUARD FAILS

`LOG_EDGES.json`, checked in, because **a list of edges that nothing checks is a resolution, not a
mechanism.** `test_declared_root.py` section 7 reads it and fails if a live log-path construction
appears in a file that is not declared, if a declared anchor has changed shape, or if a file listed
as migrated has started constructing one again.

**MIGRATED (7):** `run_card.py` (the run journal — the write half of this card), `arena.py`
(`arena-server-*.log`, the live-progress evidence `check_run.py` reads), `check_run.py` (the journal
candidates — **the `<worktree>/results/card_run.log` candidate is gone**, a log coordinate sitting
inside the results path, which is this card's coordinate question only), `chess_game.py` (log dir;
the ruling recorded it `deferred:log-coordinate` to this card), `cost_probe.py`,
`measure_reasoning_budget.py`, `reconcile_and_backfill.py`.

**DECLARED, NOT MIGRATED (3), each with its reason in the file:**

* `cabinet_root.py` — `the-one-definition`. The only file that may still build a log path, because it
  is where the rule lives.
* `test_declared_root.py` — `declared-probe`. It constructs a `logs/` path **on purpose**, to assert
  that a file under `logs/` is not in the declared domain. A probe is not an edge.
* `scripts/run_guarded.sh` — `declared-parameter`. It writes `<workdir>/logs/<UNIT>.out`, and the
  directory is **argument `$2`**, not a derivation from the script's own location, so there is nothing
  to re-point. What that edge needed was the ignore rule, and it landed.

**DEFERRED (2):** `sokoban_probe.py` and `sokoban_run.py` still build `PROBE_*.log` / `SOKOBAN_*.log`
from `HERE`. Same one-line change as the seven above. **Not migrated here for OWNERSHIP, not
uncertainty**: the SOKOBAN launch path belongs to the cabinet (CABINET_STRUCTURE.md rule 2), and
FINDING 020 is itself the record of a patch landing in a live `sokoban_run.py`. Status
`deferred:t_c442023d`, and the guard keeps them visible: they cannot be forgotten and they cannot
quietly grow a sibling.

---

## 4. BEFORE / AFTER NUMBERS, WITH THE COMMAND THAT PRODUCES EACH

```
python3 test_declared_root.py            # the controls; both refusal directions are free
python3 test_game_states.py              # the admission gate
python3 reconcile_and_backfill.py        # report-only: writes nothing without --apply
python3 check_run.py v4                  # the field's liveness instrument
git ls-files logs | wc -l                # tracked captures IN THIS TREE
git rev-parse HEAD:logs                  # the logs tree object
git check-ignore -v logs/<name>          # is this path declared unable to enter the record?
python3 cabinet_root.py                  # the resolution, the domain, and the log coordinate
```

| number | before (`7c16ea3`) | after | note |
|---|---|---|---|
| `test_declared_root.py` ok / FAIL | **25 / 0** (all four trees) | **40 / 0** | 15 new checks, section 7; the before-run found 0 failures, so nothing regressed |
| `test_game_states.py` | exit 0, NEW **0**, HISTORICAL **301** | unchanged | run in all four trees |
| `reconcile_and_backfill.py` source lines | 90 / **0** / 0 / 0 | 90 / 90 / 90 / 90 | main / sokoban / missile-command / zork |
| … admissible lines | 31 / **0** / 0 / 0 | 31 × 4 | the reader now finds the writer's journal |
| … REJECTED by the guard | 17 / **0** / 0 / 0 | 17 × 4 | **the guard is unchanged** |
| `check_run.py v4` | 46 of 59 accounted, 38 measured, all four trees | unchanged | its log candidates are declared now |
| `git ls-files logs` | 9 / 9 / 6 / 6 | **9 / 9 / 6 / 6** | declared in place: no capture moves, none is lost |
| `git check-ignore logs/NEW_CAPTURE.out` | **not ignored — stageable** | ignored | the extension rule → the directory rule |
| `git check-ignore -v logs/card_run.log` | `.gitignore:7:*.log` | `logs/` | one rule, whole directory |

**§4.1 THE FOUR TREES, READ BACK.** Filled by the commit that follows the landing: a commit cannot
report the read-back of cherry-picks it has not been cherry-picked into yet. Every number below was
produced by `bash runall.sh after` (the harness in the card's workspace) against these four commits,
2026-10-14 ~16:25 PDT.

```
tree                      HEAD        logs tree HEAD:logs   test_declared_root   backfill SOURCE / admissible / REJECTED   test_game_states
main                      8f51ae8     a60a5c6d…             40 ok / 0 FAIL       90 / 31 / 17                                NEW 0 / HIST 301
cabinet/sokoban           9aa5a21     a60a5c6d…             40 ok / 0 FAIL       90 / 31 / 17                                NEW 0 / HIST 301
cabinet/missile-command   07d8815     0817e5a4…             40 ok / 0 FAIL       90 / 31 / 17                                NEW 0 / HIST 301
cabinet/zork              07d8815     0817e5a4…             40 ok / 0 FAIL       90 / 31 / 17                                NEW 0 / HIST 301
```

**NONE REGRESSED, AND THE TWO COLUMNS THAT MOVED ARE THE CARD:** `test_declared_root.py` 25 → 40 ok
with 0 failures in every tree; the backfill's source count in the three cabinet trees **0 → 90** and
its admissible lines **0 → 31**. `check_run.py v4` reports `46 of 59 accounted for (38 measured)` in
all four trees, unchanged. `git ls-files logs` is **9 / 9 / 6 / 6** and `HEAD:logs` is **unchanged in
every tree** — declared in place means exactly that: no capture moved into or out of git.

**AND THE TREES DIVERGE ON ONE FILE, NAMED RATHER THAN SILENCED.** The landing was applied per file
(CABINET_STRUCTURE.md rule 2): ten files had pre-images identical to main's and were taken whole;
`arena.py` (older on missile-command/zork) and `CABINET_STRUCTURE.md` (behind main on all three) were
carried by hand, and `measure_reasoning_budget.py` does not exist on missile-command/zork so it has no
log edge to migrate there. The three cabinet copies of `CABINET_STRUCTURE.md` remain **behind main's**
by the 2026-10-14 addendum and the `## LANDED` section — **pre-existing divergence, not this card's,
and named in each copy** so it is not discovered as a mystery later.

---

## 5. NAMED AND NOT DECIDED HERE

* **The 292 other files under `logs/`** (untracked, ~4.4 MB of `arena-server-*.log` and per-model
  logs) **are left exactly where they are.** They were already ignored; they are now ignored by the
  directory rule. Nothing was deleted, because scratch that is already on disk costs nothing and
  deleting a log to prove a classification would be a destructive way to make a point.
* **`written_by` in the backfill record** said `"backfill_empty_reasons.py"` — **a file that does not
  exist in this tree.** Corrected in passing to `reconcile_and_backfill.py` and declared here, in the
  same dict and for the same reason as `source_log`: a literal standing where a resolved value
  belongs. It is named rather than smuggled.
* **The results half** is `t_fdf55800` under the ruling on `t_9d66efa4`. This card touched no results
  binding; the one log coordinate that sat inside a `results/` path (`check_run.py`) was owned here as
  a coordinate question only.
* **Whether the two deferred SOKOBAN edges should be migrated by this card** is a question about
  ownership, not about the rule, and it is the Chair's if he wants it answered differently.

---

## 6. ACCEPTANCE, READ BACK

1. **One classification, stated:** `logs/` is **SCRATCH** — §1, `cabinet_root.LOGS_ARE`, and printed
   by `python3 cabinet_root.py`. What replaces the write: a resolved coordinate, §1.1. The nine
   tracked files: `LEGACY_CAPTURES`, in place, §1.2.
2. **The read half:** the admissible coordinate per bundle, §2; `reconcile_and_backfill.py`
   **re-pointed**, with the guard untouched, §2.1; the measurement in §2.2.
3. **Before/after numbers with their commands:** §4.
4. **Tests re-run in all four trees, none regressing:** §4 and §4.1.
5. **Recorded as a tracked `DECISION_*.md`, committed and pushed to all four branches:** this file.
