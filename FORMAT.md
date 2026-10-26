# THE HANDICAP ARENA — FORMAT & RULEBOOK

**MENSA meets UFC.** A sanctioned competition circuit for local models running on consumer hardware.
Skill is measured; spectacle is the delivery mechanism; **reproducibility is the law.**

---

## 1. The core conceit

Frontier leaderboards rank models globally, which means a 4B quant running on a six-year-old GPU is
placed 400th and nobody ever looks at it. **That is not a worse GPT-5. That is a different sport.**

So: **weight classes defined by what actually deploys in memory, not by parameter count in a
filename.** A 350M extractor and a 35B MoE are both champions — of different divisions.

---

## 2. Divisions

| division | footprint | typical field |
|---|---|---|
| **Featherweight** | ≤4 GB | 350M–4B at Q4/Q5 |
| **Lightweight** | ≤8 GB | 7–9B at Q4 — **the reference class** |
| **Middleweight** | ≤16 GB | 12–24B at Q4 |
| **Heavyweight** | >16 GB | 30B+ (may use CPU/FFN offload) |

**Measured, not declared.** A model enters a division by its **file footprint as served**, verified
against the GGUF hash. Lying about your weight is the one thing the hash cannot be argued with.

---

## 3. Contest types → the show

Every task already has a natural combat metaphor. This is not decoration — it tells the viewer how
to read the result at a glance.

| task | the contest | what the viewer sees |
|---|---|---|
| **Structured output / JSON schema** | **Fencing** — precision duel | each valid field extends a blade; a schema violation is a touch against |
| **Tool calling** | **Chess** — a move, not a brawl | the correct tool is the winning move; wrong tool is a resignation |
| **Code repair (tests executed)** | **Pit stop** — a race against the clock | car crosses the line only when the tests pass; a failure is a DNF |
| **Long-context retrieval** | **Marathon** | 128K tokens is the distance; each needle found is a checkpoint |
| **Throughput at fixed concurrency** | **Drag race** | tokens/sec is the speed; accuracy is "did it finish without crashing" |
| **Multi-turn constraint retention** | **Endurance bout** | rounds 1–8; a dropped constraint is a knockdown |
| **Refusal calibration** | **Judge's scorecard** | two error rates, scored like boxing — over-refusal and under-refusal |

**A card** is a set of bouts in one division: undercard → co-main → **main event**, with a belt on
the line at the top.

---

## 4. Scoring

- **Each task is a round.** Each trial is one judge.
- **A round is won on pass rate** across trials; reported with the raw trial scores, never a
  summary alone.
- **No LLM judges, ever.** Rounds are scored by parsers and by *executing* generated code against a
  test suite. A model grading its own family is not a judge, it is a conflict of interest.
- **Throughput is displayed alongside every score.** A model that is right and unusably slow has
  not won anything.
- **Config is printed with every result** — temperature, max_tokens, trials, context size, quant,
  template, and whether a grammar was applied. *A result without its config is not a result.*

---

## 5. Punching above your class

The user's rule, formalised:

1. A **division champion** who wins three consecutive sanctioned bouts earns a **mandatory
   challenger slot in the division above.**
2. The bout is fought at **catchweight** — the smaller model declares its true footprint and keeps
   it; no penalty for being light.
3. **Winning above your class transfers the belt.** Moving up permanently requires vacating the
   lower title (one model, one belt).
4. Losing above your class costs nothing — you keep your division.

This is how a 3B earns a shot at an 8B, and it is the single most watchable mechanic in the format.
It also produces the most interesting *data*: where does capability actually break with size?

---

## 6. CERTIFICATION — the anti-cheat architecture

**The honest framing: you cannot verify what you did not run.** Everything else is a fingerprint,
and fingerprints can be forged. So the arena splits results into two explicit tiers and never
conflates them:

### Tier 1 — OPEN (self-reported, **UNCERTIFIED**)
Cheap, instant, anyone can enter. Every result is labelled **UNCERTIFIED** in the same size type as
the score. Screened by, in order of strength:

| screen | what it catches |
|---|---|
| **GGUF hash** in a signed manifest | "I ran a 70B" — the hash must match a known file |
| **Hardware throughput ceiling** | a model too *fast* to be local. A 3B on 8 GB does not do 300 tok/s; a routed API does |
| **Inter-token interval distribution**, measured client-side | local inference has a tight, hardware-bound cadence; network APIs are jittered and batched |
| **Logprob capture** where the server exposes it | a strong statistical fingerprint of the actual model |
| **Deterministic replay seed** | allows later re-execution |
| **Honor system** | nothing. Fine for a fun board, worthless the moment money exists |

