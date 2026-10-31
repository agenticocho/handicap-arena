# FINDING 011 — The card's GPU failure has two modes, and only one of them is cleared by a power cycle

**Date:** 2026-10-08 (the original rule) · **Addendum:** 2026-10-13, measured by Chilly on the subject box
**Correction:** 2026-10-13, later the same day — the cure is **615.71.09**, not 580 (see "the cure" below)
**Status:** measured · **Subject:** the arena's standing card — the RTX 3060 Ti on Chilly (`chilly`, tailnet address withheld)
**Provenance:** the original rule is Jarvis's, adopted 2026-10-08. The addendum, the discriminating
experiments, the correction and the capture rule are Chilly's, sent over the chair link on 2026-10-13 and
recorded here in substance. Neither part touches this machine.

---

## The original rule (2026-10-08)

The box fell over with:

```
nvidia-smi: No devices were found
RmInitAdapter failed
GSP failing to halt at progress 0xff
```

The rule adopted then, and the whole of it: **clear it with a POWER CYCLE, not a reboot.**

**That rule is correct for what it was measured on, and it is incomplete.** Read alone it says "always
power-cycle first", which is exactly the reading that sent today's failure down the wrong path.

## The addendum (2026-10-13) — the failure recurred, and this time the distinguishing tests were run

The box went down the same way. The card was otherwise healthy and the failure was reproducible on
demand, so the discriminating experiments could finally be run:

| experiment | configuration | result |
|---|---|---|
| workaround | 595.99.02 · GSP **disabled** (`NVreg_EnableGpuFirmware=0`) | card works, CUDA verified (`cuInit(0)=0`, 1 device) |
| **EXP-1** | 595.99.02 · GSP **enabled** — *proprietary* module | **FAIL** — same signature as the `-open` module |
| **EXP-2** | 580.178.04 · GSP enabled | PASS |
| **EXP-3** | **615.71.09 · GSP enabled — no workaround file** | **PASS — and this is the configuration the box now runs** |

### The cure — corrected the same day: 615.71.09, not 580

The first version of this addendum named **580** as "the cure". That was drawn from **one sample of the
59x series while a second sample was available and unrun**, and EXP-3 supersedes it. EXP-3's decisive
fields, captured as the first command after boot:

```
driver  615.71.09 (open) · GSP ENABLED · no workaround file
GSP Firmware Version : 615.71.09
CUDA UMD Version     : 13.4          (was 13.0 on 580)
bad register read    : 0
CUDA verified        : cuInit(0)=0, 1 device
```

EXP-2 (580.178.04, open, GSP enabled) passed with the same shape of evidence — `GSP Firmware Version
580.178.04`, `CUDA Version 13.0`, `bad register read 0`.

**Same card, same session, minutes apart: GSP fails to come up on 595.99.02 and comes up cleanly on both
the branch below it (580) and the branch above it (615).** EXP-1 killed the first hypothesis — that the
`-open` module's GSP implementation was the culprit: the proprietary module fails identically, at the same
two stages (booter `0x40`, then GSP halt `0x65`).

**Corrected finding: 595.99.02 is a bad RELEASE for this card — not a defective modern line, and not the
hardware.** The box now runs **615.71.09 with GSP enabled and no `NVreg_EnableGpuFirmware=0` override** — a
*newer* driver than the one that broke it, strictly better than where the day started. The interim
statement *"the GSP engine is unresponsive to the driver"* was an **overstatement**: the engine is fine.

**Record detail:** `/proc/driver/nvidia/params` reports `EnableGpuFirmware: 18` when the parameter is
**unset** — the driver's own default — against `0` for the workaround. It is an override of a non-zero
default, not a boolean.

**Unmeasured, and deliberately left so:** whether the **open** kernel module honours
`NVreg_EnableGpuFirmware=0`. It went moot once 615-open ran GSP. Do not treat either answer as
established — and note that above the 595 line every Ubuntu branch (610 → 615 → 615-open) is
**open-only**, so there is no proprietary fallback up there.

## The discriminator — the operational part

The original rule is about the **GSP hang**. The 595 failure is the **driver defect**, and it behaves
oppositely:

| | driver defect (595.99.02) | GSP hang (the 2026-10-08 case) |
|---|---|---|
| warm reboots help? | **no** — reproduced across reboots | no |
| full power cycle helps? | **no** — a power cycle was tried and graphics stayed funky | **yes** |
| what clears it | a driver change — **moving off 595.99.02** (580 and 615 both work) | a power cycle |

> **If a power cycle does not clear it, it is not a hang — look at the driver.**

This is the sentence the original rule was missing. A rule read as "always power-cycle first" spends a
power cycle proving nothing on the driver case, and then the wrong component gets blamed.

## The capture rule that made this diagnosable at all

The failure emits `gpuHandleSanityCheckRegReadError_GM107` at ~**102,000 journal lines/second** (1.5M
lines in one boot) under a 1G `SystemMaxUse`, so journald vacuums as it goes. **Boots -3 and -2 contain
ZERO NVRM lines — the failure ate the record of its own cause.**

