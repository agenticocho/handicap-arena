# THE GAMES REFERENCE
## Every event in the Arena — formats, scorers, and what each one actually discriminates

**Version 1.0 · October 2026 · Public document**
**Companion to:** `WHITEPAPER.md` (institution), `FORMAT.md` (rules), `BELTS.md` (grading), `EVENTS.md` (event book)

> This is the catalogue: every event in the Arena, organised into leagues, each with a
> **deterministic or ground-truthed scorer**, a **declared null baseline**, and an honest
> statement of **what it discriminates** and **how it can be gamed.**
>
> **Counts are not maintained in this header.** They are counted from the headings below and
> asserted by `test_doc_counts.py`. A summary line kept in sync by hand goes stale, and this one
> did: it read *"forty-plus events across nine leagues"* while the body held **61 across 11** —
> and the number had been hand-written three times. **Never hand-write this count.** Derive it:
> `for L in A B C D E F G H I J K; do printf "%s:%s " $L $(grep -c "^### $L[0-9]" GAMES.md); done`
> League J (Strategy Evaluation & Research) had arrived and only the closing line was updated. The
> stale figure then propagated out of this document and into a generated audio summary of it.
> A number a reader skims is a number that must be computed, not remembered.

---

# PART 0 — HOW TO READ AN EVENT

Every entry has the same six fields. An event without all six is not shippable.

| field | meaning |
|---|---|
| **Measures** | the capability or property under test |
| **Format** | what actually happens, and how long it takes |
| **Scorer** | the objective mechanism — parser, executed test, or ground truth |
| **Null baseline** | the dumbest thing that could work. **If the event doesn't beat this, it measured nothing** |
| **Discriminates** | what a spread in scores would tell you |
| **Anti-gaming** | the specific way this event gets gamed, and the counter |

## The three scoring primitives

Everything below reduces to one of these. **No LLM judge appears anywhere in this document.**

1. **PARSE** — compare structured output against a specification. Binary, exact, cheap.
2. **EXECUTE** — run the model's artefact (code, query, config) against a real test suite in an
   isolated subprocess. **The artefact crosses the line only if the tests pass.**
3. **GROUND TRUTH** — compare against an outcome that happened independently of the model.

## The four inviolable rules

1. **Deterministic or ground-truthed scoring.** No exceptions.
2. **A null baseline in every event.** Every flattering number in this project's history came from a
   missing or wrong baseline.
3. **Cost is part of the score.** Tokens, latency, VRAM. Every event publishes **two tracks: absolute,
   and per gigabyte of VRAM.**
4. **Pre-register before running.** Task set, scorer, baselines and decision rule frozen first.

---

# LEAGUE A — MARKET & DECISION GAMES

*The niche. All of these are forecast-free or trade-free: they test judgement, not prediction.*

### A1 · Forecast Duel
- **Measures** — probability calibration against a live market
- **Format** — a market with public data; the model emits a probability; the market's closing price is the benchmark
- **Scorer** — GROUND TRUTH: Brier skill score vs the market price
- **Null baseline** — **the market price itself.** Predicting it exactly scores zero skill, by construction
- **Discriminates** — whether the model adds information the crowd lacked
- **Anti-gaming** — the market is the baseline, so there is nothing to game. **Early result: no local model beat the market across 230 resolved markets, and one 9B beat one 35B**

### A2 · Market Selection
- **Measures** — ranking opportunities under a budget and a holding period
- **Format** — N candidate opportunities with cost, duration and capacity; the model ranks or allocates
- **Scorer** — GROUND TRUTH: realised return over the period
- **Null baseline** — **random selection**, and *greediest* (largest headline number)
- **Discriminates** — planning under a constraint vs chasing the biggest number
- **Anti-gaming** — requires a **forward** outcome, so it cannot be tuned to a backtest

### A3 · Quote Placement
- **Measures** — execution judgement: where to rest an order given a book and recent flow
- **Format** — a snapshot of book + tape; the model chooses bid, ask and size
- **Scorer** — EXECUTE: simulated fills against the subsequent tape, marked out at a fixed horizon
- **Null baseline** — quoting at the mid, and quoting at the band edge
- **Discriminates** — whether the model understands that reward and adverse selection sit in the *same* place
- **Anti-gaming** — markout horizon and fill model are fixed in advance; changing either changes the answer

### A4 · Toxicity Detection
- **Measures** — can the model identify **adversely selected** fills?
- **Format** — a sequence of trades with outcomes withheld; the model labels each as toxic or benign
- **Scorer** — GROUND TRUTH: AUC against realised markout
- **Null baseline** — label everything benign (AUC 0.5)
- **Discriminates** — the single skill a market maker actually needs, and it is narrow enough to be automatable
- **Anti-gaming** — outcome-labelled, held-out samples; rotation required

### A5 · Arbitrage Detection
- **Measures** — finding and sizing a mispricing across related instruments
- **Format** — two correlated books; the model reports whether an edge exists and at what size
- **Scorer** — GROUND TRUTH: realised edge **net of all costs**
- **Null baseline** — "no arbitrage exists" (which is usually correct)
- **Discriminates** — cost awareness. **Most "arbitrage" dies on fees, and a model that ignores costs scores below the null**
- **Anti-gaming** — the cost model is fixed and published; nothing scores on gross edge

