# PRE-REGISTRATION — THE INSTRUMENT FIX THAT PRECEDES THE FIELD RE-TAKE, AND THE FIELD RE-TAKE UNDER THE ARM THE CABINET DECLARES

**Written BEFORE both acts it describes**: before `missile_command_run.py` is edited, and before the first
entrant moves on this field. RULING 79's shape one layer out — the change, the field, the reason string and
the prediction are fixed here, so neither act can be read as support for a claim whatever it shows.

**Owner of this instrument:** `@missile-command` (this cabinet), under card `t_ec0b0420`. **This run computes
no criterion and issues no verdict.** C1–C3, the outcome rows and the population verdict are Ocho's
(`PREREG_mc_population.md`, `MC_VERDICT_1.md`); *a cabinet agent never scores its own event*
(`CABINET_STRUCTURE.md` rule 4). The counters this run measures are reported as counters.

---

## THE INPUTS, WITH DIGESTS, AS READ WHEN THIS FILE WAS COMMITTED

```
missile_command.py                        eb5ed36591b300e6   the frozen simulator -- UNTOUCHED
PREREG_missile_command.md                 01548e9a866df03e   the frozen criteria + outcome rows -- UNTOUCHED
levels/mc_01_one_shot.txt                 ab101ca955c1c853   state 01, the floor -- UNTOUCHED
levels/mc_02_scarcity.txt                 327d2157bd0b8a83   state 02, the instrument -- UNTOUCHED
MC_DECLARATION.md                         2ada03ee2ad1f60b   legend_arm plain (amended 2026-10-17)
missile_command_run.py                    b726188380ce681c   the driver BEFORE this card's fix
scripts/run_guarded.sh                    5e34e455b5193e89   the ceiling every cell goes through (24G/32G/1G)
PREREG_mc_population.md                   cfedf8b7f5e7d57f   the population pre-registration AS IT STANDS NOW
probes/MC_POPULATION_20261017-184752.json 9335b2a39b4d1d38   the population run of record
probes/MC_LEGEND_AB.json                  029244b6e5232a6b   the legend A/B
cabinet/missile-command @ 3d7ce30
```

**THE FROZEN ARTIFACTS ARE NAMED AND DIGESTED, NEVER MODIFIED**, and no frozen criterion moves in either act.

---

## 1. THE FIELD — DERIVED FROM THE COORDINATES ON DISK, NOT TYPED

**The field is every entrant that holds a published coordinate in this cabinet.** The rule, frozen here,
applied mechanically:

```
1  every file matching probes/MC_<entrant>_<level>.json  where <level> is one of this cabinet's two states
   -- i.e. every PER-CELL RECORD. The run artifacts in probes/ (MC_POPULATION_*.json, MC_LEGEND_AB.json,
   SOKOBAN_*.json, COST_PROBE_WIDE.json) are NOT cells and are excluded by the same test.
2  NOBODY PICKS AN ENTRANT BY NAME: the field is whichever entrants the coordinates hold.
3  a cell that does not LOAD is an ATTEMPT, not a measurement -- it stays in the field and is reported as
   an attempt.
4  THE PRE-MOVE RECORD OF EVERY CELL IS ARCHIVED BEFORE THE FIRST REPLACEMENT (section 5).
```

**THE SAMPLE THE RULE SELECTS: 11 entrants × 2 states = 22 cells.** Ten entrants hold measured records and one
(`Llama-3.2-3B-Instruct-Q4_K_M`) holds two ATTEMPTS — records whose own text is *"the DEVICE has no room --
a TENANCY condition, not a model condition"*.

