# PRE-REGISTRATION — `arm_effect` IS A PUBLISHED COMPARISON, AND THE TWO ARM NAMES THAT KEY IT

**Card:** `t_d21287e4` (Ocho), the NAMED RESIDUAL of card `t_8edaaf2d`. **This file and
`scripts/probe_ab_arm_keys.py` are committed BEFORE the edit they describe**, so the edit cannot be read as
support for a claim whatever it shows. Same shape as `PREREG_mc_entrant_identity.md` (card `t_8edaaf2d`) and
`PREREG_mc_field_plain.md` (card `t_ec0b0420`), which this inherits its discipline from.

**Nothing here is a criterion, a verdict or a re-score.** No record, no artifact and no frozen file is
touched. `FAILED ON THIS POPULATION` stands exactly as attached to C2 and C3 (`MC_VERDICT_1.md`).

**Where the work happens.** The decision is Ocho's and lives in `main`; the file is
`cabinet/missile-command`'s (`missile_command_population.py`), so the edit lands in this tree under
`CABINET_STRUCTURE.md` rule 2 and is mirrored to `main` as a document, not as code.

**One caption in the card is wrong, and it is named here rather than followed.** The card says the literals
are "in `aggregate()`" (and its title repeats it). **`aggregate()` is `missile_command_population.py:387-403`
and contains no arm name at all**; the block the card quotes by line number (452, 471-473) is in
**`verdict_inputs()`** (`:406-479`). The line numbers are right, the function name is not. Nothing about the
defect changes — but a reader who greps `aggregate()` for the literals will not find them, so the address is
corrected here rather than repeated.

---

## 0. THE INSTRUMENT'S OWN HISTORY, WHICH IS PART OF THE INSTRUMENT

`scripts/probe_ab_arm_keys.py` was run **twice before this file existed**, to find out whether it runs at all.
Both readings are in the tree; neither is evidence about anything except the probe.

```
run 1  06:59  mc-ab-keys-smoke   5/11 checks PASS, rc 3   <-- THE PROBE WAS WRONG, NOT THE CODE
       C1-C4 FAILED with `TypeError: 'module' object is not subscriptable`: readings 1 and 2 called the
       LIVE module with `ns["verdict_inputs"]` (the exec'd-namespace form) instead of `getattr`. Readings
       3, 4a, 4b and 5 were unaffected -- 4a and 4b still measured the defect, and C5, C8-C11 still PASSed.
run 2  07:02  mc-ab-keys-smoke2  9/11 checks PASS, rc 3   <-- the corrected instrument; C6 and C7 are the
       two checks this card's fix is supposed to turn, so FAILING them BEFORE the edit is the point
```

**The correction was a defect in the probe and nothing else:** `block_fn()` now reads the function out of
whichever container holds it, and no reading, control or expectation was changed to suit a result. The run
this pre-registration governs (§5) is the third one, taken **after** this commit; **run 1's output is quoted
in §6 and is presented as evidence about nothing.** A probe whose code was silently corrected between two
runs is a probe whose second number cannot be trusted either — so both are named.

---

## 1. THE DECISION, AND THE EDIT

### 1.1 WHAT IS STILL A SECOND COPY

```
452   p = _arm_cells(cells, "plain")
471   out["arm_effect"] = {"unknown": {"example": unk_e, "plain": unk_p},
472                        "fired":   {"example": fir_e, "plain": fir_p},
473                        "mc02_score_total": {"example": sc_e, "plain": sc_p},
476   out["spend_on_everything_value_rederived"] = per_arm["example"][...]["comparison_line_value"]
478   ... == PREREG_LINE_VALUE)
```

### 1.2 THE DECISION: THESE ARE **(2) A PUBLISHED COMPARISON**, NOT (1) THE ARMS' NAMES

