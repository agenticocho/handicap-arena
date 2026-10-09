# THE ARCADE — the frame, as settled by Mike

**Status: the frame has moved. Three documents in this repo contradict it and are listed below as
outstanding.** This file records the change where the rule lives, so a reader finds it before they find the
documents it supersedes.

## What changed

**Board games and real sports are replaced as the frame by THE ARCADE.** Every test is fronted by an
**8-bit cabinet or home-system title**, or by an **8-bit original of a sport's official rules.**

**Why this is a better frame than what it replaces: the game supplies the ORACLE, so nobody grades
anything.** That is the same standard every surviving event in this catalogue already had to meet — a
scorer that is a parser, an execution, or a ground truth, never a model judging models. The Arcade is that
standard moved from the scorer up to the frame.

## The two play formats — declared per event

| format | what happens |
|---|---|
| **A — the model is the player** | the cabinet is paused while it thinks. One decision at a time, against a fixed state. |
| **B — the model writes the POLICY** | the policy plays. The model produces the thing that produces the moves, and is scored on the run. |

**These are different measurements and must never be pooled** — the same rule as `card_version`. Format B
is the one that makes an agentic claim rather than a decision claim, and a Format B score quoted beside a
Format A score is two different events sharing a name.

## Three sourcing classes

1. **An 8-bit cabinet or home-system title** — the original game, its own win condition.
2. **An 8-bit original of a sport's official rules** — the ruleset supplies the oracle, not the sport's
   presentation.
3. **A home-system port of a title from class 1 or 2** — where the port's own numbers are the oracle.

## The selection filter worth keeping

**Prefer titles whose win state is already a NUMBER or a TIMER** — a score, a move counter, an oxygen gauge,
a count of the getting-up. Those give a **ready-made oracle and no invented rubric.**

This is the strongest operational filter in the whole catalogue discussion, because it is decidable before
anything is built: **if the cabinet's own screen already displays the outcome as a number, the event needs
no scoring design at all.** Rubrics are where gaming gets in.

## Outstanding — three documents that contradict this frame

| document | what it says now | what it needs |
|---|---|---|
| **`GAMES.md` B2c** | chess as the calibration event | **SETTLED — chess keeps it.** Mike: chess keeps calibration, chess is game 1, no rush on Punch-Out. The axis is the one where scoring needs an oracle, and chess holds the only third-party one — and the only **continuous** one (a gradient of confidence against the truth; Sokoban's solver is a boundary, asked once). **PUNCH-OUT takes PERSISTENCE/RECOVERY; SOKOBAN takes IRREVERSIBLE PLANNING.** |
| **`EVENT_chess.md`** | a standalone catalogue event with its own measure | **becomes a CABINET, or drops.** Its state schema is still correct and still reusable; its *event* status is what is in question. |
| **`GAMES.md` / `README.md` framing** | ten leagues, 56 events, board games and sports | **moves to the Arcade**, with the three sourcing classes above and the per-event play format. |

**Nothing is deleted. A rule change is recorded where the rule lives** — which is why this file exists and
why the two documents above carry a pointer rather than a gap.

## What the read-rule check said about the FROZEN verdicts

Arena ran the read rule (`compare wins/trials, never the stored aggregate`) across **all 119 graded entries**
and **the frozen verdicts do not flip:**

```
119 graded entries
 52 carry a stored aggregate that disagrees with their own wins/trials
 v2 criterion 2 reads 11 either way
 v2 criterion 3 reads 2 either way
```

**Nothing was rewritten.** A criterion is not re-scored when its reading turns out to be improvable — which
is the same rule as a criterion not moving because its author moved the measurement. The 52 are evidence
that the rendering rule holds broadly; they are **not** a reason to restate a verdict that was already
published.
