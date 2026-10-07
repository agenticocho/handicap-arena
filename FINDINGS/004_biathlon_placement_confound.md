# FINDING 004 — the biathlon is not runnable under auto-fit placement

**Date:** 2026-10-06 · **Harness:** `arena.py` (v1.0) · **Status:** open; needs an all-CPU division

---

## 1. The confound reaches the composite score, not just the reported latency

`arena.py:635` scores the biathlon as:

    total = (mean_latency × trials) + (misses × k × mean_latency)

**Latency is the base unit of the score.** Every term is a multiple of `mean_latency`, so a
latency that depends on where a model was placed contaminates the *whole figure*, not merely a
column shown beside it. Saying "the latency column is unreliable" understates it.

## 2. Placement varies per entrant, and is set by something other than the entrant

Confirmed in the result bundles:

    n_gpu_layers: null
    placement:    "auto-fit"
    gpu_free_gb_at_weigh_in: 1.6

Each model receives whatever VRAM happens to be free **at its turn**. That free figure is
determined by the production stack — at the time of writing `nvidia-smi` showed **6,453 of
8,192 MiB held by resident servers.** The tournament runs on the leavings of the production
system, which is the confound *and* a separate resource conflict.

This is not an oversight. `arena.py:197-203` is deliberate: a fixed `--ngl 99` **aborts** on a
contended GPU, so auto-fit is the safe choice. It is the right default for the question *"does
this model run here?"* It is invalid for *"is this model faster?"*

## 3. What this does NOT contaminate — checked, not assumed

The obvious hypothesis is that partial offload → slowness → timeout → truncated → **wrong scores**.
**It does not hold:**

- The generation timeout is **900 s**, far too generous to bind at these model sizes.
- The truncation that does occur is a **token cap**, not a time cap.

**The accuracy scores stand.** A scored round is placement-independent: either the model produced
a parseable correct answer or it did not.

## 4. The truncation that is real, and why it is not a placement artefact

    LFM2-350M-Math-Q4_K_M   R3_pitstop  finish_reasons {length: 3}   ALL THREE hit the 3,000 cap
                            R1, R2      finish_reasons {stop: 3}     unparseable
    Qwen3.5-2B              1 of 3 trials truncated

Its 0/9 is a **fair capability result**: R1 and R2 were genuinely unparseable, and rambling past
3,000 tokens on a code-repair task is a real failure. Placement did not cause it.

## 5. The fix: all-CPU is the only valid normaliser

For any latency comparison:

| option | valid? | why |
|---|---|---|
| fixed `--ngl N` | **NO** | `ngl` counts **layers**, not bytes — the same `N` is a different VRAM footprint for every architecture |
| auto-fit | **NO** | varies per run with momentary free VRAM, so the same model on the same box can differ between runs |
| **`--ngl 0` (all-CPU)** | **YES** | identical placement for every entrant, by construction |

**All-CPU is also the honest match for this machine.** RAM is abundant (60 GiB) and VRAM is the
scarce resource (8 GB), and CPU FFN offload is the documented best placement for aux-scale models
here rather than a fallback.

**Rule: do not mix placements inside one latency comparison.** If both are wanted, run two
divisions — *"does it run"* (auto-fit) and *"is it fast"* (all-CPU) — and never average across them.

## 6. Consequence for the board

Two changes, neither of which alters a score:

1. **Surface `finish_reasons` per round.** "Hit the token cap" and "answered wrongly" are
   different signals — for someone choosing a model to put in service, *won't stop talking* and
   *answers wrong* are different failures. The bundles already carry the distinction; the board
   now shows it.
2. **Show placement per entry**, including `gpu_free_gb_at_weigh_in`, so a reader can see which
   division a figure belongs to.

## 7. Retained as an open item

A latency comparison on this box requires a separate all-CPU run across the same field. It is
slow — everything runs on CPU — which is precisely why it is a separate exercise rather than a
default. Until it exists, **no biathlon total from this field may be quoted.**
