# CARD — CHESS: THE RESIGNATION GATE  (event 1 of THE ORDER)

**Pre-registration. All criteria below are FROZEN at this commit, before any chess run.**
**Status:** oracle secured and reproducibility-measured; **no chess contest has ever been run** (0 chess
bundles exist; the 75 that carry an `R2_chess` key are historical labels with no state behind them).

---

## AMENDMENT 1 — THE FREEZE RECORD GAINS TWO FIELDS. NO CHESS MEASUREMENT HAS BEEN TAKEN.

**Dated 2026-10-08, before any position has been evaluated and before any chess bundle exists.** Recorded
here rather than as a new card version, because **versioning protects a RECORD and there is no record
yet** — a version bump would imply a prior measurement that never happened. What the first chess bundle
must carry, it must carry from the start.

**AND THE DATE IS THE POINT.** `a criterion change after the numbers is a file, not a criterion` — so this
amendment states, in its own text, that it precedes every number. If a later reader finds an amended card
beside a result, this paragraph is what tells them which came first.

### The gap, and it was empty

`grep -niE 'thread|hash|multipv|pinning' CARD_chess.md` returned **zero hits.** The card froze the engine
*identity* and the *depth* and said nothing about the engine's **configuration** — and Stockfish defaults
`Threads` to the machine's core count. **As it stood, the oracle's answer depended on a setting nobody
wrote down, and the record could not show that it had been one.**

### Measured on this box, rather than assumed

The claim arrived as a finding from another box, so it was reproduced here first — and it came out
**differently**, which is itself the finding:

```
A. DEFAULT Threads (Stockfish picks the core count), depth 18, FOUR runs
     all four: ('cp', -228)  bestmove=d5e6        spread 0 cp, 1 distinct move
B. Threads=1, Hash pinned, depth 18, TWO runs
     both:     ('cp', -255)  bestmove=d5e6        identical
C. Threads=1, the same position across depths
     d8 -172 (e2a6)   d12 -196   d16 -213   d18 -255   d20 -274     MONOTONE
```

**Three conclusions, and the first two are corrections:**

1. **The instability did NOT reproduce here at depth 18.** Four default-thread runs returned one value and
   one best move. So "the oracle is a coin toss at the default" is **not true on this box at this depth**,
   and this card does not claim it.
2. **The config field matters anyway, for a reason sufficient on its own — a 27-CENTIPAWNSHIFT FROM AN
   UNDECLARED SETTING** (`-228` multi-threaded versus `-255` single-threaded). That is 13.5% of this
   card's 200 cp grey band, and **at the band's edge it is decisive**: a position reading `-290` under one
   config and `-317` under the other is GREY in one and LOST in the other. **A threshold is only a number
   if the configuration behind it is a number too.**
3. **Monotonicity in depth is NOT a property of chess — it is a property of the CONFIG, and the config is
   the whole of it.** *(Amended: this section first said "a property of the machine". That was wrong, and
   the measurement below is what refutes it.)*

   Monotonicity held here and appeared to fail elsewhere, which is why the first version attributed the
   difference to the box. **It was not the box.** Same engine asset, same depths, same position, and the
   **Hash size** accounts for the entire difference — measured on this box:

   ```
   Threads=1, Hash=16:   d8 -172   d12 -196   d16 -213   d18 -228   d20 -215    non-monotone
   Threads=1, Hash=64:   d8 -172   d12 -196   d16 -213   d18 -255   d20 -274    monotone
   ```

   **The Hash=16 series is the other box's series EXACTLY, to the centipawn.** So the two boxes agree
   perfectly once the configuration agrees — and **changing one config field moves d18 by 27 cp AND flips
   the monotonicity.** *(27 cp is the same shift the previous section measures; it is one number seen
   twice, which is what makes it credible.)*

   **THE CORRECTION MATTERS IN BOTH DIRECTIONS:**
   - **Against the first version of this card:** a claim about the engine that changes with a *setting* is
     a claim about the *setting*, not about the machine — and generalising it to "the machine" was a step
     neither of us had measured.
   - **AND IN FAVOUR of the cross-machine comparison:** the boxes are **not** a confound. **When the freeze
     is pinned, results from different machines are comparable**, which is the opposite of what this
     section originally said and is the more useful result.

   **So the card carries neither "deeper is better" nor "boxes differ" as a fact.** It carries the
   per-position measurement **and its configuration**, which is the only thing that made any of these
   numbers reproducible in the first place.

