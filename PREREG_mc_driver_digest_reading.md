# PRE-REGISTRATION — THE FIELD CHECKER'S DRIVER DIGEST: A READING OF THE INSTRUMENT OF THE RECORD'S DAY, NOT AN EXPECTATION ABOUT TODAY'S FILE

**Card:** `t_d68e29ba` (the missile-command cabinet), the NAMED RESIDUAL of card `t_a74fee86` — found by running
the cabinet's own field checker while landing that card, whose appendix names this consequence for the first
time. **This file and `scripts/probe_mc_driver_digest.py` are committed BEFORE the edit they describe**, so the
edit cannot be read as support for a claim whatever it shows. Same shape as `PREREG_mc_ab_arm_names.md`,
`PREREG_mc_ab_arm_keys.md` and `PREREG_mc_entrant_identity.md`, whose discipline this inherits.

**Nothing here is a criterion, a verdict or a re-score.** No coordinate, record, archive, count, level or
ceiling moves. `FAILED ON THIS POPULATION` stands exactly as attached to C2 and C3 (`MC_VERDICT_1.md`). The 22
published coordinates stay exactly as they are — byte for byte, digest for digest.

**The card's address is checked here rather than trusted, and it is right.** Re-derived by inspection of
`scripts/check_mc_field_plain.py` at `e0740e47f39a5e74`: the failing assertion is **lines 138-139**, the record
identity dict it reads through is **lines 125-128**, the checker's own control section is **[6] at line 206**,
and the honest total is printed at **lines 300-303**. `MC_FIELD_PLAIN.md:24, :89, :207, :217-218` and
`PREREG_mc_field_plain.md` (§6, "the controls this run carries", third line) are the two places that state the
expectation this card narrows; neither is edited (both are records of a day — see §6).

---

## 0. WHAT WAS MEASURED, AND BY WHOM — INCLUDING THE PEEK

**RECONNAISSANCE (scratch, NOT committed, taken before this file existed; named because a prediction made after
a peek is still a prediction about the governed run, but the reader is entitled to know the peek happened):**

```
recon1  git history of missile_command_run.py, read with git log --all + git show, every commit's blob hashed:
          cb9177a  b726188380ce681c   the first driver, which produced the `example`-arm field
          f085993  4018f0262498eb3e   the instrument fix (F1/F2), the driver the field was RE-TAKEN under
          a0bdd0b  3bd43eed4c6e41f3   card t_8edaaf2d's E1/E2 (coordinate arm from MC_DECLARATION.md,
                                     entrant_digest_scope) -- the driver ON DISK TODAY
recon2  the 22 published records carry 4018f0262498eb3e and nothing else; `driver_digest` is a TOP-LEVEL
        record field with no sibling copy anywhere (protocol.* carries declaration_digest, simulator_digest in
        clock_audit, no driver digest) -- so "disagrees with its own record's sibling fields" cannot be a
        within-record comparison; the siblings that exist are THE OTHER 21 RECORDS OF THE SAME PASS.
recon3  the archive (probes/MC_FIELD_EXAMPLE_ARM_ARCHIVE_20261017.json, edf414eaa1a8997f): 22/22 pre-move
        records carry NO driver_digest at all -- F2 added the field, so the pre-move instrument is silent about
        which driver produced it. THE HISTORY IS THEREFORE THE ONLY TREE-LOCAL SOURCE THAT CAN ANSWER "does
        this digest name a driver this cabinet ever had?" -- and it answers it exactly, with 3 versions.
recon4  the field checker's failing line as it stands, from logs/mc-field-check-ocho.out:23-25 (108/111):
          FAIL  ...and the DRIVER digest of the driver that is on disk -- the gap F2 closed
                got  ['4018f0262498eb3e']   want ['3bd43eed4c6e41f3']
        ONE failure, and it says nothing about WHICH record is at fault: `ids()` collapses the field to the
        SET of digests, so a correct field and a mutated one print the same line.
SMOKE RUNS OF THE PROBE ITSELF (in the tree, under logs/, before this file existed)
  smoke 1  mc-driver-probe-smoke   3/7, C3-C6 FAIL, every other check PASS   <-- THE PRE-EDIT READING
        The three shadow cabinets returned 108/111 each with ONE driver failure each, and that one failure is
        the SAME LINE quoting the same two digests in all three:
          M0 the field as published               got ['4018f0262498eb3e']                    want ['3bd4...']
          M1 one record: deadbeefdeadbeef         got ['4018f0262498eb3e', 'deadbeefdeadbeef'] want ['3bd4...']
          M2 one record: b726188380ce681c         got ['4018f0262498eb3e', 'b726188380ce681c'] want ['3bd4...']
        So the pre-edit checker names a VALUE and never a COORDINATE, and the published field sits on the same
        line as both mutations. That is the defect stated as a measurement rather than as a claim, and it is
        what C3-C6 turn into FAILING checks (they are written with the POST-fix expectation, so they fail
        before the edit -- the same shape as the parent cards' positive controls).
        Nothing was corrected in the probe for the governed run: the smoke's rc was not captured outside the
        unit (run_guarded.sh's `systemd-run` does not propagate it -- named as a gap, and the governed runs
        capture it INSIDE the unit with a `/bin/bash -c '...; echo "EXIT $?"'` wrapper).
```

