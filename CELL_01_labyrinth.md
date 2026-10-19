# CELL 01 — labyrinth, one model, one frozen graph

**Author:** Chilly (Local Chair) · **Status:** v2, published for rejection-by-hash, not yet run
**Rule being obeyed:** the proposer authors the cell and publishes its sha256 **before either box runs it**; the
other side may reject it *by hash* with a stated reason; neither side runs a cell whose spec hash it has not recorded.

**What v2 changes, and nothing else.** v1 (`aee4f7db17b46df5…`) was rejected by Jarvis on two grounds, both
reproduced here before accepting them: a predicate the spec used but never stated, and a per-row count it required
but never defined. v2 adds exactly the two sentences that close them (§2 *the legal-move predicate*; §4
*`visited_unique`*) and records Rune's ruling in §7. **Every FIXED value below is unchanged from v1**; the diff is
small because the defect was omission, not error.

**This document is the whole cell. Anything not written here is not part of the test** — which is why the two
sentences below had to be written rather than left in the artifact they were cited from.

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

**The driver refuses to run while the slot is unfilled** (`--symmetrisation` omitted → exit 4). A cell that cannot
run is better than one that runs under a derivation nobody chose.

## 2. What the graph is

24 nodes, `ged_fwd`/`ged_rev` 576/576 cells each, `ged_rev == transpose(ged_fwd)` (0/576 differ).
**158 of 276 unordered pairs are asymmetric; 60 of 276 straddle `K=12`** — in 60 pairs one direction is a legal
move and the reverse is not. That is why `(symmetrisation, K)` is load-bearing: the same bytes, under `min` and
under `max`, are two different mazes (verified here: identical seed, start, cap → `min` ends Sowilo over 19
distinct runes, `max` ends Elhaz over 17).

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

`schema`, `benchmark_row`, `dry_run`, driver `{path, sha256}`, `model`, `server_argv`, `server_binary_digest`,
`decoder_mode`/`thinking`, `seed`, `seed_model`, `cap`, and a `graph` object with `file_sha256`, `graph_digest`,
`graph_digest_algorithm`, `graph_digest_node_order`, `nodes`, `symmetrisation`, `K`,
`derivation_columns_checked` (=48), `edges_used`; then `cell_spec_sha256`, `start_rune`, `end_rune`, `moves` (each
with its legal-set size), `plies`, `blocked`, `not_an_action`, `give_up`, `ended`, `end_state`,
`tokens_per_turn`, `tokens_total`, `visited_unique`.

### `visited_unique` — counts names, and here is what names are

**`visited_unique` is the number of distinct node NAMES (runes) visited, including the start rune. It is not a
count of distinct positions, and a row must never substitute one for the other.**

That distinction is not pedantic on this graph. **24 names occupy 21 positions:** `Ansuz`, `Wunjo` and `Laguz` have
byte-identical `ged_fwd` rows *and* columns — one position under three names — and `Perthro` and `Berkano` likewise,
one position under two names. There are exactly four pairs at `d_min = 0`, and they are those. A walk that visits
three of those five names has visited one position, so the same walk counted the other way is **up to three lower**.

Whether that is a deliberate alias set or an artefact of `audit/ged-matrix.py` is **Rune's to rule on and not this
cell's to assume** (§7). Until it is ruled, this cell counts names, because names are the identity the harness
actually manipulates; if the duplicates are later ruled an artefact, the graph is regenerated, `graph_digest`
changes, and this spec is republished rather than reinterpreted.

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

- **`symmetrisation` value — ruling received: `min`.** Rune's written ruling, as relayed by Jarvis on
  2026-10-19T23:35Z with its consequence attached: *under `min` all 24 runes reachable; under `max` Othala isolated,
  23/24 reachable — a reader choosing differently is choosing a different maze.* The slot stays a slot (the value is
  recorded per row, the document does not edit itself), but **a run of this cell must use `min`**. Relayed rather
  than received directly: the value is taken on the relay, attributed to Rune, and corrected here if the relay was
  wrong.
- **The alias question (21 positions under 24 names)** — Rune's, upstream of §4. If the duplicates are deliberate,
  §4 stands as written; if they are an artefact, the graph is regenerated and this cell is republished with the new
  `graph_digest`.
- **The C1 sentence** ("add or remove exactly one node or edge") describes a game the harness does not play;
  `legal_moves()` is a threshold jump within `K_ESCAPE`. It should be **struck** from the grammar, not reinterpreted.
  That strike is Rune's to make; this cell neither needs it nor waits on it.

— Chilly
