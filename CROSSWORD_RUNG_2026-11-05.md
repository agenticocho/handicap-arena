# The Quiptic rung, stated as checks (2026-11-05)

Mike's word was **"generate"** — our own grids, our own clue sets, our own declared word
list, on the Quiptic difficulty specification, with no licence inquiry. Condition 3 of that
decision (`state the rung by construction, not by assertion`) has to come first, because a
generator that enforces a specification nobody has written down is enforcing a caption.

This document reports what the rung is as executable structure, and what the instrument
measured when it was pointed at the rung itself. It does **not** report a filled puzzle: no
real word list yet exists that can fill a rung pattern, and that is the finding.

**Artifacts**

| file | sha256 | what it is |
|---|---|---|
| `crossword_rung.py` | `4b83fdc7950df79fb9f316a40f0df5b5c16d6623554a9a0dd0bec19d1fae1a08` | the rung, the validator, the pattern generator, the fill, the clue permutation |
| `lexicon/quiptic_seed.tsv` | `930c26a0160e6fa7e9d407de6b7f27a4b70bc31c9c79ad7c8d48859868ff6cea` | the declared word list, 54 entries, word + clue |
| `probes/CROSSWORD_DEMAND_2026-11-05.json` | `ebc1a7cef98a3c8030ac4267a670c0007f3427fe2cfef988e00989d0e81b2a79` | the pattern-demand measurement for n = 5, 7, 15 |

Reproduce: `python3 crossword_rung.py --self-test` → `20 passed, 0 failed`;
`python3 crossword_rung.py --demand --sizes 5,7,15 --write probes/CROSSWORD_DEMAND_2026-11-05.json`.

## 1. The rung is a list of checks a grid fails by name

`RUNG` is data. `validate()` is the only authority on whether a pattern is in the rung, and
it returns named violation codes, never a boolean:

- `SYMMETRY` — some cell is a block and its 180° partner is not.
- `CORNERS` — a corner is not a block.
- `SHORT_RUN` — an across or down run of white cells shorter than `min_run` (3).
- `DISCONNECTED` — the white cells form more than one 4-connected region.
- `BLOCK_FRACTION` — block count outside `[0.10, 0.25]` of the grid.
- `TOO_FEW_SLOTS` — fewer than 6 answers.
- `UNCHECKED_CELL` — a white cell in no run of one of the two directions.

The generator re-validates every pattern before it yields it. A constructor that trusts its
own construction is the exact defect this file exists to prevent: the self-test proves the
three rejections fire on hand-built grids that must fail (a broken symmetry, a two-cell run,
a wall), not merely that a valid grid passes.

## 2. The fairness rule is not an independent condition — it is implied

A cryptic convention says every answer should be at least half checked. At this rung that
rule can never fail on its own: a white cell with no white vertical neighbour would itself be
a vertical run of length 1, which `min_run = 3` already forbids. So `min_run >= 3` implies
every white cell is checked, and the "checked" requirement carries no evidence — it is a
consequence, not a test. The self-test asserts the implication on generated 7×7 patterns and
asserts the unchecked cell is real when `min_run` is relaxed to 2, so the implication is not
vacuous. A condition that cannot fail independently may not be cited as a property.

## 3. The rung is not scale-free, and that is measured, not argued

`--demand` reports, per size, how many patterns the declared rules admit and what entry
lengths those patterns demand:

```
n=5  exhaustive patterns=1   masks=7   slots=10-10 block_frac=0.16-0.16
n=7  exhaustive patterns=74  masks=17  slots=14-16 block_frac=0.102-0.2449
n=15 sampled   patterns=200  masks=798 slots=28-74 block_frac=0.1022-0.2489
```

Three consequences, each of which changes what the generator has to do:

**(a) At n = 5 there is exactly one pattern, so there is nothing to choose.** The family is a
single grid, ten answers: six of length 5 and four of length 3. The six 5-letter entries
interlock in a 3×3 double word square, which is why the fill is hard rather than merely long.

**(b) At n = 7 the family is 74 patterns with lengths 3 through 7.** Every one of those
lengths must be in the declared list before any pattern is chosen, or the generator is
rejecting every pattern it can produce.

**(c) At n = 15 the family is too large to enumerate** — exhaustive enumeration did not
terminate inside a 240 s budget (`rc=124`), so the row above is a 200-pattern sample and is
labelled `sampled` in the JSON. The sample spans 13 distinct entry lengths, 3 through 15.
Both statements travel with the number, because "200 patterns" is a sample size and "the
family" is not.

## 4. The binding constraint on generation is the word list, not the grid rules

The validator can already accept patterns at all three sizes. What cannot proceed is the
fill: the declared list covers lengths 3 and 5 only (54 entries), and

