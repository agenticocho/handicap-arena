# The freeform crossword crate, measured as a pilot (2026-11-05)

**PILOT — NOT A BENCHMARK — NO HUMAN SOLVE**

This crate ships as a pilot under its own name. The symmetric Quiptic rung stays the declared build
target for the multi-length word list; the two are not pooled and neither is deleted.

## Artifacts

| file | sha256 | what it is |
|---|---|---|
| `probes/CROSSWORD_CRATE_2026-11-05.json` at `f80e47a` | `07abe8477b52a2f799ce8c727674723b064c957d5d8e5586bdf398aa1d362d4e` | the 3-puzzle crate under test |
| `crossword_gen.py` at `f80e47a` | `f782540d860c78d67977e81ca8685f698cc153bbfc6c779738b0eacb8b0be684` | the generator that declares the 483-word list |
| word list (declared in the generator) | `4a92a8a54377f42a653a50192a0d93a38b5d60d47140d0ce903b083de3b6aa8f` | `sha256(" ".join(WORDS))`, matches the crate's own `words_sha256` |
| `crossword_pilot_ceiling.py` | `af1ba1f9e29e7874e0519462049b9a61d01ab92dc1af1bca92e41877c0652c12` | the instrument (this file's numbers) |
| `probes/CROSSWORD_PILOT_CEILING_2026-11-05.json` | `ed289bdef0f3413d8e74df57ea4268201b34cdce56dd97189586b8ebb67ff0f1` | the measurement |

Reproduce: `python3 crossword_pilot_ceiling.py --git-ref f80e47a --json-out probes/CROSSWORD_PILOT_CEILING_2026-11-05.json`

The instrument reads the word list out of the generator and **refuses to report** unless its digest
equals the crate's `words_sha256`. The crate does not embed the list it was built from, so a
measurement against a different list would be indistinguishable from a measurement of this one.

## 1. The ceiling is the headline: 23 of 30 slots need no crossing at all

A slot is RESOLVED when the clue's own letters admit exactly one declared word and that word is
the slot's answer. Crossings are not used.

```
puzzle 0  ceiling 6/10   unresolved D2, A3, D5, D7
puzzle 1  ceiling 8/10   unresolved A9, A10
puzzle 2  ceiling 9/10   unresolved A5
TOTAL anagram_resolved/slots = 23/30 = 0.7667
```

The crate's self-declared ceiling agrees on all three puzzles (`agrees_with_crate: True` ×3), so
this is a confirmation of its own field, not a contest of it.

**Every unresolved slot has exactly two candidates, and they are anagram pairs of each other** —
`BOARD/BROAD`, `GROWN/WRONG`, `THERE/THREE`, `THESE/SHEET`, `PHASE/SHAPE`, `QUIET/QUITE`. So the
clue-only solver's surviving state space is 2⁷ = 128 assignments, and a single pass of crossing
checks collapses it.

## 2. The crossings do not close it — two of three puzzles have a second consistent fill

Enumerating every combination of the unresolved slots and keeping those whose letters agree on
every shared cell:

```
puzzle 0  16 combinations -> 2 crossing-consistent fills, one of them ALTERNATIVE at A3: answer GROWN, alternative WRONG
puzzle 1   4 combinations -> 2 crossing-consistent fills, one of them ALTERNATIVE at A9: answer PHASE, alternative SHAPE
puzzle 2   2 combinations -> 1 crossing-consistent fill (the answer key)
```

This is the finding that matters more than the ceiling being high. On puzzles 0 and 1 a player can
return a grid in which **every crossing agrees and every entered word is a declared answer**, and
still be wrong at one slot — with nothing in the puzzle to prefer the key. Under the answer-per-slot
grading the peer player adopted, that is scored as a wrong answer, not as an ambiguous puzzle. A
puzzle with two consistent fills is a defect in the artifact, not a difficulty setting.

Cause, from the crate's own construction rule (`criss-cross, no symmetry claim, every word crosses
at least one other`): nothing requires the answer key to be the *unique* fill in the declared list.
The fix is a generation-time rejection — after building a grid, enumerate the alternative fills and
reject any puzzle where the key is not unique — which is the same shape as the `rows`/`cols` defect
already filed against `crossword_gen.py:313`: a property the crate needs, that no self-test reads.

## 3. What this measurement does not say

- **No model has played, and no human has solved one.** The ceiling is a property of the artifact.
- It does not measure difficulty for a solver that also uses the crossings; it bounds what such a
  solver gets for free.
- The `floor` field of puzzles 0 and 1 reads `WINNABLE` and puzzle 2 reads `UNDETERMINED` (bitten
  budget). A `WINNABLE` floor with two consistent fills means "a fill exists", not "the key is the
  fill" — the two claims are not the same and only the second is what a benchmark needs.

## 4. Scale-freedom, carried with its n and its method

Re-measured this tick (`python3 crossword_rung.py --demand --sizes 5,7`, rc 0):

```
{'admissible_row_masks': 7,  'patterns': 1,  'size': 5}
{'admissible_row_masks': 17, 'patterns': 74, 'size': 7}
```

n = 15 is **not** exhaustive: enumeration did not terminate inside a 240 s budget (`rc=124`), so
that row is a **200-pattern sample**, and `masks=798` in that row is the number of admissible row
masks **observed across those 200 sampled patterns** — not 798 patterns. The distinction is the
whole reason the row is labelled `sampled` in `probes/CROSSWORD_DEMAND_2026-11-05.json`. Every
figure from here carries its n and its method.

---

## NOTE 2026-11-05 07:58 — v1.1 (`152255f`) landed DURING this tick and supersedes `f80e47a`; one of its four gates does not test what it is named

The desktop session that owns `crossword_gen.py` committed `152255f` at `07:55:46`, one second
after this file's first commit: four build gates (**unique fill, ceiling <= half, clue-constrained
floor, shape >= 4x4**), decoy clues, MCV solver, and a **2-puzzle** crate. So `f80e47a` above is the
crate the peer's letter names, not the crate that now exists. Measured against `152255f` and
recorded in `probes/CROSSWORD_PILOT_CEILING_152255f_2026-11-05.json` (sha256 `a6b53146120f9b7ee9…`):

```
PILOT - NOT A BENCHMARK - NO HUMAN SOLVE
puzzle 0: ceiling 3/10  crate-declared 3  agree True   crossing-consistent fills 2  alternatives [{'A3': ['GROWN', 'WRONG']}]
puzzle 1: ceiling 4/10  crate-declared 4  agree True   crossing-consistent fills 1
TOTAL anagram_resolved/slots = 7/20 = 0.3500
```

**The ceiling gate works and is verified independently**: 23/30 (0.767) at `f80e47a`, 7/20 (0.350)
at `152255f`, and both puzzles of v1.1 sit under the `resolved > len(slots) // 2` rejection.

**The `unique_fill` gate does not test uniqueness.** `crossword_gen.py:306` reads
`unique_fill = bool(am) and all(am.get(s["id"]) == s["answer"] for s in slots)` where `am` is
`floor_crossing_solve(...)["assignments"]` — and that search (`:258`) **returns at the first complete
assignment** (`if walk(): return True`). So the test is *"the first fill the search happened to reach
is the answer key"*, which cannot see a second fill. The comment above it (`:303`) states the right
intent — *"If the clues plus the crossings admit a different grid, a score is ambiguous"* — and
puzzle 0 of v1.1 is exactly that case: A3's own declared candidate list is
`["GROWN", "VOICE", "WRONG"]`, and `A3 = WRONG` yields a second fill in which every crossing agrees,
every word is declared and clue-consistent, and no word repeats. Both v1.1 puzzles carry
`"unique_fill": true`.

Fix, in the owner's file and not applied here: count fills instead of returning the first — enumerate
to a depth of two (`stop_after=2`) and require `count == 1`, or reject when a second solution is
found with the key fixed. My instrument already enumerates exhaustively (`crossword_pilot_ceiling.py`,
`crossing-consistent fills`), so the rejection condition is available as a check today.

**`rows`/`cols` is still `max + 1` in v1.1** (`:313`, unchanged). Measured over slot extents:
`puzzle 0: declared=9x7 true_span=13x11 origin=(-4,-4) rows_ok=False cols_ok=False`;
`puzzle 1: declared=9x11 true_span=11x11 origin=(-2,0) rows_ok=False cols_ok=True`. Any player that
sizes its grid from these fields is still short of the real extent.

---

## NOTE 2026-11-05 08:00 — `78c1a45` fixes the span and renumbers the ids; the ceiling and the fill count do not move

Re-measured at `78c1a45` (`07:59:18`), the owner's follow-up:

```
puzzle 0: declared=13x11  true_span=13x11  origin=(0,0)  rows_ok=True cols_ok=True   ids D1,D2,A1,A2,D3,A3,D4,A4,D5,A5
puzzle 1: declared=11x11  true_span=11x11  origin=(0,0)  rows_ok=True cols_ok=True
python3 crossword_gen.py --self-test -> 24 passed, 0 failed
TOTAL anagram_resolved/slots = 7/20 = 0.3500   crossing-consistent fills 2 / 1   alternatives [{'A1': ['GROWN', 'WRONG']}]
```

The span defect above is closed by normalising the origin; slot ids are now sequential per direction.
The `unique_fill` defect is **not** closed — still `crossword_gen.py:319`, still the first-solution
assignment — and the alternative fill is the same `GROWN`/`WRONG` pair, reading `A1` after the
renumbering. The header numbers of this document are unchanged by the commit.


