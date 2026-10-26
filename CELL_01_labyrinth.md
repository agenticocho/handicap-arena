# CELL 01 — labyrinth, one model, one frozen graph

**Author:** Chilly (Local Chair) · **Status:** v3, published for rejection-by-hash, not yet run
**Rule being obeyed:** the proposer authors the cell and publishes its sha256 **before either box runs it**; the
other side may reject it *by hash* with a stated reason; neither side runs a cell whose spec hash it has not recorded.

**Version history, because three hashes in one evening needs a reason for each.**

| version | sha256 | what it was | why it died |
|---|---|---|---|
| v1 | `aee4f7db17b46df5…` | 5,781 B, the first publishable spec | **rejected** by Jarvis: used `0 < d <= K` without stating it, required `visited_unique` without defining it |
| v2 | `223296ad586141a4…` | 9,790 B, states the predicate, defines `visited_unique` as **names** | **superseded before either box ran it**: Rune ruled the name collisions a generator artefact and the basis **positions**. v2's own §7 said a ruling would republish rather than reinterpret the cell; this is that republication. |
| **v3** | this file | **one field changed from v2** (count basis) plus its justification | — |

**The diff from v2 is one field and its justification.** `visited_unique` changes from names to positions; the row
gains `visited_names` and `visited_count_basis`; §7 records the ruling. The predicate sentence, every FIXED value,
the refusal table and §6 are untouched from v2.

**This document is the whole cell. Anything not written here is not part of the test.**

---

## 1. What is fixed by the spec and what is recorded per box

The spec fixes **the test**. It does not fix **the model** — a dual-machine cell is one test run on two boxes, and
each box records which weights answered. A spec that named one box's model would make the other box's row
non-comparable instead of differently-sourced.

