# THE CATALOGUE FORK — evidence for the open ruling

**Status:** measured from disk on 2026-10-15. This file records evidence, not a decision. The
decision is the Chair's, and it is the one question left open from tonight's exchange.

## What was asked

> **Q1: does the arena's event catalogue feed the cabinets, or are they separate?** `GAMES.md` at
> the arena root is a public 61-event reference, and each `cabinet/*` carries its own `GAMES.md`
> plus its own frozen criteria. **Nothing derives one from the other.** Until you rule, anything
> added to either is an addition to an undeclared relationship.
> — the Chair, 2026-10-15

## What the disk says

The question was posed as *two* catalogues. It is not two. It is **one catalogue, forked three ways,
and the arena has moved on alone.**

    arena commit f42026b            GAMES.md sha256 207a7797a3da6ed5   610 lines
    cabinet/zork            GAMES.md sha256 207a7797a3da6ed5   610 lines
    cabinet/sokoban         GAMES.md sha256 207a7797a3da6ed5   610 lines
    cabinet/missile-command GAMES.md sha256 207a7797a3da6ed5   610 lines

    arena main today        GAMES.md                 711 lines   11 leagues  (+ League K)

All three cabinets hold a **byte-identical copy of an arena commit**, `f42026b`, which is an exact
ancestor still present on the trunk. So each cabinet's catalogue is not an independent document that
happens to resemble the arena's — **it is the arena's, at a fixed point, and none of them has taken
a change since.**

## Why this reframes the ruling

The two options on the table were *"the arena feeds the cabinets"* and *"they are separate"*. The
measurement says neither is what is happening:

- **Not feeding.** Nothing derives one from the other, and no cabinet has moved since the fork.
- **Not separate.** They are byte-identical to a common ancestor; they began as the same document.

What actually happened is **a fork that was never declared**, which is a third thing and the one
that needs a decision. Three consequences follow from the fork being undeclared rather than chosen:

1. **The fork point is invisible.** A reader of a cabinet's `GAMES.md` cannot tell it is 101 lines
   behind the arena's, or that the arena has a league the cabinets have never seen. Both documents
   look complete and neither says it is partial.
2. **Divergence is silent by construction.** Each cabinet has **both** commits the trunk lacks and
   lacks commits the trunk has — they have **diverged**, not merely fallen behind:

   | branch | behind `main` | ahead of `main` |
   |---|---|---|
   | `cabinet/zork` | 191 | 64 |
   | `cabinet/sokoban` | 133 | 82 |
   | `cabinet/missile-command` | 191 | 64 |

   There is no mechanism that would report this, and no document that names the fork point.
3. **Every addition compounds it.** League K is the worked example: it landed in the arena's copy
   only, so there are now four `GAMES.md` files where two are identical and one is ahead, and the
   relationship between them is undeclared.

## The three end states, stated so one can be chosen

- **A — the cabinets are the authority.** The arena's catalogue is retired to a historical reference
  plus the entrant/event-structure layer; each cabinet owns its own games outright. Requires deciding
  what happens to the arena's 711-line copy.
- **B — the arena is the authority.** Cabinets take the arena's catalogue forward, on a declared
  cadence, with the fork point named. Requires a mechanism, since none exists today.
- **C — the fork stands and is declared.** Each cabinet's copy is frozen at `f42026b` on purpose and
  documented as such, with new games authored per cabinet and never merged back.

**The one thing that is not viable is the present state**: four copies, no relationship, and no
document that says so. That is the state in which an addition to either is unreadable later.

## Recorded

Measured 2026-10-15 while resolving a count discrepancy in a different exchange. The digests above
are from `git show <ref>:GAMES.md | sha256sum` and can be re-derived in one command.
