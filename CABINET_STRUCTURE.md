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
- **THE REASONING SETTING IS A CONFIG FIELD AND EVERY BUNDLE RECORDS IT** — on the same footing as `ctx`,
  `temperature` and `ngl`, because *a series taken at one setting is not comparable to a series taken at
  another.* Set it DELIBERATELY (default `off`: every cabinet here asks for a short answer, which is the
  format a non-thinking model is built for and a thinking model will fight) and record the ARGV, not a
  summary of it. **MEASURED ELSEWHERE ON THE SAME WEIGHTS: thinking ON gave 2314 tokens and no commitment;
  thinking OFF held the format. Same model, two settings, opposite outcomes.** So "the model cannot do it"
  and "the model was deliberating with no stop condition" are DIFFERENT FINDINGS.
- **THE PROBE COMES BEFORE THE FIELD.** Ask the model ONE brief question and record OBSERVED beside
  REQUESTED. A model that answers a one-token question in one token has thinking off; one that takes two
  hundred has it on. **When the two disagree, the disagreement IS the finding** — a config field nobody
  measured is the same class as a legend nobody read. And a flag can be a NO-OP for a given model, so the
  probe is what makes the claim real.
- **THE CEILING IS RECORDED SEPARATELY FROM THE COUNT USED**, and from the COMMAND cap. Three different
  numbers that were previously one word.
- **A `not_an_action` COUNT IS NOT A CAPABILITY RESULT UNTIL THE BUDGET SIGNATURE IS READ.** "Hit the cap
  deliberating" and "could not produce an answer" are different findings, and one has already been published
  as the other in this project.
- **AN EMPTY ANSWER THE HARNESS PRODUCED IS A MISSING VALUE** — capped deliberation is never a token, never
  an illegal move, never a zero, never dropped.
- **an unreadable answer is COUNTED, never scored as a wrong move.** A6: it is INSIDE the denominator.
- **`never_started` is counted SEPARATELY** and a zero-measured run is an ERROR with a non-zero exit.
- **the population is DERIVED from `ARENA_MODELS`** — not typed, not from a second directory.
- **COUNTS ARE THE RESULT. RATES ARE THE INDEX.** A rate over `attempted` can be improved by quitting.
- **a record carries the digests of the inputs it was produced under** — prompt, levels, simulator, host.
- **one run, one path.** The artifact path carries a RUN ID and the run refuses a path that exists.
- **every artifact the Chair sends is a CLAIM** until the file it names has been read, the count it quotes
  has been run, and the enforcer it cites has been found.

## HOUSE FACT -- pronouns

everyone on this box is male: tiel, ocho, ocho2, birdy, sokoban, missile-command, zork. HE/HIM.
This is a fact about PEOPLE, not about a system -- no artifact records it, so it must be READ here.

## GPU PRIORITY -- OPERATOR RULING, 2026-10-10

**If a cabinet is running, it owns the GPU. The Arcade takes priority over everything else while a game is
being played.**

**And it is not enforceable until two things are true, both of which are ours:**

1. **THE CABINET'S LAUNCHER MUST TAKE A LEASE.** A cabinet that holds the card must be VISIBLE to the
   arbiter. Tonight it was not: `sokoban_run.py` starts llama-server with a bare `subprocess.Popen` and
   records no lease, so the tool that arbitrates cannot name it. **A priority rule cannot be enforced in
   favour of a tenant the arbiter cannot see.**
2. **A SEAT LEASE MUST YIELD TO A CABINET RUN.** The current policy -- *a `mode=run` holder whose pid is
   alive is never reclaimable, at any age* -- means a warm seat can lock out a cabinet indefinitely. That is
   the priority rule inverted, and it held tonight for ~24 hours on a lease nothing was using.

**And the diagnostic that makes either one visible: a blocked load NAMES THE HOLDER** (ruling 82), never
`failed to load`. The operator's rule needs to be checkable from the failure, not inferred from it.

    measured tonight   1853 MiB free · a live mode=run lease holding 5532 MiB with no argument
                       · an unleased holder at 5874 MiB that the arbiter could not see at all
                       · the blocked run: `failed to load`, five retries, six minutes, one message
