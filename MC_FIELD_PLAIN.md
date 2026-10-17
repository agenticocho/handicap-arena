# MC_FIELD_PLAIN — THE CABINET'S FIELD RE-TAKEN UNDER THE ARM IT DECLARES, AND WHAT THE RUN MEASURED

**Card:** `t_ec0b0420`. **Pre-registration:** `PREREG_mc_field_plain.md` (`c89d8ad21fe1ed04` as committed at
`b4a6323`, BEFORE the driver was edited and before the first entrant moved; the landing note appended to it
carries the corrections and the drift, and the file is now `e40ac17826d2f87a`).
**The run of record is the 22 coordinates themselves** — `probes/MC_<entrant>_<level>.json` — each one run,
one path, each carrying its own reason and the record it replaced. **No aggregate artifact was written
beside them**: a bundle holding the same 22 records would be a second copy of records that already exist one
per path, which is the defect this project keeps removing. What re-derives every number below is a checker:
**`scripts/check_mc_field_plain.py`** (111 checks over the 22 records, the archive, the population artifact
and the files on disk — run it and the numbers appear).

**Nothing frozen moved:** `missile_command.py` `eb5ed36591b300e6`, `PREREG_missile_command.md`
`01548e9a866df03e`, `levels/mc_01_one_shot.txt` `ab101ca955c1c853`, `levels/mc_02_scarcity.txt`
`327d2157bd0b8a83`. **No criterion is read here at all** and **the population verdict is not re-scored and
not re-scoped** — it stands as computed on the arm of record (`FAILED ON THIS POPULATION` attached to C2 and
C3). This document reports a field, a replacement, two instrument facts and two findings.

---

## 1. THE INSTRUMENT FIX, AS PRE-REGISTERED — AND THE THIRD FACT F1/F2 DID NOT NAME

```
driver    b726188380ce681c  ->  4018f0262498eb3e      (the fix; self-test 50/50 -> 53/53)
F1  control [9]'s caption corrected, and the two comment sentences beside the legend arms with it
F2  driver_digest + driver_digest_scope INTO THE RECORD, on ALL THREE return paths
F3  the identity triple NOT extended to the driver digest -- with its measurable reason, not as caution
```

