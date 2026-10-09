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

## BOTH UNITS, MEASURED

```
18 entrants with both numbers:
  TOTAL wall (journal "scored in")   97.0 min
  TOTAL generation (sum of secs)     36.0 min
  GAP                                61.0 min      <- 63% of wall time is NOT inference

per entrant, the largest:
  Qwen3.5-9B-Q4_K_M     WALL 1914.0 s    GEN 707.5 s    load+overhead 1206.5 s = 20.1 min
  Qwen3.5-4B-UD-Q4_K_XL WALL 1380.0 s    GEN 600.8 s    load+overhead  779.2 s = 13.0 min
```

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

## AND THE MEASUREMENT NOBODY WAS LOOKING FOR

**63% of the run's wall time is not inference.** On this box, for this population, **loading models costs
almost twice as much wall time as running them.** That is a fact about the instrument — and it means any
future "how long does an item take" number quoted in wall time is mostly a statement about model loading.

**CONSEQUENCE, FORWARD-ONLY:** the record must carry **wall time alongside `secs`**, or the two units will
keep being read as one. `secs` alone cannot answer a question asked in wall time, and the difference is not
a correction — it is 63% of the quantity.

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
