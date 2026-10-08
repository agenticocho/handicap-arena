# CHESS — the catalogue event, specified for a reader who has none of our context

**Status:** design, ready for implementation. **Not** a card round. **No new card version.** CHESS is a
standalone Arena event (R4 in the catalogue), separate from the R1_fencing card round, and it is
deliberately not folded into any existing card.

**One line:** a tactics puzzle with a unique best move, scored by a reference engine, where **the move
list is carried in the bundle and the result is recomputed from it.**

---

## Why chess, and why it is not a metaphor

Chess came out right in the catalogue review for a mechanical reason: the event's MEASURE was read
first and the game followed from it. The measure is **near-miss discrimination under a hard rule set** —
and a chess tactics puzzle is exactly that: a position where nearly every legal move is *playable* and
only one is *best*, under rules that admit no opinion.

**CHESS is a CONTEST, not an INSTRUMENT.** It has a game, the bundle carries the game's state, and a
spectator can watch the game. That is the test: **can a stranger reconstruct the outcome from the
recorded bundle?** For a move list, yes — replay the moves. For a latency column, no.

## The six fields the catalogue requires

| field | value |
|---|---|
| **Measures** | near-miss discrimination under a hard rule set: can the model find the unique best move rather than a plausible one? |
| **Format** | N positions, one per trial, temperature 0. The model emits a move in SAN or a from/to pair. |
| **Scorer** | a reference engine (Stockfish or equivalent) in a subprocess. The move is legal-or-not, then best-or-not. **Not an LLM judge.** |
| **Null baseline** | the engine's own best move. A model scoring at the baseline has done nothing; a model scoring *at chance among legal moves* is the floor. |
| **Discriminates** | if every model finds every best move, the positions are too easy. If none does, they are too hard. Target: a middle band. |
| **Anti-gaming** | each puzzle has a UNIQUE best move verified by the engine at a fixed depth, so "any good move" cannot be claimed. And the model must not be given the engine's evaluation. |

## The recorded state — the sufficient-statistic requirement

**The bundle must carry, per puzzle:**

- `fen` — the position, so the puzzle is reproducible from the record alone
- `raw` — the model's own output, verbatim. **Non-negotiable**: see the failure below.
- `move` — the move as extracted from `raw`, plus the extraction's own decision
- `legal` — whether the move is legal in that position
- `best` — the engine's best move, and the depth it was computed at
- `outcome` — found / legal-but-not-best / illegal / unparseable / serving-failure

**The standard this event is held to, and it is the Arena's core standard applied to its own record:**
**no verdict may depend on data discarded at scoring time.** A chess event whose bundle keeps the score
but not the move list is unauditable — a reader cannot re-derive anything, and a scoring bug is
indistinguishable from a model failure, permanently.

## The failure taxonomy, and why it is explicit

An earlier round in this project shipped items scored 0.0 with **no reason and no raw**, because a
serving exception hit a `continue` that discarded both. One entry's zero was unexaminable forever. The
vocabulary above exists so that "we never got an answer" and "it answered wrong" are different records:

- **serving-failure** — the request raised. A MACHINE result, not a capability result. Must name the
  exception type, because a timeout, a connection reset and an HTTP error are three different failures.
- **unparseable** — no move could be extracted. The raw is kept so the extractor can be audited; an
  extractor that cannot reproduce its own decision is the instrument deciding the verdict.
- **illegal** — a move was extracted and the position does not permit it.
- **legal-but-not-best** — the near-miss, and the interesting case.
- **found** — the unique best move.

**A model reported as unable to play and a model reported as playing imprecisely are different claims.**
Getting them confused is the most misleading thing a benchmark can say.

## What the audience watches

The game *is* the product. The move list replays: the puzzle position, the model's move placed on the
board, the engine's answer beside it. A spectator sees, in one frame, **the move that was played and the
move that was better** — which is precisely the measure rendered as a picture.

That is why this event needs no decoration. The score and the spectacle are the same object.

## Open items, flagged rather than assumed

1. **Which engine, and at what depth.** The depth is load-bearing: a shallow engine's "best" is not a
   fact, and a deep one is slow. Depth must be frozen alongside the positions and recorded in the bundle.
2. **Puzzle sourcing.** Puzzles must be pre-verified unique-best and frozen before any run, or the
   criterion moves after the fact — which the project forbids.
3. **The null baseline needs a number, not a sentence.** "Chance among legal moves" is stateable but not
   yet measured; it must be computed for the chosen position set before the event's bar is written.
4. **`raw` must be stored by the scoring path that fails, not reconstructed afterwards.** The failure
   this document keeps describing is exactly a reconstruction that could not happen.
