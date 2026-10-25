# Multi-model cabinet suite — plan and tenancy, 2026-10-25

Approved by Mike in-session. Staged, not started: no entrant is loaded by this document.

## Why now

The GPU path was measured today at 92.4 tok/s against 6.32 on CPU (14.6x) with the entrant
holding 2,706 MiB at 8K context. The card can therefore hold the resident brain *and* one working
entrant. The constraint that made multi-model runs look expensive was a throughput assumption, and
the assumption was wrong because the seat had been running at zero GPU layers.

## Scope — local cabinets only

Runnable here, harnesses exist: **Mastermind, Sokoban, Zork, Snake, Labyrinth, Lights Out, Chess.**
Not runnable here: **Fencing, Pit Stop** — those are Jarvis's and would have to cross the link,
which is out of scope for this suite.

## Entrant ladder

Chosen to span capability rather than to flatter it, all fitting the measured VRAM envelope:

```
Ministral-3-3B-Instruct-2512-UD-Q4_K_XL      floor: smallest credible entrant
Ornith-1.5-9B-Q4_K_M                          mid: the seat class already in the record
MiMo-V2.6-Distill-Qwen-9B-Q4_K_M              mid: different lineage, same size
Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0            prism: 2.13 bpw, the one measured today
```

Each is run at `--n-gpu-layers 99`, `--ctx-size 8192` unless a cabinet declares otherwise, no
projector, on a private port. Any row that cannot state its compute path does not get filed.

## Tenancy — the rule Mike set, applied literally

V1. **One entrant resident at a time.** A cabinet holds the card for the length of its run.
V2. **The resident brain is not evicted, restarted, or reconfigured** to make room. If an entrant
    does not fit beside it, the entrant waits.
V3. **No parallel cabinets.** Sequencing is the default because a second cabinet would contend for
    the same card and turn two clean measurements into one contaminated one.
V4. **Release is part of the run.** A run is not complete until its entrant is stopped, its port is
    closed, and VRAM is back to the 1,731 MiB baseline.
V5. **The Arcade outranks everything else.** If a cabinet is running, it owns the GPU; the suite
    yields to it rather than the reverse.

## Instrument rules carried over from today's findings

I1. **No placeholder values in prompt fields.** A history field that holds `(no guesses yet)` where
    a value belongs is a live variable, not formatting — it flipped answers deterministically on an
    identical game state in Jarvis's test, and one such string is in our own Mastermind prompt.
I2. **Every row records its compute path** (`--n-gpu-layers`, ctx, quant). The 9B rows published
    before today are CPU rows and stay labelled as such.
I3. **Pin the prompt.** A run whose prompt differs from the registered one is a different run and
    gets its own registration.
I4. **Pre-register the criteria before the first model call.** No post-hoc scoring.

## Sequencing

Per cabinet: register prompt and criteria → run the 3B floor first (cheapest, and it validates the
harness on a model that cannot squint) → then the 9B entrants → file rows with compute path →
release the card.

Order of cabinets: Mastermind and Lights Out first, because both already have registered fixtures
and known-answer spaces, so an entrant's failure is attributable. Sokoban and Zork next. Snake,
Labyrinth and Chess last — Chess in particular carries the "a position that arrives with its legal
moves listed is not a chess position, it is a menu" lesson and deserves its own instrument pass
before entrant numbers mean anything.

## What this suite will not tell you

It will not separate model class from quantisation, because the entrants differ in both. A result
that holds across all four licenses a claim about the class; a split between the two 9B entrants
licenses nothing until bit-width is held fixed.
