# PRE-REGISTRATION — THE CONFORMANCE CENSUS GETS AN ENFORCER: A CHECK THAT READS THE WRITER BY `ast`, ITS POSITIVE CONTROL, AND THE 21 NAMES IT FINDS

**Written BEFORE the check and the lists land**, in the house form of `PREREG_sokoban_instrument1/2/3/4.md`, and
for the same reason: **a check whose behaviour is not predicted in advance cannot distinguish a working check
from one that happens to print nothing.**

**Card:** `t_bba8182e` (written by the Chair, assigned to Ocho). **Authority, stated rather than implied:** the
card is the Chair's, and ruling 4 of card `t_8dc430a7` says so explicitly — *"WHAT IS DELIBERATELY NOT DONE HERE:
`make_conformance_package.py`, `LIST 1` and the package's own source list are **not** amended by this ruling ...
the edit belongs to the card that owns the tool"*, and it names this card as the follow-up: *"THE CENSUS NEEDS AN
ENFORCER, NOT ANOTHER READING. Nothing in the tree compares the package's field lists with the writer ... The
enforcer is a check that reads the writer and the package and FAILS ON DRIFT, with a positive control (inject a
name, watch it fail)."* **No ruling is cited for the SURFACE because none is needed: this is the tool's own
surface and the Chair assigned it here.**

**Pre-image, measured at the commit this prereg is written against:**

```
HEAD                    d6f6011  2026-10-16 10:32:01 -0700  (main; the tree the check is written against)
make_conformance_package.py     6926 B  sha256 51463f225329b4be56ecee8333c690f290875bad90a8d9b158989f67e0043d56
SOKOBAN_CONFORMANCE_PACKAGE.md 13831 B  sha256 a670069fc62e74ea69c619fce1043914023cd93686aeee0fe5f8f6052302f73a
sokoban.py                     24872 B  sha256 00996929972b9483223bf54f4dcef007162134289c5cdb76a58533ac875e8a7c
sokoban_run.py                 58642 B  sha256 e3f20b3ba561376197ca0cea8dc64ac33a515f7015e99518002314ca02beed62
sokoban_batch.py               13663 B  sha256 d6604f398b6f6afb9e84998d4a1f3417427af22a914f170b24eeb183d6dee75c
```

**AND THE THREE WRITER FILES ARE NOT TOUCHED BY THIS CARD.** The check is a READER; the deliverable is a
mechanism, not another instrument change. Measured after the landing and predicted in §2.8.

---

## 1 WHAT CHANGES — FOUR SUBJECTS, AND ONLY ONE OF THEM IS A PUBLISHED LIST

**S1 — A NEW CHECK, `check_conformance_census.py`.** It reads THE WRITER by `ast` and THE PACKAGE, and fails on
drift in both directions. **FOUR CARRIERS OF A NAME, because a name reaches a record four ways and a reader that
knows one of them reports clean over the others:** a dict literal (identified by the keys that can only be that
literal); a `**spread` (`server_binary_*` reach the record ONLY this way); a `dict(meta, cells=...)` CALL (the run
record's write-time keys are keywords, not members); and a SUBSCRIPT ASSIGNMENT (`ended_why` and
`artifact_replaced` are never keys of any literal). **It also reports what it does NOT read** — the inner shape of
a block-by-reference name whose value is a variable (`turns`, `levels`) — because *not read* and *read and clean*
must never print the same way.

**Three classifications, declared and enforced rather than inferred:**

