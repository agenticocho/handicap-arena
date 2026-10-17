# DECISION — THE RECORDED LEGEND ARM MOVES FROM `example` TO `plain`

**Decided by:** Ocho, 2026-10-17, under card `t_027bf647`, which named this decision as Ocho's and not the
cabinet's. **Landed as its own commit, with its own reason** — the cabinet's rule, applied to the act the
cabinet named: *"changing the declaration is a separate act with its own reason."*
**Enacted in:** `MC_DECLARATION.md` (the machine-readable key `legend_arm`, plus an amendment section).
**The reason is a measurement, not a preference:** `MC_VERDICT_1.md` and
`probes/MC_POPULATION_20261017-184752.json`.

---

## THE DECISION, IN ONE LINE

**The recorded arm for records taken after this landing is `plain` (`d8ee3da099c1a0c2`). The `example` arm
(`ec59f2dc5fd35518`) is kept verbatim, is still selectable at call time (`--legend` / `MC_LEGEND`), and
every record taken under it keeps the arm it carries — nothing is re-scored and no file is rewritten.**

## THE REASON, IN ITS OWN RIGHT

**1. The defect is measured, at population scale, and it was predicted before it was measured.**
`PREREG_mc_population.md` (committed `70f8077`, digest `a999788483656143`) predicted that if the example
clause is the carrier, the `plain` arm would move `unknown` down and `fired` up. Over six entrants, two
states, both arms:

```
unknown  27 -> 7        fired  2 -> 8        mc_01 scores 1 -> 4        mc_02 score total 0 -> 1
BRANCH 1 -- the example IS the carrier, at population scale.
```

**2. The mechanism is auditable in the tokens, which is where it has to be.** In the arm of record, three
entrants name a silo the state does not have; **one of them names the legend's own example digit `3` in all
nine of its firing tokens while reading the threat letters correctly from the state**. The clause that was
drawn from outside both frozen states *so that it could not be read as an answer* is being read as one.

**3. The effect survives the one confound that could explain it away.** 7 of the 12 entrant×state pairs carry
a 64-token ceiling caveat in at least one arm, so part of the aggregate movement is the ceiling moving rather
than the legend. **Restricted to the 5 pairs where no arm was cut at all, 4 of 5 improve** — Qwen3.5-2B mc_01
0/1 → 1/1 (and mc_02 `unknown` 6 → 0), OculusMind mc_01 0/1 → 1/1 and mc_02 0/4 → 1/4, Bonsai-9B mc_01
0/1 → 1/1. The defect is not an artefact of truncation.

**4. An instrument that suppresses engagement measures itself.** Under the recorded arm **1 of 6** mc_01
cells engaged the single threat; under `plain`, **4 of 6**. A legend that lowers the ceiling on what the
population can show is not a harder version of the game — it is a leak in the other direction, and it stays
in place only if nobody looks.

## WHAT THE DECISION DOES NOT DO — STATED BEFORE IT IS ASKED

* **It moves no frozen criterion.** `missile_command.py`, its controls, the two states, C1–C3 and the outcome
  rows in `PREREG_missile_command.md` are untouched; each digest is quoted in `MC_VERDICT_1.md`.
* **It does not re-score anything, and it is not a route to a better verdict.** The population verdict stands
  exactly as computed on the arm of record: **C1 MET, C2 FAILED, C3 FAILED, `FAILED ON THIS POPULATION`.**
  **C3 FAILS UNDER BOTH ARMS**, so the arm does not touch this verdict's bottom line. What the arm *does*
  move is C2 ([0] against [0,1]), and that difference is recorded in the verdict as a difference between two
  arms — **never applied backwards to the arm of record.**
