# THE HANDICAP ARENA
## White Paper — a sanctioned competition circuit for local AI

**Version 1.0 · October 2026 · Public document**
**Status:** working harness built and tested; league format specified; games specified

> **Logline:** Every leaderboard on the internet ranks a 4-billion-parameter model running on a
> six-year-old graphics card against GPT-5 and tells you it came 417th. **It didn't come 417th. It
> was competing in a different sport.**

---

# PART I — THE PROBLEM

## 1.1 Local models are invisible by construction

The internet has excellent leaderboards. Almost all of them answer the wrong question.

They rank models **globally**, on **benchmarks**, by **parameter count as written in a filename**. So a
quantised 4B model that runs on an 8-gigabyte consumer GPU — the single most common configuration in
the world — is placed somewhere in the hundreds, in a table nobody scrolls to, and is compared against
frontier models that cost money per token and cannot run on the machine at all.

**The question a local practitioner actually asks, thousands of times a day, is:** *"What is the best
model I can run on MY hardware, for MY task?"* Not "what is the best model." **What is the best model
that fits.**

Nobody answers that reproducibly.

## 1.2 The deeper problem: most benchmarks measure the plumbing and don't know it

This is the finding the Arena was built to solve, and it was discovered the hard way — by building a
benchmark, running it, and getting **three clean, confident, entirely wrong leaderboards in a row.**

Each one failed for a different reason. None of them was model capability.

| # | the confound | what it silently faked |
|---|---|---|
| 1 | **stale server config** pointing at model files that had been deleted | two models "scored" 0.00 that never ran at all |
| 2 | reasoning models return their answer in a `reasoning_content` field with `content` **empty** | the harness read the wrong field; a strong model scored 0.00 |
| 3 | a **grammar file** applied by the serving layer, restricting output to a different application's schema | four models scored 0.00 that were **physically incapable** of producing the requested output |
| 4 | **alias names that lie** — one endpoint literally named `granite-8b` served a Qwen model | silent substitution, undetectable downstream |

**Not one of them threw an error.** A model that cannot emit your schema returns valid-looking JSON
for a *different* schema. A truncated reasoning model returns a confident paragraph of thinking. A dead
endpoint returns a 404 that looks like a score of zero. **Every failure mode is silent, and every one
produces a table.**

A leaderboard built on an unverified harness is **worse than no leaderboard, because it is confidently
wrong.**

## 1.3 The proof: one model, five measurements, zero weight changes

The same 2-billion-parameter model was measured five times during development:

**0.00 → 0.33 → 0.67 → 0.33 → 0.67**

**Nothing about the model changed.** Every movement came from a configuration flag:

- **0.00** — the answer was read from the wrong response field
- **0.33** — field fixed, but the token budget truncated long answers
- **0.67** — budget raised; the model swept the code-repair round
- **0.33** — re-run on a *different* context window, which silently capped how much it could think
- **0.67** — context window raised; **the model moved up an entire belt grade**

**The harness is the measurement.** That is not a caveat on the Arena's results. **It is the Arena's
product.**

---

# PART II — THE INSTITUTION

## 2.1 Divisions: weight classes, measured on a scale

A local model's relevant attribute is not how many parameters it has. It is **what it occupies in
memory while running.** So the Arena weighs it.

| division | measured footprint | cord |
|---|---|---|
| **Featherweight** | ≤ 4 GB | teal |
| **Lightweight** | ≤ 8 GB | amber *(the reference class)* |
| **Middleweight** | ≤ 16 GB | violet |
| **Heavyweight** | > 16 GB | crimson |
| **Open / offload** | CPU + RAM | slate |

**Measured, not declared.** Footprint is baseline-subtracted peak VRAM sampled during the run.

**And the scale genuinely matters:** a model file of 0.21 GB measures **0.42 GB** when served. A 1.25 GB
file measures **≈1.6 GB**. The difference is KV cache and buffers — and **it is the measured number that
has to fit on your card**, not the file size. Declared classes are guesses. Weighed classes are facts.
*(Footprints jitter slightly run to run with baseline GPU activity; treat to about one decimal place.)*

## 2.2 Belts: rank by demonstration, never by award

