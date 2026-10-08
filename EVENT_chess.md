# CHESS — the calibration event: the resignation gate, not a tactics puzzle

**Status:** design, **REVISED** after two questions from Chilly — a gap it found in my taxonomy, and
which event chess actually becomes. **Not** a card round. **No** new card version.

**The revision in one line:** v1 of this document specified chess as a **tactics puzzle** — near-miss
discrimination under a hard rule set. That measure is **already occupied by R1_fencing**, which is what
the card round measures and what discriminated at 39.5% while four of its siblings sat above 85%. So
chess-as-tactics would have been a **second measurement wearing a second game** — the same defect as a
game name with no state behind it, one level up.

**Chess becomes the CALIBRATION event**, because that is what the strongest line anyone has written about
this project actually describes: *"the hardest move on the board isn't a sacrifice, it's tipping your
king."*

---

## The measure

**Does the model know when it has lost?**

Two-sided, with a ground truth, and both sides are real failures:

- **resigning a WON or DRAWN position** — premature collapse. The model gives up while the engine says
  the game is holdable.
- **playing on in a LOST position** — miscalibrated persistence. The engine says lost, the model keeps
  generating moves, and the game consumes its budget to no purpose.

**Both are conformance failures with a stateable reason**, which is the standard every surviving item in
this catalogue had to meet. And the measurement is objective: the engine's evaluation at a fixed depth
is the ground truth, not an opinion.

## Why this is a gate and not a score

The event's own framing carries the gate: *a logical conclusion must be reached or the model can't
enter.* **A player who cannot recognise a lost position cannot be said to have played a game** — the game
has no end. So this is not a round with a winner; **it is an admission test**, and its output is a binary
that other events consume.

Which means the event's own contract is the thing it measures: **if the outcome cannot be recorded, the
gate does not exist.** That is the gap Chilly found, and it is fixed below.

---

## THE GAP CHILLY FOUND, AND THE FIX

**v1's taxonomy was `found / legal-but-not-best / illegal / unparseable / serving-failure` — a FAILURE
taxonomy pretending to be an OUTCOME taxonomy.**

There is no `concluded`, no `resigned`, no `abandoned`. So a self-play weigh-in that resolves by a
**decision** has nowhere to land in the record. Chilly's sentence is exact: *a weigh-in whose outcome
can't be recorded isn't yet a gate.* And worse in this specific case — **the promo makes the resignation
the achievement, so the class that would collapse is the one the sport is about.**

**THE FIX: `outcome` becomes two independent fields, because a game ending is not a failure.**

```
result       found | legal-but-not-best | illegal        -- the quality of the MOVE (unchanged)

termination  concluded | resigned | decisive | drawn
             | abandoned | insufficient-material
             | unparseable | serving-failure
             | no-conclusion                          -- HOW THE GAME ENDED, or why it did not
```

**`resigned` and `decisive` are RESULTS. `abandoned` and `no-conclusion` are failures.** They were the
same field before, and that is what made the record unable to hold the sport.

| termination | meaning | gate effect |
|---|---|---|
| `concluded` | a mate or a drawn result was reached | ADMIT |
| `resigned` | the model declared the position lost and stopped | ADMIT **if** the engine agrees; REJECT if the position was holdable |
| `decisive` | the engine adjudicated a finished line | ADMIT |
| `drawn` | repetition, 50-move, or insufficient material | ADMIT |
| `abandoned` | the model stopped emitting moves without declaring anything | REJECT — no conclusion |
| `insufficient-material` | the game ran out of playable content | NOT A MODEL RESULT; flag it |
| `unparseable` | no move could be extracted — the raw is kept | REJECT, and the extractor is on trial |
| `serving-failure` | the request raised; **names the exception type** | MACHINE result, not a capability result |
| `no-conclusion` | budget exhausted with the game unresolved | REJECT — the failure this gate exists for |

**`no-conclusion` is the one that matters most and it did not exist at all.** It is the failure mode of a
model that can always find another move, and it is invisible in a taxonomy that records only how a
*scored item* went.

---

## One event or two — answered: ONE, with two phases

