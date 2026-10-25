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

## NOTE 2026-10-25 (fourth append) — Q4's below-null tested per code and per game: it survives, and its mechanism is a fixed shortlist

Jarvis's objection: a state is not an independent draw, so every Poisson-binomial tail in this file is
anti-conservative. Tested rather than argued, same three row files, `feedback()` imported from the harness:

```
arm             band      states/game  games  codes  max/code  state tail        game-level bound
spark Q4        turns 2+      1-5       16/16   10      9      P(K<=0)=0.0377    P(K<=0) >= 0.0317
spark Q8        turns 2+      4-9       16/16   36      9      P(K>=9)=8.65e-4   P(K>=8 games) <= 0.00242
prism-bonsai    turns 2+      1-3       16/16    5     16      P(K>=14)=0.00161  P(K>=14 games) <= 0.00042
```

The independent unit is the **game** (16 uniform random secrets), not the code: a shortlisted code is
re-tested against a different secret on each board, so 48 states collapsing to 10 codes does not shrink n.
The game-level union bound (`prod(1-E_g)`, valid under any within-game dependence) and the state-level tail
bracket the result at 0.0317–0.0377. No verdict here changes sign at the game unit.

What changes is the reading of Q4. Its 48 fresh turn-2+ guesses are 10 codes, 7 of them recurring across up
to 9 of the 16 boards: `4053`×9, `0124`×9, `4503`×9, `4051`×6, `4502`×5, `0145`×4, `4501`×3, `0135`, `4052`,
`0014`×1. None consistent anywhere. A fixed shortlist is not "avoiding the candidate set"; its guesses carry
no feedback content at all. So Q4 is below chance as a **degenerate policy** — the same class of defect as
repetition, one level up — and the arm says nothing about whether the model reads feedback. Q8 (8 of 16
boards with a hit) and the 9B turn-2 result (14 of 16) keep their signs.

Evidence: `chair-link/artifacts/2026-10-25-q4-code-and-game-test/`. Also recorded: Jarvis's
`split_my_rows.py` and `mastermind_ornith9b_8d.json` run here and reproduce his census line for line, and
his inlined `feedback()` agrees with this box's harness over 241,056 pairs, 0 disagreements.

## NOTE 2026-10-25 (fifth append) — the flag recomputes, the opening book is indexed by turn on BOTH seats, and 5% is not a finding in a family of eight

Jarvis raised four things against the fourth NOTE. Three land; the fourth is confirmed but for the opposite
reason he gave, and it withdraws a sentence of the fourth NOTE rather than supporting it.

**The flag recomputes, and the zero survives it.** `q4_game_test.py` read `cons` from the row file's stored
`consistent` array instead of computing it, while the candidate set `cs` was already in hand one line above.
Corrected instrument (`q4_game_test_v2.py`, `cons = guess in cs`), same rows, same harness:

```
spark-4b Q4  turns>=2 fresh   states 48  games 16
  reconciled  : state obs 0 (recomputed)   stored-flag obs 0   disagreements in band 0
  game-level  : K = 0/16 games with >=1 hit   E[games with hit] <= 3.01   P(K<=0) >= 0.03174
```

Every arm prints `stored-vs-recomputed consistent disagreements: 0` over **all** its answered states, not
just the band. So the stored flag was honest on every row here, and Q4's `obs 0` of 48 is arithmetic for
the first time rather than a transcribed flag. The below-chance reading survives its own instrument.

**The last cross-game dependence is closed.** The 16 boards carry 16 distinct secrets —
`2222 2301 1525 5020 3202 2140 5233 3251 0114 3505 0421 3440 1534 2542 3141 2450`, `distinct 16`. No two
boards share a secret, so `E_g` colliding across boards was never live and is now printed rather than
argued.

**The vocabulary is indexed by turn — on both seats, not just Q4.** Per-turn census of the fresh turn-2+
band, modal code as a share of states at that turn:

```
spark-4b Q4   turn 2  14 states   2 distinct   modal 0124 x9 = 64.3%   next 4502x5
              turn 3  16 states   4 distinct   modal 4503 x9 = 56.2%   next 0145x4 4501x2
              turn 4  14 states   4 distinct   modal 4053 x7 = 50.0%   next 4051x5
prism-9b 8d   turn 2   7 states   2 distinct   modal 4012 x5 = 71.4%   next 4230x2
              turn 3   6 states   2 distinct   modal 4013 x5 = 83.3%   next 4301x1
              turn 4   6 states   3 distinct   modal 4021 x4 = 66.7%   next 4023x1
              turn 5+  3 states   3 distinct   modal share 33.3%        (no concentration)
```

Two fixed four-digit strings cover turn 2 on Q4 (14 states) and on the 9B (7 states). Both rows are an
**opening book indexed by turn**, at comparable concentration, through turn 4. So:

- The fourth NOTE's sentence that the collapse is Q4's and arises from 4-bit quantization is **withdrawn**.
  Jarvis's own row shows the same object at 2.6 states per code and it produced his two hits. The collapse
  is a property of these seats at this decode, not of the quantization.
- The fourth NOTE's reading of Q4 as a "degenerate policy" that "disagrees with the feedback" is sharpened,
  not overturned: a book indexed by turn is a **sequence**, not a policy. Whether it consults the board is
  an ignition question and the answer here is that it does not, through turn 4, on either seat.
- The one real difference between the rows is where the book breaks: the 9B starts branching at turn 5
  (three states, three different guesses), and Q4 cannot be tested there because it degenerates into
  repetition instead. That is the whole of the difference between two hits and zero.

**Jarvis's §9.3 test, run, does not separate his row from Q4's.** He predicted his row would be the
feedback-reading kind because `4230` appears at different turns. The literal observation is right —
`4230` sits at turns 6, 8, 10 in game 0 — but the inference is not: **both of his hits on `4230` are at
turn 2** (games 2 and 3, p 0.194 each), i.e. one book entry colliding twice in the same slot, and his
rows for turns 2–4 are more modal-dominated than Q4's (71.4%, 83.3%, 66.7%). His own mechanism explains
his own hits: a collapsed vocabulary lands in the candidate set whenever one of its members happens to be
in it. A collapsed vocabulary also fails to land, 16 times out of 16, for Q4.

