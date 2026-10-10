# SOKOBAN — POPULATION RUN 2. THE FIRST RUN THE CABINET'S CRITERIA ARE MET ON.

**Run of record:** `probes/SOKOBAN_RUN_20261010-072252.json` — its own path, three levels, the declared
reasoning setting, the budget signature, the dead-end verdict, and the A7 format fields.

---

## THE NUMBERS, FROM THE RECORD

```
cells 15   PLAYED 12   NEVER_STARTED 3 (Ternary-Bonsai-2-27B, rc=1 on all three levels)

entrant                  level                  ended               moves  blocked  unreadable
LFM2-350M-Extract        01_one_push            commands_exhausted      0        0         40
LFM2-350M-Extract        02_two_boxes           commands_exhausted      0        0         40
LFM2-350M-Extract        03_the_corner_waiting  commands_exhausted      0        0         40
granite-3.3-2b           01_one_push            SOLVED                  1        2          0
granite-3.3-2b           02_two_boxes           commands_exhausted      4       36          0
granite-3.3-2b           03_the_corner_waiting  commands_exhausted      5       35          0   DEAD END
Qwen3.5-4B               01_one_push            SOLVED                  1        0          0
Qwen3.5-4B               02_two_boxes           commands_exhausted      8       32          0
Qwen3.5-4B               03_the_corner_waiting  commands_exhausted     12       28          0
Qwen3.5-9B               01_one_push            SOLVED                  1        0          0
Qwen3.5-9B               02_two_boxes           commands_exhausted     12       28          0
Qwen3.5-9B               03_the_corner_waiting  commands_exhausted     12       28          0

per level   01: played 4 solved 3     02: played 4 solved 0     03: played 4 solved 0
```

## THE CRITERIA, AND BOTH OF THEM ARE MET FOR THE FIRST TIME

```
C1  SCALE IS VISIBLE   at least one level solved by >=1 entrant, AND >=1 level solved by NONE
                       -> 01 solved by THREE, 02 and 03 solved by NONE.  C1 MET.
C2  THE FLOOR          at least one entrant solves 01_one_push (1 move)
                       -> three did.  C2 MET.
C3  MOVES ARE A NUMBER the count travels with blocked / not_an_action / give_up, never merged.  C3 MET.
```

**THREE ENTRANTS SOLVED `01_one_push`, and TWO OF THEM SOLVED IT WITH ZERO BLOCKED — first action, no
wall-bumping.** That is the first time anything in this cabinet has solved anything.

## AND THE COMPARISON I AM NOT GOING TO OVERCLAIM

```
same model         previous run (2 levels)      this run (3 levels)
Qwen3.5-4B         unreadable 43, solved 0      unreadable 0, solved 1
Qwen3.5-9B         unreadable 40, solved 0      unreadable 0, solved 1
granite-3.3-2b     unreadable  0, solved 1      unreadable 0, solved 1
```

**BOTH QWEN ENTRANTS WENT FROM PRODUCING NOTHING READABLE TO SOLVING A LEVEL.** And the tempting sentence is
*the reasoning flag did it* — **because the declared setting is the only config change.**

**I AM NOT WRITING THAT SENTENCE. THREE THINGS CHANGED AT ONCE**: the launch now passes `--reasoning off`,
the launcher's argv changed, and a third level was added (which changes no cell, but it is a different run).
**One run is not a controlled comparison, and this project has spent a week on what happens when a plausible
mechanism is written down beside a true number.**

**THE TEST THAT WOULD SETTLE IT IS NOW ONE RUN AWAY, AND THE PARAMETER IS WIRED FOR IT:**
`SOKOBAN_REASONING_TEST_ARM=on|off` sets the arm and the record marks it as an OVERRIDE rather than a
declaration. **Same entrants, same levels, two arms, and the difference is measured instead of inferred.**

## THE PROBE, AND THE ONE PLACE IT LIED

```
entrant                  requested  observed  tokens  disagrees
LFM2-350M-Extract        off        on        33      True
granite-3.3-2b           off        off        3      False
Qwen3.5-4B               off        off        2      False
Qwen3.5-9B               off        off        2      False
```

**`observed: on` FOR LFM2 IS A FALSE INFERENCE.** Its 33 tokens are not deliberation —
**its answer is `{"answer": "2 + 2", "answer": "2 + 2", ...}`, an extraction model ECHOING THE QUESTION AS
JSON.** The probe's threshold is on ANSWER LENGTH, and length cannot see why the answer is long.

**FIXED BY SPLITTING THE MEASUREMENT FROM THE INFERENCE:** `observed_answer_shape` ("short"/"long") is what
came out; `observed` is what it is taken to mean, now labelled `observed_is_an_inference: true` with a
written caveat. **A TRUE MEASUREMENT WAS BEING USED TO MAKE A FALSE STATEMENT ABOUT A MODEL, which is the
same defect as a field name claiming more than its contents.**

**AND THE DISAGREEMENT FIELD STILL EARNED ITS PLACE:** LFM2 is flagged as anomalous, correctly. The flag was
right; the name it gave the anomaly was wrong.

## AND THE DEAD END IS NOW IN THE RECORD, BESIDE THE COUNTERS

**`granite-3.3-2b` on `03_the_corner_waiting`: `moves 5, blocked 35`, and `dead_end.no_solution_from_here:
true`, proved by a sound rule at the start.** Without that field the row reads as five successful actions.
**This is the first dead-end datum the cabinet has produced, and it is the faculty the event exists for.**

## SCOPE

**Four playing entrants, three levels, n=1 per cell, ONE instrument configuration.** Three entrants never
started (`Ternary-Bonsai-2-27B`, `rc=1` on every level — the resource question that has now been open across
two cabinets). **This is not a population rate and not a capability claim; it is one run of a frozen card,
and the comparison above is between two runs whose differences are named rather than controlled.**
