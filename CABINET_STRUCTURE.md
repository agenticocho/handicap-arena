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

---

**ADDENDUM (2026-10-14) — THIS RULE IS STATED AND NOT MECHANISED, and line 28 two paragraphs above says
exactly what that means.** Measured at the destination by the Chair-link tick and re-verified by the
Chair:

```
run_card.py:36  in ALL THREE worktrees      RESULTS = os.path.join(ARENA, "results")
   -> ARENA derives from the script's OWN LOCATION, so in a worktree the root IS that worktree's results/

<worktree>/results      exists · 520 TRACKED files · .gitignore: NO      (x3 = 1,560 files in git trees)
/home/chilly1/workspace/cabinet_results/<cabinet>/   0 entries · mtime 2026-10-09 — NOTHING WRITES HERE

the two sweeps, exact:
  reconcile_and_backfill.py:38    pat = os.path.join(RESULTS, "**", "*.json") if recursive else ...
  test_bind_control.py:39         for root, _dirs, files in os.walk(run_card.RESULTS):
```

**So the separate root is declared and unused, and the results it was declared to protect sit inside three
git trees that both sweeps match.** The reason above stands and is unchanged. **The mechanism does not
exist** — *"a rule stated and not mechanised is a resolution"*, written two paragraphs up, **and this is
the rule it describes.**

> **A DECLARED ROOT THAT NO WRITE PATH RESOLVES IS NOT A DECLARATION. IT IS A WISH.**

**What the mechanism must be — and neither half is sufficient alone:**

1. **The writer resolves the DECLARED root, not its own location.** `ARENA` must not be derived from
   `__file__`: the root has to be **the same for all three worktrees and outside all of them** — the git
   **common** dir is the natural carrier (`git rev-parse --git-common-dir`).
2. **And it REFUSES rather than falls back.** If the declared root cannot be resolved, **refuse to run.**
   **The fallback to `<worktree>/results` IS the defect** — a fallback that works silently is how a
   declared root becomes decorative.
3. **And the sweeps take the declared root as their DOMAIN**, rather than globbing a `results/` they find
   by walking. **A sweep that discovers its domain by recursion cannot be protected from recursion.**
4. **And the 1,560 tracked files under the three `<worktree>/results/` are the existing end state:** they
   are **TRACKED, so evidence rather than litter** — **but they are inside the trees the sweeps match**, so
   they must either **move to the declared root or be declared in place.** Untracked-and-unnamed is not
   available; *declared-but-matched* is the state that needs the decision.

**Owners:** this document is Ocho's and the Chair's; **the plumbing is Ocho's to draft and the Chair's to
rule on.** Nothing was edited across the link. The first draft of this addendum was produced by the
Chair-link tick, which measured it and **refused to decide it** — the correct division, for the third
time today.

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

## THE DIG DUG LINES — two cabinets, two names

**Recorded here because a decision that lives only in a transcript is not recorded.** Two
independent DIG DUG builds exist, and until now nothing on disk said which was which:

| name | line | told apart by its OWN artifacts |
|---|---|---|
| `digdug` | `fix/model-entrant-reachable` (`5e780fd`) | 31 `digdug/` files · `CONTRACT_digdug_v1.md` + `CONTRACT_frozen.json` · `card_version: digdug_v1` |
| `digdug2` | `digdug-sampler-grammar` (`5539512`) | 32 `digdug/` files · carries `FROZEN_GBNF_sampler_grammar.gbnf` + `CONTRACT_DIGDUG.md` + `FROZEN.json` |

**THE NAME IS A LABEL, NOT A PATH, AND NOTHING WAS RENAMED ON DISK FOR IT.** The
`"cabinet"` field in `digdug/FROZEN.json`, its generator at `digdug/freeze.py`, and the
`Cabinet:` line in each contract all name the cabinet's **directory** and are left exactly
as they are. The two builds stay distinguishable by their own artifacts — which is how the
mapping was re-derived in the first place, from disk rather than from memory.

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

### CORRECTION to the GPU PRIORITY ruling (2026-10-10, later the same night)

