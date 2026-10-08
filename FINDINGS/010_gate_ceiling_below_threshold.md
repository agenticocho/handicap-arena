# FINDING 010 — the gate's threshold was chosen before the exclusions were known, and the exclusions cap the field below it

**Date:** 2026-10-08
**Status:** computed from the artifacts, not estimated. Recompute with the command at the bottom.

## The finding

`evaluate_v4.py` refuses to call a verdict on a field with fewer than **40 measured** entrants. That
number was chosen **before the run**, on the expectation of **46 entrants**, and it is correct as a rule:
*calling a verdict on a partial field is how v3's verdict became conditional on the scope of its own
correction.*

**But the exclusions cap the field below the gate.**

```
cardv4 entrants with a measurement   34   (at the time of writing)
entrants accounted for               42
entrants expected                    46
remaining entrants                    4

ABSOLUTE CEILING if every remaining entrant measures:  34 + 4 = 38
GATE REQUIRES:                                         40
```

**So the gate cannot be met on this population — not narrowly, and not by waiting.** The floor is above the
field's own maximum, and **no re-reading of this field changes that.**

## Why this is not the bar moving, and not a card failure

Three things make this a *result* rather than a rationalisation, and each is checkable:

1. **The gate was written BEFORE the run** (`CARD_v4.md`, frozen at `222baec`). It was not selected after
   seeing the count.
2. **The ceiling is COMPUTED from the artifacts, not argued** — it is `measured + remaining`, and the
   measured count is read from bundles that carry a `results` list.
3. **The remedy was stated before the number was known** — *"a population that can run, not a relaxation
   of the bar."* That sentence is already in `evaluate_v4.py` and in the CARD.

**The failure is in the GATE'S DESIGN, not in the card and not in the entrants:** a threshold expressed as
an absolute count of a *thinned* population cannot be compared against a field whose thinning is
size-correlated. **A gate on a fraction of the RUN would have been satisfiable; a gate on a count of the
MEASURED was not, because the two diverge exactly where the population is broken.**

## What it does and does not tell us

**It does NOT say the card passes.** The diagnostic stands as a diagnostic:
**C1 PASS (4 of 6 in band) · C2 FAIL (3 below 0.34) · C3 FAIL by construction · C4 PASS**, with
**Outcome 3 attached as a scope**: *C2 failed on this population, and the population is a candidate cause
this field cannot rule out.*

**It DOES say that v4's verdict is NOT CALLABLE from this field, and that the honest output is the
diagnostic with its scope** — exactly what the evaluator prints, and exactly why it refuses rather than
printing a verdict line it would then have to qualify.

## The rule this adds

**A gate set on an ABSOLUTE COUNT of a thinned population is a gate whose satisfiability depends on the
thinning — and the thinning is a property of the box, not of the entrants being graded.**

The next card should state its floor as a **fraction of the field that ran**, and name both denominators,
because this field produced three counts for one version and four for one run:
`46 expected / 42 accounted / 34 measured`.

## Recompute

```
python3 -c "
import glob, json
m = 0
for p in glob.glob('results/*cardv4*.json'):
    try: d = json.load(open(p, encoding='utf-8'))
    except Exception: continue
    if d.get('harness') == 'handicap-arena' and (d.get('results') or []): m += 1
print(f'measured {m}; ceiling {m + remaining}; gate 40')"
```