Mike's specification contains both phases *and* their relationship: *"the model plays itself. A logical
conclusion must be reached or the model can't enter the tournament to challenge other models."*

**The self-play game is the ADMISSION. The tournament is the CONTEST.** They share one state schema
(`fen`, `move`, `eval_before`, `eval_after`, `termination`, `result`) and differ only in what they consume:
**the weigh-in PRODUCES the binary, the tournament CONSUMES it.**

**So: one event, two phases.** Splitting them would require two state schemas for one game, and the
second would have to re-derive the first's conclusion — which is precisely the drift this catalogue keeps
catching (a game name and a measure that drifted apart inside one entry; a label asserted instead of a
behaviour measured). **A gate and the contest behind it are one event with a checkpoint, not two sports.**

---

## Which event chess is — answered

Chilly relayed a real conflict: the promo makes chess the **calibration** event, `GAMES.md:133` says
**B2 · Chess — Tool Selection**, and the deep dive puts tool selection on **golf** (five clubs = the
five-tool schema; the 7-iron through the oak = the hallucinated call).

**Both derivations are correct. They named different measures under one game name.**

- **TOOL SELECTION is golf's measure** — restraint over the hero play, and the punch-out when no club
  fits. The deep dive's derivation is right and should stand.
- **CALIBRATION is chess's measure** — knowing when to tip the king. The promo's line is right, and this
  document now implements it.

**So: `GAMES.md:133` B2 changes from "Chess · Tool Selection" to "Golf · Tool Selection", and CHESS
becomes the calibration event.** The conflict was not between two documents but inside one entry: a game
name and a measure that had drifted apart. Same defect as `metaphor: CHESS` on a weather API — caught
this time before it shipped.

---

## The recorded state — and the board contract, written for a renderer

Per position or per game, the bundle carries:

- `fen` — the position, so the record reproduces the board
- `raw` — the model's own output, verbatim. **Non-negotiable** — see FINDING 007.
- `move` — the move extracted from `raw`, plus the extraction's own decision
- `eval_before`, `eval_after` — the engine's evaluation at a **frozen depth**, recorded
- `termination` — from the table above, **written by the path that produced it, never inferred later**
- `result` — the move quality, where a move exists

**The sufficient-statistic standard:** the move list plus the evaluations reproduce both fields. A record
keeping the termination but not the evaluation cannot say whether a resignation was correct; a record
keeping the evaluation but not the termination cannot say whether the game ended.

### WHAT A BOARD NEEDS — confirmed, WITH ONE CORRECTION

**The answer to Arena is YES, this record renders a board and a move-by-move replay. But the field list
CHANGED in this revision, and the change matters for what gets drawn.**

Jarvis was given `fen + move + legal + best + outcome`. That was v1, which specified a **tactics** event.
`legal` and `best` are tactics fields: they say whether a move was permitted and whether it was the
engine's choice. **They are not what a calibration board shows**, and two of them are now redundant:

| field | what it draws |
|---|---|
| `fen` | **the position** — the board itself |
| `move` | **the move played** — placed on the board |
| `eval_before` → `eval_after` | **the comparison the replay is built on** — the engine's judgement of the position before and after the model moved. This is the calibration visual: the evaluation is the thing the model is being asked to perceive |
| `termination` | **how it ended** — and here the drama is legible, because `resigned` draws a stopped clock rather than a mate |

**`best` is NOT required for calibration** and should not be drawn as if it were: the measure is not "did
the model find the engine's move," it is **"did the model know where it stood."** The eval pair replaces
`best` entirely, and a board that draws a "best move" arrow on a calibration event is drawing the wrong
sport. `legal` is implied by `move` being parseable and the position being reproducible — keep it in the
record as a check, but no renderer needs it.

### THE THING A BOARD CANNOT DECIDE — and it is Arena's call, not mine

**The measure is two-sided, and the two sides are different pictures:**

- **premature collapse** — the model resigns a **won or drawn** position. The board shows a position the
  engine still likes, and a player who stopped.
- **miscalibrated persistence** — the model plays on in a **lost** position. The board shows a position
  the engine has given up on, and a player who did not.

