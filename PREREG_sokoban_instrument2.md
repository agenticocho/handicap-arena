# PRE-REGISTRATION — SOKOBAN INSTRUMENT CHANGE 2: R1'S RECORD-SIDE DIAGNOSTIC, AND THE IDENTITY MOVE THAT CARRIES IT

**Written and committed BEFORE the code change**, in the house form of `PREREG_sokoban_instrument1.md`, and
for the same reason: **a fix whose effect is not predicted in advance cannot distinguish a repaired
instrument from a luckier sample.**

**Card:** `t_b439b167`. **Authority:** the Chair's ruling of 2026-10-15,
`governance/rulings/2026-10-15-a-text-correction-does-not-move-a-pinned-identity.md` (filed from card
`t_31c14a0d`, sha256 `168e89b91e48d2f6…`, §2 and §3 corollary 3), carrying the RATIFIED amendment **R1** of
`RULINGS_independent_implementations.md` (ratified by the Chair 2026-10-13).

**Pre-image, measured at the commit this prereg is written against:**

```
sokoban.py    21325 B   sha256 7134c3e8fc59fe027f3691ffa56ab4acb5eb735018a17683f3183ce538f90235
```

**THE NEW DIGEST IS NOT PREDICTED AND CANNOT BE.** A digest is a function of bytes that do not exist until the
commit is made; predicting one would be a fabricated number. What IS predicted is enumerated below, and the
new digest is recorded against its reason in `SOKOBAN_FREEZE_RECORD.md` when it exists.

---

## WHAT CHANGES — TWO SUBJECTS, ONE IDENTITY MOVE, ONE COMMIT

This instrument's bytes are a **pinned identity** (`SOKOBAN_FREEZE_RECORD.md`'s live pin block,
`sokoban_solver.py`'s `FROZEN_DIGESTS` and its control [6], and `CABINET_DECLARATION_sokoban.md`'s
equality with the run of record's recorded `simulator_digest`). **The ruling refused to move it for prose.**
This change moves it for a MEASUREMENT reason, and the prose rides the move rather than buying it.

**SUBJECT (a) — R1's RECORD-SIDE ITEM: A LOOSE-MATCH COUNT, AS A DIAGNOSTIC ONLY, NEVER SCORED.** R1 froze
the abstention whitelist and ruled, in the Chair's own words, that the record must carry **"a LOOSE-MATCH
COUNT as a DIAGNOSTIC ONLY, NEVER SCORED … that is how you find out how much the strict reading is throwing
away without letting the loose reading into the score."** `gave_up_at` already carries WHICH token fired;
this carries the other half. `play()` gains exactly one counted field and one note:

```
loose_match_diagnostic_only_never_scored   the count of tokens an ABSTENTION-SHAPED reading would have
                                            taken and the strict whitelist did not
loose_match_diagnostic_note                what it is, in words, so the record explains itself
```

**The name is the contract:** it says *diagnostic only, never scored*, because a diagnostic that can be read
as a counter is how a diagnostic becomes a score — the one thing R1 forbids. **It is in no rate, no gate, and
no denominator.** It is incremented in exactly one place, the branch that already counts `not_an_action`; it
can never affect `solved`, `moves`, `blocked`, `not_an_action`, `give_up`, `gave_up_at`, `ended`, or the
trace.

**The loose reading is defined ONCE, and its stems have provenance:** the eight frozen whitelist tokens, plus
the abstention-shaped forms the read-grammar's own §2a table names as NOT firing
(`ABSTAIN`, `STUCK`, `UNSOLVABLE`, `DEAD END`, `NO MOVE`, `I GIVE UP`). Match is **letters-only, upper-cased,
stem anywhere in the token** — deliberately the broadest reading, because it is a reading of what was
discarded and not a second scoring rule. Measured against the grammar's own examples: `RESIGNING`, `XRESIGN`,
`SURRENDERED`, `STUCK`, `ABSTAIN`, `DEAD END`, `QUIT!`, `I GIVE UP` are counted by it and score
`not_an_action`; the eight whitelisted tokens are NOT counted by it (they fire strictly).

**SUBJECT (b) — THE SIMULATOR'S OWN TEXT THAT STATES THE RETIRED RULE OR THE RETIRED COUNTER NAME.** R2
(`solved` IS THE SCORE, `moves` IS A COST) and the `not_an_action` rename are not landed on this file, and
**cannot be landed by prose** — so the correction travels with this move, in the same commit. The four lines
the ruling named, plus two further lines inside the same file that the ruling's census pattern could not
reach and that state the same two retired claims in the present tense. **The set is disclosed here, BEFORE
the change, with the exact SAYS AFTER text, rather than assembled after it.**

One line each, verbatim, wrapped nowhere (the four marked `<- the RULING's` are the four the ruling names):

```
1  :9    SAYS NOW    2. NO EXTERNAL ORACLE. The simulator decides solved or unsolved and the score is the move counter. Chess
         SAYS AFTER  2. NO EXTERNAL ORACLE. The simulator decides solved or unsolved; `solved` is the score and `moves` is a cost. Chess   <- the RULING's

2  :31   SAYS NOW        moves      SUCCESSFUL actions -- the score, and the number that is comparable across entrants
         SAYS AFTER      moves      SUCCESSFUL actions -- a COST, never the score (`solved` IS the score)                            <- the RULING's

3  :396  SAYS NOW        print(f"  moves       {r['moves']}   (successful actions -- the score)")
         SAYS AFTER      print(f"  moves       {r['moves']}   (successful actions -- a COST, not the score: `solved` IS the score)")   <- the RULING's

4  :397  SAYS NOW        print(f"  attempted   {r['attempted']}   blocked {r['blocked']}   unrecognised {r['not_an_action']}")
         SAYS AFTER      print(f"  attempted   {r['attempted']}   blocked {r['blocked']}   not_an_action {r['not_an_action']}")       <- the RULING's

5  :189  SAYS NOW            solved + moves          the number, and the reason this game was chosen
         SAYS AFTER          solved + moves          `solved` IS the score; `moves` is a COST beside it

6  :194  SAYS NOW        `unrecognised` and changes nothing -- it is a fact about the output, not about the board.
         SAYS AFTER      `not_an_action` and changes nothing -- it is a fact about the output, not about the board.
```

