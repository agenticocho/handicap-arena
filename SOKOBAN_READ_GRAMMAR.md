# SOKOBAN READ-GRAMMAR -- FROZEN BEFORE THE FIRST ENTRANT MOVES

**Event:** SOKOBAN (the order's position 2) · **Instrument, not advice.** The run that follows is scored
under exactly these rules. Changing them after a number exists makes the number a different measurement.

> **AMENDED 2026-10-15 -- §2, §2a, §5, §6, §7.** This text now carries the RATIFIED amendments **R1, R2 and
> R3** (`RULINGS_independent_implementations.md` `f0eba6e`; ratified by the Chair 2026-10-13 in
> `2026-10-13-chair-ratification-r1-r2-r3-six-item-rulings.md`). **FUTURE RUNS ONLY -- no published number
> is retro-fitted or reinterpreted.** What moved, what the moved lines said before they moved, and the two
> things this amendment does NOT settle: **§7.**

## WHY THIS DOCUMENT EXISTS, AND IT IS NOT THEORY

Chess was blocked by its read-grammar: every entrant failed to commit a move unaided, and the only surviving
record had to be asterisked because the prompt had supplied the moves.

**Then the first Sokoban run reproduced the wall in a new form.** An extraction model TRANSCRIBED THE
PROMPT -- it keyed on the board legend and treated it as a schema to fill. Forty tokens, forty
`not_an_action`, zero moves. The model was not failing to play; **the instrument described the wrong task.**

> Neither failure was a model failing to play. Both were a carrier changing the question.

## 1. THE ANSWER

    exactly one action letter:  U  D  L  R      ONE CHARACTER. Nothing else on the line.

    case-insensitive        accepted
    W A S D                 NOT synonyms. They are `not_an_action`, and they are counted.
    punctuation, quotes,
    fences, JSON, prose     `not_an_action`. Counted, never read for a move.
    more than one letter    `not_an_action`. Never truncated. Never the first character.

## 2. THE FOUR OUTCOMES -- AND THEY ARE FOUR, NOT TWO

    moved / pushed   a legal action executed                    -> counts toward `moves`, which is a COST.
    blocked          a legal LETTER aimed at a wall or crate     -> `blocked`. No move, no board change.
    give_up          an explicit ABSTENTION -- §2a names it      -> `give_up`. Attempt ENDS. SCOREABLE.
    not_an_action    anything else                               -> `not_an_action`. Counted.

**`solved` IS THE SCORE. `moves` IS A COST -- a tiebreak between solvers, NEVER the score (R2, ratified
2026-10-13).** A cost is not a result, and scoring by one ranks the failure this cabinet exists to measure:
**a corner-walking flailer that solves NOTHING totals 52 moves against a reference solver's 19 on identical
levels.** And there is no plan to compare a stream against -- **02 has THIRTEEN distinct 12-move optima,
enumerated exhaustively**, so "the solution" is not a thing that exists there.

**An abstention is a legal, scoreable answer -- it enters the record and the denominator, and it ADDS NO
SCORE (`solved` is the score, above).** `give_up` is not noise to be discarded -- **it is the
dead-end faculty's counter, and it is the only reason this event can measure collapse without a solver.**

## 2a. THE ABSTENTION TOKENS -- THE LIST IS THE CODE'S, STATED VERBATIM

**R1, ratified 2026-10-13, and it is a FIX rather than a decision: the frozen instrument ships EIGHT ways to
give up and this document named ONE, so an implementation built from the grammar -- which is what a grammar
is FOR -- and one built from the code DISAGREED ON IDENTICAL BYTES, both conforming.** The list below is
`sokoban.py`'s, stated here verbatim from the code. **The grammar is the artifact that moves, because the
code is already frozen, already scored, and already the path every published number went through.**

    RESIGN   RESIGNS   RESIGNED   GIVEUP   SURRENDER   IQUIT   QUIT   FORFEIT      <- EIGHT, and no others

    MATCH       one token, upper-cased, with ALL whitespace removed first.
                NOT a prefix. NOT a substring. NOT the first letter.
                `GIVE UP` / `give up` / `GIVEUP` FIRE -- whitespace is removed, not significant.
                `RESIGNING` / `XRESIGN` / `RESIGN X` / `SURRENDERED` DO NOT: they are `not_an_action`.
                `R` alone is an ACTION (right), never a give-up -- §3's `RESIGN -> R` repair, still holding.

    FIRED       the record names WHICH token fired: the trace row at `gave_up_at` carries that token, and
                `ended` reads `gave_up`. **What is NOT recorded, and is scored neither way: R1's LOOSE-MATCH
                COUNT as a diagnostic only -- measured absent from `sokoban.py`'s record at `7134c3e8`.**

    NOT ON
    THE LIST    STUCK  ABSTAIN  UNSOLVABLE  NO MOVE  DEAD END  I GIVE UP  QUIT!  resigns.  -> `not_an_action`
                *A model writing `STUCK` scored `give_up` on one implementation and `not_an_action` on the
                other, from identical bytes. That is what this section removes.*

## 3. THE RULE THAT IS EASIEST TO GET WRONG

    A MALFORMED ANSWER IS NEVER A WRONG MOVE.

It is `not_an_action`; it is counted; and it moves neither the score nor the board. **The first Sokoban
reader took `token[:1]`, so `RESIGN` was read as `R` -- Right -- and EXECUTED: a six-letter word became a
legal move by accident.** Same class as the greedy parser and the name whitelist: a reader wide enough to
find an answer in text that does not contain one.

## 4. THE ZERO RULE

    a run with ZERO measured entrants is an ERROR (non-zero exit), never a verdict
    coverage 1.000 with measured 0 is a BROKEN RUNNER, not a clean field
    `never_started` is counted SEPARATELY from `played-and-failed` -- different claims

## 5. WHAT THE ENTRANT MAY SEE

    PERMITTED   the board in ASCII, with a legend; the move history so far; the move count; solved or not
    FORBIDDEN   the word "schema"; any key-value framing; any JSON example; any "fill in" language

**The legend is PROSE, and this is measured rather than stylistic: a legend formatted as key-value pairs
reads as a FORM to a model whose training is schema-filling, and that model transcribes the prompt instead
of playing.** The legend fix is an INSTRUMENT CHANGE and carries its own pre-registered prediction.
**§5's FORMAT claim is what the A/B measured; its MECHANISM sentence is NOT established, and it is not
settled by the 2026-10-15 amendment -- see §7, item 1.**

**AND WHAT §5 PERMITS THE HARNESS TO SHOW IS CONTEXT, NOT AN ANSWER SHAPE (R3, ratified 2026-10-13).**
The history and the move count are **CONTEXT**; the harness's own `play(level_text, tokens)` signature is
the **INTERFACE** -- *it consumes a stream of one-letter answers and is silent on how they were obtained.*
**Neither is a licence to answer with a PLAN: §1 is the controlling sentence -- ONE ACTION LETTER PER TURN.**
*Under the whole-plan reading every legal plan would be a malformed answer and a level's own six-letter
solution would score as a failure -- a reading under which the correct answer is a failure is not a reading
of the spec; it is a disproof of it.*

## 6. FROZEN IDENTITY

    simulator    sokoban.py · self-test is the contract: `python3 sokoban.py --self-test`
    levels       levels/01_one_push.txt · levels/02_two_boxes.txt  (sha256 with the run)
    controls     49, all passing -- `--self-test` prints the line; a stale count in prose is not the instrument
    host         recorded per bundle, WITH the host's hardware state (see the box rule, below)
    zero rule    enforced, not described
    this text    AMENDED 2026-10-15 (§7). The 2026-10-10 population was read under the PRE-amendment text,
                 sha256 `6f4d72319ec6f87…` (commit `744ae42`) -- **a number taken under that text is not a
                 number taken under this one**, and the two are never pooled.

## 7. THE AMENDMENT -- 2026-10-15. WHAT MOVED, AND WHAT THE MOVED LINES SAID BEFORE THEY MOVED

**This text is frozen, so the lines below are not silently replaced: what they SAID is quoted, and what they
SAY now is beside it.** R1, R2 and R3 were ruled 2026-10-10 (`RULINGS_independent_implementations.md`,
`f0eba6e`) and RATIFIED by the Chair 2026-10-13. **THIS DOCUMENT'S LAST COMMIT PREDATED BOTH -- and a ruling
that names the artifact that changes is satisfied when THAT ARTIFACT'S BYTES MOVE.** They had not. They have.

    §2 SAID    "moved / pushed   a legal action executed   -> counts toward `moves`. THE SCORE."
               and named ONE abstention token -- `RESIGN`, in §3 -- while `sokoban.py` scored EIGHT
    §2 SAYS    `moves` is a COST and `solved` is THE SCORE; §2a states the eight tokens verbatim   <- R1, R2
    §5 SAID    the entrant may see "the move history so far" -- and nothing about what that permission
               is NOT a licence for
    §5 SAYS    the history is CONTEXT, the harness signature is the INTERFACE, and §1 controls:
               ONE ACTION LETTER PER TURN                                                           <- R3

**WHY THE GRAMMAR MOVES AND NOT THE CODE:** the code is already frozen, already scored, and already the path
every published number went through; naming its existing list here repairs the divergence **without touching
a single measured cell. AND THAT IS MEASURED, NOT ASSERTED: `give_up` is `0` in every cell of the 2026-10-10
population (12 cells) and in both pilots (7 and 5).** No run of record is re-scored by this section.

**SCOPE, carried so it cannot drift: FUTURE RUNS ONLY.** A number is read under the text it was taken under;
nothing here is retro-fitted, restated or reinterpreted. **AND THE ONE OTHER CARRIER OF THE OLD WORDING IS
NAMED RATHER THAN QUIETLY LEFT:** `THE_ARCADE_CABINET_SOKOBAN_tech-and-promo.md` `:81` and `:137` still call
`moves` THE SCORE and print the same four counters. **That is a different artifact, it is NOT edited by this
amendment, and until it moves it is the second place where R2 disagrees with a current text.**

**AND TWO THINGS THIS AMENDMENT DOES NOT SETTLE, named so that a reader does not read them as settled:**

    1  §5's MECHANISM. The legend's FORMAT is a measured carrier defect; the SCHEMA-FILLING mechanism §5
       states is NOT established for the entrant the A/B measured (40 -> 40 on the extraction model), and
       the replacement text is prescribed at `SOKOBAN_FREEZE_RECORD.md` §1. **This amendment does not carry
       it; §5's mechanism sentence stands as written until a second amendment moves it.**
    2  R1's RECORD-side requirement -- a LOOSE-MATCH COUNT as a diagnostic only, NEVER scored -- is **not
       emitted by `sokoban.py` at `7134c3e8fc59fe02…`**, read from `play()`'s own return keys, and this
       amendment adds nothing to the code. **Which token fired IS carried; how much the strict reading
       throws away is not.**