Same fields, opposite stories. **Whether that is two renders or one is a rendering question and Arena
owns it** — I can say the record supports both, and that a single render which cannot distinguish them
would collapse the exact distinction the class split exists to protect.

### The state is a BUNDLE, not a specification

There is **no chess bundle in existence.** The field running now is card v4's R1 fencing. Arena is not
blocked on design and never was — **it is blocked on a first bundle**, and the renderer can be written
against the shape above today and pointed at real data the moment one exists.

### MOVE NOTATION, THE CLOCK, AND THE PUZZLE/MATCH SHAPE — REVISED AFTER JARVIS READ IT

Three gaps Arena found that this spec did not have, all of them mine.

**1. MOVE NOTATION IS NOW SPECIFIED — UCI PRIMARY, SAN ALONGSIDE.**

A battle-chess board moves a piece **from square to square**. `g1f3` carries that directly. `Nf3` is what
a human reads and **requires replaying the position to recover the squares.** If the bundle carries only
SAN, then **every renderer re-implements a legal-move generator just to animate** — hidden work that turns
a two-day job into a two-week one, on a project whose whole point is that the measurement is the product.

```
move_uci    "e7e8q"          PRIMARY -- the machine form. Movement, animation, replay.
move_san    "e8=Q+"          alongside, for display and for a human reading the record
move_flags  {capture, promotion, castling, check}   so the animation can show what happened
```

**UCI is the recorded truth; SAN is a courtesy.** A record that stores only the readable form has made the
rendering the problem.

**AND THE FLAGS ARE DERIVABLE, SO THEY ARE NOT CARRIED — ruled, with the reason.** Arena asked whether
capture / promotion / castling / check should be recorded, and the answer is no, because **all four follow
from `fen` + `move_uci` without a move generator:**

| flag | derived how |
|---|---|
| promotion | the suffix on `move_uci` — `e7e8q`. It is in the notation already. |
| castling | a king moving two files — `e1g1`. The rook's move follows from that. |
| capture | **the destination is occupied in `fen` — OR, for EN PASSANT, the moving piece is a pawn and the destination is the `fen`'s en-passant target square.** The second clause is not optional: `8/8/8/3pP3/8/8/8/4K2k w - d6 0 1` with `e5d6` is a capture onto an EMPTY square, and the victim leaves from `d5`. |
| check | the position **after** the move — applying it means moving the piece, moving the castling rook, removing the en-passant victim, and applying the promotion. **Less than a legal-move generator; more than zero.** Shared work for every reader of a bundle. |

**AND THE EN-PASSANT CLAUSE WAS MISSING FROM THE FIRST VERSION OF THIS TABLE, which is worth recording
because of WHERE the failure lived.** The flag is wrong for **exactly one move in the game**, silently, in
a flag we agreed **not to carry because it is derivable** — so the defect was inside the derivation rather
than inside the record. **A derived field is not safer than a stored one; it is a stored one with the
defect moved into shared code.** Found by Arena reading a position, which is the only way it would have
been found.

**AND THE CONTRAST THAT VALIDATES THE TEST:** SAN is **NOT** derivable from `fen` + `move_uci`, because
disambiguation (`Nbd2` vs `Nfd2`) needs the *other* candidate movers — so **SAN is carried for exactly the
right reason, and `move_flags` would have been carried for the wrong one.** One field is in the bundle
because a stranger cannot recompute it; the other is out because a stranger can, given one more clause
than I wrote the first time.

**CARRY WHAT CANNOT BE DERIVED; DERIVE WHAT CAN.** Carrying them would create a second source for a fact
the primitives already state, and **four of today's defects are exactly that** — a compact stand-in trusted
after the thing it stands for had changed or been approximated: the parser's extraction, `_EMPTY_` in a
filename, a slot name surviving a card change, a rounded percentage stored beside its own ratio. **A
recorded flag that disagreed with `fen` would be a defect with no way to tell which side was right.**

**The same rule, applied the other way, is why the clock fields ARE carried:** `secs`, `gen_tokens` and
`budget_hit` are facts about the **RUN**, not about the position — they cannot be recovered from the board,
so they must be recorded. `wins`/`trials` are carried and `aggregate` is derived for the identical reason.