```
BLOCK_BY_REFERENCE  a name whose VALUE is a nested block (config, host, freeze, levels, cells, turns,
                    reasoning_probe, budget_signature, dead_end, artifact_replaced). The census lists such a
                    name at its parent's level and its keys in the block's own block, so it is RESOLVED by
                    expansion -- here, and not counted as drift in either direction. VERIFIED, not asserted:
                    the check reports how many of them resolved to a key of the writer's literal.
CONDITIONAL         a name carried ONLY by literals that sit on a named execution path (the dead-end verdict's
                    branches, the two load-failure returns, a replacement, a confounded cell). Computed off the
                    writer -- a name is conditional iff EVERY literal that carries it is -- and EVERY
                    package-named conditional name must be DECLARED with its condition. An undeclared one is
                    rc 3. A classification that is not enforced is decoration, and the next conditional name
                    would arrive unexplained exactly the way the last thirteen did.
LOCAL               a name the LOCAL/FORMAT split assigns to the local bookkeeping. Its absence from LIST 1 is
                    correct and is not drift; its absence from the WRITER is drift like any other.
```

**Exit codes, because a check with two outcomes cannot say which of two very different things happened:**
`0` no unclassified drift; `1` DRIFT; `2` THE CHECK COULD NOT READ (a declared site, header or carrier is gone
— a MISS, NOT A PASS); `3` A CONDITIONAL NAME IS NOT CLASSIFIED.

