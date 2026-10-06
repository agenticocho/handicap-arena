# FINDING 001 — Serving configuration dominates the score

**Date:** 2026-10-06 · **Status:** reproduced under controlled conditions · **Severity:** fatal to any
benchmark that ignores it

---

## The result

**Identical weights.** `Qwen3.5-9B-UD-Q4_K_XL.gguf`, verified by sha256. Same machine, same GPU,
same task suite, same scoring functions, same locked sampling config (temperature 0.0, trials 3).
Three entrants, differing only in **how the model was served**:

| entrant | serving config | T1 fencing | T2 chess | T3 pit stop | **AGG** | mean latency |
|---|---|---|---|---|---|---|
| `critic1` | no grammar | 0.00 | **1.00** | 0.00 | **0.33** | 14.8 s |
| `proposer` | no grammar | 0.00 | **1.00** | 0.00 | **0.33** | 26.2 s |
| `ocho-planner` | **GBNF grammar applied** | 0.00 | **0.00** | 0.00 | **0.00** | 2.9 s |

**The same model scores 0.33 or 0.00 depending on a flag.** A benchmark that does not control for
this is measuring its own configuration and reporting it as model capability.

---

## Two independent mechanisms

The first hypothesis — "the grammar caused it" — was **insufficient**. The no-grammar runs still
failed two of three rounds. There are two separate failure modes:

### Mechanism 1 — a grammar constrains output the task cannot accommodate
A GBNF grammar forces *every* token to fit a fixed schema. When the schema belongs to a different
application, the model becomes **physically incapable** of the requested output — not unwilling,
incapable. Evidence: T2 went **1.00 → 0.00** purely from applying the grammar.

It also makes the model look *fast* (2.9 s vs 14.8 s), because a constrained output is a short one.
**A grammar can make a model both worse and apparently more efficient.**

### Mechanism 2 — reasoning models spend the token budget before answering
T1 and T3 still fail without any grammar. The latencies explain it: **14.8 s and 26.2 s** against the
constrained 2.9 s. A reasoning model emits a thinking trace first; if `max_tokens` is small, the
trace consumes the whole budget and the model **stops without ever answering**.

Independent confirmation, on a different model:

| model | round | max_tokens=1200 | max_tokens=3000 |
|---|---|---|---|
| Qwen3.5-2B | R3 pit stop | **0/3** | **3/3** |

**Nothing about the model changed.** The budget changed, and a round went from impossible to swept.

---

## Why this is the arena's founding result

The same model was measured four times during development and produced **0.00, 0.33, 0.67 and
0.33** — with no change to the weights. Every movement came from a harness fix:

| measurement | what was wrong |
|---|---|
| 0.00 | answer read from the wrong response field (`content` empty; it was in `reasoning_content`) |
| 0.33 | field fixed, but the token budget truncated long answers |
| 0.67 | budget raised; the model swept code repair |
| 0.33 (9B) | budget still too low for a *larger* reasoning model on long-output rounds |

**The harness is the measurement.** This is not a caveat on the arena's results — it *is* the arena's
product. The scarce good is not a ranking; it is **provable execution**.

---

## Rules this finding imposes on the format

1. **Every result must declare its `max_tokens`.** A score without it is not a score.
2. **Reasoning models need a token floor.** Below it you measure the budget, not the model. Models
   that emit `reasoning_content` should be flagged and given headroom.
3. **Round design must account for output length.** A short-output round and a long-output round are
   not comparable under the same budget.
4. **The harness must own its server flags and print them.** Never measure through an
   application-configured endpoint: an alias is an application, and benchmarking an application tells
   you nothing about the model.
5. **Truncation must be distinguished from failure.** "The model answered wrongly" and "we cut it off"
   are different claims. The harness now records `finish_reason` and labels the difference:
   `TRUNCATED at max_tokens before answering — not a capability result`.
6. **A model that cannot serve is scratched, not scored.** Models pointing at deleted files were
   scored 0.00 in an early run — publishing a lie about a model that never ran.

---

## Reproduced on a second model — the mechanism is general

The experiment was repeated on an entirely different architecture, through the neutral harness, using
`--extra-flags` to apply the same grammar:

| model | neutral serving | with the grammar | change |
|---|---|---|---|
| Qwen3.5-9B-UD-Q4_K_XL | 0.33 — T2 chess **1.00** | 0.00 — T2 chess **0.00** | −0.33 |
| **LFM2-350M-Extract-Q4_K_M** | 0.33 — T2 chess **3/3** | 0.00 — T2 chess **0/3** | −0.33 |

