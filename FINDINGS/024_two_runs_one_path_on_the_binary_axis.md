# FINDING 024 — TWO RUNS, ONE PATH, ON THE BINARY AXIS: THE NAME CARRIES FEWER INSTRUMENTS THAN THE RECORD DOES, AND THE SECOND RUN DELETES THE FIRST

**Card `t_33042da0` changed the driver so the binary is selectable and recorded (`PREREG_sokoban_instrument3.md`).
Three things were measured on the way in and are NOT fixed by it. Every number below is from a run on this
box, and every one of them is reproducible from the commands named.**

---

## 1. THE SECOND RUN ON A DIFFERENT BINARY OVERWRITES THE FIRST RUN'S RECORD — AND A FIELD CANNOT FIX IT

The card was right that a record must say which binary produced it, and right that the fix wanted a
preregistration. **It is wrong that the record did not say it** (§2). What the record cannot do is survive the
second run:

```
two runs of the PRE-IMAGE driver, same (entrant, level), different binaries:

  run 1   Ternary-Bonsai-2-2B-Q2_0  +  prism fork b10777    ->  loaded false   (rc=-6, ggml_abort)
  run 2   Ternary-Bonsai-2-2B-Q2_0  +  mainline b10931      ->  loaded true    (64 tokens of salad/turn)

  artifacts written: 2 runs, 1 path   probes/SOKOBAN_Ternary-Bonsai-2-2B-Q2_0_01_one_push.json
  mtime advanced: run 1 -> run 2, and the file now records ONLY run 2.  RUN 1'S RECORD IS GONE.
  logs:            logs/SOKOBAN_Ternary-Bonsai-2-2B-Q2_0_01_one_push_new_rea-off.log says nothing about the
                   binary either, so run 1's log was overwritten by run 2's as well -- measured: the file
                   holds run 3's `ggml_abort` backtrace, i.e. the fork's, where the mainline run's log was.
```

**The name carries the entrant, the level, the legend and the reasoning arm — and not the instrument.** The
legend and the reasoning arm were put into the LOG name for exactly this reason (the comment at
`sokoban_run.py`'s log path says so: *"an A/B over `--reasoning` would have had arm A's raw log OVERWRITTEN BY
arm B's"*), and **the artifact name never got the same treatment for any of the three.** So this is `FINDING
020` — *"two runs, one path"* — recurring on the axis the last fix did not cover.

**AND NO FIELD CLOSES IT.** `server_argv`, `server_binary_digest` and the reasoning arm are all inside the
file that the second run replaces. A record that is overwritten cannot carry anything. **The disposition is a
naming question, and the naming convention is published** (`probes/SOKOBAN_<entrant>_<level>.json` is cited
in `GAMES.md` and in `SOKOBAN_CONFORMANCE_PACKAGE.md`'s census), so it is **proposed and not landed**:

```
FLIP, one line:  refuse to write an artifact whose existing record carries a different
                 `server_binary_digest` than this run's, with a documented one-token override.
COST OF FLIPPING   the per-cell artifact name or the write becomes instrument-dependent, and every
                   citation of a `--llama-server` cell must carry which one.
COST OF NOT        a second run on a different binary destroys the first run's record, silently,
                   and the destroyed record is the one the card exists to make legible.
```

---

## 2. THE INSTRUMENT NOTE BESIDE THE BONSAI ARTIFACTS ASSERTS A FIELD THAT ITS OWN ARTIFACT CARRIES

`probes/SOKOBAN_Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0_01_one_push.INSTRUMENT-NOTE.md` (and its `02` sibling),
committed at `dc1375b`, says:

> *"NOT RECORDED BY THE ARTIFACT : the record contains no `server_argv` field, so without this note the
> artifact is indistinguishable from one the default binary produced."*

**The artifact it annotates records the opposite, in the field the note names:**

```
probes/SOKOBAN_Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0_01_one_push.json   config.server_argv[0]
  = /home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server        (the PRISM FORK)
probes/SOKOBAN_Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0_02_two_boxes.json  config.server_argv[0]
  = the same path
```

`config.server_argv` has been written by `sokoban_run.py` since **`2e4e3de` (2026-10-10, FINDING 022)** — six
days before the Bonsai run — and it recorded the fork because the in-memory override moved the very constant
the field is built from. **So the two Bonsai artifacts were attributable all along, and the note is the only
carrier that says otherwise.** The note's closing line — *"READ THE INSTRUMENT NOTE BESIDE EACH ARTIFACT
BEFORE CITING EITHER"* — makes a false sentence the first thing a careful reader is told.

**THE ARTIFACT WINS** (`PRECEDENCE.md`: the artifact over a statement about it; the carrier over the claim).
**No record is rewritten** — the note and the artifact are both dated, and the loser here is still evidence:
it is a true measurement of the operator's BELIEF at the time, and that belief is why the driver had no flag.
The permanent fix is the flag, and the flag now exists.

---

## 3. A LOAD REFUSAL BY A BINARY THAT CANNOT READ THE FILE IS REPORTED AS A GPU-TENANCY CONDITION

`holder_sentence()` (RULING 82) is appended to **every** load failure. On a CPU-only run (`-ngl 0`) of a file
whose tensors the binary cannot parse, the record reads:

```
server exited rc=1.
AND THE CARD IS HELD BY: pid 2418 (134 MiB) holding the card with NO LEASE TRACED TO IT; pid 845036
(5874 MiB) ...; pid 852656 (1138 MiB) ...  Tenants total 7146 MiB.
```

and the actual cause is two lines further down the log that only the log has:

```
E gguf_init_from_reader: tensor 'token_embd.weight' has invalid ggml type 142. should be in [0, 43)
```

**RULING 82's sentence was ratified for a real cause** — five failed loads whose real cause was a live seat
lease, and one sentence being the difference between an infrastructure condition and a model failure. **It is
not wrong; it is unconditional.** Two different conditions now print the same sentence, and the one that
prints it for a tensor-type refusal points the reader at the wrong subsystem. **Reported, not changed:** the
sentence belongs to another ruling's carrier and narrowing it is not this card's to do. The one-line shape, if
the Chair wants it: append the holder sentence only when `srv.returncode` is not a parse/load refusal, and say
which condition is being reported.

**WHAT THE CHANGE DOES DO HERE:** the failure record now carries `server_binary_digest` and
`server_binary_source`, so at least the record says *which binary* could not read the file — measured on the
4B: `server_binary_digest 0d5393431782ddf8`, `server_binary_source "no selector given: the module constant
LLAMA"`.

---

## 4. WHAT THIS FINDING IS NOT

It is not a claim that the Bonsai artifacts are wrong: their numbers stand, and §2 strengthens them by
showing what they already carried. It is not a claim that a fork is the right instrument: **the prism fork
aborts (`rc=-6`) on the 2B file and the default binary refuses the 4B file**, so neither binary is a drop-in
for the family, which is the argument for recording the instrument rather than for choosing one. And it is
not a criticism of the note's author: the note is the only reason a reader knows the fork was used at all —
it is simply the wrong place for the fact, and the field it says does not exist does.
