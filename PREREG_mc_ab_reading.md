# PRE-REGISTRATION — THE A/B's `reading` STRING: A RECORD'S COPY AND A LIVE SCRIPT'S COPY, SEPARATED

**Card:** `t_16a3b025` (Ocho), the NAMED RESIDUAL of card `t_a74fee86`, found by that card's own reading of
`missile_command_legend_ab.py` and carded rather than tidied up. **This file and
`scripts/probe_ab_reading.py` are committed BEFORE the edit they describe**, so the edit cannot be read as
support for a claim whatever it shows. Same shape as `PREREG_mc_ab_arm_names.md` (card `t_a74fee86`),
`PREREG_mc_ab_arm_keys.md` (card `t_d21287e4`) and `PREREG_mc_entrant_identity.md` (card `t_8edaaf2d`).

**Nothing here is a criterion, a verdict or a re-score.** No record, no artifact and no frozen file is
touched. `FAILED ON THIS POPULATION` stands exactly as attached to C2 and C3 (`MC_VERDICT_1.md`).

**The decision this file pre-registers is drafted for the Chair's ratification**, because it moves TEXT A
RUN PUBLISHES (§1.6). It is Ocho's draft, not Ocho's ruling.

**Where the work happens.** The file is `cabinet/missile-command`'s (`missile_command_legend_ab.py`), so the
edit lands in this tree under `CABINET_STRUCTURE.md` rule 2, and the DOCUMENT is mirrored to `main` — `main`
does not carry this cabinet's python files.

---

## 0. THE INSTRUMENT'S OWN HISTORY, WHICH IS PART OF THE INSTRUMENT

**There is no smoke run and no scratch reconnaissance to declare, because none was taken.** What was done
before this file existed is READING, and it is named so a reader can judge the predictions against it:

```
read 1  missile_command_legend_ab.py:207-226   the artifact dict, and the `reading` value inside it
read 2  missile_command_run.py:495-524         LEGEND_ARMS, LEGEND_DEFAULT, legend(), legend_source(),
                                               legend_digest(); the declaration is read at IMPORT
read 3  MC_DECLARATION.md:20-22, :118-154      `legend_arm plain`, its note, and AMENDMENT 4
read 4  DECISION_mc_legend_arm.md              the decision that moved the key, and its reasons
read 5  probes/MC_LEGEND_AB.json               the PUBLISHED `reading`, verbatim (the record)
read 6  git log / stat probes/MC_LEGEND_AB.json  2026-10-17 11:31:43 -0700
```

**The predictions in §2 are therefore predictions about the GOVERNED RUN, not about a state nobody had
looked at.** No governed run of this probe was taken before the commit that carries it; the first one is
§5 step 2, and it is the pre-edit counterfactual.

---

## 1. THE DECISION, AND THE EDIT

### 1.1 TWO COPIES OF ONE SENTENCE, AND TWO DIFFERENT STATUSES

The sentence is the third sentence of the artifact's `reading` value (`missile_command_legend_ab.py:222-225`):

```
The DECLARED ARM DOES NOT MOVE: `example` remains the recorded instrument, and changing it is a separate
act with its own reason.
```

It exists in TWO places, and they are not the same kind of thing:

```
probes/MC_LEGEND_AB.json      a RECORD. The A/B ran on 2026-10-17 11:31:43 -0700, when `example` WAS the
(029244b6e5232a6b)            arm of record: the key moved to `plain` LATER THE SAME DAY (the population run
                              behind that move is timed in its own filename, MC_POPULATION_20261017-184752).
                              The sentence is TRUE OF ITS DAY, and the card's bounds forbid moving the record.

missile_command_legend_ab.py  a LIVE CAPTION. It is the string the next run would PUBLISH. Since the key moved
(the live copy)              it is false, and a re-run REPUBLISHES it -- the defect card t_a74fee86 named and
                              did not fix, because fixing it moves a published field.
```

### 1.2 THE DECISION: IT IS A LIVE CAPTION, AND IT IS CORRECTED

**The published copy is the record and is not touched. The live copy is a caption and is corrected.**
A record says what was true when it was written; a caption says what will be true when it is read. The same
words cannot be both, and the file that will republish them is on the caption's side of that line.

