# CARD v5 — a population that can run, and a gate that cannot silently tighten

**Written:** 2026-10-08, before the run. **Status:** criteria FROZEN at this commit.

---

## WHY THIS CARD EXISTS

v4 returned `UNSCOREABLE ON THIS FIELD` for exactly one reason: **the population could not complete.** Its
gate was an absolute count — *40 measured* — against a field of 46 whose ceiling turned out to be **38**.

**The mechanism, because it is the whole point of this card.** A gate of *40 of 46* is **87% of the field**.
When eight entrants failed to load, the ceiling became 38 — so the same gate silently became **100% of what
remained.** Nobody chose 100%. **An absolute count's satisfiability depends on the thinning, and it diverges
from a fraction exactly where the population breaks — which is where a completeness gate is needed.** The
remedy named at the time was **a population that can run, not a weaker bar.** This card is that population,
and a gate stated as a fraction so it cannot tighten unnoticed.

**AND THE ITEMS DO NOT CHANGE.** v5 re-measures **the same R1 items** as v4, on a population that can load,
**with the per-item clock on.** The card version bumps because the *run* differs — population, gate, and the
clock — not because the measurement does. **v4's item criteria are CARRIED, not re-chosen**, and that is
stated here so no reader can mistake a carried criterion for a new one.

---

## THE POPULATION, NAMED — with the exclusion rule stated

```
applicants    53   every .gguf in the model library
admitted      46   applicants minus the EXCLUDE_PAT classes (7 terms, 4 actual classes)
planned       38   admitted minus entrants with a RECORDED PERMANENT MEASUREMENT FAILURE
```

**THE EXCLUSION IS BY RECORD, NOT BY SIZE, and the reason is that the size hypothesis is already refuted.**
The eight permanent failures are **size-correlated AND NOT ONLY size-correlated** — six are 27 B, and **two
are small** (`Kev-4B` 3.03 GB, `laya_english_f16` 0.85 GB) — **while a 0.219 GB entrant measured cleanly.**
So excluding on size would **encode a hypothesis the record has already falsified.** Excluding on **record** —
*≥2 attempts, empty in every copy* — encodes **what happened**, which is the only thing we know.

**AND THE EIGHT ARE NOT RE-RUN.** They have failed **three times each** — original run, re-run, re-attempt.
That is **a recorded result, not a queue.** A fourth attempt would spend the night to re-confirm a number we
already have.

**THE RULE, STATED SO IT CAN BE RE-DERIVED RATHER THAN TRUSTED:**
> **planned** = entrants the library yields, minus any entrant whose **EVERY RECORDED ATTEMPT** produced an
> **empty** `results` list. **A serving failure is a MISSING VALUE, not a score of zero** — so this excludes
> entrants we have never measured, and it excludes them **by evidence, not by a guess about why.**

**AND THE RECORD IS NOT ONE FILENAME — this was found by measuring, and the canonical-path test is wrong.**

A failed bundle is **moved aside by name** before a re-attempt (`.attempt2.empty.json`, `_EMPTY_*.json`), so
**the canonical path is empty for exactly the entrants that must not be re-run.** Measured both ways:

```
by canonical path only   ->  7 excluded, 1 "no bundle at all", planned 39
by record, all name forms ->  8 excluded, 0 unrecorded,      planned 38
```

**The missing one is `Kev-4B-Q4_K_M` (3.03 GB).** Its canonical bundle was moved aside after the first
failure, so a path test reports it as never attempted — **and re-runs an entrant whose failure is already
recorded three times.** **A PATH TEST IS NOT A RECORD TEST**, and the exclusion must sweep **every name the
record takes**, not the one the runner would have written.

**So the derivation is: collect every file matching `<stem>_card*.json`, `<stem>*_EMPTY_*.json`, and
`<stem>*attempt*.json`; the entrant is excluded iff no file in that set carries a non-empty `results` list.**
Measured: **the eight carry 7, 7, 7, 7, 7, 7, 7 and 8 naming forms respectively** — the record of a failure is
not one row.

---

## THE DENOMINATORS, NAMED IN THE CARD

**v4 produced four numbers where the documents said one.** So all four are named here, and every criterion
that quotes a count **quotes its denominator with it**:

| denominator | meaning |
|---|---|
| **applicants** | every `.gguf` in the model library |
| **admitted** | applicants minus the exclusion classes |
| **attempted** | entrants the runner actually started (≤ planned) |
| **accounted** | attempted entrants carrying a bundle file |
| **measured** | entrants whose bundle carries a **NON-EMPTY** `results` list |

**`accounted` is not `measured`** — a bundle can exist and hold nothing. **`attempted` is not `planned`** — a
run can be interrupted. **A count of files is not a count of measurements**, and this card treats those as
different quantities everywhere.

---

## THE GATE — A FRACTION OF THE FIELD THAT RAN, STATED BEFORE THE RUN

