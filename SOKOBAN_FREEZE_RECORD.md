# SOKOBAN FREEZE RECORD — A5. THE GRAMMAR, ITS IDENTITY, ITS EVIDENCE, AND THREE CONTRADICTIONS

**The gramar is frozen at `/home/chilly1/.hermes/workspace/SOKOBAN_READ_GRAMMAR.md`, 3730 bytes,
sha256 `6f4d72319ec6f87…`.** Read against what the run actually did, as instructed. **Three things in it did
not match the implementation, and one thing in it is now cited as evidence it does not carry.**

---

## 1. THE ONE THAT MATTERS MOST: §5 NOW CITES A MEASUREMENT, AND THE MEASUREMENT DOES NOT SAY WHAT §5 SAYS

**§5's rule as written:** *"a legend formatted as key-value pairs reads as a FORM to a model whose training is
schema-filling, and that model transcribes the prompt instead of playing."*

**THE MEASUREMENT, from the controlled A/B (n=3 per arm):**

```
new legend  solved 3/3   varied 3/3
old legend  solved 0/3   varied 0/3                       <- the legend fix is REAL and LARGE
not_an_action   OLD [0, 0]   NEW [0, 0]                   <- AND THE PREDICTED METRIC DID NOT MOVE
```

**SO THE RULE IS SUPPORTED AND THE STATED MECHANISM IS NOT — for the entrant the A/B measured.** The fix is
causally responsible for a change from *zero moves in eighty attempts* to *a solve*, and **it did so without
touching `not_an_action` at all.** **granite never produced an unreadable token. It produced a perfectly
readable one, `U`, forty times.** Its failure was **LOCKING ON THE FIRST LISTED CONTROL**, not transcribing a
form. **`not_an_action` was the wrong metric and the pre-registered branch table said so in advance; the run
landed in BRANCH 3, not BRANCH 1.**

**AND THE SCHEMA-FILLING MECHANISM IS REAL — FOR A DIFFERENT ENTRANT, WHERE THE FIX DOES NOT REACH IT:**

```
LFM2-350M-Extract   emits {"wall": "", "first_line": "U = up", ...}   not_an_action 40 -> 40
```

**Forty before the fix, forty after.** An extraction model echoes structure **whatever the legend says**,
because schema-filling is what it does. **So the legend change removed the invitation and did not change the
model — which is the correct outcome, and the opposite of "the fix repaired the schema-filling".**

**THEREFORE §5 NEEDS AMENDING TO SAY WHAT IS TRUE:**

```
TRUE AND MEASURED   the legend's FORMAT is a carrier defect that changed the task
                    (0/3 -> 3/3, repeated, with the arms provably different)
TRUE AND MEASURED   schema-filling is REAL but INTRINSIC to the extraction model, and the legend
                    change does NOT reach it (40 -> 40)
NOT ESTABLISHED     that the legend's format causes SCHEMA-FILLING. That is one entrant's failure mode
                    and not the mechanism of the 0/3 -> 3/3 result. The A/B varies the whole legend,
                    so it cannot separate the list format from the FIRST LINE label from the
                    key-value symbol line. A three-arm follow-up would, and has not been run.
```

**A FREEZE RECORD THAT CITES A MEASUREMENT MUST CITE THE ONE IT HAS.** Putting 3/3-against-0/3 beside
"schema-filling" would make a true number argue for a claim it does not support — **which is the exact defect
this project has spent the week removing, one layer up.**

## 2. THREE CONTRADICTIONS BETWEEN THE GRAMMAR AND THE RUNNER

**§4 — "zero rule: enforced, not described". IT WAS DESCRIBED.** `sokoban_batch.py` returned 0 whatever
happened; a run that measured nothing printed ordinary output and exited success. **NOW ENFORCED: exit 3, with
the error printed, verified by pointing the population at an empty directory.**
`A RULE THAT IS DESCRIBED RATHER THAN ENFORCED IS A RESOLUTION`, and the grammar said so in its own words.

**§4 — the NAME. The grammar says `never_started`; the runner said `did_not_load`.** Two names for one state is
how a format field and its reader drift apart, and **A7 makes these format fields, so the names must be the
grammar's.** **ALIGNED to `never_started`.**

**§6 — "levels … sha256 with the run" and "host recorded per bundle, WITH the host's hardware state". NEITHER
WAS IN THE RECORD.** The run recorded the entrant, the level's *name*, and the counters. **A result whose
inputs do not travel with it is unattributable** — the same lesson as FINDING 020, where a missing legend
digest cost an A/B and a repeat test to recover a fact that should have been on the first line of the file.
**NOW CARRIED:** level digests, the simulator digest, and the host with its hardware state.