```+-----------------------------------------------------------------------------------------------+
| THEY ARE THE A/B's FIXED COMPARISON. The keys are the two arms' names AS PUBLISHED on 2026-10-17, |
| and the reason is that THE DIRECTION OF THE COMPARISON IS THE MEASUREMENT: the block's branch is a  |
| claim about WHAT THE WORKED EXAMPLE DOES -- `unknown` DOWN and `fired` UP once the example is       |
| removed -- so it is keyed to WHICH ARM CARRIES THE EXAMPLE, and the names are what say which arm    |
| that is. This is not the placement rule, and it is not recoverable from COORD_ARM/COMPARISON_ARM.   |
+-----------------------------------------------------------------------------------------------+
```

**The reason, stated so it can be checked rather than believed.** Card option 1 was to derive the keys from
`COORD_ARM` / `COMPARISON_ARM`, which are both module constants two lines apart. Read what that buys:
`COORD_ARM` is `R.LEGEND_DEFAULT` — the declaration's `legend_arm`, i.e. **which arm is of record** — and
`COMPARISON_ARM` is the other one. The block asks **which arm carries the example**. Those are two different
questions and the same two names, so:

* **today** (`legend_arm plain`): `COORD_ARM = plain`, `COMPARISON_ARM = example`. The published reading is
  `unknown example 27 / plain 7`. A positional derivation would have to say "the comparison arm moved DOWN
  and `fired` UP" — and the comparison arm is `example`, whose `unknown` is the HIGH one. **Positional
  derivation contradicts the published field on the day it is written.**
* **the day the declaration names `example`**: `COORD_ARM = example`, `COMPARISON_ARM = plain`. The same
  sentence ("the comparison arm moved down") now reads as **"the example arm moved down"** — the opposite
  claim, in the same field names, with no line of the block changed and nothing on the page to show it.
  That is the silent wrongness the card is about, arriving through the fix.
* the only positional form that survives both days is "**the arm carrying the example** moved down", which
  needs to know which arm carries the example — a fact about the prompt text, not about the declaration and
  not about `ARMS`. Deriving it would mean reading `R.PROMPT_EXAMPLE`/`R.PROMPT_PLAIN` and calling one of
  them the example arm by a **new** literal, or by matching the prompt against the legend text: a new
  mechanism, wider than this card, and it would still have to name the two arms.

And the second reading is what the record itself says. **The published artifact carries the two arms of the
day in its own `arms` field**: `probes/MC_POPULATION_20261017-184752.json` records
`"arms": {"recorded": "example", "comparison": "plain"}` beside `"legend_digest"`s
(`ec59f2dc5fd35518` / `d8ee3da099c1a0c2`) — and `PREREG_mc_population.md` fixes the prediction against the
`example` arm by name ("the recorded arm stays `example` for every cell this run publishes"). So the block is
a **published comparison at an instant**, and the correct treatment of a published comparison is a caption
with its artifact and digest, plus a refusal when the names it was published under stop being arms.

**What this decision does NOT claim, and it is the card's own sentence, corrected by measurement.** The
card says "**if the declaration ever names `example` again, the keys above are wrong and wrong silently**".
**That does not reproduce, and §2's P3 measures it rather than arguing it:** both arms are ALWAYS run (the
recorded one into the published coordinate, the other inside the artifact), so `_arm_cells(cells, "example")`
finds its cells whichever arm the declaration names, and the block's three numbers and its branch are
**identical** under either declaration. The keys are exposed to **the driver's arm NAMES**, not to the
declaration — and the measured failure is a RENAME: with `plain` renamed, the pre-edit block reports
`unknown {"example": 27, "plain": 0}` and `NO BRANCH` beside it — a name that is no longer an arm, reported
as a number (§2, P4). That is the defect this edit fixes, and it is why the fix is a **refusal**, not a
re-key.

### 1.3 THE EDIT (E3) — ONE FILE, THREE HUNKS, TRANSCRIBED

**Hunk 1** — after `COMPARISON_ARM` (line 64), before `EXCLUDE_PAT`:

