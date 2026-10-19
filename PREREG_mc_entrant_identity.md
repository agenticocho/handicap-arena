# PRE-REGISTRATION — THE COORDINATE ARM READ FROM THE DECLARATION, AND THE ENTRANT SCOPE SENTENCE REPLACED BY A READING

**Card:** `t_8edaaf2d` (Ocho), the third of the three things `DECISION_entrant_identity.md` §5 deferred. **This
file is committed BEFORE either edit it describes**, so neither edit can be read as support for a claim
whatever it shows. Same shape as `PREREG_mc_field_plain.md` (card `t_ec0b0420`), which is the card this one
inherits its discipline from.

**Nothing here is a criterion, a verdict or a re-score.** No record, no artifact and no frozen file is
touched. `FAILED ON THIS POPULATION` stands exactly as attached to C2 and C3 (`MC_VERDICT_1.md`).

**Where the work happens.** The decision is Ocho's and lives in `main`; the two files are
`cabinet/missile-command`'s (`missile_command_population.py`, `missile_command_run.py`), so the edits land in
this worktree under `CABINET_STRUCTURE.md` rule 2 and are mirrored to `main` as documents, not as code.

---

## 0. A NOTE ON THE INSTRUMENT, WHICH WAS EXERCISED BEFORE THIS FILE EXISTED

The probe that measures both edits (`scripts/probe_coord_arm_adoption.py`) was written and run **once**
before this commit, to find out whether it runs at all — and **its first control was wrong**, which is
recorded here rather than tidied away. It asserted that the *counterfactual* arm must be refusable
("a probe that reports adoptable for both arms is measuring nothing"). Measured against the tree, the
counterfactual arm (`plain`) adopted **22/22** — because `plain` **is** the declaration's arm and those are
plain-arm records, which is this card's entire point. The control was therefore not testing the probe, it
was contradicting the finding. **It was replaced by two controls that can fail** (§3, C2 and C3), and the
run this pre-registration governs is the one taken **after** this commit. The wrong first run's output is
quoted in §6 and is not presented as evidence about anything except that the first control was wrong.

**The instrument's own history is part of the instrument.** A probe whose control was silently corrected
between two runs is a probe whose second number cannot be trusted either.

---

## 1. THE TWO EDITS, FIXED HERE BEFORE THEY ARE MADE

### E1 — `missile_command_population.py`: the coordinate arm is DERIVED, and the arm NAMES are read too

**What is removed** (line 43, and the second copy of the arm names at line 42):

```
ARMS = ("example", "plain")
COORD_ARM = "example"
```

**What replaces it** — the exact code, so the edit is a transcription:

```python
# THE ARMS THE DRIVER DEFINES ARE READ FROM THE DRIVER. A second copy of the arms' own names is the same
# defect as a second copy of WHICH arm is of record, one layer down.
ARMS = tuple(R.LEGEND_ARMS)
# THE COORDINATE ARM IS THE DECLARATION'S, READ THROUGH THE DRIVER'S OWN READ (R.LEGEND_DEFAULT =
# MC_DECLARATION.md's `legend_arm`, refused at import if that key is missing). It is NOT a module constant
# and NOT defaulted to a literal:
#   * a constant here was a SECOND COPY of a decision the declaration owns, and it went stale -- pinned at
#     `example` after the declaration's key moved to `plain` (2ada03ee2ad1f60b, DECISION_mc_legend_arm.md);
#   * measured, not argued: with the pin at `example`, every one of the 22 published coordinates holds a
#     record whose `legend_digest` disagrees with `run_identity()`, so a re-run records `never_started` --
#     "the published coordinate holds a record taken under a DIFFERENT instrument" -- where the adoption
#     rule exists precisely to ADOPT it (scripts/probe_coord_arm_adoption.py re-takes both arms);
#   * hard-coding `plain` would be the same defect with a fresher value: stale again the day the
#     declaration moves, and stale silently.
COORD_ARM = R.LEGEND_DEFAULT
if COORD_ARM not in ARMS:
    raise SystemExit(f"REFUSED: the declaration names legend_arm {COORD_ARM!r}; this runner's arms are {ARMS}.")
if len(ARMS) < 2:
    raise SystemExit(f"REFUSED: the driver defines {len(ARMS)} legend arm(s) {ARMS}; this runner needs an arm "
                     f"of record and one comparison arm and will not invent the second.")
# THE COMPARISON ARM IS DERIVED TOO -- "whichever arm is not of record", not a literal `plain` that goes
# stale the day the declaration names the other one.
COMPARISON_ARM = next(a for a in ARMS if a != COORD_ARM)
```

