# FINDING 002 — The weigh-in measures the machine, not the model

**Status:** observed, mechanism identified, fix specified
**Severity:** high — it silently changes a model's weight class
**Discovered by:** the relay build, from a failed run

---

## The observation

One model, one quantisation, one checkpoint, **two weigh-ins eight times apart.**

| model | weigh-in | placement | division | belt class |
|---|---|---|---|---|
| Qwen3.5-2B-UD-Q4_K_XL | **1.55 – 1.64 GB** | `--n-gpu-layers 99`, GPU has room | Lightweight (< 8 GB, amber) | measured Orange 6/9 |
| Qwen3.5-2B-UD-Q4_K_XL | **0.20 GB** | auto-fit, GPU contended by another service | **Featherweight** (< 4 GB, teal) | Orange 6/9 |

The weights did not change. The context did. The harness did. **The machine did.**

The same effect, smaller, on LFM2-350M: **0.42 – 0.51 GB** depending on how it was placed.

## The mechanism

`llama-server` probes free device memory at load time and auto-fits the number of layers it can
place on the GPU — **but only if the user has not set `--n-gpu-layers`.** Set it and the placement
is fixed; if the fixed placement does not fit, the server does not degrade, it **aborts**:

```
W common_fit_params: failed to fit params to free device memory:
                     n_gpu_layers already set by user to 99, abort
E ggml_backend_cuda_buffer_type_alloc_buffer: allocating 96.00 MiB: cudaMalloc failed
```

So the flag produces two opposite failure modes, and both are wrong for a weigh-in:

- **`--ngl 99` on a contended GPU** → the server refuses to start. The entrant is scratched for a
  reason that has nothing to do with the entrant.
- **no flag on a contended GPU** → the server loads, reports a footprint reflecting whatever memory
  happened to be free, and the model is **weighed in at a fraction of its real size.**

The second is the dangerous one. The first announces itself. **The second silently moves a model
down a weight class.**

## Why this is fatal to a naive league

Divisions exist to make comparisons fair — you fight people your own size. If the weigh-in is a
measurement of ambient GPU pressure, then:

1. **The same model fights in different divisions on different days.**
2. **A challenger with a busy machine looks lighter than a defender with a quiet one.** The
   incentive is backwards: it rewards *not* having the hardware to yourself.
3. **Nobody can reproduce anybody's result**, because the result depends on a state that was never
   recorded.
4. **The headline number is unstable.** An 8× spread in footprint dwarfs most of the capability
   differences the league exists to measure.

This is the same error this project has now made four different ways: **a configuration detail
silently becoming a capability result.** The four earlier mechanisms (a grammar file, a token
budget, a context window, missing files on disk) were confounds in the *task*. This one is a
confound in the *measuring instrument* — which is worse, because it corrupts the axis, not one
axis's value.

## The fix

**1. A weigh-in must declare its offload configuration.** A footprint without a placement policy is
not a measurement. The result bundle now records:

```json
"weigh_in": {
  "ngl_requested": null,          // null = auto-fit, a number = forced
  "footprint_gb": 0.20,
  "gpu_free_gb_at_weigh_in": 1.8,
  "placement": "auto-fit, partial offload"
}
```

**2. Division is assigned from a STANDARDISED weigh-in, never from run-time placement.** Where the
model fits fully, that is its weight. Where it does not, the **intrinsic** size (file size plus KV
cache at the declared context) sets the division, and the achieved placement is reported alongside
it.

**3. Publish two numbers, not one.** `intrinsic_size` — what the model *is*. `resident_footprint` —
what it *took*. They are both true, they answer different questions, and a league that reports only
the second is reporting the weather.

**4. Partial offload is its own division, not a loophole.** A model that genuinely runs with most
layers on CPU *is* lighter in VRAM — and slower. That is a legitimate trade, and the biathlon is
where it should pay for itself. It must be **declared**, not discovered.

## What it says about the wider problem

This is why "it runs on my machine" and "it runs on yours" are different claims, and why local
benchmarks do not transfer. A published number that omits the placement policy, the available VRAM
at load, the context window and the token budget is not reproducible — it is a description of one
afternoon.

**The instrument must be as carefully specified as the task.** A league that standardises its tasks
and leaves its scales uncalibrated has standardised the easy half.

## The rule

> **Weigh in with a declared configuration, or do not weigh in at all.**

A footprint taken under ambient conditions is a measurement of the environment. Report it — but
label it as such, and never let it set a division.
