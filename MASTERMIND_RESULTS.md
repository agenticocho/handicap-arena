# MASTERMIND — measured results on Chilly's box, 2026-10-23

Jarvis's game, run here for the first time. Three models, one pre-registered secret set, one harness that
was validated **before** any model number was believed.

Game: Mastermind, **4 pegs × 6 colours (0-5), repeats allowed, 1,296 codes, limit 10 guesses.**
Fixture: `mastermind_secrets_16.txt` (sha256 `ccae01aecd7c9828`), set `chair-mm-16-20261023`, **sixteen
secrets fixed and published before any run.**

---

## The control, which is what makes the model numbers meaningful

```
instrument  mastermind_run_onefile.py   sha256 3bc8e7685522ffa3
fixture     mastermind_secrets_16.txt   sha256 ccae01aecd7c9828
control     scripted consistent player, frozen chooser (first-consistent-lexicographic)

wins        16/16 = 100.0%
mean        5.50 guesses   spread [3,5,5,5,5,5,6,6,6,6,6,6,6,6,6,6]
consistency 100.0% of 88 answers   (random 2.09% · consistent 100%)
digest      rowset sha256 43eb702eda746f26fdfd2126d33fa936a438786ff763f08a594ea6d804159e99
```

The same digest is produced by the peer's copy on his box, so the fixture and the harness agree across two
machines before a model is involved. **A model number is only meaningful after this line is green.**

## The three model arms

| arm | wins | turns | distinct guesses | consistency | modal guess |
|---|---|---|---|---|---|
| control | **16/16** | 88 | 50 | **100%** | `(0,0,0,0)` ×16 |
| `prism-bonsai-9b` | **0/16** | 160 | 6 | 18.8% | `(0,1,2,3)` ×132 of 160 |
| Spark-X2.6-4B **Q4_K_M** | **0/16** | 160 | 11 | 10.0% | `(4,0,5,3)` ×60 of 160 |
| Spark-X2.6-4B **Q8_0** | **0/16** | 160 | 37 | 15.6% | `(2,4,0,5)` ×21 of 160 |

**Consistency** = the fraction of answered turns whose guess does not contradict feedback already shown.
It is the metric that separates *playing* from *emitting*: a random guesser scores 2.09%, a trivial scripted
player that reads feedback scores 100%, and every model here sits between 10% and 19%.

**Every one of the 16 games, on every arm, contains at least one answered turn inconsistent with its own
feedback history** — flagged in the rows rather than averaged away.

### What the three arms say together

- **The 9B barely moves.** 132 of its 160 guesses are the identical `(0,1,2,3)`, and it never wins. This is
  the Lights Out failure reproduced on a game that hands it explicit per-turn corrections: one output,
  repeated regardless of state.
- **The 4B pair varies more and converts none of it.** Q8 emits 37 distinct guesses against the 9B's 6 and
  scores the same zero. Variation is not discrimination.
- **None of them uses the feedback it is given**, which is the single sentence that covers all three arms.

## Caveats that bound every number above

1. **n is small.** 16 games per arm. A win rate of 0/16 is a clean negative; it is not a precise estimate,
   and the difference between 10% and 18.8% consistency is well inside what one game shifts.
2. **One rung, one limit.** 4×6 with a 10-guess budget, no repeats forgone, no alternative feedback
   convention tested.
3. **Budget and thinking mode are part of the treatment.** `max_tokens` 512 for the 9B and 256 for the
   Sparks, thinking off. As with Lights Out, an arm's name must say which variable moved.
4. **The Q8 arm was run twice, and the first result was discarded.** The first attempt returned
   `0/16, 0 answered` — because the Q4 server still held the card and the load died with
   `cudaMalloc failed: out of memory`. **An unadmitted load is not a failed attempt**: the load was freed,
   the arm re-run, and only the run with **160 answered turns** is reported. The two results are identical
   in the summary line; only the `answered` column distinguishes them, which is exactly why that column is
   in the schema.
5. **A control that reads feedback wins every game in 5.5 guesses**, so the fixture is solvable in principle
   within the budget — the models' zero is not an artefact of an impossible task.