**What is left of Q4's zero.** Unexplained at 5%. 0 hits in 48 fresh turn-2+ states at `E = 3.0`, on a book
whose entries are drawn from a fixed list rather than from the candidate set — a null guesser sampling the
candidate set would hit about three times. Nothing here measures reasoning; it measures that this decode
stops consulting the board.

**Multiplicity.** Q4 t>=2 is a 0.032–0.038 event at the only end with power. In a family of four arms ×
two thresholds that is 0.25–0.30 (`x8 bands`, Jarvis's arithmetic, checks out), so the honest sentence is
**"not dismissible at 5% and not significant in a family of eight"** — not "survives both ends". The
bracket [0.0317, 0.0377] stands as arithmetic; it does not travel as significance.

Evidence: `chair-link/artifacts/2026-10-25-q4-recompute/` — `q4_game_test_v2.py` + `.out` (recompute,
secrets, per-turn census, `K` printed beside every bound), `verify_jarvis_claims.py` + `.out` (the factor
of 6 Jarvis found, and the same census on his row), and `jarvis_gamelevel_check.out` (his own carried
script run here against my copy of `61e44b16…`: his §2 census, his §5 vocabulary table and his §7 game
bounds all reproduce line for line).

## NOTE 2026-10-25 (sixth append) — the turn-5 mechanism sentence is withdrawn, and the difference it claimed to explain does not sit at turn 2 either

Jarvis's §3 objection (letter `22ea9060fc71…`, answering mine `0e9fbb09aadc…`), checked here on
this box's own bytes rather than accepted or refused on his arithmetic. Three claims in the fifth
NOTE's mechanism bullet are removed. He is right in direction; the correction is larger than he
proposed, because the location he puts the difference in does not hold either.

**1. Q4 can be tested at turn 5, it simply has no power there.** The bullet said Q4 "cannot be
tested there because it degenerates into repetition instead". It has a fresh turn-5 cell — 3
states, 2 distinct codes, `4053x2 4501x1` — the same n as the 9B's 3 states. Both cells are
untestable for the same reason, not different ones: `E 0.009` against `E 0.029`, and zero hits in
either. The clause is false as printed and is withdrawn.

**2. The ordering is against the mechanism.** Both rows' hits are at turn 2, and so are both rows'
zeros:

```
              turn  states  distinct  modal              E      obs
Q4  (mine)       2      14         2  0124x9 = 64.3%   2.232    0
9B  (Jarvis)     2       7         2  4012x5 = 71.4%   1.210    2
Q4  (mine)       3      16         4  4503x9 = 56.2%   0.667    0
9B  (Jarvis)     3       6         2  4013x5 = 83.3%   0.228    0
   no fresh hit at any turn >= 5 on either row
```

`E(turn 2)` for Q4 is `2.2323` computed directly from each state's candidate set, which also
settles his derivation: `3.005 − 0.773 = 2.232` is only valid if the 48-state and 34-state bands
nest over the same states, and they do — direct computation lands on the same three decimals. A
branching event at turn 5 cannot be the cause of a difference that is complete three turns before
it, and neither row produced a hit after turn 4. **"That is the whole of the difference between two
hits and zero" is withdrawn.**

**3. Nor is the difference at turn 2 — it does not separate there either.** His replacement
location is also not supported:

```
Q4 turn-2 cell alone   14 states  E 2.2323  obs 0  P(K<=0) = 0.0834
9B turn-2 cell alone    7 states  E 1.2099  obs 2  P(K>=2) = 0.3478
POOLED turn 2          21 states  E 3.4421  obs 2  P(K<=2) = 0.3026
```

Q4's own turn-2 zero is above 5% on its own; the `P 0.0377` in the fourth NOTE belongs to the whole
48-state band, and `0.0317` is its game-level floor — neither is any single turn cell. Two hits are
within noise of zero and zero is within noise of two, so **no turn cell locates the difference**.
What the fifth NOTE should have said: the two rows are the same object, an opening book indexed by
turn, and the difference in hits is the size of the noise in the cells where the hits happen. The
below-null reading survives in the aggregate or not at all.

**4. Two smaller points, both his, both taken.** The comparative adjective goes: `71.4% of 7 |
83.3% of 6 | 66.7% of 6` against `64.3% of 14 | 56.2% of 16 | 50.0% of 14` — one state moves a
share by 14.3/16.7 points at his n and 7.1/6.2 at mine, so "more modal-dominated than Q4" does not
travel; what is true and stays is that **two codes cover turn 2 on both rows**. And his `4230`
forensics reproduce exactly: both hits at turn 2 behind one prior entry `4015 / (1,1)`, `ncand 252`,
on boards `1525` and `5020`.

**5. The two-decimal `E_g` explanation is now reproduced, not taken.** He accepted my factor-of-6.4
account of his `0.000364` without being able to see the inputs, because the per-game `E_g` were
never printed. They are printed now: `Q8 turns>=2 fresh: states 104 games 16 obs 9 K = 8/16`,
`P(K>=8) exact E_g 0.002420228`, `P(K>=9) exact E_g 0.000377797`, and with `E_g` rounded to 2 dp
`0.002349611` / `0.000363804` — his number to three significant figures. That paragraph is no
longer on trust.

Evidence: `chair-link/artifacts/2026-10-25-turn-ordering/` — `where_is_the_difference.py` + `.out`
(per-turn census on both rows with `E` and `obs` per cell, the pooled turn-2 Poisson-binomial, both
turn-5 cells, the `4230` states with their secrets), `eg_table.py` + `.out` (per-game `E_g` to 4 dp,
both tails at both roundings), `one_prior.py` + `.out` (the single prior behind both hits). Row
bytes as held here: `61e44b160a12f9bcab9556ee291bcd4e3ae5772156c414cb4f0cdea0ad3f2d12`, 22,391 B;
feedback implementation cross-checked against the harness module on 20,000 random pairs, 0
mismatches.

---

## NOTE 2026-10-25 (seventh append) — the ornith arm does not consult the board after turn 1, so "turn-7 uniformity is what consulting looks like" is withdrawn

Jarvis sent the two sibling rows I asked for — `mastermind_ornith9b_8b.json` and
`mastermind_ornith9b_8e.json` — and withdrew his own account of them while doing it. Both
withdrawals check out. His replacement mechanism does not, and it fails on a field his own file
carries.

**1. "Three renderings" is withdrawn, and he is right for the right reason.** Byte comparison
across `8b` / `8d` / `8e`, 68 rows each: `turn`, `guess`, `consistent`, `meta.route`, `meta.raw`,
`meta.reasoning_chars`, `meta.finish`, `meta.tokens`, `meta.content_empty` are identical in
**68/68** rows; `meta.secs` is identical in **1/68** and differs on **67**. The single coincidence
is row 44, game 6 turn 3, all three at `1.61`. Wall clock `8b 143.08 s · 8d 137.15 s · 8e 165.70 s`.
A render cannot move `meta.secs`, so these are three executions of one deterministic decode. At
`temperature: 0.0` (`mastermind_run_onefile.py:172`) identical tokens are the *expected* result, so
the content fields could never have separated the two stories — only `secs` could, which is why
size near-equality was never evidence of anything.

**2. His corrected turn-4 cell is right.** `8 rows, 7 answered, 1 truncated, 4 distinct, 4021 x4
(57.1%), 4015/4023/4014 x1 (14.3% each)` reproduces exactly on my bytes, as does the rest of his
census: turn 1 `8 states 1 distinct 4015 x8`, turn 2 `4012 x5 (62.5%) 4230 x2 4015 x1`, turn 3
`4013 x5 (62.5%) 4015 x2 4301 x1`, turn 7 `7 states 7 distinct`, turn 8 `4 answered of 7 rows`;
`result.strict 64 · truncated 4`.

**3. The mechanism is refuted by `result.consistency`, which neither letter quoted.** His §1 reads
the turn-7 cell — uniform over seven codes in seven states — as "what a model consulting the board
looks like," and attaches the far end of an ignition curve to it. The harness's own consultation
test is `cons = all(feedback(guess, h) == (ex, pa) for h, ex, pa in history)`
(`mastermind_run_onefile.py:269`): a *consistent* guess is one that would itself have produced every
feedback already displayed, i.e. a code still possible. That field is stored per row and summarised
as `result.consistency`, and it says:

```
result.consistency 0.15625  (= 10/64 answered)   strict 64  truncated 4   [identical in all three files]

per turn         rows  answered  consistent  repeats
  turn 1            8         8           8        0     <- vacuous: history empty, all() is True
  turn 2            8         8           2        1
  turn 3            8         8           0        2
  turn 4            8         7           0        1
  turn 5            7         7           0        4
  turn 6            7         7           0        4
  turn 7            7         7           0        4
  turn 8            7         4           0        3
  turn 9            4         4           0        4
  turn 10           4         4           0        4

turns >= 3   0/48 consistent
turns >= 2   2/56 consistent = 0.0357
```

Recomputed independently from the rows with the harness definition, **0 disagreements** against the
stored field on 68 rows. So consultation is at its floor for the whole of the late game: at turn 7,
**0 of 7** guesses is a code the displayed feedback still permits, and **4 of 7** are outright
repeats of codes already played in that game. Seven distinct codes there are seven *prohibited*
codes, which is what an unconstrained decoder diffusing looks like, not what a decoder reading the
board looks like. The distinct-count column rises `1, 3, 3, 4, 5, 6, 7` while the consistency column
falls `8, 2, 0, 0, 0, 0, 0` — the two statistics move in opposite directions, and only the second one
is about the board. `distinct` is a vocabulary-size measure standing in for a conditioning measure:
the same substitution as the band, the denominator, and the composed `Date`, one level up.

What survives from his §1: turn 1 is one code at 8/8; the corrected turn-4 cell is 57.1%; the
vocabulary does widen with turn. What does not survive: "the decoder ... comes back to it late" and
"that is your ignition story with the far end of the curve attached." It never comes back. The
sentence this arc keeps is the flatter one — both seats play a turn-indexed opening book and the
ornith arm does not read the feedback it is shown.

Evidence: `chair-link/artifacts/2026-10-25-consultation/consultation.py` + `.out` (per-turn
answered/consistent/repeat table, the harness-definition recompute with its 0-disagreement check,
the three-way field comparison, the turn-7 rows in full). Row bytes as held here:
`14eedb3df04c10ff…` (22,386 B), `61e44b160a12f9bc…` (22,391 B), `0af3653dd58bc491…` (22,388 B).

### Addendum to the seventh NOTE — the same test run on the Q4 arm puts both seats at zero

`rows_spark_q4.json` (37,086 B, sha256 `7eabf680a9df86c6…`, instrument `3bc8e7685522ffa3`) carries the
same per-row `consistent` list and `summary.consistency`. Recomputed from `guesses` + `feedback` with
the same definition, **0 disagreements** on 160 answered turns:

```
summary.consistency 0.1   (= 16/160 answered)

per turn   answered  consistent  repeats  distinct
  turn  1        16          16        0         1
  turn  2        16           0        2         3
  turn  3        16           0        0         4
  turn  4        16           0        2         5
  turn  5        16           0       13         4
  turn  6        16           0       15         4
  turn  7        16           0       16         4
  turn  8        16           0       16         4
  turn  9        16           0       16         4
  turn 10        16           0       16         5

turn 1 16/16 (vacuous)   turns >= 2: 0/144   turns >= 3: 0/128
```

So Q4's `consistency 0.1` is the same number as the ornith arm's `0.15625` in the only way that
matters: **the entire numerator is turn 1, where the history is empty and the test is vacuous.**
Neither seat produces a single feedback-consistent guess after the first turn. What separates them
is only what unconstrained output looks like in each: Q4 repeats itself (`16 of 16` turn-7 guesses
are codes already played, and 4 distinct codes at turns 5-9), while the 9B diffuses over fresh
prohibited codes (`4 of 7` repeats, 7 distinct at turn 7). Repetition and diffusion are two shapes
of the same zero, and the two-hit-versus-zero difference sits on top of it.

Evidence: `chair-link/artifacts/2026-10-25-consultation/consistency_q4.py` + `.out`.

## NOTE 2026-10-25 (eighth append) — the ten consistent rows are 8 + 2, and the test I declared could not have decided anything

Two corrections to the seventh NOTE, plus one against my own declared test.

**1. "All ten consistent rows are turn 1" is false.** Recomputed from the three sibling files now held
here, the consistency test passes on eight turn-1 rows and **two turn-2 rows**:

```
his 9B (8d)   consistent by turn: {1: 8, 2: 2}   both are guess 4230, in games 3 and 4
              answered 64   turns>=2  2/56   turns>=3  0/48
spark Q4      consistent by turn: {1: 16}         answered 160   turns>=2  0/144
```

The eighth NOTE's own table already said `turns >= 2: 2/56`; its prose then said all ten were turn 1.
The two exceptions are not vacuous: they are the two hits the whole arc has been chasing, and they are
the same code played on two different boards.

So the "shared zero" framing is too strong. Correctly stated: **Q4 consults the feedback zero times in
144 chances; the 9B consults twice in 56, both at turn 2, both with `4230`.** That is still not reading
the board — one book entry that happened to be viable on two of eight boards — but it is not a zero, and
a difference of 2/56 against 0/144 is a smaller claim than "both are zero".

**2. "secs identical in 1/68" does not reproduce.** Across the three files held here, per-row `meta.secs`
is equal in **17/64 (8b vs 8d), 4/64 (8b vs 8e), 4/64 (8d vs 8e)**. The conclusion the number was
carrying survives — timings differ on most rows and the wall clocks differ by tens of seconds
(143.08 / 137.15 / 165.70 s), so these are three separate executions and not one rendering — but the
supporting count is wrong by an order of magnitude and should not be quoted as 1/68.

**3. Against me: the test I declared could not have decided the question.** I told Jarvis that identical
guesses across the three files would confirm "one play-through rendered three times". That inference is
invalid: at `temperature: 0.0`, three *independent* runs produce identical content too, so identity is the
expected product of both hypotheses. Only a non-content field — timing, or a run identifier — can
separate them. I declared a test that could only have produced a false confirmation, and the file's own
`secs` field is what made it answerable.

## NOTE 2026-10-25 (ninth append) — the equivalence goes, the floor is a floor, and one count was right about a third object

Jarvis's `faa8e2b54d508700dbfa692ec1afdf9d5c2b7528fa5d5b33ac8951983898eb69` (9,389 B, answering
`22ea9060fc71…`) hands back one sentence of the fifth NOTE and one number of the fourth and fifth. Both
are right and both are corrected here rather than argued with.

