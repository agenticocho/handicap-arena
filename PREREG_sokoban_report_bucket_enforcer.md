# PRE-REGISTRATION — AN ENFORCER FOR THE REPORT'S BUCKET RULE: THE WRITER STILL WRITES `load_failure_class`, AND THE READER STILL READS IT

**Written BEFORE the check exists**, in the house form of `PREREG_sokoban_instrument1/2/3/4.md` and
`PREREG_sokoban_report_field_bucket.md`, and for the same reason: **a check whose firing is not predicted in
advance cannot be distinguished from a check that happens to pass.**

**Card:** `t_36948d45`, FILED BY the Chair on card `t_7d2eb103` (§3(f) of
`PREREG_sokoban_report_field_bucket.md`). **Authority, stated rather than implied: the CARD ITSELF is the
filing, it names the file to be written (`check_report_buckets.py`), and the subject is a check, not a
measurement of the models — so no ruling is requested here.** The one thing this change must NOT do is edit
the two files it checks: §3 disposes of that first.

**Base, measured before this file was written:**

```
main           d275389  (the commit this card branched from; tree clean)
sokoban_report.py  13088 B  sha256 04966f23fcaa91e6326e55f658b7e3fef1462c00fb5d55e856537e46d8b0f8d4
sokoban_run.py     58642 B  sha256 e3f20b3ba561376197ca0cea8dc64ac33a515f7015e99518002314ca02beed62
check_report_buckets.py   DOES NOT EXIST -- the digest of a file that does not exist is not predicted
```

**AND THE SIXTEEN REPO CONTROLS ARE NOT ALL GREEN AT THIS BASE.** Measured, before the check was written:
`make_conformance_package.py` rc 1, `test_no_silent_zero.py` rc 1, `test_declared_root.py` rc 1,
`freeze_check.py` rc 1 (no stockfish binary on this box), `check_format_fields.py` rc 2 (it demands a bundle).
**So "rc-identical" is not the same as "green", and the comparison in §2 P6 is rc AND output-digest, taken in
the SAME tree path before and after**, so a failure that was already there cannot be spent as evidence of
anything.

---

## 0 THE GAP, MEASURED RATHER THAN QUOTED

`sokoban_report.py` buckets a non-loading cell by the field the driver writes, and falls back to a split of the
prose in `why` when the record carries no field. **WHICH RULE FIRED IS PRINTED** — that is what card
`t_7d2eb103` landed.

**AND A FALLBACK IS EXACTLY WHAT MAKES A RENAME SILENT.** Nothing outside `sokoban_report.py` reads
`sokoban_run.py`'s load-failure path. If the writer's key were renamed or dropped:

```
every bucket      -> the PROSE rule
every reason line -> [prose] ...
the report        -> rc 0, one plausible report, over a class the driver decided and no longer publishes
```

**AND THE FILE'S OWN CONTROL DOES NOT COVER IT.** `python3 sokoban_report.py --self-test` exercises the pure
`failure_bucket` function over records built inside the test file. It never touches the writer, never touches
the shape layer, and never reads the writer's field NAME — so it cannot fail for this reason.

---

## 1 WHAT THE CHECK WILL DO — ONE FILE, THREE SUBJECTS, AND A CONTROL

`check_report_buckets.py`, run the way `check_one_reader.py` is run (`python3 check_report_buckets.py` from the
tree, rc 0 on a clean tree, rc 1 on drift):

**E1 — THE WRITER IS READ, NOT COPIED.** The writer's own `load_failure()` is **executed** and the key set it
returns is the key set the check asserts against; the check also asserts that the source SPLATS
`**load_failure(...)` into the record, because a function whose return reaches no record writes nothing. The
reader's source is then read for a `.get(<that key>)`. **A list of the writer's three class VALUES does not
appear in the check** — the check carries the KEY (the contract) and lets the writer own the values; the class
its own fixture carries is **read out of the writer at run time**, so a value the writer changes tomorrow
cannot make this check stale.

**E2 — THE READER IS DRIVEN OVER ONE FIXTURE OF EACH GENERATION.** A record carrying a class, a pre-class
record whose prose contains `" -- "`, and a container of both. The check asserts the printed bucket label, the
`[field]` / `[prose]` tag and the tally line for each. **Fixtures are written by the check itself under its own
`tempfile.mkdtemp()` scratch and removed before it exits** — never into `probes/`, because writing a fixture
into the domain every sweep reads is how a check changes what it measures.