```python
# THE PUBLISHED A/B. `arm_effect` (in `verdict_inputs`, below) reports the comparison `PREREG_mc_population.md`
# fixed BEFORE the population ran -- "THE PREDICTION FOR THE ARM, AND ITS BRANCHES": the arm carrying the
# worked example against the arm without it. THAT COMPARISON IS PUBLISHED, in
# `probes/MC_POPULATION_20261017-184752.json` (`verdict_inputs.arm_effect`; sha256
# 9335b2a39b4d1d389b78b4a88a82f576020387bf7ed3ed21b7c2158899d54156), whose OWN `arms` block records the two
# names of the day (`recorded` `example`, `comparison` `plain`). These two constants are therefore NOT a
# second copy of the declaration's decision -- the declaration decides WHICH arm is of record, and this
# block does not read it -- and NOT a second copy of `ARMS` either: they are the two arms the comparison was
# published between. A key is right here only while the driver still defines it as an arm, so the refusal
# below is what keeps the keys from outliving the names they name.
AB_EXAMPLE_ARM, AB_PLAIN_ARM = "example", "plain"
_ab_missing = [a for a in (AB_EXAMPLE_ARM, AB_PLAIN_ARM) if a not in ARMS]
if _ab_missing:
    raise SystemExit(
        f"REFUSED: `arm_effect` reports the A/B comparison PUBLISHED in "
        f"probes/MC_POPULATION_20261017-184752.json (9335b2a39b4d1d38) between the arms {AB_EXAMPLE_ARM!r} "
        f"and {AB_PLAIN_ARM!r}; the driver defines {ARMS}. Those keys are the names of arms that no longer "
        f"exist, and the block would report zeros under a name it does not contain. RE-PUBLISH the "
        f"comparison as a NEW artifact with a NEW digest; do not re-key this block to the declaration.")
```

**Hunk 2** — the block itself, keys and lookups through the two constants, with the caption that says all of
§1.2 in the source:

```python
    # THE PUBLISHED A/B COMPARISON, KEYED BY THE NAMES IT WAS PUBLISHED UNDER -- not a reading of the
    # declaration, and not derived from COORD_ARM/COMPARISON_ARM. The direction below is a claim about WHAT
    # THE EXAMPLE DOES (`unknown` DOWN and `fired` UP once the example is removed), so it is keyed to which
    # arm carries the example. Deriving it positionally would invert the claim the day the declaration names
    # `example`: COMPARISON_ARM would then be `plain`, and "the comparison arm moved down" would read as
    # "the example arm moved down" -- the opposite of what this block publishes. See `AB_EXAMPLE_ARM`
    # above, where a rename of either arm is refused rather than reported as zeros.
    e = _arm_cells(cells, AB_EXAMPLE_ARM)
    p = _arm_cells(cells, AB_PLAIN_ARM)
    ...
    out["arm_effect"] = {"unknown": {AB_EXAMPLE_ARM: unk_e, AB_PLAIN_ARM: unk_p},
                         "fired": {AB_EXAMPLE_ARM: fir_e, AB_PLAIN_ARM: fir_p},
                         "mc02_score_total": {AB_EXAMPLE_ARM: sc_e, AB_PLAIN_ARM: sc_p},
                         "branch": branch}
```

**Hunk 3** — the two lines below it that index the arm by name (`per_arm["example"]`), which are the same
literal in the same block and which the refusal above also covers: both become `per_arm[AB_EXAMPLE_ARM]`.
The value they read is the C3 comparison line, which is computed from the STATE (line 420-421) and is the
same under every arm — so no value can move, and P6 predicts that.

**What is NOT touched:** `_arm_cells`, `_measured`, the branch cascade, the branch sentences, the three
counter definitions, every key of `arm_effect`, and every other field of `verdict_inputs` — the artifact's
shape is the artifact's. `IDENTITY_IN_RECORD`, the gate, the criteria, `n`, the states and the ceiling are
untouched. **The unique field names the artifact publishes are unchanged, and the probe checks that by
recomputing the published field, not by reading this note.**

