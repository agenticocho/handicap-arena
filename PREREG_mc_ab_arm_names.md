# PRE-REGISTRATION — THE A/B'S OWN TWO ARM NAMES: A PUBLISHED COMPARISON, NAMED ONCE

**Card:** `t_a74fee86` (Ocho), the NAMED RESIDUAL of card `t_d21287e4`, found by that card's own literal
sweep. **This file and `scripts/probe_ab_arm_names.py` are committed BEFORE the edit they describe**, so the
edit cannot be read as support for a claim whatever it shows. Same shape as `PREREG_mc_ab_arm_keys.md` (card
`t_d21287e4`) and `PREREG_mc_entrant_identity.md` (card `t_8edaaf2d`), whose discipline this inherits.

**Nothing here is a criterion, a verdict or a re-score.** No record, no artifact and no frozen file is
touched. `FAILED ON THIS POPULATION` stands exactly as attached to C2 and C3 (`MC_VERDICT_1.md`).

**Where the work happens.** The decision is Ocho's and lives in `main`; the file is
`cabinet/missile-command`'s (`missile_command_legend_ab.py`), so the edit lands in this tree under
`CABINET_STRUCTURE.md` rule 2 and the DOCUMENT is mirrored to `main`, not the code (`main` does not carry
this cabinet's python files — the parent card's mirror `1d4f8d6` added only its document).

**The card's address is checked here rather than trusted, and this time it is right.** Re-derived by
inspection: `ARMS = ("example", "plain")` is line **28**, `arm_totals(cells, "example")` /
`arm_totals(cells, "plain")` are line **153**, and `"totals": {"example": ex, "plain": pl}` is line **187** —
three sites, six string constants. **One site the card does NOT list also reads the pair**: line **180**,
`"arms": {a_: R.LEGEND_ARMS[a_] for a_ in ARMS}` — it iterates `ARMS`, so it carries the pair's staleness
without carrying a copy of the names, and it is why the arm SET (line 28) is part of this card and not only
the two key sites. (The parent card's own address was wrong — `aggregate()` instead of `verdict_inputs()` —
and that correction is not repeated here because there is nothing here to correct.)

---

## 0. THE INSTRUMENT'S OWN HISTORY, WHICH IS PART OF THE INSTRUMENT

`scripts/probe_ab_arm_names.py` was run **twice before this file existed**, and reconnaissance was taken with
three scratch scripts that live OUTSIDE the tree (the kanban workspace, not committed). All of it is named,
because a prediction made after a peek is still a prediction about the governed run, but the reader is
entitled to know the peek happened.

```
RECONNAISSANCE (scratch, not committed, before this file existed)
  recon1  arm_totals() over the published artifact's own cells reproduces its published `totals` -- both
          names, value for value. This is what READING 1 later re-takes as a check.
  recon2  (a) arm_totals(relabeled cells, <a name that is no longer an arm>) -> {"cells": 0, ... every
              counter 0 ..., "controls_pass": true}   <-- A ROW THAT FAILS NOTHING BECAUSE IT HOLDS NOTHING
          (b) legend_digest(<a name that is no longer an arm>) -> KeyError, bare, naming nothing
          (c) main() CAN be run model-free with the driver's run() stubbed, and the artifact it writes
              carries arms keys ['example','plain'] and totals keys ['example','plain'] -- the published
              order. Key structure is therefore measurable without a model; no model loaded, no lease taken.
  recon3  the frozen inputs re-read: every digest in §4 below was MEASURED, none typed from the card.
SMOKE RUNS OF THE PROBE ITSELF (in the tree, under logs/, before this file existed)
  smoke 1  mc-ab-names-smoke   12/15, rc 3   <-- ONE CHECK WAS THE PROBE'S OWN DEFECT
        C10 was written with its expectation INVERTED: it passed when the script did NOT refuse, i.e. it
        passed exactly when the defect was present. Found by reading the run's own output (C10 PASS while
        its reading printed "the same artifact is keyed two ways: YES"), corrected in the check and NOT in
        the code: no reading, expectation or control was changed to suit a result. **smoke 1's output is
        presented as evidence about nothing but the probe.**
  smoke 2  mc-ab-names-smoke2  11/15, rc 3   <-- the corrected instrument
        C8, C9, C10 and C11 FAIL. Those four are this card's fix's own checks, so FAILING them BEFORE the
        edit is the point; every other check passes on the same run.
```

**The run this pre-registration governs** (§5) is the third one, taken **after** this commit.

---

## 1. THE DECISION, AND THE EDIT

### 1.1 WHAT IS STILL A SECOND COPY

```
line  28   ARMS = ("example", "plain")
line 153   ex, pl = arm_totals(cells, "example"), arm_totals(cells, "plain")
line 187   "totals": {"example": ex, "plain": pl},
line 180   "arms": {a_: R.LEGEND_ARMS[a_] for a_ in ARMS},     <- reads the pair through ARMS (card omits)
```

### 1.2 THE DECISION: THESE ARE **(2) THE PUBLISHED COMPARISON**, NOT (1) THE DRIVER'S ARM SET

```
+-----------------------------------------------------------------------------------------------------+
| THEY ARE THE ARMS OF THE A/B AS PUBLISHED, in `probes/MC_LEGEND_AB.json` (sha256                     |
| 029244b6e5232a6b77e67cf5e21dea342c7da336a932386b3a16015e96b286c8), whose own `arms`, `legend_arms`,   |
| `cells` and `totals` fields are keyed by exactly these two strings. The pair stays the names it was    |
| published under, with (a) a caption naming the artifact and its digest and (b) an import-time refusal  |
| when a published name stops being an arm -- NOT a derivation from anything live.                      |
+-----------------------------------------------------------------------------------------------------+
```

