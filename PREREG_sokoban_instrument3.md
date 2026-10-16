# PRE-REGISTRATION — SOKOBAN INSTRUMENT CHANGE 3: THE BINARY IS SELECTABLE, AND IT TRAVELS WITH THE NUMBER

**Written BEFORE the code change**, in the house form of `PREREG_sokoban_instrument1.md` and
`PREREG_sokoban_instrument2.md`, and for the same reason: **a fix whose effect is not predicted in advance
cannot distinguish a repaired instrument from a luckier sample.**

**Card:** `t_33042da0` (written by the Chair). **Authority, stated rather than implied: NO Chair ruling is
cited, because there is none.** The card names the fix, requires a pre-registration rather than a silent
edit, and says *"Filing the prereg is the owner's call."* Read one way, the filing is this card's first
deliverable; read the other way, the filing is the owner's own act and this is a draft filed in the tree.
**Both readings are recorded here rather than resolved by me**, because the landing this precedes is
reversible in one commit and **moves no published number** (the default is unchanged — prediction 1).

**Pre-image, measured at the commit this prereg is written against:**

```
sokoban_run.py   35909 B   sha256 2d3da54d1446cef7f08adf4ccf405fbb40ca4cc1a7cff1fa0b12184402504d8f
```

**AND IT IS IN NO PINNED SET.** `FROZEN_DIGESTS` (`sokoban_solver.py:97-102`) names `sokoban.py` and the
three level files, and nothing else; a grep for `sokoban_run` across the tree returns comments, usage lines
and the conformance package's census of its blocks — **no digest of this file is asserted anywhere.** So this
change moves no frozen identity, the re-freeze procedure does not apply to it, and **no cell of any
population is re-scored.**

**THE NEW DIGEST IS NOT PREDICTED AND CANNOT BE** — a digest is a function of bytes that do not exist until
the commit is made; predicting one would be a fabricated number. It is recorded in the landing note appended
to this file after the commit exists.

---

## 1 WHAT CHANGES — TWO SUBJECTS, SEPARABLE COMMITS

**SUBJECT S1 — THE BINARY BECOMES A SELECTABLE, NAMED PART OF THE INSTRUMENT.** `--llama-server PATH`, with
**the default unchanged** (`LLAMA`, the hardcoded constant, still what runs when the flag is absent). A path
that does not exist or is not executable is **REFUSED before `exec`** — the guard `arena.py:152` already
carries, for the same reason: `--llama-server /typo` would otherwise surface as a launch failure and read
like a broken model.

**SUBJECT S2 — THE RECORD CARRIES THE BINARY'S IDENTITY.** `config` gains three keys, and the two
load-failure records gain the same three at their top level (those returns carry no `config` block at all):

```
server_binary_digest          sha256 of the BINARY FILE, first 16 hex
server_binary_digest_scope    what that digest is a digest OF, in words
server_binary_source          which selector chose the binary
```

**NO NEW PATH IS PUBLISHED, AND THAT IS A CONSTRAINT RATHER THAN AN OMISSION.** `server_argv` already carries
the path and is already classified **LOCAL** in `make_conformance_package.py` (`("config", "server_argv")`).
A digest, a scope sentence and a selector name are PORTABLE-shaped, so the package's two lists need no change
to stay true — and a new path-bearing field would have published another filesystem coordinate through a spec
whose whole point is that it does not.