---

## 2. PREDICTIONS — MADE BEFORE THE EDIT, FALSIFIABLE, NONE OF THEM A CEILING

**P1 (the published field does not move, and the block still computes it).** `verdict_inputs()` over
`probes/MC_POPULATION_20261017-184752.json`'s own 24 cells reproduces that artifact's
`verdict_inputs.arm_effect` exactly — `unknown {example 27, plain 7}`, `fired {example 2, plain 8}`,
`mc02_score_total {example 0, plain 1}`, the BRANCH 1 sentence, **and the key order (`example` then `plain`
inside each sub-dict)** — **in both runs, before and after the edit, and identical to each other.** Falsified
if any value, key, order or the sentence differs in either run, or if the two runs differ from each other.

**P2 (the name is what the block reads).** Relabeling every cell `example`<->`plain` mirrors all three
sub-dicts (`unknown {example 7, plain 27}`, `fired {example 8, plain 2}`, `mc02 {example 1, plain 0}`) and
moves the branch to **BRANCH 3** — in both runs. Falsified if the numbers do not mirror or the branch does
not move.

**P3 (the card's stated failure mode does not reproduce — a prediction about the DEFECT, not a defence of the
edit).** With the driver's `LEGEND_DEFAULT` substituted to `example` in memory (arms unchanged; nothing on
disk touched), the runner's `COORD_ARM` is `example` and `COMPARISON_ARM` is `plain`, and the block is
**UNCHANGED from the published reading**, in both runs (C5). Falsified if it moves. **If this had turned out
the other way, option 1 would have been the right fix — which is why it is predicted before the edit rather
than asserted after it.**

**P4 (the real exposure, measured PRE-EDIT — the positive control).** With the driver's `LEGEND_ARMS`
patched to `('example','terse')` / `LEGEND_DEFAULT 'terse'` and the cells relabeled `plain`->`terse`, the
pre-edit block **does not refuse**: it reports `unknown {"example": 27, "plain": 0}`,
`fired {"example": 2, "plain": 0}`, `mc02_score_total {"example": 0, "plain": 0}` and the branch sentence
`NO BRANCH -- one arm has no measured cell...`. With the cells relabeled `example`->`worked`, it raises
`KeyError('example')`. **So the pre-edit probe FAILS exactly two checks (C6, C7) and returns rc 3.** Each was
already measured twice before this file (§0, runs 1 and 2 — the same values). Falsified if the pre-edit run
refuses, if any number differs, or if any check other than C6/C7 fails.

**P5 (the fix is a refusal, not a re-key).** Post-edit, both renamed-arm setups **REFUSE at import** with a
`SystemExit` whose message names `MC_POPULATION_20261017-184752.json` and `9335b2a39b4d1d38` and says
re-publish — C6 and C7 PASS, the probe is **11/11, rc 0**. Falsified if either setup imports, raises anything
other than `SystemExit`, or refuses without naming the artifact.

**P6 (the two `per_arm["example"]` lines keep their value).** `spend_on_everything_value_rederived` is `2`
and `comparison_line_matches_the_preregistration` is `true` **before and after** — the value is computed
from the state, and the two renames are of the index, not of the value. Falsified if either moves.

**P7 (drift, and nothing else moves).** `missile_command_population.py` `e588199faf5bbbaa` -> **a different
value** (a hash cannot be predicted from prose; the value is recorded in the landing note). **No other digest
in §4 moves.** Falsified if the module's digest is unchanged after the edit, or if any input in §4 moved.

**P8 (no record is touched).** `git status --porcelain probes/ results/` is **empty** after every command in
§5. The probe writes nothing into the tree, the dry-run writes nothing, and neither loads a model nor takes a
lease. Falsified if any coordinate or result changes.

