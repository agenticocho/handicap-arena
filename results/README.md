# results/ — evidence bundles for FINDING 001

Every file here is a raw result bundle from `arena.py`. Each one carries its own full config
(`temperature`, `max_tokens`, `trials`, `ctx`, `n_gpu_layers`, and the **complete server command
line**) plus the **GGUF sha256**. Nothing here is a summary; these are the measurements.

## Naming convention — a filename must not lie

```
<model>_<serving>_ctx<N>_mt<N>.json
         ^^^^^^^^^         ^^     ^^
         neutral | GRAMMAR  context  max_tokens
```

**This convention exists because of the finding below.** During development, two bundles were written
for the *same model* with *identical filenames* and *different serving configs* — one scoring 0.33
and one 0.00. A reader browsing this directory would have had no way to tell which was which, and
would very reasonably have concluded the model was inconsistent. It wasn't. The filenames were.

The lesson generalises: **if a config can change the outcome, it belongs in the name.**

## The controlled pairs

### Pair A — the grammar (mechanism 1)

| file | serving | score | note |
|---|---|---|---|
| `LFM2-350M_neutral_ctx2048_mt3000.json` | neutral | **3/9 — Yellow** | sweeps R2 chess |
| `LFM2-350M_GRAMMAR_ctx2048_mt3000.json` | + `--grammar-file` | **0/9 — White** | **R2 chess 0/3** |

**Identical weights.** The grammar constrains output to `{contract_id, direction, magnitude,
reasoning}`, which makes a tool call **unrepresentable**. The model is not failing; it is forbidden
from succeeding. LFM2-350M falls from Yellow to White.

### Pair B — the context window (mechanism 3)

| file | ctx | score | note |
|---|---|---|---|
| `Qwen3.5-2B_neutral_ctx2048_mt3000.json` | 2048 | **3/9 — Yellow** | R1 and R3 hit the **context limit** |
| `Qwen3.5-2B_neutral_ctx8192_mt3000.json` | 8192 | **6/9 — Orange** | R3 passes; R1 now max_tokens-limited |

**Identical weights, identical `max_tokens`.** Doubling `--ctx` moves the model Yellow → Orange. A
reasoning model pays for its thinking from the same window as its answer, so `--ctx` is effectively a
cap on how much a model is allowed to think before it is graded.

## Reading a bundle: check `truncated` before believing a zero

Every round records:

- `wins` / `trials` — the raw record
- `finish_reasons` — `{stop: 3}` or `{length: 3}`
- `truncated` — true if any trial was cut off
- `ctx_limited_trials` — **how many attempts hit the context window rather than `max_tokens`**
- `why` — a plain-language verdict, distinguishing a *wrong answer* from a *cut-off answer*

**A round with `truncated: true` is not a capability result.** It is a measurement failure. The
harness says so in the `why` field, and names which of the two limits bit — because the first version
of that diagnostic always advised *"raise --max-tokens"*, which is wrong advice when `--ctx` is the
binding constraint. **A diagnostic that names the wrong cause is worse than no diagnostic.**

## Regenerate anything here

```bash
# neutral
python3 ../arena.py --model model.gguf --ctx 8192 --trials 3 --max-tokens 3000

# constrained (mechanism 1)
python3 ../arena.py --model model.gguf --ctx 2048 --trials 3 --max-tokens 3000 \
                    --extra-flags '--grammar-file some.gbnf'

# then review belts / run the biathlon
python3 ../arena.py --grade results/whatever.json
python3 ../arena.py --biathlon results/*.json --penalty-k 1.0
```

If a bundle here cannot be reproduced from its own recorded config and sha256, that is a bug worth
filing — it would mean the harness is measuring something it does not record.