```
0.214 GB  LFM2-350M-Extract-Q4_K_M                       measured
1.188 GB  Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0             measured   ternary -> THE PRISM FORK
1.248 GB  Qwen3.5-2B-UD-Q4_K_XL                          measured
1.681 GB  granite-3.3-2b-instruct-critical-thinking.Q5_K_M  measured
1.708 GB  Qwen3-1.7B-Q8_0                                measured
1.881 GB  Llama-3.2-3B-Instruct-Q4_K_M                   ATTEMPT (device tenancy)
2.229 GB  Phi-3.5-mini-instruct-Q4_K_M                   measured
2.492 GB  Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0             measured   ternary -> THE PRISM FORK
4.841 GB  OculusMind-ToolCall-8B-v2.i1-Q4_K_M            measured
5.440 GB  MiMo-V2.6-Distill-Qwen-9B-Q4_K_M               measured
7.517 GB  Mellum2.1-12B-A2.5B-Thinking-Q4_K_M            measured
```
*(file sizes divided by 2^30; the population pre-registration quotes the same files in decimal GB — its
8.071 GB is this 7.517 GiB, its 1.340 GB is this 1.248 GiB.)*

**n = 1 PER CELL, AND THE COST IS DECLARED.** One model per cell, one state set, the shapes the population
run's own scope used. 22 cells, CPU-only (`-ngl 0`), 0.214–7.517 GB, bounded at tens of minutes on this box.
**A second run of the same cell would be a rate rather than a reading, so none is taken.**

## 2. THE ARM, AND WHY NO `--legend` FLAG IS PASSED

**The arm is `plain` (`d8ee3da099c1a0c2`), and the run does not name it on the command line.** The driver
reads `legend_arm` from `MC_DECLARATION.md` and refuses to run if it is undeclared, so these cells carry
`legend_source` = *"the recorded default (plain)"* — the arm the cabinet declares, not an arm a caller chose
one cell at a time. **That is the whole point of the re-take**: the coordinates should hold the declared
instrument because the declaration says so.

**BOTH ARMS STAY VERBATIM IN THE DRIVER AND `example` STAYS SELECTABLE** (`--legend example` / `MC_LEGEND`);
nothing is withdrawn and no frozen criterion moves.

## 3. THE REASON THE GATE WILL RECORD, QUOTED VERBATIM

**One run, one path.** Every one of the 22 coordinates already holds a record, so every one of the 22 runs
goes past the artifact gate with a reason and the gate writes what it replaced into the record that replaces
it. **The reason string, fixed here before the first run:**

```
THE COORDINATE HELD AN example-ARM RECORD AND THE DECLARATION NOW NAMES plain (MC_DECLARATION.md
2ada03ee2ad1f60b, DECISION_mc_legend_arm.md, card t_ec0b0420): the cabinet's field is re-taken under the arm
it declares. The replaced record's exact bytes are archived in
probes/MC_FIELD_EXAMPLE_ARM_ARCHIVE_20261017.json with their sha256, so the replacement is recorded rather
than silent.
```

**A SILENT OVERWRITE IS THE DEFECT THIS MECHANISM EXISTS TO PREVENT; A REASONED REPLACEMENT IS THE DESIGNED
PATH** (`DECISION_mc_legend_arm.md`, consequence 2 — the act this card enacts). What the gate preserves in
the replacing record is the replaced record's sha256, byte count, mtime, and what it claimed about its own
instrument; the record's own bytes are preserved by the archive beside it.

## 4. THE INSTRUMENT FIX — PRE-REGISTERED BEFORE IT IS MADE