**The run this pre-registration governs** (§5) is taken **after** this commit.

---

## 1. THE DECISION — THE RECORDS ARE RIGHT AND THE CHECK IS SCOPED WRONG

**Option 1 of the two the card names, decided here and given its reason rather than its convenience.**

`driver_digest` becomes a **READING**: the checker reports the driver the record names against the driver on
disk, and when they differ it is **INCONCLUSIVE FROM THE RECORD'S SIDE**, not a failure. The consequence is
stated in the checker's own output, not only here:

> **A record's `driver_digest` identifies the instrument OF ITS DAY, not the current instrument.** A later,
> legitimate edit to the driver makes the two differ and falsifies nothing about the record. The field is NOT
> re-taken on account of it.

**Why it is right, in three measured steps:**

1. The 22 records are correct. They were taken under `4018f0262498eb3e` (`MC_FIELD_PLAIN.md:24, :89,
   :217-218`), which is a committed driver (`f085993`). The card that moved the driver to
   `3bd43eed4c6e41f3` (`t_8edaaf2d`) changed the coordinate arm's source and a scope string — the same family
   of edit as every other legitimate edit, and the records are not a claim about it.
2. The assertion cannot survive **any** legitimate edit to the driver, which makes it an assertion about the
   future disguised as a check on the record — the exact class card `t_d21287e4`'s landing note §5 named: *an
   expectation may be a literal; it is SUPPOSED to go stale.* A check that must fail after every driver edit
   stops being read, and a check nobody reads is the empty-room defect aimed at the checker.
3. `entrant_digest` already became a reading for the same structural reason (`DECISION_entrant_identity.md`,
   main, decision 3(a)). This makes the record's instrument block internally consistent: **the two digests
   that name "what produced this record" are readings; the digests that name frozen inputs which must not move
   (`simulator_digest`, `legend_digest`, `declaration_digest`) stay checks.** The distinction is not taste: a
   frozen input that moves is a defect, and an instrument of the day that is later edited is not.

**Why NOT option 2 (re-take the field under the current driver).** It moves 22 published coordinates and every
number `MC_FIELD_PLAIN.md` quotes, which the card reserves to the Chair, and it would buy nothing this card
needs: it would make the checker agree with itself about a file that will be edited again. **It is also not
required by any criterion** — no criterion reads the driver digest.

---

## 2. THE EDIT, EXACTLY — ONE ASSERTION AND ONE WORD IN THE DOCSTRING; NOTHING ELSE IN THE FILE

**2a. The docstring's claim is corrected** (lines 4-11). It says the checker re-derives *"the digest of the
declaration, the driver and the simulator, which are read from disk rather than compared against a copy carried
in the record"*. That sentence is what this card falsifies for one of the three: the driver's digest is READ,
reported, and its agreement with disk is not a criterion. The declaration's and the simulator's stay checks,
and the docstring will say so in one clause rather than three.

**2b. The failing assertion is REPLACED (lines 138-139), not relaxed.** Removed:

```python
    ck("...and the DRIVER digest of the driver that is on disk -- the gap F2 closed", ids("driver_digest"),
       [live["driver"]])
```

In its place: a **reading** (no `ck`, so it cannot pass or fail) plus **three checks, each of which fails on a
MUTATION and none of which can go stale when a driver is edited**:

