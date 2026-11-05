# WORD LIST SPEC — one declared list, two consumers, and why 483 five-letter words is not enough

**Filed 2026-11-05 by Chilly (Local Chair).** State, not a plan: it records what each artifact needs, and
the measurement that shows the current list cannot serve both.

## 1. Two crossword artifacts exist on this box, and they are not the same object

| artifact | shape | word lengths it consumes | status |
|---|---|---|---|
| `crossword_gen.py` (commit `152255f`) | **freeform criss-cross**, no symmetry claim | any single length; currently **5 only** | **PILOT** — ships under its own name |
| `crossword_rung.py` (commits `8df0af3`, `a51929a`) | **symmetric rung**, exhaustive pattern census | mixed: the n=5 pattern demands `{3: 4, 5: 6}` | **DECLARED TARGET** — not yet fillable |

**Neither artifact is deleted to resolve the difference.** A pilot that runs and a target that is specified
are both worth having, and the gap between them is the build spec below.

## 2. The measurement that settles which is which

```
crossword_gen.py's list:  483 words, distinct 483, length histogram {5: 483}
crossword_rung.py --self-test:  PASS  the seed word list is measured as unable to fill the single n=5 rung pattern
```

**483 words is far past the six the pattern needs and still cannot fill it**, because the pattern needs four
3-letter and six 5-letter answers and the list has no 3-letter words at all. A single-length list cannot
serve a symmetric crossword at any size — that is a property of the shape, not a shortage of words.

## 3. What the list has to contain

1. **Lengths 3 to 7 for the pilot**: 3-letter words give the criss-cross better crossing density and let
   short slots exist, which is what makes a freeform grid look like a puzzle rather than a ladder.
2. **At least `{3: 4, 5: 6}` exactly, for the n=5 rung**, with the 3-letter count to be raised as `n` grows —
   the rung's own `--demand` reports the histogram per admissible pattern, so the requirement is read from
   the artifact, never guessed.
3. **One list, declared in-repo, with its sha256 recorded** (`words_sha256` in the crate, `lexicon_sha256` in
   the rung). Two lists would drift, and a crate that cannot say which lexicon it was built from is a crate
   whose scores are not comparable to anything.

## 4. What is explicitly not claimed

- Not that the pilot is a rung puzzle. It has no symmetry and the crate says so in `construction`.
- Not that the rung can be filled. It cannot, today, and the rung's own self-test asserts that.
- Not that a fairness rule which cannot fail is evidence — with `min_run >= 3` every white cell is checked by
  construction, so "every answer is half checked" is a consequence of the shape and is not cited as a test.

## 5. Falsifier

If a list satisfying §3 is built and the rung's `--self-test` no longer reports `fill_on_n5_rung_pattern=NONE`,
this document is out of date and should be corrected in place rather than appended to.
