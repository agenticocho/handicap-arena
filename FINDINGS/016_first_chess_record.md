# FINDING 016 — THE FIRST CHESS RECORD, AND THE FIVE DEFECTS THE SMOKE TEST FOUND BEFORE IT

**Event 1 of THE ORDER produced its first record.** One entrant, both sides, this box, no cross-machine
anything — Mike's sequencing, and it was right. `results/CHESS_GAME_DEBUG_Ministral3B.json`:

```
19 plies · termination `decisive` (engine adjudicated mate in 1 after d4c5) · wall 133 s
e2e3 e7e5 d2d3 d7d5 e3e4 d5d4 c2c3 g7g6 c3d4 f8c5 d4e5 c5b4 c1d2 b7b6 d2c3 b4c5 d3d4 c8g4 d4c5
premature collapse         0      miscalibrated persistence   3
plies recorded            19      plies spent in lost positions  3
```

**AND THE ZERO IN THE CONTRACT IS NOW NON-ZERO: 0 contests, 75 labels was the gap the game contract was
built around. There is a contest, and it has a record.**

---

## THE FIVE DEFECTS, ALL FOUND BY RUNNING THE LOOP ON A CHEAP MODEL BEFORE SPENDING ON THE REAL ONE

**Every one of them would have been recorded as a failure of the ENTRANT.** Four were fixed; the fifth is
a defect in the FROZEN CARD and is reported rather than patched.

### 1. THREE FALSE ILLEGAL-MOVE VERDICTS, EACH ON A CORRECT ANSWER

```
the model played `e4`          a UCI-only parser scored it ILLEGAL. SAN is expected input -- the record
                               carries `move_san` precisely because of it.
the model played `g1f3`        matches the SAN pattern as a PAWN move from g1, lowercase first letter.
                               UCI must be matched literally BEFORE any notation parsing.
the model played `**d4c5**`    markdown bold, after EIGHTEEN PLIES OF REAL CHESS. Decoration stripped
                               first. This one fired live, mid-game, at ply 18.
```

**THE CLASS: A MODEL THAT PLAYS CORRECT CHESS IN A FORMAT THE HARNESS DID NOT ANTICIPATE IS NOT MAKING AN
ILLEGAL MOVE.** Three times, the instrument's narrowness was about to be filed as the entrant's failure.
**And the third arrived after the first two were fixed — the form that beats it next has not been written
yet, which is why the resolution is now by *engine-verified legality plus declared ambiguity* rather than
by pattern.** Where the text yields more than one distinct legal move it returns nothing: **ambiguity is
not a winner.**

### 2. THE ANSWER THE CAP ATE — FINDING 001 ARRIVING IN THIS LOOP

`max_tokens: 64` against a prompt listing twenty legal moves and inviting a resignation judgement: the
**reasoning trace** consumed the whole budget and `content` came back **empty** — with the server reporting
283 tokens generated and the model audited fine on a short prompt (`content "e2e4"`, 58 tokens). The model
answered; the cap ate it. **That is FINDING 001's first silent mechanism exactly.**

**And the label is a separate fix from the value:** empty output WITH `finish_reason = length` now maps to
the frozen taxonomy's **`serving-failure`** — MISSING VALUE, never scored zero, never dropped, re-run is a
RE-MEASUREMENT — **rather than to an illegal move. An empty answer the HARNESS produced must not be
recorded as a move the MODEL failed to make.**

### 3. THE PERSPECTIVE INVERSION — THE ONE THAT MATTERED MOST

**Stockfish reports `score cp` FROM THE SIDE TO MOVE.** A row's `fen` is the position *before* the move
with the entrant to move, so `eval_before` is **the entrant's** evaluation. The position *after* the move
has the **opponent** to move, so `eval_after` is **the opponent's**. **They are the same quantity read from
opposite sides.**

```
ply  0  e2e3   eval_before   37   eval_after   -9        eval_after at ply N equals
ply  1  e7e5   eval_before   -9   eval_after   14        eval_before at ply N+1 --
ply  2  d2d3   eval_before   14   eval_after   32        verified on EVERY row.
ply  3  d7d5   eval_before   32   eval_after  -33
```