**Option 1 here is `ARMS = tuple(R.LEGEND_ARMS)` (or the same pair read from the declaration). Read what
that buys, because it is the tempting version and it is wrong three times over:**

* **It would make a pre-registered experiment follow the driver.** `PREREG_mc_legend_ab.md`
  (`49784e02849a401f`, the digest the artifact itself carries as `prereg_digest`) fixes ONE entrant, TWO
  states, **TWO ARMS, ONE CLAUSE APART**. `LEGEND_ARMS` is the set of arms that EXIST. A third arm added
  there would silently turn a two-arm A/B into a three-arm run — published under the old pre-registration,
  with the old prediction — which is exactly the class of silent change this whole family of cards is about.
* **It would re-key and re-order a published record.** The artifact's `totals` are `('example','plain')` in
  that order, and the run order is the same tuple. A dict-derived pair would take its order from the
  driver's `LEGEND_ARMS` literal — an implementation detail of another file — so the published key order
  would be a consequence of where a line happened to be written.
* **Deriving it from the declaration would be worse, and it is the parent card's measured case.** The arm
  of record (`plain` since 2026-10-17) answers WHICH ARM IS OF RECORD; this comparison's meaning is WHICH
  ARM CARRIES THE WORKED EXAMPLE (`unknown` DOWN, `fired` UP once the example is removed). Those are two
  questions with the same two names, and `PREREG_mc_ab_arm_keys.md` §1.2 measured the positional form
  contradicting its own published field on the day it was written.

**So the pair becomes ONE copy of two named constants, and the exposure is closed by a REFUSAL rather than
by a derivation.** The refusal fires when a published arm name stops being an arm — the measured failure is
a RENAME (`§3` C8/C9/C10), not the declaration's role, which the A/B does not read at all.

### 1.3 THE EDIT (E4) — ONE FILE, THREE HUNKS, TRANSCRIBED

**Hunk 1** — line 28 (`ARMS = ("example", "plain")`) becomes the caption, the two constants, the pair derived
from them, and the refusal:

```python
# ==================================================================================================
# THE TWO ARMS, NAMED ONCE -- AND WHY THEY ARE NOT READ FROM THE DRIVER'S ARM SET.
#
# THESE TWO NAMES ARE THE COMPARISON AS PUBLISHED. They are the arms of the A/B in
# `probes/MC_LEGEND_AB.json` (sha256
# 029244b6e5232a6b77e67cf5e21dea342c7da336a932386b3a16015e96b286c8), whose own `arms`, `legend_arms`,
# `cells` and `totals` fields are keyed by exactly these two strings -- the entrant's cells for both arms
# travelled in that ONE run-level file, which is why the pair cannot be re-derived from the driver without
# re-keying a published record (`PREREG_mc_ab_arm_keys.md`, card t_d21287e4, refused the same derivation one
# layer in: the direction of the comparison is WHICH ARM CARRIES THE WORKED EXAMPLE, not which arm is of
# record).
#
# `missile_command_run.LEGEND_ARMS` IS THE SET OF ARMS THAT EXIST; this is the PAIR THAT WAS COMPARED, and
# deriving it from that dict would do two wrong things at once: an added third arm would silently turn a
# two-arm A/B into a three-arm run and publish it under `PREREG_mc_legend_ab.md` (whose digest the artifact
# carries), and the run order and the key order of the published `totals` would follow another file's dict.
#
# A KEY IS RIGHT ONLY WHILE THE DRIVER STILL DEFINES IT AS AN ARM. The refusal below is what stops these
# names outliving the arms they name: without it a rename reports an arm that no longer exists as
# `{"cells": 0, ...}` -- every counter zero and `controls_pass` TRUE, because zero cells satisfy both
# equalities trivially -- and a publication under a name that measured nothing reads exactly like one that
# measured something. Measured rather than argued: `scripts/probe_ab_arm_names.py`, readings 4a/4b/4c.
AB_EXAMPLE_ARM, AB_PLAIN_ARM = "example", "plain"
ARMS = (AB_EXAMPLE_ARM, AB_PLAIN_ARM)          # ONE COPY OF THE PAIR: run order, and the keys below
_ab_missing = [a for a in ARMS if a not in R.LEGEND_ARMS]
if _ab_missing:
    raise SystemExit(
        f"REFUSED: this script is the A/B comparison PUBLISHED in probes/MC_LEGEND_AB.json "
        f"(029244b6e5232a6b) between the arms {AB_EXAMPLE_ARM!r} and {AB_PLAIN_ARM!r}; the driver defines "
        f"{tuple(R.LEGEND_ARMS)}. Those two names are the arms the comparison was published under, and one "
        f"that is no longer an arm would be published as zero cells under a label that measured nothing. "
        f"RE-PUBLISH the A/B as a NEW artifact with a NEW digest; do not re-key this script to the "
        f"declaration or to the driver's arm set.")
```

**Hunk 2** — line 153, the two key sites, through the constants:

```python
    ex, pl = arm_totals(cells, AB_EXAMPLE_ARM), arm_totals(cells, AB_PLAIN_ARM)
```

**Hunk 3** — line 187, the published keys, through the same two constants:

```python
        "totals": {AB_EXAMPLE_ARM: ex, AB_PLAIN_ARM: pl},
```