```
grammar        86251be3d717d3b5…      the instrument's own text
sokoban.py     00996929972b9483…     the simulator (§6: self-test is the contract)
01_one_push    db6ca59655f0d7d1…     the level, as an INPUT with a digest
02_two_boxes   7549657f1768607c…     the level, as an INPUT with a digest
levels/03_the_corner_waiting   77d18407a001da292b2f1dcf8054ed40ddc2038563f23b96861a362c78cf23d6
```

**RE-FROZEN 2026-10-14.** `sokoban.py` advanced `186f561f…` -> `7134c3e8fc59fe02…` when the ruled fixes
for this cabinet landed on `main` and were merged into `cabinet/sokoban`. The pin above is the CURRENT
enforcer, a precondition for any future run; the 2026-10-10 run was produced under `186f561f…`
and carries that digest in its own artifact, so nothing above is rewritten, only superseded forward.
`SOKOBAN_CONFORMANCE_PACKAGE.md` still cites `186f561f…` deliberately — it is a record of the package
produced under that instrument, not a live pin.

**RE-FROZEN 2026-10-15.** The grammar advanced `6f4d72319ec6f87…` -> `b25d59567255c937…` when the RATIFIED
amendments R1/R2/R3 landed on `main` (grammar §2's score line, §2a's eight abstention tokens named verbatim
from the code, §5's CONTEXT/INTERFACE line, and §7's record of what moved). **THE HEADER OF THIS RECORD --
3730 bytes, `6f4d72319ec6f87…` -- is the text §1, §2 and §3 above were READ AGAINST, and it is left exactly
as read; the pin line above is the CURRENT instrument, a precondition for any future run.** The 2026-10-10
population was produced under `6f4d7231…`, and no cell of it is re-scored by the amendment (`give_up` is `0`
in all 12 cells), so nothing above is rewritten, only superseded forward. **AND §1's ITEM IS NOT SETTLED BY
IT:** the amendment moves the abstention list and the score wording, **not §5's schema-filling mechanism**,
which still awaits its own amendment.

**RE-FROZEN 2026-10-15 (SECOND AMENDMENT).** The grammar pin advanced again,
`b25d59567255c937…` -> `c2124f17a6bdaaa8…`, when the read-grammar's SECOND amendment landed on `main` (§5's
three-part measurement replaces the unsupported mechanism sentence; §6's `levels` line names THREE and gains
the per-population `roster` line; §7 records both moves). **The pin block above is the CURRENT instrument, a
precondition for any future run; the HEADER of this record -- 3730 bytes, `6f4d72319ec6f87…` -- is the text
§1, §2 and §3 above were READ AGAINST, and it is left exactly as read.** The 2026-10-10 population was produced
under `6f4d7231…` and `give_up` is `0` in all 12 of its cells, so the second amendment moves no cell of it:
**no cell of the 2026-10-10 population is re-scored**, and nothing above is rewritten, only superseded
forward. **AND §2 ABOVE NOW AGREES WITH THE RUN IT PINS:** `levels/03_the_corner_waiting` is added to the pin
block because that run carries `03` = `77d18407a001da29…` and §2's own item already records that level
digests are *"NOW CARRIED"* -- a pin block naming two of three levels is the stale list this record exists to
prevent. **AND §1's ITEM IS SETTLED IN THE TEXT:** the prescribed three-part replacement is now §5, quoted
back in the grammar's §7 -- **while the MEASUREMENT its text calls for, the three-arm follow-up, has still
NOT been run.**

**PIN ADVANCED FOR THE NAMING, HELD FOR THE PROSE -- 2026-10-15 (R2).** Two pins, two dispositions, and this
landing's own note beside the `sokoban.py` pin line above.

**1. THE GRAMMAR PIN ADVANCES** `c2124f17a6bdaaa8…` -> `02cd63c19bcb65d4…`, because this landing APPENDS §7a to
the read-grammar (the Chair's carrier disposition, filed as
`2026-10-15-a-text-correction-does-not-move-a-pinned-identity`). **A list inside a live pin block is a live
pin, not a history:** the line above is the CURRENT instrument, so it moves with the text it names, exactly as
it did at the first and second amendments. §7a is NAMING, not measurement -- **it re-scores no cell and moves
no published number** (`give_up` is `0` in all 12 cells of the 2026-10-10 population and in both pilots), and
the HEADER of this record -- 3730 bytes, `6f4d72319ec6f87…` -- is still left exactly as read.