**S2 — THE SPLIT IS EXTENDED (`make_conformance_package.py`), which is the published list this card owns.** The
13 names the card measures are landed **plus the ones the writer shows and no carrier could** (§1's table), each
where the LOCAL/FORMAT test puts it. **`LOCAL` gains a one-name form** — a tuple of length 1 is a TOP-LEVEL
field (`why`), a tuple of length 2 is a field inside a block (`host.node`) — because a split that can only name
nested fields cannot name a top-level local one, and `why` is exactly that.

**S3 — `SOKOBAN_CONFORMANCE_PACKAGE.md` §1: `LIST 1` and `LIST 2` are updated, and NOTHING ABOVE OR BESIDE §2a
IS.** §2's census blocks and §2a's dated second reading are left exactly as they are; they are a READING, and
this card does not rewrite readings. **But `LIST 1`'s config group is RESPELLED to the dotted form the split
uses** (`config.reasoning`, not `reasoning` under a group header): the two carriers were one list in two
notations, and a parity check that normalises that difference is a parity check that excuses it.

**S4 — THE POSITIVE CONTROL, `check_conformance_census_control.py`,** in the shape the card asks for: inject a
name into a COPY of the package, remove one from a COPY of the writer, and watch the check fail naming both.
**It carries its own control:** the same copies, unmutated, must pass — otherwise the failure proves nothing
about the injection.

### THE 21 NAMES, WITH WHAT PUTS EACH ONE WHERE

**All 13 of the card's names are here, and the check finds EIGHT MORE.** Six of them are the inner keys of the
`artifact_replaced` block, which the card's measurement could not see because it read the record's top level and
the four envelope blocks, and `artifact_replaced` is a fifth block; two — `ended_why` and `error` — are on paths
no committed carrier has ever taken. **A RECORD CANNOT SHOW A PATH IT NEVER TOOK; THE WRITER CAN.**

```
NAME                                       BLOCK             LANDED IN   WHY THERE
artifact_replaced                          CELL RECORD       LIST 2      a LOCAL block: a repo-relative path, an
artifact_replaced.path/_sha256/_bytes/                  (its 7     mtime, and the replaced record's own
  _mtime/_it_named/_reason_given/_reading                keys)      identity. Meaningful only here.
why                                        DEAD-END CELL     LIST 2      two of its three branches embed the
                                           + LOAD FAILURE               holder's tenancy reading (pid, MiB)
                                                                        read off THIS box, and it quotes THIS
                                                                        box's log line. Its portable half
                                                                        travels as load_failure_class.
reasoning_probe.error                      REASONING PROBE   LIST 2      the local socket's exception text,
                                                                        unbounded by anything in this tree.
                                                                        Its portable half is `observed: None`.
load_failure_class                         LOAD FAILURE      LIST 1      which condition the failure reports:
                                                                        a class, and it means the same thing
                                                                        on another box.
ended_why                                  CELL RECORD       LIST 1      the confounded-cell caveat; prose that
                                                                        names no local coordinate.
entrant_digest, entrant_digest_scope        CELL RECORD       LIST 1      THE ENTRANT IS THE THING MEASURED, so
                                                                        it is identified by a digest and not
                                                                        by a name (the package's own §2).
attempted_emitted, attempted_consumed,      CELL COUNTERS     LIST 1      two counts and the note that says the
  attempted_note                                                        old name is deprecated -- and the
                                                                        rate is solved/attempted_emitted,
                                                                        which a shorter run cannot flatter.
loose_match_diagnostic_only_never_scored,   CELL COUNTERS     LIST 1      a count that says in its own NAME
  loose_match_diagnostic_note                                           that it is never scored, and its
                                                                        scope sentence.
server_binary_digest,                       CONFIG BLOCK      LIST 1      FORMAT-shaped, as the ruling says: a
  server_binary_digest_scope,                                           digest, a scope sentence and a
  server_binary_source                                                  selector name -- AND NO PATH.
```

**AND WHY THE LAST THREE STAY TRUE TO THE SPLIT'S PURPOSE:** `server_argv` already carries the absolute path and
is already LOCAL; the three new names are what the record can say about the binary WITHOUT a coordinate. **That
is confirmed by running the tripwire, not by asserting it** (§2.4 and §2.5).

---

## 2 THE PREDICTION, RECORDED BEFORE THE CHANGE

**1. THE CHECK FAILS ON THE PRE-IMAGE, WITH EXACTLY 21 NAMES IN ONE DIRECTION AND NONE IN THE OTHER.** Direction
1 (emitted, unnamed) lists 21 names across 6 blocks and 4 files with a `file:line` for each occurrence;
direction 2 (named, unemitted) is empty. **The card's 13 are a subset of the 21.**
*Falsifier: any other count; any of the 13 missing from it; or a name reported that the record carries under a
different block than the one printed.*

**2. THE ENFORCER FINDS NAMES NO CARRIER CARRIES.** `ended_why` (`sokoban_run.py:805`, on a cell where every
command was a harness-produced empty) and `error` (`sokoban_run.py:591`, when the probe could not be asked at
all). Both are absent from all three carriers the last card measured, and neither is a mistake in those carriers.
*Falsifier: either name appearing in a committed artifact; or the same 21 arriving from records alone.*

**3. THE TWO DIRECTIONS ARE INDEPENDENTLY DRIVEN, AND BOTH GO TO ZERO AFTER THE LANDING.** rc 1 before, rc 0
after; direction 2 empty on this tree (the package names nothing the writer has lost), which is why the control
MUST inject to demonstrate it (§2.6).
*Falsifier: direction 2 non-empty on the pre-image, or a tree that passes before the lists are extended.*

**4. THE TRIPWIRE STAYS TRUE, MEASURED.** `python3 make_conformance_package.py` still exits **0** and still
prints **THE SPLIT IS CLEAN** with eleven new FORMAT names in its list. **Its output BYTES change** — the run of
record predates instrument 3, so the new names print `?` UNRESOLVED ("not checked, not clean") — and that is
predicted here rather than discovered later.
*Falsifier: rc ≠ 0; a LEAK line; or a NEW FORMAT field whose value carries a path, hostname or device where it
does resolve.*

**5. THE PARITY CHECK FAILS BEFORE THE LANDING AND PASSES AFTER.** Before: `LIST 1` names the config keys bare
while `FORMAT` prefixes them `config.`, so the two carriers of one list differ. After: sets equal.
*Falsifier: parity clean on the pre-image (then the carriers were already one list and this prediction is
wrong), or dirty after the landing.*

**6. THE CONTROL FAILS WHERE IT MUST AND PASSES WHERE IT MUST.** On COPIES in a scratch directory: (a) a name
injected into §2's CELL RECORD block → rc 1, printed under DIRECTION 2; (b) `final_board` renamed in
`sokoban.py`'s `play()` literal → rc 1, the new name under DIRECTION 1 and `final_board` under DIRECTION 2;
(c) both copies UNMUTATED → rc 0. **(c) is the control's own control: without it, a check that fails on
everything would look like a check that catches everything.**
*Falsifier: an arm that does not fail where it should, or an arm that fails on the unmutated copy.*

**7. A MISS IS NOT A PASS.** With the `**DEAD-END CELL …**` header deleted from a copy of the package: rc **2**,
and the missing header is printed as a miss. With `sokoban_batch.py` absent from the root: rc 2, likewise.
*Falsifier: rc 0 with a declared block or writer gone.*

**8. NOTHING ELSE MOVES.** The repo's controls are **rc-identical** before and after (the same 16 commands the
last card ran, output bytes listed where they differ); the three writer files, every artifact, every record, the
freeze record and each published number are byte-identical after the card; no digest in any pinned set moves.
*Falsifier: a control rc that moves; a byte of any writer or record that changes.*

