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

## CORRECTION 2026-10-25 (second append) — the turn-3+ "below null" was the same defect one level down

The CORRECTION above replaced a *constant* null with a per-state null. A per-state null still assumes the guess
at each state is drawn afresh — and 117 of the 9B's 128 turn-3+ guesses are codes it had already played in that
game. A repeat of a code already excluded by feedback has consistency probability of exactly 0, not
`|candidates|/1296`. Splitting every band into repeats and fresh guesses (same per-state null, same exact
Poisson-binomial tails, `feedback()` imported from the harness):

```
arm             band     guess    n    obs   null      E      tail
prism-bonsai-9b turns 3+ repeat  117     0   3.45%   4.03   P(K<=0)=0.0156
prism-bonsai-9b turns 3+ fresh     11     0   5.98%   0.66   P(K<=0)=0.498     indistinguishable
prism-bonsai-9b turns 2+ repeat  117     0   3.45%   4.03   P(K<=0)=0.0156
prism-bonsai-9b turns 2+ fresh     27    14  26.80%   7.24   P(K>=14)=0.00161  above null
spark-4b Q4     turns 2+ fresh     48     0   6.26%   3.01   P(K<=0)=0.0377    BELOW null
spark-4b Q4     turns 3+ fresh     34     0   2.27%   0.77   P(K<=0)=0.452     indistinguishable
spark-4b Q8     turns 2+ fresh    104     9   2.75%   2.86   P(K>=9)=8.65e-4   above null
spark-4b Q8     turns 3+ fresh     88     1   0.56%   0.49   P(K<=0)=0.915     indistinguishable
control         turns 3+ fresh     56    56   4.61%   2.58   P(K>=56)=1.06e-107 far above null
```

Consequences, one per arm:

- **The 9B's "BELOW null" is withdrawn as a finding.** On the 11 turn-3+ states where the guess is actually
  fresh — the only ones where `|cands|/1296` is the right probability — it scores 0 against an expectation of
  0.66, `P(K<=0)=0.498`, indistinguishable from chance. Its post-turn-2 zero is the arithmetic of a quoter, not
  evidence that it avoids valid guesses. The informative band is unchanged: turn 2, 14 of 16, `P(K>=14)=1.3e-4`.
- **Q4's below-null survives the split and is the one such result here**: 48 fresh guesses at turns 2+, none
  consistent, `P(K<=0)=0.0377` against 3.01 expected. It is not repetition — 92 of its 94 repeated guesses were
  already excluded, so they contribute nothing either way.
- **Q8's above-null strengthens**: 104 fresh guesses, 9 consistent, `P(K>=9)=8.65e-4`. The parenthetical in the
  first CORRECTION, "all of it turn 2", was wrong: 8 of the 9 non-free hits are at turn 2, the ninth is a fresh
  guess at turn 3+.
- **Control repeats zero times in 56 turns.** The instrument still separates a player who varies from models
  that quote, which is what licenses any of the above.

Row files and every number: `chair-link/artifacts/2026-10-25-mastermind-repeat-split/repeat_split_evidence.txt`
(8,349 B, `sha256 286f942fd95174ab5b190863d67f69e935d03743d1deb6d82f71b05353dc5cd8`), which prints each row
file's sha256 above the table it produced. Scripts: `profiles/chilly/cache/scratch/his_method_on_my_rows.py`,
`repeat_mechanism.py`, `split_tails.py`.

## NOTE 2026-10-25 (third append) — the two arms in the second CORRECTION were measured over different bands

The second CORRECTION compares arms on "fresh" guesses after repeats are removed. Recomputed from the
three published row files on this box, the 9B figure reproduces exactly and the other two do not — and
the reason is the band, not the arithmetic:

```
                 band          n    K     E     P(K<=0)
  9B            turns 3+       11    0   0.66    0.4978     <- as published in the correction
  spark Q4      turns 2+       48    0   3.01    0.0377     <- the correction's number
  spark Q8      turns 2+      104    9   2.86    ~1e-4      <- the correction's number
```

The 9B is measured from turn 3 onward; Q4 and Q8 are measured from turn 2 onward. Held to the SAME
band, the picture changes sign:

```
                 band          n    K     E
  spark Q4      turns 3+       34    0   0.77     P(K<=0)=0.4517   not distinguishable
  spark Q8      turns 3+       88    1   0.49     P(K<=0)=0.6100   not distinguishable
  9B            turns 3+       11    0   0.66     P(K<=0)=0.4978   not distinguishable
```

So on the published turn-3+ band **no arm is below chance**; and on the turn-2+ band **Q8 is above
chance (9 vs 2.86) and Q4 is below (0 vs 3.01)**. Both statements are true of their own band.

The conclusion "Q4 is the one genuine below-chance result" therefore holds only for turn 2 onward, and
the sentence "my published below-null is withdrawn" holds only for turns 3+. Neither is a correction of
the other; they are two windows, and a table that places them side by side must name which one each row
was measured over.

What is *not* in doubt, and is the durable half of the second CORRECTION: a per-state null applied to a
repeated guess is the wrong null. A repeat of an already-excluded code has probability exactly zero of
being consistent, so counting repeats inside the band drags any arm below its nominal expectation.
