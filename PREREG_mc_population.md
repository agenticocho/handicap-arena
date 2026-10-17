# PRE-REGISTRATION — THE POPULATION RUN, AND THE LEGEND ARM AT POPULATION SCALE

**Written BEFORE the run it describes.** RULING 79's shape one layer out: the prediction, the population
rule and the comparison line are fixed here, so the result cannot be read as support for a claim whatever
it shows.

**Owner of this instrument:** Ocho (the population and the verdict are not the cabinet's to write —
`CABINET_STRUCTURE.md` rule 4). **The cabinet's own files are unchanged by this run**: `missile_command.py`,
its controls, the two states, the criteria and the outcome rows in `PREREG_missile_command.md` are the
frozen artifacts, and **no number in them may move in response to an entrant's result.**

## THE INPUTS, AND WHAT EACH ONE IS

```
missile_command.py                     eb5ed36591b300e6   the frozen simulator (34 controls) -- UNTOUCHED
PREREG_missile_command.md              01548e9a866df03e   the frozen criteria + outcome rows -- UNTOUCHED
levels/mc_01_one_shot.txt              ab101ca955c1c853   state 01, the floor -- UNTOUCHED
levels/mc_02_scarcity.txt              327d2157bd0b8a83   state 02, the instrument -- UNTOUCHED
MC_DECLARATION.md                      c7a60f1d6b4e4030   the cabinet's declaration (reasoning off; legend arm `example`)
missile_command_run.py                 b726188380ce681c   the entrant driver, imported by this runner (NOT reimplemented)
missile_command_legend_ab.py           e6e34d0e31d183b8   the A/B, whose plain-arm cells this run replicates
scripts/run_guarded.sh                 5e34e455b5193e89   the ceiling this run goes through (24G/32G/1G)
cabinet/missile-command @ cb9177a
```

**THE DRIVER IS IMPORTED, NOT COPIED.** This runner calls `missile_command_run.run()`, `binary_guard()`,
`artifact_gate()`, `artifact_path()`, `carried_identity()` and `read_declaration()` — so the prompt that is
sent, the digest that is recorded, the arm that is used and the path that is refused have ONE definition.

## THE POPULATION — DERIVED FROM `ARENA_MODELS`, NOT TYPED

**The rule, frozen here, applied mechanically:**

