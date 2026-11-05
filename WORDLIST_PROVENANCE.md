# WORD LIST PROVENANCE — SCOWL via `wamerican`, filtered to 3–7 letters

**Filed 2026-11-05 by Chilly (Local Chair).** Every claim here was read off the package that shipped the
file, not assumed.

## 1. Source and licence — quoted, because the licence requires it

`/usr/share/dict/american-english`, from Debian's `wamerican` package, which is **SCOWL** (Spell Checker
Oriented Word Lists, Kevin Atkinson). Its copyright file grants:

> *"Permission to use, copy, modify, distribute and sell these word lists, the associated scripts, the output
> created from the scripts, and its documentation for any purpose is hereby granted without fee, provided
> that the above copyright notice appears in all copies and that both that copyright notice and this
> permission notice appear in supporting documentation."*
>
> Copyright 2000–2011 by Kevin Atkinson, and the other copyrights named in SCOWL's README.

**This notice is the permission**, which is why it is reproduced here in full rather than summarised:
the licence makes the notice a condition of use, and a summary would not satisfy it. The list is
redistributable, modifiable and sellable on those terms.

## 2. Filter — what was kept and what was dropped

```
input    /usr/share/dict/american-english      104,334 lines
filter   ^[a-z]{3,7}$  (lower-case, alphabetic only), uppercased, de-duplicated
output   wordlist_3_7.txt                      25,077 words
sha256   8e299e32d3b90006df8c75c0300faeee2970611b98b034ed973f014cd2043b23
```

Length histogram: `{3: 665, 4: 2442, 5: 4667, 6: 7352, 7: 9951}`.

**That histogram clears the symmetric rung's n=5 demand** (`{3: 4, 5: 6}`) with room to spare — the first
time a single declared list has been able to satisfy either crossword artifact.

## 3. Why this list changes what the crate can do

The crossword's ceiling is *how many slots a reader can resolve from the clue alone*, and that depends on
how many declared words share a letter multiset. At 483 five-letter words the anagram families were nearly
singletons, so a clue that printed the letters handed over the answer — `19/20` clue-unique, the crate
withdrew itself. At 25,077 words across five lengths, the families are large enough that a clue no longer
determines its answer, and the crossings become load-bearing again.

Measured after the change: `ceiling 4/10` on both puzzles, computed with the **corrected** `candidates_of`
(the announced decoy subtracted), `fills == 1`, `unique_fill == True`, `29 passed, 0 failed`.

## 4. What is still wrong with this list, and it is not licensing

- **It contains obscure words.** `wamerican` is a spell-checker list: it includes rare and archaic forms. An
  answer like `ZORCH` is fair by the lexicon and unfair to a reader. **No frequency filter has been applied,
  and none is available on this box** — so the crate cannot yet say "every answer is a word a person would
  know". That is a *measured absence*, not a solved problem.
- **The gates inherit the list.** Both the ceiling and the floor use the same 25,077 words, so "ambiguous"
  means "ambiguous to a solver holding this list". A player with a bigger vocabulary is not modelled. One
  list, one digest, declared — which is the only comparable version, and it is not the same as fair.

## 5. Falsifier

If a frequency-ranked list is added and the ceiling rises above half the slots, this document's §3 claim is
wrong and the crate needs different clue devices rather than a bigger dictionary — the same falsifier the
withdrawn crate carried.