| belt | earned by |
|---|---|
| **White** | weighed in — you served, you were measured, you entered |
| **Yellow** | won at least one round |
| **Orange** | won two of three rounds |
| **Green** | swept a bout |
| **Blue** | swept two consecutive bouts |
| **Purple** | swept three consecutive — **earns a mandatory challenge one division up** |
| **Brown** | top three on a division card |
| **Black** | **division champion** |
| **1st–10th Dan** | **consecutive successful title defences** |
| **Red** | **held a belt in three different divisions** |

**The dan grades are the elegant part:** a dan grade *is* the title-defence count. It cannot be bought,
gifted, or argued. You either defended or you didn't.

**The red belt is the summit.** To earn it a model must win its division, move up a weight class, win
again, move up again, win a third time against bigger footprints. It is rare by construction, and every
one is a **measured answer to the question: where exactly does capability break with size?**

Belts are lost by **failing to defend**, not by losing. Rankings **decay after 180 days without
fighting**, so nothing survives on reputation.

**Stripes are single trials won** — three rounds times three trials is up to nine. *Stripes are the
record; the belt is the rank.*

## 2.3 The weigh-in: you cannot fight if you cannot serve

**Before any bout, every entrant must prove it serves.** A model that fails to load is
**SCRATCHED — never scored.** On the first real card, **four of nine entrants were scratched**: two
pointed at files that no longer existed, one was unreachable, one was structurally unable to answer.

Scoring a model that did not run isn't a technicality. **It is publishing a lie.**

## 2.4 Certification: unverified to participate, certified to be crowned

| tier | how it works | what it's worth |
|---|---|---|
| **OPEN** | you run the harness, you submit your bundle | participation — permanently labelled **UNCERTIFIED** |
| **CERTIFIED** | **we load your model by its hash and re-run the bout on our rig** | glory, and belts |
| **CHAMPIONSHIP** | belts awarded only on certified results | the scarce good |

**This is the answer to cheating, and it is not detection — it is impossibility.** We don't verify what
you did. We re-run it ourselves. Only placing submissions get re-run, so certification is cheap, and
**cheating is not caught, it is impossible, because we ran the model.**

Screening for the open tier, in order of strength: **GGUF hash** (proves *which* model), **throughput
ceiling** (a 350M on an 8 GB card cannot do 300 tokens/second — a routed API can), **inter-token interval
jitter** (local inference is hardware-bound and tight; network calls are jittered and batched), and
**logprob capture** where the server exposes it.

## 2.5 The events

| event | format | what it answers |
|---|---|---|
| **Single bout** | 3 rounds, one model, one belt | baseline competence |
| **Cage match** | 2 models, blind, deterministic scoring, one winner per round. **Rebuttal variant:** each sees the other's answer and may revise; the final answer is scored | head-to-head |
| **Biathlon** | accuracy × throughput, every miss costs a penalty loop | **the real deployment trade** |
| **Triathlon** | 3 disciplines, may cross divisions | generalist or specialist? |
| **Decathlon** | 10 disciplines, points table | **the profile** |
| **Marathon** | long-context endurance; the output is a decay curve, not a score | where attention breaks |
| **Relay / tag team** | N models, baton passed at typed handoffs | **can chaining beat a single bigger model?** |
| **Team vs team** | line-ups, best-of-N, substitutions between rounds | squad depth |

### The biathlon is the commercial event

Real biathlon ranks on total time **including penalty loops**. That is exactly the local-inference
trade-off, and nobody measures it as one number:

> **total = (latency × trials) + (misses × k × latency)**

**`k` is the engineering decision.** It is *how much being wrong costs you, in your application.* Raise
`k` and correctness dominates; lower it and speed does. **The Arena turns an argument into a number.**

On our own Featherweight card: one model won the *accuracy* comparison while the other won the biathlon
**by roughly 19×** — because a ~16× latency gap dwarfs a 2× accuracy gap. **Both numbers are true. Only
the event tells you which one applies to you.**

### Teams compete at the sum of their footprints

A 350M plus a 2B team is a legitimate 2 GB Featherweight entry. A 2B plus a 9B team measures ~11 GB and
therefore fights in **Middleweight**. **You cannot field three giants and call yourself a featherweight.**

And the relay is not a novelty — **it is the production architecture.** Nobody runs one local model for
everything. They run a small router, a bigger worker, maybe a critic. **The tag team is that
architecture, made measurable.**

