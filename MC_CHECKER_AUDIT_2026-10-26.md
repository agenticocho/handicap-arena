# MC_CHECKER_AUDIT_2026-10-26 — THE CHECK THAT DOES NOT PASS, NAMED, DECIDED, AND MUTATION-TESTED

**Card:** `t_3abd318f`. **Owner:** the Missile Command agent (`missile-command`). **Authorised by** Mike,
2026-10-26. **Instrument:** `scripts/check_mc_claims.py` (new, CPU only, no model call, no GPU, no lease).
**The published checker is BYTE-IDENTICAL at this commit** — `scripts/check_mc_field_plain.py`
`575cd30462517038`, `git status` clean for it — because this card's constraint says not to edit it. What
supersedes its denominator is this instrument and this note, not a silent rewrite of the file.

---

## 0. THE ANSWER, IN FIVE LINES

```
the check that does not pass    #114 of 115, "over 12 cells the tokens reproduce TOKEN-FOR-TOKEN (P2)"
why it does not pass            2 of the 12 shared cells emitted different token streams; both records are
                                CORRECT (their scores agree), and the cause is measured: the model files are
                                not reproducible objects on this box (MC_FIELD_PLAIN.md Finding A)
can any input make it fail      YES -- the published field itself, rc 1; and a mutation does it too
can any input make it pass      YES -- shadow P5 makes the two token lists equal: 115/115, rc 0
the honest denominator          114/114, the check DEMOTED to a reading; the coverage lost is named in §3
```

---

## 1. THE PUBLISHED CHECKER, ENUMERATED IN ITS OWN ORDER

`scripts/check_mc_claims.py --denominator` imports `scripts/check_mc_field_plain.py` without editing it,
wraps its `ck()`, and runs it in-process. Measured, this commit:

```
checks emitted 115   passing 114   failing 1   exit code 1
  #114 FAIL  over 12 cells the tokens reproduce TOKEN-FOR-TOKEN (P2)
        got  [('Mellum2.1-12B-A2.5B-Thinking-Q4_K_M', 'mc_01_one_shot'),
              ('MiMo-V2.6-Distill-Qwen-9B-Q4_K_M', 'mc_02_scarcity')]
        want []
```

**THE ORDINAL, CAREFULLY.** `114/115` means the one check that does not PASS is **#114** in emission
order. Check **#115** is `...over exactly 12 cells`, its non-vacuity guard: it PASSES, and it fires on its
own input (§4, P6). So "the 115th check" in the card's phrase names *the missing pass*, not the 115th line
of the checker; both readings are answered here, and neither is a dead control.

**THE 115 ARE NOT ALL THE SAME KIND OF THING**, and the count says so: 88 are per-cell measurements
(22 cells × 4), 27 are structural checks over the archive, the population artifact, the declaration, the
driver history and the entrant sizes, and 5 are in-checker controls. An aggregate like `114/115` is
therefore a score over four different kinds of statement, which is the second reason it should not be read
as a capability figure.

---

## 2. THE DECISION — DEMOTED TO A READING, WITH THE COVERAGE LOST NAMED

`PREREG_mc_field_plain.md` P2 predicted that every cell this field shares with the population run's `plain`
arm would reproduce **token-for-token**, because the instrument fix touched no prompt, no cap, no screen and
no ceiling. Measured on the published field:

```
12 shared cells   TOKENS 10 of 12   SCORE 12 of 12   COUNTERS 11 of 12
```