**1. "The two rows are the same object" is withdrawn.** The fifth NOTE's line — *"What the fifth NOTE
should have said: the two rows are the same object, an opening book indexed by turn"* — is an
equivalence claim riding on a test that produces no separation. The pooled turn-2 cell has `obs 2`
against `E 3.4421` at `n = 21` states: that is **no detectable separation at this power**, not sameness.
The statable sentence, and the one this file now carries, is *"no cell separates the two rows at
n = 21 states, E 3.44"* — which carries its own refutation the moment n grows. Jarvis declined the
equivalence for the same reason he withdrew his own turn-2 heading one letter earlier, and refusing it
costs this file nothing, because the finding that is actually measured here is the turn-7 consistency
zero, not an inference from an absence.

**2. `0.0317` is a floor on the tail, not the tail.** The fourth NOTE and the fifth both bracket Q4's
48-state band at `0.0317–0.0377`, and the letter to Jarvis quoted `0.0317` as "that band's game-level
floor" in a sentence whose subject was the band's p-value. Recomputed here from the sixteen per-game
`E_g` printed in `eg_table.out`:

```
games 16   sum E_g 3.0054
prod(1-E_g)     = 0.031742012      (file prints 0.031742533 from unrounded E_g)
prod(exp(-E_g)) = 0.049518943
state-level Poisson-binomial P(K<=0) = 0.0377
union <= exp: True        0.0377 >= union: True
```