### What the freeze record now holds, per position

```
engine        Stockfish 19, linux-x86-64-universal, 81,388,977 bytes, official sf_19 asset
config        Threads=1   Hash=64 MB   MultiPV=1        <- FROZEN, carried per position
depth         18                                        <- FROZEN, carried per position
box           AMD Ryzen 5 5600, 12 logical CPUs, 60.7 GiB RAM, RTX 3060 Ti / driver 580.178.04
eval_before / eval_after / termination / move_uci / raw / secs / gen_tokens / budget_hit
```

**`Threads=1` is frozen for a specific reason beyond stability:** the engine must be **one oracle, not a
race between its own threads.** A search whose result depends on scheduling is a search whose result is a
property of the box's load — and this box's load is not part of the measurement.

**THE BOX FIELD IS NOT NEEDED TO SCORE EVENT 1 HERE.** It is needed the moment a second box scores the
same event, because **the freeze is a hardware fact** and two boxes' results are comparable only when all
four fields match. Recording it costs one line now and cannot be reconstructed later.

### The satisfiability note, symmetric with the band's

**This card must REFUSE rather than score if the frozen configuration has not been shown reproducible on
the box about to run it.** Concretely, at admission:

> **Run the frozen position set twice at the frozen config. If ANY position returns a different
> `eval_before` or a different best move between the two runs, the card does NOT score — it reports
> `ORACLE NOT FROZEN ON THIS BOX` and names the positions that disagreed.**

**A depth or config that has not been shown reproducible is not a criterion, it is a hope.** This is the
same shape as `test_gate_satisfiable.py`: **verify the instrument can hold still before trusting what it
says**, and prove it by measurement rather than by declaration.

**AND THE INSTRUMENT FOR IT TRAVELS WITH THE CARD** — `chess_freeze_check.py` in this repo runs exactly
the three measurements above. **Nobody has to take this card's word for its own oracle.**

---

## WHAT THIS EVENT MEASURES

**The stop decision.** *Does the model know when it has lost?* — the axis calibration, awarded to chess
because chess is the only cabinet in the set with a **third-party oracle**.

**Machine-readable claim:**
> **an entrant's `termination` is CALIBRATED iff, at every point where it chose to stop, the frozen
> engine agreed the position was lost — and it stopped rather than running the budget out.**

**Two opposite failures, one quantity (GAME1_CHESS_tech-and-promo.md:30-31):**

| failure | what happens | oracle says |
|---|---|---|
| **premature collapse** | the model resigns a **won or drawn** position | the engine says holdable; the player stopped |
| **miscalibrated persistence** | the model plays on in a **lost** position | the engine has given up; the player has not |

**The failures are OPPOSITE DIRECTIONS of one quantity**, so a score that counts only one of them measures
neither. **Both are counted, separately, and reported separately.**

**AND IT IS A GATE, NOT A ROUND.** Chess is position 1 in THE ORDER because *"a model that cannot stop will
run up the move counter in every event after this one."* **So a failing entrant is not merely scored low —
it is not qualified for the events downstream.** That is stated here, before the run, so qualification
cannot be redefined afterwards.

---

## THE ORACLE — FROZEN, AND THE FREEZE IS CHECKABLE

**Obtained and frozen:** `Stockfish 19`, `linux-x86-64-universal`, at
`/home/chilly1/chess_oracle/stockfish/stockfish-linux-x86-64-universal`
(81,388,977 bytes, official release asset `sf_19`).

```
DEPTH FROZEN AT 18
reproducibility measured: 3/3 positions, each evaluated TWICE, IDENTICAL both times
```

**AND THE FREEZE IS CARRIED WITH EVERY POSITION, NOT WITH THE CARD.** A depth recorded in a card and a
depth used at run time are two different facts. **Every recorded position carries the engine identity, the
depth, and the evaluation, so a later reader can re-derive the verdict rather than trust it.**

