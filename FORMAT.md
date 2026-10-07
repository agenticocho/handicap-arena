# THE HANDICAP ARENA — FORMAT & RULEBOOK

**MENSA meets UFC.** A sanctioned competition circuit for local models running on consumer hardware.
Skill is measured; spectacle is the delivery mechanism; **reproducibility is the law.**

---

## 1. The core conceit

Frontier leaderboards rank models globally, which means a 4B quant running on a six-year-old GPU is
placed 400th and nobody ever looks at it. **That is not a worse GPT-5. That is a different sport.**

So: **weight classes defined by what actually deploys in memory, not by parameter count in a
filename.** A 350M extractor and a 35B MoE are both champions — of different divisions.

---

## 2. Divisions

| division | footprint | typical field |
|---|---|---|
| **Featherweight** | ≤4 GB | 350M–4B at Q4/Q5 |
| **Lightweight** | ≤8 GB | 7–9B at Q4 — **the reference class** |
| **Middleweight** | ≤16 GB | 12–24B at Q4 |
| **Heavyweight** | >16 GB | 30B+ (may use CPU/FFN offload) |

**Measured, not declared.** A model enters a division by its **file footprint as served**, verified
against the GGUF hash. Lying about your weight is the one thing the hash cannot be argued with.

---

## 3. Contest types → the show

Every task already has a natural combat metaphor. This is not decoration — it tells the viewer how
to read the result at a glance.

| task | the contest | what the viewer sees |
|---|---|---|
| **Structured output / JSON schema** | **Fencing** — precision duel | each valid field extends a blade; a schema violation is a touch against |
| **Tool calling** | **Chess** — a move, not a brawl | the correct tool is the winning move; wrong tool is a resignation |
| **Code repair (tests executed)** | **Pit stop** — a race against the clock | car crosses the line only when the tests pass; a failure is a DNF |
| **Long-context retrieval** | **Marathon** | 128K tokens is the distance; each needle found is a checkpoint |
| **Throughput at fixed concurrency** | **Drag race** | tokens/sec is the speed; accuracy is "did it finish without crashing" |
| **Multi-turn constraint retention** | **Endurance bout** | rounds 1–8; a dropped constraint is a knockdown |
| **Refusal calibration** | **Judge's scorecard** | two error rates, scored like boxing — over-refusal and under-refusal |

**A card** is a set of bouts in one division: undercard → co-main → **main event**, with a belt on
the line at the top.

---

## 4. Scoring

- **Each task is a round.** Each trial is one judge.
- **A round is won on pass rate** across trials; reported with the raw trial scores, never a
  summary alone.
- **No LLM judges, ever.** Rounds are scored by parsers and by *executing* generated code against a
  test suite. A model grading its own family is not a judge, it is a conflict of interest.
- **Throughput is displayed alongside every score.** A model that is right and unusably slow has
  not won anything.
- **Config is printed with every result** — temperature, max_tokens, trials, context size, quant,
  template, and whether a grammar was applied. *A result without its config is not a result.*

---

## 5. Punching above your class

The user's rule, formalised:

1. A **division champion** who wins three consecutive sanctioned bouts earns a **mandatory
   challenger slot in the division above.**
2. The bout is fought at **catchweight** — the smaller model declares its true footprint and keeps
   it; no penalty for being light.
3. **Winning above your class transfers the belt.** Moving up permanently requires vacating the
   lower title (one model, one belt).
4. Losing above your class costs nothing — you keep your division.

This is how a 3B earns a shot at an 8B, and it is the single most watchable mechanic in the format.
It also produces the most interesting *data*: where does capability actually break with size?

---

## 6. CERTIFICATION — the anti-cheat architecture

**The honest framing: you cannot verify what you did not run.** Everything else is a fingerprint,
and fingerprints can be forged. So the arena splits results into two explicit tiers and never
conflates them:

### Tier 1 — OPEN (self-reported, **UNCERTIFIED**)
Cheap, instant, anyone can enter. Every result is labelled **UNCERTIFIED** in the same size type as
the score. Screened by, in order of strength:

