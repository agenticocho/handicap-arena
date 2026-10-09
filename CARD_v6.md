# CARD — v6: ITEMS REBUILT ON THE ONLY AXIS THAT STILL DISCRIMINATES

**Frozen before any v6 measurement.** Written after the v5 verdict and before any v6 run, so the item
criteria below are a prediction about difficulty rather than a description of a result.

---

## THE SATURATION, STATED EXPLICITLY — THIS IS THE FIRST THING A READER OF THE V5 VERDICT NEEDS

**v5 did not fail because the models were bad. It failed because THE SUITE STOPPED MEASURING.** Stated here
in the card, not buried in a finding, because a reader arriving at "4 of 6 criteria FAIL" will otherwise
conclude something about the entrants that the numbers do not support.

```
v5, computed from the artifacts -- 37 entrants measured, 16 of them scored a PERFECT 1.000

  R1.1 ordered_sequence_with_a_gap     0.577   IN BAND   <- discriminates
  R1.2 order_is_the_content            0.910   saturated
  R1.3 duplicates_are_significant      0.856   saturated
  R1.4 absence_is_the_answer           0.568   IN BAND   <- discriminates
  R1.5 exact_key_set_under_a_bribe     0.892   saturated
  R1.6 exact_scalar_types              0.973   saturated

  C1 (band 15-85%, needs >= 4 of 6 IN BAND)   2 of 6   FAIL
  C2 (below 0.34, needs >= 5)                 3 of 37  FAIL
```

**AND THIS IS THE SECOND TIME.** `FINDINGS/004` recorded the same shape on 2026-10-07: *R1 89.9% SATURATED.*
Two saturated cards in a row is not a coincidence about a model population — **it is a property of the
items.** A suite most entrants pass ranks nobody, and ranking is the Arcade's entire purpose.

**AND THE CEILING WAS INVESTIGATED RATHER THAN REPORTED.** The perfect bundles were opened and read: the
answers are genuinely correct, three trials agreeing, clock carried, no failure reason. **So the ceiling is
real and not a scoring artifact. The finding is about the ITEMS, not about the models.**

---

## WHAT THE TWO SURVIVORS HAVE IN COMMON, AND WHY THE OTHERS DIED

**Read the six traps rather than the six scores:**

| item | what it tests | why it saturates |
|---|---|---|
| R1.2 | element ORDER | a reordering task; modern models reorder reliably |
| R1.3 | duplicates preserved | deduplication is a skill models now have |
| R1.5 | exact key set under a bribe | omission under an explicit instruction |
| R1.6 | scalar types | coercion (`"0042"` vs `42`) is drilled into these models |
| **R1.1** | **a gap in a sequence** | **the model must represent a MISSING thing** |
| **R1.4** | **a key that must not exist** | **the model must represent a MISSING thing** |

> **THE SATURATED FOUR TEST FORMAT COERCION — types, keys, order, dedup — WHICH IS EXACTLY WHAT INSTRUCTION
> TUNING OPTIMISES. THE TWO THAT SURVIVE TEST THE REPRESENTATION OF ABSENCE, WHICH IT DOES NOT.**

**THAT IS THE DESIGN RULE FOR v6 AND IT IS MIKE'S OWN WORDING: DIFFICULTY FIRST, NEW FACULTIES LATER.**
Every v6 item is on the absence-and-gap axis. **None introduces a new faculty**, because a new faculty
confounds difficulty with capability and would leave the next verdict unreadable for the same reason this
one was.

## THE SIX ITEMS — `tasks/v6/01_conformance.json`

**Each one raises a specific dimension of the axis the survivors defined. The `trap` field in the task file
carries the full argument; this is the map.**

```
R1.1  three_gaps_including_both_ends     ONE gap in three  ->  THREE gaps in five, at BOTH ENDS
                                          (an endpoint gap cannot be handled by a middle-gap rule)
R1.2  gap_that_must_survive_a_bribe       absence stated   ->  absence stated AFTER A PLAUSIBLE VALUE IS
                                          SUPPLIED, reachable two ways (catalogue and neighbour-average)
R1.3  nested_absence                      top level        ->  ONE LEVEL DOWN, inside a container that is
                                          itself fully present
R1.4  absence_in_an_array_position        a KEY disappears ->  the ARRAY LENGTH changes; position is the
                                          thing that must not be preserved
R1.5  gap_versus_required_value           one kind of      ->  TWO KINDS OF NOTHING that look identical:
                                          nothing              NOT RUN (key absent) vs RAN, FOUND NOTHING
                                                               (the string "none" -- key PRESENT)
R1.6  sequence_survives_the_gap           keep the element ->  keep THE ONE FIELD THAT IS KNOWN when the
                                          other is missing; the times are asymmetric so the array cannot
                                          be reconstructed positionally
```

**R1.5 IS THE SHARPEST AND IT IS THE ONE THE AXIS POINTS AT: the two survivors both asked "can the model
represent a missing thing", and R1.5 asks "can it tell a missing thing from a present thing whose value is
nothing".** Those are different claims, they look identical in a transcript, and telling them apart is the
faculty the four saturated items never touched.

## THE CRITERIA — CARRIED FROM v5 UNCHANGED, AND MARKED AS CARRIED

```
GATE       COVERAGE attempted/planned >= 0.95      YIELD measured/attempted >= 0.85
C1         per-item pass rate IN BAND 15-85%,  needs >= 4 of 6
C2         entrants below 0.34,                needs >= 5 of 37
populations applicants / admitted / planned / attempted / measured -- all four denominators named
exclusion  BY RECORD, not by size or path
field rule empty bundle = MISSING VALUE, not zero; re-run = RE-MEASUREMENT; every failure stays reported;
           no entrant dropped for failing
taxonomy   as frozen in CARD_chess.md, carried
```

**THE FLOOR IS NOT MOVED AND THE BAND IS NOT WIDENED TO MAKE v6 PASS.** A band widened after a saturation
is the same defect as a window widened to admit a sample: **it converts "the suite stopped discriminating"
into "the suite discriminates", by changing the question.** If v6 also saturates, that is a finding about
the axis and it gets reported as one.

**AND THE ITEMS ARE PREDICTED, NOT BACK-FITTED.** The prediction, recorded before the run: **at least four
of the six fall IN BAND (15-85%), and the hardest is R1.5** — because it is the only one whose failure mode
requires holding two representations of nothing apart, and no item in four prior cards asked for that.

## FROZEN

**This card, its item set, its band, its gate and its prediction are fixed at this commit.** The files are
named neutrally from the start (`tasks/v6/01_conformance.json`), which is where the label debt retires —
**forward, without rewriting a single recorded bundle.**
