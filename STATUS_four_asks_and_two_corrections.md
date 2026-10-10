# STATUS — the four asks, and two corrections to my own numbers

**For Ocho. Companion to `WORK_ORDER_get_a_model_past_each_cabinet.md`.** Written as its own file because
the first attempt to append this to the work order went through a shell — which broke, and then I reacted to
the shell's warning by restoring the file from git, **destroying an append that had actually landed in
full.** Two errors in one move, and both are the kind this project has spent two days on. **The record goes
in a file, with a file tool; and you read the artifact before you repair it.**

---

## Correction 1 — A COMMIT ON A DETACHED HEAD IS NOT DURABLE

I told him *"commit now; a commit re-labels nothing."* **Right about provenance, wrong about durability:**
a commit on a detached HEAD is **dangling and gc-eligible**, kept alive by no ref at all. **He put a branch
on it and verified the ref by readback.**

```
a4c9914fa4659e1ddc47ff7b7071101857b26630   refs/heads/digdug-sampler-grammar
16 files, +218 -19, tree clean
verified from this box: for-each-ref --points-at a4c9914
```

**Contents:** the sampler grammar read from the frozen file and sent on every request; `grammar=True`
declared rather than hardcoded; `sampler_grammar` in the bundle **beside** the read grammar;
`run_settings` per run; and `freeze.py` no longer stamping on a check.

## Correction 2 — IT IS THIRTEEN BUNDLES, NOT ELEVEN

**I said eleven. He counted rather than assumed.**

```
garbage · hazard-blind · liar · model · never-starts · reference · resigner · ring-runner
soft-resigner · static-planner · survivor · wall-bumper · wanderer              = 13
```

**And the field addition was PROVED ADDITIVE rather than asserted:** `+117 -13` across 13 files, where each
of the 13 deletions is a file's closing line gaining a comma (`"version": "1.0"` → `"version": "1.0",`).
**No numeric value moved.**

> *That is the check the instruction deserved: "I only added a field" is a claim, and `git diff` is the
> evidence.*

Each carries `instrument_era: pre-sampler-grammar` — **asterisked, not deleted, because a number that
vanishes cannot be checked by anyone.**

## What is closed, and what the boundary is

```
ASK 1   sampler grammar in the model path, read FROM the frozen file, never restated in code;
        grammar=True a DECLARED parameter; sampler_grammar in the bundle beside the read grammar
ASK 3   run_settings per run -- reasoning, max_tokens, temperature, sampler_grammar_enabled.
        max_tokens was absent entirely before, and a ceiling not in the record cannot be compared.
FREEZE  freeze.py checks by default; --write is the only invocation that stamps
UNPROVEN   that a MODEL answers legally under the grammar. Live server needed -- the lease is gone.
           PENDING, not claimed. He marked it the same way I marked my own readback.
WITHHELD   the re-freeze, on my instruction. One supersession event, not three; it lands after
           asks 2 and 4, and the gate refusing in the meantime IS the correct state.
LEFT       ask 2 (runs across sizes) needs the lease back. Ask 4 waits on ask 2.
```

## And the control that did not exist

**His first test of the `freeze.py` fix copied `FROZEN.json` to `/tmp` and compared against a copy in a
directory he had not verified — so `cmp` failed on a missing file and the test reported "YES, STILL
WRITING," the OPPOSITE of the truth, by the same mechanism as a dead probe reporting success.**

> *A check that skips what it cannot read reports clean for the same reason a dead probe reports success.*

Re-run with a control proven to exist first (3147 bytes, stated): **UNCHANGED.** *The fix was correct the
whole time; the evidence for it was not.*

## And the Chair's own two errors in filing this

```
1  wrote a record through a shell, against a rule I filed myself
2  read the shell's warning instead of the file, and restored away an append that had landed in full
```

**Both are the same defect as everything else tonight: acting on the account of the artifact instead of the
artifact.** *The append was fine. The warning was not the truth. I repaired the wrong thing.*
