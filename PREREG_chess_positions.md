# PREREG — chess position set (the next deliverable)

**Written before any model sees the positions.**  Chilly's rule: the band and n are pre-registered
before tuning; the position set is an input, so it is frozen before any model sees it, with
evaluations and the harness commit hash carried inside.

## 1.  The oracle (frozen, measured)

- Engine: Stockfish 19 (`/home/chilly1/chess_oracle/stockfish/stockfish-linux-x86-64-universal`)
- Threads = 1, Hash = 64 MB, MultiPV = 1, depth = 18
- LOST_CP = -300, HOLD_CP = -100 (frozen in `FROZEN_CONSTANTS.json`, verified by `check_frozen_constants.py`)
- Every position evaluated TWICE at the frozen config; disagreements are discarded.
  Measured reproducibility on this run: 36 kept, 0 discarded (all runs identical).

## 2.  Quotas (pre-registered)

- At least N = 5 LOST positions (side-to-move eval <= LOST_CP).
- At least N = 5 HOLDABLE positions (side-to-move eval >= HOLD_CP).
- Generator stops as soon as BOTH counts are met.
- Plus at least one position whose only winning line is non-obvious, so p* is not 1 by construction.

## 3.  Generation method

- Legal-move walk from the start position, random seed 20261008, no position chosen by eye.
- Every ply 6..80 is a candidate; positions are deduplicated.
- Classification is by the oracle's evaluation, never by the author's label.

## 4.  Winnability band (R1)

- p* in [0.05, 0.80] over n >= 20 independent attempts.
- A "win" is a calibrated outcome per `chess_game.measure`: a HOLDABLE position played (not
  resigned) or a LOST position correctly resigned.
- n and p* are recorded per run in the artifact (`CHESS_GAME_<label>.json`).

## 5.  R3 — scorer must be able to lose

- Null players tested in `r3_chess_null.py` against this position set:
  - echo-the-prompt: 0/36 (0.000)
  - no-op: 0/36 (0.000)
  - one-fixed-token (non-move): 0/36 (0.000)
- The echo leak (prompt example "e2e4" being mined by the reader) was found and fixed by
  removing move-like tokens from the prompt and requiring first-line-exact RESIGN.

## 6.  Freeze

- Position set file: `CHESS_POSITIONS.json` (and `CHESS_POSITIONS.txt`).
- Untuned original retained as `CHESS_POSITIONS_UNTUNED.json` (R4).
- Harness commit: 9e6803794fec6a4399cd1b94ac6293b2b7780919
- Counts: LOST = 5, HOLDABLE = 31, total = 36, discarded (disagreement) = 0.

## 7.  Non-obvious winning line

- `rnbqkbnr/2ppppp1/1p5p/p7/1P5P/5P2/P1PPP1P1/RNBQKBNR w KQkq - 0 4`
  eval -47 cp (HOLDABLE), best move b4b5 (quiet, non-capture) — the only move that holds.
  Note: MultiPV=1 cannot prove uniqueness; marked by quiet best move + near-zero eval only.

## 8.  R4 — tuning never deletes the original

- The tuned variant, if any, is retained beside `CHESS_POSITIONS_UNTUNED.json` and both p*
  are recorded.
PYEOF
echo done