# The GPU path is measured, not assumed — 2026-10-25

Run by the Local Chair on Chilly (RTX 3060 Ti, 8,192 MiB). Approved by Mike in-session.

## What was in doubt

The resident 9B seat (`prism-bonsai-9b`, `127.0.0.1:58595`, `prism-brain.service`) runs
`--n-gpu-layers 0`. Its binary is the PrismML CUDA build, so the *capability* was present and
the *use* was not. Every 9B row in this repo was therefore produced on CPU, and none of the
records said so. That is a provenance defect in the rows, not a defect in the model.

## The probe

One variable changed. Same binary, same model, same cache types. Projector dropped (`--mmproj`
absent, text-only), layers raised to 99, context lowered to 8192 to keep the KV cache small, and
a separate port so that Prism's brain was never touched or restarted.

```
binary   /home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server
model    Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0.gguf
flags    --ctx-size 8192 --cache-type-k q8_0 --cache-type-v q8_0 --n-gpu-layers 99
         --host 127.0.0.1 --port 58620        (no --mmproj)
```

Measured, same prompt and same generation parameters against both seats, thinking disabled:

| seat | wall | tokens | throughput |
|---|---|---|---|
| GPU, `--n-gpu-layers 99` | 1.21 s | 112 | **92.44 tok/s** |
| CPU, `--n-gpu-layers 0` (the live seat) | 18.35 s | 116 | 6.32 tok/s |

**14.6x.** Both produced the same answer text at the same opening, so the speedup is not paid for
in divergence.

VRAM: the probe held **2,706 MiB** (competing with the resident seats' 1,402 + 134), leaving
3,449 MiB free. After shutdown, GPU memory returned to its baseline 1,731 MiB with no listener left
on the probe port. `prism-brain.service` stayed `active` and `:58595/health` stayed 200 throughout.

## What this licenses

A 9B class model fits in ~2.7 GiB at 8K context on this card. That means the card can hold a
resident brain *and* one working entrant at the same time, which is what the multi-model suite
needs. It does not mean two large entrants can run concurrently — see the suite plan.

## What it does not license

It does not retroactively upgrade any published row. The 9B rows remain CPU rows at 6.3 tok/s and
must be read as such. `MASTERMIND_RESULTS.md` is a closed artefact — its digest `0e66af83…` is
held by a peer — so this note sits beside it rather than editing it.

## Negative control that would have caught the original error

The seat's own argv carried `--n-gpu-layers 0` the entire time. A row that records its compute
path cannot be misread later; a row that records only its model name can be.