**F1 — THE STALE CAPTION, QUOTED.** It read *"THE LEGEND HAS TWO ARMS, AND THE ONE THE RECORDS WERE TAKEN
UNDER HAS NOT MOVED"* — false the day the declaration's key moved to `plain`, while the control under it was
true the whole time (it compares the driver's default against the DECLARATION, not against a constant). It now
reads *"THE LEGEND HAS TWO ARMS, EITHER MAY BE RECORDED, AND THE ONE OF RECORD IS THE ONE THE DECLARATION
NAMES"*, so the prose states what is checked. **The comment beside the arms said "`example` remains the
DEFAULT" and is corrected the same way, with the date it stopped being true** — the adjacent half of the same
defect, fixed rather than left standing.

**F2 — THE DRIVER'S OWN DIGEST, AND THE THIRD FACT.** The card named one gap: *a driver change is invisible
in the records it produced*. Measured while fixing it: **the load-failure return paths left `run()` BEFORE
the arm, the declaration and the driver were named** — visible in this very tree, on the two `Llama-3.2-3B`
coordinates, which carried no `legend_digest` at all. **An ATTEMPT that cannot be sorted by the arm it was
attempted under is the same defect one path over**, so the failure records now carry the same instrument
block (arm, both arms' digests, simulator, driver, declaration file + digest). Three controls were added
(`[9b]`), taking the self-test from **50/50 to 53/53** — the pre-registration predicted two and 52, and
**the prediction is corrected in the landing note rather than the controls trimmed to fit it.**

**F3 — WHAT WAS NOT DONE, WITH ITS REASON.** The identity triple the gate and the population runner's
adoption rule compare (`server_binary_digest`, `legend_digest`, `reasoning`) does **not** gain the driver's
digest: every existing record predates the field, so a triple that names it would make **every occupied
coordinate un-adoptable (`never_started`)** for the population runner — a change to an instrument this
cabinet does not own. Named as an open consequence, not made. *(The population runner also pins its
coordinate arm as a constant, `COORD_ARM = "example"`; after this re-take a re-run of it would find the
coordinates occupied by `plain`-arm records and refused. Also named, also not edited — `PREREG_mc_field_plain.md` §9.)*

## 2. THE FIELD, AND THE REASON EVERY REPLACEMENT CARRIES

**Derived from the coordinates on disk, not typed:** every `probes/MC_<entrant>_<level>.json` whose level is
one of this cabinet's two states — **11 entrants × 2 states = 22 cells**, 20 measured records and 2
ATTEMPTS at the time of the archive. **n = 1 per cell.** Every cell went through `scripts/run_guarded.sh`,
never a bare `python3`.

**THE ARM WAS NOT NAMED ON THE COMMAND LINE.** No `--legend` flag: the driver read `legend_arm` from
`MC_DECLARATION.md`, which is the point of the move — the coordinates hold `plain` because the cabinet
declares it (`legend_source: "the recorded default (plain)"` in all 22 records).

**THE REASON, AS PRE-REGISTERED AND AS RECORDED 22/22 VERBATIM** (read from the pre-registration by the
checker, not typed into it):

```
THE COORDINATE HELD AN example-ARM RECORD AND THE DECLARATION NOW NAMES plain (MC_DECLARATION.md
2ada03ee2ad1f60b, DECISION_mc_legend_arm.md, card t_ec0b0420): the cabinet's field is re-taken under the arm
it declares. The replaced record's exact bytes are archived in probes/MC_FIELD_EXAMPLE_ARM_ARCHIVE_20261017.json
with their sha256, so the replacement is recorded rather than silent.
```

**AND THE REPLACED RECORDS ARE ARCHIVED, NOT LOST** — `probes/MC_FIELD_EXAMPLE_ARM_ARCHIVE_20261017.json`
(374,045 bytes, `edf414eaa1a8997f6fbde9caca70584f0ac79369e4e29c9736217829a9c3dcf3`), taken BEFORE the first
replacement: per cell the file's **exact bytes**, its sha256, byte count, mtime and what it said about its
own instrument. It was written because **five of the eleven entrants' `example`-arm records existed nowhere
else** — including `granite-3.3-2b`'s `3W`×4 cell, the record the declaration's amendment and the driver's own
comment quote as the A/B's motivation.

```
cells replaced        22 / 22, each with sha256 + byte count + mtime + the replaced record's own claimed arm
replaced-record mtms  2026-10-17T17:59:28Z (Bonsai-4B) .. 2026-10-17T18:55:32Z (Mellum)
verified against       the archive (22/22 digests and byte counts) AND, for the 12 cells the population
                       artifact also holds, against ITS OWN coordinate_sha256, taken by another instrument
records now carry      legend plain · legend_digest d8ee3da099c1a0c2 · declaration_digest 2ada03ee2ad1f60b
                       driver_digest 4018f0262498eb3e · simulator eb5ed36591b300e6 · 11 distinct entrant
                       digests · artifact_replaced
```

## 3. THE FIELD, MEASURED — AND THE CONTROLS IT CARRIES

```
mc_01 one shot    11 cells measured   scores [0,1,1,0,1,1,0,1,1,1,0]   7 of 11 engage the single threat
mc_02 scarcity    11 cells measured   scores [0,0,0,0,1,0,0,0,0,0,0]   1 of 11 finishes above zero
ARM TOTALS (22)   fired 12   passed 17   unknown 12   out_of_range 9   malformed 24   late 9   no_ammo 0
attempts 0   measured 22   planned 22   every cell ended `threats_resolved`
```

```
per cell, re-derived with the FROZEN SIMULATOR from (state_text, tokens), not read from the record:
      the score recomputes 22/22 · the counters recompute 22/22 · one outcome per token 22/22 ·
      every threat destroyed, hit or spared 22/22 · sufficiency re-derived 22/22
the checker's own control: a MUTATED action stream fails the same comparison, 22/22 -- it can fail
the arm, the declaration, the driver and the simulator: every value read FROM THE FILES ON DISK, 22/22
```

**THE NAME OF EVERY CELL, WITH ITS TOKENS, IS PRINTED BY THE CHECKER** (`logs/mc-field-check3.out` beside
the records); the score table above is its summary.

## 4. TWO FINDINGS, MEASURED — AND ONE PREDICTION FALSIFIED

### FINDING A — THE ENTRANT FILES ARE NOT REPRODUCIBLE OBJECTS ON THIS BOX, AND THAT IS NOT THIS CABINET'S TO FIX

**When the checker compared each record's `entrant_digest` with the model file on disk, four cells disagreed
— and re-reading the same paths minutes apart gave a DIFFERENT value every time.** Measured before anything
was written about it:

```
Phi-3.5-mini-instruct-Q4_K_M.gguf   2,393,232,672 B   mtime 2026-01-27   ctime 2026-09-12
    read 1 (page cache)                 599d5b306cac0074
    read 2 (after POSIX_FADV_DONTNEED)  e5e618bc12f1015a      <- a DIFFERENT file per the read path
    read 3 (15 s later, re-cached)      d4f236c238ed325c      <- and different again
Mellum2.1-12B-A2.5B-Thinking-Q4_K_M.gguf   8,071,295,264 B   mtime/ctime 2026-10-12
    three reads, minutes apart: 86b4914a00a68e28, 815560bb45e5c8f7, eccbff7c9e2d8fef
    and 20 s apart in a separate probe: 6661b42163e18345 -> 543b89f2973f087d
and over ten minutes, single-hash readings of the same paths: LFM2 687a31c3 .., OculusMind d86e2dc1 .. then
1ef540cf .., granite c35bc375 .. then 3dedc321 .., Phi-3.5 c3a537e5 .. then 0cab5d42 .., Qwen3-1.7B
b599efde .. then 1163cd8a ..
WHAT DID NOT CHANGE: mtime and ctime (nobody wrote per the metadata), the byte counts, and the two ternary
files, which hashed identically in EVERY reading (5ddb268245634001 / c79fcdfaf6b7bf47).
WHAT IS NOT THE CAUSE: the reader. A 76 KB source file on the same box hashed identically three times in a
row, and the values reproduce across two independent readers (this cabinet's `file_digest` and `sha256sum`).
AND SOMETHING IS WRITING INTO THAT DIRECTORY: a Chromium download in progress sits beside the models
(`Unconfirmed 131991.crdownload`).
```

**WHAT THIS ESTABLISHES, AND WHAT IT DOES NOT.** It establishes that **an `entrant_digest` is a READING AT A
MOMENT, not the identity of a stable artifact** — so cross-run comparisons of entrant digests are not
comparisons of the same object, and 18 of the 22 pre-move records' entrant digests already disagree with the
same paths read now. **It does NOT establish the mechanism** (a device/filesystem-level fault, a write path
that bypasses inode metadata, or a second view of the models mount in another namespace are all consistent
with what was measured here, and this shell cannot measure the earlier run's namespace). **It is reported as
a finding with its scope and handed to Ocho, whose instruments — the population and every cabinet's records —
are all identified by these digests.** The mechanism is the first thing to settle, not the last.

### FINDING B — THE REPLICATION CONTROL REPRODUCES 10 OF 12 CELLS, AND THE TWO THAT FAIL ARE THE TWO WHOSE READING MOVED

`PREREG_mc_field_plain.md` P2 predicted that every cell this field shares with the population run's `plain`
arm reproduces token-for-token (the fix touches no prompt, no cap, no screen and no ceiling). **10 of 12 do;
2 do not, and the scores still agree in both:**

```
Mellum2.1-12B mc_01   now ['1P']                                      then ['1A','1P']    score 1/1 both ways
MiMo-V2.6-9B   mc_02  now ['Let',"Let's","Let's",'Let',"I'll",'Silo']  then ['Let',"Let's",'Let','Let','Silo','Silo']
```

**Both disagreeing cells belong to entrants whose file reading moved between the two runs** (Mellum's file
hashed a4a0393a.. at 11:55 and a different value at 12:14, 12:15, 12:24 and 12:25). That is offered as the
standing explanation **because it is measured**, and it is not offered as a proof: nondeterminism is not
excluded by this run either, and the population's own replication control found this path deterministic.

### PREDICTION P4 IS FALSIFIED, AND THE DIRECTION IS THE HONEST ONE

**P4 said the two `Llama-3.2-3B` cells would be ATTEMPTS again.** They are not: the model **loaded and
played** (`1P` → 1/1 on mc_01; `1.`×6, `unknown` 6, on mc_02), **so the tenancy condition those records
describe had cleared** and two attempts became two measurements. **The archived attempts said what it was —
"the DEVICE has no room — a TENANCY condition, not a model condition" — and this run confirms the sentence
by falsifying the prediction built on top of it.** The field is 22 measured cells, not 20 + 2.

*(And the count in the pre-registration's section 5 was wrong: **five** entrants' `example`-arm records exist
nowhere else, not six — `Qwen3.5-2B` is also a population entrant. The archive's own cell list measured it;
the correction is in the landing note and the sentence was not quietly rewritten.)*

## 5. THE ARM MOVED — WHAT THE FIELD SHOWS, REPORTED AND NOT SCORED

**The two arms, over the SAME 20 cells, re-derived by the frozen simulator from each arm's own tokens** (the
two `Llama-3.2-3B` cells have no archived counterpart, being attempts):

```
                           example (archived)        plain (this run, same 20 cells)
scores, non-zero cells     3 of 20                   7 of 20
fired                      5                         11
passed                     29                        17
unknown                    34                        6
out_of_range               2                         9
malformed                  15                        24
late                       1                         9
tokens IDENTICAL between the arms: 5 of 20 cells      counters differ: 14 of 20
CEILING CAVEAT             5 of 20 paired cells had EVERY turn cut at the ceiling in at least one arm
                           (the field's own 22-cell totals under `plain` are fired 12, passed 17,
                            unknown 12, out_of_range 9, malformed 24, late 9 -- two cells more)
```

**THE DIRECTION IS THE ONE THE POPULATION RUN MEASURED, over a field three times its size and including the
five entrants it never saw**: `unknown` and `fired` move the way BRANCH 1 pre-registered (the population's
six cells: `unknown` 27 → 7, `fired` 2 → 8; this field's eleven entries, 20 paired cells: `unknown` 34 → 6,
`fired` 5 → 11), and the
mechanism is visible at the cell the decision quoted — **`granite-3.3-2b`'s `3W`×4 is gone**: `PASS`×6 on
mc_02, `unknown` 4 → 0.

**AND IT IS NOT A CRITERION, AND NOT A VERDICT.** No criterion is read from it (C1–C3 and the outcome rows
are the population's and this cabinet does not score its own event), the verdict is not re-scored or
re-scoped, **and the comparison is confounded three ways that are stated rather than left to be found**: the
two arms' records were taken under **an earlier driver digest and an earlier declaration digest**, **5 of the
20 pairs carry a ceiling caveat**, and — Finding A — **the two runs did not read the same bytes of the same
model files.** What the section is: the cabinet's own field, measured under the arm it declares, beside the
records it replaced, with the caveats attached.

## 6. WHAT A READER OF THESE RECORDS MUST DO

1. **Read the arm.** A record taken before 2026-10-17 (`example` `ec59f2dc5fd35518`) and one taken after
   (`plain` `d8ee3da099c1a0c2`) are different instruments, and the declaration's own digest moved with them
   (`c7a60f1d6b4e4030` → `2ada03ee2ad1f60b`).
2. **Read the driver digest**, now that the record carries one: `b726188380ce681c` is the driver before this
   card, `4018f0262498eb3e` after it. Everything in this field is the latter.
3. **Treat `entrant_digest` as a reading, not an identity** (Finding A) — it is still recorded on every
   record, and it is still the best available identification of what answered a turn, but two records with
   different values are not thereby different models and two with equal values are not thereby the same bytes.
4. **The coordinates hold the declared arm**, one run, one path, and the records they replaced are archived
   byte-exactly with their digests.

## 7. THE POPULATION VERDICT IS UNTOUCHED, AND THE UPPER TAIL IS STILL OUT

* **C1–C3, the outcome rows, the criteria and the verdict are not re-read, re-scored or re-scoped.**
  `FAILED ON THIS POPULATION` stands as attached to C2 and C3.
* **The upper tail (12–25 GB) was out of the population and stays out.** This field is the cabinet's
  coordinates, not a population rule, and nothing here widens either.
* **`example` is not withdrawn**: it is kept verbatim in the driver, still selectable, and the arm every
  record before this date was taken under — which is exactly what the archive preserves.
* **n = 1 per cell, one state set, counts are the result and rates are the index.**

---

## THE ARTIFACTS OF THIS CARD

```
PREREG_mc_field_plain.md                       the pre-registration, then its landing note (corrections + drift)
probes/MC_FIELD_EXAMPLE_ARM_ARCHIVE_20261017.json   the pre-move field, byte-exact, with digests
probes/MC_<entrant>_<level>.json (22)          THE RUN OF RECORD: the field under `plain`, each with its reason
                                               and the record it replaced
missile_command_run.py                         4018f0262498eb3e -- F1 + F2 + the controls
scripts/check_mc_field_plain.py                the checker: 111 checks, and it can fail
logs/mc-field-check3.out                       its output (109/111 -- the two failures are Findings A and B)
logs/mc-field-plain-<entrant>.out (11)         the guarded units' own output, one per entrant
logs/mc-selftest-fix2.out                      the controls after the fix: ALL CONTROLS PASS 53/53
logs/mc-dryrun-fix.out                         the driver's own report of the arm it read
```