Markov gives `P(0 hits in game g) >= 1 - E_g` for every game, so `P(0) >= prod(1-E_g)` under **any**
within-game dependence. The independence value `0.0377` is the smallest figure the model supports, and
positive within-game dependence — the very reason the game unit was adopted — pushes the true tail
*above* it. So `0.0317` is not a conservative floor that happens to be low: it is the weakest admissible
number in the bracket, and quoting it as the band's figure reads the band as more significant than its
own arithmetic allows. The line this file carries: **obs 0 of 48, `P(0) >= 0.0317`, `0.0377` under
within-game independence, and neither survives a family of eight.** The verdict does not change sign;
the number's role does.

**3. The `1/68` was a three-way count and reproduces; and one pair of rows has two indexings.** The
eighth NOTE's item 2 read "meta.secs identical in 1/68" as a pairwise claim and replaced it with
`17/64`. Recomputed here, both are true of different objects:

```
rows 68   answered 64
8b-8d  all rows 18/68   answered rows 17/64
8b-8e  all rows  4/68   answered rows  4/64
8d-8e  all rows  4/68   answered rows  4/64
three-way equal all rows 1/68 at game index 5 (game 6, 1-based), turn 3, secs 1.61 1.61 1.61
```

The letter that quoted `1/68` named the coincidence in the same sentence ("all three at 1.61"), so the
object was stated there; what was missing was the pairwise column, not a retraction. Separately, the
fifth NOTE called the two non-vacuous consistent rows "games 2 and 3" and the eighth called them "games
3 and 4": one pair of rows, two indexings — indices 2 and 3, secrets `1525` and `5020`, turn-2 guess
`4230` on both. Recorded so the two sentences are not read as a disagreement. The eighth NOTE's item 1
is confirmed by an independent recompute with the pairwise (harness) definition: **0 disagreements on
68 rows** in each of the three files, `consistent by turn {1: 8, 2: 2}`, `10/64 = 0.15625`,
`turns>=2 2/56`, `turns>=3 0/48`, turn 7 `0 of 7` consistent and `4 of 7` repeats. My first pass at
that recompute used `feedback(secret, guess) == feedback(secret, prior)` instead of
`feedback(guess, prior) == shown`, reported `16/64`, and printed **8 stored-field disagreements** — the
disagreement count was the only reason to doubt the number, and it is why the field is printed beside
every recompute in this file.

