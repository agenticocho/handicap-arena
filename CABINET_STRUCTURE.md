# CABINET STRUCTURE — HOW THE THREE CABINET AGENTS WORK WITHOUT COLLIDING

**Written by Ocho. Ratified by Chilly (Local Chair). This is the operating document for
`sokoban`, `missile-command` and `zork`.**

---

## THE FOUR RULES, AND THEY ARE STRUCTURAL RATHER THAN ADVISORY

### 1. OCHO IS THE SINGLE POINT OF ACCOUNTABILITY

**Cabinet agents report to Ocho, not to the Chair.** One route in, one route out. **A report that arrives by
two routes is two reports**, and this project has spent the week removing second copies of things.

### 2. ONE OWNER PER FILE, AND A WORKTREE PER CABINET SO THEY CANNOT COLLIDE

```
/home/chilly1/workspace/ocho_arena                          main          (Ocho; the shared, frozen files)
/home/chilly1/workspace/ocho_arena_cabinets/sokoban          cabinet/sokoban
/home/chilly1/workspace/ocho_arena_cabinets/missile-command  cabinet/missile-command
/home/chilly1/workspace/ocho_arena_cabinets/zork             cabinet/zork
/home/chilly1/workspace/cabinet_results/<cabinet>/           a SEPARATE ROOT, outside the repo entirely
```

**A WORKTREE IS NOT TIDINESS. EACH HAS ITS OWN INDEX, so `git add -A` in one cabinet CANNOT STAGE ANOTHER
CABINET'S WORK.** That defect cost us a real commit: a teammate deliberately withheld a file because others
were mid-flight, and someone else's `-A` committed it anyway. **The worktree makes that impossible rather
than discouraged.** *A rule stated and not mechanised is a resolution.*

**AND `cabinet_results/` IS A SEPARATE ROOT BECAUSE THE SWEEPS RECURSE** —
`reconcile_and_backfill.py:38` (`**` glob when `recursive`) and `test_bind_control.py:39`
(`os.walk(run_card.RESULTS)`) both walk trees, and **a results directory reachable by a sweep is a results
directory that a sweep will eventually rewrite.** Verified by reading the files, not by being told.

### AND THE LOGS ARE **SCRATCH** — ONE CLASSIFICATION, DECIDED 2026-10-14

**`logs/` is scratch, and the directory does not move.** A record must sit outside every git tree
because a sweep that can reach it will rewrite it; **scratch's obligation is the inverse — it must be
unable to ENTER the record**, which is the ignore rule's job (`.gitignore` now ignores `logs/` whole,
not `*.log`), and a second declared root for scratch would refuse a run over a diagnostic file.
A log is not a record format (FINDING 020); the one time one carried a published number the record was
the re-minted file in `probes/`, not the log.

**AND THE COORDINATE IS DECLARED PER BUNDLE** — `cabinet_root.log_for(bundle)`: a `live:<cabinet>`
bundle resolves to that cabinet's worktree journal, a `legacy` bundle to `LEGACY_LOGS` declared in
place. Measured before it landed, the same declared domain resolved **90 log lines from main and 0
from each cabinet worktree.** Nine captures under `logs/` are declared in place (a FINDING cites one by
path); `LOG_EDGES.json` lists every remaining log edge with a status and is itself checked.

**Read the decision:** `DECISION_logs_are_scratch.md` — one classification, the read half, the
before/after numbers, and the edge list.
**NOTE, so it is not discovered as a mystery:** this copy of the operating document is BEHIND main by
the 2026-10-14 addendum and the `## LANDED` section — pre-existing, not this card's, and named here
rather than left silent.

### 3. OCHO IS THE MERGE GATE. SHARED FILES STAY FROZEN.

**Frozen, and changed only by Ocho, in `main`, with a reason:**

```
the record format      what a bundle contains
the runner             arena.py / run_card.py
the gate               gate_ratios(), and the pair condition
the evaluator          the scorers
the card registry      KNOWN_CARDS -- ONE definition, in arena.py
```

**A cabinet that needs a frozen file changed STOPS AND ASKS.** That is not a formality: three writers in one
repo is the one-definition defect at repo level, **and it looks like a merge conflict for ten minutes and
like a measurement bug for a week.**

### 4. A CABINET AGENT NEVER SCORES ITS OWN EVENT

**The cabinet agent writes THE SIMULATOR.** The scoring rules, the frozen criteria and the verdict stay with
Ocho and the Chair. **A simulator author who scores the event is measuring the thing they built with a rule
they chose** — and the rule is the part that has to be written before the number exists.

## WHAT A CABINET DELIVERS, AND WHEN

**In this order, every time:**

```
1  SIMULATOR + FROZEN CRITERIA     before the first entrant moves. Reviewed, not debugged.
2  CONTROLS                        the simulator proves it can FAIL, in both directions
3  THE RUN                         under scripts/run_guarded.sh -- never a bare python3
4  THE RECORD                      counters, never merged; reason counts separate from totals
```

**AND THE STANDING RULES THAT APPLY TO EVERY CABINET:**

- **the answer is SHORT** — one letter, one digit, one word. A long answer can be deliberated into the cap.
- **an unreadable answer is COUNTED, never scored as a wrong move.** A6: it is INSIDE the denominator.
- **`never_started` is counted SEPARATELY** and a zero-measured run is an ERROR with a non-zero exit.
- **the population is DERIVED from `ARENA_MODELS`** — not typed, not from a second directory.
- **COUNTS ARE THE RESULT. RATES ARE THE INDEX.** A rate over `attempted` can be improved by quitting.
- **a record carries the digests of the inputs it was produced under** — prompt, levels, simulator, host.
- **one run, one path.** The artifact path carries a RUN ID and the run refuses a path that exists.
- **every artifact the Chair sends is a CLAIM** until the file it names has been read, the count it quotes
  has been run, and the enforcer it cites has been found.