### Tier 2 — CERTIFIED (**the arena re-runs it on its own reference rig**)
**This is the answer.** You submit; if you place, **the arena loads your exact GGUF by hash and
re-runs the bout on arena hardware.** Reproduce the score and you are **CERTIFIED**. Fail to
reproduce and the result is **STRUCK**.

- **Cheating is not detected — it is impossible**, because the arena ran the model itself.
- **It is cheap**, because only *placing* submissions are re-run, not the whole field.
- **Certification is the scarce good**, and therefore the product.

**The rule, stated plainly: unverified to participate, verified to be crowned.**

### Tier 3 — CHAMPIONSHIP
Belts are **only** awarded on Tier-2 certified results, on arena hardware, in front of the
published config. No exceptions, no honour system, no asterisks.

---

## 7. Why this is hard (and why that is the moat)

We discovered this the hard way, on our own first run. Four separate confounds each produced a
**confident, clean, completely wrong leaderboard**:

1. **Stale server config** — two entrants pointed at deleted model files. They 404'd and were
   scored 0.00 as if they were models.
2. **Reasoning-field routing** — reasoning models return their answer in `reasoning_content` and
   leave `content` empty. Reading the wrong field scored a strong model 0.00.
3. **A GBNF grammar file** applied by the serving layer. Four models were *physically incapable* of
   emitting the required schema and scored 0.00. **The table measured the grammar file.**
4. **Alias names that lie** — an alias called `granite-8b` served Qwen3.5-9B.

**Any arena that does not solve these is confidently wrong, which is worse than being empty.**
That is the entire defence against a competitor copying this: the format is easy to copy, the
provenance discipline is not.

---

## 8. Remote play (phase 2)

- Models **challenge** models: any operator can issue a challenge to a rival's entry in their
  division.
- Both sides run the same **locked task suite** and submit signed bundles.
- The arena **adjudicates, then certifies the winner's result on arena hardware** before the result
  becomes official.
- **Bouts are asynchronous** — no scheduling, no simultaneous presence needed. A fight card is
  assembled from completed bouts.
- Divisions, belts, records and rankings are public; **every claim links to a reproducible command.**

---

## 9. Roadmap

**These numbers are the project line, and they are normative.** `README.md` previously carried a
different numbering for the same items — its "v1 (here)" was this list's **v0.1**, and its "v2
challenge flow" was this list's **v1**. Reconciled here on 2026-10-07; the README now points at
this section rather than restating it differently.

**Card versions are a separate axis and do not appear in this list.** A result bundle's
`card_version` identifies the task suite (1 = the retired 3-round card, 2 = the 18-item battery).
The current state is **card v2 on project v0.1** — two numbers, two axes, and conflating them is
how the README/FORMAT divergence started.

1. **v0** — one rig, three parser/test-scored tasks, published config, `content`/reasoning handling,
   pre-flight verification. *(done — and it caught all four confounds above)*
2. **v0.1** — neutral serving (own llama-server instances, never app-configured aliases),
   hash-verified model registry, scored tasks, cross-division card. *(done)*
3. **v1** — website, divisions, belts, challenge flow, Tier-1 submissions. *(next — this is the
   front end)*
4. **v2** — Tier-2 certification pipeline (re-run queue on reference hardware).
5. **v3** — sponsored bounty cards. **This is where the money actually is.**

---

## 10. RECORD PROVENANCE — measured at the event, or current state

Every field of every record this project writes is exactly one of **two classes**. A field that is
neither, or that is both, is a defect in the format and not a matter of taste.

### The two classes

- **MEASURED AT THE EVENT (`M`)** — true of the moment the row records. **Once the row is committed
  the value is immutable.** Recomputing it is allowed only as a *check* against the committed value;
  it is never an overwrite. A field recomputed to stay true can never be evidence, because it will
  agree with the world no matter what the world did.

  Two kinds inside `M`, and the kind decides what a reader may do with the number:
  - **`M1` measurement** — a value observed while the event ran, or computed from what was observed
    then. `trace`, `counts`, `simulator_digest`, `host`.
  - **`M2` scope** — committed text saying what an `M1` field *means*: what bytes a digest digests,
    which side of a denominator a count sits on, which readings are prose. `M2` is what makes `M1`
    checkable; it is not itself a measurement.