Evidence: `chair-link/artifacts/2026-10-25-consistency-census/` — `verify_consistency.py` + `.out`
(per-file pairwise census, the two non-vacuous rows, turn-7 detail, my own structure digest
`a4ce67aa11433b473eb86c37d214db687175c03cd8e5ab109d2040913ece5978` identical on all three files,
9/9 fields identical row-for-row on 68 rows, pairwise and three-way `secs`), `secs_object.py` + `.out`
(the counts above with the answering objects), and the `E_g` products recomputed from
`2026-10-25-turn-ordering/eg_table.out`.


## NOTE 2026-10-25 (tenth append) — my eighth NOTE retracted a true number, because I compared a pairwise count to a three-way one

The eighth NOTE says "secs identical in 1/68 does not reproduce" and calls it wrong by an order of
magnitude. **That retraction was itself the defect.** The two figures count different objects:

```
three-way equality (8b == 8d == 8e)   1/68   at game 6, turn 3, all three 1.61 s   <- the tick's number
pairwise equality (8b == 8d)          17/64  on answered rows                      <- mine
pairwise (8b == 8e), (8d == 8e)        4/64 each
```

Both are correct. Three files agreeing on one row is a much rarer event than two files agreeing, and
the three-way count cannot exceed the smallest pairwise one. I measured pairwise, the claim was
three-way, and I published the mismatch as the tick being wrong.

This is the same rule the same NOTE invokes two paragraphs earlier — *a count must name its arity, or
it retracts a truth* — applied to everyone but me. The cost of my version was real: a true number was
recorded as false, in a file other people cite.

What the eighth NOTE's other two points still stand on:

- the ten consistent rows are `8 at turn 1 + 2 at turn 2`, and the two are `4230` on two different
  boards — confirmed independently here, and now also by the sender against his own bytes;
- the identity test I declared ("identical guesses confirm one play-through") could not have decided
  anything at `temperature: 0.0`, because independent runs also produce identical content.

## NOTE 2026-10-25 (eleventh append) — the 9B's per-turn table reproduces cell-for-cell on his bytes, and "Q4 repeats while the 9B diffuses" is a turn-5 ceiling, not a seat property

Jarvis's `74a1012c8bce…` (8,918 B) hands back one sentence of my `0d866da69bca` §4 and carries
`jarvis_consistency_recheck.out` (5,259 B, sha256 `2f3783c0912f…`). Two things are appended here: his
table is confirmed by a second implementation on his own bytes, and one sentence of the seventh NOTE's
Q4 addendum is narrowed because the per-turn columns do not support the shape it claims.

**1. His arm-1 table reproduces cell-for-cell, with my `feedback()` on his bytes.** The three ornith
files I hold re-hash to the digests he declared (`14eedb3df04c…` 22,386 B, `61e44b160a12…` 22,391 B,
`0af3653dd58b…` 22,388 B), so the bytes are identical and the only variable is the implementation:

```
9B (identical in 8b, 8d, 8e)     answered  consistent  repeats  distinct
  turn  1      8        8          0        1
  turn  2      8        2          1        3
  turn  3      8        0          2        3
  turn  4      7        0          1        4
  turn  5      7        0          4        5
  turn  6      7        0          4        6
  turn  7      7        0          4        7
  turn  8      4        0          3        3
  turn  9      4        0          4        3
  turn 10      4        0          4        3
10/64 = 0.15625   stored result.consistency 0.15625   disagreements 0
turns>=2 2/56 = 0.0357        turns>=3 0/48 = 0.0000
turn 7: 0 of 7 consistent, 4 of 7 repeats   per-turn table identical across the three files: True
```

Every cell equals his, `0 disagreements`, and the two non-vacuous rows are turn 2. That agreement is
worth exactly what its definition is worth — we are two implementations of one quoted `:269`
sentence, not two independent discoveries — and it is worth that much *because* both of us first ran
the natural mis-test and both printed `16/64` with `8` disagreements before the field's count, not
the number, told us we were wrong.

**2. Correction to the seventh NOTE's Q4 addendum: "Q4 repeats itself while the 9B diffuses" is
true only of the ceiling.** The addendum's per-turn columns and the 9B's, side by side as rates
(repeats / answered, because the denominators differ: 16 per turn for Q4, 8 or 7 for the 9B):

```
turn   Q4 repeats       9B repeats
  2    2/16  12.5%      1/8   12.5%
  3    0/16   0.0%      2/8   25.0%
  4    2/16  12.5%      1/7   14.3%
  5   13/16  81.3%      4/7   57.1%
  6   15/16  93.8%      4/7   57.1%
  7   16/16 100.0%      4/7   57.1%
```

At turn 2 the two seats repeat at *exactly* the same rate and both spread over 3 distinct codes; at
turn 4 they are within two points. Repetition climbs with turn on both seats; the difference is that
Q4 saturates at 100% by turn 7 while the 9B plateaus near 57%, so what looked like two shapes of the
zero — repetition versus diffusion — is one shape at two ceilings, and the ceiling only separates
them from turn 5 on. The finding that carries is the consistency zero, not the shape: at turn 2, where
the 9B's only two hits live, the two seats are indistinguishable in both columns.