**9. FALSIFIERS, NAMED SO THE PREDICTION CAN FAIL:** a check that passes on the pre-image; a drift count other
than 21; a name reported without a `file:line`; a classification that is asserted rather than resolved; a
conditional name accepted without a declared condition; a control that cannot fail; and a tripwire that stops
reporting THE SPLIT IS CLEAN.

---

## 3 WHAT IS **NOT** IN THIS CHANGE, DISPOSED OF ONE BY ONE

**(a) `SOKOBAN_CONFORMANCE_PACKAGE.md` §2's census blocks AND §2a ARE NOT EDITED.** They are a reading, and the
card says so in as many words. The check REPORTS the two censuses' divergence as a reading rather than failing on
it, because the sea of names the census carries and the split does not is the SPLIT's deliberate scope, not
drift.

**(b) NO RECORD IS REWRITTEN, AND NO ARTIFACT IS TOUCHED.** Nothing here re-measures anything; the evidence is
source, not a run.

**(c) THE ARTIFACT-PATH GATE AND `sokoban_report.py` ARE OTHER CARDS' SURFACES** (`sokoban_run.py` `c015995`;
card `t_7d2eb103`). Not touched, not re-litigated.

**(d) THE TRIPWIRE'S PATTERN SET IS NOT WIDENED.** It scans for a path, a hostname or a device name, and it is
run rather than asserted. **Its blind spot is recorded rather than silently left:** `why` carries the holder's
tenancy reading on two branches (pid + MiB) and NO pattern in `LEAK` matches it — which is why `why` is LOCAL by
the TEST and not by the tripwire. **A tripwire that is the only defence would have passed it.**

**(e) THE MODELS ARE NOT TOUCHED AND NO CLAIM IS MADE ABOUT THEM.** No counter, rate, criterion, cell, prereg,
freeze record, grammar or declaration is edited.

---

## 4 THE MEASUREMENT SCALE

**No model is loaded, no GPU is touched, no arm is run.** The check reads source by `ast`; the controls run on
copies in a scratch directory; the 16 repo controls are the same list the last card ran and take ~1.3 s.
**Evidence lands at the declared results root, `/home/chilly1/workspace/cabinet_results/t_bba8182e/`, outside
every git tree.**
# LANDED — 2026-10-16 10:40 -0700. THE PREDICTIONS ABOVE WERE WRITTEN FIRST AND ARE VERIFIED, NOT RESTATED.