**2. THE `sokoban.py` PIN IS HELD, and this note records what the pinned file's own text still READS** so that
a reader who greps it finds a DATED sentence rather than a deletion: `sokoban.py` `:9` and `:31` still call
`moves` the score, and its RUNTIME PRINTED LEGEND at `:396` still prints the same claim beside `:397`'s
retired `unrecognised` for the counter the code names `not_an_action`. **R2 (`solved` IS THE SCORE; `moves` is
a COST) IS NOT LANDED ON THIS FILE, and it cannot be landed by editing prose.** The bytes are held because
they ARE the identity: this pin is asserted by `sokoban_solver.py`'s control [6] and required by
`CABINET_DECLARATION_sokoban.md:42-44` for the live equality with the run of record's recorded
`simulator_digest` (`probes/SOKOBAN_RUN_pilot-20261011-105455.json`); moving the identity for a comment would
spend that equality permanently for zero measurement content
(`2026-10-14-a-name-fix-must-not-buy-a-provenance-supersession`). **The four text lines move in the SAME
COMMIT as the next change that moves this identity for a MEASUREMENT reason -- card `t_b439b167` (`:9`, `:31`,
`:396`, `:397`) -- and the re-freeze it carries will name every subject it moves.** The carriers this record
does not own -- both PREREGs, the pin-time snapshot with its `MANIFEST.txt`, the proposal diff, and the
SUPERSEDED promo -- are NAMED, with lines, digests, dates and reasons, in `SOKOBAN_READ_GRAMMAR.md` §7a.

**RE-FROZEN 2026-10-15 (R1's RECORD-SIDE ITEM — THE PIN HELD ABOVE NOW ADVANCES).** `sokoban.py` advanced
`7134c3e8fc59fe02…` → `00996929972b9483…` (21325 B → 24872 B) when **R1's ruled and never-landed RECORD-side
item** landed on `main` (card `t_b439b167`): the record now carries a **LOOSE-MATCH COUNT AS A DIAGNOSTIC
ONLY, NEVER SCORED** — `play()` returns `loose_match_diagnostic_only_never_scored`, whose name is the
contract, plus `loose_match_diagnostic_note`, which says what it is in words. **THAT IS THE MEASUREMENT
REASON THIS IDENTITY MOVED, and the text rode the move rather than buying it**, exactly as the R2 note above
and the ruling require. The precedent for a bundle is the 2026-10-14 re-freeze above, and **what made it
legitimate was that each subject was named — so every subject this move carries is named here:**

**1. R1's LOOSE-MATCH DIAGNOSTIC — the reason for the move.** One field, one note. It is a count BESIDE the
counters and never IN one: no rate, no gate, no denominator, and `not_an_action` is the scored fact about the
same tokens and is unchanged by it. It has exactly one increment site, in the branch that already counts
`not_an_action`, and the loose reading it applies is defined once beside the whitelist. **Its `gave_up_at`
half — which token fired — was already carried; this is the half that says how much the STRICT reading threw
away.**

**2. THE FOUR TEXT LINES THE RULING NAMED** — `:9`, `:31`, `:396`, `:397` **at the pre-image**, now `:9`,
`:31`, `:443`, `:444`: the module docstring's pre-R2 score claim (`:9`, `:31`), the RUNTIME PRINTED LEGEND's
same claim (`:443`), and that legend's retired `unrecognised` for the counter the code names `not_an_action`
(`:444`). **NOTHING IS ADDED TO THE RUNTIME LEGEND AND NO CONTROL IS ADDED OR REMOVED: `--self-test` still
prints 49/49.** *A moved control count would be a third subject, and neither the ruling nor the card names
it.*

**3. TWO FURTHER LINES INSIDE THE SAME FILE, NAMED RATHER THAN LEFT SILENT** — `play()`'s docstring `:189`
and `:194` **at the pre-image**, now `:220` and `:226`. They state the same two retired claims in different
words (`the number` for the score; `unrecognised` for `not_an_action`) and **the ruling's census pattern —
the retired rule's own words — could not reach them.** They are corrected in the SAME commit, because a false
present-tense sentence left inside the instrument could only ever be corrected by moving this identity a
SECOND time for prose, which is the thing the filed control
`2026-10-14-a-name-fix-must-not-buy-a-provenance-supersession` forbids. **`sokoban.py:49` is NOT corrected**:
*"it used to be counted as `unrecognised`"* is past tense and true. **And `:187`'s *"THE RECORD IS A SUFFICIENT
STATISTIC FOR THE SCORE"* stands**: under R2 the record IS a sufficient statistic for the score, which is
`solved`, and `:220` now says which term that is.

**NOTHING ABOVE IS REWRITTEN, ONLY SUPERSEDED FORWARD, AND NO CELL IS RE-SCORED.** The 2026-10-10 population
was produced under `186f561f…` and the two pilots under `7134c3e8…`, and **each still carries its own digest
in its own artifact — no probe, no prereg and no conformance package is edited by this move.** **MEASURED, NOT
ASSERTED: all 25 played cells — the population's 12 (its 3 `never_started` cells are still not cells), the two
pilots' 5 and 7, and the single-cell evidence file's 1 — re-derive through the NEW bytes to their recorded
counters, their recorded `final_board` and their recorded `trace`, entry for entry. And the recorded `give_up`
is `0` in every one of them, so R1's diagnostic is `0` in every published cell too** (0 loose-only tokens
across all 25, before and after). The one precedent that matters here is not rewritten either: `186f561f…` is
still recoverable as commit `6be5bbb`, **and the pre-image this pin just left is recoverable as commit
`f0eba6e` (blob `247f22b620cc456e…`)**, pinned at `3276b4d`.

