# Control artifacts — files that are in the record because a TEST ran, not because the field ran

**Disclosed rather than deleted.** Two files under `results/` were written by the *first version of the
bind's control*, which ran `run_card.py` whole to watch the gate pass. Passing the gate **starts the work**,
so the control reached the entrant loop and re-attempted two of the eight permanent failures.

## What was written, in commit `06c43c2`

```
Kev-4B-Q4_K_M_..._mt3000.json.attempt2.empty.json          (new)
laya_english_f16_..._mt3000.json                           (MODIFIED: generated 22:04:59Z -> 23:03:23Z,
                                                            secs 2.3 -> 2.6)
laya_english_f16_..._mt3000.json.attempt2.empty.json       (new, 13 lines)
```

**And the message on that same commit said "0 control artifacts left behind."** The diff contradicted the
sentence three lines away from it — which is the whole reason this file exists.

## Why the artifacts are honest and still must be named

**They are honest**: `laya_english_f16` and `Kev-4B` loaded, scored nothing, and produced empty bundles —
**the same failure this field has recorded three times**, and two of the eight entrants that have now failed
every attempt. **They do not change the verdict.**

**They must still be named**, because **a future reader cannot tell a record written by the field from one
written by a test.** That is a provenance question, not a correctness one — and provenance is exactly what
this repository separates evidence on.

**The old bundle content is preserved** as `.attempt2.empty.json`, because `run_card.py` moves an empty
aside before re-attempting. So no measurement was destroyed — it was superseded by a *test's* re-measurement
rather than by the field's, and only the newer `generated`/`secs` reflect the test.

## THE DEFECT, and it is structural rather than a caution

> **A CONTROL FOR A GATE MUST NOT WRITE TO THE RECORD IT CONTROLS.**
> **Testing a REFUSAL is free — the refusal *is* the short circuit.**
> **Testing a PERMISSION is not free, because the permission's only observable effect IS the permitted
> work.** Nobody prices in the cost of the thing being permitted.

**Both agents hit this identically, thirty seconds apart** — one here, one on the Mac-bound side. Independent
reproduction of a defect by two parties is the strongest evidence that it is a property of the **design**,
not of either party's care.

## THE FIX, applied in `run_card.py`

The gate was extracted into `game_contract_gate() -> (ok, detail)`. The control now **reads the decision**
and the caller is the only thing that proceeds, so **testing a permission costs the record nothing** —
verified by fingerprinting every file under `results/` before and after and asserting it is unchanged.

```
ok    clean contract -> gate ALLOWS
ok    testing PERMISSION wrote NOTHING (measured: results/ fingerprint unchanged)
FIRES a NEW violation -> gate REFUSES
ok    the refusal NAMES the offending record
ok    testing REFUSAL wrote NOTHING else
```

Run it: `python3 test_bind_control.py`