So the prediction was falsified on 2 of 12 cells — and both cells are **correct records**: their scores
agree, their counters nearly do, and the cabinet already filed the explanation (Finding B, measured in
Finding A: those two entrants' model files hashed differently minutes apart). That is the whole case.

**The check is not broken and it is not unfalsifiable.** §4 exhibits it FAILING (the field; and P1-P4) and
PASSING (P5, 115/115, rc 0). It is a live control. **But its pass condition is an identity this cabinet
measured not to exist**: it requires two runs to emit identical completions from files whose bytes are not
stable. An expectation that fails on a correct record is a permanent red lamp, and a permanent red lamp
hides the next real regression inside a failure that is expected every run.

This is the **third instance of one class in this one checker**:

```
t_d68e29ba   driver_digest expected to equal the file on disk   -> a READING, three falsifiable checks added
t_77f73033   entrant identity expected to be the digest         -> the SIZE, per measurement; digests printed
t_3abd318f   two runs expected to emit the same tokens          -> a READING; score identity promoted to a check
```

**What is kept as a check** (and it CAN fail — §4 M2): the SCORE reproduces on all 12 shared cells, the two
runs are the same instrument (simulator, arm, state digest), and the two runs' claimed scores agree.

**What coverage is lost, named rather than left to be found:** token-level provenance against an independent
run, over the 12 shared cells — previously the only thing that could notice a token stream substituted for
another that produces the same score. It is lost because it could not be relied on: on this box a genuine
re-run trips it too, so it could not separate a substitution from a changed entrant. §6 states what the
cabinet now cannot separate, and §4 M9 exhibits the residual rather than describing it.

---

## 3. CLAIM vs OUTCOME — 22 ROWS, DISAGREEMENTS PRINTED (AND ZERO)

Computed from `(state_text, tokens)` by the frozen simulator, not read from the record. `hit` = the threat
impacted a city (a city was lost); `miss` = it impacted empty ground; `no-fire` = no token ever named it.

```
entrant                                  level             score  hit  miss  no-fire | c.score c.hit c.miss  disagree
LFM2-350M-Extract-Q4_K_M                 mc_01_one_shot        0    1     0        1 |       0     1      0  -
LFM2-350M-Extract-Q4_K_M                 mc_02_scarcity        0    4     4        8 |       0     4      4  -
Llama-3.2-3B-Instruct-Q4_K_M             mc_01_one_shot        1    0     0        0 |       1     0      0  -
Llama-3.2-3B-Instruct-Q4_K_M             mc_02_scarcity        0    4     4        8 |       0     4      4  -
Mellum2.1-12B-A2.5B-Thinking-Q4_K_M      mc_01_one_shot        1    0     0        0 |       1     0      0  -
Mellum2.1-12B-A2.5B-Thinking-Q4_K_M      mc_02_scarcity        0    4     4        8 |       0     4      4  -
MiMo-V2.6-Distill-Qwen-9B-Q4_K_M         mc_01_one_shot        0    1     0        1 |       0     1      0  -
MiMo-V2.6-Distill-Qwen-9B-Q4_K_M         mc_02_scarcity        0    4     4        8 |       0     4      4  -
OculusMind-ToolCall-8B-v2.i1-Q4_K_M      mc_01_one_shot        1    0     0        0 |       1     0      0  -
OculusMind-ToolCall-8B-v2.i1-Q4_K_M      mc_02_scarcity        1    3     4        4 |       1     3      4  -
Phi-3.5-mini-instruct-Q4_K_M             mc_01_one_shot        1    0     0        0 |       1     0      0  -
Phi-3.5-mini-instruct-Q4_K_M             mc_02_scarcity        0    4     3        5 |       0     4      3  -
Qwen3-1.7B-Q8_0                          mc_01_one_shot        0    1     0        1 |       0     1      0  -
Qwen3-1.7B-Q8_0                          mc_02_scarcity        0    4     4        7 |       0     4      4  -
Qwen3.5-2B-UD-Q4_K_XL                    mc_01_one_shot        1    0     0        0 |       1     0      0  -
Qwen3.5-2B-UD-Q4_K_XL                    mc_02_scarcity        0    4     4        4 |       0     4      4  -
Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0       mc_01_one_shot        1    0     0        0 |       1     0      0  -
Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0       mc_02_scarcity        0    4     4        8 |       0     4      4  -
Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0       mc_01_one_shot        1    0     0        0 |       1     0      0  -
Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0       mc_02_scarcity        0    4     1        4 |       0     4      1  -
granite-3.3-2b-instruct-critical-…       mc_01_one_shot        0    1     0        1 |       0     1      0  -
granite-3.3-2b-instruct-critical-…       mc_02_scarcity        0    4     4        8 |       0     4      4  -

DISAGREEMENTS 0 of 22 measured rows
```

**AND THE RECORDED TRAJECTORY IS A CLAIM TOO.** Each record carries a `trace` (one row per tick: outcome,
note, cities alive, ammo, threats remaining). The published checker **never reads it** — it re-derives its
own and stops. This instrument does read it: **22 of 22 recorded traces equal the trace re-derived from
`(state_text, tokens)`**, measured, and §4 P1 shows what happens when one does not. The record also holds
**three copies of the token stream** (`tokens`, `trace[].token`, `turns[].token`): all 22 rows agree, and a
substitution that misses one copy is caught (§4 M10).

---

## 4. THE MUTATION MATRIX

### 4a. In memory, through the whole audit (§4, default run)

```
CAUGHT   M1  trajectory: a threat's impact moves from a city to empty ground
CAUGHT   M2  target assignment: a token names another threat
CAUGHT   M3  claimed hit: counts.hit +1 and the score and the record paid for it
CAUGHT   M4  recorded trajectory: the trace says a city died        <- the published checker does NOT catch this
CAUGHT   M5  claim: the population's claimed score altered on a shared cell
CAUGHT   M6  instrument: the population's simulator_digest altered
CAUGHT   M7  frozen board: a level file gains a city
CAUGHT   M8  the ceiling's own control: the wrong policy disagrees with the optimum
CAUGHT   M10 one copy of the token stream substituted (three copies of one claim)
SURVIVED M9  a SELF-CONSISTENT token substitution on a cell the population never measured
```

**M9 is the residual and it is meant to survive**: the record is re-recorded with a different token stream
that produces the **same** counters, on one of the 10 cells the population never measured. No check fires,
because the record is its own only copy and nothing in the cabinet holds a second one. The check that
asserts this survival FIRES if the residual is ever closed.

### 4b. The published checker on a shadow cabinet (its own exit code, `--mutations`)

A copy of the tree per mutation, one mutated record (or one mutated population artifact), `git` history read
from the real tree through `MC_DRIVER_HISTORY_REPO`. The real tree is never written.

```
rc 1  114/115  P0  no mutation -- the copy is faithful                       FAIL: #114 only
rc 1  114/115  P1  recorded trajectory (`trace`) altered                    FAIL: #114 only  <- INVISIBLE
rc 1  112/115  P2  claimed hit altered (counts.hit +1, score -1)            FAIL: <record>: the score recomputes,
                                                                                  <record>: the counters recompute, #114
rc 1  112/115  P3  target assignment altered (`1P` -> `1Q`)                FAIL: <record>: the score recomputes,
                                                                                  <record>: the counters recompute, #114
rc 1  112/115  P4  state trajectory altered (S impacts empty ground)        FAIL: <record>: the score recomputes,
                                                                                  <record>: the counters recompute, #114
rc 0  115/115  P5  the population's two differing token lists set equal     #114 PASSES
rc 1  114/115  P6  the two differing cells leave the shared set (10)        FAIL: #115 "...over exactly 12 cells"
```

**P1 IS THE FINDING NOBODY HAD NAMED.** A record's recorded trajectory can be falsified — a city marked dead
that the simulator does not kill — and the published checker reports **exactly the same 114/115, rc 1,
same single failure** as the unmutated copy. The trace is carried, displayed, and never read. That is the
arena's common defect class one field over: an outcome field that can be produced without the event it
names. This instrument reads it (§2) and catches the mutation.

**P5 and P6 ARE THE OTHER DIRECTION.** P5 makes the demoted check pass (115/115, rc 0): it is a live
control, not dead code. P6 drops the shared set to 10: **#114 passes and its guard #115 fails alone**
(114/115, `got 10 want 12`), so the guard is live and is not a copy of the check above it.

---

## 5. THE CEILING — WHAT A CONSTANT POLICY GETS

Exhaustive search over the step-locked protocol (exact, not an estimate), against constant policies that
read only the state:

```
level            policy                                    score   rate
mc_01_one_shot   PASS always                               0/1       0.0% of optimal
mc_01_one_shot   spend on EVERY threat (trivial policy)    1/1     100.0% of optimal
mc_01_one_shot   spend on every CITY-BOUND threat          1/1     100.0% of optimal
mc_01_one_shot   OPTIMAL (exhaustive)                      1/1     100.0%   ['1P']
mc_02_scarcity   PASS always                               0/4       0.0% of optimal
mc_02_scarcity   spend on EVERY threat (trivial policy)    2/4      50.0% of optimal
mc_02_scarcity   spend on every CITY-BOUND threat          4/4     100.0% of optimal
mc_02_scarcity   OPTIMAL (exhaustive)                      4/4     100.0%   ['1P', '1Q', '2R', '2S']

entrants, mean score / optimum      mc_01  0.636 / 1 = 63.6%      7 of 11 reach the trivial policy's score
                                    mc_02  0.091 / 4 =  2.3%      0 of 11 reach it
```

**THE HUMAN BASELINE THE CABINET MUST SUBTRACT.** A constant policy that fires at every threat's impact
coordinate, in impact order, gets **100% of the optimum on mc_01 and 50% on mc_02**; a policy that also
looks at which coordinates are cities gets **100% on both**. The score therefore cannot separate a model
that plays from a four-line program that reads. The entrants' mean is **63.6%** where the trivial policy is
at 100%, and **2.3%** on mc_02, where the trivial policy is at 50%: on this field the event separates
"reads the state" from "does not", and nothing above that.

**AND THE LEVEL FILE'S PROSE IS WRONG ABOUT ITS OWN BOARD.** `levels/mc_02_scarcity.txt` says
*"SEVEN THREATS"* (the state has **eight**: P Q R S T X Y Z) and *"T -> 4 city"* (impact 4 is **empty
ground**: cities sit at 2, 3, 5 and 6, so **T is a decoy** with X, Y and Z). The parser ignores comments, so
no score moves, and the file is frozen, so it is recorded here and not edited. It matters: an entrant that
read the prose instead of the state would spend a round defending nothing, and the ceiling section would
report that as a choice rather than as a misreading.

---

## 6. WHAT THIS CABINET CANNOT SEPARATE

1. **A differing token stream from a changed entrant.** The model files are not reproducible objects on this
   box (Finding A): two runs that record the same `entrant_digest` may not have read the same bytes.
   Replication was measured to hold **only within one session** (the population's own control: 4 of 4
   cells). So a token stream that differs from the population's is not evidence about the record — which is
   what §2 demotes.
2. **A self-consistent substitution on the 10 cells the population never measured** (§4 M9). The record is
   its own only copy; a substitution that moves no number is invisible. The 12 shared cells are covered for
   anything that moves the **score**; nothing is covered for a substitution that moves nothing.
3. **A model from a four-line program** (§5). The optimum is reached by a constant policy.
4. **One run from another.** n = 1 per cell, one state set, one arm; there is no within-cell variance.
5. **The entrant's bytes from a file of the same size.** Per the ruling on `t_7f400932` the identity is
   `st_size`, because the digest does not reproduce; two rows of equal size are not thereby the same weights.

---

## 7. WHAT WAS AND WAS NOT TOUCHED

```
scripts/check_mc_field_plain.py   575cd30462517038   UNCHANGED (the published checker; git status clean)
scripts/check_mc_claims.py        NEW                the instrument this card adds
probes/  levels/  MC_DECLARATION.md  PREREG_*        UNCHANGED
MC_FIELD_PLAIN.md                 a dated NOTE appended (§8); nothing above it edited
```

Reproduce the whole audit (about 6 minutes, because seven shadow cabinets each re-hash the entrant files):

```
scripts/run_guarded.sh mc-claims <cab> /usr/bin/python3 scripts/check_mc_claims.py --denominator --mutations
# or, bare: /usr/bin/python3 scripts/check_mc_claims.py            (fast: 12 checks, ~0.4 s)
```

---

## 8. THE DATED NOTE APPENDED TO MC_FIELD_PLAIN.md

The note is appended to that file rather than written here twice; it carries the same five lines as §0 and
points at this document. Nothing above the note in `MC_FIELD_PLAIN.md` is edited — including the sentence at
its line 11 that says the checker has "111 checks", which is that card's record of its own day.