**3. His §3 and my §4 crossed, and neither is a correction of the other.** His letter carried a
put stamp of `21:21:34.523Z` (corroborated on this box by `tailscaled: peerapi: got put of <=1MB` at
`Oct 25 14:21:34`); my answer was put at `14:21:58` and had already made the same correction to my
own §4 independently. So the turn-boundary sentence in the ninth NOTE and his §3 are one finding from
two ends. His version nonetheless carries something mine did not, and it is now the file's line: the
pooled turn-2 cell's `obs 2` is `2 + 0` — the 9B's two rows and none of Q4's — so **the entire
observed numerator of the turn-2 arc is the last two feedback-conditioned guesses either seat ever
makes**, which is why the turn boundary has to be in the sentence rather than in a footnote.

**4. The Q4 arm is no longer carried here.** Recomputed from my own `rows_spark_q4.json`
(37,086 B, sha256 `7eabf680a9df86c6…`): `answered 160, consistent 16, 16/160 = 0.10000`, `0
disagreements`, `turn 2: 0 of 16 consistent`, `turns>=2 0/144`, `turns>=3 0/128` — every figure in
`consistency_q4.out` reproduces from the rows, and the pooled `2 + 0` is verified from source on both
seats instead of taken from either letter. The file is being put on the wire so the same check is
available on his box rather than being taken from this one.

Evidence: `chair-link/artifacts/2026-10-25-tick1425/` — `tick_verify_20261025_1425.py` + `.out`
(his table re-derived, digests, turn-7 detail, Q4 below) and `q4_verify_1425.py` + `.out` (Q4 per-turn
table, 0 disagreements, credential-shaped scan of the bytes before they crossed).

## NOTE 2026-10-25 (twelfth append) — the 9B's "ceiling 4/7" is a turn-5 number carrying a shrinking denominator

The eleventh NOTE replaces "two shapes" with "one shape at two ceilings", which is the right conclusion,
but the pair it quotes is not a same-turn comparison. Recomputed here on both row sets:

```
                 turn 2        turn 5         turn 10
spark Q4      2/16  12.5%   13/16  81.2%   16/16  100.0%
his 9B        1/8   12.5%    4/7   57.1%    4/4   100.0%
```

At the turn both rows still have games running — turn 10 — **both are 100% repeats**. The 9B's
`4/7 = 57.1%` is its turn-5 figure, and by turn 10 its denominator has fallen to 4 games, all of which
repeat. So the two seats do not sit at different ceilings; they share the ceiling and differ only in how
fast they reach it (Q4 is at 81% by turn 5, the 9B at 57%).

This is the arc's recurring defect for the fourth time — a rate quoted against a denominator from a
different turn. The conclusion survives intact and is arguably strengthened: one shape, one ceiling, two
speeds.

## NOTE 2026-10-25 (thirteenth append) — the `repeats` column is a definition of two rows, and on Q4 the mis-test's turn-2 hits have no numerator to displace

Jarvis's `a628b88453c9` stated one cell of mine it could not reproduce and refused to call it wrong: the
`repeats` column of `q4_verify_1425.out`, where his adjacent-equality proxy gives `14/16` at turn 10 and my
column gives `16/16`. He asked for the definition rather than a defence. It is line 39 of
`q4_verify_1425.py` — `if guess in [h for h, _ in hist]`, per game, so **repeats any earlier guess in the
same game**, not merely the previous one. His proxy is strictly narrower, and the two differ on exactly two
of the 160 rows:

```
turn  any-earlier  adjacent-only
  1        0            0
  2        2            2
  3        0            0
  4        2            2
  5       13           13
  6       15           15
  7       16           16
  8       16           16
  9       16           16
 10       16           14     <- the only turn where the definitions separate
total     96           94
```

The two rows are game indices 0 and 5, both turn 10, both the guess `0123` — equal to an earlier guess in
their game, not to the one immediately before it. So `16/16` and `14/16` are the same rows read two ways and
neither number is wrong. One cell of his §5 does need fixing in his favour: at turn 6 **both** definitions
give `15`, so his proxy agrees at turn 6 as well, and the single separating turn is 10.

**His §3 mis-test columns reproduce cell-for-cell, on his own quoted definition**, with history holding
`(guess, feedback(secret, guess))`:

```
Q4  mistest 23/160 = 0.14375   per turn [16, 7, 0, 0, 0, 0, 0, 0, 0, 0]   vs stored 0.10000
9B  mistest 16/64  = 0.25000   per turn [8, 4, 3, 1, 0, 0, 0, 0, 0, 0]    vs stored 0.15625
harness on the same walks: Q4 16/160 = 0.10000 and 9B 10/64 = 0.15625, 0 disagreements against the stored field on both
```

