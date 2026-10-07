# GAME CONTRACT — when a game is a measurement and when it is a costume

**Date:** 2026-10-07 · **Author:** Ocho (CFO), design owner · **Status:** normative, with an
enforcing test

## The directive

> *"They all must have a visual game... board games to combat sports to summer/winter olympics to UFC
> to any extreme sport. That's the spirit of The Arena."* — Mike

The game is **not decorative**. It is the product. Which means the game has to be **the measurement**,
not a picture drawn over one.

## The standard

**Can a stranger reconstruct the game from the recorded bundle?**

- **Yes** → the game *is* the measurement, and the visual is honest.
- **No** → **the visual is a skin over someone else's result.**

That second case is not a cosmetic defect. It is **the same failure as a count carried as a literal**:
a claim with no carrier, displayed as though it had one. A front end rendering a chessboard over a
tool-selection score is asserting something the record does not contain.

**Strengthened into something checkable:** the recorded state must be a **sufficient statistic for
the score** — *the scored outcome can be recomputed from the recorded state alone.* Not "the state
is related to the outcome"; the state **reproduces** it. A move list reproduces a chess result. A
latency column does not reproduce a boxing result.

## The two event classes

This split is not a concession to laziness. **It is forced by the standard above**: an INSTRUMENT
event given a `game` name would fail the reconstruction test, so the class must exist.

| class | has a game? | watchable? | ranking? | bundle carries |
|---|---|---|---|---|
| **CONTEST** | yes | yes | ranked, with belt and division | **the game's state** |
| **INSTRUMENT** | **no** | **no, deliberately** | **never ranked** | its measurements |

**League I is INSTRUMENT and that is correct.** The catalogue already says those events *"don't exist
to rank models; they exist entirely to expose flaws in the testing harness. A clean, boring,
negative result here is a massive success."*

> **Those are the officials, not the athletes.** Nobody watches the scales get calibrated. But a
> sport without them is not a sport, it is a show.

**Dressing an INSTRUMENT event as a game is the worst version of the retrofit — the referee in a
costume.** So INSTRUMENT events carry **no belt, no division and no rank**, and that exclusion is a
**hard partition in the render path**, the same way `card_version` is. A front end that merely
*labels* them will eventually rank a scale-calibration against a boxing match. (Credit: the class
split and the officials framing are Chilly's.)

## The rule

**An event may declare a `game` only if it also declares the bundle fields that carry that game's
state. `game` set + empty `game_state_in_bundle` = FAIL.**

**And the name is a LABEL on the state, not a parallel declaration.** The state schema is the primary
artifact; `game` is derived from it. This is the day's own rule — *derive, don't carry* — because a
name kept alongside a schema drifts from it exactly the way a hand-maintained count drifts from what
it counts.

**Scope, stated so the rule does not overreach:** the catalogue may name a game **as a
specification** — that is a target, not a claim. **The check binds BUNDLES.** A bundle that claims a
game and carries no state is a lie in the record; a catalogue entry that names one is a plan.

## The sport category determines the math, so pick the game from the math

| class | examples | math | status |
|---|---|---|---|
| **OLYMPIC** — absolute | 100m, long jump, weightlifting | every entrant measured independently against a **frozen instrument** | **the Arena's native shape.** The card already is this |
| **COMBAT** — head-to-head | boxing, MMA, UFC | contested, but **pairing-dependent**: the score depends on who you drew | **a different event class. Needs Elo or round-robin.** Expensive to measure honestly |
| **TEAM / RELAY** | H league | the unit is the team; the footprint is the **sum** of members | already stated in the catalogue, and correct |

**COMBAT is a trap and must be treated as one.** A score that depends on who you played is
**FINDING 002's twin** — *two entrants measured against different machines*, one level up. **No
COMBAT event ships without a stated n and a confidence interval.** Model-versus-model play is
brilliant to watch and expensive to measure honestly; free play comes later, as its own event, with
its own acceptance criteria.

## What the Arena already gets right

Worth noticing, because it is a stronger foundation than it looks: **the Arena already speaks combat
sport.** Weight classes (Featherweight → Heavyweight) and belts (white → red) are martial-arts
vocabulary, and **divisions are assigned by measured footprint** — a real measurement, not a label.
The metaphor system is half-built and internally consistent. It needs the games to be **real rather
than named**, which is the whole of this document.

## Enforced by

`test_game_states.py` — reads every card task file and every bundle, and fails on a game name with no
state behind it. **Positive control included**: the test is verified to fire on a reintroduced
`metaphor`-without-state, so it cannot become a check that passes by being unable to fail.

**First finding, from running it against today's repo:** the card's three rounds carry `metaphor`
names (`FENCING`, `CHESS`, `PIT STOP`) and **no game state whatsoever**. They must therefore either
**lose the metaphor** or **gain the state**. `R2_chess` is the live case: it is a tool-selection task
named after a game it does not play, and the real chess event (R4, tactics puzzles scored by a
reference engine) is the one that earns the name.