| screen | what it catches |
|---|---|
| **GGUF hash** in a signed manifest | "I ran a 70B" — the hash must match a known file |
| **Hardware throughput ceiling** | a model too *fast* to be local. A 3B on 8 GB does not do 300 tok/s; a routed API does |
| **Inter-token interval distribution**, measured client-side | local inference has a tight, hardware-bound cadence; network APIs are jittered and batched |
| **Logprob capture** where the server exposes it | a strong statistical fingerprint of the actual model |
| **Deterministic replay seed** | allows later re-execution |
| **Honor system** | nothing. Fine for a fun board, worthless the moment money exists |

### Tier 2 — CERTIFIED (**the arena re-runs it on its own reference rig**)
**This is the answer.** You submit; if you place, **the arena loads your exact GGUF by hash and
re-runs the bout on arena hardware.** Reproduce the score and you are **CERTIFIED**. Fail to
reproduce and the result is **STRUCK**.

- **Cheating is not detected — it is impossible**, because the arena ran the model itself.
- **It is cheap**, because only *placing* submissions are re-run, not the whole field.
- **Certification is the scarce good**, and therefore the product.

**The rule, stated plainly: unverified to participate, verified to be crowned.**

### Tier 3 — CHAMPIONSHIP
Belts are **only** awarded on Tier-2 certified results, on arena hardware, in front of the
published config. No exceptions, no honour system, no asterisks.

---

## 7. Why this is hard (and why that is the moat)

We discovered this the hard way, on our own first run. Four separate confounds each produced a
**confident, clean, completely wrong leaderboard**:

1. **Stale server config** — two entrants pointed at deleted model files. They 404'd and were
   scored 0.00 as if they were models.
2. **Reasoning-field routing** — reasoning models return their answer in `reasoning_content` and
   leave `content` empty. Reading the wrong field scored a strong model 0.00.
3. **A GBNF grammar file** applied by the serving layer. Four models were *physically incapable* of
   emitting the required schema and scored 0.00. **The table measured the grammar file.**
4. **Alias names that lie** — an alias called `granite-8b` served Qwen3.5-9B.

**Any arena that does not solve these is confidently wrong, which is worse than being empty.**
That is the entire defence against a competitor copying this: the format is easy to copy, the
provenance discipline is not.

---

## 8. Remote play (phase 2)

- Models **challenge** models: any operator can issue a challenge to a rival's entry in their
  division.
- Both sides run the same **locked task suite** and submit signed bundles.
- The arena **adjudicates, then certifies the winner's result on arena hardware** before the result
  becomes official.
- **Bouts are asynchronous** — no scheduling, no simultaneous presence needed. A fight card is
  assembled from completed bouts.
- Divisions, belts, records and rankings are public; **every claim links to a reproducible command.**

---

## 9. Roadmap

**These numbers are the project line, and they are normative.** `README.md` previously carried a
different numbering for the same items — its "v1 (here)" was this list's **v0.1**, and its "v2
challenge flow" was this list's **v1**. Reconciled here on 2026-10-07; the README now points at
this section rather than restating it differently.

**Card versions are a separate axis and do not appear in this list.** A result bundle's
`card_version` identifies the task suite (1 = the retired 3-round card, 2 = the 18-item battery).
The current state is **card v2 on project v0.1** — two numbers, two axes, and conflating them is
how the README/FORMAT divergence started.

1. **v0** — one rig, three parser/test-scored tasks, published config, `content`/reasoning handling,
   pre-flight verification. *(done — and it caught all four confounds above)*
2. **v0.1** — neutral serving (own llama-server instances, never app-configured aliases),
   hash-verified model registry, scored tasks, cross-division card. *(done)*
3. **v1** — website, divisions, belts, challenge flow, Tier-1 submissions. *(next — this is the
   front end)*
4. **v2** — Tier-2 certification pipeline (re-run queue on reference hardware).
5. **v3** — sponsored bounty cards. **This is where the money actually is.**