**AND THE EQUALITY THIS MOVE SPENDS IS SPENT KNOWINGLY, RECORDED RATHER THAN DISCOVERED LATER.**
`CABINET_DECLARATION_sokoban.md` asserted a LIVE equality — the on-disk `sokoban.py` IS the pilots' recorded
`simulator_digest` — **and after this move it is not**, so that declaration is amended to CARRY THE FREEZE
instead of asserting the equality (its own §"DO NOT COLLAPSE THESE TWO" rule already demands that a run-of-
record line say which instrument produced it). **What is spent is the check "the bytes that produced the run
of record are the bytes on disk"; what replaces it is the strictly weaker claim, now stated: the pilots'
instrument is recoverable as commit `f0eba6e`, and every one of their cells re-derives under this one.** The
read-grammar's §2a and §7 item 2 citations, which recorded R1's loose-match count as MEASURED ABSENT at
`7134c3e8`, are converted to **SETTLED** in `SOKOBAN_READ_GRAMMAR.md` §7b, and that block is an APPEND: §7's
text and §7a's table are not edited and their items are not renumbered.

**AND THE GRAMMAR PIN ADVANCES IN THE SAME LANDING** `02cd63c19bcb65d4…` → `86251be3d717d3b5…`, because
`SOKOBAN_READ_GRAMMAR.md` §7b is APPENDED to the read-grammar: the settlement of §2a's `FIRED` line and §7's
item 2, the discharge of §7a's row 1 and of its *"R2 IS NOT LANDED ON `sokoban.py`"* sentence, and the census
of the LANDED bytes with every hit disposed. **A list inside a live pin block is a live pin, not a
history:** the line above is the CURRENT instrument, so it moves with the text it names, exactly as it did at
the first amendment, the second amendment and §7a. **§7b is NAMING AND SETTLEMENT, not measurement -- it
re-scores no cell and moves no published number** (`give_up` is `0` in all 12 cells of the 2026-10-10
population and in both pilots), and the HEADER of this record -- 3730 bytes, `6f4d72319ec6f87…` -- is still
left exactly as read.

## 3. WHAT THE GRAMMAR GOT RIGHT, CHECKED RATHER THAN ASSUMED

**§1 "exactly one action letter … more than one letter -> `not_an_action`, never truncated, never the first
character"** — matches the reader, which is exact-match on a whole token and never truncates. **This is the
`RESIGN -> R` repair, and it is still holding.**

**§2 the four outcomes — `moves` / `blocked` / `give_up` / `not_an_action` — match the simulator's counters
name for name**, and `give_up` is terminal and scoreable as §2 requires.

**§3 "a malformed answer is never a wrong move"** — matches: a bad token is counted and moves neither the
board nor the score.

**§4 "`never_started` is counted SEPARATELY from `played-and-failed`"** — matches, and the reason counts are
reported beside every total.

## 4. AND THE PATTERN WORTH NAMING, FROM THE RUN'S OWN NUMBERS

**`give_up` is 0 in every cell of the population run — and that is informative, not absent.** Nobody resigned,
**because none of the failing entrants realised there was a game to resign from.** Same fact as the extraction
model's forty `not_an_action`, seen from the other side:

> **A MODEL THAT CANNOT FORM AN ACTION ALSO CANNOT FORM A SURRENDER.**

**Which is why `give_up` being split out of `unrecognised` is load-bearing rather than tidy:** had it stayed
merged, this would have read as noise rather than as a fact about capability.

## 5. COUNT-WRITING RULE, ADOPTED INTO THE VERDICT TEMPLATE

> **COUNTS ARE THE RESULT. RATES ARE THE INDEX.**

**A rate over `attempted` carries the same defect A6 removed from `planned`: an entrant that exits early has a
SMALLER denominator and can improve a rate by quitting.** So the counts print beside every rate and are the
load-bearing numbers; the rates exist to navigate them.
