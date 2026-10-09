# FINDING 012 — "A SINGLE MOVE CAN TAKE EIGHT MINUTES": THE UNIT DECIDES IT

**From the v5 run** — the first field to carry a per-item clock at scale.

> **AMENDMENT, and it changes the finding's shape:** the first version measured only `secs` and reported a
> refutation. **`secs` is not wall time**, and the claim says *"eight minutes of actual real-world wall
> time."* Both units are now measured, and the answer is different in each. **The refutation was sound about
> generation and unproven about the claim** — which is the same defect as `budget_hit`: a maximum in the
> wrong unit measures the wrong thing.

---

## WHAT `secs` ACTUALLY MEASURES — READ FROM THE CODE

```python
t0 = time.time()
r = json.load(urllib.request.urlopen(req, timeout=900))
dt = time.time() - t0          # -> recorded as `secs`
```

**`secs` is the duration of ONE HTTP REQUEST** — prefill plus generation, from the request going out to the
response coming back. **It excludes model load and server startup entirely.**

**That reconciles an observation that otherwise looked contradictory:** during the run, an arena process
appeared ~6 minutes old while its own log showed `n_gen = 1172` at `15.36 t/s` — about 76 seconds of work.
**Process age includes loading a multi-gigabyte model; `secs` does not. Both were correct.**

## BOTH UNITS, MEASURED — AND A CORRECTION TO THE FIRST VERSION OF THIS SECTION

### What `secs` and `gen_tokens` each cover — settled against the server log

The bundle records **one `secs` and one `gen_tokens` per ITEM**, but **each item ran THREE times.** Measured
on the Qwen3.5-9B entrant's own server log (`arena-server-27520-33129.log`, 78,938 bytes):

```
distinct tasks (requests) in the log   18      = 6 items x 3 trials
log total tokens (per-task maxima)     24,324
bundle total gen_tokens                11,601
ratio                                  2.10
```

**And the three largest tasks in the log are 2969, 2972, 2983 — matching the bundle's three `3000`s.** So
**`gen_tokens` and `secs` each describe ONE of the item's three trials**, not the item's total.

**THE FIRST VERSION OF THIS SECTION SAID "63% OF WALL TIME IS NOT INFERENCE". THAT WAS WRONG**, and wrong
in exactly the way this finding is about: `wall − sum(secs)` captured **both the two uncounted trials and
the load**, and the whole gap was attributed to load.

```
sum(item secs) x the measured ratio   707.5 x 2.10  =  1486 s   <- TOTAL generation
wall (journal "scored in")                          =  1914 s
LOAD + OVERHEAD                                     =   428 s   =  7.1 min
```

**So the real split is ~78% generation, ~22% load — not 37/63.**

### And the load is PER-ENTRANT, which is the question that decides the claim

**One `llama-server` is constructed per entrant** (`arena.py:1037`), all six items run against it, and it is
torn down at the end. **So the model is loaded ONCE per entrant** — the 428 s above — **and a single item
costs one request.**

**Consequence for the claim, and this is the definite answer:**

```
a single ITEM  (one request)   max 145.6 s  =  2.43 min   ->  the claim is REFUTED
the entrant's LOAD (once)          ~428 s  =  7.1 min    ->  the claim is nearly EXACT
```

**"A single move can take eight minutes of actual real-world wall time" is therefore not a unit error so
much as a SUBSTITUTION: one entrant's model load standing where a move should be.** And 7.1 min is close
enough to 8 that the figure is almost certainly that number.

**IN A GAME, THE LOAD HAPPENS ONCE AND IS NOT A MOVE** — so the claim fails as stated, **and the number
behind it is now located rather than merely doubted.** A reader can check both: the item maximum is 2.43
min, and the load is 7.1.

### The per-entrant numbers, for the record (generation estimated at the measured ratio)

```
Qwen3.5-9B-Q4_K_M     WALL 1914.0 s    sum(secs) 707.5 s    ->  ~1486 s gen,  ~428 s load+overhead (7.1 min)
Qwen3.5-4B-UD-Q4_K_XL WALL 1380.0 s    sum(secs) 600.8 s    ->  ~1262 s gen,  ~118 s load+overhead (2.0 min)
```