**The sentence carries THREE claims, and they do not stand or fall together. Read one at a time:**

```
(a) "The DECLARED ARM DOES NOT MOVE"                    TRUE, and it is what the sentence was FOR: running this
                                                        A/B does not move the declaration. KEPT -- and now
                                                        VERIFIED from the script's own source (R3: its only
                                                        write is its own artifact), not asserted by the text.
(b) "`example` remains the recorded instrument"         FALSE since 2026-10-17 (`MC_DECLARATION.md`'s
                                                        `legend_arm` is `plain`). DELETED.
(c) "changing it is a separate act with its own reason" TRUE, and the reason has a file. KEPT, with
                                                        `DECISION_mc_legend_arm.md` named.
```

**AND THE CARD'S SECOND BULLET IS ADDRESS-CHECKED RATHER THAN TRUSTED, BECAUSE IT IS WRONG ABOUT THIS FILE.**
The card says the sentence "also carries a live-looking claim that must be separated: whether `example` IS
STILL SELECTABLE (`--legend example` / `MC_LEGEND=example`) -- that part is true and must not be corrected
away with the false part." **The sentence does not state selectability at all** (read above: it states the
arm of RECORD). What is TRUE and absent is that both arms stay selectable, so the fix **ADDS** it rather than
preserving it — and it has to be added, because deleting the false clause alone would leave a reader of the
record holding the arm-of-record claim and nothing about whether `example` is still usable, which is the one
fact that keeps every `example`-era record reproducible. The claim is also not the A/B's to make: the A/B
does not accept `--legend` (it iterates `ARMS`); selectability is the DRIVER's (`missile_command_run.py:1281-1283`,
`:1301-1303`), so the corrected sentence attributes it to the driver's call time and says which two tokens do it.

### 1.3 WHY THE FIX IS NOT "SWAP THE LITERAL": THE ARM OF RECORD IS A CHANGING STATE

**Replacing `example` with `plain` would be true today and false the next time the key moves — the same
defect, deferred.** This is the family's own rule: a FIXED claim travels as text; a CHANGING state travels as
the reading that observes it. The arm of record is a changing state, and the driver already has the function
that reads it (`legend_source()`, `missile_command_run.py:508-513`), so the corrected sentence carries
**the driver's own reading, taken at the instant the artifact is written**, and names the file the value comes
from. **F4 is the check a swapped literal fails**: with the driver's default patched in memory to the other
arm, the constructed `reading` must FOLLOW the patch. A literal cannot, which is the whole difference.

### 1.4 THE EDIT (E5) — ONE FILE, ONE HUNK, TRANSCRIBED

The two sentences before it are untouched, character for character (R5 checks that against the published
words). The third sentence is replaced by:

```python
                    "cell -- a demonstration, not a field. THE DECLARED ARM DOES NOT MOVE AND IS NOT "
                    "ASSERTED HERE: this A/B writes nothing but this artifact, the arm of record is named by "
                    f"`MC_DECLARATION.md`'s `legend_arm` and read by the driver (it reported it as "
                    f"`{R.legend_source()}` when this artifact was written), and changing it is a separate "
                    "act with its own reason (`DECISION_mc_legend_arm.md`). BOTH ARMS REMAIN SELECTABLE at "
                    "the driver's call time (`--legend example` / `MC_LEGEND=example`): this A/B runs both, "
                    "and every cell carries the digest of the arm it was taken under."),
```

**Read what each clause buys, because every one of them is a check rather than a style choice:**

```
"AND IS NOT ASSERTED HERE"     the sentence stops claiming a state it does not read (F1: the stale clause is
                               gone; F3: what it carries instead is the driver's own reading)
"MC_DECLARATION.md's `legend_arm`"  it NAMES the file the value comes from, so a reader can re-read it (F2)
"`{R.legend_source()}`"        the value is a READING at the instant of the write, not a literal (F3, F4)
"writes nothing but this artifact"  the scope promise is now a claim about the SOURCE, and R3 reads it there
"DECISION_mc_legend_arm.md"    the "separate act with its own reason" gets the file that holds the reason
"BOTH ARMS REMAIN SELECTABLE"  the TRUE claim the card demanded, absent today, added with the driver's own
                               two tokens (F5)
"...the digest of the arm"     the existing per-cell `legend_digest` is why a reader can sort cells across
                               the move -- stated so the artifact says what it already carries
```

