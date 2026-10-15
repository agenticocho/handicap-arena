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

The question was posed as *two* catalogues **that share a filename but name different things** — the
arena's public event catalogue, and each cabinet's own games file. **That premise does not hold.**
Measured:

    arena now      8efe16c2d5ae8533   711 lines   11 leagues   "# THE GAMES REFERENCE ... v1.0"
    arena f42026b  207a7797a3da6ed5   610 lines   10 leagues   same header, same version line
    cabinet/zork   207a7797a3da6ed5   610 lines   10 leagues   <- IDENTICAL, not merely similar
    cabinet/sokoban        207a7797a3da6ed5
    cabinet/missile-command 207a7797a3da6ed5

A cabinet's `GAMES.md` is **not its own games file.** It is **the arena's `GAMES.md`, byte for byte,
at commit `f42026b`, with the same title and the same `Version 1.0 · Public document` line** — one
league behind the arena's own copy. This is not a homonym, and it is not two documents that happen to
be named alike. **It is one document, forked three ways, that nobody has declared.**

The distinction matters for the ruling. *"Two things share a name"* is a naming problem solved by
renaming. **"One document was forked and the fork was never declared"** is a provenance problem, and
renaming does nothing about it — the four copies would still be four copies at four different states.

It is also, on the evidence, the *second* time this exchange has produced the same shape. Much of
today's work went into the rule that **a run must carry the freeze it was produced under**. A
catalogue that was forked must carry its fork point for the same reason, and for the same
consequence: without it, a reader compares two states and reads the difference as a design decision.


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
