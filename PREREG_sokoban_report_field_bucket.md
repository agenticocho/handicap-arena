# PRE-REGISTRATION — SOKOBAN REPORT: BUCKET A LOAD FAILURE BY `load_failure_class`, NOT BY SPLITTING THE PROSE IN `why`

**Written BEFORE the code change**, in the house form of `PREREG_sokoban_instrument1/2/3/4.md`, and for the
same reason: **a fix whose effect is not predicted in advance cannot distinguish a repaired reader from a
luckier sample.**

**Card:** `t_7d2eb103`, FILED BY the Chair's ruling 3 on card `t_8dc430a7` (`DECISION_four_dispositions_of_
instrument_3.md`, main `53506be` / `cabinet/sokoban` `e5c202d`). **Authority, stated rather than implied:
the CARD ITSELF is the Chair's filing, it names this file as the subject, and `sokoban_report.py` is my own
reader — so no ruling is requested here. The one thing this change must NOT do is pretend to be the
instrument change that instrument 4 pre-registered; that is disposed of in §3.**

**Pre-image, measured at the commit this prereg is written against:**

```
sokoban_report.py   4155 B   sha256 59ff2408f163adbd28ad8f1f7c54005b45e90be15d7dee00b590d14318c04d3d
                    commit d238d03 (the file's only commit), working tree clean at 53506be, main
```

**AND IT IS IN NO PINNED SET.** `FROZEN_DIGESTS` (`sokoban_solver.py:97`) names `sokoban.py` and the three
level files and nothing else, and no other digest of `sokoban_report.py` is asserted anywhere in the tree
(grepped: the only three mentions of the filename outside `.worktrees` are prose in `PREREG_sokoban_
instrument4.md`, `DECISION_four_dispositions_of_instrument_3.md` and `FINDINGS/018`, all of them ABOUT the
file and none of them carrying a digest). **The new digest is not predicted and cannot be** — a digest is a
function of bytes that do not exist until the commit is made; it is recorded in the landing note appended to
this file after the commit exists.

---

## 0 THE DEFECT, MEASURED RATHER THAN QUOTED

**THE PRE-IMAGE RULE, READ OUT OF THE FILE** (`sokoban_report.py:69`, in the reason-count block):

```
k = (r.get("why") or "unknown").split(" -- ")[0][:44]
```

**A BUCKET IS A CLAIM ABOUT WHICH CONDITION A CELL FELL INTO, AND THIS ONE IS A SPLIT OF PROSE.** The record
now carries the condition the driver actually decided, as a FIELD:

```
sokoban_run.py:303   "load_failure_class": "the binary refused the FILE (the log names the cause)"
sokoban_run.py:312   "load_failure_class": "unknown -- the server's log could not be read"
sokoban_run.py:317   "load_failure_class": "no cause named by the log: the card at failure is what is reported"
```

**AND IN ONE OF THE THREE CASES THE PROSE CONTAINS `" -- "` INSIDE THE SENTENCE** (`sokoban_run.py:305`:
`THE BINARY REFUSED THE FILE -- log line {n}, quoted verbatim: …`), so the split stops landing on a sentence
boundary and lands inside one. **MEASURED, pre-image tree, on the instrument-4 record** (`s2_pair.json`'s
`new` member, wrapped as a one-cell run — §4 says why it has to be wrapped):

```
    did not load    1   server exited rc=1.
THE BINARY REFUSED THE F
```

**AND THE PRE-IMAGE READER CANNOT READ THE TWO RECORDS THE ACCEPTANCE NAMES AT ALL.** MEASURED, pre-image
tree, on `s2_pair.json` verbatim and on each of its two members bare: **rc 1, stdout EMPTY, and the last
stderr line is `AttributeError: 'str' object has no attribute 'get'`** — a bare cell record is a dict with no
`"cells"` key, so the row selector returns the dict itself and the reader calls `.get` on its KEYS. That is a
pre-existing shape limitation, not this change's doing (the parent card measured it and left it, correctly,
because the report's shape was not its subject). **It is disposed of here rather than around: §1 S2, and it is
not optional, because THE ACCEPTANCE NAMES TWO INPUTS THAT ARE BARE RECORDS.**

---

## 1 WHAT CHANGES — ONE FILE, THREE SUBJECTS

### S1 — THE BUCKET READS THE FIELD; THE PROSE SPLIT BECOMES THE FALLBACK, AND WHICH ONE FIRED IS PRINTED

```
load_failure_class present and non-blank  ->  the bucket IS the field, printed VERBATIM, rule = FIELD
load_failure_class absent / blank / not a string  ->  the pre-image split, rule = PROSE
```

**THE CLASS IS NOT ENUMERATED IN THE READER, DELIBERATELY.** A list of the three values in the report would be
a SECOND DEFINITION of a set the writer owns — the same defect shape as a census that lists fields the record
does not carry (that is the open follow-up `t_bba8182e`, and this file is not going to create a small copy of
it). The field is printed as it stands, so a fourth class the driver adds tomorrow is REPORTED rather than
folded into "unknown".

**THE 44-CHARACTER CUT STAYS ON THE PROSE AND IS NOT APPLIED TO THE CLASS.** The cut is the fallback's own
display compromise over prose of unknown length; a class is a label with an authored meaning, and a truncated
one is a reader's defect in a new place.

**AND THE RULE IS PRINTED BESIDE EVERY BUCKET, in the bucket line itself and in a tally under it.** The card's
own sentence is the requirement: *a report that silently changes buckets between record generations is two
reports.* **So a bucket is keyed by `(rule, label)` and not by `label` alone** — two generations cannot be
pooled into one line even if their labels happened to read the same.

### S2 — THE READER READS THE SHAPES THE ACCEPTANCE HANDS IT, AND REFUSES WHAT IT DOES NOT READ

Exactly four shapes, named in the output on a `source … SHAPE …` line, none of them guessing:

```
run        a dict with "cells"                      <- unchanged, the pre-image path
list       a bare list of cell records              <- unchanged, the pre-image path
cell       ONE cell record (a dict with level, and loaded or why)
container  a dict whose every non-underscore value is a cell record, e.g. {"pre": …, "new": …}, in KEY order
anything else -> rc 1 with a one-line refusal naming what was found. A TRACEBACK IS NOT A READING.
```

**THIS IS ADDITIVE AND MOVES NO ARITHMETIC**: `run` and `list` take the identical code path they took before,
and `cell`/`container` only add INPUTS. The proof is not the argument, it is the measurement in §2 P1/P2: on
the run of record the counter block and the per-level fractions are byte-identical between the two trees.

### S3 — THE RULE CARRIES ITS OWN CONTROL: `python3 sokoban_report.py --self-test`

A rule with no control is a rule nobody can falsify, so the shipped file carries a pure self-test over
`failure_bucket` covering the two generations and the three edges that decide between them: **field present
AND the prose containing `" -- "` (the field must win), a blank class, a class that is not a string, a
pre-instrument-4 record (fallback, cut at 44), and neither carrier (the pre-image's `"unknown"` kept).**
**AND THE CONTROL IS MEASURED AGAINST A BROKEN COPY OF THE RULE (§2 P9): a self-test that has only ever been
run against a working function is a self-test for one afternoon.**

---

## 2 THE PREDICTION, RECORDED BEFORE THE CODE CHANGE

**1. THE RUN OF RECORD'S NUMBERS DO NOT MOVE.** On `probes/SOKOBAN_RUN_20261010-072252.json` (216011 B, sha256
`05084c8e7ca9ed94c5a82ed62917ecb8b6e2e1f9667a04953591d66a38a1d447`, 15 cells / 12 played / 3 did not load / 3
levels): **rc 0**, and the `cells … PLAYED … DID NOT LOAD …` line, EVERY per-cell counter row, EVERY per-level
sum row and EVERY per-level fraction are **byte-identical** to the pre-image report's on the same bytes.
*Falsifier: one counter digit or one fraction digit differs.*

**2. THE REASON BLOCK ON THE RUN OF RECORD KEEPS ITS LABELS AND ITS COUNTS, AND ONLY ADDS THE RULE.** Same
three cells, still one bucket, label still `server exited rc=1` (all three are pre-instrument-4: no class in
any of them, measured — `{(why, load_failure_class)}` over the non-loading rows is the single pair
`('server exited rc=1', None)`), count still 3, and the tally under it reads **field 0 / prose 3**.
*Falsifier: the label differs from the pre-image's, the count differs, or a bucket is labelled `field` on a
record that carries no class.*

**3. (b) THE INSTRUMENT-4 RECORD BUCKETS BY THE FIELD, VERBATIM.** On `s2_new.json` (the `new` member of
`s2_pair.json`, extracted unchanged and compared back to it): the bucket label IS `the binary refused the
FILE (the log names the cause)` CHARACTER FOR CHARACTER, the rule printed is `field`, and the prose fragment
the pre-image printed (`server exited rc=1.` + newline + `THE BINARY REFUSED THE F`) appears NOWHERE as the
bucket. *Falsifier: the bucket is the prose fragment, the rule says `prose`, or the class is truncated.*

**4. (b) PAIRED, ON THE SAME BYTES: THE TWO TREES DISAGREE, AND THEY DISAGREE IN THE NAMED DIRECTION.** On the
one-cell wrapper `s2_new_run.json` (both trees can read it, so this is the only paired form available for a
bare record): pre-image bucket `server exited rc=1.\nTHE BINARY REFUSED THE F` (rule: prose, and the tree
prints no rule at all), new bucket the class (rule: field). **A paired arm whose result is the same on both
trees would mean the field was not read.** *Falsifier: the two trees print the same label for this input.*

**5. (c) THE PRE-INSTRUMENT-4 RECORD STILL BUCKETS BY THE PROSE, AND NOW SAYS SO.** On `s2_pre.json` (the
`pre` member, extracted unchanged): the bucket label is EXACTLY the pre-image label
`server exited rc=1.\n  AND THE CARD IS HELD B` (44 characters, measured pre-image on the wrapper
`s2_pre_run.json`), the rule printed is `prose`, and no class is claimed. *Falsifier: a class appears for this
record, or the label differs from the pre-image's.*

**6. NO SILENT POOLING ACROSS GENERATIONS.** On `s2_pair.json` VERBATIM, at the path the card names: ONE report,
TWO bucket lines, one per generation, each carrying its own rule, and the tally reads field 1 / prose 1.
*Falsifier: one line with a count of 2.*

**7. THE FALLBACK IS NOT DEAD CODE (CONTROL).** The instrument-4 record with `load_failure_class` REMOVED
(`s2_new_noclass_run.json`) falls back to the prose rule, prints `prose`, and its label equals the pre-image
tree's label on that input — and the pre-image tree's label on that control is BYTE-IDENTICAL to its label on
the un-removed record (measured pre-image: both `2a988c4a9168e3d2`, because the pre-image reader ignores the
field entirely). *Falsifier: the control still buckets by `field`, or its label differs from the pre-image's.*

**8. THE REFUSAL IS A MESSAGE, NOT A TRACEBACK (CONTROL).** `not_a_record_run.json` (a dict whose values are
not cell records): rc 1, stdout carrying a one-line refusal that names what was found, and **no
`AttributeError` / no traceback on stderr**. *Falsifier: a traceback, or rc 0.*

**9. THE SELF-TEST CAN FAIL.** `--self-test` exits 0 on the shipped rule and **exits 1 on a copy of the file
whose preference is INVERTED (prose first)** — the mutation is applied to a copy in the evidence directory,
never in the tree. *Falsifier: the self-test passes the inverted copy, which would mean it tests nothing.*

**10. NOTHING ELSE MOVES.** The repo's sixteen controls (the same list `controls.py` ran for card
`t_8dc430a7`) are **rc-identical before and after**; no pinned digest moves; no published number, rate,
criterion, level file, probe artifact or record on disk is edited; `sokoban_run.py`, `vram_holder.py` and
`sokoban.py` are byte-identical after the change.
*Falsifier: any control's rc changes; any file other than `sokoban_report.py` and this prereg's own
landing note differs; the report raises on any input above.*

**FALSIFIERS, NAMED SO THE PREDICTION CAN FAIL:** the report raising on the run of record; a counter or a
fraction moving; a bucket labelled `field` on a record with no class; a bucket labelled `prose` on a record
that carries one; a class printed truncated; two generations merged into one line; the fallback never firing;
the refusal printing a traceback instead of a sentence; the self-test passing a rule with the preference
inverted.

---

## 3 WHAT IS **NOT** IN THIS CHANGE, DISPOSED OF ONE BY ONE

**(a) IT IS NOT A REVISION OF INSTRUMENT 4'S PREREG.** `PREREG_sokoban_instrument4.md` prediction 7 read *"the
report still runs and still buckets by it"* — TRUE OF THE PRE-IMAGE READER, and the follow-up was NAMED IN
THE SAME FILE (`§(iii)`, and the decision document's follow-up 2) rather than discovered later. **This card IS
that follow-up, it is a different file's rule at a different time, and it says so here rather than quietly
adding to a file that was pre-registered without it.** Instrument 4's record, prose, driver and carriers are
untouched.

**(b) NO RECORD IS EDITED, AND NO PROBE IS COMMITTED.** The two records the parent card wrote live in the
evidence root, outside every git tree, for the reason it gave; this card adds none and edits none. The report
READS records; it does not own any.

**(c) THE COUNTERS, THE RATES, THE FRACTIONS AND THE PER-CELL BLOCK ARE NOT TOUCHED.** The reason block and one
new `source … SHAPE …` header line are the whole visible change; the arithmetic code is not edited at all.

**(d) THE `why` PROSE IS NOT REWRITTEN, NOT SHORTENED AND NOT MOVED.** The fallback still splits it, exactly as
before, for the records that have nothing else to read.

**(e) `sokoban_report.py` DOES NOT GAIN A SCORER.** It reports; it does not decide. A field it cannot read is
printed as it stands rather than repaired, and a label it produced is always accompanied by the rule that
produced it.

**(f) NO ENFORCER IS ADDED FOR THE WHOLE REPORT.** There is no check that runs this reader in CI, and this
change does not pretend to be one: the controls here are the two in S3 and the sixteen in §2 P10. An enforcer
that runs the report against a fixture record of each generation is a defensible follow-up and is NOT claimed
here.

**IT IS NOT A CLAIM ABOUT THE MODELS.** Nothing here says what any entrant can do; no probe, population,
prereg, freeze record, grammar, declaration or level is edited.

---

## 4 THE MEASUREMENT SCALE

**THE WRAPPER, AND WHY IT IS NOT A DODGE.** The pre-image reader cannot read a bare cell record (§0), so the
only PAIRED before/after form available for (b) and (c) is a one-cell run. `wrap.py` writes
`{"cells": [<row>]}` — the row inserted unchanged, no field added, no field touched, and the wrapped cell is
re-read and compared back to the record it wraps (json-canonical equality, measured, not asserted). **The
paired arms are the SAME BYTES on both trees; the only difference is the reader.** The named artifacts
(`s2_pair.json` and its two members) are ALSO run directly, new tree only — and the pre-image tree's rc 1 on
them is recorded as the pre-image behaviour it is.

No arm below changes a published number. No model is loaded, no GPU is used, no server is started. **Evidence
lands at the declared results root, `/home/chilly1/workspace/cabinet_results/t_7d2eb103/`, outside every git
tree.**

---

# LANDED — 2026-10-16. THE PREDICTIONS ABOVE WERE WRITTEN FIRST AND ARE VERIFIED, NOT RESTATED.

**APPENDED, NOT REWRITTEN:** everything above is the pre-registration as it was committed, before the code
change. This note is added after it, and it is dated.

**THE DIGEST, BEFORE → AFTER:**

```
sokoban_report.py   4155 B  sha256 59ff2408f163adbd28ad8f1f7c54005b45e90be15d7dee00b590d14318c04d3d
                -> 13088 B  sha256 04966f23fcaa91e6326e55f658b7e3fef1462c00fb5d55e856537e46d8b0f8d4
   commit 1886d04, ordered AFTER this file's commit bef4602 and AFTER nothing else
      S1 the bucket reads the field, the prose split is the named fallback, the rule is printed
      S2 the four shapes, named in the output, and a refusal with a sentence for anything else
      S3 --self-test, five cases, measured against an inverted copy of the rule
   git hash-object and HEAD:sokoban_report.py are the SAME object (1a1cb99c7d49e0412dd44a358af9e8baec89967e),
   and the matrix below was run against the file whose sha256 is that digest -- read back, not assumed.
```

**THE CARD'S ACCEPTANCE, ANSWERED WITH THE MEASURED BUCKET AND THE RULE FOR EACH:**

```
(a) the run of record, probes/SOKOBAN_RUN_20261010-072252.json (216011 B,
    05084c8e7ca9ed94c5a82ed62917ecb8b6e2e1f9667a04953591d66a38a1d447, 15 cells / 12 played / 3 no-load)
      rc 0 on both trees; counts line BYTE-IDENTICAL.
      did not load    3   [prose] server exited rc=1          <- pre-image: the same label, no rule tag
      [field]  0 of 3 / [prose]  3 of 3   -- all three records predate instrument 4; not one carries a class.
      COUNTERS AND FRACTIONS: identical, and identical as BLOBS -- PER CELL 18 lines sha 2faf6060c0602275,
      PER LEVEL 6 lines sha 54793cb15a4771f5, the PER-LEVEL FRACTIONS 5 lines sha 88a6b3192c626384,
      HEAD-READ 13 lines sha 56a93ea7617952c3, on both trees.
(b) the instrument-4 load-failure record, cabinet_results/t_8dc430a7/s2_pair.json `new` (bare,
    sha256 d4c11d295ccd4644567af1346db1c68fac745f811dfc76f691da65cd5dfaf03b)
      did not load    1   [field] the binary refused the FILE (the log names the cause)
      THE CLASS, VERBATIM, UNCUT; the prose fragment appears nowhere as the bucket.
(c) a pre-instrument-4 failure record, the same pair's `pre`
    (bare, sha256 48b2b75fbcb51288ea6da73b43732b7e26cc4385dd69662b9755910c23bb3ce0)
      did not load    1   [prose] server exited rc=1.
      AND THE CARD IS HELD B                     <- EXACTLY the pre-image label on the same bytes
      (a) and (c) print the label they always printed, plus the rule; (b) is the one that MOVES, and it moves
      to the field.
PAIRED, on the same bytes as a one-cell run (both trees can read the wrapper, neither can read the bare
record -- see (iii)):
      (b) wrapper  pre-image: server exited rc=1.\nTHE BINARY REFUSED THE F   |   new: [field] the class
      (c) wrapper  pre-image: server exited rc=1.\n  AND THE CARD IS HELD B    |   new: [prose] the same label
      and the field-REMOVED copy of (b): pre-image and new both print the PROSE label above, the pre-image
      with the SAME recorded stdout sha as the un-removed record (2a988c4a9168e3d2) -- which is what a rule
      that ignores the field looks like from inside.
```

**PREDICTIONS 1–10, EACH VERIFIED AGAINST AN ARM RATHER THAN RESTATED:**

```
1  (a) unmoved                              VERIFIED -- blobs above; 6 of 6 compared sections identical.
2  (a) labels/counts kept, rule added        VERIFIED -- (3, 'server exited rc=1') on both; tally 0/3, 3/3.
3  (b) the bucket IS the class              VERIFIED -- character for character, uncut.
4  (b) the two trees DISAGREE               VERIFIED -- prose fragment vs the class, same bytes.
5  (c) the fallback, label unchanged        VERIFIED -- 44 chars, indentation and all.
6  no silent pooling                        VERIFIED -- s2_pair.json verbatim: two lines, field 1 of 2,
                                              prose 1 of 2, one container read in KEY order.
7  the fallback is not dead code            VERIFIED -- class removed -> prose, and the pre-image cannot
                                              tell that copy from the record it came from (same sha).
8  a refusal is a sentence, not a traceback VERIFIED -- rc 1, four lines, empty stderr, on a dict of
                                              non-records; pre-image answered the same input with a traceback.
9  the self-test can fail                   VERIFIED -- shipped rc 0 (5 cases as predicted), the copy with the
                                              preference INVERTED rc 1, first failure named.
10 nothing else moves                       VERIFIED -- 16/16 controls rc-identical; the two trees differ in
                                              ONE file (git diff --stat bef4602 1886d04: sokoban_report.py,
                                              160 insertions / 5 deletions); FROZEN_DIGESTS untouched;
                                              sokoban_run.py, vram_holder.py and sokoban.py byte-identical.
```

**AND THREE THINGS THIS MEASUREMENT GOT WRONG ON THE WAY, RECORDED RATHER THAN TIDIED:**

```
(i)  THE ACCEPTANCE COMPARISON READ A LABEL AS ITS FIRST PHYSICAL LINE. A bucket label can span lines (the
     pre-image prose is multi-line and its continuation is INDENTED, like every report line), so the first
     version of `bucket_entries` cut one label at its newline. THE CHECKS THAT COMPARED THE TWO PARSERS
     PASSED ON THE TRUNCATED FRAGMENT -- two parsings by the same broken parser cannot disagree -- and it was
     the comparison against the 44-character label WRITTEN DOWN IN THIS FILE, read out of the raw output,
     that failed and exposed it. Fixed by bounding the block first (from `played` to the rule tally or
     `(A POPULATION`); the function's docstring now records it.
(ii) MY FIRST DISPOSAL OF THE SIXTEEN CONTROLS UNDERSTATED NOTHING AND MY SECOND OVERSTATED IT. Normalising
     only the literal worktree path left 5 of 5 movements labelled SUBSTANTIVE, because these checks DERIVE a
     cabinet name and a results root from the worktree leaf (PREBRANCH_7d2eb103 vs ocho_arena) and count the
     *.json in their own cabinet directory. Disposed of by normalising the derived names, the count, and the
     line order those names imply -- and the residue after that is ONE solver TIMING and nothing else. Every
     moved byte is named in controls_verdict.txt.
(iii) THE PRE-IMAGE READER CANNOT READ EITHER RECORD THE ACCEPTANCE NAMES, so the paired arms had to be
     one-cell runs. That is not a workaround, it is the second subject of this change: rc 1, empty stdout,
     `AttributeError: 'str' object has no attribute 'get'` on s2_pair.json and on both members, recorded in
     matrix_preimage.json; the new tree reads all three, rc 0.
```

**THE EVIDENCE, AT THE DECLARED RESULTS ROOT** (`/home/chilly1/workspace/cabinet_results/t_7d2eb103/`,
outside every git tree): `wrap.py` + `wrap_out.json` (the records extracted and compared back, the wrappers,
the class-removed control, the non-record control, with every digest), `run_matrix.py` + `matrix_preimage.json`
+ `matrix_new.json` + `out_*.txt` (rc, full stdout, its sha256, stderr, input sha256, per input per tree),
`compare.py` + `compare_out.txt` + `compare_out.json` + `diff_a_run_of_record.txt` (the 15 checks, each with
the text it compared), `mutate_and_test.py` + `mutate_out.json` + `selftest_shipped.txt` +
`selftest_inverted.txt`, `sokoban_report_INVERTED.py` (outside the tree, never committed), `controls.py` +
`controls_pre.json` + `controls_new.json`, `diff_controls.py` + `diff_controls_out.txt` +
`diffctl_*.txt` (the five moved outputs, diffed), `controls_verdict.py` + `controls_verdict.txt`,
`not_a_record_run.json`, `s2_new.json`, `s2_pre.json`, `s2_*_run.json`.

**AND TWO THINGS THIS LANDING DOES NOT CLAIM.** It does not claim the report's shapes are now complete: a
record shape nobody has written yet will be refused by name, which is the correct failure and not coverage.
And it does not claim an enforcer: nothing runs `sokoban_report.py` in CI, so the controls above are the
sixteen repo checks plus the file's own `--self-test`, and §3(f) says so rather than leaving it to be found.