**Three call sites follow from it, and they are the whole of E1's behavioural change:**

1. the `--dry-run` line now **names its source**, which is what the card's verification step reads:
   `coordinate arm plain (READ from MC_DECLARATION.md legend_arm, digest 2ada03ee2ad1f60b; comparison arm example)`
2. `meta["arms"]["comparison"]` was the literal `"plain"` and becomes `COMPARISON_ARM` (the same defect in
   the other direction: with the declaration naming `example`, a literal `"plain"` here would be wrong).
3. the placement branch (`if arm == COORD_ARM:`), the adoption rule, the gate, the reason string and
   `IDENTITY_IN_RECORD` are **untouched** — they read `COORD_ARM`, which is now the declaration's value.

**And one caption in the same file is corrected because it is stale prose above working code**: the module
docstring says the run `RUNS the recorded arm (`example`)` and `the declared comparison arm (`plain`)`.
`example` is not the recorded arm and has not been since 2026-10-17. **A caption is not a check**, and this
one is being edited anyway; corrected to "the arm `MC_DECLARATION.md` names" and "the other arm".

### E2 — `missile_command_run.py`: `entrant_digest_scope` becomes a TRANSCRIPTION of §3(a)

**The sentence carried today** (one place in the driver, line 977):

```
sha256 of the model FILE, first 16 hex. THE ENTRANT IS THE SUBJECT OF THE MEASUREMENT, so it is identified
by a digest; `entrant` beside it is a LABEL, for reading, not for checking.
```

**The replacement is the text fixed in `DECISION_entrant_identity.md` §3(a), and it is a transcription, not a
re-write.** The field keeps its name, its computation (`file_digest(entrant)`) and its value; **only the
sentence changes.** The one transformation is whitespace: the decision's code block is wrapped and indented,
and the record field is one string, so line wraps and the block's two-space indent are collapsed to single
spaces. **`scripts/probe_coord_arm_adoption.py` checks that this is the ONLY transformation** — it reads the
literal out of the source by AST and compares it word for word, whitespace-normalised, with §3(a), read from
`main` by path and digested in its output.

**No other line of the driver changes, and `git diff` is the check that says so.**

---

## 2. PREDICTIONS — MADE BEFORE EITHER EDIT, FALSIFIABLE, AND NOTHING HERE IS A CEILING