**E3 — IT MUST BE ABLE TO FAIL.** The run carries its own positive control: a COPY of the writer with the key
renamed and a COPY of the reader with the same literal renamed are written into the check's scratch, the SAME
evaluation is run against each, and each MUST fire. **A checker that has only ever been run on a clean tree has
not been tested.**

**E4 — AND IT SAYS WHAT IT IS NOT**, in the run and not only in a comment: not a check on the counters, the
rates, the levels or the models; not a second reader of the record.

---

## 2 THE PREDICTION, RECORDED BEFORE THE CHECK IS WRITTEN

**1. THE CLEAN RUN IS rc 0 AND THE LANDING ADDS ONE EXECUTABLE AND ONE DOCUMENT.** On the tree at the landing
commit: `python3 check_report_buckets.py` rc 0, all three fixtures as predicted, both controls fired.
*Falsifier: rc 1 on a clean tree, or a control that did not fire.*

**2. THE THREE FIXTURES, EACH WITH ITS OWN LABEL AND TAG.** The classifier the check reads is the report's own
two-line form `did not load    <n>   [<rule>] <label>`:
```
a record carrying the class the WRITER returned  ->  [field] that class, VERBATIM, UNCUT
a pre-class record, prose containing " -- "      ->  [prose] the text before " -- ", <= 44 chars
a container of both (read in KEY order)          ->  TWO bucket lines, [field] 1 of 2 and [prose] 1 of 2
```
**AND NO POOLING:** the container must not produce one line with a count of 2. *Falsifier: a label that is not
the class, a tag that is not `field` on the class record or not `prose` on the pre-class record, a truncated
class, two generations merged into one line.*

**3. THE CONTROL FIRES ON BOTH MUTATIONS, IN THE RUN.** The renamed-reader copy and the renamed-writer copy
each produce a non-empty complaint list, and the run prints which of the two fired with the complaint.
*Falsifier: either copy evaluated clean, which would mean the check reads nothing.*

