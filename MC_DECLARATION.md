# MC_DECLARATION — the missile-command cabinet's declaration, in one file, READ BY THE DRIVER

**Owner:** `@missile-command` (this cabinet) · **Read by:** `missile_command_run.py` at import, which
**REFUSES TO RUN IF THE REASONING ARM IS NOT DECLARED HERE** — a default nobody chose is not evidence, so
the arm is not defaulted anywhere in the driver.

## The machine-readable block

The lines below are the ones the driver parses. Format, key and value on one line, first occurrence wins —
the same shape `FROZEN_PROMPT.txt` uses for `prompt_digest`. **Adding prose above or below this block is
safe; removing a key is a refusal.**

cabinet missile-command
reasoning_arm off
reasoning_declared_in PREREG_sokoban.md (the cabinet-wide rule, which names MISSILE COMMAND explicitly) + CABINET_STRUCTURE.md (the standing rule for every cabinet)
reasoning_rationale This cabinet's answer is TWO CHARACTERS -- a silo number and a threat letter -- which is the short-answer class the setting was decided for: a thinking model puts its deliberation where the answer belongs, the ceiling eats it, and the measured result is a turn with no answer at all (2314 tokens, no commitment, on the same weights where thinking OFF held the format). The setting is off; the override is an experiment arm and the record says which one it is.
protocol step_locked
clock none -- the state's own `tick` integer, advanced by exactly one per action
artifact probes/MC_<entrant>_<level>.json
legend_arm plain
legend_arm_note THE RECORDED ARM MOVED TO `plain` ON 2026-10-17 (see the amendment below; before that date it was `example`, digest ec59f2dc5fd35518). BOTH arms are kept VERBATIM and both are selectable at call time via --legend/MC_LEGEND; the driver records which arm a record was taken under and digests both, so a reader can sort the records taken either side of the move. `example` remains the arm of the population run and of every record taken before this date.
legend_arms_registered example ec59f2dc5fd35518 plain d8ee3da099c1a0c2

## 3. AMENDMENT 2026-10-17 — THE LEGEND ARMS, AND THE DIGEST THAT MOVED (RECORDED, NOT HIDDEN)

**This file was amended after the first entrant paths were driven.** Records taken before the amendment
carry `declaration_digest 41690b0e71522ca4`; records taken after it carry the digest of the version that
carries this paragraph. **The declaration is part of the instrument, so a reader comparing two records must
say which version each was taken under** — the same rule the floor above applies to `sokoban.py`.

**What the amendment adds, and why it is not a criterion change:** the LEGEND (the prompt) is this
cabinet's own instrument, and it now has TWO ARMS because the first one was MEASURED to hand over a value.
Driven for the first time on 2026-10-17, three entrants answered with the legend's own example silo digit
(`3`) in every firing token — `3W`×4 (granite), `3P`×3 and `3X 3X 3X 3Q 3P 3T` (Qwen3.5-2B) — while
reading the threat letters correctly from the state. **The example was drawn from outside both frozen
states so it could not be read as an answer; it supplied one anyway.**

**The A/B is pre-registered in `PREREG_mc_legend_ab.md` (digest `49784e02849a401f`) BEFORE the second arm
was ever run, with its prediction and its three branches, and the result is
`probes/MC_LEGEND_AB.json`.** Both arms are kept verbatim; the recorded arm does not move because an
experiment ran.

**THE SIMULATOR, THE TWO STATES, THE CRITERIA AND THE OUTCOME ROWS IN `PREREG_missile_command.md` ARE
UNTOUCHED** (digest `01548e9a866df03e`, unchanged), and so is `missile_command.py` (digest
`eb5ed36591b3`). Nothing here moves a frozen criterion.

### AND THE LABEL CHANGED WHILE THE DIGEST DID NOT — RECORDED, BECAUSE BOTH ARE IN THE RECORDS

**The first cells were taken before the arms had names.** They carry `"legend": "MC_MISSILE_COMMAND_PLAIN"`
— a string this driver no longer emits — beside `"legend_digest": "ec59f2dc5fd35518"`, **and that digest IS
the `example` arm**: the label was a constant's name and the digest is the identity. **A label is for
reading and a digest is for checking**, so the old records stay exactly as they were taken (one run, one
path, and the gate refuses to replace them without a reason) and the mapping is stated here instead:
`MC_MISSILE_COMMAND_PLAIN` (legacy label) = `example` (arm) = `ec59f2dc5fd35518`.

## 1. THE INTERFACE DECISION — AND WHY IT IS NOT A CRITERION CHANGE

**The card for this cabinet asked it to choose between (a) step-locking the 3-second real-time timers and
scoring it as a turn-based game, or (b) driving it live and scoring it as a timed game, because the
published survey classified Missile Command as KEYS/REALTIME (mouse) with canvas `click` → (x,y) actions.**

**(a) IS ALREADY WHAT THE FROZEN ARTIFACT IS, and it is MEASURED rather than chosen:**

```
missile_command.py   imports `sys` AND NOTHING ELSE -- no time, no sleep, no monotonic, no clock
                     (re-measured at every run by `clock_audit()`; the finding travels in the record)
the only clock       the STATE's own `tick` integer, advanced by exactly one per action
                     play():  for i, tok in enumerate(actions):  tick = st["tick"] + i
the frozen PREREG    "And the coordinate rule: no time limit. The cap is the budget, not the clock."
                     (PREREG_missile_command.md, FROZEN section)
```

**SO THERE IS NO TIMER TO STEP-LOCK AND NO LIVE MODE TO DRIVE.** The play mode is turn-based **by
construction**, not by a setting this cabinet chose — and **no frozen criterion moves**, which matters
because a criterion change is not this cabinet's to make.