**What is NOT touched:** `cell_summary`, `cell_controls`, `arm_totals`' body, `COUNTER_KEYS`,
`PER_TOKEN_COUNTERS`, `IMPACT_COUNTERS`, the branch cascade and its four sentences, the artifact's field
list, `ENTRANT`, `STATES`, `PORT`, the gate, the pre-registration, the levels, the driver, the declaration.
**The unique field names the artifact publishes are unchanged, and the probe checks that by producing an
artifact with the script's own `main()` and comparing its keys with the published ones — not by reading this
note.** Line 180 needs no edit: it reads the pair through `ARMS`, which is now the constants.

**ONE THING IN THIS FILE IS STILL WRONG AND IS NOT TOUCHED HERE — NAMED, NOT FIXED.** The artifact's
`reading` string (line 189-192) asserts in the present tense that *"`example` remains the recorded
instrument"*. **It does not.** `MC_DECLARATION.md` (`2ada03ee2ad1f60b`) names `legend_arm plain`, the
declaration moved on 2026-10-17 (`DECISION_mc_legend_arm.md`, card `t_027bf647`), and the driver's
`LEGEND_DEFAULT` is `'plain'` — measured in the probe's own header line. The sentence was true when the A/B
was written and it is a RECORD of that day inside the published artifact, but in the LIVE SCRIPT it is a
caption that lies on the next run, and a re-run would publish it again. **It is not fixed here because
fixing it would change a field a future run PUBLISHES, which under this card's own bounds is the Chair's
and not a runner's**; it is carded as its own residual (see §6).

---

## 2. PREDICTIONS — MADE BEFORE THE EDIT, FALSIFIABLE, NONE OF THEM A CEILING

**P1 (the published totals are reproduced, and the function the keys are handed to has not moved).**
`arm_totals()` over `probes/MC_LEGEND_AB.json`'s own four cells reproduces that artifact's `totals` — both
rows, **every value and every key, and the key ORDER, rows and outer dict** — **in both runs, before and
after the edit, and identical to each other.** Falsified if any value, key or order differs in either run,
or if the two runs differ from each other.

**P2 (the name keys the row).** Relabeling every published cell `example`<->`plain` MIRRORS the two rows (the
row published under one name is what the other name now returns), in both runs; and **the two published rows
differ** (else C3 would be satisfied by a constant). Falsified if the rows do not mirror.

**P3 (the artifact's keys), measured without a model.** With the driver's `run()` stubbed to a not-loaded
record (**no model, no lease; every number in that artifact is zero BY CONSTRUCTION and is not a measurement
of anything**), the script's own `main()` writes an artifact whose `arms` keys and `totals` keys are the
published keys in the published order, in both runs. Falsified if either key list differs or is reordered.

**P4 (THE DEFECT, PRE-EDIT — the positive control, and it has TWO HALVES).** With the driver's arms renamed
in memory and the published cells relabeled to match (what a future run under renamed arms would produce),
the pre-edit script **DOES NOT REFUSE**, and:
  * **4a/4b (the run path dies uninformatively):** `legend_digest(<the renamed-away name>)` raises a bare
    `KeyError('plain')` / `KeyError('example')` — an exception that names neither the artifact, nor that a
    name stopped being an arm, nor any remedy.
  * **4a/4b (the totals path reports a number):** `arm_totals(relabeled cells, <the renamed-away name>)`,
    the callable line 153 builds the published rows from, returns `{"cells": 0, "best_cell_score": null,
    ...every counter 0..., "controls_pass": true}` — **a row that fails nothing because it holds nothing**,
    while the name the cells actually carry gets no row at all.
  * **4c (the SILENT half, at artifact level):** with the pair moved (in memory) to match the renamed driver
    and the two key sites left as written, the pre-edit `main()` **runs to completion** and publishes an
    artifact whose **`arms` keys are `('example','terse')` and whose `totals` keys are `('example','plain')`**
    — the same artifact keyed two ways, both rows zero and `controls_pass` true.
  Pre-edit the probe is **11/15 with exactly C8, C9, C10 and C11 FAIL and rc 3.** Falsified if the pre-edit
  run refuses any of the three setups, if any number above differs, or if any check other than C8–C11 fails.

**P5 (the fix is a REFUSAL, not a re-key).** Post-edit, all three setups **REFUSE at import** with a
`SystemExit` whose message names `MC_LEGEND_AB.json` and `029244b6e5232a6b` and says re-publish — **C8, C9
and C10 PASS, the probe is 15/15, rc 0.** Falsified if any setup imports, raises anything other than
`SystemExit`, or refuses without naming the artifact.

**P6 (one copy of the names).** Pre-edit the exact arm-name string constants in the live source are **6, on
three lines (28, 153, 187)**; post-edit there are **exactly 2, both on the `AB_*_ARM` assignment**, and
**none outside it** (C11 FAIL -> PASS). Falsified if any exact name constant survives outside that line —
and this check's limit is stated in the instrument: comments and prose are invisible to it, so it says
nothing about captions.

**P7 (the reachable state, the published record and the criteria are untouched).** The module imports under
the driver on disk and its `ARMS` are the driver's own two arms (the refusal does not fire on the state on
disk); the published artifact is not rewritten by any command in §5; `git status --porcelain probes/
results/` is **empty** after every command in §5; the published artifact's sha256 re-computed **in full**
equals `029244b6e5232a6b77e67cf5e21dea342c7da336a932386b3a16015e96b286c8`; no criterion, verdict, count,
level, ceiling or `IDENTITY_IN_RECORD` moves. Falsified if any of these fails.