### A6 · Capital Allocation Under Duration
- **Measures** — distributing a fixed budget across opportunities with different lock-ups
- **Format** — budget, N opportunities with cost/duration/expected value; the model allocates
- **Scorer** — GROUND TRUTH: return on capital over the period
- **Null baseline** — equal-weight across all, and all-in on the best headline
- **Discriminates** — whether the model reasons about **time** as a cost
- **Anti-gaming** — duration is measured, not self-reported

### A7 · Inventory & Risk
- **Measures** — hedge, widen or pull, given inventory and incoming flow
- **Format** — a state; the model picks an action per step; the state evolves
- **Scorer** — GROUND TRUTH: drawdown-adjusted PnL over the episode
- **Null baseline** — never hedge
- **Discriminates** — whether risk management exists at all, which is usually a binary discovery
- **Anti-gaming** — the episode's flow is fixed and seeded; re-running must reproduce

### A8 · Settlement Reasoning
- **Measures** — applying resolution rules to adversarial edge cases
- **Format** — a market's rules plus a messy outcome; the model states the settlement
- **Scorer** — PARSE: exact match to the correct settlement
- **Null baseline** — always answer "as expected"
- **Discriminates** — careful reading of rules. **A defect of exactly this kind was found in production** — a resolver fabricating settlements on rows it could not parse
- **Anti-gaming** — cases written by an adversarial generator (see I3), not chosen by the entrant

---

# LEAGUE B — REASONING, CODE & STRUCTURE

### B1 · Fencing — Structured Output
- **Measures** — schema compliance under instruction pressure
- **Format** — a JSON Schema plus content requirements, and a **distractor instruction** ("after the JSON, add a friendly sentence")
- **Scorer** — PARSE: valid JSON, required keys, types, enums, cardinality
- **Null baseline** — `{}`
- **Discriminates** — whether output discipline survives pressure. **This is the round that caught a grammar file silently making a model incapable** (see FINDINGS/001)
- **Anti-gaming** — schema generated per run, so it cannot be memorised

### B2 · Golf — Tool Selection
- **Measures** — choosing the right tool and arguments from a spec, **and knowing when no tool fits**
- **Format** — a tool list and a natural request
- **Scorer** — PARSE: exact match on parsed tool name and required arguments
- **Null baseline** — pick the first tool
- **Discriminates** — the difference between a model that *can* call tools and one that *will*, and
  between a hero play and the punch-out when no club fits
- **Anti-gaming** — the correct tool is varied; distractor tools share surface words with the request

> **RENAMED 2026-10-08, from "Chess" to "Golf".** The entry's MEASURE never changed — tool selection,
> restraint, the punch-out when no club fits. What had drifted was the game named beside it. The deep
> dive's derivation put the five clubs on the five-tool schema and the 7-iron through the oak on the
> hallucinated call, and it was right; chess had been attached to this measure without carrying its
> state. **A game name and a measure had drifted apart inside one entry** — the same defect as
> `metaphor: CHESS` on a weather API, caught before it shipped. Chess is now its own event, below.

### B2c · Chess — Calibration
- **Measures** — **does the model know when it has lost?** Two-sided, with a ground truth
- **Format** — a position and a budget. The model plays until it concludes, resigns, or runs out.
- **Scorer** — a reference engine at a **FROZEN depth** in a subprocess. The engine's evaluation is the
  ground truth, not an opinion
- **Null baseline** — always play on, never resign (loses the "premature collapse" half entirely); and
  always resign at the first sign of trouble (loses the other half)
- **Discriminates** — **resigning a WON or DRAWN position** is premature collapse; **playing on in a
  LOST one** is miscalibrated persistence. Both are conformance failures with stateable reasons
- **Anti-gaming** — the engine's evaluation is never shown to the model, and the threshold for "lost" is
  a frozen centipawn number, not a phrase
- **SETTLED — CHESS KEEPS CALIBRATION.** Mike: *"Chess keeps it. And chess first sounds good. No rush for
  punch-out."* Chess is **event 1 of `THE ORDER`**, because a model that cannot stop will run up the move
  counter in every event after it. **PUNCH-OUT takes PERSISTENCE/RECOVERY (the count)**, and **SOKOBAN takes
  IRREVERSIBLE PLANNING** — the same faculty tested where nothing tells you the answer. Three claimants, one
  each, and **calibration is not re-homed.** The tie-break is not "which cabinet is about being beaten" but
  **which cabinet's oracle can decide it**: chess's engine is third-party and **continuous** (a gradient of
  confidence against the truth), Sokoban's solver is **binary** (a boundary, asked once).
- **Gate, not a round** — *a logical conclusion must be reached or the model can't enter.* A player who
  cannot recognise a lost position cannot be said to have played a game, because the game has no end.
  **Its output is a binary other events consume.**

> **The strongest sentence ever written about this project is this event's specification:** *the hardest
> move on the board isn't a sacrifice, it's tipping your king.*
>
> **And its own contract is what makes it checkable: if the outcome cannot be recorded, the gate does not
> exist.** `EVENT_chess.md` carries the state (`fen`, `raw`, `move`, `eval_before`, `eval_after`,
> `termination`, `result`) and the two-field outcome split — `result` is the quality of the MOVE,
> `termination` is HOW THE GAME ENDED. They are separate fields because **a game ending is not a failure**,
> and a taxonomy that could not record a resignation could not hold the sport.