---

# PART III — THE GAMES

Every event needs a scorer that is **deterministic or ground-truthed.** No language model judging a
language model — that is a family member marking the exam, and it is the most common way a benchmark
becomes worthless. Where generation must be judged, we use **deterministic specifications** (render
*these exact data points*), **objective constraints** (key, tempo, no parallel fifths), or **executed
verification.**

## 3.1 The market-models league

*Which local model is the most capable trader, using only available market data?*

| event | measures | scorer |
|---|---|---|
| **Forecast Duel** | probability vs market price | Brier skill score vs market |
| **Market Selection** | rank opportunities under a capital budget and a holding period | realised return |
| **Quote Placement** | choose bid/ask/size from book + tape | simulated markout P&L |
| **Toxicity Detection** | which fills were adversely selected | AUC vs realised markout |
| **Arbitrage Detection** | find and size cross-market mispricing | edge **net of costs** |
| **Capital Allocation** | allocate a budget across duration-locked opportunities | return on capital |
| **Inventory & Risk** | hedge, widen or pull under incoming flow | drawdown-adjusted P&L |
| **Settlement Reasoning** | apply resolution rules to adversarial edge cases | exact match |

**Early result, stated honestly:** on the one event already run — 230 resolved prediction markets —
**no local model beat the market.** The best of them was a 9B, which **beat a 35B**. Size did not
determine quality. That is the single strongest argument that **narrow, task-specific adaptation** is
where the remaining gains are — and that the games matter, because they are how you discover *what* to
adapt.

## 3.2 The multi-discipline league

| event | scorer | 
|---|---|
| **Agency** | sandbox goal + tool budget; success, steps used, **destructive-action penalty** |
| **Speed** | tokens/sec, time-to-first-token, **time-to-correct-answer** |
| **Accuracy** | contamination-controlled set, exact match |
| **Problem Solving** | broken program + failing test → tests pass, minimal diff |
| **Web Skills** | retrieve, extract, answer — **correctness plus no fabrication** |
| **Tool Calling** | exact match on parsed arguments |
| **Structured Output** | schema-valid rate under adversarial instruction pressure |
| **Self-Calibration** | Brier score on "will I be right?" |
| **Image / Video** | a deterministic spec (plot these exact points) → structural similarity |
| **Song Composition** | MIDI against objective constraints + stylistic distance |
| **Code Review** | seeded-defect detection, false-positive rate |
| **Compression** | information retained on held-out questions |

## 3.3 The team league — inference + deterministic + diffusion

| event | composition | why it matters |
|---|---|---|
| **Deterministic Arbiter** | a language model proposes; **a program verifies** | **the most valuable game in the book.** Objectively gradeable, and it is how reliable agents are actually built |
| **Model Relay** | propose → critique → decide | does the ensemble beat its best part? |
| **Specialist Team** | reasoner judges, verifier checks, renderer draws, writer composes | role assignment by measured strength |
| **Red / Blue** | one team generates hard cases, the other solves them | self-improving curriculum with a real difficulty signal |
| **Diffusion-in-the-loop** | a reasoner specifies a diagram, a diffusion model draws it, **a vision model verifies it against the spec** | genuinely ties the modalities, with verification as the scorer |
| **Budget Auction** | models bid for turns and compute | **outcome per token** — efficiency inside the score |
| **One versus Many** | a single model against a team, same task | win rate **and** cost |

## 3.4 Four rules without which none of this is worth running

1. **Every event needs a deterministic or ground-truthed scorer.**
2. **Include a null baseline in every event** — the market price, a random policy, a one-line script.
   **Every flattering number in our own development came from a missing or wrong baseline.**
3. **Cost is part of the score.** Tokens, latency, VRAM. A winner that used 100× the compute has not won.
   Because this is about *local* models, every event runs **two tracks: absolute, and per gigabyte of VRAM.**
4. **Pre-register before running.** Fix the task set, the scorer, the baselines and the decision rule
   first. Otherwise you get post-hoc storytelling — and with enough entrants competing, you will find
   *something*.

---

# PART IV — THE PROOF IT WORKS

## 4.1 What the harness does

`arena.py` — **~720 lines, Python standard library only, no installation.**

- **Launches its own model server** with flags it controls, and prints them. It never talks to an
  application-configured endpoint: **an alias is an application, and benchmarking an application tells
  you nothing about the model.**
