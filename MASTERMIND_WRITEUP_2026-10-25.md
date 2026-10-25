# Mastermind: the decoder never reads the feedback — and the instruments that had to be fixed to see it

Chilly (Local Chair) · 2026-10-25 · two seats, two boxes, one shared cabinet

**The finding, in one sentence.** On a pre-registered 16-board Mastermind fixture, no arm consults
the feedback it is given more often than chance after the first turn: each plays a canned opening
book indexed by turn number. Q4 `spark` makes zero consistent guesses in 144 chances; the 9B makes
two in 56, both at turn 2, both the same code; `bonsai` makes three in 128, against a per-state null
of 3.3%. Everything any seat does after turn 2 is repetition.

This is a finding about **ignition** — whether a decoder ever engages with its input — not about
reasoning quality or model ranking. It was reached only after eight instrument defects were found and
fixed, six of them in the analysis rather than the models, and the corrections are the more
transferable result.

---

## 1. What was measured, and on what

```
fixture      16 pre-registered secrets, 4 pegs, 6 colours, 10 turns
             each board solvable, unique solution, labels recomputed at run time
harness      temperature 0.0, thinking disabled, one shared parser, prompt pinned by digest
interview    every guess scored twice: CONSISTENT (does it match all feedback shown so far?)
             and CLAIM (what the model said about itself) — claim never awards a solve
```

| arm | compute path | answered | consistent | turns ≥ 2 | turns ≥ 3 | re-entry density |
|---|---|---|---|---|---|---|
| `spark-4b Q4` | GPU -ngl 99 | 160/160 | **16 (all turn 1, vacuous)** | **0/144** | 0/128 | 2/160 = 0.0125 |
| `ornith9b` (peer seat) | his Mac | 64 | 10 (8 turn 1 + **2 at turn 2**) | **2/56** | 0/48 | 13/64 = 0.203 |
| `ternary-bonsai-9b` PQ2_0 | GPU -ngl 99 | 160 | 26 (16 + 7 + 3) | 10/144 | **3/128** | — |
| `ternary-bonsai-9b` | CPU -ngl 0 (control) | 160 | 30 (16 + 14) | 14/144 | 0/128 | — |
| scripted control | — | **88** | **88 (100%)** | 72 | 56 | — |

Turn 1 is **one identical code, 16 of 16 games, on every arm** (`0123` / `0000` / `4015` by seat).
That alone is not a model reading a board; it is a book indexed by turn.

The aggregate zero: `P(K ≤ 0) ≥ 0.0317` under a Markov union bound, `0.0377` under within-game
independence, **neither significant in a family of eight tests**. Stated as the weaker number,
because a bound is not a p-value.

## 2. What the score does NOT say

- **Not a ranking.** No entrant separated on capability in any of seven cabinets. Where a difference
  appears it is one board in sixteen (`ornith` on Lights Out) or a shape (`Q4` stuck decoder vs the
  9B oscillator), not a score.
- **Not quantisation.** The first reading — "the collapse is a 4-bit artefact" — died when the 9B
  collapsed identically and its two hits landed on the same turn.
- **Not a target.** The re-entries to the opening code match a frequency-weighted null (exp 5.72,
  obs 6). The walker dwells on the code it has seen most; it is not aiming at one.
- **Not separable into one number per seat.** With `R` fixed, `K = R − D − A`; the classification has
  rank two, so every scalar proposed as "the" seat number is a function of `(D, A)`.
- **Not a difference in returning, past the third lag.** Measured over both row sets, the return ratio
  collapses as the lag threshold rises — `96 vs 27` (3.56x) at lag > 0, `2 vs 1` (2.00x) at lag > 4,
  and `2 vs 0` in Q4's favour at lag > 6 — while the *capacity* ratio stays at exactly `4.00x` at
  every threshold, because it is just sixteen ten-turn games against four. Past lag 3 the comparison
  measures how the two row sets were cut, not how either model walks.

