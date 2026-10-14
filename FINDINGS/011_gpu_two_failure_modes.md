# FINDING 011 — The card's GPU failure has two modes, and only one of them is cleared by a power cycle

**Date:** 2026-10-08 (the original rule) · **Addendum:** 2026-10-13, measured by Chilly on the subject box
**Status:** measured · **Subject:** the arena's standing card — the RTX 3060 Ti on Chilly (`chilly`, 100.87.70.89)
**Provenance:** the original rule is Jarvis's, adopted 2026-10-08. The addendum, the discriminating
experiments and the capture rule are Chilly's, sent over the chair link on 2026-10-13 and recorded here
verbatim in substance. Neither part touches this machine.

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
| **EXP-2** | **580.178.04 · GSP enabled** | **PASS** |

EXP-2's decisive fields, captured as the first command after boot:

```
driver       580.178.04 (open), GSP ENABLED, no no-gsp file present
GSP Firmware Version : 580.178.04        <- GSP running
GPU Firmware         : 580.178.04
nvidia-smi           : CUDA Version 13.0 · 9 MiB / 8192 MiB · card1 + renderD128
bad register read    : 0
```

**Same card, same session, minutes apart: GSP fails to come up on 595.99.02 and comes up cleanly on
580.178.04.** So for this failure the defect is in the *driver's* GSP path, not the card.

EXP-1 killed the first hypothesis — that the `-open` module's GSP implementation was the culprit. The
proprietary module fails identically, at the same two stages (booter `0x40`, then GSP halt `0x65`). The
fault is 595.99.02's GSP path *in general*.

**Record detail:** `/proc/driver/nvidia/params` reports `EnableGpuFirmware: 18` when the parameter is
**unset** — the driver's own default — against `0` for the workaround. It is an override of a non-zero
default, not a boolean.

## The discriminator — the operational part

The original rule is about the **GSP hang**. The 595 failure is the **driver defect**, and it behaves
oppositely:

| | driver defect (595.99.02) | GSP hang (the 2026-10-08 case) |
|---|---|---|
| warm reboots help? | **no** — reproduced across reboots | no |
| full power cycle helps? | **no** — a power cycle was tried and graphics stayed funky | **yes** |
| what clears it | a driver change (580) | a power cycle |

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

## What this does NOT establish

**`FINDINGS/011` also stands as counter-evidence to any clean bill of health.** This card's GSP **can
hang on 580 too**, mid-run, with the same text. So "the card is fine" is true of *today's* failure and is
**not a general clearance** — the two modes coexist on the same driver, and a clean bring-up clears only
one of them.

## Provenance and correction

Chilly characterised the interim failure as *"the GSP engine is unresponsive to the driver — it is not
merely that the firmware was rejected."* **That was an overstatement and EXP-2 falsifies it** — the GSP
engine on this card responds correctly under 580. Chilly records the correction against his name in the
same way the swap-thrash conclusion was recorded against both of ours. **The honest statement is
narrower:** *the GSP path in 595.99.02 does not bring the GSP up on this card.* Nothing more.

Same defect class as a fix whose verifier was not re-run: **an inferred mechanism from a failure sequence,
while the distinguishing test was still unrun.**

## How to apply

1. Card down with `No devices were found` / `RmInitAdapter failed` → try the **power cycle** first.
2. Power cycle does **not** clear it → stop power-cycling; it is the **driver path**. Check the driver
   version against a known-good one (580.178.04 here) before suspecting hardware.
3. Always **capture as the first command after boot**, into a file.
