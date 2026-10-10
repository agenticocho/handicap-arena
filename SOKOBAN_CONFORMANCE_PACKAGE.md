# SOKOBAN CONFORMANCE PACKAGE — SOURCE LIST, FIELD NAMES, AND THE PUBLISH/PRIVATE SPLIT

**For the Chair's review before anything leaves this machine. NOT FOR OUTBOUND SEND YET.**

**Proposed code name:** `SOKOBAN-CONFORMANCE-1` — the `-1` because **a frozen spec must carry a version, and
a version that can be bumped without a new name is not an identity.**

---

## 1. THE SOURCE LIST — GATHERED, WITH DIGESTS, NOT RECALLED

Every file below was read to produce this list. Digests are `sha256`, first 16 hex, taken now.

```
PREREG_sokoban.md                11535 B  625c07ad7c8792db   the frozen criteria, the outcome rows,
                                                            and the DECLARED CONFIG
sokoban.py                       17047 B  186f561facd44916   the simulator; its --self-test IS its contract
verify_levels.py                  5385 B  d8671df3fee59258   the VERIFIER: replays a PUBLISHED solution
                                                            per level; independent of the simulator
levels/01_one_push.txt              18 B  db6ca59655f0d7d1   1 move, BFS-verified
levels/02_two_boxes.txt             45 B  7549657f1768607c   12 moves, BFS-verified; fatal fraction 0.000
levels/03_the_corner_waiting.txt    48 B  77d18407a001da29   6 moves, BFS-verified; ONE PROVEN FATAL
                                                            OPENING; fatal fraction 0.250
CABINET_STRUCTURE.md              5946 B  28e22bb97440cd9f   the four rules and the standing rules
sokoban_solver.py                33371 B  8b1eddc9d9969f35   SOLVABLE / UNSOLVABLE / BUDGET_EXHAUSTED
sokoban_deadend.py               10957 B  908e784538a77415   the dead-end mapper
check_format_fields.py           18194 B  f256da8eb2194adb   the A-ruling format check
PREREG_reasoning_ab.md            4493 B  4ba518eda4dd0a8c   the reasoning A/B, pre-registered
```

**AND ONE FILE IS NOT IN THIS REPO, WHICH IS ITSELF A FINDING:**

```
SOKOBAN_READ_GRAMMAR.md          OUTSIDE THE REPO -- it lives in the Hermes workspace, not in the arena.
                                 A FROZEN INSTRUMENT THAT IS NOT VERSIONED WITH THE THING IT SCORES is a
                                 frozen instrument that can go missing. It must be copied in before the
                                 package is assembled.
```

## 2. THE FIELD NAMES — EXTRACTED FROM THE CODE THAT WRITES THEM

**Every list below is read out of the dict literal that owns it, via `ast`. THE FIRST VERSION OF THE EXTRACTOR
TOOK A FIXED-WIDTH WINDOW AFTER A MARKER AND BLED ACROSS NEIGHBOURING DICTS** — the list it produced for the
config block was actually the cell record's keys. **A field-name extractor that bleeds is a
false-verification machine: it produces a list that looks checked and is wrong.** It now identifies each dict
by a distinguishing key, and **reports a miss as a MISS rather than as an empty list.**

**CELL COUNTERS — `sokoban.py`, `play()`**

```
solved  moves  attempted  blocked  not_an_action  give_up  gave_up_at  ended  trace  final_board
```

**CELL RECORD — `sokoban_run.py`, `run()`**

```
entrant  level  loaded  load_s  turns  cap  final_screen  legend  legend_digest
kind  unreadable  unreadable_is_the_aggregate_of  missing_values  missing_values_are_a_subset_of
never_started  config  reasoning_probe  budget_signature  dead_end
```

**CONFIG BLOCK — `sokoban_run.py`**

```
reasoning  reasoning_source  reasoning_declared  reasoning_declared_in  reasoning_rationale
reasoning_changed_from_declaration  reasoning_argv  reasoning_supported_by_build
max_tokens_ceiling  command_cap  ctx  n_gpu_layers  temperature
legend  legend_digest  server_argv
```

**REASONING PROBE — `sokoban_run.py`, `probe_reasoning()`**

```
question  answer  answer_from_reasoning_field  completion_tokens  finish_reason
observed_answer_shape  shape_threshold_tokens          <- THE MEASUREMENT
observed  observed_is_an_inference  inference_caveat  requested  disagrees_with_config
                                                        <- THE INFERENCE, kept separate
```

**BUDGET SIGNATURE — `sokoban_run.py`**

```
turns  turns_that_hit_the_ceiling  ceiling  fraction_capped  all_turns_capped  reading
```

**DEAD-END CELL — `sokoban_run.py`, `dead_end_verdict()`**

```
checked  first_action  no_solution_from_here  proof_kind  proof_rule
reachable_states_enumerated  states_expanded  reading  unknown  still_solvable_in  budget
```

**RUN RECORD — `sokoban_batch.py`, `meta` (+ the nested blocks)**

```
run_id  kind  legend  legend_digest  levels  simulator_digest  host  freeze  cells
        never_started  unreadable  unreadable_note          <- added at write time

freeze :: simulator  verifier  dead_end_verifier  why_this_field_exists
host   :: node  platform  cpu_count  nvidia_smi
```

## 3. AND THE THING THAT MUST BE CAUGHT BEFORE ANYTHING LEAVES THIS MACHINE

**THE RECORD AS IT STANDS CONTAINS TWO BLOCKS THAT CANNOT BE PUBLISHED:**

```
host    :: node, platform, cpu_count, nvidia_smi     <- MACHINE NAMES AND HOST DETAILS
config  :: server_argv                               <- ABSOLUTE LOCAL PATHS AND THE LAUNCH LINE
```

**The Chair's constraint is explicit: no credentials, no local paths, no machine names, no host details.**
**So a PUBLISHED record shape must name these as LOCAL-ONLY FIELDS THAT A CONFORMING IMPLEMENTATION DOES NOT
PRODUCE** — and the guide must say so, because **an external builder following the record shape literally
would publish a local path in a public spec.**

**THIS IS EXACTLY THE CLASS OF THING THAT GOES WRONG IN A HAND-OFF, AND IT WAS FOUND BY READING THE FIELDS
RATHER THAN BY READING THE PROSE ABOUT THEM.**

## 4. WHAT THE PACKAGE MUST STATE, AND IN WHICH VOICE

```
THE EVENT       a simulator, three levels with BFS-VERIFIED shortest solutions, a read-grammar that is
                FROZEN, a frozen criteria set, and a declarative record
THE CONTRACT    the answer is ONE LETTER; a malformed answer is never a wrong move; unreadable is INSIDE
                the denominator; never_started is OUTSIDE and separate
THE OUTCOME     what it IS, not what it hoped to be: 15 cells, 12 played, 3 never_started, ONE level
                solved by three entrants, two levels solved by none, and one PROVEN dead end on level 03
THE METHOD      that this was built and run on one machine, by one agent, against a frozen card
```

**AND THE EXTERNAL RESULT COMES BACK AS AN EXTERNAL DERIVATION, RECORDED AS ONE** — who built it, from what,
**and that it was never run on this box.** *The method is part of the claim.*