- **CURRENT STATE (`C`)** — a value that depends on something **outside the row's own bytes**: a file
  on disk now, the live archive now, the instrument in use now. It changes without the event
  changing. A `C` field is recomputable *by definition*, which is exactly why it cannot be evidence.

### The naming rule — how a reader tells them apart without reading the rest of this section

1. An **`M`** field carries a **bare name** (`simulator_digest`, `counts`, `trace`). A field naming an
   artifact by digest MUST have a sibling `<name>_scope` of class `M2` saying what it digests.
2. A **`C`** field MUST be named **`current_<thing>`** (`current_simulator_digest`). **No bare name
   may be defined as recomputable, and no name beginning `current_` may be a measurement.** The name
   is the whole contract: a reader who sees `simulator_digest` may rely on it being the instrument at
   measurement, and a reader who sees `current_simulator_digest` may rely on it being a statement
   about now that is not evidence about then.
3. **A `C` field MUST NOT be written into a committed row.** Writing it changes the row's bytes and
   therefore the digest of the very record it annotates — the annotation destroys its subject.
   Current state lives in a sidecar beside the row (`<row>.json.provenance.json`, the convention
   already in use under `suite2/runs/published_cpu/`) or is computed at read time. A row carrying its
   own "current" value is stale from the second it is written.

### The measurement instant — the one field a row cannot be asked to carry

**Measured case, 2026-10-26.** Eight committed rows carried no field saying *when* they were measured.
Their reader took the date from `artifact_replaced.mtime` — 2026-10-25 — and concluded that a later
commit (`13b161a`, 2026-10-26 14:36) had rewritten `simulator_digest` inside already-recorded rows. The
rows were written **2026-10-26 14:05:20–14:06:29**; the 2026-10-25 stamp belonged to the records they
*replaced*. The ordered repair was withdrawn because what was missing was a field, not a defect.
**A missing instant is not a cosmetic gap: the nearest available timestamp gets read as the row's own.**

`measured_at_utc` is therefore required for every row, and it is class **`M1`**: the instant the driver
closed the row's file — the *end* of the event — read once from the filesystem and **frozen at
observation**. It is not in git and cannot be recomputed; the ledger also records `observed_at_utc`,
the instant the reading was taken, so the reading has a date of its own instead of looking live
forever.

**It lives beside the row, in `provenance/measurement_times.json`, and never inside it.** Writing a
field into a committed row changes that row's `sha256` — the digest of the very record the field
annotates, and the digest every check and every ruling cites. The ledger is instead **keyed by
`row_sha256`**: if a row's bytes move, the entry stops matching and the check goes red. Drift is
impossible to hide rather than merely forbidden, and the reading is never silently refreshed by a
re-run.

**A predecessor's time is never a bare `mtime`.** It is `predecessor_mtime_utc`, and it appears only
beside `measured_at_utc` — the two instants are adjacent in every entry and a day apart, so the
misreading that produced the withdrawn ruling reads as an obvious error.

**Recoverability, measured rather than asserted:** each entry names the superseded artefact under
`suite3/preserved/<ts>/` and the check hashes that file against the `predecessor_sha256` the row itself
recorded. All **8 of 8** superseded rows are present on disk and hash to their recorded digests —
"preserved" is a claim; a hash against the row's own record is a measurement.

### Why this is not pedantry — two measured cases

**One: the field that was suspected of being recomputed.** `simulator_digest` carries the scope text
*"THE SIMULATOR IS THE INSTRUMENT THIS EVENT IS MEASURED WITH"*. A bare field under that sentence
that is recomputed at read time is a `C` wearing an `M`'s name, and every row automatically claims the
instrument that happens to be on disk. The naming rule makes that impossible to do silently; if a row
must also express today's instrument it is `current_simulator_digest` in the sidecar, never a rewrite
of the measured field.

**Two: a control that reads the archive and calls it an invariant.** `zork_run.py`'s block [5] asserts
over the **live** `probes/ZORK_*.json` that every row contradicts itself —
`config.n_gpu_layers` says `0` against `server_argv -ngl 99` — and expects all eight to disagree. That
is a **`C` assertion in an `M` assertion's clothing**: it is a claim about which files are in a
directory right now, not about the instrument. Measured at `13b161a`: `0` of `8` rows contradict, so
both controls go red and `--self-test` reads **62/64** — the control fails *because the writer was
fixed*. A control of this shape must read a **fixture** whose bytes are committed (the sitting-2 rows
under `suite3/preserved/` carry exactly the eight `('0','99')` pairs this control wants — measured),
never the mutable archive.

