# DECISION — THE FOUR DISPOSITIONS OF INSTRUMENT 3, AND THE ONE OF THEM THE CHAIR MOVED HIMSELF

**Chair's ruling. Card `t_8dc430a7`. Filed 2026-10-16.** The card's own words: *"Four things it measured on the
way in and deliberately did NOT land. Each is a decision rather than a chore."* **Four rulings follow, one per
item, in the card's order; the first is the only one that needed code, and it is landed.** Ocho's landing note on
card `t_33042da0` named the first as *"the Chair's to move and not mine"* — it is the Chair's, and it moved.

**Two of the four are landed here, and two are landed as carriers rather than as code.** Every ruling below
states what was landed, what it cost, and what was deliberately left undone. **Nothing here re-scores a cell, and
no published number moves.**

---

## RULING 1 — THE ARTIFACT PATH: FLIP, AND WIDER THAN THE CARD PROPOSED. LANDED AS INSTRUMENT 4.

**THE MEASUREMENT (the card's, reproduced here rather than restated):** two runs of the pre-image driver on one
`(entrant, level)` pair, different binaries, wrote **one artifact path and one log path**; the first run's record
is gone and its log was overwritten with it. **No field can close it** — the record that would carry the field is
the record that gets overwritten.

**RULED: A RUN REFUSES TO WRITE OVER A RECORD IT DID NOT TAKE — AT ADMISSION, WITH A REASON-CARRYING OVERRIDE.**
Landed in `sokoban_run.py` (commit `c015995`), pre-registered in `PREREG_sokoban_instrument4.md`
(**S1**, filed as `c6cd542` before the code). Three things were decided beyond the card's one-liner, each for a
measured reason:

```
THE GATE IS AT ADMISSION, NOT AT THE WRITE. A refusal that costs a whole model load is a report filed
afterwards; the tree already carries this rule ("a refusal must consume nothing"). It also closes the LOG axis
with no change to the log's name, and the name is NOT MOVED: probes/SOKOBAN_<entrant>_<level>.json is cited in
GAMES.md and in this package's census, so the fix is a refusal rather than a rename.

IT REFUSES ON ANY EXISTING RECORD, NOT ONLY ON A DIFFERING server_binary_digest. (a) a pre-image record
carries NO digest to compare -- MEASURED at this tip: both committed Bonsai artifacts carry no
server_binary_digest, and one of them is the record the last card's acceptance run destroyed; the narrower
gate would not have protected it. (b) the artifact NAME never carried the legend or the reasoning arm either
(only the LOG name did), so a same-binary arm swap would still delete arm A. (c) the same instrument twice is
not the same record: MEASURED on the 2B Bonsai, 0 and 64 tokens on two runs of one binary.

THE ESCAPE HATCH CARRIES A REASON RATHER THAN A FORCE. --overwrite-artifact "<why>", and the reason lands in
the record that does the replacing, beside the replaced record's sha256, bytes, mtime and the identity it
carried. A bare --force is refused by this tree's own standard (run_card.py: "a gate with an override that is
not written down is a gate nobody can audit"). An empty reason exits 2 and writes nothing.
```

**COST OF THE FLIP, AS THE CARD ASKED FOR IT, STATED HONESTLY AND LARGER THAN THE CARD'S VERSION:** every
deliberate re-measure of an occupied cell now needs one token **and a sentence**. The refusal is not a warning,
so a re-run that a reader might consider routine now stops and asks. **That is the price of FINDING 020's rule
("a run must OWN its artifact path") being applied where the last fix did not reach it**, and it was accepted
because the alternative is silent destruction of the one record the change exists to make legible.

**COST OF NOT FLIPPING, MEASURED ANEW HERE RATHER THAN QUOTED** (`arm2_18_preimage_overwrite.json`): the pre-image
driver, run a second time on a live path in the same cell, exits **0** and replaces the record — `before
bb07f620d37a9246…` → `after 519007ccc634ce70…`, no refusal, no exit code, nothing in the console.

**NOT DONE, AND NAMED:** the gate protects the CLI path only. `sokoban_batch.py`, `sokoban_repeat.py` and the
two A/B drivers write their OWN paths (measured) and call `run()` in-process, so they are unaffected — which is
also why none of them suppresses the defect: **they never wrote the colliding path.** No follow-up is filed for
them because there is nothing measured to file.

---

## RULING 2 — THE FALSE SENTENCE BESIDE THE TWO BONSAI ARTIFACTS: A CORRECTION RECORD **BESIDE THE NOTE**. LANDED.

**THE QUESTION THE CARD ASKED:** *"the only open question is whether the Chair wants a correction record beside
them … or whether the card thread is enough."*

**RULED: A CORRECTION RECORD, AND IT GOES BESIDE THE NOTE — NOT AT THE ROOT.** Landed as
`probes/SOKOBAN_Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0_01_one_push.CORRECTION.md` and `…_02_two_boxes.CORRECTION.md`.

**WHY NOT THE ROOT, WHEN THE TREE'S `CORRECTION_*.md` CONVENTION IS AT THE ROOT:** the root form is for a claim
that is read from the root. **This note's own last line tells the reader where to read: *"READ THE INSTRUMENT
NOTE BESIDE EACH ARTIFACT BEFORE CITING EITHER."*** A correction filed at the root would be filed **where the
reader is not going**, and the card thread is a carrier nobody citing an artifact reads. The reader arrives via
the note, so the correction sits where the note sent them — and it is named for the artifact, so a reader who
opens one of the two gets the correction for that one.

**WHY THE CARD THREAD IS NOT ENOUGH, IN ONE SENTENCE:** `FINDINGS/024` §2 states the contradiction in the tree,
and a reader who follows the note is never sent to `FINDINGS/`. **The fact was recorded; the reader was not.**

**THE MEASUREMENT (the card's premise, verified here):** both artifacts carry
`config.server_argv[0] = /home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server` — the fork — while
the note says the record *"contains no `server_argv` field"*. **The artifact wins (`PRECEDENCE.md`), the note is
not rewritten, and neither is the artifact.**

**COST, AND IT IS THE REASON RECORDS ARE NOT REWRITTEN:** reading the two corrections takes time a reader might
resent, and the resolution is one indirection rather than one edit. **The benefit is the one the tree keeps
choosing: the note survives as a true measurement of the operator's belief, which is itself why the driver had no
`--llama-server` flag — and the correction records that belief beside the artifact that contradicts it.**

---

## RULING 3 — `holder_sentence()` ON A LOAD REFUSAL: FLIP THE **RECORD**, NOT RULING 82'S CARRIER. LANDED.

**THE MEASUREMENT (the card's, confirmed by this change's own arms):** a CPU-only run of a file the binary cannot
parse printed *"AND THE CARD IS HELD BY: pid 2418 (134 MiB) … Tenants total 7146 MiB"*, while the cause was two
lines further down the log that the record did not quote. **RULING 82's sentence is not wrong; it is
unconditional, and two conditions printed one sentence.**

**RULED: `vram_holder.py` IS NOT TOUCHED, AND THE DISTINCTION GOES IN THE RECORD.** Landed in `sokoban_run.py`
(commit `c015995`, **S2** of `PREREG_sokoban_instrument4.md`). The sentence is **kept verbatim** for the case the
ruling was ratified for — a log that names no cause of its own — and the other case quotes the binary's own line
instead:

```
THE LOG NAMES A READER'S REFUSAL OF THE FILE -> the matched line is QUOTED WITH ITS LINE NUMBER, the holder
                                               sentence is NOT appended, and the record says why
THE LOG NAMES NO SUCH CAUSE                  -> RULING 82's sentence, UNCHANGED, and the record says the log
                                               named no cause -- its ratified case
THE LOG CANNOT BE READ                       -> said out loud; never reported as absent
and the record carries load_failure_class in every case, and it names which of the conditions is being reported
```

**WHY THE CARRIER WAS NOT EDITED, WHICH IS THE WHOLE POINT OF THIS RULING:** the card's cost line said *"the
change must not weaken that case."* **The way not to weaken it is to not touch it:** `vram_holder.py` is
byte-identical to its committed blob (`db357edafd2fd54d494338a5f32c1d2ecfec0ff77eab22cb8c6e6a2a6d1f5135`, not in
the diff), and RULING 82's five-loads-held-by-a-live-lease case prints exactly what it printed before. **A ruling
whose ratified half is preserved by construction is stronger than one whose ratified half is preserved by care.**

**COST OF THE FLIP, AS MEASURED:** a new `why` line and a new field on two failure records, one new module-level
signature list, and the two failure returns now take their class from one definition. The signature list is **a
snapshot of one build's wording**, which is why **the class never travels without the line it was decided from** —
and the six-input control (`classifier_control.py`, 3 real logs + a transcription of RULING 82's own measured
string + an empty log + an unreadable log) fires in both directions and **failed on its first run on an
expectation table I had written wrong**, which is the only evidence that it can fail at all.

**COST OF NOT FLIPPING, MEASURED:** the pre-image failure record for the refused 27B file carries the tenant list
and nothing else; the new one carries `E gguf_init_from_reader: tensor 'output.weight' has invalid ggml type 142`
with its line number. **Two records, one refused file, two subsystems named.**

---

## RULING 4 — THE CENSUS: NEITHER "APPEND THREE NAMES" NOR "LEAVE IT AS THE CENSUS OF ITS DATE" — **RE-DERIVE IT, DATED**. LANDED.

**THE CARD'S QUESTION WAS A CHOICE BETWEEN TWO: append, or leave it as the census of the date it describes.**
**Both are wrong, and the measurement says so:** the census is not short by three names — it is short by **ten at
the time this card was written and thirteen when instrument 4's names are counted** — and its drift began **three
minutes** after it was last derived.

```
MEASURED (census_names_now.py, three carriers at the results root):
  the census names 70 names across its six blocks; the records carry 77; 13 ARE NEVER NAMED BY IT --
    artifact_replaced, load_failure_class (c015995, 2026-10-16, instrument 4), why (the failure path has
    always written it), server_binary_digest/_scope/_source (f1c0c5d, 2026-10-16), loose_match_* (afbebf6,
    2026-10-15), entrant_digest/entrant_digest_scope (3923a52, 2026-10-10), attempted_* (f0eba6e, 2026-10-10).
MEASURED: the census's own last touch is 6d77696 at 2026-10-10 09:17:35; entrant_digest lands in 3923a52 at
09:20:01. FOR ALL BUT THREE MINUTES OF ITS LIFE THE CENSUS HAS DESCRIBED AN INSTRUMENT THAT NO LONGER EXISTS.
```

**RULED: THE LISTS ARE NOT REWRITTEN AND NOT EXTENDED IN PLACE; A DATED SECOND READING IS LANDED UNDER THEM**
(`SOKOBAN_CONFORMANCE_PACKAGE.md` §**2a**). **A census is a READING of the writer; it is dated by construction,
and the fix for a stale reading is a NEW reading, not an edit to the old one** — which is this package's own rule
about its digests (*"still cites 186f561f… deliberately — it is a record of the package produced under that
instrument, not a live pin"*, `SOKOBAN_FREEZE_RECORD.md`) applied to its field lists.

**AND WHAT THE CARD'S "make_conformance_package.py NEEDS NO CHANGE" GETS RIGHT AND WRONG.** Right: the three new
names carry no path, so **the LOCAL/FORMAT split stays true and the tripwire stays clean** — measured, and it is
the tool's own output, not an inference. Wrong, if read as *nothing needs to change*: **`FORMAT` is also a census,
and the three names are absent from it, so the tool reports CLEAN over fields it never examined** — the same shape
as its own documented defect (*"a check that skips what it cannot read reports clean for the same reason a dead
probe reports success"*). **A tool cannot be extended by a document edit; see the follow-up below.**

**WHAT IS DELIBERATELY NOT DONE HERE:** `make_conformance_package.py`, `LIST 1` and the package's own source
list are **not** amended by this ruling. The measurement is landed, the decision is stated, and the edit belongs
to the card that owns the tool.

---

## THE FOLLOW-UPS THIS RULING CREATES, AND WHO OWNS THEM

**Two, both created as cards rather than done here, because doing them would be scope-creep into another owner's
surface and neither is needed for this card's answer to stand:**

```
1  THE CENSUS NEEDS AN ENFORCER, NOT ANOTHER READING. Nothing in the tree compares the package's field lists
   with the writer, which is why the drift went unnoticed for eight days and why the tool reports CLEAN over
   names it has never seen. The enforcer is a check that reads the writer and the package and FAILS ON DRIFT,
   with a positive control (inject a name, watch it fail). Owner: whoever holds the conformance tooling.
2  sokoban_report.py SHOULD READ load_failure_class RATHER THAN SPLIT THE PROSE. It buckets a non-loading cell
   by why.split(" -- ")[0][:44]; with the new prose that label becomes "server exited rc=1.\nTHE BINARY
   REFUSED". It still runs and its numbers do not move (rc 0, byte-identical output on the run of record), and
   it was NOT changed here because instrument 4's own prereg predicted it stays as it is. Owner: the driver's
   owner.
```

---

## WHAT THIS DOCUMENT IS NOT

**It is not a claim about the models.** The 4B solving level 01 in one move is one level every prior winner has
solved, `02_two_boxes` is passed by nobody (measured: 4 played, 0 solved in the run of record, and 0 in the pilot
before it), and no Bonsai entrant is registered in the population. **Nothing here changes a counter, a rate, a
criterion or a cell.**

**It is not a ruling on the artifact NAMING CONVENTION.** The convention stands, unchanged and unconditional, and
Ruling 1 exists precisely so that it can: **the protection is a refusal, so the name does not have to carry the
instrument.**

**And it is not the last word on the fourth item.** Ruling 4 lands a reading and names its own enforcer gap.
**A reading with no enforcer is this card's own finding, already committed, and it is the reason the follow-up
exists rather than a note in a thread.**
