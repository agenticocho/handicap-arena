# DIG DUG — TIER 3 CABINET

Search on a grid that the search itself changes. **Format A: the model is the player.**

Read `DIGDUG_REPORT.md` first. Read `DIGDUG_PROSE_TRAPS.md` for the section the tier demanded —
**what I would have got wrong if I had trusted the prose** — measured, not argued.

---

## Run it

```bash
cd digdug

python3 digdug.py --self-test            # 100 controls            -> exit 0
python3 digdug_solve.py --prove          # optima + destruction proofs
python3 digdug_run.py run-all --reasoning off --out results   # 12 code entrants
python3 digdug_run.py run model --reasoning off --out results # the model entrant
python3 digdug_run.py verify --out results   # replays every bundle from its own record
python3 test_digdug.py results               # the side script, 626 checks
python3 prose_check.py                       # the second implementation (section 4F)
```

Everything is stdlib. No network, no pip, no weights. `results/` holds 13 bundles; delete them and
re-run to reproduce.

### The order matters

`freeze.py` must run before `digdug_run.py`, and the runner **refuses** otherwise (exit 6). Any edit
to a normative file — `digdug.py`, `digdug_reader.py`, `digdug_run.py`, `CONTRACT_DIGDUG.md`,
`tasks/`, `levels/` — invalidates the freeze: re-freeze, then re-run the field.

```bash
python3 freeze.py            # writes FROZEN.json: contract digest, per-file digests, 26 decisions
python3 freeze.py --check    # verifies the tree still matches; refuses a normative file added later
```

## Files

| file | what it is |
|---|---|
| `CONTRACT_DIGDUG.md` | the `step()`/`turn()` contract I wrote from the 91-word paragraph, 26 marked decisions |
| `FROZEN.json` | the freeze: digests, decision register, abstention token list, timestamp |
| `digdug.py` | simulator + both facet functions + 100 controls |
| `digdug_reader.py` | **the one reader of record** — answer shape, frozen abstention list |
| `digdug_solve.py` | complete search; proves optima, counts distinct optimal lines, proves the destruction claims |
| `digdug_run.py` | runner, scorer, bundle writer, 13 entrants, 7 exit codes |
| `test_digdug.py` | the side script: replays the records, checks the claims about them |
| `alt_reading.py` | a **second, independent implementation** of the same paragraph |
| `prose_check.py` | cross-checks the two, then attributes every divergence to one clause |
| `DIGDUG_REPORT.md` | report sections 1–6 |
| `DIGDUG_PROSE_TRAPS.md` | **section 4F** |
| `levels/`, `tasks/`, `results/` | the level set, the item set, the records |

## Exit codes

| code | meaning |
|---|---|
| 0 | scored |
| 1 | **instrument not proven** — reserved; no entrant's run can return it, asserted by executing them |
| 2 | error: zero measured (no readable answer, or nothing scored) |
| 3 | usage |
| 4 | entrant never started (the holder is named, or the probe that found nobody) |
| 5 | record not written |
| 6 | not frozen |

## What this host cannot do

There is no GPU, no `llama-server` and no `.gguf` here. `run model` therefore exits 4 with
`weights.sha256: null` **and a written reason**, and the declared GPU block is `null` with the probe
that found nothing — never `0.00`, never `"none"`. Every number in the report is an instrument
number, not a model number.
