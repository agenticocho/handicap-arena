# FINDING 012 — "A SINGLE MOVE CAN TAKE EIGHT MINUTES": REFUTED, AND THE UNIT THAT FOOLED IT

**From the v5 run** — the first field to carry a per-item clock at scale. The claim was `UNVERIFIED` in the
transcript audit because the clock did not exist; **it now has its carrier, and the carrier refutes it.**

---

## THE MEASUREMENT

222 item records carrying `secs`, across 37 measured entrants.

```
LONGEST SINGLE ITEM :  145.6 s  =  2.43 min     R1.1  Qwen3.5-4B-UD-Q4_K_XL   3000 tok
EIGHT MINUTES       :  480.0 s
SHORTFALL           :  nothing came within 334 s of the claim.
```

The ten longest single items, with their token counts:

```
145.6 s  2.43 min  R1.1_ordered_sequence_with_a_gap   3000 tok  Qwen3.5-4B-UD-Q4_K_XL
139.5 s  2.33 min  R1.4_absence_is_the_answer         3000 tok  Qwen3.5-9B-Q4_K_M
128.2 s  2.14 min  R1.1_ordered_sequence_with_a_gap   3000 tok  Qwen3.5-9B-Q4_K_M
122.6 s  2.04 min  R1.3_duplicates_are_significant    3000 tok  Qwen3.5-9B-Q4_K_M
118.1 s  1.97 min  R1.5_exact_key_set_under_a_bribe     474 tok  Qwen3.5-9B-Q4_K_M
```

## THE ERROR, AND ITS SHAPE IS NOW VISIBLE RATHER THAN INFERRED

**The claim is not a lie about a number. It is the right number under the wrong label** — and the data
shows exactly where the wrong label came from:

```
longest ENTRANT total (all six items):  707.5 s  = 11.79 min   Qwen3.5-9B-Q4_K_M
longest single ITEM:                    145.6 s  =  2.43 min
```

**Entrant durations of eight to twelve minutes exist in this field.** So the figure is real; it is an
**entrant's whole run wearing a move's label.** The audit had already guessed the direction —
*"eight minutes matches BTL-4's WHOLE run at 471 s"* — and **this is that guess with a carrier behind it,
measured across 222 records instead of inferred from one.**

**This is the UNIT axis, arriving with data instead of with an argument:** a number is not wrong because it
is wrong, but because it answers a different question than the one it was attached to.

## AND A SECOND THING THE CLOCK SHOWS, WHICH NOBODY ASKED FOR

**The two longest items both stopped at exactly `3000 tok` — the `max_tokens` budget.**

So the ceiling on item duration in this field is **not deliberation, it is truncation**: the slowest items
are the ones that ran out of budget rather than the ones that thought longest. **An item that reaches the
cap is a CUT answer, and `budget_hit` is the field that says so** — which means the longest-duration item
and the least-reliable answer are, in this field, the same record.

**Practical consequence for any future card:** `secs` and `budget_hit` must be read together. **A duration
max taken without checking `budget_hit` measures the cap, not the model.**

## WHAT THIS SETTLES

- **The claim, as stated, is refuted on this field.** A single move did not take eight minutes; the longest
  took 2.43.
- **The number behind it is real and is an entrant duration.** So the transcript was not inventing — it was
  **relabelling**, which is the harder error to catch and the one this project keeps finding.
- **And it is the first claim in this project refuted by a measurement that did not exist when the claim was
  made.** The clock was built precisely because the claim could not be settled without it, and it has now
  settled one.