**P8 (the drift, and what it costs).** `missile_command_legend_ab.py` `e6e34d0e31d183b8` -> **a different
value** (a hash cannot be predicted from prose; the value is recorded in the landing note). **No other
digest in §4 moves, and the driver's self-test is 53/53 before and after.** **And the cost is named rather
than discovered later: `PREREG_mc_population.md:21` cites the A/B at `e6e34d0e31d183b8`, so that line
becomes a citation of an EARLIER version of this file.** That is not a moved input — it is a `PREREG` doing
what a pre-registration does: recording what was true when it was written (`MC_DECLARATION.md` is cited
there at `c7a60f1d6b4e4030` and is `2ada03ee2ad1f60b` today; `missile_command_run.py` is cited at
`b726188380ce681c` and is `3bd43eed4c6e41f3` today, the parent card's own edit). Falsified if the module's
digest is unchanged after the edit, or if any input in §4 moved.

---

## 3. CONTROLS — EACH WITH THE COMMAND THAT READS IT

The controls are numbered `CONTROL n` and the **instrument's own checks** keep the `Cn` labels, so a reader
can tell a control in this note from a line of a probe log.

```
CONTROL 1   THE PUBLISHED TOTALS ARE RECOMPUTED FROM THE PUBLISHED RECORD, NOT FROM A FIXTURE WRITTEN HERE.
            The probe reads probes/MC_LEGEND_AB.json's own 4 cells and calls the A/B's own arm_totals() over
            them; a fixture would only show what this note already believes.            [check C1]
CONTROL 2   AND THE KEY ORDER IS CHECKED, rows and outer dict: a re-key that kept the numbers and swapped
            the order would still be a change of the published keys, and C1 alone would not see it. [C2]
CONTROL 3   THE NAMES ARE WHAT THE ROWS ARE KEYED BY: relabeling every published cell must mirror the two
            rows.                                                                          [C3]
CONTROL 4   AND THE CHECK IS NOT VACUOUS: the two published rows must DIFFER, so C3 cannot be satisfied by
            a constant.                                                                    [C4]
CONTROL 5   THE ARTIFACT'S KEY STRUCTURE IS MEASURED BY RUNNING THE SCRIPT'S OWN main(), not by reading its
            source -- with the driver's run() stubbed, so no model is loaded and no lease is taken. Every
            number in that fixture is zero by construction, the run's own branch says NO VERDICT, and the
            KEYS are the reading.                                                          [C5, C6, C7, C7b]
CONTROL 6   THE PROBE CAN FAIL, AND DOES (C8-C11, pre-edit 11/15, rc 3) -- a check that cannot fail is not a
            check. C8/C9/C10/C11 are its falsifiable core: they FAIL before the fix and PASS after it. **And
            one of them already failed for the wrong reason**: C10's expectation was inverted in smoke 1 and
            it passed while the defect was present (§0). That is why every number is read in the same run,
            and why smoke 1 is named as evidence about nothing.                            [C8, C9, C10, C11]
CONTROL 7   THE RENAMED-ARM AND MOVED-PAIR FIXTURES TOUCH NOTHING ON DISK. They patch the driver module's
            attributes in memory, exec the script's SOURCE read from the tree, and restore the attributes in
            `finally`; C12 (git) is the check that says so and is read in the same run.      [C8, C9, C10]
CONTROL 8   AND THE FIXTURES ARE FIXTURES: the pair everything is compared against is the pair the PUBLISHED
            artifact carries, not a list typed into the probe -- so a change to the artifact's keys would
            FAIL C5/C6 rather than be followed silently.                                   [C5, C6, C7]
CONTROL 9   NO RECORD, NO ARTIFACT AND NO FROZEN FILE IS WRITTEN: `git status --porcelain probes/ results/`
            is read IN THE SAME RUN as every reading above, so "nothing moved" is a reading with a time, not
            a promise.                                                                      [C12]
CONTROL 10  THE PUBLISHED ARTIFACT'S DIGEST IS RE-COMPUTED IN FULL against the value the card quotes -- 64
            hex, not a 16-hex prefix copied from the card or from the parent's landing note. [C13]
CONTROL 11  THE FROZEN INPUTS ARE RE-READ, including the two pre-registrations this card descends from and
            the parent card's landing note, so §4 cannot quietly become a list of values nobody checked.
            The reachable state is read in the probe's header (driver arms, LEGEND_DEFAULT, module ARMS,
            both digests) so a reader can see WHICH state C1-C4 were taken in.       [header, C7b, C14]
```

**The checks, as they appear in the instrument:** C1, C2, C3, C4, C5, C6, C7, C7b, C8, C9, C10, C11, C12,
C13, C14 — **fifteen**, of which **C8, C9, C10, C11 are the four this card turns** (11/15 rc 3 before,
15/15 rc 0 after).

---

## 4. FROZEN INPUTS — RE-READ, NOT QUOTED FROM THIS NOTE

```
missile_command_legend_ab.py   e6e34d0e31d183b8  ->  A DIFFERENT VALUE  (P8; the edit; the drift)
EVERYTHING ELSE UNCHANGED (the probe re-reads each one and fails C14 if any moved):
  missile_command.py eb5ed36591b300e6 · missile_command_run.py 3bd43eed4c6e41f3 · PREREG_missile_command.md
  01548e9a866df03e · levels/mc_01_one_shot.txt ab101ca955c1c853 · levels/mc_02_scarcity.txt 327d2157bd0b8a83
  MC_DECLARATION.md 2ada03ee2ad1f60b · scripts/run_guarded.sh 5e34e455b5193e89 · PREREG_mc_population.md
  cfedf8b7f5e7d57f · PREREG_mc_legend_ab.md 49784e02849a401f · PREREG_mc_ab_arm_keys.md 47db6b9368bae18c
  probes/MC_LEGEND_AB.json 029244b6e5232a6b  (sha256, re-computed by C13)
IDENTITY_IN_RECORD ("server_binary_digest", "legend_digest", "reasoning") -- untouched, the Chair's
NOT IN THIS LIST, AND THE REASON IS THE CARD: probes/MC_LEGEND_AB.json is the PUBLISHED artifact this
card's names come from; the probe reads it and re-computes its digest, and no command in §5 writes to it.
```

**And one reading is deliberately NOT compared, with its reason.** The stubbed fixture's artifact carries an
`entrant_digest` of its own (the 1.3 GiB `Qwen3.5-2B-UD-Q4_K_XL.gguf`), and it will not equal the published
one. **That is not this card's subject and it is already settled**: the model files in `ARENA_MODELS` do not
hash reproducibly on this box (card `t_cdd433bb`), so an `entrant_digest` is a reading at an instant rather
than an identity. The probe compares KEYS, and a reader who sees the two digests differ has found the
already-named defect, not a new one.

---

## 5. THE ORDER OF OPERATIONS, FIXED HERE

```
1  commit this file + scripts/probe_ab_arm_names.py                                (pre-registration + instrument)
2  run the probe      -> P4 must hold: 11/15, C8+C9+C10+C11 FAIL, rc 3              [unit mc-ab-names-probe-pre]
3  run the driver's --self-test -> P8 must hold (53/53)                             [unit mc-ab-names-selftest-pre]
4  run the runner's --dry-run   -> the runner is untouched and must still read the declaration
                                                                                    [unit mc-ab-names-dryrun-pre]
5  make E4 (hunks 1-3, one file)
6  run the probe again -> P5 must hold: 15/15, rc 0; P1/P2/P3/P6 unchanged          [unit mc-ab-names-probe-post]
7  run the driver's --self-test -> P8 (53/53) and the runner's --dry-run            [units mc-ab-names-selftest-post,
                                                                                     mc-ab-names-dryrun-post]
8  read §4 back: the digests, and git status --porcelain probes/ results/          (C12, P7, P8)
9  append the landing note to THIS file (drift, counts, every prediction by name, anything corrected)
10 commit the edit with the landing note; mirror this document to main; push both; read both back
```

**Step 2 is not optional and it is not ceremony.** Without it, "15/15 after the edit" is a number with no
counterfactual: with it, the same probe on the same cells returns 11/15 and 15/15 depending on whether two
names in one file are refused rather than typed three times — which is this card's whole claim, measured.

**Every command in §5 runs under `scripts/run_guarded.sh` (`5e34e455b5193e89`), never a bare `python3`.**
The guard is `systemd-run --user` with the arena's own ceilings, and its logs are `logs/<unit>.out`; the
probe takes no lease, loads no model and starts no server, so no lease can be held by any command here.

---

## 6. WHAT WOULD FALSIFY THE CARD, AND WHAT WOULD NOT COUNT AS SUCCESS

**Falsified if** the pre-edit probe refuses a renamed arm or a moved pair (P4 — then the defect was already
fixed and this card is a caption), or the post-edit probe imports under a renamed arm (P5), or any published
totals row or key order moves in either run or differs between runs (P1, P2), or the artifact's key
structure changes (P3), or the same artifact can still be keyed two ways (P4, P6), or any frozen input in §4
moves (P7, P8), or the driver's self-test count moves (P8).

**NOT success:** a caption with no refusal — a comment cannot fail, and the measured defect is a name that
is no longer an arm being reported as a zero row whose controls PASS. **NOT success either:** deriving the
pair from `R.LEGEND_ARMS` or from the declaration (§1.2). **And NOT success:** editing the declaration, the
arm prompts, the pre-registration or the published artifact to make this file true. The declaration is the
Chair's; the arms are the driver's; the artifact is a record.

**ONE BOUND THIS DECISION LEAVES, STATED RATHER THAN LEFT TO BE FOUND.** The refusal fires when a published
arm name **stops being an arm**. It does **not** fire if the driver **ADDS** a third arm — the artifact's
`arms` and `totals` would then carry the two published names while `legend_arms` carries three. That is
correct under §1.2 (the pair is the published comparison, not an inventory of arms) and it is why the
caption in the source says so in as many words. A reader wanting the third arm's effect needs a new A/B and
a new pre-registration, not a re-key of this one.

**AND THE RESIDUALS THIS CARD NAMES AND DOES NOT FIX:**

```
1  THE `reading` STRING IS STALE PROSE IN A LIVE SCRIPT (§1.3). It asserts that `example` "remains the
   recorded instrument"; the declaration has named `plain` since 2026-10-17. In the PUBLISHED artifact that
   sentence is a record of the day it was written; in the live script it would be REPUBLISHED by the next
   run. NOT fixed here: it is text a future run publishes, and this card's bounds put a change to a
   published field with the Chair.
2  `missile_command_run.py:1239-1240` and `scripts/check_mc_field_plain.py:133` pin arm names in ASSERTIONS'
   expected values -- named by card t_d21287e4's landing note §5 as NOT defects, and left alone here:
   an expectation may be a literal, a measurement may not.
3  `PREREG_mc_population.md:21` will cite an earlier version of this file after the edit (P8). A
   pre-registration records what was true when it was written; it is not edited to keep up.
4  THE `reading` STRING'S STALE SENTENCE IS CARDED, not left silent: **`t_16a3b025`** (assignee Ocho, parent
   this card), created by this landing because a residual named only in prose is a residual only until the
   next reader. It carries the harder half this card could not decide: that sentence is a FIELD A FUTURE RUN
   PUBLISHES, so correcting the live copy is the Chair's to ratify, and the published artifact's copy stays
   the record of the day it was true.
```

---

# LANDING NOTE — APPENDED AFTER THE WORK, WITH THE READINGS AND EVERY PREDICTION DISCHARGED BY NAME

**Written after E4 and after every command in §5, 2026-10-19 ~07:20 PDT.** This note is appended; nothing
above it is rewritten. **No record, no artifact, no criterion and no frozen file was touched**, and no model
was loaded and no lease taken — the whole of this card is a caption, a refusal and reads.

## 1. THE READINGS, EACH WITH ITS UNIT AND ITS INSTANT

```
BEFORE THIS FILE EXISTED (the instrument's own history; §0)
  07:08:52  mc-ab-recon           scratch reconnaissance (NOT committed)      the published totals recomputed
  07:11:06  mc-ab-recon2          scratch reconnaissance (NOT committed)      (a) (b) (c) of §0, quoted there
  07:12:45  mc-ab-recon3          scratch digest re-read (NOT committed)      §4's digests, all measured
  07:12:50  mc-ab-selftest-pre    missile_command_run.py --self-test          ALL CONTROLS PASS 53/53
  unrecorded  mc-ab-names-smoke    probe (run 1, C10 INVERTED -- see §4)      12/15, rc 3
  unrecorded  mc-ab-names-smoke2   probe (run 2, corrected)                   11/15, C8/C9/C10/C11 FAIL, rc 3
              (both smoke runs sit between 07:12:50 and 07:17:43; their OWN LOGS ARE GONE -- §4 (a))
AFTER THE PRE-REGISTRATION, BEFORE THE EDIT (the governed counterfactual)
  07:17:44  mc-ab-names-probe-pre     scripts/probe_ab_arm_names.py           11/15, C8/C9/C10/C11 FAIL, rc 3 (P4)
  07:17:48  mc-ab-names-selftest-pre  missile_command_run.py --self-test      ALL CONTROLS PASS 53/53
  07:17:52  mc-ab-names-dryrun-pre    missile_command_population.py --dry-run coordinate arm plain
AFTER THE EDIT
  07:18:43  mc-ab-names-probe-post    scripts/probe_ab_arm_names.py           15/15, rc 0              (P5)
  07:18:46  mc-ab-names-selftest-post missile_command_run.py --self-test      ALL CONTROLS PASS 53/53  (P8)
  07:18:50  mc-ab-names-dryrun-post   missile_command_population.py --dry-run coordinate arm plain
every one of the six governed runs under scripts/run_guarded.sh 5e34e455b5193e89, units named above, logs
under logs/<unit>.out; no lease was taken and no model was loaded by any command above
```

**THE ONE LINE THE WHOLE CARD TURNS ON, before and after, the same probe, the same published cells:**

```
PRE-EDIT   4a  `plain` -> `terse`:
               run path      legend_digest('plain') -> KeyError: 'plain'          (bare: no artifact, no remedy)
               totals row    arm_totals(relabeled cells, 'plain') -> {"cells": 0, ..., "controls_pass": true}
                             arm_totals(relabeled cells, 'terse') -> the REAL plain row (cells 2, unknown 0, fired 1)
                             ^ THE NAME THAT IS NO LONGER AN ARM IS REPORTED AS A ROW THAT PASSES ITS CONTROLS,
                               and the name the cells actually carry gets no row from the script at all
           4b  `example` -> `worked`: the same two halves, mirrored (KeyError: 'example'; the zero row under
                             'example', the real row under 'worked')
           4c  the pair moved:      main() RUNS TO COMPLETION under the stub and would publish
                                      arms keys   ['example', 'terse']
                                      totals keys ['example', 'plain']        <- THE SAME ARTIFACT KEYED TWO WAYS
                                      both rows cells 0, controls_pass true
POST-EDIT  4a/4b/4c  REFUSED AT IMPORT, SystemExit, naming probes/MC_LEGEND_AB.json (029244b6e5232a6b),
                     naming the driver's arm set, and saying RE-PUBLISH as a NEW artifact with a NEW digest.
```

**A NAME THAT IS NO LONGER AN ARM WAS REPORTED AS A ROW THAT FAILS NOTHING BECAUSE IT HOLDS NOTHING — zero
cells satisfy both of the script's own equalities trivially, so `controls_pass` was `true` — and with the
pair moved the artifact came out keyed two ways. It is now a refusal that names the artifact, its digest and
what to do instead.**

## 2. THE DRIFT, AS PREDICTED (P8)

```
missile_command_legend_ab.py   e6e34d0e31d183b8  ->  2c1c12a90e850bdf     E4, the caption, the one copy and
                                                                           the refusal. The line numbers moved
                                                                           with it: the constants are :51-52,
                                                                           the two key sites are :186 and :220
EVERYTHING ELSE IN §4 UNCHANGED, re-read after the last command (probe C14: 11 re-read, 0 moved):
  missile_command.py eb5ed36591b300e6 · missile_command_run.py 3bd43eed4c6e41f3 · PREREG_missile_command.md
  01548e9a866df03e · levels/mc_01_one_shot.txt ab101ca955c1c853 · levels/mc_02_scarcity.txt 327d2157bd0b8a83
  MC_DECLARATION.md 2ada03ee2ad1f60b · scripts/run_guarded.sh 5e34e455b5193e89 · PREREG_mc_population.md
  cfedf8b7f5e7d57f · PREREG_mc_legend_ab.md 49784e02849a401f · PREREG_mc_ab_arm_keys.md 47db6b9368bae18c
  probes/MC_LEGEND_AB.json 029244b6e5232a6b  (FULL sha256 re-computed in both runs:
  029244b6e5232a6b77e67cf5e21dea342c7da336a932386b3a16015e96b286c8)
git status --porcelain probes/ results/  ->  0 lines, read in BOTH the pre-edit and the post-edit run
the driver's --self-test: 53/53 before and after; the runner's --dry-run: `coordinate arm plain` before and after
```
**And the cost P8 named, now a fact: `PREREG_mc_population.md:21` cites the A/B at `e6e34d0e31d183b8`, so
that line now cites an EARLIER version of this file.** It is not edited and it is not a moved input: a
pre-registration records what was true when it was written — that same block cites `MC_DECLARATION.md` at
`c7a60f1d6b4e4030` (now `2ada03ee2ad1f60b`) and `missile_command_run.py` at `b726188380ce681c` (now
`3bd43eed4c6e41f3`, the parent card's own edit).

## 3. EVERY PREDICTION, DISCHARGED BY NAME — NONE CORRECTED, NONE TRIMMED

```
P1   the published totals are reproduced, value for value and key order for key order, in BOTH runs and
     identical to each other .................................................................  HIT  (C1+C2, twice)
P2   relabeling the cells MIRRORS the two rows, and the two published rows differ so the check is not
     vacuous .................................................................................  HIT  (C3+C4, twice)
P3   the script's own main(), run with run() stubbed, publishes an artifact whose `arms` and `totals` keys
     are the published keys in the published order ...........................................  HIT  (C5/C6/C7/C7b, twice)
P4   PRE-EDIT the renamed arms and the moved pair are NOT refused, and the failure has the two measured
     halves: a bare `KeyError` on the run path and a zero row whose `controls_pass` is TRUE on the totals
     path, plus an artifact keyed two ways in 4c; probe 11/15 with exactly C8/C9/C10/C11 FAIL, rc 3 ...  HIT  (probe-pre)
P5   POST-EDIT all three setups REFUSE at import with SystemExit naming MC_LEGEND_AB.json and
     029244b6e5232a6b; probe 15/15, rc 0 ......................................................  HIT  (probe-post)
P6   one copy: 6 exact name constants on 3 lines (28/153/187) become 2, both on the AB_*_ARM assignment,
     none outside it .........................................................................  HIT  (C11, both runs)
P7   no record, artifact, criterion or frozen file moves; the published artifact re-read at full sha256 in
     both runs ................................................................................  HIT  (C12/C13, twice)
P8   the module's digest moves; every other §4 input unmoved; self-test 53/53 both sides; and the cost to
     PREREG_mc_population.md:21's citation named ...............................................  HIT  (§2)
```

**Eleven of the fifteen checks are replication controls and they pass in BOTH runs with identically equal
values; the four that move are the fix's own and they FAIL before and PASS after. The published artifact was
re-read, not trusted: its bytes are read from disk in both runs and its full sha256 re-computed (C13).**

## 4. ADDENDUM (POST-HOC, DECLARED) — TWO READINGS IN §1 WITH NO CARRIER, AND ONE MISTAKE OF MINE

**Declared here rather than left to be discovered, because "a claim with no carrier is unverified" applies to
this note's own first four lines.**

```
(a) THE TWO SMOKE RUNS' LOGS NO LONGER EXIST. `logs/mc-ab-names-smoke.out` and `logs/mc-ab-names-smoke2.out`
    were deleted BY MY OWN `rm -f logs/mc-ab-names-*.out` at 07:17:43, before the governed runs -- a
    housekeeping command that took the instrument's own history with it. Their numbers (12/15 with C10
    passing while its own output said the defect was present; 11/15 with C8/C9/C10/C11 FAIL) are recorded in
    §0 above and in §1 here, and **they can no longer be checked by a reader.** They are therefore presented
    as UNCORROBORATED: the governed runs at 07:17:44 / 07:18:43 are the readings this card stands on, and
    their logs exist. §0's phrase "in the tree, under logs/" is now false of those two files and is corrected
    by this paragraph rather than left standing.
(b) THREE UNITS AT 07:17:15-07:17:33 WROTE NO LOG ANYWHERE. `mc-ab-names-probe-pre`, `-selftest-pre` and
    `-dryrun-pre` were launched with a RELATIVE workdir, so `run_guarded.sh`'s `StandardOutput=append:
    ./logs/<unit>.out` was not resolved to this directory; the units are gone (collected) and no such file
    exists under logs/ or elsewhere on this box. Whether they executed or failed at start CANNOT be
    established from what remains, so their output is presented as evidence about nothing. **The readings
    quoted in §1 are the SECOND launch of the same three units, with an absolute workdir, whose logs are in
    logs/.** Nothing was written into the tree by either launch (`git status --porcelain` was read after both:
    0 lines).
(c) NO PREDICTION WAS ADDED, REMOVED OR REWRITTEN AFTER THE FACT. The one number that changed between the
    smoke run and the governed run is a CHECK'S expectation (C10's, inverted -> corrected, §0), never a
    reading and never the code.
```

## 5. WHAT THIS LANDING DOES NOT DO, AND WHAT IT NAMES

**Nothing was re-run, re-scored or re-scoped.** No A/B run was taken and no model was loaded; no published
artifact, record, coordinate, result, criterion, level, ceiling or `IDENTITY_IN_RECORD` value moved; the A/B's
own `readings` in the published artifact are the published artifact's. **The four cells the replication
control reads are the four cells the published artifact already carried** — `example` `{unknown 9, fired 0}`
and `plain` `{unknown 0, fired 1}` — and they are read from the artifact, not from a fixture written here.
**`entrant_digest` is still a reading at an instant rather than an identity (§4), and nothing in this diff
treats it as one.**

**NAMED, NOT CHANGED — the residuals, and each one is now either carded or explicitly out of everyone's way:**

```
1  THE `reading` STRING'S STALE SENTENCE (line 221-225). It asserts in the present tense that `example`
   "remains the recorded instrument"; the declaration has named `plain` since 2026-10-17. In the published
   artifact it is a record of the day it was written and stays; in the LIVE script it is a caption the next
   run would republish, and correcting it moves text a run publishes -- the Chair's, per this card's bounds.
   **CARDED AS `t_16a3b025`** (assignee Ocho, parent this card), with the harder half of the question written
   into that card: the sentence also carries a TRUE statement (`example` is still selectable) that must not be
   corrected away with the false one.
2  `missile_command_run.py:1239-1240` and `scripts/check_mc_field_plain.py:133` pin arm names in ASSERTIONS'
   expected values. NOT defects, NOT touched: an expectation is supposed to go stale and fail loudly. An
   expectation may be a literal, a measurement may not (card t_d21287e4's landing note §5).
3  `PREREG_mc_population.md:21` now cites an earlier A/B digest. NOT a defect and NOT corrected: a
   pre-registration records what was true when it was written.
4  LINE 180 (`"arms": {a_: R.LEGEND_ARMS[a_] for a_ in ARMS}`) needed no edit: it reads the pair through
   `ARMS`, which is now the constants. It WAS a second route to the pair's staleness (a bare `KeyError` inside
   `main()`, not a published row), and the refusal above closes it by firing before `main()` is reached.
```

**AND THE ONE THING A READER SHOULD CHECK FIRST, IF ONLY ONE THING IS CHECKED: the same probe, the same four
published cells, returns `11/15 rc 3` before the edit and `15/15 rc 0` after it, and the four checks that
move are the four the fix is about. Both runs are in `logs/` with their units named in §1.**

---

## APPENDIX — THE CABINET'S FIELD CHECKER, RUN FOR INFORMATION (NOT A CHECK ON THIS CARD)

**Run after the edit, so that a reader meeting the name of this card in the checker's output — or meeting the
checker at all — can tell what is and is not mine.**

```
07:22:29  mc-field-check-ocho  scripts/check_mc_field_plain.py  108/111, 3 CHECKS FAILED
          logs/mc-field-check-ocho.out      (its EXIT STATUS was not captured -- the unit's log was read,
                                             not its return code; named as a gap in this reading)
          read-only: git status --porcelain probes/ results/ -> 0 lines, read after it
```

**The checker does not read this card's file, and that is checkable rather than argued:**
`grep -c legend_ab scripts/check_mc_field_plain.py` is **0** and `git show --stat 047aded` names exactly two
files (`missile_command_legend_ab.py`, `PREREG_mc_ab_arm_names.md`). Its arm checks PASS in this run —
*"every record names the arm the declaration declares"*, *"by the digest the driver computes for it"*,
*"...and none of them names the arm of record before the move"* — which is the one thing it could have said
about this card, and it says the records are consistent with the declaration.

**The three failures, each traced, and only the third is named here for the first time:**

```
1  "every measured record's entrant digest IS the digest of the model file on disk"  got 8 records where
   the fresh reading disagrees, want []
   -> the cabinet's known finding, with a settled mechanism: THE BOX DOES NOT HASH LARGE FILES
      REPRODUCIBLY (card t_cdd433bb, ~1 bit per 0.3-1.5 GB of data in motion, episodic). Its checker
      amendment is card t_77f73033 (currently blocked). NOT this card's, and NOT stable in size: the same
      check reports 8 mismatching records here and 18 in the checker's own pre-move comparison inside this
      same run, so the COUNT of failures can move while the CAUSE does not.
2  "over 12 cells the tokens reproduce TOKEN-FOR-TOKEN (P2)"  got 2 cells, want []
   -> the same finding's second face (MC_FIELD_PLAIN.md Finding B): the two cells whose file reading moved
      are the two that do not reproduce. NOT this card's.
3  "...and the DRIVER digest of the driver that is on disk -- the gap F2 closed"
      got ['4018f0262498eb3e'] (what all 22 published coordinates carry)  want ['3bd43eed4c6e41f3']
   -> NEW, UNNAMED UNTIL THIS PARAGRAPH, and a consequence of card t_8edaaf2d's edit to the driver, not of
      this card. The recorded state after the field re-take (card t_ec0b0420) was 109/111 with TWO failures;
      4018f0262498eb3e is the driver OF THAT DAY (MC_FIELD_PLAIN.md:24, :89, :217-218) and t_8edaaf2d moved
      it to 3bd43eed4c6e41f3. `grep -rn 4018f0262498eb3e` over the tree returns the 22 records and no
      document, so no landing note names this consequence. **CARDED AS `t_d68e29ba`** (assignee the
      missile-command cabinet, parent this card), with the decision written into it: either the record's
      `driver_digest` becomes a READING (as `entrant_digest` became in DECISION_entrant_identity.md) or the
      field is re-taken under the current driver -- and either way the check must still fail on a mutated
      record.
```

**WHY IT IS REPORTED HERE RATHER THAN IN A CARD OF ITS OWN QUIETLY:** the field checker is the cabinet's
instrument, and a reader who runs it now sees THREE failures where the record says two. Without this
appendix, the third one is indistinguishable from damage done by this card — which is exactly the defect
class this whole family of cards exists to remove, aimed at a landing note.