## 3. The eight instrument defects, and what each cost

| # | defect | what it produced | the rule it generated |
|---|---|---|---|
| 1 | constant "2.09% random floor" | a strong-looking result from one state's null | the null belongs to the **state** |
| 2 | per-state null applied to repeated guesses | a "below chance" reading that was structural | a repeat of an excluded code has probability **exactly 0** |
| 3 | band moved between arms (turn 3+ vs turn 2+) | a difference that belonged to the boundary | a comparison holds the **band** fixed |
| 4 | distinct-count over press sets, not answers | 1 instead of 2, hiding the out-of-language rows | a count **names its object** |
| 5 | stored flag trusted instead of recomputed | a finding resting on an inherited field | a stored field's **disagreement count** is the alarm |
| 6 | two arms compared across different denominators | `6` that was a difference of counts | a count names its **arity** |
| 7 | exposure index counting rows where the event is impossible | `3.37×` where the true figure is `4.36×` | an exposure may not include ineligible rows |
| 8 | "the class is lag ≥ 2" — true by definition | an empirical claim that could not fire | a containment that **cannot fire** is not a control |

Two of these were found by applying the other side's own test back to their control; one was found by
a disagreement counter that fired while the number looked fine; one by a peer noticing that a
sentence stated a rule one section after stating it correctly.

## 4. The criteria a cabinet must meet before its numbers count

1. **A control arm that scores a known answer**, in the same process that produced the rows.
2. **Every claim carries its denominator, band and arity** in the cell that states it.
3. **Stored fields are re-derived**, and the disagreement count is printed even when it is zero.
4. **A containment must be able to fire.** A check whose predicate is true by construction certifies
   nothing; the reach of a check is computable from the data before the bug exists.
5. **A bound prints its direction** and is never quoted as if it were a measurement.
6. **Claim and state are separate columns**; a solve counts only if the cabinet's own state check
   agrees.
7. **An instrument failure is not a zero.** Zork's `ministral`/`mimo` rows are marked
   INSTRUMENT-FAILURE, not failure; `mimo`'s Mastermind zero is an interface outcome — its guess was
   in the bytes, glued to a `<|end_of_thinking|>` tag.

## 5. One cabinet must not be scored at all

**Chess** is INSTRUMENT-FAILURE for all four entrants. From the initial position it rejected
`e2e4` and `e4` as illegal while reporting the correct 20-move legal count, and reported a 29-move
legal set for a position that has 20 — three faults on ply 0, across three renderings, from three
models, with the row asserting `A FAILURE OF THE ENTRANT` in capitals.
See `CHESS_INSTRUMENT_FAULT_2026-10-25.md` for the four controls a fix must pass.

## 6. What would change the finding

- a fixture where turn 1 carries information (a mid-game start), so "book" and "reading" separate;
- a prompt that scores only the turn after a **novel** feedback vector;
- a model small enough to be a genuine floor, run to a much larger `n` than 16 boards;
- a seat that consults the feedback **above** its per-state null after turn 1. Measured turns ≥ 3:
  Q4 `0/128`, the 9B `0/48`, `bonsai` GPU `3/128` (2.3%, against a 3.3% null — below chance, so not
  evidence of consulting either). No arm has yet cleared its own null on a turn that carries feedback.

## 7. Provenance

```
cabinet      probes/mastermind/  (fixture, parser, one-file harness, sha 3bc8e7685522ffa3)
rows         suite/runs/mastermind_*.json (GPU), probes/mastermind/rows_*.json (published CPU)
peer bytes   mastermind_ornith9b_8b/8d/8e.json, held in chair-link/archive at their declared digests
record       MASTERMIND_RESULTS.md, eighteen dated NOTEs, each a correction made in the open
```

Every number in this document was recomputed from the row files by the author of this document, not
carried from a letter. Where the two boxes disagreed, both figures are shown with the object each
counts.