**IT IS AN f-STRING, AND THAT IS THE POINT.** The interpolated value is the ONLY thing in the sentence that
can change between runs; everything else in it is a fixed claim about the script and the declaration's
existence, both of which travel with the commit.

### 1.5 WHAT IS NOT TOUCHED

```
probes/MC_LEGEND_AB.json 029244b6e5232a6b -- the RECORD. Not rewritten, not "corrected", not re-taken.
MC_DECLARATION.md 2ada03ee2ad1f60b        -- the Chair's; this card reads it and writes nothing to it.
PREREG_mc_legend_ab.md 49784e02849a401f   -- a pre-registration (records what was true when written). Its
                                             :40 line calls `example` "the recorded instrument, unchanged",
                                             which is TRUE OF ITS DAY and stays.
PREREG_mc_ab_arm_names.md 3f670a15e8e9cb4e -- the parent card's pre-registration. It QUOTES the stale
                                             sentence (:365, :526) and names the residual; it stays.
PREREG_mc_population.md:21                -- cites an earlier digest of the A/B. NOT a defect, NOT corrected.
missile_command_run.py                    -- the driver, frozen for this card (3bd43eed4c6e41f3). Its
                                             `--legend` help says "the recorded instrument" of the DEFAULT,
                                             which is TRUE and interpolated: not this card's file.
missile_command_run.py:1239-1240, scripts/check_mc_field_plain.py:133
                                          -- arm names pinned in ASSERTIONS' expected values. An expectation
                                             may be a literal and is supposed to go stale loudly (card
                                             t_d21287e4's landing note §5). NOT touched.
the branch cascade, the four branch sentences, the field list, the refusal from t_a74fee86, ENTRANT,
STATES, PORT, the gate, the levels, the pre-registration the artifact carries
```

### 1.6 THE RATIFICATION, NAMED RATHER THAN ASSUMED — AND WHY THE LANDING COMES FIRST

**The decision is the Chair's to ratify because the change moves text a run publishes** (card
`t_a74fee86`'s own bound: *"if the change can move any of the artifact's fields ... it is the Chair's, not a
runner's"*). This card is therefore completed as a HANDOFF TO THE CHAIR, not as a ruling: the landing note
states the decision, its reason and its consequence, and the card is routed to `tiel` for review.

**AND THE ORDER — LAND, THEN RATIFY — IS A DECISION WITH A REASON, NOT AN IMPATIENCE.** The two states the
tree can be in while the ratification is pending are not symmetric:

```
unfixed (today)   any re-run of the A/B PUBLISHES a sentence the declaration contradicts -- and a re-run is
                  a gated act someone could take without reading this card.
fixed (landed)    any re-run publishes a TRUE sentence, and the one thing the Chair has not yet ratified is a
                  turn of phrase -- which is exactly what review is for.
```