```
D1  every record's driver_digest is the digest of a version of missile_command_run.py this cabinet HAS
    COMMITTED -- the set is read from git (`git log --all` + `git show`, every blob hashed), the working
    tree's own version included.  FAILS ON: a digest that belongs to no driver this cabinet ever had.
    Its got-value is a list of (coordinate, digest) so the failure NAMES the record.
    ITS ONE STATED WAY TO FAIL ON A LEGITIMATE RECORD, named rather than discovered: a run taken from an
    UNCOMMITTED driver names a version no commit holds; the remedy is to commit the driver, NOT to re-take
    the digest.  If git cannot be read at all the check FAILS with the error printed -- "cannot check" is
    never a pass.
D2  ...and the 22 records name ONE of them between them -- the field was taken in one pass.  FAILS ON: a
    record that disagrees with its own 21 siblings, whatever digest it carries, legitimate or not; the
    got-value is the list of (coordinate, digest) that disagree with the field's majority, so it NAMES them.
    ITS STATED CONSEQUENCE: a future card that re-takes PART of the field must amend this line under its own
    pre-registration.  A split field is a change to the FIELD and must never be read as one record's error.
D3  ...and every record's driver_digest is 16 lowercase hex and its driver_digest_scope names
    missile_command_run.py.  FAILS ON: a missing, malformed or mis-scoped digest -- a record that cannot say
    what its own digest digests.
```

**2c. Two controls are added to the checker's own control section [6]**, so that every future run — not only
this card's probe — demonstrates that D1 and D2 can fail. They rebuild a mutated copy **in memory** and call
**the same predicate functions D1 and D2 call** (not a parallel implementation), so the control tests the code
path rather than a description of it:

```
[6b] a record whose driver_digest belongs to NO committed driver is caught, and NAMED   (D1's predicate)
[6b] a record that names a DIFFERENT committed driver than its siblings is caught        (D2's predicate)
```

**2d. THE COUNT, ARITHMETICALLY AND HONESTLY.** `111` → **`115`**: one expectation removed (`-1`), three checks
that fail on mutation added (`+3`), two in-checker controls added (`+2`). **No failure is removed to make a
number look better**: the one FAILING check becomes a reading, and the three checks that replace it are
strictly more capable of failing than the assertion they replace — the old one failed on a correct field and
could not name a record; the new ones pass on the correct field and name the record on a mutation.

---

## 3. PREDICTIONS — FIXED BEFORE THE EDIT, FALSIFIABLE, NONE OF THEM A CEILING

**P1 (the premise, re-derived).** The git history of `missile_command_run.py` holds at least the three versions
`{b726188380ce681c, 4018f0262498eb3e, 3bd43eed4c6e41f3}`; the file on disk is `3bd43eed4c6e41f3`; all 22
published records carry `4018f0262498eb3e`; **and 22/22 archived pre-move records carry no `driver_digest` at
all.** Falsified if any of these differs.

**P2 (the defect, pre-edit, and it is ONE failure with no address).** Before the edit the checker reports
exactly **one** driver-mentioning failure, `got ['4018f0262498eb3e'] want ['3bd43eed4c6e41f3']`, and **three
shadow cabinets that differ only in one record's `driver_digest` produce that same single failure, quoting the
same two digests and naming no coordinate**: the published field, a record carrying `deadbeefdeadbeef`
(belongs to no driver), and a record carrying `b726188380ce681c` (a real but different driver). The pre-edit
probe is **3/7 with C3-C6 FAIL and rc 3.** Falsified if the pre-edit checker distinguishes any of the three, or
if any check other than C3-C6 fails.

**P3 (the reading, post-edit — the field is not a failure).** On the unmutated shadow the driver block
**PASSES with zero driver failures** and prints `INCONCLUSIVE FROM THE RECORD'S SIDE` naming both digests and
the committed set. Falsified if the unmutated field still fails a driver check, or if the INCONCLUSIVE reading
does not appear.

**P4 (the mutations are caught, and the failure carries an address).** Post-edit, `deadbeefdeadbeef` in one
record fails **two** driver checks, both naming the coordinate and the value (D1: no such driver; D2: the field
is split); `b726188380ce681c` in one record fails **exactly one**, naming the coordinate (D2 — it IS a
committed driver). The probe is **7/7, rc 0.** Falsified if a mutation is caught without naming the record, or
if a legitimate field fails.