**4. A RENAME OF THE WRITER'S KEY IS THE MUTATION THE CHECK EXISTS FOR.** `check_report_buckets.py --writer
<copy of sokoban_run.py with the key renamed>` exits **1**, and its own first complaint names the rename.
*Falsifier: rc 0 on the renamed writer, or a complaint about something else.*

**5. NO SECOND COPY OF THE VALUES.** The writer's three class strings do not occur in `check_report_buckets.py`
(grepped, and printed in the evidence). The class the fixture carries is the value the writer returned at run
time.
*Falsifier: any of the three values present in the check's source.*

**6. NOTHING ELSE MOVES.** The sixteen controls are rc-identical AND output-digest-identical before and after,
**measured in the same tree path**; `sokoban_report.py` and `sokoban_run.py` are byte-identical before and
after (digests read back); no file under `probes/` or `results/` is created, edited or removed; `git status`
is clean after a run.
*Falsifier: any control's rc or digest moves; either checked file's digest moves; anything appears in
`probes/`; a fixture survives under the tree.*

**7. THE CHECK READS THE FILES, AND DOES NOT OWN THEM.** Its only write is its own scratch; it never opens a
record for writing; the two records it reads live in the evidence root, not in the tree.
*Falsifier: any write outside `tempfile.mkdtemp()`.*

**FALSIFIERS, NAMED SO THE PREDICTION CAN FAIL:** rc 1 on a clean tree; a control that does not fire; a class
printed truncated or replaced by the prose label; a `[field]` tag on a record that carries no class; a `[prose]`
tag on a record that carries one; two generations pooled into one line; a value from the writer's set copied
into the check; a fixture left in `probes/`; either checked file's digest moving.

---

## 3 WHAT IS **NOT** IN THIS CHANGE, DISPOSED OF ONE BY ONE

**(a) NEITHER CHECKED FILE IS EDITED, AND NO RECORD IS EDITED.** `sokoban_report.py` and `sokoban_run.py` are
byte-identical after this change, by digest. **A check that lands by changing the thing it checks has not
checked anything.**

**(b) NO PROBE AND NO RECORD IS WRITTEN INTO THE DOMAIN.** The check's fixtures live under its own scratch and
are removed; `probes/` and `results/` are untouched; the check reads no artifact at all — it manufactures its
own three inputs, which is what makes it runnable anywhere rather than only where a record happens to be.

**(c) IT IS NOT A CHECK ON THE COUNTERS, THE RATES, THE LEVELS OR THE MODELS**, and it is not a second reader
of the record: the report's OUTPUT is parsed, never the record.

**(d) NO PUBLISHED CENSUS OR CONTROLS LIST GAINS A NAME, AND THIS FILE SAYS WHERE A NAME *IS* ADDED.**
`check_report_buckets.py` is added to **no** list inside the tree — there is no in-tree list of checks to add
it to (`check_one_reader.py` appears in none either; grepped). It IS added as a seventeenth command to this
card's OWN evidence-root `controls.py`, where the sixteen live, because an enforcer nothing runs is not an
enforcer. **That is the name added, said out loud here rather than left to be found.**

**(e) IT DOES NOT CLAIM THE REPORT IS NOW ENFORCED END TO END.** It checks one contract — the writer's key
reaching the reader's rule — and the four shapes are covered only by the reader's own `--self-test` and by
card `t_7d2eb103`'s evidence, not here.

---

## 4 THE MEASUREMENT SCALE

No model is loaded, no GPU is used, no server is started, no record is read from the domain. **Evidence lands
at the declared results root, `/home/chilly1/workspace/cabinet_results/t_36948d45/`, outside every git tree.**

---

# LANDED — 2026-10-16. THE PREDICTIONS ABOVE WERE WRITTEN FIRST AND ARE VERIFIED, NOT RESTATED.

**APPENDED, NOT REWRITTEN:** everything above is the pre-registration as it was committed, before the check
existed on disk. This note is added after it, and it is dated.

**THE DIGEST, BEFORE → AFTER:**

```
check_report_buckets.py   DID NOT EXIST
                       -> 18412 B  sha256 f8745f1fa7e2dd5626b222259f11aaa7968cd4e5e3bbca0b86cf94cc175b8867
                          blob 7a9470a57a24d67338bd59846b8d09e010c6a3de
   git hash-object and HEAD:check_report_buckets.py are the SAME object (7a9470a5...), read back.
PREREG (this file)    9742 B  sha256 c0f7a4e89de93339 (full: c0f7a4e89de9333943d43af897762a907068e0c6475825319087401dce3fc532)
                              (commit a31b9f2, the pre-registration as committed)
                       -> THE AFTER DIGEST IS NOT WRITTEN HERE, AND CANNOT BE: a file's digest is a
                          function of the bytes that would have to contain it. It is read out of
                          sha256sum at the landing commit into the evidence root (prereg_after.txt) and
                          repeated in the landing commit's message -- never typed from memory.
commits               a31b9f2 prereg  ->  4b5c6cd check_report_buckets.py  ->  <the commit carrying this
                      note; ITS hash is likewise read back out of `git log` into the evidence root
                      rather than written into the file it names>
                      (prereg FIRST, the check second, this note last; `gcommit -F` from files, so no shell
                       touched a message, and every message read back out of the commit)
