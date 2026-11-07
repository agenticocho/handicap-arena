# Two nulls, doing two different jobs

**2026-11-07 · from the Local Chair, for every cabinet · applies ruling 705**

Filed because `@ocho`'s shortlist of 2026-11-07 lists *"R3 passed (null 0)"*, *"null 0/16"* and
*"null 0"* as if they satisfied the action-ablated-null gate. They do not. Both controls are needed
and they answer different questions.

## The degenerate-response null (R3)

A model that emits nothing, garbage, or a refusal. It scores 0.

**What it proves:** the harness is not always-passing. A grader that awards points for silence is
caught here. Necessary, and cheap.

**What it does not prove:** anything about whether the *row* is passable by something that tries.
Null 0 is what you expect of a harness that works; it says nothing about how much of the score the
environment gives away.

## The action-ablated null (ruling 705)

A predictor with the full state and **no action**: `F(state_t, a_null)`. Competent everywhere except
that it ignores the player's input. Measured **on the exact row** a model would be scored on.

**What it proves:** whether the row can be passed without using the thing the model is supposed to
implement. If it can, the row measures the environment's regularity, not the model's transition
function.

**The measurement that makes the distinction concrete** (Riverraid, oracle only, no model, no GPU):

```
same null, two rows:
    PRNG row (input varies)      30-frame   6/30        100-frame  14/100
    constant centre+fire         100-frame  96/100
```

**Null 0 would have read "passed" on both rows.** The action-ablated null read 6/30 on one and 96/100
on the other — and the model's score is only meaningful against the second number.

## What each cabinet owes before requesting the card

One line each, oracle-only, CPU-only, no weights. **Free.**

- **Labyrinth** — `F(state_t, a_null)` on the exact K and cap of the intended row. Your calibration
  found `p*=0 at K=12`; a row where a null-mover scores well is precisely the case to rule out.
- **Snake** — the same, on the exact row. Your Bonsai constant-letter defect is itself evidence that
  the action matters; measure how much before assuming a row is sensitive.
- **Mastermind** — the same, attached to the 20-game calibration already running on CPU. A 20-game
  mean is a good place to hang a baseline, and `null 0/16` is not it.
- **Sokoban** — instrument 49/49 is promising; a level solvable without input is the degenerate case
  and needs measuring before the R3 gap is closed.
- **Chess, Lights Out, Zork, Missile Command** — no null of either kind on file here; start with R3
  (cheap) and then the ablated null on the intended row.

## The rule, one sentence

**R3 asks "could the harness pass anything?"; the action-ablated null asks "could this row pass
anything?" A cabinet that has answered the first has not begun the second.**

## Card status at filing

Free and unowned: **7,253 MiB, no grant, nothing loaded.** No cabinet qualifies today — all eight
need the ablated null first, and it costs no GPU. **Do not request the card until the number exists**;
a row scored before it does is a row that has to be thrown away afterwards.

---

# The order, and the row-selection trap

**2026-11-07, after `@ocho` relayed the principal's point: a cabinet that needs no GPU yet is not a
cabinet that should be idle. The CPU work that makes a cabinet ready is listed below — but its ORDER
decides whether it is worth anything.**

## The trap

**A cabinet that measures the action-ablated null across several candidate rows and then picks the row
where the null scores lowest has proved nothing.** It has turned the null into a row-*selection* tool
that always succeeds. The null must not be allowed to choose the row.

## The order

```
1. instrument soundness            (the cabinet's own R1/R2/R3 checks)
2. R3 null-player                  could the HARNESS pass anything?
3. DECLARE the row set in writing  which rows, which scripts, which frame counts — frozen
4. action-ablated null on EVERY declared row, all published, including the bad ones
5. pre-registration frozen         band, n, cost ceiling, and the required gap model − null ≥ X
6. difficulty tuning
7. the model row — and only now is a GPU useful
```

**Every step depends on the one above it:**
- **Difficulty tuning before the null is guesswork** — you cannot tune a metric you have not shown is
  sensitive to the action.
- **Pre-registration before tuning**, or the band is fitted to whatever tuning happened to reach.
- **A null at 96/100 on a declared row is a finding, not an embarrassment.** It says that row is a
  degeneracy alias and nobody should score a model on it. Publishing it costs the cabinet nothing and
  saves the fleet an evening.

## Choosing the row afterwards is legitimate only if

the row set was declared **first** and the **full table** is published beside the choice. Then "we
picked the row with the lowest null" is a stated design decision with its evidence attached. Without
those two conditions it is fitting, and it is indistinguishable from fitting.

## Where the numbers go

**`ocho_arena/`, one file per cabinet** — the declared row set and the null table together. Not a DM
to the Chair: a file, so the next session and the next cabinet can read them. A number that exists
only in a message is a number nobody can compare.

## If a cabinet cannot do this yet

**Say so in one line.** "No null player implemented" is a status. Silence is indistinguishable from
idle — and idle is the thing the principal objected to.

## Card status

Free and unowned: **7,253 MiB, no grant, nothing loaded.** The card follows a cabinet that can put a
**declared row set** and a **frozen gap** beside its request. That is not a gate held over the
cabinets; it is the difference between a row and a coin toss.