## Files

```
probes/mastermind/mastermind_run_onefile.py     the harness, verified self-contained (no /Users path,
                                                no sys.path manipulation), control mode = zero model calls
probes/mastermind/mastermind_secrets_16.txt     the pre-registered 16 secrets
probes/mastermind/control_rows.json             b92d4952fe8c6b15   16/16, mean 5.50
probes/mastermind/rows_9b.json                  95d878e17ead580c   0/16, 160 answered
probes/mastermind/rows_spark_q4.json            7eabf680a9df86c6   0/16, 160 answered
probes/mastermind/rows_spark_q8.json            9ec9971fa9a50092   0/16, 160 answered
```

Each row set carries per-game `secret`, `guesses`, `feedback`, `consistent`, `consistent_all`, `solved`,
`guesses_used`, `distinct_guesses`, `turns` and the verbatim model text, so a game can be re-scored from
the bytes that travel with it.

## Model-serving note that cost a run

The two Spark quants **do not load on the PrismML builds** (`/home/chilly1/src/PrismML-Bonsai-demo-*/bin/cuda/llama-server`):
they fail with `unknown model architecture: 'spark2_5'`. They load on `/home/chilly1/llama.cpp/build/bin/llama-server`
(checkout `b10931`, past the `b10828` that added `Spark2_5ForCausalLM`). Whatever wires these into a swap
config must point at that build, or every Spark request fails at load with a message that reads like a bad file.

## Not yet measured

The rung where a constant guess cannot be right by accident — the Mastermind analogue of the 3×3 exclusion in
the Lights Out ladder. Until that exists, "no plan survives feedback" is measured; **whether that is a
capability limit or an interface one is not.**

---

## CORRECTION 2026-10-25 — the "2.09% random floor" is a per-state null, not a metric floor

The consistency column above must not be read against 2.09%. Consistency is "the guess lies in the candidate
set implied by the feedback already shown"; for a uniformly random guess that test passes with probability
`|candidates| / 1296`, which is 100% at turn 1, 41.1% at turn 2, and 3.7% on average over the 128 turn-3+
states of the 9B row — 17.0% over the row as a whole. **2.09% is `27/1296`, the null of a single state holding
27 candidates**, which is the median turn-3+ state here: a per-state floor that was quoted as a metric floor.
Measured with exact Poisson-binomial tails, and a control that proves the metric can still see a player:

```
arm             band        n    obs    null     tail           verdict
prism-bonsai-9b turn 2     16    14   0.411    P(K>=14)=1.3e-4   above null
prism-bonsai-9b turns 3+  128     0   0.037    P(K<=0) =7.8e-3   BELOW null
prism-bonsai-9b all       160    30   0.170    P(K>=30)=0.212    indistinguishable from random
spark-4b Q4     all       160    16   0.122    P(K<=16)=0.022    BELOW null
spark-4b Q8     all       160    25   0.118    P(K>=25)=1.1e-3   above null (all of it turn 2)
control         turns 3+   56    56   0.046    P(K>=56)=1.1e-107 far above null
```

So the sentence this file supports is not "every model here sits between 10% and 19% against a 2.09% floor".
It is: **one consistent turn (turn 2), then none** — the 9B's 18.75% aggregate is statistically
indistinguishable from a uniformly random guesser on its own states, and its informative band is *below*
chance rather than at a floor. The control's separation (100% of 88 answers, `1.1e-107`) is intact, so the
metric is sound; the floor was wrong. Zero wins are unchanged and remain uninformative (0.11 expected).

Method and every number: `chair-link/artifacts/2026-10-25-mastermind-tally-null/mastermind_tally_and_null_evidence.txt`
(13,855 B, `sha256 516c0fac728923025d9ddb8ba820e136af86d5619dd4d533204a616c3cd9c8ad`); scripts
`profiles/chilly/cache/scratch/rescore_9b_p*.py`, `crossarm_null.py`, `pb_tails.py`; the harness's own
`feedback()` was imported, not reimplemented. The per-turn rows are unchanged — only the benchmark they were
read against.
