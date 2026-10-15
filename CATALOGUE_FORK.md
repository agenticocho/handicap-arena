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
that needs a decision. The Chair reached the same reading independently and added two things worth
keeping:

**1. What the extra lines ARE.** (The gap is a live length, not a constant — re-derive it with the command below.) The arena's copy runs **League A through K**. All three cabinet copies
stop at **J**. So the delta is League K — with one correction from re-deriving it: it was **103 added and 2 removed** when measured at `f527da2`, of which exactly **one** is a league
header. The rest is League K's body plus the count-discipline note added the same day. **Those figures
are already stale and will keep moving** — the arena's copy is growing while the cabinets' copies are
unchanged since the fork. *(The rate once printed here — "14 lines every two hours" — was a single early
reading quoted as a constant. **So was my first replacement for it: this paragraph briefly said the
window average is "roughly double", which was itself unmeasured and wrong in the other direction.**
Measured properly, the growth is BURSTY and no single rate describes it: 123 lines across the whole
fork-to-now window is **0.7 lines/hour**, while the same file moved ~15 lines/hour during a single
evening's work. A rate is a reading with a window, and a bursty series has no rate without one. Both
figures and their windows are removed; the command above produces the only honest pair.)* *"League K is exactly the delta"* is
right about the substance and slightly too tidy about the arithmetic.

  ```
  git -C ~/workspace/ocho_arena diff --shortstat f42026b origin/main -- GAMES.md
  ```

  The one figure that has NOT moved is structural: **exactly one added line is a league header.**
  A length is a live reading; a header count is a fact about the shape of the change.

**2. The cabinets are not stale mirrors.** They are **64 to 82 commits AHEAD** of the trunk as well as
behind it — **working documents seeded from this file that have since grown their own content.**
`GAMES.md` is the one file they have not touched.

> **Quote the command, not the numbers.** These divergence counts move. **The figures once printed
> here have been removed rather than updated**, because updating them is the defect: an unanchored
> count beside an anchored table states the rule and violates it in the same breath. *(Caught by
> @zork, who noted that the cells got the sha while the sentence beside them did not — and that
> **"behind" is the half that grows while "ahead" holds**, so a "behind" figure is the one that
> strictly needs a revision pinned to it.)* A divergence figure is a **changing state** and travels
> as the command that reads it:
>
> `for b in cabinet/zork cabinet/sokoban cabinet/missile-command; do git rev-list --count main..$b; done`
>
> This is the same rule the day produced for run artifacts, applied to a repository fact.

Three consequences follow from the fork being undeclared rather than chosen:

1. **The fork point is invisible.** A reader of a cabinet's `GAMES.md` cannot tell how far behind the
   arena's it is, **and cannot tell it is behind at all** — the cabinet copy carries the same title, the
   same version line, and one fewer league, with nothing on the page saying a league is missing. *(A
   line count once printed here has been removed for the reason given above; the gap grows and the
   figure would have aged inside the sentence claiming it.)* Both documents
   look complete and neither says it is partial.
2. **Divergence is silent by construction.** Each cabinet has **both** commits the trunk lacks and
   lacks commits the trunk has — they have **diverged**, not merely fallen behind:

   | branch | behind `main` | ahead of `main` | measured at |
   |---|---|---|---|
   | `cabinet/zork` | 191 | 64 | `f527da2` — and it is already stale |
   | `cabinet/sokoban` | 133 | 82 | `f527da2` |
   | `cabinet/missile-command` | 191 | 64 | `f527da2` |

   **These numbers are a snapshot, not a fact** — the trunk was committing roughly once a minute
   while this file was being written (`f527da2` 13:44, `fa09db3` 13:45, `4a65bb0` 13:46), so any
   figure here is stale within the hour. That is why the cell carries **the sha it was measured at**:
   a divergence count without its revision is a number with no subject. Raised by @zork, who pointed
   out that his own earlier 180 and the later 191 were *both real* — they were different moments.

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
  **RECOMMENDED: C-plus — and the "plus" is three things, not one.**
  1. **Declare the fork point.** C alone declares the *relationship*.
  2. **Declare the per-file sync rule.** The four files are not on one rule: `GAMES.md` is behind by a
     length that keeps changing (115 at the last reading, while `DECISION_oracle_depth.md`, `FROZEN_CONSTANTS.json` and `FROZEN_PROMPT.txt` are
     **in sync with the arena's current copies.** Nobody chose that split, and a single fork-point line
     would hide it rather than record it.
  3. **Fix the masthead claim.** A cabinet's `GAMES.md` prints `# THE GAMES REFERENCE … Public
     document` — the arena's own masthead — so every reader is told they hold the complete public
     document. These four header lines are worth more than the rest of C, because **this is the part
     that is actively untrue on the page** rather than merely undeclared.

  Items 2 and 3 are the Chair's, arrived at independently; 3 is the one neither the model nor I had
  raised as a fix, only as evidence. The recommendation is recorded here with his name on it.

**The one thing that is not viable is the present state**: four copies, no relationship, and no
document that says so. That is the state in which an addition to either is unreadable later.

## Recorded

Measured 2026-10-15 while resolving a count discrepancy in a different exchange. The digests above
are from `git show <ref>:GAMES.md | sha256sum` and can be re-derived in one command.
