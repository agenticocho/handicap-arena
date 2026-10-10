# SOKOBAN READ-GRAMMAR -- FROZEN BEFORE THE FIRST ENTRANT MOVES

**Event:** SOKOBAN (the order's position 2) · **Instrument, not advice.** The run that follows is scored
under exactly these rules. Changing them after a number exists makes the number a different measurement.

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

    moved / pushed   a legal action executed                    -> counts toward `moves`. THE SCORE.
    blocked          a legal LETTER aimed at a wall or crate     -> `blocked`. No move, no board change.
    give_up          an explicit ABSTENTION                      -> `give_up`. Attempt ENDS. SCOREABLE.
    not_an_action    anything else                               -> `not_an_action`. Counted.

**An abstention is a legal, scoreable answer.** `give_up` is not noise to be discarded -- **it is the
dead-end faculty's counter, and it is the only reason this event can measure collapse without a solver.**

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

## 6. FROZEN IDENTITY

    simulator    sokoban.py · self-test is the contract: `python3 sokoban.py --self-test`
    levels       levels/01_one_push.txt · levels/02_two_boxes.txt  (sha256 with the run)
    controls     49, all passing -- `--self-test` prints the line; a stale count in prose is not the instrument
    host         recorded per bundle, WITH the host's hardware state (see the box rule, below)
    zero rule    enforced, not described