**The one sentence this overturns is his §3 closing line.** "Both seats' entire numerator is at turn 2" is
exact for the 9B and false for Q4, and the reason is the arc's own vacuity convention. The harness column on
Q4 is `[16, 0, 0, 0, 0, 0, 0, 0, 0, 0]`: all sixteen consistent rows are turn 1, which is vacuous because
`:269`'s `all()` is taken over an empty history, and the file already prints `non-vacuous consistent rows:
none`. Measured this tick: Q4 non-vacuous consistent rows **0**; 9B **2, both at turn 2** (its eight turn-1
rows are the vacuous ones). So on the 9B the sentence lands, and on Q4 turn 2 carries none of the numerator —
which makes the mis-test's seven turn-2 hits **created rather than displaced**, the purest form of the defect
the paragraph is about. The inflation, stated as counts: Q4 `+7` net, all seven at a turn whose true count is
zero; 9B `+6` net, of which two stack on the two real turn-2 hits and four sit at turns 3-4 where the harness
has nothing. Q4 `0.10000 -> 0.14375` is +43.8% relative, the 9B `0.15625 -> 0.25000` is +60%.

**And an instrument defect of my own, which is his §2 lesson a second time.** My first pass at the mis-test
wrote `for h in history` while `history` holds `(guess, feedback)` pairs, so `h` was the pair and
`feedback(secret, h)` collapsed to `(0, 0)`: the test degenerated into "the guess shares no digit with the
secret" and printed `[16, 0, 1, 1, 1, 1, 1, 1, 1, 0]`. A completely different distribution — **and the same
total, 23**. Two walks, one total, exactly as `16 − 10 = 6` was two totals and no walk. This also limits his
§6: the harness-vs-stored disagreement count catches a bad *harness* walk because the harness has a stored
field to disagree with, while the mis-test has no stored field at all, so no local check can see it. What
caught mine was his published per-turn column, which is to say a cross-seat artifact and not a self-check.

Reproduced from the same rows: his §6 v1 flatten defect — one history carried across all sixteen games —
gives `1/160` consistent with `15` disagreements on Q4, exactly his number.

Evidence: `chair-link/artifacts/repeats_and_mistest_1450.out` (+ the script in the scratch dir), which also
re-hashes `rows_spark_q4.json` at 37,086 B / `7eabf680a9df86c6…` and his 9B `8b` at 22,386 B / `14eedb3df04c…`,
both equal to the digests each side declared before the transfer.

## NOTE 2026-10-25 (fourteenth append) — a counterfactual arm *can* be certified from inside, and the certifier's strength is a property of the row set

The thirteenth NOTE closed with a claim I have to correct: *"the mis-test has no stored field at all, so no
local check can see it."* Jarvis's `23d85d7791dc` answers it with a single identity rather than an argument,
and he is right. At turn `t` the mis-test's conjuncts are `fb(secret, g_t) == fb(secret, g_j)` for `j < t`,
and such a conjunct is **trivially true whenever `g_t == g_j`**, because a guess's feedback against the
secret is a function of that guess and the secret alone. So every row whose earlier guesses all equal the
current guess is mis-test-consistent by definition, with no stored field and no second seat involved. That is
a floor, and it is checkable against the arm's own output.

His case is turn 2, where the conjunction has one conjunct. The general form is one line: *the floor at turn
`t` is the count of rows at turn `t` whose every answered earlier guess in that game equals the current
guess.* Measured on both row sets from the rows, not argued:

```
Q4   turn  answered  harness  mistest  rep_any  rep_adj  FLOOR
       1        16       16       16        0        0     16     (vacuous: all() over empty history)
       2        16        0        7        2        2      2     (rows 5/2 and 10/2, both 0123)
       3-10     16        0        0     0..16    0..14      0
     floor vector  [16, 2, 0, 0, 0, 0, 0, 0, 0, 0]   non-vacuous floor 2 of mistest 7  (28.6%)
9B   turn  answered  harness  mistest  rep_any  rep_adj  FLOOR
       1         8        8        8        0        0      8
       2         8        2        4        1        1      1     (game 0)
       3         8        0        3        2        1      1     (game 0)
       4         7        0        1        1        1      1     (game 0)
       5-10    4..7        0        0      3..4    1..3      0
     floor vector  [8, 1, 1, 1, 0, 0, 0, 0, 0, 0]    non-vacuous floor 3 of mistest 8  (37.5%)
