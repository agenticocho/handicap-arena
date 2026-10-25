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