### Classification of every field in a Zork cell record

Measured from the eight committed rows at `13b161a`: **65 top-level fields, 0 of them `C`.** The
format has no current-state field today, so this rule is prospective — its job is to forbid the
transformation and to fix the name for anything added later. Nested blocks are classified with the
fields inside them.

The same eight rows carry **no field naming when they were measured**, which is why the ledger beside
them (`provenance/measurement_times.json`) exists; its **19 keys** are classified in the second table
below and carried by no row, so the row count stays at 65.

| field | class | why |
|---|---|---|
| `artifact_replaced` | `M1` | digest, byte count and mtime of the record that was at this path before — facts about bytes that existed at the event; `reason_given` inside it is operator prose and the block says so |
| `attribution` | `M1` | per-command attribution totals counted at the event; re-derivable from `trace` as a check only |
| `attribution_checked_against_counts` | `M1` | result of a check the driver ran at the event |
| `attribution_is_the_scoreable_form` | `M2` | declaration about the format, not a measurement |
| `attribution_of` | `M2` | scope text defining what `attribution` counts |
| `attribution_reasons` | `M1` | reason-code counts counted at the event |
| `attribution_reasons_text` | `M2` | the human strings for those codes |
| `attribution_scope` | `M2` | scope text |
| `budget_signature` | `M1` | derived from `turns[].gen_tokens` against the ceiling at the event |
| `cap` | `M1` | the command cap the run was launched under — a parameter fixed at the event |
| `carried_required_item` | `M1` | observed faculty flag |
| `commands` | `M1` | counted at the event |
| `commands_consumed` | `M1` | counted at the event |
| `config` | `M1` | the config **as launched** (`server_argv`, `ctx`, `n_gpu_layers`, `parallel`, …) — read out of the argv at launch, immutable after |
| `counts` | `M1` | the frozen counters; re-derivable from `trace` as a check only |
| `criteria_read_by` | `M2` | states that the C1–C4 verdict is not the driver's to make |
| `ended` | `M1` | observed |
| `ending` | `M1` | observed |
| `entrant` | `M2` | a LABEL for reading, not for checking — the row says so itself |
| `entrant_digest` | `M1` | sha256 of the model file measured at the event |
| `entrant_digest_scope` | `M2` | says what the digest digests |
| `final_inventory` | `M1` | world state read at the end of the event |
| `final_room` | `M1` | world state read at the end of the event |
| `final_state` | `M1` | the text the entrant last saw at the end of the event |
| `finished` | `M1` | observed |
| `host` | `M1` | **the box at the event** (`platform`, `release`, `machine`, `cpus`, `python`) — not "what box is this now"; if it were recomputed at read time it would be `host` the `C` field and its name would be a lie |
| `kind` | `M2` | declares `model` \| `code` — a parameter of the event |
| `legend` | `M1` | which legend variant the run used |
| `legend_digest` | `M1` | sha256 of the rendering function measured at the event |
| `legend_digest_scope` | `M2` | says what the digest digests |
| `level` | `M2` | level name label |
| `level_digest` | `M1` | sha256 of the level file measured at the event |
| `level_digest_scope` | `M2` | says what the digest digests |
| `level_text` | `M1` | the level **as it was**, so the score is recomputable from the record alone |
| `load_s` | `M1` | measured |
| `loaded` | `M1` | observed |
| `missing_values` | `M1` | A7 counter, counted at the event |
| `missing_values_are_a_subset_of` | `M2` | states the relation to `unreadable` |
| `never_started` | `M1` | A7 counter, outside the denominator |
| `never_started_scope` | `M2` | states which side of the denominator it sits on |
| `outcomes` | `M1` | counted at the event |
| `progress` | `M1` | computed from the parsed world and its state **at the event**; re-derivable from `trace` as a check only |
| `progress_field_source` | `M2` | declares a source for each `progress` leaf |
| `progress_prose_only` | `M2` | names the readings that are prose and must not be counted |
| `progress_scope` | `M2` | scope text |
| `reading_note` | `M2` | note on how to read the driver's rule |
| `reasoning_probe` | `M1` | observed completion fields; `inference_caveat`/`observed_is_an_inference` inside it are `M2` |
| `required_item` | `M2` | the level's required item — a parameter of the event |
| `rooms` | `M1` | world state at the event |
| `rooms_visited` | `M1` | world state at the event |
| `scoreable` | `M1` | verdict computed at the event from the row's own contents |
| `scoreable_scope` | `M2` | states the condition under which it is true |
| `simulator` | `M2` | the instrument's FILE NAME — a label; the digest is the identity |
| `simulator_digest` | `M1` | **the instrument this event was measured with.** Never recomputed, never rewritten |
| `simulator_digest_scope` | `M2` | says what the digest digests and that the instrument is pre-registered |
| `start_room` | `M2` | the level's start room — a parameter |
| `sufficiency` | `M1` | thirteen checks run at the event |
| `sufficiency_ok` | `M1` | their result at the event |
| `took_item_at_step` | `M1` | observed (nullable, and null means null — never a substituted zero) |
| `trace` | `M1` | the per-command record: the core measurement |
| `transcript_lines` | `M1` | counted at the event |
| `turns` | `M1` | the raw entrant turns (`prompt`, `raw`, `answer_field`, `gen_tokens`, `secs`, `budget_hit`, `cap_cut`, `missing_value`) |
| `unreadable` | `M1` | A7 counter, inside the denominator as a non-pass |
| `unreadable_is_the_aggregate_of` | `M2` | states what it aggregates |
| `unreadable_scope` | `M2` | states which side of the denominator it sits on |