**The reversal is one string.** The old text is quoted verbatim in §1.1, in the landing note, and in the
commit it was removed by; nothing else in the tree depends on it, `reading` is parsed by no consumer
(`grep -rn 'reading' --include=*.py` over the cabinet: no reader of this field's content), and the published
artifact was never touched. **If the Chair rules the other way, the fix is `git revert` of one commit and no
record, criterion or artifact has to move with it.**

---

## 2. PREDICTIONS — MADE BEFORE THE EDIT, FALSIFIABLE, NONE OF THEM A CEILING

**P1 (THE DEFECT IS IN THE FIELD, NOT ONLY IN THE PROSE, AND IT IS MEASURED PRE-EDIT).** Constructed by the
script's own `main()` with `run()` stubbed, the live `reading` is **byte-identical to the published
artifact's `reading`** — the record and the caption are the same sentence — while the driver's own reading of
the declaration is `the recorded default (plain)`. Falsified if they differ, or if the live string does not
carry the stale clause.

**P2 (PRE-EDIT THE PROBE FAILS ON EXACTLY THE FIX'S OWN CHECKS).** Pre-edit the probe is **8/14, rc 3, with
exactly F1, F2, F3, F4, F5 and F6 FAIL** and R1-R8 PASS. Falsified if any other check fails, or if any of the
six passes.

**P3 (POST-EDIT IT PASSES).** Post-edit the probe is **14/14, rc 0**. Falsified if any check fails.

**P4 (THE CORRECTED SENTENCE, CLAUSE BY CLAUSE).** Post-edit the constructed `reading`: (a) does not contain
the stale clause; (b) names `MC_DECLARATION.md`; (c) contains the driver's `legend_source()` value as read at
that instant; (d) keeps `--legend`, `MC_LEGEND` and `example`; (e) opens with the published first two
sentences, character for character. Falsified if any of the five fails.

**P5 (NON-RECURRENCE — THE CHECK A SWAPPED LITERAL FAILS).** With the driver's `LEGEND_DEFAULT` patched in
memory to the other arm, the constructed `reading` **changes and names the other arm**; on the state on disk
it names the arm the declaration names. Pre-edit the constructed `reading` is **invariant** under the patch.
Falsified if the post-edit text does not follow the patch, or if the pre-edit text does.

**P6 (ONLY THE LAST SENTENCE MOVES, AND NOTHING ELSE IN THE ARTIFACT DOES).** The constructed artifact's field
set is the published field set (minus `artifact_replaced`, which only a REPLACING run writes), and the
fingerprint of every field that is neither the `reading`, nor a function of the stubbed cells (`cells`,
`totals`, `branch`), nor the box's unreproducible `entrant_digest`, is **IDENTICAL pre-edit and post-edit** —
both logs carry it. Falsified if the field set differs, or if the two runs' fingerprints differ.

**P7 (NOTHING ELSE MOVES).** The published artifact is not written by any command in §5:
`git status --porcelain probes/ results/` is **0 lines after every command**; its **full sha256**, re-computed
in both runs, is `029244b6e5232a6b77e67cf5e21dea342c7da336a932386b3a16015e96b286c8`; all twelve frozen inputs in
§4 are unmoved; the driver's `--self-test` is **53/53** on both sides; the runner's `--dry-run` still prints
`coordinate arm plain (READ from MC_DECLARATION.md \`legend_arm\`)`. Falsified if any of these fails.

**P8 (THE DRIFT, AND ITS COSTS, NAMED BEFORE THEY LAND).** `missile_command_legend_ab.py` `2c1c12a90e850bdf`
-> **a different value** (a hash cannot be predicted from prose; the value is recorded in the landing note).
**No other digest in §4 moves.** And **two costs, named rather than discovered later**: (i)
`PREREG_mc_ab_arm_names.md`'s line numbers for this sentence (`:221-225` in that document's own words) still
cite the file as it was, and its §1.3 says the sentence is "NOT fixed here" — both are TRUE OF THE COMMIT THEY
DESCRIBE and stay, because a pre-registration records what was true when it was written; (ii) after this card
the phrase lives in exactly **three** tracked files, and a fourth would be a live copy (F6 is that check).

**P9 (THE PUBLISHED RECORD'S OWN WORDS ARE STILL THE PUBLISHED RECORD'S OWN WORDS).** R2 pins the published
`reading` **verbatim** in the probe, so a reader sees the card did not "fix" the record by editing it, and a
moved record FAILS a check instead of passing one. Falsified if R2 fails in either run.

---

## 3. CONTROLS — EACH WITH THE COMMAND THAT READS IT

The controls are numbered `CONTROL n`; the instrument's own checks keep the `Fn`/`Rn` labels, so a reader can
tell a control in this note from a line of a probe log.

```
CONTROL 1   THE FIELD IS MEASURED, NOT QUOTED: the live `reading` is the output of the script's own main(),
            with run() stubbed -- no model, no lease, every number zero by construction. The STRING is not a
            function of the cells, which is why it can be read out of a stubbed run at all.   [READING 1]
CONTROL 2   AND THE TWO COPIES ARE COMPARED WITH EACH OTHER, not with a copy of the sentence typed here
            (the one literal this probe pins is the RECORD's own words, and pinning them is what makes a
            moved record fail).                                                        [R1, R2, READING 1]
CONTROL 3   THE STALE CLAIM IS CHECKED AGAINST THE DECLARATION, not against an opinion: the driver's
            `legend_source()` is printed beside the string in every run.        [header, F1, F3, R4]
CONTROL 4   THE CHECK A SWAPPED LITERAL FAILS. Patching the driver's default in memory to the other arm must
            move the text; a literal `plain` would sit there naming the wrong arm.          [F4, P5]
CONTROL 5   THE TRUE CLAIM IS CHECKED FOR, NOT GESTURED AT: the three tokens that make `example` selectable
            must be present in the corrected text.                                    [F5]
CONTROL 6   THE SCOPE OF THE EDIT IS PINNED ON BOTH SIDES: the first two sentences must be the published
            words (R5), and every other artifact field must be unmoved (R8 + fingerprint). [R5, R8, P6]
CONTROL 7   THE CARRIER SWEEP READS THE WHOLE TRACKED TREE, and names the files too large to read rather than
            skipping them silently. Its needle is ASSEMBLED FROM FRAGMENTS so the instrument is not a carrier
            of the sentence it hunts.                                                       [F6, P8(ii)]
CONTROL 8   THE SENTENCE'S OWN PROMISE IS CHECKED FROM THE SOURCE: "this A/B writes nothing but this
            artifact" is an AST reading of every write-mode open(), every mutating call, every makedirs and
            every json.dump in the module -- not a promise taken from prose.                [R3]
CONTROL 9   THE PROBE CAN FAIL, AND DOES (8/14 pre-edit, rc 3): F1-F6 are its falsifiable core.  [P2]
CONTROL 10  NO RECORD IS WRITTEN: `git status --porcelain probes/ results/` is read IN THE SAME RUN as every
            reading above, so "nothing moved" is a reading with a time rather than a promise.     [R6]
CONTROL 11  THE PUBLISHED ARTIFACT'S DIGEST IS RE-COMPUTED IN FULL -- 64 hex, not the 16-hex prefix the card
            quotes -- in both runs.                                                          [R1, P7]
CONTROL 12  THE FROZEN INPUTS ARE RE-READ, twelve of them, including both pre-registrations this card
            descends from; the reachable state is printed in the header so a reader can see WHICH state the
            readings were taken in.                                              [header, R4, R7, §4]
```

**The checks, as they appear in the instrument:** `F1, F2, F3, F4, F5, F6` (the fix's own) and `R1, R2, R3,
R4, R5, R6, R7, R8` (replication controls) — **fourteen**, of which **six move** (8/14 rc 3 before, 14/14
rc 0 after).

---

## 4. FROZEN INPUTS — RE-READ, NOT QUOTED FROM THIS NOTE

```
missile_command_legend_ab.py   2c1c12a90e850bdf  ->  A DIFFERENT VALUE  (P8; the edit; the drift)
EVERYTHING ELSE UNCHANGED (the probe re-reads each one and fails R7 if any moved):
  missile_command.py eb5ed36591b300e6 · missile_command_run.py 3bd43eed4c6e41f3 · PREREG_missile_command.md
  01548e9a866df03e · levels/mc_01_one_shot.txt ab101ca955c1c853 · levels/mc_02_scarcity.txt 327d2157bd0b8a83
  MC_DECLARATION.md 2ada03ee2ad1f60b · scripts/run_guarded.sh 5e34e455b5193e89 · PREREG_mc_population.md
  cfedf8b7f5e7d57f · PREREG_mc_legend_ab.md 49784e02849a401f · PREREG_mc_ab_arm_keys.md 47db6b9368bae18c
  PREREG_mc_ab_arm_names.md 3f670a15e8e9cb4e · probes/MC_LEGEND_AB.json 029244b6e5232a6b  (sha256, R1)
IDENTITY_IN_RECORD ("server_binary_digest", "legend_digest", "reasoning") -- untouched, the Chair's
NOT IN THIS LIST, AND THE REASON IS THE CARD: the published artifact is the RECORD this card is about; the
probe reads it and re-computes its digest, and no command in §5 writes to it. Nor is this file: it gains a
landing note.
```

**And one reading is deliberately NOT compared, with its reason.** The stub fixture's artifact carries an
`entrant_digest` of its own (the 1.3 GiB `Qwen3.5-2B-UD-Q4_K_XL.gguf`) and it will not necessarily equal the
published one: the model files in `ARENA_MODELS` do not hash reproducibly on this box (card `t_cdd433bb`), so
an `entrant_digest` is a reading at an instant rather than an identity. The fingerprint in P6 excludes it,
and a reader who sees the two digests differ has found the already-named defect, not a new one.

---

## 5. THE ORDER OF OPERATIONS, FIXED HERE

```
1  commit this file + scripts/probe_ab_reading.py                                (pre-registration + instrument)
2  run the probe      -> P2 must hold: 8/14, F1-F6 FAIL, rc 3                      [unit mc-ab-reading-probe-pre]
3  run the driver's --self-test -> 53/53                                           [unit mc-ab-reading-selftest-pre]
4  run the runner's --dry-run   -> `coordinate arm plain`                          [unit mc-ab-reading-dryrun-pre]
5  make E5 (one hunk, one file)
6  run the probe again -> P3 must hold: 14/14, rc 0; P1/P4/P5/P6 unchanged         [unit mc-ab-reading-probe-post]
7  run the driver's --self-test and the runner's --dry-run again
                                                                   [units mc-ab-reading-selftest-post, -dryrun-post]
8  read §4 back: the digests, and git status --porcelain probes/ results/          (R6, R7, P7, P8)
9  append the landing note to THIS file (drift, counts, every prediction by name, anything corrected)
10 commit the edit with the landing note; mirror this document to main; push both; read both back
11 the card is routed to the Chair (`tiel`) for ratification of §1.6
```

**Step 2 is not optional and it is not ceremony.** Without it, "14/14 after the edit" is a number with no
counterfactual: with it, the same probe on the same tree returns 8/14 and 14/14 depending on whether one
sentence in one file reads a changing state or asserts it.

**Every command in §5 runs under `scripts/run_guarded.sh` (`5e34e455b5193e89`), never a bare `python3`**, with
an ABSOLUTE workdir (the parent card lost three units to a relative one: its own addendum (b)). The probe takes
no lease, loads no model and starts no server, so no lease can be held by any command here.

---

## 6. WHAT WOULD FALSIFY THE CARD, AND WHAT WOULD NOT COUNT AS SUCCESS

**Falsified if** the live `reading` is not the published one pre-edit (P1 — then the published record is not
what the script would publish and this card's whole framing is wrong), or the pre-edit probe refuses to fail
(P2, P5), or the post-edit probe still asserts the arm of record as a literal, or does not follow the
declaration when it moves (P3, P4, P5), or any other artifact field moves (P6), or any frozen input in §4
moves (P7, P8), or the driver's self-test count moves, or the record's own words are not the record's words
(P9).

**NOT success:** swapping the literal (`example` -> `plain`) — true today, false the next time the key moves,
and F4 is the check it fails. **NOT success either:** deleting the sentence. It carries a true scope promise
(this A/B does not move the declaration) and a true fact about changing it; and the selectability of
`example` has to be **added**, because it is not in the sentence to preserve (§1.2). **And NOT success:**
editing the declaration, the driver, the pre-registration, `PREREG_mc_population.md`'s citation, or the
published artifact to make the live script true. The declaration is the Chair's; the driver is frozen for
this card; the artifact is a record.

**AND THE BOUND THIS DECISION LEAVES, STATED RATHER THAN LEFT TO BE FOUND.** The corrected sentence reads the
arm of record **at the instant the artifact is written**, through `legend_source()`. It says nothing about
which arm any EARLIER record was taken under — that is each cell's own `legend_digest`, and the two are not
interchangeable: a record taken under `example` carries `ec59f2dc5fd35518` and stays that way after the
declaration moves. A reader who wants "which arm was of record on the day of THIS run" reads this field; a
reader who wants "which arm was this CELL taken under" reads the cell. Both are in the artifact, and after
this card they cannot be confused by a stale sentence.