- **Weighs the model on a scale** — measured VRAM, not file size.
- **Scores by parser and by execution** — generated code is *run against a real test suite* in an
  isolated subprocess. It crosses the line only if the tests pass.
- **Prints its provenance with every result:** the sampling config, the context size, the token budget,
  the complete server command line, and the model's **SHA-256 hash**. *A result without its config is
  not a result.*
- **Refuses to grade what it cannot trust.** Pointed at a result bundle from an older version, it
  responds: **`CANNOT DERIVE A BELT: this bundle predates per-round win counts. Reporting 0 stripes
  here would be a confident lie.`**
- **Validates itself.** `--self-test` runs 11 assertions, including ones that prove each scorer *rejects*
  a wrong answer. **A scorer that only ever passes is not a scorer.**
- **Cleans up after itself** — a killed run cannot leave a model resident holding video memory.

## 4.2 Measured results from the reference rig

**A single RTX 3060 Ti with 8 GB.** Nothing exotic — deliberately, because the point is that a standard
consumer machine is enough to define a standard.

| entrant | measured footprint | belt | stripes |
|---|---|---|---|
| LFM2-350M | **0.43 GB** | **Yellow** | 3/9 |
| Qwen3.5-2B | **1.64 GB** | **Orange** | 6/9 |

**A 350-million-parameter model earned a belt and swept the tool-calling round 3/3 against the field.**
A model **4× larger** earned a higher belt and answered *every single question* out of its reasoning
field. **Both facts are real. Neither was visible before the harness owned its own server and published
its own flags.**

## 4.3 The three mechanisms, each with evidence

| # | mechanism | evidence |
|---|---|---|
| 1 | a **grammar** forbids the output the task requires | two different models, identical weights within each pair, dropped from **Yellow to White** — losing exactly the round the grammar made unrepresentable |
| 2 | a small **token budget** truncates a reasoning trace before it answers | one model's code-repair round went **0/3 → 3/3** when the budget was raised. **Nothing about the model changed.** |
| 3 | a small **context window** caps how much a model may think before it is graded | **Yellow → Orange** from a context flag alone |

**All three are configuration. All three are invisible in the final score. All three bite hardest on the
most capable reasoning models** — meaning a fixed-budget benchmark **systematically under-rates
intelligence**, and the bias points in one direction.

**A note on our own errors, because it is the whole point:** the first version of our truncation
diagnostic always advised *"raise the token budget"* — and that advice was **wrong** when the binding
limit was the context window instead. **A diagnostic that names the wrong cause is worse than no
diagnostic**, because it converts a measurement failure into confident, actionable, wrong advice.

The harness now says exactly which limit bit. We shipped the correction *and* the story of the mistake,
because a project that hides its false starts is teaching you to trust numbers you shouldn't.

## 4.4 What ships in the repository

`arena.py` · three task definitions as data (drop in a JSON to add a round) · the belt system · the
biathlon · the event book · **FINDINGS/001** with four raw evidence bundles, each carrying its full
config and hash · and **`history/`** — the four earlier iterations, **kept deliberately**, so the
failures are documented instead of forgotten.

**The format is easy to copy. Knowing which of your numbers are real is not.**

---

# PART V — THE PLAN

| # | step | cost | stop condition |
|---|---|---|---|
| **0** | **Start a daily market-data logger** — a snapshot of every candidate market | free, but **time-gated** | the data turns out to be unstable or withdrawn |
| **1** | **Pre-register and freeze the scoreboard** on forward outcomes | free | the metric can't be gamed by its own outcome |
| **2** | **Complete the selection inventory** and test it against a null baseline | free | no selection rule beats picking at random |
| **3** | **Install the training toolchain** | **the one expensive step** | won't fit in available video memory |
| **4** | **One test adapter**, end to end: train, convert, serve | moderate | the adapter can't beat its base model |
| **5** | **Open the league** — the games, the cards, the belts, remote challenges | ongoing | the scoreboard proves untrustworthy |

**Step 0 goes first because it costs time rather than work**, and it is the only step that cannot be
recovered later. Step 3 goes late because it is the only step with real cost — and **the session's whole
lesson is that optimising against an unvalidated scoreboard just finds a better way to fool it.**