**The ledger beside the rows — every key classified.** These 19 names appear in
`provenance/measurement_times.json` and in no row. `measured_at_*` and `predecessor_*` are deliberately
adjacent: one is the row's own instant, the other is the instant of the record the row replaced.

| field | class | why |
|---|---|---|
| `ledger_kind` | `M2` | says what the file is |
| `measured_at_local` | `M1` | the same instant as `measured_at_utc` in the box's civil time — a rendering, not a second reading |
| `measured_at_scope` | `M2` | says that `measured_at_utc` is the write instant (the END of the event), read from the filesystem once, corroborated by `preserved_at_utc` |
| `measured_at_utc` | `M1` | **the instant this row was measured.** Frozen at observation; not in git, never recomputed, never refreshed |
| `naming_rule` | `M2` | the naming rule for the ledger's own keys |
| `observed_at_utc` | `M1` | when the filesystem reading was taken — a second instant, so the reading is dated rather than looking live |
| `observed_from` | `M2` | what was read and from where |
| `predecessor_mtime_scope` | `M2` | says that `predecessor_mtime_utc` is the REPLACED record's time and never this row's |
| `predecessor_mtime_utc` | `M1` | the mtime of the record this row replaced, as the row itself records it in `artifact_replaced.mtime` |
| `predecessor_sha256` | `M1` | digest of the superseded record |
| `preserved_at_utc` | `M1` | when the superseded record was copied aside — must precede `measured_at_utc`, and does in 8 of 8 |
| `preserved_copy` | `M2` | path of the superseded bytes — a label; `predecessor_sha256` is the identity |
| `preserved_sidecar` | `M2` | path of the preservation record carrying those bytes' digest and size |
| `row` | `M2` | the row's path — a label |
| `row_bytes` | `M1` | size of the bytes annotated, as measured on disk at observation |
| `row_sha256` | `M1` | **the digest of the bytes this entry annotates** — the key; drift means the annotation no longer describes its subject |
| `rows` | `M1` | the entries, one per row in scope |
| `scope` | `M2` | scope text for the file |
| `why_not_in_the_row` | `M2` | states why the instant is beside the row instead of inside it |

**Enforced, not declared:** `python3 check_provenance_classes.py --self-test` parses this table and
fails if a committed row carries a field this table does not classify, if a row carries any field
named `current_*`, or if a field is declared `C` under a bare name. Both directions are controlled by
mutation. `python3 check_measurement_times.py --self-test` fails if a row in `probes/` has no ledger
entry, if an entry's `row_sha256`/`row_bytes` do not match the file, if `measured_at_utc` is not
strictly later than `predecessor_mtime_utc`, if the preserved copy is missing or hashes to anything
other than the recorded predecessor, if a ledger key is unclassified, or if a `current_*` key appears
in the ledger — six controls, five of them mutants.