**P9 (the driver is not reached by this).** `missile_command_run.py`'s self-test is **53/53 before and
after**, and its digest `3bd43eed4c6e41f3` does not move (the refusal is in the runner, which imports the
driver; the driver imports nothing from the runner). Falsified if the count moves or the driver's digest
moves.

**P10 (the reachable state is unaffected).** `missile_command_population.py --dry-run` still prints
`coordinate arm plain` with exit 0 in both runs, and the value it prints still equals
`MC_DECLARATION.md`'s own `legend_arm` — the new refusal must not fire on the declaration on disk, and it
must not have turned the arm of record back into a constant. Falsified if the dry-run refuses, changes its
line, or prints an arm that is not the declaration's.

---

## 3. CONTROLS — EACH WITH THE COMMAND THAT READS IT

```
C1   THE PUBLISHED FIELD IS RECOMPUTED FROM THE PUBLISHED RECORD, NOT FROM A FIXTURE WRITTEN HERE. The
     probe reads probes/MC_POPULATION_20261017-184752.json's own 24 cells and calls the runner's own
     verdict_inputs() over them; a fixture would only show what this note already believes.
C2   AND ITS KEY ORDER IS CHECKED, not just its values: a re-key that kept the numbers and swapped the
     order would still be a change of the published field, and C1 alone would not see it.
C3   THE PROBE CAN FAIL, AND DOES (P4, pre-edit rc 3) -- a check that cannot fail is not a check. C6/C7 are
     its falsifiable core: they FAIL before the fix and PASS after it.
C4   THE RENAMED-ARM FIXTURE TOUCHES NOTHING ON DISK. It patches the driver module's attributes in memory,
     execs the runner's SOURCE read from the tree, and restores the attributes in `finally`; C8 (git) is the
     check that says so, and it is read in the same run.
C5   `LEGEND_DEFAULT` IS SUBSTITUTED, NOT THE DECLARATION. The substitution is one attribute on the driver
     module for the duration of one exec; MC_DECLARATION.md is not edited and its digest is checked
     unchanged in §4 (C10). A test that edited the declaration would be a test of a different tree.
C6   THE TWO ARMS ARE PRINTED SIDE BY SIDE WITH THE DECLARATION'S KEY. The probe prints
     `driver ('example','plain')`, `LEGEND_DEFAULT`, `COORD_ARM` and `COMPARISON_ARM` in its header, so a
     reader can see WHICH state readings 1-3 were taken in, and C11 asserts it is the reachable one.
C7   THE PUBLISHED ARTIFACT'S DIGEST IS RE-COMPUTED (C9) against the value the card quotes: sha256 of the
     364,818-byte file, not a 16-hex prefix copied from the card.
C8   `git status --porcelain probes/ results/` IS READ IN THE SAME RUN as every reading above, so "no record
     moved" is a reading with a time, not a promise.
```

---

## 4. FROZEN INPUTS — RE-READ, NOT QUOTED FROM THIS NOTE

```
missile_command_population.py  e588199faf5bbbaa  ->  A DIFFERENT VALUE  (P7; the edit; the runner drift)
EVERYTHING ELSE UNCHANGED (the probe re-reads each one and fails C10 if any moved):
  missile_command.py eb5ed36591b300e6 · missile_command_run.py 3bd43eed4c6e41f3 · PREREG_missile_command.md
  01548e9a866df03e · mc_01 ab101ca955c1c853 · mc_02 327d2157bd0b8a83 · MC_DECLARATION.md 2ada03ee2ad1f60b
  scripts/run_guarded.sh 5e34e455b5193e89 · PREREG_mc_population.md cfedf8b7f5e7d57f ·
  probes/MC_LEGEND_AB.json 029244b6e5232a6b · PREREG_mc_entrant_identity.md 34c5c2f4c6492eef
  probes/MC_POPULATION_20261017-184752.json 9335b2a39b4d1d38  (sha256, re-computed by C9)
IDENTITY_IN_RECORD ("server_binary_digest", "legend_digest", "reasoning") -- untouched, the Chair's
```