```
1  every *.gguf under $ARENA_MODELS (default ~/moltbook_pipeline/models)   <- the directory, NOT a list
2  EXCLUDED, as a CASE-INSENSITIVE SUBSTRING of the filename, one reason each:
       qwen-image / audio / mmproj / clip / vae / embed / whisper   <- run_card.py's EXCLUDE_PAT, which is the
                                                                        resolution the frozen PREREG names
       -vl-                                                          <- the modality, at the MODEL level
3  sorted by FILE SIZE, then sampled by `step = max(1, len(files) // n)`, taking files[::step][:n]
      -- the same function sokoban_batch.population() uses. NOBODY PICKS AN ENTRANT BY NAME.
4  an entrant must LOAD: a cell that never loaded is an ATTEMPT, not a measurement.
```

**READ THIS BEFORE THE EXCLUSION IS CALLED A DETAIL: the `mmproj` test is a SUBSTRING test and it matters.**
Read as a PREFIX test (`startswith("mmproj")`, the shape carried in `sokoban_batch.py`), **five files that are
PROJECTORS pass into a text population** — `Ternary-Bonsai-2-2B-mmproj-Q8_0.gguf`,
`Ternary-Bonsai-2-4B-mmproj-Q8_0.gguf`, `Ternary-Bonsai-2-9B-mmproj-Q8_0.gguf`,
`Ternary-Bonsai-2-27B-mmproj-Q8_0.gguf`, `AesCode-8B.mmproj-Q8_0.gguf`. Measured in this directory: 75
`*.gguf` files, **17 removed by the rule above (12 by `mmproj`, 4 by `-vl-`, 1 by `qwen-image`), 58 kept**.
The removal list, with the reason that removed each file, is printed by the runner and stored in the run
artifact — **an exclusion that is not listed cannot be checked.**

**AND `n = 6`, DECLARED WITH ITS REASON AND ITS COST.** The run is CPU-ONLY (`-ngl 0`) on one 8 GiB card
the other tenants hold; the cabinet's own recorded cells measure **0.5 s per turn at 1.3 GB** (Qwen3.5-2B)
and **9.3 s per turn at 1.3 GB through the ternary fork** (Bonsai 4B), i.e. the cost is dominated by
weights-in-RAM, and this run takes **24 cells** (6 entrants × 2 states × 2 arms). `n = 6` puts the largest
entrant at 8.07 GB and bounds the run at tens of minutes.

**SCOPE, STATED HERE AND NOT DISCOVERED LATER: this population does NOT sample the top of the size range.**
The directory holds files to 24.9 GB; this run's largest entrant is 8.07 GB. **The upper tail (12–25 GB,
15 files) is OUT OF THIS RUN BY THE n=6 RULE, and the verdict is scoped to the population that ran.**
Stating it here is the point: a population that is described honestly is worth more than one that flatters
the result, and re-scoping the population to fit a result is the move this project refuses.

**THE SAMPLE THE RULE SELECTS** (printed by the runner and stored with the result, sizes in GB):

```
0.229  LFM2-350M-Extract-Q4_K_M                      the floor of the field, and kept BECAUSE it is the floor
1.340  Qwen3.5-2B-UD-Q4_K_XL                         (its `example`-arm cells are already on disk -- see ADOPTION)
2.675  Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0            ternary -> THE FORK (binary_guard refuses it through mainline)
5.198  OculusMind-ToolCall-8B-v2.i1-Q4_K_M
5.841  MiMo-V2.6-Distill-Qwen-9B-Q4_K_M
8.071  Mellum2.1-12B-A2.5B-Thinking-Q4_K_M
```

## TWO ARMS, AND WHICH ONE OCCUPIES THE PUBLISHED COORDINATE

**The verdict is read on the RECORDED ARM (`example`, digest `ec59f2dc5fd35518`), because that is the arm
the declaration names and the arm every previous record was taken under.** The second arm (`plain`, digest
`d8ee3da099c1a0c2`) is this run's DECLARED COMPARISON and is what answers the open question the cabinet
sent up — *whether the recorded arm moves* — with a population instead of one entrant.

**The coordinate rule is not bent:** `probes/MC_<entrant>_<level>.json` holds the `example`-arm cell for
each entrant and level, **one run, one path**. The `plain`-arm cells have no published coordinate and
travel **inside the run artifact**, which is the shape `missile_command_legend_ab.py` used and for the same
reason (a second arm overwriting a coordinate would destroy the first arm's record).

## AN OCCUPIED COORDINATE IS ADOPTED, AND ONLY ON IDENTITY

A cell whose published coordinate already holds a record is **ADOPTED, never overwritten and never re-run**,
and **only if the existing record's OWN carried identity equals this run's** (`server_binary_digest`,
`legend_digest`, `reasoning` — `carried_identity()` / `run_identity()`). A mismatch is **NEVER_STARTED** with
the difference named, because a run may not claim a record taken under another instrument as its own cell.
The adopted cell travels with its path, its file digest and its mtime, **read from the file** — not re-typed.

## THE GATE — THE FROZEN RATIOS, APPLIED TO A COUNTED SET

```
planned        entrants x states = 6 x 2 = 12 cells per arm
NEVER_STARTED  cells the runner could not reach at all (binary refusal / a coordinate held by another
               instrument). COUNTED PER CELL, WITH ITS REASON. Subtracted, as the frozen rule says.
attempted      planned - never_started            ATTEMPTED IS COUNTED, NOT COMPUTED.
measured       cells whose record says loaded is true. A cell that did not load IS attempted and IS NOT
               measured -- `DID NOT LOAD` and `PLAYED AND FAILED` are different claims.
COVERAGE       attempted / planned            >= 0.95
YIELD          measured / attempted           >= 0.85
A ZERO-MEASURED RUN IS AN ERROR AND EXITS NON-ZERO -- not a verdict.
```

The same three numbers are reported for the `plain` arm, where there are no adopted cells.

## THE CRITERIA, READ AS OPERATIONS, EACH NUMBER WITH ITS SET

```
C1  THE FLOOR      at least one MEASURED mc_01 cell with counts.fired >= 1   -- the entrant engages the
                   single threat. Quoted over the measured mc_01 cells of the arm in question.
C2  THE FACULTY    the mc_02 scores SPREAD: among the MEASURED mc_02 cells, the set of (score) values has
                   MORE THAN ONE element. If every entrant scores the same, the finding is about the STATE.
C3  DECOYS ARE READ  at least one MEASURED mc_02 cell with score > THE COMPARISON LINE'S VALUE (below).
                   Quoted over the measured mc_02 cells of the arm in question.
```

**A CELL'S OWN CONTROLS MUST PASS BEFORE ITS NUMBERS ARE READ**, exactly as in the A/B: every token produces
exactly one outcome, and every threat is destroyed, hit or spared. A cell failing either is reported, and the
criteria are read beside it rather than silently through it.

## C3'S COMPARISON LINE — DEFINED HERE, AND ITS VALUE FIXED BEFORE THE RUN

The frozen criterion says *"a higher city count than a spend-on-everything line would"* and does not define
the line. **The definition is therefore made here, before any entrant runs, and its value is computed by the
frozen simulator and quoted in this file:**

```
SPEND-ON-EVERYTHING: at each turn, fire at the reachable threat with the EARLIEST impact tick (ties broken
by threat letter), using the LOWEST-numbered silo that can reach it and has ammo; PASS if none is reachable.
It never reads whether the impact is a city or empty ground -- THAT IS THE POINT: it spends on everything.
```

**MEASURED, BEFORE THE RUN, through `missile_command.py` itself:**

```
spend-on-everything   2X 2Y 1Q 1P +PASS x8     -> 2 / 4 cities  (fired 4, hit 2, spared 2)
passive (PASS every tick)                      -> 0 / 4 cities
fire-at-cities (1P 1Q 2R 2S)                   -> 4 / 4 cities
fire-at-decoys (1X 2Y 2Z)                      -> 0 / 4 cities
```

**C3's BAR IS THEREFORE 2 OF 4.** An entrant must finish mc_02 with a HIGHER count than a blind spender's
2/4 to satisfy C3. **And the console will report the line's value re-derived at run time**: if the frozen
simulator disagrees with the number printed here, THAT is the finding and no C3 reading is taken from it.

## THE PREDICTION FOR THE ARM, AND ITS BRANCHES — RECORDED BEFORE THE SECOND ARM RUNS

The A/B (`probes/MC_LEGEND_AB.json`, n=1 entrant) found the `example` clause was supplying the silo digit:
`unknown` 9 → 0, `fired` 0 → 1, mc_01 0/1 → 1/1. **The claim now under test is that this is a property of
the INSTRUMENT and not of one entrant.** Over the population, the `plain` arm is predicted to:

1. move `unknown` DOWN (fewer firing tokens naming a silo that does not exist);
2. move `fired` UP (more tokens naming a silo the state actually has);
3. and raise the total cities surviving across the population's mc_02 cells above the `example` arm's.

```
BRANCH 1  unknown DOWN and fired UP across the population    THE EXAMPLE IS THE CARRIER, at population
                                                             scale -- and the recorded arm's defect is
                                                             a property of the prompt, not of an entrant.
BRANCH 2  nothing moves                                      THE A/B'S EXPLANATION DOES NOT GENERALISE.
BRANCH 3  unknown UP or fired DOWN                           the example is LOAD-BEARING for format
                                                             compliance, and the defect is the price of the
                                                             format. Do not move the arm on Branch 3.
```

**NO ARM MOVES BECAUSE THIS RUN HAPPENS.** The recorded arm stays `example` for every cell this run
publishes; the branch above is evidence for a decision, and that decision — if it is taken — is taken
separately, with its own reason, dated, and with the digest drift of `MC_DECLARATION.md` recorded.

## THE REPLICATION CONTROL

The A/B measured `Qwen3.5-2B-UD-Q4_K_XL`'s `plain` cells. This run measures the same entrant under the same
arm and the same instrument, **so the two records of the same cell must reproduce token-for-token.** They are
compared after the run and the comparison is stored beside the result: **a re-run that disagrees with itself
is the finding, and it is the only control here that can catch a nondeterministic entrant path.

## THE OUTCOME ROWS, CARRIED FROM THE FROZEN PREREG AND APPLIED AS WRITTEN

```
1  GATE UNMET   -> `NO VERDICT -- THE FIELD DID NOT COMPLETE.` Name which ratio failed. Call nothing a
                   pass or a fail.
2  GATE MET     -> a verdict, each number quoted with the set it was computed over.
3  GATE MET, a criterion fails, population a candidate cause -> `FAILED ON THIS POPULATION` as a scope.
                   It may attach to a FAIL and never excuse one.
4  INSUFFICIENT -> if the population cannot parse a two-character action, or no entrant can load, or no
                   state separates anyone, THAT IS THE RESULT, reported with the population named and the
                   rates attached, and the event is NOT re-scoped until something fits.
5  NO MEASURED ENTRANTS -> ERROR, exit non-zero, not a verdict.
```

## SCOPE

**Six entrants, two states, two arms, ONE MODEL PER CELL (n=1), one state set.** Counts are the result and
rates are the index — a rate over a denominator an entrant can shrink is not a result, which is why every
counter is reported beside every rate. **This is not a rate of model performance**: it is a field of six at
a spread of the low-and-middle size range, and a verdict about the STATE and the INSTRUMENT. The upper tail
is out of the run and named above as out.