**The load scales with the model, which is what a load does.** This is the number a reader of the card
needs and it did not exist before this run.

**CONSEQUENCE, FORWARD-ONLY:** the record must carry **wall time alongside `secs`**, and **the trial count
alongside both** — because `secs` is per-trial while the bundle presents it per-item, and **the two differ by
the trial count, which is the same defect as reading a count without its set.**

## THE VERDICT, IN EACH UNIT — AND THEY DISAGREE

```
longest single ITEM (inference)      145.6 s  =  2.43 min    ->  REFUTED
largest ENTRANT load+overhead       1206.5 s  = 20.1 min    ->  "eight minutes" sits INSIDE this range
```

**So the claim is:**
- **REFUTED if "move" means an inference** — the longest is 2.43 min, and nothing came within 334 s.
- **PLAUSIBLE if eight minutes is a LOAD time** — loads reach 20.1 min in this field, and 8 is comfortably
  inside that.

**AND THE RIGHT UNIT IS INFERENCE, so the claim is refuted as stated** — because **in a game the model is
loaded once and plays many moves.** A move's wall time is `secs`; the 20-minute load happens once and is not
a move. **But the 8-minute figure is now explained as a plausible LOAD time rather than as an invented
number, which is a stronger refutation than "the number is wrong."**

## AND THE MEASUREMENT NOBODY WAS LOOKING FOR — RESTATED, BECAUSE THE FIRST VERSION WAS WRONG

**The load is real, large and per-entrant: ~7.1 min for the 9B, ~2.0 min for the 4B.** On a box with an
8 GB card serving models that offload to CPU, **a single entrant's model load is 2–7 minutes, and it happens
once.** That is a fact about the instrument, and it was invisible until this run.

**But the first version of this section claimed "63% of wall time is not inference", and that was wrong** —
it came from `wall − sum(secs)`, and `sum(secs)` covers one trial of three. **The gap was mostly the two
uncounted trials, not the load.** The corrected split is **~78% generation / ~22% load.**

**THE ERROR IS THE FINDING'S OWN SUBJECT, COMMITTED TWICE IN ONE FILE:** first a duration reported in the
wrong unit against a claim made in another, then a *ratio* computed from a quantity whose denominator was
not what its name said. **A number is not wrong because it is wrong — it answers a different question than
the one it was attached to, and it does so in the same way each time.**

**CONSEQUENCE, FORWARD-ONLY:** the record must carry **wall time alongside `secs`, and the trial count
alongside both** — because `secs` is per-trial while the bundle presents it per-item, and **the two differ
by the trial count, which is a count read without its set.**

## THE ITEM-LEVEL TABLE (unchanged, and it is inference)

222 item records carrying `secs`, across 37 measured entrants.

```
LONGEST SINGLE ITEM :  145.6 s  =  2.43 min     R1.1  Qwen3.5-4B-UD-Q4_K_XL   3000 tok
EIGHT MINUTES       :  480.0 s
SHORTFALL           :  nothing came within 334 s of the claim.
```

## AND A SECOND THING THE CLOCK SHOWS

**Every item that ran long ran into the token budget.** Of the 11 items that reached exactly `3000 tok`,
**all four items over 120 s are among them** — and the four longest items in the field (145.6, 139.5,
128.2, 122.6 s) **each stopped at exactly the cap.**

So the ceiling on item duration is **truncation, not deliberation** — **an item that reaches the cap is a CUT
answer, and `budget_hit` is the field that says so.** **`secs`, `budget_hit` and wall time must be read
together**; any two of the three will mislead.

## WHAT THIS SETTLES

- **The claim, as stated, is refuted** — in its own unit, on 222 records, with the longest at 2.43 min.
- **The number behind it is real and locatable: it is a plausible LOAD time**, where this field reaches
  20.1 min.
- **And the first version of this finding was itself an instance of its own subject** — a duration in one
  unit reported against a claim made in another. **The unit axis does not spare the person measuring it.**