**WHAT I RECORDED:** an unleased tenant at 5,874 MiB, created by our own launcher.
**WHAT IS TRUE, read not recalled:**

    (a) the cabinet launcher passes `-ngl 0` -- it is CPU-ONLY, cannot hold VRAM, and was never that tenant
    (b) the 5,534 MiB holder IS LEASED -- llama-swap-brain -- and the arbiter sees it correctly.
        The association was missed because the tool matched lease pid to tenant pid BY EQUALITY, when the
        lease is held by the WRAPPER (`gpu-lease.sh`) and the memory by its CHILD (`llama-server`).
        Fixed: association is by ANCESTRY, walking the process tree, verified against nvidia-smi.
    (c) the one truly untraced tenant is 134 MiB.

    ITEM 1  launcher lease      PRUDENCE, NOT EVIDENCE. The code does take no lease and that is true;
                                with `-ngl 0` it is harmless; it would matter only at `-ngl > 0`.
                                **Required on that basis -- not on a number that was wrong.**
    ITEM 2  seat lease yields   **STANDS, and it is the item the measurements support.** The live lease
                                held 5,534 MiB under a never-reclaim policy and it DID block the load --
                                the six-minute stall and the failed load were real. Same conclusion,
                                different holder.

**AND THE SHAPE, FOR THE THIRD TIME IN ONE DAY:** the profile config described a runtime it did not
control; the run record omitted the artefact the verdict was about; **and the diagnostic named the wrong
holder.** Each time **the reader was checked against its own expectation and not against the thing it
read.** Ruling 82 is what made this catchable: a blocked load must NAME THE HOLDER -- and it was re-reading
that output against ground truth, not the tool, that found the error.

## POINTING AN AGENT AT THE LOCAL RUNTIME -- FIVE CHECKS, IN ORDER

**DECISION 3 IS WITHDRAWN AND THESE REPLACE IT.** The recipe it gave was wrong, it was wrong SILENTLY, and it
was found from Hermes's own error log rather than from a hypothesis. **A profile configured exactly as instructed
— provider `llamacpp`, `base_url` `127.0.0.1:8080/v1`, model a llama-swap alias — produced:**

```
provider=custom base_url=http://127.0.0.1:36389/v1 model=brain
HTTP 400: model 'brain' not found
```

**TWO THINGS WERE WRONG AND BOTH WERE SILENT.**

```
1  THE MODEL NAME IS A PRESET from ~/.hermes/runtimes/llamacpp/presets.ini -- NOT a llama-swap alias.
 Aliases live on :8080; the provider does not go there. Using an alias gets HTTP 400, every turn.

2  THE `base_url` LINE IS DECORATION. The profile declares :8080 and the provider reaches :36389. THE CONFIG
 SAYS ONE THING AND THE PROVIDER DOES ANOTHER, AND THE CONFIG IS NOT EVIDENCE. The working profile works
 because its MODEL NAME IS A PRESET, and that is the whole of it.

3  CONFIRM THE NAME BY READING THE PROFILE'S OWN PRESET SECTION -- not a list of aliases from somewhere else.

4  AND THE ENDPOINT THE PROVIDER ACTUALLY USES IS KNOWN. The declared base_url is not evidence of it. THE
 ERROR LOG NAMED IT; nothing on disk did.
```

**AND THE FAILURE DOES NOT LOOK LIKE ONE.** Hermes surfaces that 400 as:

```
"Your request was not processed. Send it again if you still want me to carry it out."
```

**THAT READS AS A TRANSIENT HICCUP. IT IS A MISCONFIGURATION THAT RECURS ON EVERY TURN** — an agent will retry
forever while a human reads a suggestion to try again. **The queued-versus-delivered shape, one layer down: a
route that ACCEPTS is not a route that ANSWERS.**

### AND THE FIFTH IS THE ONE TO INSIST ON

```
5  RUN A TRIVIAL ROUND TRIP AND READ THE REPLY.
```

**NOT the config. NOT the provider. NOT a successful dispatch. THE REPLY.** *Every one of the four checks above
can pass while the agent still produces nothing* — a correct preset name on a busy card, a reachable endpoint
that cannot load the model, a dispatch that returns `queued`. **THE VERIFICATION OF A CONFIGURED AGENT ENDS WITH
TEXT THAT CAME BACK.**

**This is the fifth carrier, and the carrier ruling is amended rather than extended by a new one:** menu, legend,
shell, launch config, **and now the profile config — a file that describes a runtime it does not control. The
first four were text a reader could inspect; this one is a description whose behaviour lives somewhere else
entirely. THE DESCRIPTION AND THE BEHAVIOUR ARE TWO DOCUMENTS AND ONLY ONE OF THEM IS ON DISK.**

