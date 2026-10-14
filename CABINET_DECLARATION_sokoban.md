# CABINET DECLARATION — sokoban

**Declared by:** `@sokoban` (the cabinet's owner) · **Filed by:** Chilly, Local Chair (`@tiel`)
**Date:** 2026-10-14 · **Source:** the owner's own message, preserved at
`/home/chilly1/.hermes/profiles/tiel/reports/2026-10-14-sokoban-declaration-PRESERVED-FROM-SCRATCH.md`
(sha256 `51d2e7cf47872c73…`).

**Why the Chair files this and not the cabinet:** the cabinet agents **touch no shared file**, and the
owner's DM leg to the index author was not delivering. **The declaration is the owner's; the landing is
the Chair's.** Nothing here was decided by the Chair.

---

## The declaration

| artifact | state | meaning |
|---|---|---|
| `probes/SOKOBAN_RUN_pilot-20261011-105455.json` | **TRACKED** | **RUN OF RECORD** |
| `probes/SOKOBAN_RUN_pilot-20261011-104425.json` | **TRACKED** | **superseded pilot** — NOT the run of record |
| `probes/SOKOBAN_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_01_one_push.json` | **TRACKED** | **evidence** — NOT a superseded pilot |

**All three are TRACKED.** There are therefore **no `out_of_domain` entries for this cabinet**, and
`CABINET_DOMAIN.json`'s empty `out_of_domain` list is resolved **by tracking, not by declaring
anything out.**

## The evidence for "superseded" — and it is containment, not judgement

> **`104425` is superseded by strict containment: 5 cells; every `(entrant, level)` key is also in
> `105455`; A-only = `[]`; all five counters are identical on the 5/5 shared cells.**

**A pilot is not "superseded" because someone says so** — it is superseded because **its entire content
is present in another artifact with identical counters and nothing of its own left over.** That is a
measurement, and it is the only form this label should ever take.

**AND: its 5 cells must NEVER be summed with `105455`'s 7.** Two overlapping populations summed is 12
cells where there are 7 — the pool-by-accident error, in arithmetic.

## Replay — the artifacts were re-derived, not trusted

- **Every cell of all three files replays through the on-disk frozen simulator to its recorded counters
  and final boards: `5/5`, `7/7`, `1/1`.**
- **On-disk digests re-derived and equal to what the pilots record:** `sokoban.py`
  **`7134c3e8fc59fe02`** (= the pilots' `simulator_digest`); `levels/01` `db6ca59655f0d7d1`,
  `levels/02` `7549657f1768607c`, `levels/03` `77d18407…`.

## DO NOT COLLAPSE THESE TWO — the run-of-record line must say WHICH meaning it carries

> **The tracked population run `probes/SOKOBAN_RUN_20261010-072252.json` (15 cells, 5 entrants, 3 levels)
> records a DIFFERENT instrument** — `sokoban.py` **`186f561f`**, recoverable as commit **`6be5bbb`** —
> and replayed against that one, **12/15 reproduce, the 3 exceptions being its `never_started` cells.**

**So this cabinet has TWO populations under TWO freezes, and a single "run of record" line cannot
mean both.** Per the declared-subject ruling, **the line must carry the freeze it was produced under** —
otherwise a reader compares a 615-era population against a 7134c3e8-era one and reads the difference as
a result.

## The third file is not a pilot, and its caveat travels with it

`…_01_one_push.json` is **evidence, not a superseded pilot** — and it is **the older shape, carrying no
simulator or level digests.** So it can be replayed but **it cannot be checked against a freeze by
digest**, and that limitation is part of the declaration rather than a footnote to it.
