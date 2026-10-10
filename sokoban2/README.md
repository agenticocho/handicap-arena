# sokoban2/ — an independent SOKOBAN cabinet (implementation #2)

Written against `SOKOBAN_READ_GRAMMAR.md`, the two frozen levels and the dossier. **It shares no code
with `sokoban/sokoban.py` and was not derived from it.** Where the frozen artifacts do not speak, the
code decides, marks the decision `[G<n>]`, and argues it in `SOKOBAN2_AMBIGUITIES.md`.

Stdlib only. No model played — the box that built this has no GPU and no `llama-server`.

## Files

| file | role |
|---|---|
| `sokoban_reader.py` | **THE ONE READER OF RECORD.** Imported by every other script. Never reimplemented. |
| `sokoban2.py` | the simulator: `step()`, `play()`, `build_prompt()`, `--self-test` |
| `sokoban2_solve.py` | exhaustive BFS solver. Verifies the frozen optima; supplies the dead-end **diagnostic** (never scores) |
| `sokoban2_run.py` | the runner + scorer. Writes the record **before** the success/failure branch |
| `test_sokoban2.py` | side script: replays every bundle from the record and recomputes the result |
| `levels/03_the_corner_waiting.txt` | level 03 — **this file did not exist in the branch**; see `[W1]` |
| `tasks/sokoban_v1.json` | the item set, with the proven optima |
| `results/sokoban_v1_*.json` | the bundles |
| `SOKOBAN2_AMBIGUITIES.md` | **the deliverable** — where the contract does not speak |
| `SOKOBAN2_REPORT.md` | what was built, verified, and measured |

## The frozen contract, as implemented

```
step(state, action) -> (position_after_the_action, word)        TWO values
    word in {moved, pushed, blocked}; position is the PLAYER's, unchanged when blocked
    the reader owns give_up and not_an_action -- they never reach step()
```

Levels 01 and 02 are read **in place** from `sokoban/levels/` (not copied — a copy drifts) and checked
against `sokoban/MANIFEST.txt` by digest (control group `[0]`).

## Run it

```sh
cd sokoban2

python3 sokoban2.py --self-test                      # 78/78 controls, exit 0
python3 sokoban2_solve.py                            # verifies 1 / 12 / 6 by exhaustive BFS
python3 sokoban2_run.py levels                       # the same, as a subcommand
python3 sokoban2_run.py instrument-check --out results --reasoning off
python3 sokoban2_run.py run-all --reasoning off      # the whole field, ONE declared setting
python3 sokoban2_run.py verify                       # replay every bundle from the record
python3 sokoban2_run.py exit-codes                   # the table
```

A model entrant (needs a running llama.cpp server):

```sh
python3 sokoban2_run.py run --entrant model \
        --model-path /path/to/model.gguf \
        --server-url http://127.0.0.1:8080 \
        --reasoning off
```

## Exit codes

| code | meaning |
|---|---|
| 0 | SCORED — measured > 0, harness sound |
| 1 | **INSTRUMENT NOT PROVEN** — self-test / instrument-check / level verification failed |
| 2 | ZERO MEASURED — an ERROR, never a verdict (read-grammar §4) |
| 3 | USAGE — unknown entrant or bad arguments |
| 4 | ENTRANT NEVER STARTED — **counted separately** from played-and-failed |
| 5 | RECORD NOT WRITTEN — a run with no record is not a run |

`1` is reserved. No entrant's run can produce it, and there is a control that says so — because the
failure this table exists for is a CLI that returned 1 for **every** real invocation while its
self-test reported all green.

## The two fields that decide everything

Every bundle carries them at the top, under `declared`, where a reader cannot miss them:

```json
"declared": {
  "reasoning": "off",
  "gpu": {"probe": "nvidia-smi (absent) -> host is Linux x86_64",
          "name": null, "note": "NO ACCELERATOR FOUND by this probe. ..."}
}
```

No accelerator is `null` **with the probe that ran** — never `0.00` and never `"none"`. An unprobed
machine is not a machine with no GPU.

`test_sokoban2.py` refuses a results directory whose bundles do not all declare the same
reasoning and the same GPU: two bundles for one event that declare different instruments are not the
same measurement (darts A11).
