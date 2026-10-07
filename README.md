# The Handicap Arena

**A sanctioned evaluation circuit for local models running on consumer hardware.**

Divisions by *measured VRAM footprint*, ranks as *belts*, everything scored by parsers and by
executing code. Download it, point it at your GGUFs, and see where your models actually stand.

---

## Why this exists

Ranking every model on one global leaderboard means a 4B quant on a six-year-old GPU is placed
417th and nobody ever looks at it. **That is not a worse GPT-5. That is a different sport.**

**Read the full white paper: [WHITEPAPER.md](WHITEPAPER.md)** — the problem, the institution, the games,
the measured evidence, and the plan.

So the arena separates two things that leaderboards collapse into one meaningless number:

- **Weight class** — *who you fight.* Assigned by **measuring peak VRAM on a scale**, not by the
  number in the filename. (A 0.21 GB file measures 0.42 GB served; a 1.25 GB file measures 1.57 GB.
  KV cache is real, and it's what actually has to fit.)
- **Belt** — *what you've proven.* Earned by demonstrated, reproducible results. Never awarded.

A 350M and a 35B can both be black belts. They are champions of different divisions.

---

## Quickstart

```bash
# 1. validate the scorers before trusting any score they produce
python3 arena.py --self-test

# 2. fight one model
python3 arena.py --model /path/to/model.gguf

# 3. fight everything in a directory
python3 arena.py --model-dir ~/models --pattern '*.gguf'

# 4. re-derive the belt from a stored bundle (belts are computed, never assigned)
python3 arena.py --grade result_my_model.json
```

**Requirements:** Python 3.8+ (stdlib only — no pip install), a built `llama-server` on your PATH or
passed via `--llama-server`, and some GGUFs. An NVIDIA GPU is optional; without one you get no
footprint measurement and the division reads `UNKNOWN`.

---

## What it does that a leaderboard doesn't

### It launches its own server, neutrally
The harness **spawns its own `llama-server`** with flags it controls and prints them. It never talks
to an application-configured endpoint. **An alias is an application, and benchmarking an application
tells you nothing about the model.**

### It weighs the model on a scale
Division comes from **baseline-subtracted peak VRAM** sampled with `nvidia-smi` during the run —
not from a parameter count, and not from file size. Unload other GPU workloads first, or a
concurrent model's eviction will skew the scale.

### It scores by parser and by execution — never by an LLM judge
- **R1 · FENCING** — JSON-schema compliance under instruction pressure. Parse-scored.
- **R2 · CHESS** — tool selection and arguments. Parse-scored.
- **R3 · PIT STOP** — code repair. **The generated code is executed against a real test suite** in an
  isolated subprocess. It crosses the line only if the tests pass.

A model grading its own family is not a judge. It is a conflict of interest.

### It prints its provenance
Every result carries the config, the server flags, and the **GGUF sha256**. *A result without its
config is not a result.*

---

## Four confounds this design exists to prevent

Each of these produced a **confident, clean, completely wrong leaderboard** when we hit it ourselves.
They are the reason the harness looks the way it does:

| # | confound | what it fakes | how this harness prevents it |
|---|---|---|---|
| 1 | **stale server config** pointing at deleted model files | entrants scored 0.00 that don't exist | **weigh-in**: a model that doesn't serve is **scratched**, never scored |
| 2 | reasoning models answer in `reasoning_content`, `content` empty | the wrong field read; a strong model scores 0.00 | reads both fields, and **reports** which one it had to use |
| 3 | a **GBNF grammar file** applied by the serving layer | the table measures the grammar, not the model | **we control the server flags**, and we print them |
| 4 | **alias names that lie** (`granite-8b` serving Qwen3.5-9B) | silent model substitution | we take a **file path** and report its **sha256** |

**A leaderboard built on an unverified harness is worse than no leaderboard, because it is
confidently wrong.**

---

## Divisions

| division | measured footprint | cord |
|---|---|---|
| Featherweight | ≤4 GB | teal |
| Lightweight | ≤8 GB | amber *(the reference class)* |
| Middleweight | ≤16 GB | violet |
| Heavyweight | >16 GB | crimson |

## Belts

`White` → `Yellow` → `Orange` → `Green` → `Blue` → `Purple` → `Brown` → `Black`, then **dan grades
by title defence**. A **red belt** is reserved for a model that has held a belt in three different
divisions — the measured answer to *"where does capability break with size?"*

Full grading rules in **[BELTS.md](BELTS.md)**. Format and contest metaphors in **[FORMAT.md](FORMAT.md)**.

**Stripes are single trials won.** They are the record; the belt is the rank.

---

## Certification

| tier | how | worth |
|---|---|---|
| **OPEN** | you run it, you submit the bundle | participation — labelled **UNCERTIFIED** everywhere |
| **CERTIFIED** | **we re-run your model from its sha256 on our rig** | glory, and belts |

**Unverified to participate. Certified to be graded.** Only placing submissions get re-run, so
certification is cheap — and cheating isn't *detected*, it's **impossible**, because we ran the model.

---

## Extending it

Drop a JSON file in `tasks/`. No code changes needed:

```json
{
  "id": "R4_marathon",
  "kind": "long_context_retrieval",
  "metaphor": "MARATHON",
  "scorer": "json_schema",
  "prompt": "...",
  "spec": { "required": ["found"], "enums": {"found": ["yes", "no"]} }
}
```

Available scorers: `json_schema`, `tool_call`, `code_repair`. **Every new scorer must be covered by
`--self-test`**, including a case that proves it *rejects* a wrong answer. A scorer that only ever
passes is not a scorer.

---

## Games

Fifty-five events across ten leagues: market and decision games, reasoning and code, agency,
perception, creative under objective constraints, calibration, efficiency, team relays,
diagnostics, and strategy evaluation. Each carries a deterministic or ground-truthed scorer,
**a declared null baseline**, and an honest statement of how it can be gamed.

**Full catalogue: [GAMES.md](GAMES.md)**

## Roadmap

- **v1 (here)** — local harness, 3 rounds, weigh-in, belts, result bundles
- **v2** — challenge flow: models issue and accept challenges remotely, asynchronously
- **v3** — certification pipeline on arena hardware; public belts and cards
- **v4** — sponsored bounty cards

---

## Contributing

The most valuable contributions are **tasks that are hard to game and impossible to saturate**, and
**new scorers with self-tests that prove they discriminate.** Rotating held-out task suites are the
moat; a static suite gets tuned to within a month.

## Licence

MIT.