*(Leading whitespace in the SAYS lines is the source indentation of the line, shown so the corrected text can
be checked against the commit token for token; the quoted text inside rows 3 and 4 carries its own quote
characters, which are part of the line.)*

**Lines 1–4 are the ruling's four.** **Lines 5–6 are named here because the ruling reached its four by a
census whose pattern was the retired rule's own words, and `play()`'s docstring states the same two retired
claims in different words** (`the number` for the score on `:189`; `unrecognised` for `not_an_action` on
`:194`). Leaving them is the defect the ruling's own §4(c) refused — *a false sentence sitting inside the
instrument indefinitely* — and they cannot be corrected later without moving this identity a second time for
prose, which is the thing the filed control forbids. **Every line above is corrected in ONE commit, and every
one is named in the re-freeze.**

**Corrected text agrees token-for-token with `SOKOBAN_READ_GRAMMAR.md` §2/§2a and with `play()`'s own keys:**
`moved / pushed` counts toward `moves`, which is a COST; `solved` IS the score; `not_an_action` is the name,
not `unrecognised`. **No line is added to the runtime printed legend and no control is added or removed.**

**NOT CHANGED, because the artifact is evidence of a date rather than a statement of the current reading:**
`sokoban.py:49` (`it used to be counted as `unrecognised`` — past tense, and true). And **`sokoban.py:187`'s
`THE RECORD IS A SUFFICIENT STATISTIC FOR THE SCORE` stands**: under R2 the record IS a sufficient statistic
for the score, which is `solved`, and `:189` now says which term that is.

---

## THE PREDICTION, RECORDED BEFORE THE CHANGE

**1. NO MEASURED CELL MOVES — and this is the claim the identity move is bought with.** Every played cell of
every published sokoban artifact re-derives through the NEW bytes to its RECORDED counters, its recorded
`final_board`, and its recorded `trace`, entry for entry:

```
probes/SOKOBAN_RUN_20261010-072252.json          12 played cells (3 never_started)   12/12
probes/SOKOBAN_RUN_pilot-20261011-104425.json     5 cells                            5/5
probes/SOKOBAN_RUN_pilot-20261011-105455.json     7 cells                            7/7
probes/SOKOBAN_Ministral-…_01_one_push.json       1 cell                             1/1
```

**2. THE DIAGNOSTIC IS ZERO IN EVERY PUBLISHED CELL.** Measured from the RECORDED token streams before the
change: **0 loose-only tokens across all 24 played cells.** So no published reading is disturbed by the new
field, and the diagnostic cannot be mistaken for a live quantity in this cabinet's own data. *That is also
why it is a diagnostic and not a headline: this population threw nothing away.*

**3. THE DIAGNOSTIC CAN FIRE, AND MOVES NOTHING WHEN IT DOES.** On a synthetic stream it counts the
abstention-shaped rejects; `not_an_action` counts the same tokens beside it; `give_up` stays `0`; and every
scored quantity is identical to the same stream with the abstention-shaped tokens replaced by plain junk.
**A count that cannot fire is not a count** — the same doctrine as the two positive controls in
`check_frozen_constants.py`.

**4. NOTHING ELSE MOVES.** `sokoban.py --self-test` is **49/49, exit 0 — unchanged, and NO CONTROL IS ADDED
OR REMOVED by this change**: the identity move carries exactly the subjects above, and a moved control count
would be a third subject that neither the ruling nor the card names. The diagnostic's own controls are run in
the landing evidence and quoted in the handoff. Every other control in the tree that passed before passes
after.

**FALSIFIERS, named so the prediction can fail:** any counter, board or trace that differs on any played
cell; any nonzero diagnostic in a published cell; a diagnostic that cannot fire; a control count that moves;
or any file changing beyond the re-freeze carriers (`sokoban.py`, `FROZEN_DIGESTS`, the freeze record, the
cabinet declaration) and the read-grammar's appended landing block.

---

## HOW THIS PREREG IS PRE-REGISTERED, STATED HONESTLY

The prediction and the line-level SAYS AFTER text above were fixed **before** the code change, in this commit,
which is ordered before it in history. **The zero baseline in prediction 2 was measured from the recorded
token streams** (read-only, from `probes/*.json`) rather than guessed, because the value of that quantity in
an ALREADY-PUBLISHED population is a fact about that population and not a prediction about the instrument;
**the prediction is that the new field REPRODUCES it, cell for cell, and moves nothing else.** The outcomes
are therefore enumerated above with their falsifiers, and there is no outcome that this document would read
as a repaired instrument if it did not happen.

**SCOPE, carried so it cannot drift: FUTURE RUNS ONLY.** A number is read under the text it was taken under.
Nothing is retro-fitted, restated or reinterpreted; **records are never rewritten** — the pilots' recorded
`simulator_digest`, every probe, `SOKOBAN_CONFORMANCE_PACKAGE.md` (which cites `186f561f…` deliberately) and
both earlier preregs keep their own digests and their own dates.