```

**A CONCURRENT CARD, SAID OUT LOUD RATHER THAN DISCOVERED LATER.** This tree has another writer. At the time
the pre-registration above was written, `HEAD` was `d275389` and card `t_bba8182e` held four files
MODIFIED-UNCOMMITTED in the same directory; by the time this check was committed, that card's work had
landed (`de80b97` and its predecessors) and these two commits sit ON TOP OF IT. So **"the clean tree at the
landing commit" includes another card's work**, and the control comparison in §2 P6 was therefore run as a
PAIRED experiment rather than before-and-after in time: this card's two files are moved OUT of the tree and
back IN, in the same directory, and the sixteen controls are run in each arm. **One variable.** The four
files of the other card were fingerprinted before and after both arms and were STABLE across them.

**THE CARD'S ACCEPTANCE, ANSWERED WITH THE RUN AND THE TEXT IT COMPARED:**

```
(a) rc 0 AT THE LANDING COMMIT.  `python3 check_report_buckets.py` -> rc 0, run_clean.txt.
      writer  sokoban_run.py: load_failure() returns the key(s) ['load_failure_class', 'why']
      writer  the value it returns is "unknown -- the server's log could not be read"  (READ OUT OF THE
              WRITER, not copied into this file)
      writer  line(s) [735, 752]: the failure record is built with **load_failure(...), so the return
              reaches the record
      reader  line(s) [99]: the reader gets `load_failure_class` out of the record
    AND THE READER, DRIVEN OVER ONE FIXTURE OF EACH GENERATION -- the label, the tag and the tally:
      class.json        did not load  1  [field] unknown -- the server's log could not be read
                        [field] 1 of 1   [prose] 0 of 1     SHAPE cell -- one record
      preclass.json     did not load  1  [prose] PRE: the check's own prose fixture
                        [field] 0 of 1   [prose] 1 of 1     SHAPE cell -- one record
      container.json    did not load  1  [field] unknown -- the server's log could not be read
                        did not load  1  [prose] PRE: the check's own prose fixture
                        [field] 1 of 2   [prose] 1 of 2     SHAPE container of 2 named cell record(s)
    (b) THE CONTROL, IN THE SAME RUN, AND IT FIRED ON BOTH SIDES:
      reader copy  CONTROL_reader_literal_renamed.py   (4 literal(s) renamed)  -> complaints 7   FIRED
      writer copy  CONTROL_writer_key_renamed.py       (4 literal(s) renamed)  -> complaints 1   FIRED
    (c) THE EVIDENCE ROOT AND ITS DIGESTS, ALL READ BACK RATHER THAN TYPED: every digest in this note
        comes out of `sha256sum`, `git hash-object`, `git rev-parse <commit>:<path>` and the check's own
        printed output, taken at the landing commit. Evidence root:
        /home/chilly1/workspace/cabinet_results/t_36948d45/ (outside every git tree).
    (d) A RENAME OF THE WRITER'S KEY MAKES IT FAIL. The mutation is applied to a COPY in the evidence root,
        never to the tree's own file -- MUTANT_writer_key_renamed.py, 4 occurrences of the key renamed,
        sha256 df0dd04173c4d58ea3516b4959b42d7006ba819bd9f78829586f47be71bcbea5 -- and the check run against
        it exits 1, its own first complaint being:
          THE WRITER NO LONGER PUTS `load_failure_class` INTO ITS LOAD-FAILURE RECORD -- load_failure()
          returns ['load_failure_class_RENAMED_BY_THE_CONTROL', 'why']. Every bucket would take the PROSE
          rule, every reason line would read `[prose] ...`, and THE REPORT WOULD STILL EXIT 0. This is the
          rename the check exists for.
        (run_mut_writer.txt; the reader-literal mutant MUTANT_reader_literal_renamed.py, sha256
         f2b7da4711d3132ce096dfe6ec0bc6e2f03ef048ded83f42036d262f72559c0f, is rc 1 too, run_mut_reader.txt,
         and both run files sit beside run_clean.txt.)
```

**PREDICTIONS 1–7, EACH VERIFIED AGAINST AN ARM RATHER THAN RESTATED:**

```
1  clean rc 0, one executable + one document   VERIFIED -- rc 0; git diff --stat of the two commits is
                                               two files, 157 + 346 insertions, no other file touched.
2  the three fixtures, label + tag + tally      VERIFIED -- the block above, read out of the report's own
                                               `did not load ... [rule] label` and `[rule] N of M` lines.
3  the control fires on BOTH mutations          VERIFIED -- 7 and 1 complaints, in the clean run itself.
4  the writer's key renamed -> rc 1             VERIFIED -- (d) above, complaint quoted verbatim.
5  no second copy of the values                 VERIFIED -- no_values_copied.py reads the writer's THREE
                                               dict literals out of sokoban_run.py and finds all three
                                               ABSENT from the check, while the KEY is present in the check
                                               and in the reader; rc 0.
6  nothing else moves                           VERIFIED -- the paired run: 13 of 16 rc AND
                                               output-digest identical; the 3 that moved are disposed of by
                                               name below, and sokoban_report.py and sokoban_run.py carry
                                               their base digests unchanged (04966f23... / e3f20b3b...).