```
main            a057d1a prereg        a6acf19 the check + its control        de778b4 the two carriers
after           make_conformance_package.py  10894 B  sha256 73408d666a07ac9ec8743f7cf7c8cd360eed7cbbef8c026b4e7901a2d30a9e7e
                SOKOBAN_CONFORMANCE_PACKAGE.md 16085 B sha256 b63996d2fb8939562261d699e18d53ccd5d4710a670e8084b413a08234f416d6
                check_conformance_census.py    36076 B sha256 ff4b8d20bb1a054fb2d38650ec3d27f7afe7899814ff6bd7b6ee65e9488f3da6
                check_conformance_census_control.py 7460 B sha256 3e247a60894298d26b9fbac10f861fd4b32d94e9f047c84ddb4c9834ed9075e3
UNCHANGED       sokoban.py   00996929972b9483223bf54f4dcef007162134289c5cdb76a58533ac875e8a7c
                sokoban_run.py e3f20b3ba561376197ca0cea8dc64ac33a515f7015e99518002314ca02beed62
                sokoban_batch.py d6604f398b6f6afb9e84998d4a1f3417427af22a914f170b24eeb183d6dee75c
EVIDENCE        /home/chilly1/workspace/cabinet_results/t_bba8182e/  (outside every git tree)
```

**1. THE CHECK FAILS ON THE PRE-IMAGE — rc 1, 21 names in one direction, none in the other, each with its
`file:line`.** VERIFIED: `check_pre.txt` (captured at `d6f6011`, before the lists moved) lists 21 names across
6 blocks; DIRECTION 2 is empty; the card's 13 are all inside the 21. **The prediction said exactly 21 and it was
21** — which is itself worth stating plainly, because the number was written down before the reader existed.

**2. THE ENFORCER FINDS NAMES NO CARRIER CARRIES.** VERIFIED, and it is the strongest single result on this card:
`ended_why` (`sokoban_run.py:805`) and `error` (`sokoban_run.py:591`) are absent from all three carriers the last
card measured (`leak_scan.txt`: `NOT PRESENT ON ANY CARRIER`). **The card's own measurement could not have found
them, not because it was careless but because it read RECORDS and a record cannot show a path it never took.**
Six more names — the inner keys of the `artifact_replaced` block — were invisible to it for a smaller reason: the
measurement read the record's top level and the four envelope blocks, and `artifact_replaced` is a fifth.

**3. BOTH DIRECTIONS GO TO ZERO. rc 1 -> rc 0.** VERIFIED: `check_post.txt`, DIRECTION 1 none, DIRECTION 2 none.
**AND DIRECTION 2 WAS INDEED EMPTY ON THE PRE-IMAGE**, which is why §2.6's injection is not decoration: on this
tree a check that only ever compared the writer against the package would never have exercised the other way.