**AND A PATH IS NOT AN IDENTITY — measured on this box, not asserted:**
`~/.hermes/runtimes/llamacpp/b10931/cuda/llama-server` reports `version: 0.4.1-dev (build 10964, commit
b29c606e2)`. A record carrying that path names 10931 and describes 10964. **That is the same rule the ENTRANT
already gets forty lines below in the same file** (`model_digest`, and its comment *"a name is not an
identity"*), applied one layer down the instrument.

**AND ONE FIELD THE FIRST DRAFT HAD IS DELETED, FOR A MEASURED REASON.** The draft carried
`server_binary_is_the_declared_default`. It cannot be answered from inside the driver: **the pre-image way of
running the fork was to set the module constant in memory at the call site** (the method the card itself
describes), and a module cannot tell that its own constant was patched — the field would have answered `true`
for a fork run. That is a false statement made out of a true measurement, so the two facts are kept separate
and each is worded as what it is: the DIGEST says which bytes ran; `server_binary_source` says which selector
was used (`"--llama-server"` or `"no selector given: the module constant LLAMA"`).

**NOT A SUBJECT, AND NOT ADDED: `server_argv` AND THE REASONING ARM.** Measured to be already present — see
§2(a).

---

## 2 THE PREMISE, RE-MEASURED — BECAUSE THE PREMISE DECIDES THE SCOPE

The card's premises were checked against the carriers rather than taken from them. **Two do not hold as
written, and one of them does not hold in the direction that matters.**

### (a) "the artifact carries … but no `server_argv` and no reasoning field" — FALSE at `dc1375b`

Measured from the committed bytes of
`probes/SOKOBAN_Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0_01_one_push.json` (and `…_02_two_boxes.json`):

```
config.server_argv[0]     /home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server
config.reasoning          off
config.reasoning_argv     ["--reasoning", "off"]
```

`config.server_argv` has existed since **`2e4e3de`, 2026-10-10** ("FINDING 022: the launch config was a
carrier too, and it was never written down") — **six days before the Bonsai run** — and it recorded the fork,
because the in-memory override moved the constant that the field is built from. So the artifact **was**
attributable before this change.

The false sentence lives in the artifact's own `INSTRUMENT-NOTE.md` (*"NOT RECORDED BY THE ARTIFACT: the
record contains no `server_argv` field … the artifact is indistinguishable from one the default binary
produced"*). **The artifact wins:** `PRECEDENCE.md`, *"the run log vs the artifact → the artifact"*, and
*"prefer the carrier to the claim"*. **No record is rewritten** — the note is a dated statement beside a
dated artifact, and the correction is filed as `FINDINGS/024` and named in the card thread.

### (b) "Mainline llama.cpp LOADS Bonsai ternary ggufs and emits degenerate garbage … mainline b11540" — the binary named is not the driver's default, and on the 4B file mainline does not load it at all

`/home/chilly1/llama.cpp/build/bin/llama-server` — **the binary the driver hardcodes** — is
`version: 0.4.0-dev (build 10931, commit 3057bb66c)`, not b11540. b11540 does exist on this box
(`~/.hermes/tools/llamacpp-cuda-11540-linux-x64/llama-server`), and **both refuse the 4B file at load**:

```
E gguf_init_from_reader: tensor 'token_embd.weight' has invalid ggml type 142. should be in [0, 43)
E llama_model_load: error loading model
```

**THE PHENOMENON IN THE CARD IS REAL, AND IT IS REPRODUCED HERE — with the driver's ACTUAL default, on a
different file of the same family.** Five arms, two files, one level (`01_one_push`), `-ngl 0`, cap 1–3:

| entrant file | binary | outcome | what the record then said |
|---|---|---|---|
| `Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0` | **b10931 = THE DECLARED DEFAULT** | `rc=1`, model **REFUSED**: invalid ggml type 142 | `loaded: false`, and the `why` glued a GPU-tenant sentence onto a CPU refusal |
| `…2-4B-PQ2_0-MTP-Q8_0` | b11540 mainline | `rc=1`, **REFUSED**, same tensor | `loaded: false` |
| `…2-4B-PQ2_0-MTP-Q8_0` | **prism fork b10777** | **LOADS — SOLVES in 1 move**, token `R` | `solved: true`, `moves: 1` |
| `Ternary-Bonsai-2-2B-Q2_0` | **b10931 = THE DECLARED DEFAULT** | **LOADS, and answers with 64 tokens of multilingual token salad per turn**; 3 turns, `moves 0`, `not_an_action 3`, every turn capped | **FILED AS THE MODEL'S NUMBER** — the hazard in the card, reproduced |
| `…2-2B-Q2_0` | prism fork b10777 | `rc=-6` (`ggml_abort`) | `loaded: false` |

**AND TWO THINGS FOLLOW THAT THE CARD DOES NOT SAY.** First, the hazard is **not** conditional on a fork
being available: `python3 sokoban_run.py --entrant <the 2B>` measures mainline and files token salad under
the model's name, and nothing in the run says which binary answered. Second, **a fork is not a universal
substitute** — b10777 aborts on the 2B file — so "use the fork" is not a fix that can be made silently in
the driver's default. **Both are arguments for exactly this change: the binary must be selectable AND
recorded, with the default left alone.**

**Also measured, and it is why the last column is not decoration:** on the 2B, two runs of the *same*
pre-image driver on the *same* binary produced **0 and 64 tokens** respectively — the salad is not even
reproducible run to run. Nothing about that arm is a measurement of the model except by accident.

---

## 3 THE PREDICTION, RECORDED BEFORE THE CODE CHANGE

**1. THE DEFAULT IS BYTE-IDENTICAL.** `server_argv(<any entrant>, 4096, 8751)` returns the pre-image list
exactly, and a default run prints exactly what it printed before — the new `binary` line prints **only** when
`--llama-server` is given, so the declared default's stdout stays its own control.
*Falsifier: any byte of that list or that stdout differs.*

**2. NO MEASURED QUANTITY MOVES.** Pre-image and new-image records, same arms, same ports: every counter,
`final_board`, `trace`, `budget_signature`, `dead_end`, `unreadable`, `missing_values` and **every config
value that already existed** identical; the only deltas are the three new keys. *(Measured in the working
tree before this was written: it holds on the 2B-default, 4B-default-refusal and 4B-prism arms, with
`config` values that moved = `[]` on all three — and the one arm whose MODEL OUTPUT is not reproducible is
named in §2(b) rather than discovered later.)*

**3. THE FLAG HOSTS THE FAMILY END TO END.** `--llama-server <prism b10777>` on the 4B solves level 01 and
the artifact carries `server_binary_digest 3c7090fb24b84615` with `server_binary_source "--llama-server"`;
the same command **without** the flag refuses and the failure record carries the default's digest
`0d5393431782ddf8` with `server_binary_source "no selector given: the module constant LLAMA"`.
*Falsifier: a record whose digest is not the digest of the binary that ran it.*

**4. A BAD PATH IS REFUSED, NOT EXEC'D.** `--llama-server /nope/llama-server` exits **2** with
`BINARY ABSENT OR NOT EXECUTABLE`, and no server is started.

**5. NOTHING ELSE MOVES.** The repo's controls return **rc-identical** before and after; the ones whose bytes
differ differ only in a worktree-name string or a solver TIMING, enumerated line by line in the landing note.
`sokoban.py`, the three levels, `FROZEN_DIGESTS`, `SOKOBAN_FREEZE_RECORD.md`, `SOKOBAN_READ_GRAMMAR.md`,
`CABINET_DECLARATION_sokoban.md`, `SOKOBAN_CONFORMANCE_PACKAGE.md`, both earlier preregs and every artifact
under `probes/` are **untouched**. *Falsifier: any file outside the two named subjects changes.*

**6. FALSIFIERS, NAMED SO THE PREDICTION CAN FAIL:** any change to the default argv or to the default's
stdout; any published quantity moving on any arm; a record claiming a digest the binary did not have; a
refused path reaching `exec`; a third file changing; or the new fields failing to appear on the load-failure
records, which are exactly where the binary is decisive.

---

## 4 WHAT IS **NOT** IN THIS CHANGE, DISPOSED OF ONE BY ONE

*(A carrier is disposed of explicitly or not at all.)*

**(a) THE ARTIFACT AND LOG NAMES CARRY NO BINARY — AND A SECOND RUN ON A DIFFERENT INSTRUMENT OVERWRITES
THE FIRST. MEASURED:** two runs of the pre-image driver on one `(entrant, level)` pair, first the fork and
then mainline, wrote **one artifact path and one log path**. The log now holds the fork's abort backtrace
where the mainline run's log was, the artifact's mtime advanced, and **the first run's record is gone** —
`probes/SOKOBAN_<entrant>_<level>.json` and `logs/SOKOBAN_<entrant>_<level>_<legend>_rea-<arm>.log` name
neither the binary nor the selector. **This is `FINDING 020`'s shape — "two runs, one path" — on the binary
axis, and no FIELD fixes it: the record that would carry the field is the record that gets overwritten.**
**PROPOSED, NOT LANDED**, because the fix changes a published naming convention (`probes/*.json` names are
cited in `GAMES.md` and in the conformance package's census). The named flip, in one line: **refuse to
overwrite an artifact whose recorded `server_binary_digest` differs from this run's, with the escape being
the documented one-token override.** *Cost of flipping:* the filename convention becomes
instrument-dependent and citations must carry it. *Cost of not flipping:* a second run on a different binary
destroys the first run's record silently.

**(b) THE LOAD-FAILURE `why` NAMES A GPU HOLDER FOR A CPU RUN. MEASURED** — the 4B refusal (invalid ggml
type 142, `-ngl 0`, no VRAM touched) printed *"AND THE CARD IS HELD BY: pid 2418 (134 MiB) … Tenants total
7146 MiB"*. `holder_sentence()` is appended on **every** load failure, so a binary that cannot read a tensor
type is rendered as a card-tenancy condition. **Reported, not changed:** that sentence is RULING 82's, it was
ratified for a different cause, and narrowing it is a change to that ruling's carrier — not this card's.

**(c) THE CONFORMANCE PACKAGE'S FIELD CENSUS IS NOW THREE NAMES SHORT.** `SOKOBAN_CONFORMANCE_PACKAGE.md`'s
CONFIG BLOCK list does not name the three new fields. **Not amended:** it is a dated carrier (the freeze
record treats its digest citations as belonging to a date), the addition is not a correction of anything in
it, and the two lists in `make_conformance_package.py` stay true precisely because no path was added.

**(d) THE FALSE SENTENCE BESIDE THE BONSAI ARTIFACT (§2a).** Records are not rewritten. Filed as
`FINDINGS/024`; named in the card thread; a reader of the note is sent to the artifact, which wins.

**(e) THE LOG FILENAME.** The log is **declared SCRATCH** (`DECISION_logs_are_scratch.md`;
`LOG_EDGES.json:35-39` declares this launch path's log coordinates an open, deliberate edge). The binary is
not added to its name here, for (a)'s reason: the convention is the Chair's to move.

---

## 5 SCOPE, AND WHAT THIS DOCUMENT IS NOT

**FUTURE RUNS ONLY.** A number is read under the text and the instrument it was taken under. Nothing is
retro-fitted, restated or reinterpreted. **No probe, prereg, freeze record, grammar, declaration,
conformance package, snapshot or manifest is edited**, and the three new fields appear only in records
written after this change.

**IT IS NOT A CLAIM ABOUT THE MODELS.** Nothing here says what a Bonsai entrant can do. The 4B solving level
01 in one move is one SOKOBAN level that **every** prior winner has solved; `02_two_boxes` remains unpassed
by any entrant, as the card's own last section records.