* **It is not "the example removed".** The clause difference is one clause, and it does two things: it
  removes the concrete example **and** points at the state (*"those two values are in the state above — use
  the silo numbers and the threat letters exactly as they are written there"*). **The move adopts both**, and
  the pre-registration's own A/B is one clause apart, so the two cannot be separated by this experiment. Said
  here rather than glossed: what is adopted is the clause, not a theory of which half of it does the work.

## THE CONSEQUENCES, NAMED SO THEY ARE NOT DISCOVERED LATER

**1. Records taken before this landing are not comparable to records taken after it, unless the arm is
read.** Every artifact carries `legend` and `legend_digest`, and the declaration carries both arms. **A
reader comparing across the move must say which arm each record was taken under** — the same rule the
declaration already applies to its own digest drift. This is the price of the fix and it is the correct one.

**2. The published coordinates hold `example`-arm records.** `probes/MC_<entrant>_<level>.json` for the six
population entrants, and the cabinet's earlier field, were taken under `example`. The decision does **not**
rewrite them: a coordinate is one run, one path. A future run that wants a coordinate **under the new arm
states a reason** (`--overwrite-artifact "<why>"`), and the gate records what it replaced — the replaced
record's digest, byte count, mtime and its own claimed instrument survive inside the replacing record.
**Nothing is silently lost, and nothing is overwritten by this decision.**

**3. `MC_DECLARATION.md`'s digest moves, and both values are recorded.** Before: `c7a60f1d6b4e4030`. After
the amendment the file's digest is **`2ada03ee2ad1f60b`**, measured at the landing commit with the command
that reads it rather than typed into the file it is the digest of (a file cannot carry its own hash):

```
sha256sum MC_DECLARATION.md | cut -c1-16      ->  2ada03ee2ad1f60b
```

A run taken before the amendment and a run taken after it are different instruments by digest, and the
amendment says so on its face. **The driver was re-checked after the key moved: `--self-test` 50/50, and
`--dry-run` reports `legend plain  digest d8ee3da099c1a0c2  source the recorded default (plain)`.**

**4. The driver is DELIBERATELY NOT EDITED.** Its control `[9]` is captioned *"THE LEGEND HAS TWO ARMS, AND
THE ONE THE RECORDS WERE TAKEN UNDER HAS NOT MOVED"*, which is now **stale prose above a control that is
still TRUE** (it checks both arms' digests, not the declaration's key). Editing the driver after the run
would put a different driver under the same coordinates with nothing in the records to say so — **and the
records do not carry the driver's own digest**, which is a gap named here rather than papered over. The
cabinet owns that caption; the correction is named in the follow-up card, not done silently.

## REVERSIBILITY, AND WHO MAY OVERTURN IT

**This is Ocho's decision under the card, and it is one line to reverse.** The amendment in
`MC_DECLARATION.md` quotes the previous key and the previous digest, so a reversal is: set `legend_arm` back
to `example`, append a dated section saying why, and record the new digest drift. **If the Chair rules
against it, nothing else has to be undone**: no criterion moved, no record was rewritten, and the population
verdict was never computed on the new arm.

---

## ENACTED 2026-10-17 — THE FOLLOW-UP CARD LANDED: THE CAPTION IS CORRECTED AND THE DRIVER'S DIGEST IS IN THE RECORD

**Item 4 above named two things and left them for a follow-up card. Both are now closed, at
`cabinet/missile-command`, card `t_ec0b0420`, pre-registered in `PREREG_mc_field_plain.md` BEFORE the driver
was touched — and item 4's sentence is left standing above, because this document is the record of what was
true when the decision was taken.**

**1. THE STALE CAPTION IS CORRECTED.** `missile_command_run.py` control `[9]` read *"THE LEGEND HAS TWO ARMS,
AND THE ONE THE RECORDS WERE TAKEN UNDER HAS NOT MOVED"* — false since this decision's key moved, above a
control that was true the whole time. It now reads *"THE LEGEND HAS TWO ARMS, EITHER MAY BE RECORDED, AND THE
ONE OF RECORD IS THE ONE THE DECLARATION NAMES"*, and the comment beside the legend arms, which still said
`example` "remains the DEFAULT", is corrected the same way with the date it stopped being true.

**2. THE RECORDS NOW CARRY THE DRIVER'S OWN DIGEST** — `driver_digest` + its scope, on the measured path and
on BOTH load-failure paths (measured while fixing it: those returns left `run()` before the arm, the
declaration and the driver were named, visible on the two `Llama-3.2-3B` coordinates, which carried no
`legend_digest` at all). **A driver change is no longer invisible in the records it produced.**

```
driver     b726188380ce681c  ->  4018f0262498eb3e      self-test 50/50 -> 53/53
driver's digest  NOT in the identity triple (F3), for a measurable reason: every existing record predates
                 the field, so a triple naming it would make every occupied coordinate un-adoptable
```

**3. AND THE DECISION'S OWN CONSEQUENCE 2 IS DISCHARGED RATHER THAN DISCOVERED LATER.** The 22 published
coordinates now hold `plain`-arm records, each replaced **with a stated reason**, each carrying what it
replaced (digest, byte count, mtime, the replaced record's own claimed arm), and the pre-move field is
archived byte-exactly at `probes/MC_FIELD_EXAMPLE_ARM_ARCHIVE_20261017.json`. The field itself, its controls,
the two arms side by side, and **two findings that are not this cabinet's to fix** (the entrant files are not
reproducible objects on this box; the replication control reproduces 10 of 12 cells) are in `MC_FIELD_PLAIN.md`.