**Both models lost exactly the one round the grammar forbade, and nothing else that mattered.**
LFM2-350M was demoted from **Yellow belt to White** by a serving flag.

**The grammar's content confirms the mechanism.** It constrains the root production to
`{"contract_id": …, "direction": …, "magnitude": …, "reasoning": …}` — a fixed four-key object. A
tool call or a JSON-schema answer is therefore **not merely unlikely but unrepresentable**. The model
is not failing; it is *forbidden from succeeding*.

**Latency moved too — in opposite directions per model.** Qwen got *faster* under constraint (2.9 s
vs 14.8 s) because the grammar truncated its reasoning trace; LFM2 got **15× slower** (0.2 s → 3.0 s)
fighting the constraint. So a serving flag can alter score and apparent efficiency, and the direction
of the efficiency effect is **model-dependent and unpredictable**. There is no way to reason your way
to the right configuration; it has to be measured and published.

---

## Mechanism 3 — the context window is a silent belt-tax

Discovered by chasing a discrepancy: the *same model at the same settings* produced **Yellow (3/9)**
in one run and **Orange (6/9)** in another. That looked like nondeterminism. It was not.

The answer was in `finish_reason` and the token accounting:

```
R1_fencing   0/3   finish={'length': 3}   maxctok=1888   ctx=2048
R3_pitstop   0/3   finish={'length': 3}   maxctok=1767   ctx=2048
```

`completion_tokens ≈ 1888` against `ctx=2048` — **the model was hitting the CONTEXT WINDOW, not
`max_tokens`.** Raising `max_tokens` would have changed nothing; the room simply wasn't there.
Doubling the context, holding everything else fixed:

| config | R1 fencing | R3 pit stop | belt | AGG |
|---|---|---|---|---|
| `--ctx 2048` | 0/3 — context-limited | 0/3 — context-limited | **Yellow** | 0.33 |
| `--ctx 8192` | 0/3 — now max_tokens-limited | **3/3** | **Orange** | **0.67** |

**A context-window flag moved a model from Yellow to Orange with no change to the weights.** A
reasoning model pays for its thinking out of the same window as its answer, so a small `--ctx` is a
**cap on how much a model is allowed to think before it is graded** — and it penalises precisely the
models that think most.

**And this produced a bug in our own diagnostic worth recording:** the first version of the truncation
check said *"raise --max-tokens"* regardless of which limit bit. That advice was wrong here — it would
have sent the operator to tune a parameter that was not binding. The harness now reports **which**
limit was hit:

```
CONTEXT LIMIT hit (2048 tokens) before answering — not a capability result; raise --ctx
TRUNCATED at max_tokens (3000) before answering — not a capability result; raise --max-tokens
```

**A diagnostic that names the wrong cause is worse than no diagnostic**, because it converts a
measurement failure into confident, actionable, wrong advice.

---

## The three mechanisms together

| # | mechanism | evidence |
|---|---|---|
| 1 | a **grammar** forbids the output the task requires | Qwen3.5-9B 0.33→0.00; LFM2-350M 0.33→0.00, Yellow→White |
| 2 | a small **max_tokens** truncates a reasoning trace before the answer | Qwen3.5-2B pit stop 0/3 → 3/3 at 3000 |
| 3 | a small **--ctx** caps how much the model may think | Qwen3.5-2B Yellow → Orange at 8192 |

All three are **configuration**, all three are invisible in the final score, and all three bite hardest
on the most capable reasoning models.

---

## Reproduce

```bash
# neutral serving — the model answers freely
python3 arena.py --model model.gguf --max-tokens 3000

# same weights, constrained by a grammar: score collapses on the forbidden rounds
python3 arena.py --model model.gguf --max-tokens 3000 \
                 --extra-flags '--grammar-file some.gbnf'

# both print the full server command line, the GGUF sha256, and the locked sampling config
```

Verified twice on two different models, through two different serving paths. If a reported score
cannot be reproduced from the sha256, the flags and the config, it is not a result.

---

## The general lesson

**Configuration is a confound that scales with a model's reasoning ability.** The more a model
thinks before answering, the more a small token budget penalises it — so a fixed-budget benchmark
**systematically under-scores the strongest reasoning models** while flattering fast non-reasoning
ones. That is a bias, not noise, and it points in one direction.

Any local-model leaderboard that does not publish its token budget, its server flags, its prompt
template and its model hashes is not measuring models. It is measuring plumbing, and it does not
know it.