- the single n = 5 pattern will not fill from it — `fill()` returns no assignment, and the
  search exhausts; 30 five-letter words is *more* than the 6 entries the pattern needs, so
  size of the list is not the criterion. The criterion is prefix structure: the middle 3×3
  must be a double word square, and a list of that size supplies too few usable three-letter
  prefixes.
- n = 7 and n = 15 require 6- and 7-letter entries (and up to 15-letter entries) that the
  list does not contain at all.

So the next artifact is **the declared word list**, sized from the length demand of the size
the crate intends to ship, and validated by a fill attempt rather than by a count. A word
list is not adequately described by its length or its histogram; it is described by whether a
rung pattern can be filled from it.

## 5. A clue permutation is only meaningful inside a length class

The published-vs-permuted comparison is supposed to estimate memorisation: re-map the clues
and see whether the score moves. But a clue states its answer's length. A permutation that
moves a clue onto a slot of a different length produces a puzzle that is wrong on its face,
and detectable by counting cells — so `permute_clues` permutes only among entries of equal
length. This bounds the estimate: what the control measures is substitution **within a length
class**, not across the whole clue set. That restriction is part of the measurement and is
stated here rather than left in the code.

## What would overturn this

- A pattern at n = 5 other than the one reported. The enumeration is exhaustive over
  `min_run >= 3`, `rot180`, corners blocked and block fraction in `[0.10, 0.25]`; relaxing any
  of those four rules adds patterns, and the claim is scoped to the rung as declared.
- A fill of the n = 5 pattern from a list of the sort described. That would show the
  constraint is list quality rather than list structure, and would move the finding.
- Exhaustive enumeration at n = 15 terminating with a pattern count; the 200-pattern sample
  would then need to be replaced, since a sample and a census are different numbers.
- A human solve that finds the structural rules irrelevant to difficulty. Nothing here
  measures difficulty; it measures structure. The human-solve sample that the decision asks
  for has **not** been produced, and this document does not stand in for it.

## Declared limits

- The fill/number/permute code path is tested with a word list read off a filled grid. That
  is circular by construction and proves the machinery, not that a real list can fill a rung.
- No generated puzzle ships from this document. The seed list is 54 definition-style clues
  authored here; it is not a Quiptic-grade clue set and is not presented as one.
- `p*` and headroom at generation time — the reason generation was called the stronger option
  — are **not** measured here. They need a crossword solver with a declared word list, which
  is a separate instrument and does not exist yet.

## NOTE 2026-11-05 07:45 — a concurrent session built the crate, and the two designs are not interchangeable

A second session of this profile was working in this repository at the same time as this
document was written. It committed `f80e47a` (`2026-11-05 07:41:19 -0800`, *Crossword crate v1*)
carrying `crossword_gen.py`, a 3-puzzle crate and `probes/CROSSWORD_CRATE_2026-11-05.json`.
That work is not superseded by anything here and nothing in it was touched. Two collisions are
recorded because they affect what §4 can claim:

1. **`f80e47a` swept two files of this document's lineage into its own commit.** It ran a
   tree-wide add while `lexicon/quiptic_seed.tsv` (written `07:33:59`, before the crate's
   commit) and an intermediate `crossword_rung.py` were untracked, so both appear in that
   commit. Nothing of the crate's was overwritten — `lexicon/` did not exist before this
   lineage created it — and the current HEAD carries the final versions (`8df0af3`). The
   history is muddied; the artifacts are not.
2. **The crate's declared word list is single-length.** Measured from the committed blob:
   `git show f80e47a:crossword_gen.py` → `f782540d860c78d67977e81ca8685f698cc153bbfc6c779738b0eacb8b0be684`,
   then the list is read out of it: `words=483 distinct=483`, `length_histogram={5: 483}`.
   The rung's only n=5 pattern demands `{3: 4, 5: 6}`; supplied `{3: 0, 5: 483}`; and
   `fill_on_n5_rung_pattern=NONE`.

So §4's sentence *no real word list yet exists that can fill a rung pattern* is now scoped
and, in its strong form, corrected: a real 483-word declared list **does** exist, and it still
cannot fill a rung pattern — not because it is small, but because it is **one length**. The
crate is a criss-cross (freeform) grid whose header states *there is no symmetry claim*; the
rung is a 180°-symmetric barred grid with `min_run >= 3`. The two are different structures,
and the single-length list is exactly what makes the freeform shape cheap to fill and what
makes the rung shape unfillable from it.

That is a structural incompatibility, not a stylistic preference, and it is a decision rather
than something either session should settle by deleting the other's artifact: one crate cannot
be both shapes under one name.

