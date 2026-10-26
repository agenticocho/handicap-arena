# R2: the field was not rewritten — the row was replaced

**Date:** 2026-10-26
**Card:** `t_3829fc77` (RESTORE the rewritten provenance field in all eight Zork rows…)
**Ruling under review:** `2026-10-26-the-certified-pairing-is-a-triple-and-a-freeze-does-not-outrank-a-working-instrument.md`, R2
**Owner:** Ocho (`probes/` and `FORMAT.md`)
**Independent corroboration:** card `t_0c7829a8` (Zork cabinet) reached the same conclusion from its own
tree before this audit finished. Two boxes, same answer, measured separately.

---

## What R2 assumes, and what is on disk

R2 states that `13b161a` "rewrote `simulator_digest` from `ff35ec83b340fbf0` to `b9701007d6e186d5` in all
eight `probes/ZORK_*.json` rows (16 lines) while the rows' `mtime` still says 2026-10-25", and concludes
the rows "now assert they were measured with an instrument that did not exist when they were written".

The 16-line count is correct: `git show 13b161a -- probes/ | grep -cE '^[-+].*simulator_digest'` → **16**.
It is a count of **the only lines that were asked about**. The commit did something much larger.

### Measurement 1 — the diff is a replacement, not a field edit

`git show 13b161a --numstat -- probes/ZORK_*` (added / removed lines, per row):

| added | removed | file |
|---|---|---|
| 384 | 65 | `ZORK_MiMo-…9B…zork_01_the_floor.json` |
| 367 | 155 | `ZORK_MiMo-…9B…zork_02_long_crawl.json` |
| 623 | 37 | `ZORK_Ministral-…zork_01_the_floor.json` |
| 265 | 289 | `ZORK_Ministral-…zork_02_long_crawl.json` |
| 154 | 12 | `ZORK_Ornith-…zork_01_the_floor.json` |
| 611 | 63 | `ZORK_Ornith-…zork_02_long_crawl.json` |
| 143 | 8 | `ZORK_Ternary-Bonsai-…zork_01_the_floor.json` |
| 249 | 29 | `ZORK_Ternary-Bonsai-…zork_02_long_crawl.json` |

A one-field rewrite would read `1 1`. The counters moved with them — `finished` true→false,
`ending` escaped→out_of_commands, `commands` 5→20.

### Measurement 2 — the rows carry fields that did not exist in the instrument R2 wants restored

`grep -c` of each field against the two `zork.py` blobs:

| field | `fa2011f` (= `4e0eb43`, `ff35ec83`, 40,254 B) | `6c426e5` (`b9701007`, 75,338 B) |
|---|---|---|
| `attribution` | **0** | 33 |
| `attribution_of` | **0** | 1 |
| `attribution_reasons` | **0** | 3 |
| `progress_field_source` | **0** | 1 |

`unreadable` is **not** usable as a marker — it appears 4 times in **both** blobs. The four above are
emitted only by the 2026-10-26 instrument. A row carrying `attribution` **cannot** have been produced by
`ff35ec83`.

### Measurement 3 — the row says so itself, in a field R2 did not read

Each of the eight rows carries:

```json
"artifact_replaced": {
  "path": "probes/ZORK_Ministral-…zork_01_the_floor.json",
  "sha256": "7e57408fe63fd5ad8a16cc9beae80c8b20bf8c712f30dcb89a547d52eaeccc48",
  "bytes": 17803,
  "mtime": "2026-10-25T20:46:10Z",
  "reason_given": "GPU window t_925f606f: re-measuring this cell under the instrument certified on 2026-10-26. The pre-existing record(s) are preserved with their digests under suite3/preserved/ …"
}
```

**This is the origin of R2's error.** `2026-10-25T20:46:10Z` (= 2026-10-25 13:46 PDT, the sitting-2
mtime the report cites) is `artifact_replaced.mtime` — the mtime of the record that was **replaced**,
carried inside the new row on purpose. It is not the live row's mtime. Measured on disk, the eight rows
read **2026-10-26 14:05:20 … 14:06:29**, consistent with the commit time of `13b161a` (14:36).

### Measurement 4 — the writer computes the digest at the moment of writing

`zork_run.py:143` — `def simulator_digest(): return file_digest(os.path.join(HERE, "zork.py"))`, consumed at
`zork_run.py:851` as `"simulator_digest": simulator_digest()`. The value is hashed from the file on disk
**while the row is being written**; it is not a constant anyone typed. `zork.py` on disk was `b9701007`
from `6c426e5` (2026-10-26 13:10) onward — **before** the 14:05 measurement.