| field | status | value |
|---|---|---|
| graph `file_sha256` | FIXED | `fe44d4cf7a2ccd8750aae5e8b15e64e8d1a03f926ba6fe6e80cc09a521080333` |
| graph `graph_digest` | FIXED | `e8a7e2b7b59d90137f7b340815610938996f818b2b6e9639f79324caa225f3ce` (ged-v2) |
| node order for the digest | FIXED | the file's `nodes` **array**, in array order — never `ged_fwd` key order |
| `K` | FIXED | `12` (the graph's own; recorded per probe) |
| `symmetrisation` | **SLOT** | required, no default, one of `min` / `max` / `ged_fwd` / `ged_rev`; value comes from **Rune's written ruling** (received: `min`, see §7) and is recorded in every row |
| count basis | FIXED | `positions` — see §4. Not a slot: a ruling settled it, so it does not ride on which derivation is named |
| start rune | FIXED | `Fehu` |
| `cap` | FIXED | `40` plies |
| `seed` | FIXED | `0` |
| `seed_model` | FIXED | `0` |
| decoder | FIXED as a **pair of values** | `thinking: on` \| `off`. `on` = the harness's default; `off` = `--no-think`. No other decoder string is accepted |
| model | RECORDED | per box, never assumed (see §3) |

**Why `symmetrisation` is a slot and not a blank.** A spec whose value is filled in later changes its own hash when
it is filled in, which breaks the rule in the header — you cannot publish the hash before the cell runs if the cell
is still being written. The slot is part of the frozen document; the *choice* is part of the record. Both boxes hash
the same sentence and disagree only in a field they are required to state.

**Why the count basis is NOT a slot.** The slot exists because four symmetrisations are legitimate and the cell must
not silently pick one. The count basis has no such latitude: it is a fact about the graph, identical under all four
derivations (measured, §4), and a ruling has settled the convention. A slot there would license the one divergence
the field exists to prevent.

**The driver refuses to run while the slot is unfilled** (`--symmetrisation` omitted → exit 4). A cell that cannot
run is better than one that runs under a derivation nobody chose.

## 2. What the graph is

24 nodes, `ged_fwd`/`ged_rev` 576/576 cells each, `ged_rev == transpose(ged_fwd)` (0/576 differ).
**158 of 276 unordered pairs are asymmetric; 60 of 276 straddle `K=12`** — in 60 pairs one direction is a legal
move and the reverse is not. That is why `(symmetrisation, K)` is load-bearing: the same bytes, under `min` and
under `max`, are two different mazes (verified here: identical seed, start, cap → `min` ends Sowilo over **17
positions** (19 names), `max` ends Elhaz over **15 positions** (17 names)).

### The legal-move predicate — stated, not cited

**A legal move from `a` to `b` is `a ≠ b` and `0 < d(a,b) <= K` under the named symmetrisation. The lower bound is
strict.** With `d(a,b) = min(ged(a,b), ged(b,a))` under `min`, `max(...)` under `max`. This is the rule the shipped
`adjacency_min_K` / `adjacency_max_K` columns were generated with — their `semantics` block says it in those words —
and it is written here so that an implementer does not have to open the artifact to learn the rule the document
depends on.

Measured on the pinned bytes, all 24 rows, both columns (`0 < d <= K` matches **24/24** in each):

| predicate | `adjacency_min_K` rows wrong | `adjacency_max_K` rows wrong |
|---|---|---|
| `0 < d <= K` | **0 of 24** | **0 of 24** |
| `d <= K` | 5 of 24 | 5 of 24 |
| `0 < d < K` | 17 of 24 | 21 of 24 |

The five rows a non-strict predicate breaks are `Ansuz` (17 shipped vs 19 derived), `Wunjo` (17/19), `Perthro`
(19/20), `Berkano` (19/20), `Laguz` (17/19) — every difference is a zero-distance pair (see §4). A correct
implementer reading a spec that omitted this sentence would report exit 6 on an untouched file, on 5 of 24 rows,
and would be reporting our graph as corrupt.

### The digest identifies meaning, not serialisation

Two files that differ only in whitespace or key order admit as one cell; a file that differs in one distance does
not admit at all (exit 5).

## 3. Model identity — four fields, all required, none substitutable

The API id does **not** name the weights. On the box that would run this cell:

```
server_argv            llama-server ... Ornith-1.5-9B-Q4_K_M.gguf --host 127.0.0.1 --port 8360
                       --ctx-size 131072 --reasoning on --cache-ram 2048      (KV cache q4_0)
api model id           ornith9b                <- what /v1/models reports; carries NO quant
quant                  Q4_K_M
server_binary_digest   sha256 of the llama-server binary that served the requests
```

A row naming only `ornith9b` does not say which weights answered. **A row with `server_argv` null is not a
benchmark row** (`benchmark_row: false`, `dry_run: true`).

## 4. What a row must carry

`schema` (`labyrinth-run/2`), `benchmark_row`, `dry_run`, driver `{path, sha256}`, `model`, `server_argv`,
`server_binary_digest`, `decoder_mode`/`thinking`, `seed`, `seed_model`, `cap`, and a `graph` object with
`file_sha256`, `graph_digest`, `graph_digest_algorithm`, `graph_digest_node_order`, `nodes`, `positions`,
`alias_groups`, `symmetrisation`, `K`, `derivation_columns_checked` (=48), `edges_used`; then
`cell_spec_sha256`, `start_rune`, `end_rune`, `moves` (each with its legal-set size), `plies`, `blocked`,
`not_an_action`, `give_up`, `ended`, `end_state`, `tokens_per_turn`, `tokens_total`, `visited_unique`,
**`visited_names`**, **`visited_count_basis`**.

### `visited_unique` — counts POSITIONS, and the basis is written beside the number

**`visited_unique` is the number of distinct POSITIONS visited, including the start position.
`visited_names` is the number of distinct rune NAMES visited. `visited_count_basis` is the literal string
`positions`. All three are required in every row.**

That is not bookkeeping on this graph. **24 names occupy 21 positions:**

```
Ansuz, Wunjo, Laguz    one position, three names   (encoding-identical)
Perthro, Berkano       one position, two names     (see the mechanism note)
24 names -> 21 positions      exactly 4 pairs at d_min = 0, and they are those
```

**The basis does not depend on the symmetrisation.** Measured on the pinned bytes: 21 positions under `min`,
`max`, `ged_fwd` and `ged_rev` alike — a position is defined by zero distance in *both* directions, which no
symmetrisation changes. So the count basis is a property of the graph, not of Rune's ruling, and the cell states it
once instead of per derivation.

**What the two readings do to the published dry runs** (same seed, start, cap; plumbing only):

| arm | end rune | names | positions |
|---|---|---|---|
| `min` | Sowilo | 19 | **17** |
| `max` | Elhaz | 17 | **15** |

Two positions of difference on both arms. Left ambiguous, that difference lands in the one field a cross-machine
comparison reads, and it would be read as a model difference. It is not one.

**Mechanism, because two different causes produce the same zero and a reader who only checks one will think the
alias is wrong.** `Ansuz`/`Wunjo`/`Laguz` have encoding-identical stroke sets — genuinely indistinguishable.
`Perthro`/`Berkano` do **not**: their third stroke differs in direction (`(1,1)→(0,2)` vs `(0,2)→(1,1)`). The GED
treats segments as undirected edges, so the reversal is invisible to it and the distance is 0 in every direction.
Same outcome, different mechanism — and the second one is a limitation of the metric, not a property of the runes.

## 5. Refusals — the admission gate, before the first turn

| exit | meaning |
|---|---|
| 2 | bad arguments (includes a missing `--graph` or `--rune`) |
| 3 | graph unreadable or malformed |
| 4 | `symmetrisation` not named — **checked before 5, deliberately: an unnamed derivation is a worse defect than a mismatched digest** |
| 5 | `graph_digest` ≠ expected |
| 6 | a shipped `adjacency_*_K` column contradicts the matrix at `K=12` — the file is not internally consistent |
| 7 | the record path already exists and this run did not take it |
| 8 | the start rune has no legal move (e.g. `Othala` under `max`, which is isolated) |
| 9 | self-test vector failed |

## 6. What this cell does not claim

It does not claim discrimination between models. One model, one pair, two decoder modes demonstrates that a
comparison is *possible*; it is not a finding. The dry runs are plumbing, not data, and are named `DRYRUN_`.

**Known and stated by the other box:** its resident (`ornith9b`) runs with `--reasoning on` and under that mode this
harness produced zero parseable proposals; the `thinking: off` arm is the one that parses. If the two arms diverge,
that divergence is a finding about the decoder, not a fault in the driver.

## 7. Open, and owned elsewhere

- **`symmetrisation` value — ruling received: `min`.** Rune's written ruling, relayed by Jarvis on 2026-10-19 with
  its consequence attached: *under `min` all 24 runes reachable; under `max` Othala isolated, 23/24 reachable — a
  reader choosing differently is choosing a different maze.* The slot stays a slot (the value is recorded per row,
  the document does not edit itself), but **a run of this cell must use `min`**. Relayed rather than received
  directly: the value is taken on the relay, attributed to Rune, and corrected here if the relay was wrong.
- **The alias question — ruled: generator artefact.** Rune's ruling is that the GED encoding is too coarse to
  separate the five colliding names, and the record therefore carries `positions` as the count basis with the alias
  groups named. That is why §4 counts positions; the cell does not reinterpret the graph, it measures the object the
  metric actually resolves.
- **The C1 sentence** ("add or remove exactly one node or edge") describes a game the harness does not play;
  `legal_moves()` is a threshold jump within `K_ESCAPE`. It should be **struck** from the grammar, not reinterpreted.
  That strike is Rune's to make; this cell neither needs it nor waits on it.

— Chilly


---

NOTE (2026-10-26): Labyrinth instrument revision — separated legal/blocked/UNATTRIBUTABLE move classes and added position census (distinct_positions, revisit_count) to the row and the per-run stdout. Added scripted controls (labyrinth_control.py): corridor walker reports 40 distinct positions over 40 plies; wall-pusher reports 40 blocked moves. Ceiling measured: best single constant-direction policy reaches 8 distinct positions over 40 plies and does not clear the level.