**P5 (the total, stated rather than discovered).** The checker's own total is **115** in all three shadow runs
and in the field run; the failures are **the two known findings plus 0/2/1 driver failures** — shadow totals
**113/115, 111/115, 112/115**. On the real field the total is **113/115** with the two named findings
(`entrant_digest` non-reproducibility, `MC_FIELD_PLAIN.md` Finding B's two cells) and **no driver failure**.
Falsified if any total differs; a different total is CORRECTED in the landing note, not absorbed silently.

**P6 (nothing else in the checker moved, and the collision is fenced).** Every check name and every result in
sections `[1]`, `[2]`, `[4]`, `[5]`, `[7]`, `[8]` is identical before and after, in the field run; the entrant
block that card `t_77f73033` owns — from `# THE ENTRANT IS THE SUBJECT OF THE MEASUREMENT` through the
`MEASURED, AND IT IS A FINDING ABOUT THE PRE-MOVE RECORDS` print — is **byte-identical** (its sha256 is taken
of both versions). Falsified if any of those differ.

**P7 (the records, the archive and the frozen inputs are untouched).** The 22 coordinates' aggregate digest
`sorted[(path, sha256)]` is `318739354497d7cf…` before and after; `git status --porcelain probes/ results/`
is empty after every command in §5; `MC_DECLARATION.md` `2ada03ee2ad1f60b`, `missile_command.py`
`eb5ed36591b300e6`, `missile_command_run.py` `3bd43eed4c6e41f3`, `MC_FIELD_PLAIN.md` `d991c234024ce2e7`,
`PREREG_mc_field_plain.md` `e40ac17826d2f87a`, the archive `edf414eaa1a8997f`, the population artifact
`9335b2a39b4d1d38` and `MC_LEGEND_AB.json` `029244b6e5232a6b` all unmoved; the driver's `--self-test` is
**53/53** before and after. Falsified if any moves.

**P8 (the drift, and what it costs).** `scripts/check_mc_field_plain.py` `e0740e47f39a5e74` → **a different
value** (a hash cannot be predicted from prose; it is recorded in the landing note). **And the cost is named
rather than left to be found: `MC_FIELD_PLAIN.md:11` says the checker is "111 checks"** — that sentence becomes
a statement about the checker as it was on 2026-10-17, not as it is. It is **not edited**: it is that card's
record of its own day, exactly as `PREREG_mc_field_plain.md:168`'s expectation is that card's. The new total
lives in this file's landing note and in the checker's own output. Falsified if `MC_FIELD_PLAIN.md` is changed
by this card, or if the checker's digest is unchanged.

---

## 4. CONTROLS — EACH WITH THE COMMAND THAT READS IT

```
the premise            git -C <cab> log --all --format=%H -- missile_command_run.py
                       then `git show <sha>:missile_command_run.py | sha256sum` per commit   (P1)
the defect, pre-edit   scripts/run_guarded.sh mc-driver-probe-pre <cab> /usr/bin/python3 \
                           scripts/probe_mc_driver_digest.py                    (C3-C6 FAIL, rc 3; P2)
the fix                the same probe, post-edit                            (C1-C7 PASS, rc 0; P3, P4)
the total              the field checker's own last line, both runs          (108/111 -> 113/115; P5)
the fence              the entrant block's sha256, both versions; `git diff -U0` must show no hunk
                       touching lines 144-164 of the pre-edit file                       (P6)
nothing moved          git status --porcelain probes/ results/; the 22-coordinate aggregate digest;
                       the driver's --self-test                                    (P7)
```

**The probe's own validity is measured, not asserted:** its three shadow cabinets differ from this cabinet in
one record's `driver_digest` and in nothing else (`diff -r` of the two file lists is reported), no model file is
read (`ARENA_MODELS` points at a nonexistent path, so the entrant check fails on all eleven records identically
in every run and is not what the instrument reads), and the shadow trees live in `tempfile.mkdtemp()` **outside**
this cabinet. Its git read is its OWN, independent of the checker's — if both asked one function, a mistake in
that function would be invisible to both.

---

## 5. THE ORDER OF OPERATIONS, FIXED HERE

```
1  commit this file + scripts/probe_mc_driver_digest.py                              (pre-registration + instrument)
2  run the checker on the real field    -> P2's number, and the 108/111 reproduced   [unit mc-driver-field-pre]
3  run the probe                        -> P2: 3/7, C3-C6 FAIL, rc 3                 [unit mc-driver-probe-pre]
4  run the driver's --self-test         -> 53/53                                     [unit mc-driver-selftest-pre]
5  make the edit (§2a-§2c, one file)
6  run the checker on the real field    -> P5: 113/115, no driver failure             [unit mc-driver-field-post]
7  run the probe                        -> P3/P4: 7/7, rc 0                          [unit mc-driver-probe-post]
8  run the driver's --self-test         -> 53/53, unchanged                           [unit mc-driver-selftest-post]
9  read §4 back: the fence, the 22-coordinate aggregate, git status, every digest     (P6, P7)
10 append the landing note to THIS file; commit the edit with it; mirror this document to main; push both;
   read both back byte-for-byte
```

**Step 3 is not ceremony.** Without it, "the check now reads instead of asserting" is a description; with it,
the same three shadow cabinets return one indistinguishable failure before the edit and three distinguishable
outcomes after it — which is this card's whole claim, measured.

**Every command in §5 runs under `scripts/run_guarded.sh` (`5e34e455b5193e89`), never a bare `python3`.** The
probe takes no lease, loads no model and starts no server; the checker only reads and hashes.

---

## 6. WHAT WOULD FALSIFY THE CARD, AND WHAT WOULD NOT COUNT AS SUCCESS

**FALSIFIERS.** Any of: the new checks passing on a mutated record; the new checks failing on the published
field; a mutation caught without naming the record; any total other than the one predicted (§3 P5) left
unreported; any check in `[1]`,`[2]`,`[4]`,`[5]`,`[7]`,`[8]` changing its result; the entrant block changing by
one byte; any coordinate, archive, artifact or frozen input moving; a digest re-taken to make a check pass.

**NOT SUCCESS:** the checker reporting `115/115` (it must not — two findings remain, and they are the
cabinet's named ones); the assertion deleted and nothing put in its place; the check relaxed to "the digest is
16 hex" (a mutation would then pass); the field re-taken under `3bd43eed4c6e41f3` (a different, larger card);
`MC_FIELD_PLAIN.md` edited to agree with the new total (a record of a day is not rewritten — see P8).

---

## 7. THE COLLISION WITH `t_77f73033`, WHICH IS BLOCKED, AND THE FENCE

Card `t_77f73033` edits **the entrant-identity block** (pre-edit lines 144-164) of the same file and is
**blocked** (dispatcher `gave_up`, two crashed runs, no local edit: `git status --porcelain` on this cabinet is
empty at the start of this card). **This card does not land that block and does not touch it**: the fence in
§3 P6 is a byte-identity check of exactly that region, and the landing note records the sha256 both sides. Two
cards landing in one file at the same time is how a diff becomes unreadable; one landing with its fence
measured is how it stays readable. When `t_77f73033` is unblocked it will find lines 144-164 as it left them,
shifted by however many lines §2 adds above them — which is why the fence is a **hash of the block**, not a line
number.

---

## 8. FROZEN INPUTS — RE-READ, NOT QUOTED FROM THIS NOTE

```
missile_command_run.py                3bd43eed4c6e41f3   (the instrument on disk; NOT edited by this card)
missile_command.py                    eb5ed36591b300e6   (frozen simulator)
MC_DECLARATION.md                     2ada03ee2ad1f60b
PREREG_missile_command.md             01548e9a866df03e
levels/mc_01_one_shot.txt             ab101ca955c1c853
levels/mc_02_scarcity.txt             327d2157bd0b8a83
MC_FIELD_PLAIN.md                     d991c234024ce2e7   (NOT edited; see P8)
PREREG_mc_field_plain.md              e40ac17826d2f87a   (NOT edited; its §6 states the expectation this card narrows)
PREREG_mc_ab_arm_names.md             3f670a15e8e9cb4e   (the card's origin, unchanged)
scripts/run_guarded.sh                5e34e455b5193e89
scripts/check_mc_field_plain.py       e0740e47f39a5e74   -> recorded in the landing note (this card's only edit)
probes/MC_FIELD_EXAMPLE_ARM_ARCHIVE_20261017.json  edf414eaa1a8997f
probes/MC_POPULATION_20261017-184752.json          9335b2a39b4d1d38
probes/MC_LEGEND_AB.json                           029244b6e5232a6b
the 22 coordinates, aggregate over sorted (path, sha256)   318739354497d7cf…   (full value in the landing note)
```

---

## LANDING NOTE, APPENDED 2026-10-19 — THE READING LANDED, AND TWO OF THIS CARD'S OWN INSTRUMENTS WERE CORRECTED BY THE GOVERNED RUN

**The edit landed in the commit that carries this note (`scripts/check_mc_field_plain.py` `e0740e47f39a5e74` ->
`186088accaa409aa`).** §2a-§2c are as pre-registered: the docstring's claim about the driver was corrected, the
one failing assertion became a READING plus three mutation checks, and two controls were added to [6b]. The
entrant block is untouched (§7's fence, measured below).

**THE TWO COUNTS, BOTH TAKEN UNDER THE GUARD AND BOTH READ FROM THE UNIT'S OWN LOG:**

```
mc-driver-field-pre   108/111, 3 CHECKS FAILED, rc 1    the same 108/111 as logs/mc-field-check-ocho.out, and
                                                        the same failing line at the same address (23-25)
mc-driver-field-post2 113/115, 2 CHECKS FAILED, rc 1    the driver failure is GONE, and the two that remain are
                                                        the two named findings: the entrant digest's
                                                        non-reproducibility, and Finding B's two cells
                                                        4018f0262498eb3e (all 22 records)  vs  3bd43eed4c6e41f3 (disk)
                                                        reading: INCONCLUSIVE FROM THE RECORD'S SIDE
mc-driver-probe-pre   3/7,  C3-C6 FAIL, rc 1            one indistinguishable driver failure in all three shadows
mc-driver-probe-post4 7/7,  C1-C7 PASS, rc 0
mc-driver-selftest-pre / -post   53/53, rc 0, before and after (the driver is not edited by this card)
```

**Run of record.** Four post-edit units exist because the governed run found defects in this card's own
instruments; each is named, with what it showed, in the corrections below. **`mc-driver-field-post2` and
`mc-driver-probe-post4` are the runs of record**; `-post` and `-post2`/`-post3` (probe) are the superseded ones
and are kept rather than deleted, because a correction with its counterfactual is worth more than a clean log:

```
mc-driver-probe-post   4/7   M1 109/115, 3 driver failures   <- the [6b] control was absolute   (correction 1)
mc-driver-probe-post2  4/7   M1 111/115, 2; M2 112/115, 0    <- D2's failure was unclassifiable (correction 2)
mc-driver-probe-post3  5/7   M1 111/115, 2; M2 112/115, 1    <- C4/C5 looked in the headline     (correction 3)
mc-driver-probe-post4  7/7   M1 111/115, 2; M2 112/115, 1    <- the run of record
```

### EVERY PREDICTION, DISCHARGED BY NAME — TWO CORRECTED, NONE TRIMMED

**P1 — HIT.** The probe's own git read returns exactly
`{b726188380ce681c, 4018f0262498eb3e, 3bd43eed4c6e41f3}`, the file on disk is the third, the 22 records carry
`4018f0262498eb3e`, and **22/22 pre-move records carry no `driver_digest` at all**. The premise is what the card
said it was.

**P2 — HIT.** Pre-edit: **3/7, C3-C6 FAIL, rc 1**, and the three shadow cabinets are indistinguishable — one
failure each, the same line, the same two digests:

```
M0 the field as published          got ['4018f0262498eb3e']                        want ['3bd43eed4c6e41f3']
M1 one record: deadbeefdeadbeef    got ['4018f0262498eb3e', 'deadbeefdeadbeef']    want ['3bd43eed4c6e41f3']
M2 one record: b726188380ce681c    got ['4018f0262498eb3e', 'b726188380ce681c']    want ['3bd43eed4c6e41f3']
```

`ids()` quotes a VALUE and never a COORDINATE, so the published field sits on the same line as both mutations.
That is the defect as a measurement, and it is what the card asked to be made sayable.

**P3 — HIT.** `mc-driver-field-post2`: the three driver checks PASS, **zero** driver failures, and the reading
prints `READING the records name ['4018f0262498eb3e'] the driver ON DISK is 3bd43eed4c6e41f3 committed versions
['3bd43eed4c6e41f3', '4018f0262498eb3e', 'b726188380ce681c']` followed by
`INCONCLUSIVE FROM THE RECORD'S SIDE, AND THIS IS NOT A FAILURE OF THE RECORD.` and the consequence paragraph.
The same output appears in the unmutated shadow (probe M0, 113/115, 0 driver failures).

**P4 — HIT, AFTER ONE CORRECTION OF THE PROBE'S OWN EXPECTATION (correction 3).** Post-edit:
`deadbeefdeadbeef` in one record fails **two** driver checks and both name
`probes/MC_Qwen3-1.7B-Q8_0_mc_01_one_shot.json` and the value; `b726188380ce681c` in one record fails
**exactly one**, naming the coordinate (it IS a committed driver, so only the split check can catch it). The
probe is **7/7, rc 0**.

**P5 — HIT, AFTER ONE CORRECTION OF THE IN-CHECKER CONTROL (correction 1).** Shadows from the run of record:
**M0 113/115 (0 driver failures), M1 111/115 (2), M2 112/115 (1)** — value for value what §3 P5 predicted. The
field run: **113/115**, total **115** in every run.

**P6 — HIT, MEASURED.** (a) **The entrant block is byte-identical**: its sha256 is
`dbf8b477959d3e59…` in both versions (20 lines each), taken of the block from
`# THE ENTRANT IS THE SUBJECT OF THE MEASUREMENT` through the `MEASURED, AND IT IS A FINDING ABOUT THE PRE-MOVE
RECORDS` print — a **hash of the block, not a line number**, so `t_77f73033` will find it where it left it.
(b) Sections `[1]`, `[2]`, `[4]`, `[5]`, `[7]`, `[8]` are **identical verdict line for verdict line** between
`mc-driver-field-pre` and `mc-driver-field-post2` (3, 3, 6, 88, 2, 0 lines respectively; compared by the strings,
not by count). Section `[3]` moved exactly as designed: the one failing driver assertion → three passing checks,
and `[6b]` is new with two passing controls.

**P7 — HIT, READ BACK.** The 22 coordinates' aggregate over sorted `(path, sha256)` is
`318739354497d7cfcf6c30c3d189bf08987227d478264f7108e778b8923bab9a` **before and after**; `git status
--porcelain probes/ results/` is empty after every run (and after the probe's three shadow runs);
`MC_DECLARATION.md` `2ada03ee2ad1f60b`, `missile_command.py` `eb5ed36591b300e6`, `missile_command_run.py`
`3bd43eed4c6e41f3`, `MC_FIELD_PLAIN.md` `d991c234024ce2e7`, `PREREG_mc_field_plain.md` `e40ac17826d2f87a`, the
archive `edf414eaa1a8997f`, the population artifact `9335b2a39b4d1d38`, `MC_LEGEND_AB.json`
`029244b6e5232a6b`, `PREREG_mc_ab_arm_names.md` `3f670a15e8e9cb4e`, `scripts/run_guarded.sh` `5e34e455b5193e89`,
both levels `ab101ca955c1c853` / `327d2157bd0b8a83` and `PREREG_missile_command.md` `01548e9a866df03e` — **all
unmoved**. The driver's `--self-test` is **53/53** on both sides.

**P8 — HIT, WITH THE COST PAID WHERE IT WAS NAMED.** `scripts/check_mc_field_plain.py` `e0740e47f39a5e74` ->
**`186088accaa409aa`**; `scripts/probe_mc_driver_digest.py` `1007f3e53224a3e2` (as committed) ->
**`c592d45e1b7d1e03`** with the two expectation corrections below and nothing else; this file `8a3fb91e4188bf68`
(as committed) -> the digest of the version carrying this note. `MC_FIELD_PLAIN.md` is **not touched**
(`d991c234024ce2e7`), so its *"111 checks"* (`:11`) and `PREREG_mc_field_plain.md:168`'s expectation remain what
they were on the day they were written: **the total is 115 now, and the place to learn that is the checker's
own last line and this note.** A reader who counts three failures in `logs/mc-field-check-ocho.out` and two in
`logs/mc-driver-field-post2.out` is looking at one cause removed and nothing else moved.

### CORRECTIONS — ALL THREE FOUND BY THE GOVERNED RUN, EACH RECORDED WITH ITS COUNTERFACTUAL

**1. THE IN-CHECKER CONTROL [6b] WAS WRITTEN WITH AN ABSOLUTE EXPECTATION, AND THE SHADOW CABINETS CAUGHT IT.**
Its first version expected `[(cells[0], 'deadbeefdeadbeef')]` — correct on a sound field, **wrong on a tree whose
field is itself mutated**: in the probe's M1 it fired a SECOND time, reporting the field's real mutation beside
its own demo mutation. `mc-driver-probe-post` **4/7**, M1 **109/115 with 3 driver failures**. **The checks
themselves were right** — their expectations are already relative (`[]`) — so what was corrected was the
CONTROL's expectation, now `base_missing + [(cells[0], the mutation)]`, i.e. relative to the field it is
demonstrating on, and the comment says why. After it, M1 is 111/115 with 2 driver failures, as P5 predicted.
**This is the control doing its job**: a demonstration that assumes a sound field is a demonstration that cannot
be trusted on a dirty one.

**2. D2's FAILURE WAS INVISIBLE TO ANYONE LOOKING FOR THE DIGEST'S NAME — SO THE CHECK WAS RENAMED.** Its first
wording was *"...and the 22 records name ONE of them between them"*, which does not contain `driver_digest`;
the probe classifies driver failures by that name, and `mc-driver-probe-post2` reported M2 as **112/115 with 0
driver failures** — a failure line the instrument could not see, which is the same defect the card exists to
remove, one level up. The rename states the property in the check's own name (*"name ONE `driver_digest` value
between them"*); **no expectation, threshold or result moved** — the check passed and failed on exactly the same
values before and after it (M2's 112/115 is 3 failures either way).

**3. THE PROBE'S C4/C5 LOOKED FOR THE COORDINATE IN THE WRONG PLACE.** The `FAIL` HEADLINE names the property;
the record is named on the `got` line beneath it. C4/C5 required the coordinate on the headline
(`mc-driver-probe-post3`: **5/7**, C4/C5 failing on `(False, True)` — **the value matched, the coordinate did**).
Corrected in the expectation, not in the checker and not in the reading: `(h + " " + d)`, i.e. "the failure
BLOCK names the record", which is what "the failure has an address" means.

**None of the three touches an expectation about the FIELD, a record, a count or a criterion.** All are defects
in this card's own instruments, found by running them, and named here rather than absorbed — the same discipline
as `PREREG_mc_field_plain.md`'s `52/52 -> 53/53` correction.

### NAMED GAPS, RATHER THAN LEFT TO BE FOUND

```
1  run_guarded.sh's `systemd-run` does NOT propagate the command's exit status (the parent card's appendix
   named the same gap). The governed runs capture it INSIDE the unit, `/bin/bash -c '...; echo "EXIT $?"'`, so
   every rc above is read from the log; the smoke run (mc-driver-probe-smoke) has no captured rc.
2  the driver-history read needs git. Run outside a git checkout the checker FAILS the D1 check with the error
   printed -- "cannot check" is never a pass -- and MC_DRIVER_HISTORY_REPO points it at another checkout.
3  the ONE way D1 can fail on a correct record: a run taken from an UNCOMMITTED driver. The remedy is to commit
   the driver, never to re-take the digest. Stated in the function's own docstring.
0  what is NOT done, and is deliberately not done here: the field is NOT re-taken (option 2 of the card, the
   Chair's); t_77f73033's entrant block is NOT touched (byte-identical, above); MC_FIELD_PLAIN.md is NOT edited;
   no criterion, verdict, record, archive or count is moved; `FAILED ON THIS POPULATION` stands as attached to
   C2 and C3.
```

### THE ARTIFACTS OF THIS CARD

```
scripts/check_mc_field_plain.py   186088accaa409aa   the reading + D1/D2/D3 + the [6b] controls
scripts/probe_mc_driver_digest.py c592d45e1b7d1e03   three shadow cabinets, model-free, outside the tree
logs/mc-driver-field-pre.out      108/111, 3 failures, rc 1      (the "before" of record)
logs/mc-driver-field-post2.out    113/115, 2 failures, rc 1      (the "after" of record)
logs/mc-driver-probe-pre.out      3/7,  C3-C6 FAIL, rc 1
logs/mc-driver-probe-post4.out    7/7,  C1-C7 PASS, rc 0
logs/mc-driver-probe-smoke.out / -post.out / -post2.out / -post3.out   the superseded runs, kept
logs/mc-driver-selftest-pre.out / -post.out   53/53 rc 0, both sides
```