### B3 · Pit Stop — Code Repair
- **Measures** — fixing a defect against a test suite
- **Format** — a buggy function plus failing cases; return the corrected function
- **Scorer** — EXECUTE: generated code run against a real suite in an isolated subprocess
- **Null baseline** — return the input unchanged (which fails the new cases)
- **Discriminates** — whether the model reads the failing case, or pattern-matches "fix"
- **Anti-gaming** — the tests are the specification. **A model that only ever passes is not a model; a scorer that only ever passes is not a scorer**

### B4 · Greenfield — Implement to Spec
- **Measures** — writing a working artefact from a description
- **Format** — a spec plus a held-out test suite the model cannot see
- **Scorer** — EXECUTE: hidden tests
- **Null baseline** — an interface-only stub (passes type checks, fails tests)
- **Discriminates** — genuine implementation vs plausible-looking signatures
- **Anti-gaming** — **hidden tests are the whole design.** Published tests get trained on

### B5 · Debugging Under Fog
- **Measures** — root-causing from symptoms only
- **Format** — a failing system, logs, no source-level pointer; the model proposes the cause
- **Scorer** — PARSE: does the diagnosis match the seeded defect
- **Null baseline** — a random defect from the catalogue
- **Discriminates** — hypothesis formation vs symptom restatement
- **Anti-gaming** — the same symptom is seeded by different defects across instances

### B6 · Refactor Without Regression
- **Measures** — improving structure while preserving behaviour
- **Format** — code plus a passing suite; the model restructures
- **Scorer** — EXECUTE: original suite must still pass, plus a complexity or duplication metric must improve
- **Null baseline** — no change (passes tests, fails the metric)
- **Discriminates** — the difference between editing and refactoring
- **Anti-gaming** — dual requirement (tests **and** metric) prevents gaming either

### B7 · Exact Arithmetic Without a Calculator
- **Measures** — numeric reliability
- **Format** — arithmetic, unit conversion, date math, percentage chains
- **Scorer** — PARSE: exact answer
- **Null baseline** — a one-line Python script. **Most models lose to this**
- **Discriminates** — whether the model knows when to be uncertain and when to be exact
- **Anti-gaming** — non-round numbers; the null baseline makes the bar explicit

### B8 · Instruction Conflict Resolution
- **Measures** — handling contradictory constraints
- **Format** — a system prompt and a user request that conflict in a defined way
- **Scorer** — PARSE: does it follow the declared precedence, and *flag* the conflict
- **Null baseline** — follow the last instruction blindly
- **Discriminates** — whether the model notices the conflict at all
- **Anti-gaming** — precedence rule is declared in the task, so it is a reading test, not a guessing test

---

# LEAGUE C — AGENCY & TOOLS

### C1 · Sandbox Goal
- **Measures** — achieving a goal with tools, over multiple steps
- **Format** — a sandboxed file system and shell; a goal; a step budget
- **Scorer** — EXECUTE: goal state verified by assertion, plus steps used and **destructive-action penalties**
- **Null baseline** — do nothing
- **Discriminates** — planning and error recovery
- **Anti-gaming** — **penalties for destructive actions**, so a model cannot win by resetting or wrecking

### C2 · Tool Harness
- **Measures** — long-horizon tool use where the environment changes
- **Format** — a tool whose behaviour changes mid-episode (an error format shifts)
- **Scorer** — EXECUTE: task completion
- **Null baseline** — retry the same failing call forever
- **Discriminates** — adaptation. **Failure modes here are diagnostic, not random**

### C3 · Retrieval & Attribution
- **Measures** — fetching, extracting, and citing
- **Format** — a question requiring a source; the model retrieves and answers with citations
- **Scorer** — PARSE: answer correctness **plus citation validity plus zero fabricated references**
- **Null baseline** — refuse to answer
- **Discriminates** — fabrication rate, which is the failure that matters most in deployment
- **Anti-gaming** — citations resolved against the actual page; **an unresolvable citation scores worse than no answer**

### C4 · Long-Horizon Consistency
- **Measures** — holding a plan over many steps
- **Format** — a 40-step task where a constraint set at step 1 matters at step 35
- **Scorer** — EXECUTE: end state plus constraint satisfaction
- **Null baseline** — solve only the final sub-goal
- **Discriminates** — context retention under accumulation

---

# LEAGUE D — PERCEPTION & MULTIMODAL

### D1 · Spec-to-Plot
- **Measures** — rendering exactly what was specified
- **Format** — a deterministic specification ("a line through these five points, these axis labels")
- **Scorer** — GROUND TRUTH: structural similarity to a reference render
- **Null baseline** — a blank canvas of correct dimensions
- **Discriminates** — whether generation respects constraints or merely produces something plausible
- **Anti-gaming** — **the spec is numeric, not stylistic.** No judge is asked whether it "looks good"

### D2 · Diagram Comprehension
- **Measures** — reading structured visual information
- **Format** — a generated diagram with known ground truth; the model answers questions about it
- **Scorer** — PARSE: exact answers
- **Null baseline** — guess the majority label
- **Discriminates** — genuine reading vs caption-level pattern matching
- **Anti-gaming** — figures generated fresh with randomised values

### D3 · Cross-Modal Consistency
- **Measures** — agreement between what the model says and what it shows
- **Format** — describe an image, then answer questions about your own description
- **Scorer** — PARSE: internal consistency rate
- **Null baseline** — a fixed generic description
- **Discriminates** — whether perception feeds generation or they run in parallel

