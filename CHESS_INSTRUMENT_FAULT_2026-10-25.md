# The chess cabinet rejected legal first moves and called it an entrant failure — 2026-10-25

Found while verifying the sitting-2 suite (`t_234b2387`, commit `ba9d660`). Chess was filed as
"9 plies total across four entrants, 3 illegal-move, 1 serving-failure". Two of those three
"illegal-move" terminations are wrong, and the third is unverifiable from the row it sits in.

## What the rows say

All four chess rows start from the same position:

```
fen  rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1     (the initial position)
```

and the cabinet terminated three entrants as follows:

| entrant | model's move | cabinet's claim | what is true |
|---|---|---|---|
| `bonsai-9b` | `e2e4` | "IS NOT a legal move in this position (20 are legal)" | **`e2e4` is legal.** It is one of the 20. |
| `ministral-3b` | `e4` | "IS NOT a legal move in this position (20 are legal)" | **`e4` is the SAN for `e2e4`.** Legal. |
| `mimo-9b` | `e4d5` | "IS NOT a legal move in this position (29 are legal)" | The count is wrong before the verdict is: **the initial position has 20 legal moves, not 29.** |

The rows then state, in capitals, `A FAILURE OF THE ENTRANT -- the move list is not supplied, so the
candidates must be derived.`

## Why this is the instrument and not the entrants

1. The legal-move count of 20 in the first two rows is **correct for the initial position**, so the
   engine produced a legal list and the extraction then failed to match a move that is in it.
2. The count of 29 in the third row is **impossible for that FEN**, so at least one row's legal list
   does not belong to the position recorded beside it.
3. Both failures occur at ply 0, on the one position in chess where the legal set is least ambiguous.
   Three different entrants, three different renderings (`e2e4`, `e4`, `e4d5`), all rejected.

An entrant cannot cause any of those three facts.

## Consequence

**Chess is INSTRUMENT-FAILURE for all four entrants and no chess number may be scored** — not the
ply counts, not `premature_collapse 0`, not `miscalibrated_persistence 0`, and not the "illegal-move"
class, which is not in `CARD_chess.md`'s frozen taxonomy and does not need ratifying while the
detector itself is unsound.

This is the same rule the suite applied correctly elsewhere and misapplied here: *a zero that is an
interface outcome is not a capability result.* Zork's `ministral` and `mimo` rows were correctly
marked INSTRUMENT-FAILURE on a replay-audit mismatch; the chess rows assert the opposite about
themselves in the same document.

## What a fix has to prove before chess runs again

- a control that feeds `e2e4` into the extractor on the initial FEN and must return a legal move;
- a control that feeds a genuinely illegal move (`e4d5` at the start) and must reject it;
- the reported `legal` count compared against the engine's own list for the same FEN, asserted equal,
  so a mismatched position cannot silently pass;
- `termination: illegal-move` may only be emitted when both controls pass in the same process that
  produced the row.