**4. THE TRIPWIRE STAYS TRUE, AND ITS OUTPUT BYTES CHANGE.** VERIFIED: `make_conformance_package.py` rc **0**,
closing with **THE SPLIT IS CLEAN**; 14 lines print `UNRESOLVED: not checked, not clean` because the run of
record predates the names — predicted, not discovered. **AND THE PATTERNS WERE RUN OVER THE VALUES THEMSELVES**
(`leak_scan_new_format_fields.py`, importing the split's own `LEAK`/`leak_in` rather than copying them): the three
`server_binary_*` carry a digest, a scope sentence and a selector name and **no path**; no pattern matches any of
the twelve new FORMAT fields on the three carriers that carry them.

**5. PARITY FAILED BEFORE AND PASSES AFTER.** VERIFIED: pre-image the two carriers differed by 22 names
(`LIST 1` bare `reasoning` vs `FORMAT`'s `config.reasoning`); after, `identical: LIST 1 and FORMAT both name 52;
LIST 2 and LOCAL both name 16`.

**6. THE CONTROL FAILS WHERE IT MUST AND PASSES WHERE IT MUST — FIVE ARMS, ALL AS PRE-REGISTERED**
(`control_post.txt`, rc 0): C the unmutated copies pass (rc 0); A an injected package name fails and is named
under DIRECTION 2 (rc 1); B a renamed writer key fails with the new name under DIRECTION 1 and the old under
DIRECTION 2 (rc 1); D a deleted census header is a MISS (rc 2); E a literal whose identifying key is renamed is a
MISS (rc 2). **BECAUSE OF C, the failures are shown to be caused by the mutation — not by the copy, the temp
directory, or the run.**

**7. A MISS IS NOT A PASS.** VERIFIED: arms D and E. **Arm E exists because arm B's FIRST CUT was wrong and the
check was right:** it renamed `final_board`, which is one of the keys the check identifies that literal BY, so
the site vanished and the check reported a MISS (rc 2) while my arm expected DRIFT (rc 1). See "what the
prediction got wrong" below.

**8. NOTHING ELSE MOVES.** VERIFIED: the three writer files are byte-identical to the pre-image; the repo's
controls are **rc-IDENTICAL 16/16** before and after. **OUTPUT BYTES differ on 7 of the 16** and each is
accounted for: five were already non-byte-stable at the parent's own run (`sokoban_solver.py`,
`test_no_silent_zero.py`, `test_declared_root.py`, `check_field_semantics.py`, `verify_scope.py`),
`make_conformance_package.py` differs because of prediction 4, and `check_one_reader.py` differs because it
scans `*.py` files and this card ADDS TWO — `files scanned 91` where the pre-image said 89, measured, not
assumed.

**9. FALSIFIERS: NONE FIRED**, with one of them firing against me rather than against the check (§2.6's "an arm
that does not fail where it should"), which is recorded below rather than tidied away.

---

## AND THE THREE THINGS THIS MEASUREMENT GOT WRONG, RECORDED BECAUSE A RECORD THAT ONLY REPORTS ITS SUCCESSES IS NOT A RECORD

**(a) MY FIRST CONTROL ARM EXPECTED THE WRONG RC, AND THE CHECK WAS RIGHT.** Renaming `final_board` in
`sokoban.py` makes the CELL COUNTERS literal unfindable, because `final_board` is part of the fingerprint that
identifies it — so the check reported a MISS (rc 2) and my arm insisted on DRIFT (rc 1). **The arm was wrong.**
It was re-cut onto a key that identifies nothing, and the fingerprint case became its own arm (E) so that the
two failure modes can never again be mistaken for one another.

**(b) THE FIRST VERSION OF THE READER DOUBLE-COUNTED THE NESTED BLOCKS.** Expanding every block-by-reference
name's value named the config block's keys TWICE — once bare under CONFIG BLOCK and once dotted under CELL
RECORD — and a census that names a field twice can disagree with itself. The four names whose keys are another
declared site's block (`config`, `reasoning_probe`, `budget_signature`, `dead_end`) are now read THERE and only
there.

**(c) THE FIRST DIRECTION-1 MATCH WAS BY NAME ALONE, AND THE TWO CENSUSES ARE WRITTEN IN TWO NOTATIONS.** A
census names a sub-block's keys BARE under the parent's block (`freeze :: simulator verifier ...`); this reader
gives dotted paths (`freeze.dead_end_verifier`). Matching on the bare name alone would have reported those keys
as drift of one notation against the other — **and matching on the LEAF ALONE would have been worse: it would
have let the cell record's `legend` answer for the config block's, which is a different field that happens to
share a name.** The match is at the leaf WITHIN THE OWNING BLOCK, in both directions, and the rule is written
where it is applied.

**AND ONE THING IS DELIBERATELY NOT READ, NAMED IN THE CHECK'S OWN OUTPUT** so it cannot be mistaken for a
clean result: the inner shape of `turns` and `levels`, whose values are a variable and a dict comprehension
rather than literals. `turns` is named by the census and by the split as a BLOCK; nothing in the package names
its keys, and this check does not pretend to have read them.

**IT IS NOT A CLAIM ABOUT THE MODELS. No counter, rate, criterion, cell, prereg, freeze record, grammar,
declaration or artifact is touched, and no published number moves.**
