# FINDING 004 — The standing card is saturated

**Status:** measured · **Evidence:** 50 bundles in `results/`, 42 graded
**Run:** `run_card.py`, 167.6 min, ctx 8192 / mt 3000 / trials 3, `--ngl` omitted (auto-fit)
**Date:** 2026-10-07

---

## What was run

The standing card — fencing, chess, pit stop — across every text-capable GGUF in the model
library, at one declared configuration, verifiable from each bundle's own recorded
`config.server_flags`.

**42 models graded. 8 did not serve at all.**

## The result that matters

    1.00  (9/9)  ->  21 models
    0.89         ->   1
    0.67  (6/9)  ->  10
    0.56         ->   2
    0.33  (3/9)  ->   4
    0.00  (0/9)  ->   4

    White 4 · Yellow 4 · Orange 12 · Green 22

**Fifty-two percent of the field scores a perfect aggregate.** The Green sweeps span the entire
size range:

    LFM2.5-1.2B-Instruct-Q6_K      0.32 GB   Featherweight
    Qwen3-1.7B-Q8_0                0.61 GB   Featherweight
    Llama-3.2-3B-Instruct          0.55 GB   Featherweight
    SmolLM3-3B                    0.57 GB   Featherweight
    Meta-Llama-3.1-8B              2.85 GB   Lightweight
    MiMo-V2.6-Distill-Qwen-9B      2.64 GB   Lightweight
    Tiel-Coder-35B-A3B             3.46 GB   Heavyweight
    Ornith-1.5-35B-A3B             3.47 GB   Heavyweight

**A 0.32 GB model and a 35B model are indistinguishable on this card.** The task suite cannot
discriminate between them, which means it is not measuring capability at the top of its range —
it is measuring a floor.

## Why this is the expected failure, and what it costs

`GAMES.md` states the requirement directly: *"the most valuable contributions are tasks that are
hard to game and **impossible to saturate**."* This card is now demonstrably saturable, and the
consequences land in a specific order:

1. **A leaderboard built on this card would be meaningless.** Twenty-two ties at the top, ordered
   by a number the tasks cannot resolve. That is why the leaderboard was gated behind a frozen
   scoreboard — and the freeze now has a second reason.
2. **The belt system loses its upper range.** Green is supposed to mean "swept the card"; when 52%
   of entrants sweep it, Green is the participation award. Blue, Purple, Brown and Black inherit
   nothing.
3. **The 0.67 cluster is a task-design signal, not a capability one.** Ten models from unrelated
   architectures and quantisations land on *exactly* 6/9. Identical scores across unrelated models
   usually means one round is capping everyone — and the round to suspect is R1 fencing, the
   structured-output round, which is also the round that exposed the grammar confound.

## The good news, and it is real

**FINDINGS/002 was exercised in production, on the largest models, and held.** The 35B entrants were
partially offloaded — and the harness reported it honestly rather than silently re-classing them:

    ** PARTIAL OFFLOAD — resident 3.49 GB is LESS than the 22.75 GB of weights on disk,
       so the surplus is on CPU.
       DIVISION: Heavyweight  (taken from WEIGHTS — ...)

Six entries were divisioned Heavyweight on weights alone at 3.46–3.49 GB *resident*. Without that
clause they would have been filed as Lightweight and would have "beaten" every Featherweight in the
table. The fix earned its place on the first real field.

## Two defects in this run, both mine

**1. The run summary lied, in the optimistic direction.** `run_card.py` reported *"scored 46,
scratched 0"*. The artifacts say **42 scored, 8 scratched**. Cause: the harness writes a bundle even
for an entrant scratched at weigh-in, so `rc=0 and bundle exists` was counted as a score — an 8-byte
answer for an 807 MB model. The fix (require ≥1 graded entry) landed after the process had already
loaded the module, so this run kept the bug. **The corrected count is the one computed from the
bundles.**

**2. A naming violation, and one run output that is unaccounted for.**

`LFM2.5-1.2B-Instruct-Q6_K` has exactly **one** bundle:
`LFM2.5-1.2B-Instruct-Q6_K_autofit_neutral_ctx8192_mt3000.json`. That puts `_autofit` where the
convention puts the **model** name, so the serving distinction is recorded in the wrong slot — it
renders as a model called `..._Q6_K_autofit`, which is not a model.

Separately, and **unresolved**: `results/card_run.log` records
`LFM2.5-1.2B-Instruct-Q6_K  rc=0  18s  bundle=True`, and `run_card.py` writes
`<stem>_neutral_ctx8192_mt3000.json` — but no bundle under that name exists. The file count is
fully accounted for (50 files = 42 graded + 8 empty), so this is not a lost file; the run's output
for this model appears to be recorded under the `_autofit` name instead. **Recorded as an open
discrepancy rather than explained away.** I first reported this as a duplicate; on checking the
directory it is not one, and that claim is withdrawn.

## 8 models could not serve

    Cloudflare_clef-flash        IQ4_NL, Q4_K_M
    Kev-4B                       Q4_K_M
    Ternary-Bonsai-2-27B         PQ2_0, PTQ1_0, Uncensored-Heretic-PQ2_0
    Underdog-27B                 PQ2_0
    laya_english_f16             (f16)

Not scored, not fabricated — each produced an empty bundle and no row. But a **16% unservable rate**
is a finding about the model library, not about the models: ternary and low-bit quantisations are
prime suspects for unsupported tensor types in this llama.cpp build, and the reason should be read
from the server logs rather than guessed.

## What this changes

The card is a **floor test**, and it is now calibrated: it separates White/Yellow/Orange from Green
and does nothing above Green. **Nothing further can be built on top of it until it is hardened.**

Per `GAMES.md`'s own build order, the next work is **I3 Adversarial Task Generation** — near-miss
variants that break surface-form matching — and **R1 fencing** should be examined first, since the
0.67 cluster points at it. The honest summary: the arena just completed its first full field, and
the field's main lesson is that the questions are too easy.