### D4 · Diffusion-in-the-Loop (team)
- **Measures** — a reasoner specifying a diagram that a renderer draws and a vision model verifies
- **Format** — spec → render → verify against spec
- **Scorer** — EXECUTE: verification pass rate
- **Null baseline** — render without a spec
- **Discriminates** — whether verification actually closes the loop
- **Anti-gaming** — **the verifier checks against the numeric spec**, not against the render's plausibility

---

# LEAGUE E — CREATIVE WITH OBJECTIVE CONSTRAINTS

*Creative events are only admissible if the constraint is checkable. Otherwise they belong to nobody.*

### E1 · Song Composition — Constraint Grades
- **Measures** — composing inside formal rules
- **Format** — emit MIDI to a brief (key, tempo, length, form)
- **Scorer** — PARSE: objective constraints — key adherence, tempo, **no parallel fifths**, voice ranges, cadence placement
- **Null baseline** — a random walk in the correct key
- **Discriminates** — whether the model knows the rules or merely the vocabulary
- **Anti-gaming** — a style-embedding distance is reported **separately** from the constraint score, so a model cannot trade correctness for sounding nice

### E2 · Structured Creative — Form Compliance
- **Measures** — following a demanding form (sonnet, villanelle, sestina) exactly
- **Format** — write to form
- **Scorer** — PARSE: metre, rhyme scheme, stanza structure, line count
- **Null baseline** — free verse of the right length
- **Discriminates** — constraint-holding, and it is a well-known hard case

### E3 · Compression / Summarisation
- **Measures** — retaining what matters
- **Format** — compress a document; then answer held-out questions using only the compression
- **Scorer** — PARSE: question accuracy at a fixed compression ratio
- **Null baseline** — the first N% of the document, and a random N% sample
- **Discriminates** — whether compression preserves *information* or just plausibility
- **Anti-gaming** — ratio fixed, questions held out

---

# LEAGUE F — SELF-KNOWLEDGE & CALIBRATION

### F1 · Answer-or-Abstain
- **Measures** — knowing what you don't know
- **Format** — a mixed set of answerable and unanswerable questions; the model may abstain
- **Scorer** — PARSE: two rates — accuracy on answered, and abstention on unanswerable
- **Null baseline** — answer everything (high accuracy, terrible abstention) and answer nothing (degenerate)
- **Discriminates** — calibration vs confidence. **Two error rates, never collapsed into one score**
- **Anti-gaming** — the unanswerable set is generated to be *plausible*, not absurd

### F2 · Confidence Brier
- **Measures** — the calibration curve itself
- **Format** — answer with a stated confidence
- **Scorer** — GROUND TRUTH: Brier score and a reliability diagram
- **Null baseline** — always state 50%
- **Discriminates** — overconfidence, which is the single most common failure in local models
- **Anti-gaming** — the curve is published, not just its summary; a single number hides everything

### F3 · Adversarial Self-Audit
- **Measures** — can the model find its own errors?
- **Format** — the model answers, then is shown its answer and asked to find faults
- **Scorer** — PARSE: did it flag the errors that exist, and only those (precision **and** recall)
- **Null baseline** — claim everything is correct
- **Discriminates** — whether self-critique is real or performative
- **Anti-gaming** — requires **both** precision and recall, so "flag everything" fails

---

# LEAGUE G — EFFICIENCY & OPERATIONS

### G1 · Drag Race — Throughput
- **Measures** — raw generation speed
- **Scorer** — GROUND TRUTH: tokens/second at fixed concurrency
- **Null baseline** — none needed; this is a measurement
- **Discriminates** — hardware and quantisation effects, and nothing about quality

### G2 · Time to Correct Answer
- **Measures** — speed *and* correctness together
- **Format** — keep generating until the answer is correct, or give up
- **Scorer** — GROUND TRUTH: wall-clock to first correct answer
- **Null baseline** — a model that is correct but enumerates
- **Discriminates** — the metric that actually maps to user experience

### G3 · Biathlon
- **Measures** — accuracy × throughput with misses costing time
- **Scorer** — GROUND TRUTH: `total = (latency × trials) + (misses × k × latency)`
- **Null baseline** — the fastest model regardless of accuracy
- **Discriminates** — **`k` is the engineering decision.** Raise it to weight correctness, lower it for speed; the winner can flip
- **Anti-gaming** — `k` is declared before the run

### G4 · Context Economy
- **Measures** — the smallest context window in which the task still succeeds
- **Scorer** — EXECUTE: binary search over `--ctx`, report the threshold
- **Null baseline** — use maximum context
- **Discriminates** — genuinely useful for anyone with a 8 GB card
- **Anti-gaming** — this event exists **because** a too-small context silently caps reasoning (FINDINGS/001, mechanism 3)

### G5 · Quantisation Ladder
- **Measures** — quality retained per byte
- **Format** — the same model at Q4/Q5/Q6/Q8
- **Scorer** — EXECUTE: score vs measured footprint, as a curve
- **Null baseline** — the largest quant
- **Discriminates** — the actual trade users face. **The curve is the finding, not any single point**

### G6 · Deployability
- **Measures** — does it start, stay up, and fail gracefully?
- **Scorer** — EXECUTE: cold-start time, time to first token, behaviour on a malformed request, memory after 1000 requests
- **Null baseline** — a model that works only in the harness
- **Discriminates** — operational fitness, which no leaderboard measures and every deployment needs

---

# LEAGUE H — TEAM & RELAY GAMES

*Team division = the **sum** of member footprints, so chaining cannot smuggle size.*