---

## 5. THE ORDER OF OPERATIONS, FIXED HERE

```
1  commit this file + scripts/probe_ab_arm_keys.py                                (pre-registration + instrument)
2  run the probe      -> P4 must hold: 9/11, C6+C7 FAIL, rc 3                      [unit mc-ab-keys-probe-pre]
3  run the driver's --self-test -> P9 must hold (53/53)                            [unit mc-ab-self-test-pre]
4  run the runner's --dry-run   -> P10 must hold (coordinate arm plain)            [unit mc-ab-dryrun-pre]
5  make E3 (hunks 1-3, one file)
6  run the probe again -> P5 must hold: 11/11, rc 0; P1/P2/P3/P6 unchanged         [unit mc-ab-keys-probe-post]
7  run the driver's --self-test -> P9 (53/53) and the runner's --dry-run -> P10    [units mc-ab-self-test-post,
                                                                                    mc-ab-dryrun-post]
8  read §4 back: the digests, and git status --porcelain probes/ results/          (C8, P7, P8)
9  append the landing note to THIS file (drift, counts, every prediction by name, anything corrected)
10 commit the edit with the landing note; mirror this document to main; push both; read both back
```

**Step 2 is not optional and it is not ceremony.** Without it, "11/11 after the edit" is a number with no
counterfactual: with it, the same probe on the same cells returns 9/11 and 11/11 depending on whether two
names in one file are refused rather than reported — which is this card's whole claim, measured.

**Every command in §5 runs under `scripts/run_guarded.sh` (`5e34e455b5193e89`), never a bare `python3`.**
The guard is `systemd-run --user` with the arena's own ceilings, and its logs are `logs/<unit>.out`; the
probe takes no lease and loads no model, so no lease can be held by any command here.

---

## 6. WHAT WOULD FALSIFY THE CARD, AND WHAT WOULD NOT COUNT AS SUCCESS

**Falsified if** the pre-edit probe refuses a renamed arm (P4 — then the defect was already fixed and this
card is a caption), or the post-edit probe imports under a renamed arm (P5), or the published field moves in
either run or differs between runs (P1), or the declaration-flip reading moves (P3), or the two derived
lines change value (P6), or any frozen input in §4 moves (P7), or the driver's self-test count moves (P9),
or the runner's dry-run refuses or stops reading the declaration (P10).

**NOT success:** a caption with no refusal — a comment cannot fail, and the measured defect is a name that is
no longer an arm being reported as a number. **NOT success either:** deriving the keys from
`COORD_ARM`/`COMPARISON_ARM`. That is option 1, and §1.2 is why it is wrong: it would re-key a published
comparison to a *live* role, and it contradicts the published field today. **And NOT success:** editing the
declaration, or the two arm prompts, to make this block true. The declaration is the Chair's; the arms are
the driver's.

**The first, wrong run of the probe** (run 1, before this file existed, before its own defect was corrected)
printed, for the record and for nothing else:

```
READING 1  REPLICATION -- verdict_inputs() over the PUBLISHED artifact's own cells
  computed   TypeError: 'module' object is not subscriptable
  CHECK  FAIL  C1  the block reproduces the published field, value for value
  CHECK  FAIL  C2  the key ORDER is the published order
READING 2  THE NAME IS WHAT IT READS -- every cell relabeled example<->plain
  CHECK  FAIL  C3  ...   CHECK  FAIL  C4  ...
  VERDICT FAIL  (rc 3)      5/11 checks PASS
```

**The reading that mattered in it was READING 3's, which PASSED** (the block unchanged under the
declaration's other arm) — the readings about the runner's code were sound; the five that failed were the
probe's own. That is why the correction is in the probe and the expectations are not.