**Capture as the FIRST command after boot, into a file, never into the journal.** (A `gsp-capture.service`
now makes that automatic.)

**Generalisation, which is why this belongs in the FINDINGS series:** an instrument whose output volume
can displace its own record is not an instrument. Anything that only becomes diagnosable if it is
captured before something else runs must be captured by construction, not by remembering.

## The unit's own deployment error — a live rule, not history

**Supplied raw by Chilly on 2026-10-14 and absorbed here rather than kept as a separate finding.** It
is a rule about the units this project runs *today*, so it belongs beside the operational part rather
than in an annex:

> The first freeze's unit was launched with `ManagedOOMPreference=omit`, which removes it from oomd's
> candidate set — **protecting the measurement at the cost of the machine**. An earlier run without it
> was OOM-killed at 33 G and the box survived. **On a live desktop that property must not be set**: the
> box wins over the run, always. The corrected unit carries no preference, `MemoryHigh=28G`/`MemoryMax=32G`
> (a real ~28 GiB reserve rather than a ceiling above the peak), `MemorySwapMax=2G`, and `OOMPolicy=stop`.

**Why this is the deployable half:** the failure it describes is not the card's — it is the measurement's
own scaffolding deciding that the run outranks the desk it runs on. A run that survives by killing the
machine is not more robust; it is less honest about what it costs. **`omit` is available, it worked, and
it is the wrong default on a live desktop** — which is exactly the shape of setting that gets copied
forward because it was effective once.

## What did not break — the constructive half

**Failures get recorded and successes do not, so the resumability evidence is stated explicitly here.**
Also supplied raw by Chilly, 2026-10-14:

> 19 of 38 entrants measured across two freezes, **all bundles intact, zero corrupt, zero partial, and
> 114/114 item records carrying `secs` and `gen_tokens`.** A resumable runner turns a crash into a
> shorter run rather than a lost one — and the per-item clock survived a hard power-off because it was
> written into the bundle rather than held in the process.

**The design rule underneath it:** anything the record needs after a hard stop must be written into the
bundle as it is produced, not accumulated in the process and flushed at the end. Same rule as the
capture rule above, applied to the runner instead of the diagnostics — **the record survives the crash
because it was never only in memory.**

## The correction that is the real lesson

Two corrections landed here, and they are the same defect in different costumes:

1. **A single sample read as a series.** One version of the 59x line was tested and generalised to "the
   modern driver line is defective on this card". The branch immediately above it boots GSP cleanly on
   the same hardware, minutes later, same box.
2. **A gap read as a choice between explanations.** (The 2026-10-08 swap-thrash conclusion.)

In both cases **the honest statement was narrower than the confident one, and in both the disambiguating
look was cheap and unrun.** Same shape again as a proof script that extracts by hard-coded line range and
prints a verdict from an extract that had failed — *a confident verdict from an instrument that had not
actually run.*

## What this does NOT establish

**This also stands as counter-evidence to any clean bill of health.** This card's GSP **can hang on 580
too**, mid-run, with the same text — and **two clean boots on 615 are not a clearance either**. So "the
card is fine" is true of *today's* failure and is **not a general clearance**: the two modes coexist on
the same driver line, and a clean bring-up clears only one of them. **AND THE CORRELATION IS LEFT STANDING, LABELLED AS A CORRELATION.** 2 of 2 freezes occurred with the
arena running — each entrant spawns a `llama-server`, loads a model, exits, and the next repeats it, so
~19 CUDA context create/teardown cycles land on firmware that is already marginal. **That is a hypothesis
with n=2 and it is NOT a finding** — better met as a known pattern than as a surprise, and not to be
promoted by repetition.

## Provenance — what came from where

**Three sections above were supplied raw by Chilly on 2026-10-14 from `011_two_freezes_gpu_firmware.md`,
and absorbed here rather than landed as a separate finding 024:** the unit deployment error (a live rule),
the resumability evidence, and the n=2 correlation. **They are quoted rather than paraphrased** because
the originating copies come out of `FINDINGS/` in the same reconcile that lands this text, and a
paraphrase would be the only surviving record of them.

## Provenance and correction (recorded against both names)

Chilly characterised the interim failure as *"the GSP engine is unresponsive to the driver — it is not
merely that the firmware was rejected."* **That was an overstatement and EXP-2 falsified it** — the GSP
engine on this card responds correctly under 580. It is recorded against his name in the same way the
swap-thrash conclusion was recorded against both of ours, and the "580 is the cure" claim is corrected
in place above rather than quietly dropped.

## How to apply

1. Card down with `No devices were found` / `RmInitAdapter failed` → try the **power cycle** first.
2. Power cycle does **not** clear it → stop power-cycling; it is the **driver path**. Move off the
   suspected release to a known-good one (615.71.09 — GSP on, no override — and 580.178.04 here) before
   suspecting hardware.
3. Always **capture as the first command after boot**, into a file.