### H1 · Relay — Router to Worker
- **Measures** — whether chaining beats a single model
- **Format** — leg 1 plans; the last leg answers, receiving the plan verbatim
- **Scorer** — PARSE/EXECUTE on the **final** output only
- **Null baseline** — **the worker alone.** A relay without its control means nothing
- **Discriminates** — whether a plan *helps*, harms, or is ignored. **A misleading plan is the most interesting outcome available**
- **Anti-gaming** — a dropped baton is a DNF. Passing garbage downstream is a failure, not a recovery

### H2 · Deterministic Arbiter
- **Measures** — a model proposes, a program verifies
- **Format** — the model emits an artefact; a deterministic checker (test runner, schema validator, arithmetic recompute) accepts or rejects
- **Scorer** — EXECUTE: acceptance rate
- **Null baseline** — the checker alone, rejecting everything
- **Discriminates** — **the most valuable event in this document.** It is objectively gradeable and it is how reliable agents are actually built
- **Anti-gaming** — the checker is the authority; the proposer cannot adjudicate its own work

### H3 · Red / Blue
- **Measures** — generating hard cases and solving them
- **Format** — one team authors adversarial cases; the other solves; roles swap
- **Scorer** — GROUND TRUTH: the solver's failure rate on the author's cases
- **Null baseline** — cases sampled at random from a fixed pool
- **Discriminates** — a self-improving curriculum, with difficulty as the measured signal

### H4 · Budget Auction
- **Measures** — outcome per unit of compute
- **Format** — models bid turns or tokens for a task
- **Scorer** — GROUND TRUTH: score ÷ cost
- **Null baseline** — spend the whole budget
- **Discriminates** — efficiency under competition, and it is the only event where being cheap is a skill

### H5 · Adversarial Pair
- **Measures** — proposing vs verifying, as separate roles
- **Format** — one model writes a plausible-but-wrong answer; another must catch it
- **Scorer** — PARSE: catch rate **and** false-alarm rate
- **Discriminates** — whether verification is independent or merely agreeable

### H6 · One Versus Many
- **Measures** — a single model against a team, same task
- **Scorer** — GROUND TRUTH: win rate **and** total cost
- **Null baseline** — the single model
- **Discriminates** — whether orchestration earns its overhead. **Often it does not, and that is worth publishing**

### H7 · Marathon Relay
- **Measures** — handoffs under load, over a long horizon
- **Scorer** — EXECUTE: end state, plus a per-leg attribution of where it broke
- **Discriminates** — compounding error. The leg attribution is the useful output

---

# LEAGUE I — DIAGNOSTIC & ADVERSARIAL

*These events exist to find failure, not to rank. A **clean negative is a success.***

### I1 · Serving-Configuration Sweep
- **Measures** — how much of a score is plumbing
- **Format** — the same weights under varied flags: grammar on/off, context sizes, token budgets
- **Scorer** — PARSE/EXECUTE: score delta attributable to configuration
- **Null baseline** — the unmodified serving config
- **Discriminates** — **this is the event that found three separate mechanism defects.** A model that scores differently across configs is telling you about your harness, not itself

### I2 · Truncation Discrimination
- **Measures** — whether a failure is the model's or the harness's
- **Scorer** — PARSE: `finish_reason`, token accounting, and **which limit actually bit**
- **Null baseline** — attributing every zero to capability
- **Discriminates** — measurement failure vs capability failure. **"The model answered wrongly" and "we cut it off" are different claims**

### I3 · Adversarial Task Generation
- **Measures** — how brittle a suite is
- **Format** — a generator produces near-miss variants of every task
- **Scorer** — PARSE: score degradation under perturbation
- **Null baseline** — the original suite
- **Discriminates** — whether the suite tests the capability or the surface form
- **Anti-gaming** — **this is the anti-saturation mechanism.** A static suite is tuned to within a month

### I4 · Baseline Audit
- **Measures** — whether the *event* is meaningful
- **Scorer** — parse: is the null baseline present, correct, and actually losing?
- **Null baseline** — none; this audits the auditors
- **Discriminates** — **every flattering number in this project's history came from this event failing**

### I5 · Reproducibility
- **Measures** — does a result survive re-running?
- **Format** — the same bundle, re-executed on a second rig
- **Scorer** — GROUND TRUTH: exact agreement, and a report of where it diverges
- **Null baseline** — trusting a single run
- **Discriminates** — **latency and footprints jitter.** A result quoted to two decimals that moves on re-run is false precision

---

# LEAGUE J — STRATEGY EVALUATION & RESEARCH

*Derived from `FINDINGS/003`. This league exists because the evaluative infrastructure under retail
trading is nearly absent: a 53.8K-view article can headline a best-of-325 backtest whose decisive
statistic is withheld, and no venue tests the reasoning that produced it. Every event here is
deterministically scorable, and none of them requires predicting a market.*

### J1 · Backtest Fabrication Audit
- **Measures** — whether a model reports performance numbers it cannot actually compute
- **Format** — a strategy spec plus a fixed historical dataset; the model reports the standard metrics (total return, drawdown, win rate, profit factor, trade count)
- **Scorer** — EXECUTE: a deterministic engine re-runs the identical spec on the identical data; score is the deviation between claimed and computed metrics, with a fabrication penalty past a declared tolerance
- **Null baseline** — **the engine's own run**, and separately *"I cannot verify this without running it"* (which scores honest-unknown, not fabrication)
- **Discriminates** — the failure the source article names explicitly (*"confirm Claude didn't hallucinate during the backtest"*). A model that invents a plausible equity curve and a model that computes it are indistinguishable without this event
- **Anti-gaming** — datasets generated per run from a seeded synthetic price process, so there is no memorised answer; the tolerance is declared before the run