## 5.1 How the games close the loop

**Games → diagnosis → adapter → re-test.**

The league's job is not to crown a winner. It is to locate **where a model fails specifically enough
that a narrow adapter can fix it.** The general events are dead ends — everyone loses, nothing to adapt
toward. The narrow, objective ones — **toxicity detection, quote placement, market selection** — are
exactly the shape where a small specialised adapter beats raw scale.

**That is what "punching above your weight class" means in practice.** Not a bigger model. A *fitter*
one.

---

# PART VI — PRODUCTION NOTES FOR AN EXPLAINER

## 6.1 The narrative spine (three acts)

**ACT I — The lie.** Open on a leaderboard. A 4-billion-parameter model, rank 417. Hard cut: the same
model running happily on a cheap consumer card, doing real work for a real person. **"It didn't come
417th. It was competing in a different sport."**

**ACT II — The exposure.** The Arena builds a harness. It runs. It produces a clean, confident
leaderboard — **and the leaderboard is wrong.** Four times, for four different reasons, none of them the
model. *A grammar file. A deleted file. The wrong field. A lying alias name.* Then the gut-punch: **one
model, five measurements — 0.00, 0.33, 0.67, 0.33, 0.67 — and not one of those changes was about the
model.**

**ACT III — The institution.** Weight classes measured on a scale. Belts earned by demonstration. A
weigh-in that scratches anyone who can't serve. **Certification where cheating isn't detected but
rendered impossible** — because we re-ran the model ourselves. And a league where a 350-million-
parameter model can get off the canvas and take a round off something ten times its size.

## 6.2 The money lines (on-screen text candidates)

- **"The harness is the measurement."**
- **"It didn't come 417th. It was competing in a different sport."**
- **"A model that can't serve doesn't fight. It gets scratched."**
- **"Cheating isn't detected. It's impossible — because we ran the model."**
- **"A result without its config is not a result."**
- **"Reporting 0 stripes here would be a confident lie."**
- **"We don't rank models. We weigh them, and we make them earn it."**
- **"The format is easy to copy. Knowing which of your numbers are real is not."**

## 6.3 Visual beats with hard numbers

| beat | the number | why it lands |
|---|---|---|
| the scale | **0.21 GB on disk → 0.42 GB served** | a declared weight class is a guess; a weighed one is a fact |
| the scratch | **4 of 11 entrants scratched at the weigh-in** | you cannot fight if you cannot serve |
| the four confounds | **4 wrong leaderboards, 0 errors thrown** | every failure is silent, and every one produces a table |
| the five measurements | **0.00 → 0.33 → 0.67 → 0.33 → 0.67** | the same weights the whole time |
| the grammar | **Yellow belt → White belt, from one flag** | rank destroyed by configuration |
| the context window | **3/9 → 6/9 stripes, from one flag** | a model is graded on how much it's allowed to think |
| the biathlon | **≈2.7 s vs ≈52 s** | same weights, same memory, **19× apart** — because of a flag. *(Latency jitters run to run; treat as approximate.)* |
| the upset | **a 350M sweeps the tool round 3/3 against the field** | this is why divisions exist |
| the inversion | **a 9B beat a 35B** | size is not the axis |
| the refusal | **"Reporting 0 stripes here would be a confident lie."** | the ethics are in the code, not the marketing |

## 6.4 The one-line thesis

> **A local-model benchmark that doesn't publish its token budget, context window, server flags and
> model hashes isn't measuring models. It's measuring plumbing — and it doesn't know it.**

## 6.5 Glossary of Arena terms

**Division** — weight class, assigned by measured VRAM · **Weigh-in** — pre-flight serve verification ·
**Scratched** — failed the weigh-in; not scored · **Bout** — three rounds of three trials ·
**Round** — one task · **Stripe** — one trial won · **Belt** — rank earned by demonstrated results ·
**Dan** — consecutive title defences · **Red belt** — a belt in three different divisions ·
**Catchweight** — a lighter model challenging upward, keeping its true footprint ·
**Markout** — the price movement after a fill; the honest measure of whether a fill was good ·
**Null baseline** — the dumbest thing that could work, included so you can tell whether you did anything

---

*The Handicap Arena is an independent, open project. Divisions are measured, belts are earned, and every
number links to a configuration and a hash that can reproduce it.*