**TWO ratios. Both required. Both computed from the denominators above.**

```
COVERAGE   attempted / planned   >= 0.95     the runner got through the field
YIELD      measured  / attempted >= 0.85     the population could run
```

**WHY A FRACTION.** A fraction of *what ran* is **self-normalizing**: if the field thins, the fraction
measures the thinning instead of silently tightening the bar. Every prior gate here was satisfiable or not
depending on a number that the population, not the author, decided.

**WHY THESE NUMBERS.** `YIELD ≥ 0.85` **fails v4's field** (38/46 = 82.6%) and **passes a healthy one**
(a loadable population should return near 100%). So it separates *a broken population* from *a working one*,
which is the only distinction this gate is for. `COVERAGE ≥ 0.95` catches an interrupted run, which is a
different failure from an unloadable population and must not be reported as one.

**BOTH ARE CARD-CRITERIA, NOT VERDICT-CRITERIA.** They decide **whether a verdict may be called**, never
**what it is.** *A completeness gate answers "did enough entrants produce a measurement", not "did the card
pass".*

---

## THE OUTCOME SCOPE, DECLARED BEFORE THE NUMBERS LAND

**Three outcomes, fixed now:**

1. **GATE UNMET** → `NO VERDICT — THE FIELD DID NOT COMPLETE.` Report the ratios, name which one failed, and
   **do not call anything a pass or a fail.**
2. **GATE MET, item criteria evaluated** → a verdict on the item criteria, **each quoted with its
   denominator.**
3. **GATE MET, but an item criterion fails while the population remains a candidate cause** →
   **`FAILED ON THIS POPULATION`**, stated as a scope. **Declared here, before the numbers, so it cannot be
   read as a hedge added after a result.**

**AND THE RULE THAT KEEPS OUTCOME 3 HONEST:** *a thin field that PASSES a monotone criterion is a STRICTER
result; a thin field that FAILS one is INDETERMINATE.* **A bound is a statement about a number, not about a
verdict** — so Outcome 3 may be attached to a **FAIL** and **never used to excuse one.** Direction needs the
missing **values**, not the missing **count**.

---

## THE ITEM CRITERIA — CARRIED FROM v4, UNCHANGED, AND MARKED AS CARRIED

| | criterion | status |
|---|---|---|
| **C1** | ≥4 of 6 items land in the **15–85% band** (discrimination, not saturation) | **carried from v4** |
| **C2** | ≥5 entrants below **0.34** (the floor is populated) | **carried from v4** |
| **C3** | no silent item-zeros: every failure carries a stored `failure_class` | **carried from v4** |
| **C4** | the card is the one named in the bundles | **carried from v4** |

**THEY ARE CARRIED BECAUSE THE ITEMS ARE THE SAME.** *A bar frozen before a run does not move because its
author moved the measurement* — and it does not move because the author ran a **second** time either. **If C2
fails again, it has failed twice on two populations, and that is a stronger result than either run alone.**

---

## WHAT THIS RUN IS FOR, SPECIFICALLY

**1 · TIMED ITEMS AT SCALE.** Fix 2 gave the per-item clock a carrier, and the previous field produced **6
item records carrying it out of 180** — because every entrant after the fix emptied at weigh-in. **This is the
first run that can produce timed items at scale.**

**2 · THE 8-MINUTE CLAIM GETS A VERDICT.** The transcript says *"a single move can take eight minutes."* The
audit marks it **UNVERIFIED**: the longest item carrying a clock is **69.3 s**, and eight minutes matches
**`BTL-4-IQ2_XXS`'s whole run at 471 s** — *an entrant duration attributed to a move.* **A run with the clock
on either refutes it or gives it the carrier it lacks. Either is a result, and both are worth having.**

**3 · A POPULATION THAT CAN RUN.** v4's verdict was blocked on this and nothing else.

---

## RESOURCE DISCIPLINE — BOTH PARTS OF THE CONTROL

**`MemoryMax` alone never bound. The cgroup was killed while under it, twice.**

```
MemoryMax=50G                      the ceiling
MemoryHigh=45G                     the soft bound
ManagedOOMPreference=omit          THE PART THAT MATTERS
```

**`ManagedOOMPreference=omit` takes the unit OUT of oomd's candidate set.** The ceiling is a number the kill
did not respect; removing the unit from consideration is a control the kill cannot ignore. **A ceiling above
the peak cannot protect a cgroup that is killed while under it.**

**AND THE GATE IS NOW AT ADMISSION.** `run_card.py` runs the game-contract check **before spawning any
model** and refuses on a NEW violation. **That is protection, not a hazard: the 301 historical violations are
counted separately and cannot block a run.**

---

## FROZEN

**This card's criteria, its population rule, and its gate are fixed at this commit.** Any change after the
first measurement lands is **a new card, not a revision to this one** — because *a criterion change after the
numbers is a file, not a criterion.*
