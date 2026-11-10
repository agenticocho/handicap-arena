# STUMP — Fair-Budget Calibrated Result: spark4b-q4 vs smol3b

**Grammar:** illposed-v1, digest `e0a456b34c5964b5b6709e754c1dd597b622bb4f8bea510c77d1996f0a7b2c83`
**Trace:** `traces/stump_illposed_fairbudget.json` (60 rows, 1 run, calibrated fixed set)
**Pairing:** spark4b-q4 (4B, Q4_K_M, 2.4 GB, :8381) vs smol3b (3B, :8380)

## Run parameters (recorded on every row)

- `n` = 30 questions (15 well-posed + 15 ill-posed), both models answer the same fixed set
- `max_tokens` = 2000 on all 60 rows
- `thinking` = true on all 60 rows
- Errors: 0, timeouts: 0, budget hits: 4 (non-fatal)
- `secs_total` = 566.28 s
- `gen_tokens` total: spark4b-q4 16,904 (min 129, max 2,000, 4 rows hit the 2,000 cap); smol3b 4,950 (min 39, max 907)
- Memory warrant: 9.19 GB available at start → 6.58 GB at end, against a 3.0 GB void threshold (AVAILABLE memory = free+inactive+speculative+purgeable, not Pages free; below threshold means VOID, not a model result)

## Result

| Model | Params / size | Score | Ill-posed | Well-posed |
|---|---|---|---|---|
| spark4b-q4 | 4B (Q4_K_M, 2.4 GB) | 29 / 30 | 14 / 15 | 15 / 15 |
| smol3b | 3B | 25 / 30 | 10 / 15 | 15 / 15 |

Winner: spark4b-q4 by 4 points. Both models clear the null.

## Per-model failure breakdown (ill-posed, 15 each)

- **spark4b-q4** (1 miss): refused 14, wrong 1. The single miss — *"She has the same number of apples as she originally had"* — reasons to a non-answer instead of declining (classified `wrong`: no refusal phrase, no invented number, no parametric expression).
- **smol3b** (5 misses): refused 9, parametric 1, confabulated 2, malformed 3.
  - No answer three times: 3 malformed (`None`).
  - Guessed `0` twice: 2 confabulated (filled the missing quantity with an invented number).
  - Parametric once: `x - 2` (solved around the gap — correct, reclaimed by the parametric fix).
  - The refusal-vocabulary extension reclaimed one answer carrying the phrase "unsolvable" ("The problem is unsolvable with the given information.").

## Null reference

The null is 15 / 30 (a model that refuses everything scores 15 — all 15 ill-posed correct, all 15 well-posed wrong). Both models clear it (spark4b 29, smol3b 25); the 4-point gap is real, not a floor effect.

## Classifier fixes (verified in `stump.py`, not redone)

1. `REFUSAL_PHRASES` extended with: `unsolvable`, `unresolvable`, `no solution`, `cannot be solved`, `can't be solved`, `not solvable`, `insufficient data`. (Reclaimed one of smol3b's answers.)
2. `parametric` no longer gated behind `is_refusal`: a bare algebraic answer such as `x - 2` is solved around the gap and is parametric by definition. (Reclaimed one of smol3b's answers.)
3. Typographic apostrophes normalised (`’` U+2019 → `'` U+0027) before substring matching; both Spark variants emit `can’t`.

Regression check (all pass): `13` and `0` → confabulated; `...` and `None` → malformed; `Not enough information` → refused; `x - 2` → parametric; `INSUFFICIENT` → refused.

## Cabinet playback

The cabinet (`stump_cabinet.html`) now plays `spark4b-q4` (A, :8381) vs `smol3b` (B, :8380). The four outcome lanes (REFUSED / PARAMETRIC / CONFABULATED / MALFORMED) name why each answer lands where it does. Served from `http://localhost:8765/stump_cabinet.html` (python http.server, pid 21901). Clear any saved progress in `localStorage` (`stump_recordedA` / `stump_recordedB`) before a fresh run — stale qwen2b answers from the previous pairing would otherwise replay.