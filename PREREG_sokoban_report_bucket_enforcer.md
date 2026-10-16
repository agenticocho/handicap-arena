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