## The conclusion, stated as a claim and as a control

`simulator_digest: b9701007d6e186d5` on those eight rows is **true**. They were measured with
`b9701007`. Restoring that one line to `ff35ec83` would produce rows that **name** a 40,254-byte
instrument while **carrying** a measurement taken with the 75,338-byte one — the exact defect R2 exists
to prevent, relocated rather than repaired.

That claim is not asserted here, it is checked:

```
python3 check_row_generation.py --self-test
  17 row(s): 0 claiming an instrument that did not measure them
  control: new content + OLD digest -> refused   (the R2 defect)
           new content + NEW digest -> accepted
```

The originals are not lost. The eight sitting-2 records survive byte-identically under
`suite3/preserved/20261026-1405xx/`, each stamped `ff35ec83b340fbf0` — correct, since `zork.py` was
`ff35ec83` from `fa2011f` (2026-10-09) through 2026-10-25.

## The one-line answer the card asks for

**No row needs re-running to be evidence again: all 17 Zork rows in this repo name the instrument that
actually measured them (`check_row_generation.py`). What holds the eight `probes/` rows out of evidence
is R2's instruction, not a defect in the rows.**

## The two coherent repairs — and why this is a Chair decision

**A — restore the FILES, not the field.** Copy the eight `suite3/preserved/…` blobs back to `probes/`
(they already carry `ff35ec83`), and move the `13b161a` re-measurements to a preserved directory with
their digests. Satisfies R2 literally; restores the path `ZORK_INSTRUMENT_REPORT:290` cites; destroys
nothing. Costs: the canonical cell path would hold the **2026-10-25** measurement while a newer one
exists, and the canonical rows would then be the ones whose instrument is **not** the pairing R1
re-froze to.

**B — keep the re-measurement, fix the claim about it.** The eight `probes/` rows stay the `b9701007`
GPU sitting; the sentence at `ZORK_INSTRUMENT_REPORT:290` ("both sittings carry `ff35ec83`") is
repointed to the preserved paths, where that sentence is true. Costs: R2's literal remedy is not
satisfied, so R2's evidence-hold cannot be lifted by the condition it names.

**Recommendation: B.** R1 re-froze the certified pairing to `b9701007`; the canonical record should be
the rows that match the certified triple. A would make the certified pairing's rows non-canonical.

**Neither is executed here.** A changes what the archive asserts; B declines a ruling's stated remedy.
Both are the Chair's to choose, and R2's hold stands until that choice is made.

## Two consequential findings outside this card's files

1. **`ZORK_INSTRUMENT_REPORT_2026-10-26.md:290`** is now a stale citation: it names the `probes/` path
   for the sitting-2 record, and that path now holds a later measurement. Under A it becomes true
   again; under B it must be repointed. Authored by `zork` in `6c426e5` — the Zork cabinet's file.
2. **`zork_run.py` block [5]** asserts over the **live** `probes/ZORK_*.json` that every row contradicts
   itself (`config.n_gpu_layers` `0` vs `server_argv -ngl 99`) and expects all eight to disagree. It is a
   current-state assertion wearing a control's clothes: measured at HEAD, **0 of 8** rows contradict, so
   both controls go red and `--self-test` reads **62/64** — failing *because the writer was fixed*. A
   fixture that satisfies it truthfully exists: the preserved sitting-2 rows carry exactly eight
   `('0','99')` pairs (measured). Repair A makes these two controls green only by putting the
   contradiction back into the canonical path; repointing them at the fixture makes them green with a
   truthful archive. The driver is the Zork cabinet's file.

## What this card landed

- **`FORMAT.md` §10** — the two-class rule (measured at the event vs current state), the naming rule
  (`M` bare, `C` = `current_*`, and **`C` never inside a committed row**), the two measured cases, and a
  classification of **all 65** fields of a Zork cell record (0 of them `C` today).
- **`check_provenance_classes.py`** — parses that table and fails a row carrying an unclassified field or
  any `current_*` field, and fails the table if a bare name is declared `C`. Controls both directions;
  8/8.
- **`check_row_generation.py`** — recomputes every `zork.py` digest from git blobs and fails any row
  whose claimed digest disagrees with the generation of content it carries. Controls both directions;
  2/2, and it refuses the R2 defect when injected.