**F1 — CONTROL `[9]`'s CAPTION IS STALE PROSE ABOVE A CONTROL THAT IS STILL TRUE.** The caption reads *"THE
LEGEND HAS TWO ARMS, AND THE ONE THE RECORDS WERE TAKEN UNDER HAS NOT MOVED"*, and that sentence stopped
being true when the recorded arm moved to `plain` — while the control under it (which compares the driver's
`LEGEND_DEFAULT` against the declaration's key and digests both arms) was true the whole time. **The caption
is replaced with the claim the control actually checks:**

```
[9] THE LEGEND HAS TWO ARMS, EITHER MAY BE RECORDED, AND THE ONE OF RECORD IS THE ONE THE DECLARATION NAMES
```

**AND THE TWO COMMENT SENTENCES BESIDE THE ARMS ARE CORRECTED THE SAME WAY** — `example` is no longer the
default (it is read from the declaration), so the sentence *"`example` remains the DEFAULT"* is marked with
the date it stopped being true instead of being left to read as current. **A caption is not a check**: no
control's value can change from F1, and the control count does not move for it.

**F2 — THE DRIVER'S OWN DIGEST GOES INTO THE RECORD, ON ALL THREE PATHS.** Every other input is digested in
the record (simulator, states, legend, entrant, server binary, reader, declaration) and **the driver is not**
— so a change to `missile_command_run.py` is currently invisible in the records it produced, which is exactly
the defect the last landing named. The fix:

```
driver_digest        sha256 of missile_command_run.py, first 16 hex, from ONE function
driver_digest_scope  what it is a digest of, and why the driver is part of the instrument
```

**AND IT GOES IN ON ALL THREE RETURN PATHS, NOT ONLY THE HAPPY ONE.** The two load-failure returns leave the
function before the legend, the declaration and the driver are named — **measured, in this tree, on the two
`Llama-3.2-3B` coordinates, which carry no `legend_digest` at all.** An ATTEMPT that cannot be sorted by the
arm it was attempted under is the same defect one path over, so the failure records carry the same instrument
block (arm, both arms' digests, simulator digest, driver digest, declaration file + digest). **Two new
controls are added for F2** (the driver is identified as its own instrument; and the record-building code
names every instrument digest the record is supposed to carry), taking the self-test from **50 to 52**.

**F3 — WHAT THIS FIX DOES NOT DO, WITH ITS REASON.** The identity triple the gate and the population runner's
adoption rule compare (`server_binary_digest`, `legend_digest`, `reasoning`) is **NOT** extended to include
the driver's digest. **The reason is measurable rather than cautious:** every record in this tree predates the
field, so `carried_identity()` returns `None` for `driver_digest` in all of them — a triple that names it
would make **every occupied coordinate un-adoptable (`never_started`)** for the population runner, including
the two cells it adopted on identity. That is a change to an instrument this cabinet does not own, so it is
**named here as an open consequence and not made.**

## 5. THE ARCHIVE — WHY IT EXISTS BEFORE THE FIRST REPLACEMENT

**Six of the eleven entrants' `example`-arm records exist nowhere else.** `probes/MC_POPULATION_…json` carries
the twelve cells of *its own* six entrants, and `probes/MC_LEGEND_AB.json` carries one entrant's two states;
`granite-3.3-2b`'s `example`-arm cell — the `3W`×4 / `unknown` 4 record that `MC_DECLARATION.md`'s amendment
and the driver's own comment quote as the A/B's motivation — exists **only** at its coordinate. **So the pre-move field is archived before it is replaced**,
at `probes/MC_FIELD_EXAMPLE_ARM_ARCHIVE_20261017.json`: per cell, the file's **exact bytes** (as text), its
sha256, byte count and mtime, and what it said about its own instrument.

**THE ARCHIVE IS CHECKABLE RATHER THAN TRUSTED**, three ways: (a) the sha256 of the archived bytes must equal
the sha256 the replacing record carries in `artifact_replaced`; (b) for the twelve cells the population run
also holds, the archived sha256 must equal that artifact's own `coordinate_sha256`, a digest taken by
**another instrument, a day-part earlier, before this card existed**; (c) the archive is a byte copy, so any
reader can diff the two arms cell by cell.

## 6. THE CONTROLS THIS RUN CARRIES

```
per cell      the driver's two equalities (every token produces exactly one outcome; every threat is
              destroyed, hit or spared) and sufficiency (score + every screen re-derive from
              (state_text, tokens)) -- CARRIED PER CELL, and reported cell by cell
the arm       legend == plain; legend_digest == d8ee3da099c1a0c2; declaration_digest == the digest of
              MC_DECLARATION.md ON DISK; driver_digest == the digest of missile_command_run.py ON DISK
              -- RE-DERIVED FROM THE FILES, not compared against itself in the record
the replace   every artifact_replaced.sha256 resolves to a cell of the archive, and hashes to it
replication   the twelve cells this field shares with the population artifact's `plain` arm must
              reproduce TOKEN-FOR-TOKEN: the fix in F1/F2 touches no prompt, no cap, no screen and no
              ceiling, so a disagreement is the finding (nondeterminism, or a fix that is not inert)
the checker   a MUTATED token stream must fail the cell equalities, so the checker itself can fail
```

## 7. THE PREDICTIONS, FIXED BEFORE EITHER ACT

```
P1  the self-test still passes, at 52/52, and --dry-run reports
    `legend plain  digest d8ee3da099c1a0c2  (arms {...}, source the recorded default (plain))`
P2  no measured number moves: for every cell this field shares with the population run's `plain` arm,
    the tokens reproduce exactly; for the other cells there is no previous reading to move
P3  all 22 records carry artifact_replaced (sha256 + bytes + mtime + the replaced record's own claimed
    instrument), legend plain, and the driver digest of the version that produced them
P4  the two Llama cells are ATTEMPTS again -- a device-tenancy condition is not an arm condition -- and
    now name the arm they were attempted under
```

**A DISAGREEMENT WITH P2 IS REPORTED AS ONE, NOT EXPLAINED AWAY**: the population run's own replication
control found this entrant path deterministic (4 cells, token-for-token), so a disagreement here would be
evidence about the fix or about determinism, and which one is the first thing the note must say.

## 8. WHAT THIS RUN IS NOT — THE CONSTRAINTS CARRIED FROM THE VERDICT

* **The population verdict is not re-scored and not re-scoped.** It stands exactly as computed on the arm of
  record (`FAILED ON THIS POPULATION` attached to C2 and C3), and **no criterion is read here at all.**
* **The upper tail (12–25 GB) was out of the population and stays out.** This field is the cabinet's
  coordinates, not a population rule, and nothing about it widens either.
* **`example` is not withdrawn** and every record taken under it keeps the arm it carries — the archive is
  what makes that checkable after the coordinates move.
* **Every record carries its arm, its declaration digest and its inputs** — the artifact already does; F2 adds
  the driver's own digest so the driver stops being the one input a reader cannot see.
* **No bare `python3`**: every cell goes through `scripts/run_guarded.sh`.
* **The published coordinates are replaced one run, one path, with a reason**, and the replaced records are
  archived rather than lost — **nothing is silently overwritten, and nothing is silently kept either.**

## 9. THE CONSEQUENCES, NAMED HERE SO THEY ARE NOT DISCOVERED LATER

**1. A reader comparing a record taken before 2026-10-17 with one taken after it must read the arm.** They
are different instruments by digest (declaration `c7a60f1d6b4e4030` → `2ada03ee2ad1f60b`; legend
`ec59f2dc5fd35518` → `d8ee3da099c1a0c2`; and now the driver, which F2 makes visible).

**2. `missile_command_population.py` pins its coordinate arm as a constant (`COORD_ARM = "example"`).** After
this re-take, a re-run of that runner would find the published coordinates occupied by `plain`-arm records and
the gate refusing them (it passes no reason) — recorded as `never_started`, not as a measurement. **That
runner and the population are Ocho's instruments (`PREREG_mc_population.md`), so it is named here and NOT
edited by this card.**

**3. The archive is a new file in `probes/`, and it is NOT a coordinate.** It is not one of the 22 cells, it
is never read by the driver, and it is not a second definition of anything: it is the pre-move field as it
was, with digests, so the two arms can be compared after the coordinates moved.