### J2 · Multiple-Testing Discipline
- **Measures** — whether the model knows that the best of many tries is not a finding
- **Format** — N strategy results are presented; the model must state which, if any, represent a real edge, and how confident it is
- **Scorer** — GROUND TRUTH: in the null arm **all N are zero-edge by construction**; in the mixed arm a known subset carries a planted edge with a declared effect size
- **Null baseline** — **pick the highest performer** (the article's own rule) — which by construction selects noise in the null arm
- **Discriminates** — the single most consequential quantitative error in the entire genre. With 325 tries, the *median* best-of-325 profit factor from pure noise is **4.00 at n=20, 2.33 at n=50, 2.00 at n=75**. A model that calls the winner "proven" scores below the null baseline
- **Anti-gaming** — the planted edge size and the number of noise strategies vary per instance; the correct answer is sometimes "none", so a model that always finds an edge fails

### J3 · Out-of-Sample Honesty
- **Measures** — overfitting awareness, and whether the model will report degradation it can foresee
- **Format** — a strategy and a training period; the model tunes parameters **and must state its expected out-of-sample degradation** before seeing the test period
- **Scorer** — GROUND TRUTH: realised in-sample vs out-of-sample decay, compared against the model's own prediction
- **Null baseline** — report in-sample performance as the expectation (i.e. assume no decay)
- **Discriminates** — the article warns *"if you tweak a strategy until it fits the past perfectly, it will almost certainly fail in the future"* and then reports in-sample numbers. Stating the decay in advance is the difference between knowing that and acting on it
- **Anti-gaming** — predictions are recorded before the test period is revealed; the split point is generated per run

### J4 · Spec Completeness
- **Measures** — whether the model can turn a loose description into a fully specified, testable strategy
- **Format** — an indicator description or a strategy write-up with gaps; produce a spec covering asset, timeframe, entry, exit, stop, position sizing
- **Scorer** — PARSE: presence and validity of every required field, **plus whether invented components are explicitly flagged as invented**
- **Null baseline** — return the source text verbatim
- **Discriminates** — a spec with silent gaps cannot be backtested and cannot be falsified. The source article's own step 3 requires flagging what the converter added; that requirement is the test
- **Anti-gaming** — the number and kind of missing components vary; an unflagged invention scores worse than an admitted gap

### J5 · Cost Reality
- **Measures** — cost awareness in strategy evaluation
- **Format** — the same strategy evaluated gross and net of a declared fee, spread and slippage model
- **Scorer** — EXECUTE: net outcome against the declared cost model
- **Null baseline** — **do not trade** — under most cost assumptions a large share of high-turnover strategies lose to it
- **Discriminates** — whether the model treats costs as part of the strategy or as an afterthought. The source article includes fees; most content in the genre does not
- **Anti-gaming** — the cost model is fixed and published per instance and is sometimes deliberately punishing, so "it's still profitable" cannot be a blanket answer

### J6 · Regime Attribution
- **Measures** — whether a stated causal explanation makes a checkable prediction
- **Format** — the model is given a strategy's behaviour and must state (a) the inefficiency it exploits, (b) the regime it should work in, (c) the regime it should fail in
- **Scorer** — GROUND TRUTH: realised conditional performance across the named regimes, tested against the model's own directional claims
- **Null baseline** — *"it works in trends"* (the modal answer, and the one that cannot be wrong)
- **Discriminates** — real mechanism knowledge versus narrative. Only the **falsifiable** part is scored — the model must commit to a regime where it loses
- **Anti-gaming** — regimes are generated from a synthetic process with a known structure, so "everything works in trends" is testably false in half the instances

### J7 · Ranking vs Realised
- **Measures** — whether the model can distinguish an overfit equity curve from a real edge
- **Format** — rank N strategies by expected out-of-sample performance
- **Scorer** — GROUND TRUTH: rank correlation against realised out-of-sample results
- **Null baseline** — **rank by in-sample return**, which is a strong baseline and frequently wins
- **Discriminates** — arguably the most useful single skill in applied quant, and it is measured by one number the moment you have a holdout
- **Anti-gaming** — the instance mixes strategies whose in-sample and out-of-sample orderings are deliberately anti-correlated in a known subset

---

# LEAGUE K — ASSISTED PLAY (the seeing-eye dog)

*Proposed 2026-10-07. This league tests the boundary between PERCEPTION and REASONING by giving a
text-only entrant a declared, frozen assistive layer — a sensor that describes and does not
conclude. The point is not to let weak models cheat at vision. It is to stop scoring "has no eyes"
as "cannot reason", and to measure what the eyes are worth.*

> **TERMINOLOGY (standardised 2026-10-07).** In this repository **"cabinet" means an ARCADE
> CABINET** — a self-contained game with frozen criteria, owned by one cabinet agent, in its own
> git worktree (`cabinet/sokoban`, `cabinet/missile-command`, `cabinet/zork`). It is NOT used here
> for anything else.
>
> The assistive layer in this league is a **SENSOR**: a declared, frozen perceptual channel
> attached to an entrant. It describes and does not conclude, and it **must fail the task alone** —
> otherwise the event measures the sensor rather than the entrant. *"Assisted play"* is the mode;
> the sensor is the component. The seeing-eye-dog metaphor is the informal gloss.
>
> A sensor is **not** part of a cabinet's machinery, and a cabinet is **not** a sensor. Two
> different things, two different words, deliberately.
>
> **AND A THIRD CARRIER, NAMED SO IT CANNOT BE CONFUSED.** The token `sensor` also occurs ~46 times in
> this repo as **fixture data** — never as a concept, never as a name for anything: `sensor_count` in
> `tasks/01_structured_output.json` and in `arena.py`'s worked example; `{"sensor": "A" | "B"}` in
> `tasks/v2/01_conformance.json` and the assertions that read it; `"sensor"` in a required-key list at
> `tasks/v4/01_conformance.json:93`; and sensor 1/2/3 (PTU300), "sensor order", "the sensor model was
> supplied" in the trap text of `tasks/v6/01_conformance.json` — a weather-station instrument inside a
> JSON-schema conformance task, plus the 37 `results/` files that answered it.
>
> **FIELD-NAME VERSUS CONCEPT, stated explicitly.** Where `sensor` appears in a task payload, a test
> assertion or a model output it is a **field** and means a measuring instrument. Where it appears in
> this league it is a **concept** and means the assistive perceptual channel. **A repo-wide grep will
> land both in one result set — that is expected, and it is not a collision.** The reader's
> disambiguator is the document: a task file describes a JSON schema; this league describes a play
> mode.
>
> **A THIRD REGISTER, found by @missile-command after he checked the file list rather than the sum.**
> `rename_league_k_term.py` — the script that performed this very replacement — is the one in-repo
> document where **both terms co-occur in prose by design**, because explaining the collision is its
> entire job. It is neither register: not a task payload, not a play mode, but a **migration script**.
> The honest disambiguator is therefore the *purpose* of the document, not its type: **a task file
> declares a schema; this league declares a play mode; a migration script names both because it is
> the record of their crossing.** Anyone grepping `sensor` should expect this file to be among the
> loudest, **and which file is loudest depends on which term you grep** — measured at `49846ce`, and
> not at the revision that carries this sentence, because writing it added a line bearing each term
> and so raised all four of these figures by one. A count taken before the sentence that reports it
> is not the count that sentence publishes (counts are case-insensitive, whole-file). `GAMES.md` wins
> on `sensor` (33 occurrences, 28 lines, against 13 and 9 here), while **this script wins decisively
> on `cabinet`** (27 occurrences, 18 lines, against 12 and 8). So there is no single superlative to
> assign: **the file named for a term is the loudest carrier
> of that term**, and the earlier phrasing here — "27 cabinet-bearing lines and 32 `sensor`
> occurrences" — was wrong in both figures, having taken one from this script and one from the
> previous revision of `GAMES.md`. *(Caught by @missile-command, who measured it before accepting the
> correction, and whose finding is the sharper one: a superlative over two terms that rank in
> opposite orders cannot be stated as a superlative at all.)* The
> point survives the correction: it is the one file where both terms co-occur **by design**, and it is
> the most ambiguous by *count* and the least ambiguous by *reading*, which are not the same measure.
> *(Corrected from "the noisiest of the 47", which was a superlative I did not measure; the count is
> @missile-command's catch, made after he had verified the rest of the block and deliberately declined
> to reopen the thread over one adjective. He was right to flag it and right not to act on it — an
> adjective in a document that does the real work elsewhere is a low-value correction, and it is still
> a false one.)*
>
> *(The count is 47 tracked files, not 46 — @missile-command caught that my earlier enumeration
> omitted `rename_league_k_term.py` itself. The script was in my own output; I dropped it when
> summarising. A list is not a count, and a sum of classes is not a search.)*
> Raised by @missile-command, who verified the League K span independently (4 uses of
> "cabinet", all inside this block; 0 as the perceptual channel) and then found this residual.

## The one failure mode that would ruin this league

**If the sensor can solve the task by itself, the event measures the sensor.** A description
informative enough to be transcribed is a leak, and the entrant's score becomes the dog's score.
Every event below therefore carries an **isolation requirement**: the sensor must be scored
ALONE, and it must FAIL. A sensor that passes alone invalidates the round — the same way the
grammar file invalidated a whole table in FINDING 001 by making the model's failure uninformative.

Three further constraints, all from this project's own findings:

- **Frozen and declared.** The sensor is an LLM, so its model, version, prompt and quantisation
  are config. FINDING 001: a config that can change the outcome belongs in the record. A
  per-run-varying dog makes two runs incomparable.
- **Never merged.** The pair's score and the model's score are reported **separately**, always.
  Merging them is the same defect as a relay that reports only the team total.
- **Division is the SUM of members** (League H rule). A 350M entrant with a 2B dog competes as a
  ~2.4 GB team, not a Featherweight. Peak VRAM is the largest member, because legs run in
  sequence — but the division is what the team is worth.

---

### K1 · Assisted Perception
- **Measures** — whether a text-only model can reason over a description it did not produce
- **Format** — a task whose input is an image; a **frozen sensor** renders it to text under a declared prompt; the entrant answers from the description plus the task
- **Scorer** — PARSE against the task's own ground truth, exactly as the visual task would be scored
- **Null baseline** — **the entrant without the sensor** (expected to fail, and its failure is the baseline the delta is measured against), plus **chance**
- **Discriminates** — the reasoning half of a perceptual task. A model that scores 0 bare and 0.67 assisted has demonstrated reasoning and lacked eyes; a model that scores 0 both ways lacked both
- **Anti-gaming** — the sensor is scored alone and **must fail**; it is forbidden from emitting the answer, a decision, or a confidence; the task's ground truth is never shown to it

### K2 · Sensor Isolation *(the guard, run as its own event)*
- **Measures** — whether an assistive layer is a channel or a solver
- **Format** — run the sensor **alone** against the same tasks, with its description as its final answer
- **Scorer** — PARSE against the same ground truth
- **Null baseline** — none needed; the requirement is absolute
- **Discriminates** — **if the sensor passes a task alone, that task is void for K1.** This event exists so the check is explicit and published rather than assumed
- **Anti-gaming** — the sensor's own score is recorded beside every assisted result, so a reader can always see how much of the pair's score the dog could have earned unaided

### K3 · Mode Pair *(the delta)*
- **Measures** — the value of perception to a given model, as a number
- **Format** — the same entrant and the same tasks, run **twice**: bare text, and assisted
- **Scorer** — PARSE both arms; publish the pair, never the assisted score alone
- **Null baseline** — the bare arm
- **Discriminates** — isolates perception from reasoning within one set of weights. This is a controlled pair in the sense the evidence set already renders, so it needs no new machinery
- **Anti-gaming** — both arms use identical tasks, identical config and identical trials; a bare arm run at a different `--ctx` measures the config, not the model (FINDING 001)

### K4 · Native Control *(the three-arm comparison)*
- **Measures** — assisted text against genuine multimodal, on the same task
- **Format** — three arms: (a) text model, bare; (b) text model + sensor; (c) a native VL model, no sensor
- **Scorer** — PARSE on all three
- **Null baseline** — arm (a)
- **Discriminates** — **the question this league was proposed to answer:** does a described image plus a strong reasoner beat a small model that can simply see? Arm (c) is the honest control, and it is cheap because eight VL entrants are already in the field
- **Anti-gaming** — arm (c) gets no sensor; if it is helped, the comparison is meaningless. All three arms share the task set and the trial count

### K5 · Description Fidelity
- **Measures** — how much of the image survives the sensor channel
- **Format** — a task with a known, enumerable set of visual facts; the sensor produces a description; a deterministic parser counts which facts are present
- **Scorer** — PARSE: fact coverage, plus **hallucination rate** (facts asserted that are not in the image)
- **Null baseline** — a template description naming the image type and nothing else
- **Discriminates** — whether a low assisted score means the entrant failed to reason, or the dog failed to see. Without this, K1's result is unattributable
- **Anti-gaming** — facts are enumerated from the image's own construction, not from the description; hallucinated facts count against, so a maximal description scores worse than an accurate one

---

# PART 3 — THE NULL-BASELINE CATALOGUE

Reusable, and the reason most events are meaningful.

| baseline | where it applies |
|---|---|
| **the market price** | any forecasting event |
| **a one-line script** | arithmetic, parsing, formatting |
| **random uniform** | selection, ranking |
| **the greediest choice** | allocation with a headline number |
| **do nothing** | agency, risk, inventory |
| **refuse to answer** | retrieval, attribution |
| **no change** | refactor, repair |
| **answer everything / nothing** | abstention, calibration |
| **the worker alone** | any relay or ensemble |
| **the unmodified config** | any diagnostic sweep |

**Rule:** if you cannot name the null baseline in one sentence, the event is not ready.

---

# PART 4 — ANTI-GAMING, IN GENERAL

1. **Rotate task instances.** Generated per run wherever possible; the suite is the thing that rots.
2. **Hide part of the specification.** Greenfield implementations ship with hidden tests.
3. **Score two things at once** when one alone is gameable (tests **and** complexity; constraints **and** style).
4. **Publish the config with the score** — flags, token budget, context window, quant, hash.
5. **Never let a model adjudicate its own output.** H6 and H2 exist specifically to separate proposing from verifying.
6. **Report the curve, not the point,** wherever a trade-off exists — quantisation, context, `k`, cost.
7. **Say what the event cannot measure.** Every entry above has limits; hiding them is the only fatal move.

---

# PART 5 — BUILD ORDER

Events are not equal in value-per-line-of-code.

| priority | events | why |
|---|---|---|
| **1st** | **H2 Deterministic Arbiter**, **I1 Serving Sweep**, **I2 Truncation** | highest value, cheapest to build, and I1/I2 already exist |
| **1st (tied)** | **J1 Backtest Fabrication Audit**, **J2 Multiple-Testing Discipline** | no venue tests either one; both are pure PARSE/EXECUTE, need no forecasting, and the addressable audience is measured in tens of thousands of readers |
| **2nd** | **H1 Relay** | answers the community's real question; needs only the harness |
| **3rd** | **A2 Market Selection**, **A4 Toxicity Detection** | the niche, and both are ground-truthed |
| **4th** | **B1–B3, G3, G4** | already built; keep as the standing card |
| **5th** | **League F (calibration)**, **I3 Adversarial Generation** | these protect everything else from becoming stale |
| **later** | **League E (creative)** | admissible, but the constraints are the work |
| **last** | **H6 One Versus Many**, **D4 Diffusion-in-the-loop** | need the pipeline before they are worth running |

---

*61 events. Every one scored by parser, execution, or ground truth. Every one carrying a null
baseline. Nothing here is judged by a model — because a model grading its own family is not a
measurement, it is a conflict of interest.*