**If a future renderer needs a flag that is genuinely not derivable, that is evidence for adding it — and
not before.** The test is the same one every field in this spec had to pass: can a stranger recompute it
from what is already in the bundle?

**2. THE CLOCK — THE RECORD CARRIES TIME, because the promo's beat is a clock under the crowd and a clock
drawn over an absent measurement is decoration over nothing.**

This is the rule we all agreed on applied somewhere nobody had looked: **anything displayed must derive
from the data.** So the record must carry the time, and it already can — the runner records it:

```
secs        wall time for the decision
gen_tokens  tokens produced (the budget consumed)
budget_hit  whether the model ran out rather than concluded -- the clock's teeth
```

And **`budget_hit` is the one a clock should show**, because it is the difference between a player who
thought and a player who ran out. A ticking clock that cannot say which is theatre.

**3. THE PUZZLE/MATCH MISMATCH — THE SHARPEST THING ANYONE HAS SAID ABOUT THIS SPEC.**

Jarvis: *"your finding and my rendering answer are the same finding from opposite ends — the record is
shaped for puzzles, and the weigh-in is a match."* He is right, and the cause is that I wrote a **match's
measure over a puzzle's fields.** `move` and `best` are singular: one position, the move chosen, the move
that was better. **A frame, not a match.**

**Resolved by the two-phase structure, because the two phases genuinely have two record shapes:**

| phase | shape | what it is |
|---|---|---|
| **the weigh-in** (admission) | **a match** — a self-play game to a conclusion | Mike's gate: *a logical conclusion must be reached or the model can't enter* |
| **the tournament** (contest) | **a puzzle series** — a position, a decision, a verdict | the frame: does the model know where it stands |

**Both shapes need the same fields, and the fields listed above serve both.** The difference is cardinality:
a match is a list of frames, a puzzle is one.

**AND ARENA'S RECOMMENDATION IS ACCEPTED: THE PUZZLE VIEW SHIPS FIRST.** Everything it needs already
exists in the record above. It is not a smaller version of the match — **it is a different and arguably
stronger one, because the comparison is the entire content.** The match view follows when a match bundle
exists.

### ONE RENDER, TWO VERDICTS — Arena's answer, adopted

I put the two-sided measure to Arena as a rendering question and it came back better than it went out:
**one render, two verdicts**, because the two failures are **opposite directions of one quantity** —
model confidence against the position's truth — and two renders would tell the audience these are two
different sports.

```
premature collapse         an EVENT      a healthy board, a hand, a king over. Over in a second.
                                         Should feel like it ended too early.
miscalibrated persistence  a DURATION   a lost board that keeps producing moves.
                                         Should feel like being ground down.
```

Same component, same fields, different state — on this event's own rule that **cannot play** and **plays
imprecisely** must never render alike. Arena extended it one level in: **giving up too early and refusing
to give up are not the same failure**, and a render that cannot show the difference has collapsed the
distinction the class split exists to protect.

**And every failure carries the class assigned by the path that failed.** A field inferred afterwards
from a reason string can be overwritten by a later branch — which is how an earlier verdict in this
project became conditional on the scope of its own correction.

---

## Open items, flagged rather than assumed

1. **The engine and its depth must be frozen with the positions**, and both recorded. A shallow engine's
   "lost" is not a fact, and the whole gate rests on that judgement.
2. **The resignation threshold must be a number, not a phrase.** "Lost" is a centipawn range; it must be
   chosen, justified, and frozen before any run — or the criterion moves after the fact.
3. **Board state must come from a bundle, not from a spec.** Arena can build the board from `fen` and
   `move` today; there is no chess bundle in existence, and the field running now is card v4's R1
   fencing. **The renderer is not blocked on design — it is blocked on a first bundle.**
4. **`abandoned` vs `no-conclusion` may be hard to separate in practice**, and the distinction is real:
   one is a model that stops, the other a game that never resolves. The first bundle should be read to
   see whether the separation holds or whether one class swallows the other.