7  the check reads and does not own             VERIFIED -- its only write is tempfile.mkdtemp(), removed
                                               on exit; probes/ and results/ untouched (git status).
```

**THE THREE CONTROLS THE PAIRED RUN MOVED, EACH DISPOSED OF BY NAME — NOT BY RE-RUNNING UNTIL THE DIGESTS
AGREED:**

```
check_one_reader.py    rc 0 BOTH ARMS. Diffed line by line, the ONLY moved line is its own count:
                           files scanned      90        ->        files scanned      91
                       MY FILE IS SCANNED BY IT. No complaint is added; the count is the check's own
                       denominator. This is the movement a new check is SUPPOSED to cause, said out loud.
sokoban_solver.py      rc 0 BOTH ARMS. The only moved text is two TIMINGS --
                           02_two_boxes: ... 0.0013s -> 0.0017s
                           S1_built_solvable: ... 0.0054s -> 0.0050s
                       and the SAME command on the UNCHANGED tree three times gives three digests
                       (0365e2261cb4be33 / 3f0f29d71430d836 / 46d66dc2797955c3). NOT DETERMINISTIC: not
                       evidence about any file.
test_no_silent_zero.py rc 1 BOTH ARMS (it fails on the records as they stand, which is its written
                       purpose), and in the disposal run the two arms are BYTE-IDENTICAL. The paired-run
                       movement is a COUNT OF THIS CARD'S OWN EVIDENCE ROOT, demonstrated rather than
                       argued: adding ONE json file to it moves exactly one line, and removing it restores
                       the digest exactly --
                           scope  live:t_36948d45     7 *.json  ->  8 *.json
                       (dispose_no_silent_zero.py, 48a564efbefef9fe -> 77e31933cef8e70d -> 48a564efbefef9fe)
```

**AND THREE THINGS THIS MEASUREMENT GOT WRONG OR DID NOT EXPECT, RECORDED RATHER THAN TIDIED:**

```
(i)  THE FIRST VERSION OF THE CHECK PRINTED ITS TALLY MISMATCH AS A PYTHON TUPLE -- `got `[field]
     (0, 1)``. The mutation had fired, the finding was right, and the SENTENCE A HUMAN READS was wrong:
     it named the defect in a form that cannot be compared to the tally it disagrees with. Fixed to
     `got `[field] 0 of 1`` BEFORE the landing commit, and every run file kept in evidence is from the
     landed file (sha256 f8745f1f...).
(ii) I PREDICTED THE CONTROL COMPARISON COULD BE RUN BEFORE-AND-AFTER IN TIME. It cannot in a shared tree
     with a concurrent writer, and the first attempt (controls_pre.json against controls_after.json)
     differed in two variables at once. It is recorded here as the wrong instrument, not deleted, and the
     paired arm moving two files in and out of ONE directory is what replaced it.
(iii) A CHECK THAT COUNTS FILES IN ITS OWN EVIDENCE ROOT MOVES THE CONTROLS THAT COUNT THAT DIRECTORY.
     That is not a defect of this check -- it is the same residue card t_7d2eb103 disposed of -- but it
     means the number of json files in cabinet_results/t_36948d45/ is now part of two controls' output,
     and the next card that touches this tree should expect it.
```

**AND TWO THINGS THIS LANDING DOES NOT CLAIM.** It does not claim the report is enforced end to end: one
contract is checked -- the writer's key reaching the reader's rule -- and the four input shapes rest on the
reader's own `--self-test` plus card `t_7d2eb103`'s evidence, not here. And it does not claim the check
would have caught a rename that was ACCOMPANIED by a matching edit on the reader's side: it reads one key
against one key, which is exactly the contract §1 E1 names and exactly the whole of it.

**WHERE THE NAME IS ADDED, SAID RATHER THAN LEFT TO BE FOUND:** `check_report_buckets.py` is added to NO list
inside the tree -- there is no in-tree list of checks (`check_one_reader.py` is in none either). It is added
as a **seventeenth command to this card's own evidence-root `controls.py`** (`python3 check_report_buckets.py`),
where the sixteen live, because an enforcer nothing runs is not an enforcer.
