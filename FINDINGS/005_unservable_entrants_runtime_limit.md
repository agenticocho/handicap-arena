# FINDING 005 — the unservable entrants are a runtime limit, not a model problem

**Date:** 2026-10-07 · **Scope:** 8 of 41 entrants in the v2 field (≈20%), 8 of 50 in v1

---

## What was assumed, twice

I wrote "a 20% unservable rate is a model-library problem" in two separate commits and moved on
without reading a log. The arena had been printing the log path every time:

    *** SCRATCHED AT WEIGH-IN *** llama-server exited early rc=1
        (log: .../cache/scratch/arena-server-83324-44357.log)

**The diagnostic was delivered, unprompted, at the moment of failure, and I did not follow it.**
Recording that because it is the same shape as everything else in this project's error family: the
information was present and the reading of it was not done.

## What the log actually says

    E gguf_init_from_reader: tensor 'output.weight' has invalid ggml type 142. should be in [0, 43)
    E gguf_init_from_reader: failed to read tensor info
    E llama_model_load: error loading model: failed to load model from <path>.gguf
    E llama_server: exiting due to model loading error

**`invalid ggml type 142; should be in [0, 43)`** — the file declares a tensor type this
llama.cpp build does not know. Type IDs in this build run to 42.

The failure is at **`gguf_init_from_reader`**, the very first read of the file — **before** any
placement decision, before auto-fit, before a byte reaches the GPU. So:

- It is **not** a VRAM problem (FINDING 002 does not apply).
- It is **not** contention with the production stack.
- It is **not** a defect in the harness.
- It is **not** a statement about the models' quality — they have never been executed.

## Confirmed on two files, both `PQ*` quants

    Ternary-Bonsai-2-27B-PQ2_0.gguf     -> type 142, rc=1, load error
    Underdog-27B-PQ2_0.gguf             -> type 142, rc=1, load error

`PQ` / `PTQ` in the filenames denote experimental low-bit and ternary encodings. Those are the
prime suspects, and the two I probed share an identical failure.

**Not probed, and listed as unprobed rather than assumed:** `Cloudflare_clef-flash-IQ4_NL`,
`Cloudflare_clef-flash-Q4_K_M`, `Kev-4B-Q4_K_M`, `laya_english_f16`. IQ4_NL and Q4_K_M are both
standard types, so they probably fail for a different reason — but "probably" is not a
measurement, and this finding does not claim them.

## What this changes

1. **The arena behaved correctly.** Eight entrants produced **empty bundles and no score** — no
   row, no zero, no fabrication. A model that cannot serve is scratched, not ranked last.
2. **The fix is a runtime or a re-quantisation**, not anything to do with the models, the GPU
   budget, or the card. Upgrading llama.cpp may or may not add type 142; re-quantising to a
   supported type definitely works and produces a comparable entrant.
3. **The `EMPTY` convention earns its keep here.** These are exactly the bundles whose filename
   must not be read as an entrant, and were exactly the 7 that were unmarked until the
   canonicaliser was run over them.

## The lesson, stated so it is reusable

**When a process prints a diagnostic path at the moment of failure, read it before labelling the
failure.** Two commits described this as a "model-library problem" on the strength of the
filenames alone, when a single `grep` on a log the tool had already named would have settled it.