**The first version measured "the entrant played on while lost" from `eval_after` — WHICH IS THE ENTRANT'S
WINS.** It reported **miscalibrated persistence 0** for an entrant that played on for three plies at
−445, −521 and −745 and was mated. **Corrected: 3.**

**AND THE ONLY REASON IT WAS CAUGHT IS THAT THE OUTPUT CONTRADICTED ITSELF** — `plies_in_lost_positions 3`
printed beside `miscalibrated_persistence 0`, which cannot both be right if they describe the same
quantity. **A self-contradiction in adjacent lines of one report is a cheap and underrated detector; this
is the second time it has earned its keep in this project** (the `skipped 19 / measured 18` pair was the
first).

**This is "one rule, four axes" on WHICH SUBJECT, and it is the axis most easily lost because both fields
are integers in the same unit that look directly comparable.** `eval_before` is the mover's own side and
is the only field either direction may be read from.

### 4. THE ENGINE REFACTOR INTRODUCED TWO SILENT-EARLY-RETURN BUGS

```
a stray `isready` in the middle of the script    the persistent reader stopped at the FIRST `readyok`,
                                                 before any output. legal_moves returned 0 moves and
                                                 evaluate returned None, on an engine that answers
                                                 correctly when driven by hand.
framing `go depth 18` with `readyok`             UCI REQUIRES isready to answer PROMPTLY EVEN DURING A
                                                 SEARCH, so a search framed that way returns in 0.000 s
                                                 with only the opening info lines.
```

**THE TERMINATOR DEPENDS ON THE COMMAND: `readyok` for plain commands, `bestmove` for a search, and
`Nodes searched` for `go perft` — which never emits `bestmove` at all.** Both bugs return *early and
quietly* rather than failing, which is why the smoke test mattered: they were introduced by a performance
refactor and caught by the immediate check, not by a later run.

**AND THE REFACTOR WAS WORTH IT: one persistent engine instead of six spawns per ply took the ENGINE cost
from tens of seconds per ply to 0.111 s** — roughly 800×, which moved the whole run's cost onto the model
where it belongs.

### 5. AND THE ONE THAT IS NOT MINE TO FIX: THE FROZEN TAXONOMY DOES NOT COVER THIS

**CARD_chess.md freezes five terminations: `resigned`, `decisive`, `capitulated-in-band`, `no-conclusion`,
`serving-failure`.** The loop needed a sixth — a move that is legal nowhere, produced by the model — and
**writing `illegal-move` into the record was extending a frozen card without declaring it.** Defects 1–3
mean that outcome was mostly the instrument's fault, and the fix is almost entirely in the resolver; but
**a move that names nothing legal can still occur, and the frozen taxonomy has no value for it.**

**REPORTED, NOT PATCHED.** Amending a frozen taxonomy is a card change, the card is frozen at a commit,
and *an agent does not certify the gate that admits its own work* — nor silently extend the vocabulary it
is scored in. **The gap is named here so the next card can close it deliberately.**

---

## AND WHAT THE RECORD SAYS ABOUT THE ENTRANT, WHICH IS THE POINT OF THE EVENT

**`calibrated: false`, on the frozen definition: *an entrant's termination is CALIBRATED iff, at every
point where it chose to stop, the frozen engine agreed the position was lost — and it stopped rather than
running the budget out.*** This entrant **never chose to stop.** It played on through three plies below
−300 and was mated. **That is `miscalibrated persistence`, the direction the card names as one of the two
opposite failures of one quantity — and chess is position 1 in THE ORDER because *a model that cannot stop
will run up the move counter in every event after this one.***

**One game is not a verdict about Ornith 9B or any other entrant** — the population rule and the gate are
CARD_chess's, and this is the loop's debug run, not the event. **What is established is that the loop
plays a game, adjudicates it, writes a termination by the path that produced it, and measures both
directions of the one quantity from the correct side.** The event is now a second run of a harness that
has already worked once.
