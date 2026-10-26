# AUDIT — the measurement instant: eight rows, one missing field, eight recoverable predecessors

Card `t_3829fc77` (Owner: Ocho). Phase after the Chair withdrew R2 on 2026-10-26.

**What this phase is.** Not a restore. R2's ordered field restore is withdrawn because the premise was
false: `13b161a` re-measured the eight rows rather than rewriting their `simulator_digest`
(`git show 13b161a --numstat -- probes/ZORK_*.json` -> 143/8 .. 623/37 lines per row, and the rows carry
`attribution` / `progress_field_source`, which `zork.py@ff35ec83` cannot emit). `simulator_digest:
b9701007d6e186d5` on those rows is **true**.

**What was actually missing, and is now recorded.** The rows carry no field saying *when* they were
measured. The nearest timestamp available to a reader is `artifact_replaced.mtime` — the *replaced*
record's time, one day earlier — and that is what the Chair read as the row's own. That misreading cost
a ruling; a field ends it.

## 1. The measurement ledger — `provenance/measurement_times.json`

Eight entries, one per committed row, **keyed by the row's sha256** so it cannot drift off its subject.
`measured_at_utc` is the instant the driver closed the row's file (the end of the event), read once from
the filesystem at `2026-10-26T22:47:04.280470Z` (recorded as `observed_at_utc`), and frozen there. It is not in git and is never
recomputed; the ledger is written once and *checked* thereafter.

| row | measured_at_utc | predecessor_mtime_utc | preserved_at_utc | row sha256 |
|---|---|---|---|---|
| `ZORK_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_zork_01_the_floor.json` | `2026-10-26T21:06:01.771337Z` | `2026-10-25T20:47:11Z` | `2026-10-26T21:05:49Z` | `1f5da60554725cc6` |
| `ZORK_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_zork_02_long_crawl.json` | `2026-10-26T21:06:14.127196Z` | `2026-10-25T20:47:27Z` | `2026-10-26T21:06:02Z` | `897beeab372df396` |
| `ZORK_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_zork_01_the_floor.json` | `2026-10-26T21:05:20.290807Z` | `2026-10-25T20:46:10Z` | `2026-10-26T21:05:12Z` | `2a439c43b55857c7` |
| `ZORK_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_zork_02_long_crawl.json` | `2026-10-26T21:05:26.845733Z` | `2026-10-25T20:46:18Z` | `2026-10-26T21:05:21Z` | `754ba9f0bc7ebe67` |
| `ZORK_Ornith-1.5-9B-Q4_K_M_zork_01_the_floor.json` | `2026-10-26T21:05:34.509646Z` | `2026-10-25T20:46:37Z` | `2026-10-26T21:05:27Z` | `2b1d7470f74dd123` |
| `ZORK_Ornith-1.5-9B-Q4_K_M_zork_02_long_crawl.json` | `2026-10-26T21:05:48.134491Z` | `2026-10-25T20:46:56Z` | `2026-10-26T21:05:35Z` | `bd4971a0487f26a3` |
| `ZORK_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_zork_01_the_floor.json` | `2026-10-26T21:06:19.835460Z` | `2026-10-25T20:47:33Z` | `2026-10-26T21:06:14Z` | `6b46f04bfea387b3` |
| `ZORK_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_zork_02_long_crawl.json` | `2026-10-26T21:06:29.836017Z` | `2026-10-25T20:47:46Z` | `2026-10-26T21:06:20Z` | `2fe38cb1007b8297` |

Every row's measurement instant is corroborated independently: the preservation sidecar for that cell
was written to `suite3/preserved/` **before** the new row replaced the record at that path, and in 8 of 8
cases `preserved_at_utc` precedes `measured_at_utc` by 5.8–13.1 s. The two times are adjacent in every
entry and a day apart, so the misreading that produced the withdrawn ruling now reads as an obvious error.

## 2. Are the eight superseded artefacts still recoverable? — Yes, all 8 of 8, measured

Each entry names the superseded row under `suite3/preserved/<ts>/`, and
`check_measurement_times.py` hashes that file against the `predecessor_sha256` the row itself recorded in
`artifact_replaced` — 8/8 present on disk, 8/8 hashing to the recorded digest, 8/8 byte-identical to
`git show 13b161a^:probes/ZORK_*` and to `6c426e5:probes/ZORK_*`. Recoverability here is a hash against
the row's own record, not a claim in prose.

## 3. `probes/` was not touched

```
git diff 13b161a -- probes/   ->  <empty: byte-identical>
```

The eight rows stay byte-identical to `13b161a`, as the Chair instructed. The measurement time lives
**beside** the row and never inside it: writing a field into a committed row changes the sha256 of the
record it annotates — which is the digest every check and every ruling cites, and now also the key this
ledger is indexed by.

## 4. It is enforced, not declared

```
python3 check_measurement_times.py --self-test   ->  7/7
python3 check_provenance_classes.py --self-test  ->  8/8   (84 fields classified, 0 current-state)
python3 check_row_generation.py --self-test      ->  2/2   (17 rows, 0 claiming an instrument that
                                                            did not measure them)
```

`check_measurement_times.py` fails if a row has no entry, if `row_sha256`/`row_bytes` drift off the file,
if `measured_at_utc` is not strictly later than `predecessor_mtime_utc` (the R2 misreading, injected as a
mutant), if the preserved copy is missing or hashes to anything else, if a ledger key is unclassified, or
if a `current_*` key appears. Six controls, five of them mutants.

## 5. Which rows need re-running to be evidence again? — none

All eight name the instrument that measured them (`simulator_digest` `b9701007d6e186d5`, verified 17/17
across every Zork row in the repo), and R2's evidence-hold is lifted by the Chair's ruling.