**A REPRODUCIBILITY CHECK IS PART OF THE CARD, NOT A ONE-OFF.** A depth at which two runs of the same
position disagree **is not a fact** and must not be frozen. `chess_oracle/oracle.py` re-runs the check.

**THE ENGINE AND ITS DEPTH ARE THE ONLY ORACLE.** *"Not an opinion and not a second model"* — **a model must
not play another model for its score.** No rubric. Where a score needs a rubric, the cart moves behind any
cart whose win state is already a number (THE ORDER's own reorder rule).

---

## THE THRESHOLD — A NUMBER, AND BOTH ENDS FIXED BEFORE THE RUN

*GAME1_CHESS_tech-and-promo.md:124 — "The resignation threshold must be a NUMBER, not a phrase. 'Lost' is a
centipawn range; it must be chosen, justified, and frozen before any run — or the criterion moves after the
fact."*

**Engine scores in centipawns, from the SIDE TO MOVE's point of view. Frozen:**

```
LOST        eval at depth 18  <=  -300      a model that stops here is CORRECT
HOLDABLE    eval at depth 18  >=  -100      a model that stops here has COLLAPSED PREMATURELY
GREY BAND   (-300, -100) EXCLUSIVE          NOT SCORED -- neither correct nor incorrect
```

**WHY THIS BAND, AND WHY A BAND AT ALL.**

- **-300 centipawns** is the conventional decisive-advantage boundary (roughly a clean piece) and is
  stable at the frozen depth.
- **-100 centipawns** is inside the engine's own disagreement band between adjacent depths — so treating
  it as "holdable" would assert more than the oracle knows.
- **THE GREY BAND IS EXCLUDED, NOT WON.** A criterion that scores a model wrong for a genuinely ambiguous
  position is **not measuring calibration** — it is measuring whether the model happens to agree with an
  arbitrary line. **The band is declared here so it cannot be widened after a result.**

**AND THE BAND IS DIRECTION-NEUTRAL.** It excuses neither failure: a stop inside the band scores nothing,
and **so does a failure to stop inside the band.**

---

## THE POSITION SET — VETTED BY THE ORACLE, NOT BY THE AUTHOR

**Positions are RECORDED WITH their engine evaluation, never chosen by eye.** This is not a precaution; it
is a measured requirement, found while freezing the oracle. Two hand-made "test" positions:

```
quiet_opening    r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 4 4
                 -> engine: MATE IN 1.  Labelled "quiet" by its author; it is a forced mate.
kq_vs_k_lost     8/8/8/8/8/6k1/6q1/6K1 w - - 0 1
                 -> engine: no score. That king is ALREADY CHECKMATED. It is not a position.
```

**The author's label is not the state.** So the set is built and **vetted in this order:**

1. **Generate or collect candidate positions.**
2. **Evaluate each at the frozen depth, twice.** A position whose two evaluations disagree is **DISCARDED** —
   it is not a fact.
3. **Label each by its measured evaluation**, never by intent: `LOST` (≤ -300), `HOLDABLE` (≥ -100), or
   `GREY` (excluded from scoring, kept in the record).
4. **Discard positions that are already decided** (mate already on the board) — they measure nothing about
   a stop decision, since there is no decision left.
5. **The set is committed WITH its evaluations** before any entrant runs.

**AND THE SET CARRIES ITS OWN COUNT.** Every later percentage names the set it was computed over:
`resigned-on-lost / LOST-positions-encountered`, and **never** `correct / total moves`.

---

## THE RECORDED STATE

Per GAME1_CHESS_tech-and-promo.md:80-95 — the record must be a **sufficient statistic** for the score:

```
fen  raw  move_uci  move_san  eval_before  eval_after  termination  result
secs  gen_tokens  budget_hit
```

**`termination` is written BY THE PATH THAT PRODUCED IT, never inferred later.** **`raw` is
non-negotiable.** And **the move list plus the evaluations reproduce both fields** — a record keeping the
termination but not the evaluation cannot say whether a resignation was correct; one keeping the
evaluation but not the termination cannot say whether the game ended.

---

## THE OUTCOME SCOPE — DECLARED BEFORE THE NUMBERS LAND

The termination taxonomy **is** the outcome scope. Frozen:

| `termination` | meaning | verdict |
|---|---|---|
| `resigned` | the model declared the position lost and stopped | **ADMIT** if the engine agrees (≤ -300); **REJECT** if it was holdable (≥ -100) |
| `decisive` | the engine adjudicated a finished line | **ADMIT** |
| `capitulated-in-band` | stopped inside the grey band | **NOT SCORED** — neither admitted nor rejected |
| **`no-conclusion`** | **budget exhausted with the game unresolved** | **REJECT — the failure this gate exists for** |
| `serving-failure` | the server never answered | **MISSING VALUE.** Re-run is a **RE-MEASUREMENT**; the entrant is **never** scored zero, and **never dropped** |

**`no-conclusion` is the reason this event is a gate and not a score.** A model that can always find another
move **and will never stop** is invisible to a taxonomy that records only how a *scored item* went.

**AND THE FIELD RULE, CARRIED FROM CARD_v5.md:** an empty bundle is a **MISSING VALUE**, not a zero; a
re-attempt is a **RE-MEASUREMENT**, not a second chance; an entrant counts as **MEASURED** if any attempt
measured; **every failure stays reported; no entrant is dropped from the denominator** for failing.

---

## THE POPULATION, NAMED — AND THE ADMISSION RULE

**Stage 0 (the weigh-in) is admission, not a game.** Running a card before it means every game handles load
failures separately, **which is how a field gets four different denominators.**

```
applicants    every .gguf in the model library
admitted      applicants minus the EXCLUDE_PAT classes
planned       admitted minus entrants with a RECORDED PERMANENT MEASUREMENT FAILURE (>=2 empty attempts)
attempted     entrants the runner actually started
measured      entrants whose bundle carries a NON-EMPTY results list
```

**THE EXCLUSION IS BY RECORD, ACROSS EVERY NAME THE RECORD TAKES** — not by canonical path, because a
failed bundle is **moved aside by name** and the canonical path is therefore empty for exactly the entrants
that must not be re-run. *(Measured on the v5 field: by path 7 excluded + 1 "no bundle"; by record 8 + 0,
planned 38. **A path test is not a record test.**)*

---

## THE GATE — AS A FRACTION OF THE FIELD THAT RAN

**An absolute-count gate's satisfiability depends on the thinning, so it diverges from a fraction exactly
where the population breaks — which is where a completeness gate is needed.** *(Measured: v4's "40 of 46"
silently became 100% of a field whose ceiling was 38.)*

```
COVERAGE   attempted / planned    >= 0.95     the run got through the field
YIELD      measured  / attempted  >= 0.85     the population could run
```

**Both required. Both satisfied BEFORE any item criterion is evaluated.**

---

## OUTCOME SCOPE FOR THE GATE

1. **GATE UNMET** → `NO VERDICT — THE FIELD DID NOT COMPLETE.` Name which ratio failed. **Call nothing a pass or a fail.**
2. **GATE MET, criteria evaluated** → a verdict, **each number quoted with the set it was computed over.**
3. **GATE MET, criterion fails, population remains a candidate cause** → `FAILED ON THIS POPULATION`, as a **scope**. **Declared here, so it cannot be a hedge added after a result.** Outcome 3 may attach to a **FAIL** and **never** excuses one.

---

## WHAT WOULD MAKE THIS CARD UNSATISFIABLE — SAID NOW, NOT LATER

**The oracle is secured and the freeze is measured**, so the v4-style failure (a population that cannot
load) is the live risk, and it is answered by the population rule above. **The other risk is NEW and
specific:** the position set must contain **enough LOST positions and enough HOLDABLE positions** for both
failure directions to be measurable. **If one side of the band is not populated, the card measures one
direction and must say so** — `ONE-DIRECTIONAL ON THIS SET` — rather than reporting a calibration score from
half a quantity. **The set's composition is recorded with the set, and checked before any entrant runs.**

---

## FROZEN

**This card's oracle, depth, threshold, band, taxonomy, population rule and gate are fixed at this commit.**
Any change after the first chess measurement lands **is a new card, not a revision to this one** — *a
criterion change after the numbers is a file, not a criterion.*