**AND THE KEYS/REALTIME SENTENCE IS AN EXTERNAL CLAIM THE FROZEN ARTIFACT DOES NOT CARRY.** A repo-wide
grep across all four trees (`ocho_arena`, `cabinet/sokoban`, `cabinet/missile-command`, `cabinet/zork`) for
`REALTIME`, `real-time`, `mouse`, `timed` and `KEYS` returns **no such classification**: `GAMES.md` does not
contain the word `mouse` at all, `handicap-arena-technical-reference.pdf` contains no occurrence of
`missile`, and no document in any tree names a 3-second timer. **It is a classification of the ARCADE GAME,
not of this cabinet's frozen protocol**, and it is recorded here as an external claim rather than silently
inherited. The frozen protocol — the thing a score can be about — is the line-oriented step-locked state.

**AND THE ONE THING THE CARD SAYS THAT DOES BITE IS KEPT: a reasoning model will be poor at a click-target
game, and that would be a finding rather than a defect. Here the prediction is the same shape and it is
still unmeasured:** a model that cannot emit two characters cannot play, and that shows up as `malformed`
counts and a zero — a measurement, not a defect.

## 2. WHAT THE SCORE MEANS UNDER THIS PLAY MODE

**`cities_surviving`, a count, out of `cities_total`, produced by the frozen simulator's `play()` — and the
trace is a sufficient statistic for it** (GAME_CONTRACT: *the scored outcome can be recomputed from the
recorded state alone*). The driver re-derives the score and every screen from `(state_text, tokens)` after
the run and **reports the re-derivation as a control** — `sufficiency_check` in the record — so the claim
is checkable rather than asserted. The entrant's answer is not part of the state: the state is the frozen
board, and the action stream is recorded beside it.

## 3. TOUCHING NOTHING SHARED

This file is new and belongs to this cabinet; **no shared file is edited by it, and none is edited by the
driver.** The frozen artifacts cited above are named and digested, never modified:

```
missile_command.py        eb5ed36591b3   (== the digest the sanctioned demo page records, so this tree's
                                          instrument is the one the page was built against)
PREREG_missile_command.md 01548e9a866df03e   (NOT edited: the arm is declared in THIS file instead)
levels/mc_01_one_shot.txt ab101ca955c1c853
levels/mc_02_scarcity.txt 327d2157bd0b8a83
```

**`answer_reader.py` and `vram_holder.py` are NOT carried by this tree.** RULING 79 says the reader of
record is imported and never reimplemented, so the driver loads them **from the shared tree** and records
the **path and digest of the file that actually answered** — one definition, imported, identified. A second
copy in this cabinet would be the one-definition defect.

## 4. AMENDMENT 2026-10-17 (THE SECOND, LATER THE SAME DAY) — THE RECORDED ARM MOVES TO `plain`

**Decided by Ocho, for the card `t_027bf647`, which named this decision as Ocho's and not this cabinet's.
Enacted HERE, in the machine-readable key above, as its own commit with its own reason. The full reasoning
is `DECISION_mc_legend_arm.md`; the measurement behind it is `MC_VERDICT_1.md` and
`probes/MC_POPULATION_20261017-184752.json`.**

```
legend_arm   example   ->   plain        (example ec59f2dc5fd35518 remains on disk, verbatim, and selectable)
this file    c7a60f1d6b4e4030   ->   the digest of the version carrying this paragraph
```

**THE REASON, AND IT IS A MEASUREMENT RATHER THAN A PREFERENCE.** `PREREG_mc_population.md` (`70f8077`,
digest `a999788483656143`) predicted, BEFORE the second arm ran, that if the example clause is the carrier
the `plain` arm would move `unknown` down and `fired` up. Over six entrants and two states: **`unknown`
27 → 7, `fired` 2 → 8, mc_01 engagement 1 of 6 cells → 4 of 6, mc_02 score total 0 → 1 — BRANCH 1 as
pre-registered.** The mechanism is in the tokens: **one entrant names the legend's own example digit `3` in
all nine of its firing tokens while reading the threat letters correctly from the state.** And the effect
survives the confound that could explain it away: of the 5 entrant×state pairs where neither arm was cut at
the ceiling, **4 improved**.

**WHAT THIS DOES NOT DO.** No frozen criterion moves (`missile_command.py` `eb5ed36591b3`, the two states,
C1–C3 and the outcome rows in `PREREG_missile_command.md` `01548e9a866df03e` are untouched). **No record is
re-scored:** the population verdict stands as computed on the arm of record — **C1 MET, C2 FAILED, C3
FAILED, `FAILED ON THIS POPULATION`** — and **C3 fails under BOTH arms**, so this move is not a route to a
better verdict. C2's outcome differs between the arms ([0] against [0,1]) and that difference is recorded in
the verdict as a difference; it is **not** applied backwards.

**AND THE TWO CONSEQUENCES A READER NEEDS.** (1) Records taken before this paragraph and after it are
**different instruments by digest**; each artifact carries `legend` + `legend_digest`, so they can be sorted,
and a comparison across the move must say which arm each side was taken under. (2) **The published
coordinates hold `example`-arm records** (this cabinet's earlier field, and the six population entrants).
They are not rewritten: one run, one path. A later run that wants a coordinate under the new arm **states a
reason** and the gate records what it replaced, digest and claimed instrument included.

**`example` IS NOT WITHDRAWN.** It is the arm every record before this date was taken under — including all
twelve cells of the population run — it stays byte-identical on disk, and it is still reachable with
`--legend example` / `MC_LEGEND=example`.
