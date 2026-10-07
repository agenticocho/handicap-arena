# These are RESULT BUNDLES, but they are not the field.

**41 bundles, card v3 first pass, written 2026-10-07 ~13:16–13:35 PST.**

They were produced **before** `arena.py` stored the model's raw output per item, so they carry
`score`/`reason`/`truncated` and **no `raw`** — which means, per `FINDINGS/007`, that **no verdict
they produce can be audited.** A model failure and a scoring bug are indistinguishable in them and
will stay that way. **They cannot ground a criterion verdict.**

They are kept rather than deleted because they are a legitimate *labelled first pass*, and because
they are evidence that the field ran.

**THE TRAP, stated because it is the kind this repo keeps finding.** They live in a subdirectory of
`results/` — and `results/` is where result bundles live. So:

* `results/*cardv3*.json` (non-recursive) — **correct**, counts only the live run.
* `results/**/*cardv3*.json` (recursive) — **counts these 41 as completed entrants.**

A recursive glob therefore inflates the completed count and **hides a short run** — the exact failure
the liveness check exists to catch, introduced by the quarantine that was supposed to make the field
*more* honest. It is the same shape as a `.log` in `results/`: a file a reader counts as an entrant.

**If you are counting the v3 field: exclude this directory, and say in your output that you did.**