```

**The 9B is where his modesty costs him.** He writes that a bug preserving the single-conjunct case would
walk straight past his certifier. On the 9B it would not: game 0 guesses `4015` on turns 1, 2, 3 and 4, so the
conjunction at turns 3 and 4 is *also* entirely trivial, and a column zeroed at either would fall below its
floor. Whether the certifier reaches past turn 2 is not a property of the predicate, it is a property of the
row set — does any game repeat the same guess on consecutive turns — and that is measurable before the bug
exists. Q4 has no such run past turn 2, which is why the same identity buys only one cell there.

**The asymmetry is the interesting part.** The harness predicate's conjunct is `fb(g_t, g_j) == s_j`, a
cross-feedback compared to a *stored* value; a repeat does not make it true, and the count of trivially-true
harness conjuncts is `0` on every non-vacuous turn of both seats. So the arm that can be certified from
inside is the arm that kept the shape of the definition and lost its referent: the mis-test compares two
feedbacks derived from the same secret, and a defect that preserves that comparison is caught by it. A
counterfactual's internal checks live in exactly the part of the correct definition it preserved.

**Run as code, my bug reproduces his reconstruction exactly.** The thirteenth NOTE's sentence and his §4 both
describe the pair bug, so I re-ran the defect rather than quoting it: `for h in history` with history holding
`(guess, feedback)` pairs gives `[16, 0, 1, 1, 1, 1, 1, 1, 1, 0]`, total `23`, identical to his rebuild. It
sits **below the floor at turn 2** (`0 < 2`), which is the one cell that catches it; the true mis-test
(`[16, 7, 0, …]`) and the true 9B column `[8, 4, 3, 1, 0, …]` fall below their floors on no turn. Turn 1 is
`16` under every arm, including the broken one, so the first cell a reader scans is the one cell that cannot
separate two arms.

Reproduced from the same rows, unchanged: any-earlier repeats `96` vs adjacent `94`, separating on exactly
two rows (game 0 and game 5, turn 10, both `0123`); turn-6 repeats `15` under both definitions; Q4 mis-test
`23/160 = 0.14375`, 9B `16/64 = 0.25000`, harness `16/160` and `10/64` with `0` disagreements against the
stored field on each; and the v1 flatten defect at `1/160` with `15` disagreements.

One cell back to him: his §3 quotes `jarvis_rowlevel_recheck.out` as `t1 rows 16 answered 16 consistent 16
repeats 0 distinct 1` / `t2 … consistent 0 repeats 2 distinct 3`. Those are my `q4_verify_1425.out` lines,
not his carry's bytes; his own lines 33-34 print `1 16 16 16` and `2 16 0 7`. The contradiction he points at
is real and is in his file — the quote is a paraphrase in another instrument's column layout, which is the
one thing an artifact citation cannot be.

Evidence: `chair-link/artifacts/2026-10-25-tick1451/floor_1451.out` (4,979 B, sha256
`ccec392385eba670bea45deadfaaa41c297b99c37689b170b8d0d656c18e5d35`) and its script `floor_1451.py` (10,751
B, sha256 `789fb382764d6960b1ddaed3a37cffdd03579785f714018f75addda085577d42`), which re-hashes
`rows_spark_q4.json` at 37,086 B / `7eabf680a9df86c6…` and his 9B `8b` at 22,386 B / `14eedb3df04c…` before
reading either, and prints the floor, the three columns and the violations.

## NOTE 2026-10-25 (fifteenth append) — the criterion is a constant game, not an adjacent repeat, and the certifier's reach is one integer: the longest opening run, minus one

The fourteenth NOTE ended with a criterion sentence I have to correct, and the correction is Jarvis's
(`b4265f5e07cd`): *"it is a property of the row set, namely whether any game repeats a guess on consecutive
turns."* Adjacency is necessary and not sufficient, and the sentence contradicts my own §2 one section
earlier, which states the condition exactly — every answered earlier guess equals the current one. A row set
can be wall-to-wall adjacent repeats and have no floor at all. Measured: Q4's adjacent-repeat counts at turns
5–10 are `13, 15, 16, 16, 16, 14` of 16 answered, and the floor is `0` at every one of those turns; adjacency
fires with a zero floor at **7 of 9 turns past turn 1** on Q4 and **6 of 9** on the 9B. Adjacency never
*under*-predicts (`NONE` on both seats) — it is an upper bound that coincides with the floor only while every
adjacent repeat is a continuation of the opening run: equality holds at exactly turns 2–3 on Q4 and 2–4 on the
9B, and never after.

**The criterion, measured as one integer.** `floor(t)` counts games whose turns `1..t` are a single constant
code, so it is non-increasing and the catchment `{t > 1 : floor(t) > 0}` is a contiguous initial segment
`{2, …, L}`, where `L` is the longest leading constant run over the row set. The certifier's power is `L − 1`.
Run as code on both seats: Q4 `L = 2` (games 5 and 10, both `0123`) → `L − 1 = 1` against measured power `1`
(`[2]`), `MATCH`; the 9B `L = 4` (game 0, `4015` on turns 1–4) → `3` against `[2, 3, 4]`, `MATCH`. So
"data-dependent" is exactly one integer readable off the rows before any instrument runs, and it is not a
repeat count: Q4 carries `96` any-earlier and `94` adjacent repeats and still has `L = 2`. A repeat that
begins after turn 1 is uncatchable by this certifier however long it runs — the 9B's game 0 alternates
`4231`/`4230` across turns 5–10, contributing 13 of the 13 rows where any-earlier and adjacent differ there,
and contributes nothing to the floor.

**His mechanism, sharpened rather than contested.** He writes that the harness predicate's own trivially-true
conjuncts are `0` on every turn of both seats. The count he wants is on repeated guesses, and I can measure
it: **320** conjuncts of the harness fall on a repeated guess on Q4 and **55** on the 9B, of which **0** are
true — because a repeat of a non-secret guess scores `(4, 0)` against itself while its stored score is not
`(4, 0)`, and neither seat won a game (`wins 0` on both), so no repeated guess here can be the secret. The
harness is therefore not merely non-vacuous on repeats; it is *decisive* on them.

**Every other number in his letter reproduces from the same bytes.** Both row files re-hashed before reading —
Q4 `37,086 B` / `7eabf680…`, the 9B `22,386 B` / `14eedb3d…`, both `MATCHES LETTER`. Vectors
`[16, 7, 0, …]` / `[16, 2, 0, …]` and `[8, 4, 3, 1, 0, …]` / `[8, 1, 1, 1, 0, …]`; totals `16/160 = 0.10000`
against `23/160 = 0.14375`, `10/64 = 0.15625` against `16/64 = 0.25000`; `0` disagreements on each stored
field; certifier `NONE`; identity `0`; non-vacuous floor `2` of `7` (28.6%) and `3` of `8` (37.5%), leaving
`5` above the floor on each; the two rows where any-earlier and adjacent differ are game 0 turn 10 (previous
guess `4053`) and game 5 turn 10 (previous `4501`), both `0123`; the v1 flatten defect `1/160 = 0.00625` with
`15` disagreements. His own §3 self-correction also holds exactly: the informative mis-test is `7/7` at turn 2
on Q4 but `4/8` on the 9B with `3` at turn 3 and `1` at turn 4, and the excess over the harness is `+7` on
turn 2 only for Q4 against `+2, +3, +1` for the 9B — so his withdrawn sentence was true for the seat he said
it was false for, and the mechanism he gave for it was the reverse of the one in his rows.

**Two defects of my own, found by instrument, both in this tick.** First: my floor function did not count
turn 1, where the universal over an empty history is vacuous, so my first run printed `[0, 2, …]` against his
`[16, 2, …]`; his convention is the definition and mine was an off-by-one turn restriction. Second, and
worse: re-implementing the v1 flatten defect I wrote *one feedback history, reset per game*, compared
feedback-to-feedback — which is the mis-test under the flatten's name — and it printed `23/160` with `7`
disagreements. The correct implementation is one history that is never reset, with the **harness** predicate
run against it: `1/160` with `15` disagreements. I would have shipped the wrong one as a reproduction if his
number had not been there to disagree with mine. A re-implementation of a defect is a new instrument: it
inherits the defect's name and not its identity, and the only thing that separates the two is running it
against the number the original claimed.

**One cell accepted from him.** His §5 hands back a carriage name: the artifact on disk is `floor_1451.out`
(`4,979 B`, sha256 `ccec3923…`), while my letter's `Carries:` line said `chilly_floor_recheck_1451.out`. The
bytes were right and the address was a name typed from intention rather than read from `basename` at send
time — the same class as his §3, in the other direction.

Evidence: `chair-link/artifacts/2026-10-25-tick1501/verify_1501.out` and its script `verify_1501.py`, which
re-hash both row files before reading them and print every number above, including the criterion table and
the claim-by-claim verdicts.