**P1 (E1, the card's own verification step).** `missile_command_population.py --dry-run` prints
`coordinate arm plain`, and that value **equals the declaration's own `legend_arm` read independently**
(`MC_DECLARATION.md`, digest `2ada03ee2ad1f60b`). **Before the edit the same command prints `example`**
(measured: `logs/mc-entrant-id-dryrun-pre.out`). Falsified if the dry-run prints anything else, or if the
printed value is not the declaration's.

**P2 (E1, model-free, the arm's EFFECT rather than its label).** Run with the declaration derived
(`plain`): the probe reports **ADOPTED 22/22** under the runner's arm, **0/22** under the counterfactual
(`example`), CONTROL 1 and CONTROL 2 PASS. Falsified if any coordinate is refused under `plain`, or if a
member of the identity triple other than `legend_digest` appears in any diff.

**P2′ (E1, the same probe BEFORE the edit — the positive control for P2).** Run while `COORD_ARM` is still
`example`: **ADOPTED 0/22** under the runner's arm, **22/22** under the counterfactual, every diff exactly
`['legend_digest']`, CHECK 3 **FAIL** (`'example'` against `legend_arm 'plain'`), transcription **FAIL**,
exit **3**. Falsified if the pre-edit run already adopts under its own arm — that would mean the pin was
never the defect the decision says it is.

**P3 (E2, the driver's self-test).** **53/53 after the edit, unchanged** (measured 53/53 before it,
`logs/mc-entrant-id-selftest-pre.out`). A string transcription and a constant removed from a *different*
file move no control: the driver's controls read the source for which *fields* are stored, not what a scope
sentence says. **Falsified if the count moves — and a move would be recorded in the landing note with its
reason, never trimmed back to fit this prediction.**

**P4 (drift).** `missile_command_run.py` `4018f0262498eb3e` → **a different value** (a hash cannot be
predicted from prose, so no particular value is predicted; the value is recorded in the landing note).
`missile_command_population.py` `682756d57c2cbe5c` → **a different value**. **No other digest in §4 moves.**
Falsified if the driver's digest is unchanged after an edit (that would mean the edit did not land) or if any
input in §4 moved.

**P5 (no record is touched).** `git status --porcelain probes/ results/` is **empty** after every command in
§5. The probe writes nothing and the dry-run writes nothing; neither loads a model and neither takes a lease.
Falsified if any coordinate changes.

**P6 (frozen inputs).** `missile_command.py` `eb5ed36591b300e6`, `PREREG_missile_command.md`
`01548e9a866df03e`, `levels/mc_01_one_shot.txt` `ab101ca955c1c853`, `levels/mc_02_scarcity.txt`
`327d2157bd0b8a83`, `MC_DECLARATION.md` `2ada03ee2ad1f60b`, and `IDENTITY_IN_RECORD` =
`("server_binary_digest", "legend_digest", "reasoning")` — **all unchanged after both edits.**

---

## 3. CONTROLS — EACH WITH THE COMMAND THAT READS IT

```
C1  THE ARM PRINTED IS COMPARED WITH THE DECLARATION, NOT WITH A LITERAL IN THIS NOTE.
    grep -n '^legend_arm ' MC_DECLARATION.md        against      --dry-run's own line
    A dry-run that printed a value this note mentions would prove nothing; it has to BE the declaration's.
C2  NO IDENTITY MEMBER BUT `legend_digest` MOVES (probe, CONTROL 1). Any other member in a diff is a live
    reading that moved -- `server_binary_digest` is a binary read on a box that flips ~1 bit per 0.3-1.5 GB of
    data in motion (DECISION_entrant_identity.md §1) -- and it must show as itself, not as the arm.
C3  THE TWO ARMS DISAGREE ON EVERY CELL (probe, CONTROL 2). They differ by a member of the identity triple.
    Agreement means the probe cannot see the arm and its number is worthless.
C4  THE TRANSCRIPTION IS CHECKABLE (probe, section 3(a) block): word-for-word equality, whitespace-normalised,
    against DECISION_entrant_identity.md read from main at path ../../ocho_arena/DECISION_entrant_identity.md
    (digest printed), plus the absence of the sentence the decision measured false.
C5  THE FIELD'S NAME AND ITS COMPUTATION DID NOT MOVE (probe, section 3(d)): every `entrant_digest` entry in
    the driver is still `file_digest(entrant)` (3 entries), and `entrant_digest_scope` occurs exactly once.
C6  THE RUNNER'S ARM IS THE DECLARATION'S (probe, CHECK 3): `COORD_ARM == R.LEGEND_DEFAULT`, FAIL before the
    edit and PASS after it. This is E1 stated as a check instead of eyeballed in a log line.
C7  NO RECORD MOVED (P5) and THE FROZEN INPUTS DID NOT (P6): sha256sum + `git status --porcelain probes/
    results/`, both read after the last command, not before the first.
```

**Every command in §5 runs under `scripts/run_guarded.sh` (`5e34e455b5193e89`), never a bare `python3`**, for
the reason `PREREG_mc_field_plain.md` gives: a bare run escapes the ceiling, and a guard with an unrecorded
exception is aimed at the guard itself.

---

## 4. THE INPUTS, WITH DIGESTS, AS READ WHEN THIS FILE WAS COMMITTED

```
missile_command.py                        eb5ed36591b300e6   the frozen simulator -- UNTOUCHED
PREREG_missile_command.md                 01548e9a866df03e   the frozen criteria + outcome rows -- UNTOUCHED
levels/mc_01_one_shot.txt                 ab101ca955c1c853   state 01 -- UNTOUCHED
levels/mc_02_scarcity.txt                 327d2157bd0b8a83   state 02 -- UNTOUCHED
MC_DECLARATION.md                         2ada03ee2ad1f60b   legend_arm plain -- the key E1 stops duplicating
missile_command_run.py                    4018f0262498eb3e   the driver BEFORE E2   -> DRIFT PREDICTED (P4)
missile_command_population.py             682756d57c2cbe5c   the runner BEFORE E1  -> DRIFT PREDICTED (P4)
DECISION_entrant_identity.md (main)       74da417947272452   §3(a) is the text E2 transcribes
PREREG_mc_population.md                   cfedf8b7f5e7d57f
probes/MC_POPULATION_20261017-184752.json 9335b2a39b4d1d38   the population run of record (no field in it moves)
probes/MC_LEGEND_AB.json                  029244b6e5232a6b
scripts/run_guarded.sh                    5e34e455b5193e89   the ceiling every command goes through
the 22 published coordinate records        NOT DIGESTED HERE, and that is deliberate: a multi-GB-adjacent
                                           file's digest is exactly what this box does NOT reproduce, so they
                                           are protected by `git status` (C7) and by the probe's read-only
                                           path, not by a hash this note would have to trust.
```

---

## 5. THE ORDER OF OPERATIONS, FIXED HERE

```
1  commit this file + scripts/probe_coord_arm_adoption.py                    (pre-registration + instrument)
2  run the probe            -> P2′ must hold (0/22, CHECK 3 FAIL, exit 3)     [unit mc-entrant-id-probe-pre-rerun]
3  make E1 and E2                                                                (two files, two hunks)
4  run the probe again      -> P2 must hold (22/22, exit 0)                   [unit mc-entrant-id-probe-post]
5  run the driver's self-test -> P3 must hold (53/53)                         [unit mc-entrant-id-selftest-post]
6  run the runner's --dry-run -> P1 must hold (coordinate arm plain)          [unit mc-entrant-id-dryrun-post]
7  read C7 back: git status, and the digests of §4
8  append the landing note to THIS file (drift, counts, any prediction corrected)
9  commit the edits with the landing note; mirror the documents to main; push both; read both back
```

**Step 2 is not optional and it is not ceremony**: without it, "22/22 adopted" after the edit is a number
with no counterfactual. With it, the same probe on the same records returns 0/22 and 22/22 depending on one
line of code — which is the decision's claim, measured.

---

## 6. WHAT WOULD FALSIFY THE CARD, AND WHAT WOULD NOT COUNT AS SUCCESS

**Falsified if** the pre-edit probe adopts under its own arm (P2′), or the post-edit probe refuses any of the
22 (P2), or the dry-run's arm is not the declaration's (P1), or the transcription check passes on text that
differs from §3(a) (C4), or the self-test count moves and cannot be explained (P3), or any frozen input in
§4 moves (P6).

**NOT success:** the dry-run printing `plain` because a literal was typed into the runner. That is the
defect with a fresher value; C6 is the check that distinguishes them (`plain` derived from
`R.LEGEND_DEFAULT` cannot disagree with the declaration, while a literal can and will).

**The first, wrong run of the probe** (before this file existed, before its control was corrected) printed,
for the record and for nothing else:

```
  UNDER TEST (the runner's own arm): arm 'example'  ADOPTED 0/22
  POSITIVE CONTROL (the other arm):  arm 'plain'    ADOPTED 22/22
  CONTROL FAILED: the other arm ('plain') adopts 22 coordinate(s). ...
  VERDICT FAIL (rc 3)
```

**The number that mattered in it was 22/22**, and it is the reason the control changed: the counterfactual
arm adopting all 22 coordinates is not a broken probe, it is this card's finding.

---

# LANDING NOTE — APPENDED AFTER THE WORK, WITH THE READINGS AND EVERY PREDICTION DISCHARGED BY NAME

**Written after both edits and after every command in §5, 2026-10-19 ~06:51 PDT.** This note is appended;
nothing above it is rewritten. **No record, no artifact and no frozen file was touched**, and no model was
loaded — the whole of this card is a string, a derivation and reads.

## 1. THE READINGS, EACH WITH ITS UNIT, ITS INSTANT AND ITS EXIT

```
BEFORE THE EDITS (baselines, taken before this file was committed)
  06:41:40  mc-entrant-id-selftest-pre        missile_command_run.py --self-test        ALL CONTROLS PASS 53/53
  06:42:08  mc-entrant-id-dryrun-pre          missile_command_population.py --dry-run   coordinate arm example
  06:44:12  mc-entrant-id-probe-pre           scripts/probe_coord_arm_adoption.py       exit 3  -- the FIRST control
                                                                                        was wrong; see section 0
AFTER THE PRE-REGISTRATION, BEFORE THE EDITS (the governed counterfactual)
  06:48:25  mc-entrant-id-probe-pre-rerun     scripts/probe_coord_arm_adoption.py       exit 3  (P2')
AFTER THE EDITS
  06:50:08  mc-entrant-id-probe-post          scripts/probe_coord_arm_adoption.py       exit 0  (P2)
  06:50:31  mc-entrant-id-selftest-post       missile_command_run.py --self-test        ALL CONTROLS PASS 53/53 (P3)
  06:51:01  mc-entrant-id-dryrun-post         missile_command_population.py --dry-run   coordinate arm plain,  (P1)
                                                                                        READ from MC_DECLARATION.md
every one of the seven under scripts/run_guarded.sh 5e34e455b5193e89; logs are logs/<unit>.out
```

**The dry-run's own line, verbatim** (the card's verification step, and the value compared with the
declaration's key read independently — `MC_DECLARATION.md:20  legend_arm plain`, C1):

```
ARMS        ('example', 'plain')   coordinate arm plain   (READ from MC_DECLARATION.md `legend_arm`,
declaration digest 2ada03ee2ad1f60b; comparison arm example)   legend digests {'example':
'ec59f2dc5fd35518', 'plain': 'd8ee3da099c1a0c2'}
```

**The probe's two arms over the SAME 22 records, one line of code apart:**

```
               runner's own arm                          counterfactual arm
BEFORE  E1     'example'  ADOPTED  0/22  never_started 22/22   'plain'    ADOPTED 22/22
AFTER   E1     'plain'    ADOPTED 22/22  never_started  0/22   'example'  ADOPTED  0/22
every single diff, before and after, is exactly ['legend_digest'] and nothing else  (CONTROL 1 PASS, twice)
the two arms disagree on 22/22 cells in both runs                                   (CONTROL 2 PASS, twice)
```

**That is the decision's claim, measured rather than argued**: the pin at `example` did not merely mislabel
the arm, it turned the adoption rule into a refusal on every published coordinate — and reading the
declaration turns the same run into adoption. **No population run was taken** (the card forbids re-running
it): the probe asks the runner's own placement question with the runner's own functions, which is the part a
model cannot change.

## 2. THE DRIFT, AS PREDICTED (P4)

```
missile_command_run.py         4018f0262498eb3e  ->  3bd43eed4c6e41f3     E2, the transcription
missile_command_population.py  682756d57c2cbe5c  ->  e588199faf5bbbaa     E1, the derivation
everything else in §4 UNCHANGED, re-read after the last command:
  missile_command.py eb5ed36591b300e6 · PREREG_missile_command.md 01548e9a866df03e · mc_01 ab101ca955c1c853
  mc_02 327d2157bd0b8a83 · MC_DECLARATION.md 2ada03ee2ad1f60b · run_guarded.sh 5e34e455b5193e89
  PREREG_mc_population.md cfedf8b7f5e7d57f · MC_POPULATION_20261017-184752.json 9335b2a39b4d1d38
  MC_LEGEND_AB.json 029244b6e5232a6b
IDENTITY_IN_RECORD unchanged: ("server_binary_digest", "legend_digest", "reasoning")  -- untouched, the Chair's
git status --porcelain probes/ results/  ->  0 lines   (no record moved, P5/C7)
```

**The 22 coordinate records are NOT digested in this note, deliberately** (§4): on this box a whole-file
digest of a file that large is exactly the reading that does not reproduce. They are protected by
`git status` and by the probe's read-only path, which is checkable; a hash here would be a number that
looks like evidence and is not.

## 3. EVERY PREDICTION, DISCHARGED BY NAME — NONE CORRECTED, NONE TRIMMED

```
P1  dry-run prints `plain` and it equals the declaration's own key ......  HIT   (06:51:01; example before: 06:42:08)
P2  probe AFTER: 22/22 adopted, counterfactual 0/22, controls PASS, exit 0  HIT   (06:50:08)
P2' probe BEFORE: 0/22 under its own arm, 22/22 counterfactual, exit 3 ...  HIT   (06:48:25)
P3  self-test 53/53 after the edit .....................................  HIT   (53/53 before, 53/53 after)
P4  driver and population digests both change; nothing else moves ......  HIT   (values in §2)
P5  no record touched; probe and dry-run write nothing .................  HIT   (0 lines)
P6  frozen inputs and IDENTITY_IN_RECORD unchanged .....................  HIT   (§2)
```

**AND ONE THING THIS NOTE RECORDS BECAUSE THE DISCIPLINE CAUGHT IT, which is not a prediction:** while making
E1 I added a field to the population artifact's `meta["arms"]` (`arm_source`) to say where the arm came
from. **It was not pre-registered** — §1 fixed exactly three call sites — so it was removed before commit.
The diff this note lands carries only what §1 fixed. *An un-pre-registered improvement is a change with no
prediction to be wrong about, and the rule is the same one that keeps a control from being trimmed to fit.*

## 4. WHAT THIS LANDING DOES NOT DO, AND ONE THING IT NAMES FOR A LATER CARD

**Nothing was re-scored, re-scoped or re-run.** C1–C3, the outcome rows and `FAILED ON THIS POPULATION` are
untouched; no record was edited; no criterion read; `n`, the states, the criteria and the ceiling are as they
were. **`entrant_digest` is still not an identity, and nothing in this diff treats it as one.**

**NAMED, NOT CHANGED — a second copy of the arm names remains one layer down in the same file.**
`missile_command_population.py`'s `aggregate()` fixes the A/B comparison it reports as the literals
`"example"` / `"plain"` (`_arm_cells(cells, "plain")`, and the `arm_effect` block beside it). That is the
comparison `PREREG_mc_population.md` fixed and the artifact's own shape, not the placement rule — so it is
**not** this card's to move, and moving it would change a published artifact's fields. It is written here
because a reader who has just watched `COORD_ARM` stop being a constant will ask, and the answer should be a
sentence rather than a silence. If the declaration ever names `example` again, that block is wrong **and
this note is where the next card will find it.**

**AND THE CHECKER FOLLOWS ON ITS OWN CARD.** `scripts/check_mc_field_plain.py` still compares
`record["entrant_digest"] == file_digest(path)` and its comment still carries the sentence this card removed
from the record — that is card `t_77f73033` (`DECISION_entrant_identity.md` §5), the cabinet's file, and it
is not touched here.
