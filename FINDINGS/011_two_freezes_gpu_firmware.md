# FINDING 011 — TWO HARD FREEZES IN ONE SESSION: GPU GSP FIRMWARE, NOT MEMORY

**Date:** 2026-10-08. **Box:** AMD Ryzen 5 5600 (12 logical), 60.7 GiB RAM, RTX 3060 Ti, driver 580.178.04.

---

## WHAT HAPPENED

Two freezes during an overnight arena run. Both required a hard reboot. Both were diagnosed the same way,
and **the first diagnosis on this box was WRONG** — recorded here so it is not repeated.

```
freeze #1   16:55:16   v5 run live at [20/46] Spark-X2.5-4B-Q5_K_S
freeze #2   17:18:44   v5 run live, 1 entrant completed at 17:14:55
```

**THE CAUSE IS THE GPU'S GSP FIRMWARE HANGING.** Verbatim, from the boot AFTER the first warm reboot:

```
NVRM: gpuWaitForGfwBootComplete_TU102: GSP failed to halt with GFW_BOOT: (progress 0xff)
NVRM: kgspWaitForGfwBootOk_TU102: failed to wait for GFW boot complete: 0x65 VBIOS version 94.04.6B.00.A0
NVRM: kgspWaitForGfwBootOk_TU102: (the GPU may be in a bad state and may need to be reset)
NVRM: RmInitAdapter: Cannot initialize GSP firmware RM
NVRM: GPU 0000:2b:00.0: RmInitAdapter failed! (0x62:0x65:2028)
```

6,372,131 NVRM/GSP lines in one boot; `nvidia-smi` reporting no devices.

## THE FIX IS A POWER CYCLE, NOT A REBOOT

**A warm reboot cannot reset device firmware — the PCIe slot stays energised and the hung GSP survives
it.** Two hard reboots failed to clear it. **One full power cycle fixed it.** Anything that looks like a
GPU wedge on this box should go straight to a power cycle rather than a second reboot.

## THE DIAGNOSTIC ERROR, WHICH IS THE REUSABLE PART

**A freeze leaves its evidence in the NEXT boot, not in the boot that froze.** The freezing boot's journal
simply STOPS mid-line: no OOM, no panic, no NVRM line, nothing. A grep of that boot for `NVRM|Xid|oom`
returns **zero hits**, and the honest-looking conclusion — "the cause is unrecorded" — is wrong about a
cause that is fully recorded one boot later.

**AND THE BOOT INDICES MOVE.** `journalctl -b -1` is a *different boot* ten minutes later, because another
boot has been added. Re-run `journalctl --list-boots` before every look and quote the **boot ID**, not the
offset. This is the same defect as a line number: the coordinate resolved to different content on the two
reads, and the disagreement was read as an absence.

**And the first hypothesis was wrong in a way worth naming — and it was wrong for BOTH of us, in the same
shape, which is why it is recorded against both names.** With no OOM and no error in the freezing boot, the
freeze was attributed to **swap thrashing**. The reasoning offered was *"the signature of pressure that
slows a box to a halt rather than one that trips a limit"* — and it was stated with confidence, by both
parties, on the strength of an absence.

> **THE RULE, AND IT IS THE HEADLINE OF THIS SECTION:**
> **A firmware hang produces no record, and so does a thrash. TWO EXPLANATIONS THAT FIT THE SAME ABSENCE
> MEANS THE ABSENCE DOES NOT CHOOSE BETWEEN THEM.**
> **An absence is not evidence for the explanation that happens to fit it.**

**The tell that should have stopped it, available at the time and not used:** the observation — *"no OOM
record, no kernel error, journal simply stops"* — was treated as a **measurement** when it was only a
**gap**. A gap is compatible with every cause that leaves no trace, and there are several. Picking the one
that fit and reporting it as the signature is **a conclusion wearing the clothes of a reading.**

**This is the favourable-lie shape arriving through an ABSENCE instead of through a number** — the same
family as a value quoted over a set not named, or a count read as an inventory. It is harder to catch here,
because there is nothing to check: the missing number at least has a denominator to argue with, while a
missing record looks like an empty room. **The control is the same in both cases — name what would have
had to be true for a competing explanation, and go and look at the next boot.**

**Both halves are recorded deliberately.** The shared error is the useful part of this finding: two
independent parties, given the same gap, produced the same confident wrong answer, and neither checked the
one place the answer was written.

## THE RUN'S DEPLOYMENT ERROR, SEPARATE FROM THE CAUSE

The first freeze's unit was launched with `ManagedOOMPreference=omit`, which removes it from oomd's
candidate set — **protecting the measurement at the cost of the machine**. An earlier run without it was
OOM-killed at 33 G and the box survived. **On a live desktop that property must not be set**: the box wins
over the run, always. The corrected unit carries no preference, `MemoryHigh=28G`/`MemoryMax=32G` (a real
~28 GiB reserve rather than a ceiling above the peak), `MemorySwapMax=2G`, and `OOMPolicy=stop`.

**AND THE CORRELATION IS LEFT STANDING, LABELLED AS A CORRELATION.** 2 of 2 freezes occurred with the
arena running. A plausible mechanism — each entrant spawns a `llama-server`, loads a model, exits, and the
next repeats it, so ~19 CUDA context create/teardown cycles on firmware that is already marginal — **is a
hypothesis with n=2 and is NOT a finding.** It is recorded so that a third occurrence is recognised as a
pattern rather than met as a surprise.

## WHAT DID NOT BREAK

19 of 38 entrants measured across two freezes, **all bundles intact, zero corrupt, zero partial, and
114/114 item records carrying `secs` and `gen_tokens`.** A resumable runner turns a crash into a shorter
run rather than a lost one — and the per-item clock survived a hard power-off because it was written into
the bundle rather than held in the process.
