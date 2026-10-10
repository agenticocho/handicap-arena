# FINDING 022 — THE LAUNCH CONFIG WAS A CARRIER TOO, AND IT WAS NEVER WRITTEN DOWN

**The Chair measured this outside the arena: Ornith-1.5-9B with thinking ON returned 2314 tokens and no
commitment on a real chess position; the SAME WEIGHTS with thinking OFF held a format, carried instructions
across turns, and compressed accurately. Same model, two settings, opposite outcomes.**

**Checked in our tree, and the finding is worse here than a missing field.**

---

## 1. THE BUILD SUPPORTS IT AND OUR LAUNCHER PASSED NONE OF IT

```
llama-server on this box:
  -rea, --reasoning [on|off|auto]     (env: LLAMA_ARG_REASONING)
  --reasoning-format  --reasoning-effort  --reasoning-budget  --chat-template-kwargs

our launcher before this change:
  [LLAMA, "-m", entrant, "-c", "4096", "-ngl", "0", "--port", str(port), "--no-webui"]
```

**No reasoning flag. So the setting was `auto` — decided by each model's own default, recorded nowhere, and
invisible for exactly the reason the Chair gave: it was never written down.** *Same shape as the legend:
yesterday the PROMPT could describe the wrong task; today the LAUNCH CONFIG can.*

**AND IT IS NOW SET DELIBERATELY AND RECORDED. `SOKOBAN_REASONING`, default `off`, because every cabinet here
asks for a SHORT answer — one letter, one digit, one word — and that is the format a non-thinking model is
built for and a thinking model will fight.**

**IT APPLIES TO FUTURE RUNS. The runs already taken were taken at `auto` and their numbers STAND AS RECORDED.**

## 2. THE FIELD NAMES, AS ASKED

```
config.reasoning_requested          "off" (the deliberate setting; SOKOBAN_REASONING on|off|auto)
config.reasoning_argv               ["--reasoning","off"] -- THE ARGV, not a summary of it
config.reasoning_supported_by_build true  (this build answers --reasoning)
config.max_tokens_ceiling           64    <- THE CEILING, distinct from...
config.command_cap                  8     <- ...how many turns were allowed. TWO ceilings, one word before
config.server_argv                  the whole launch, so the record says what was run
reasoning_probe                     {question, answer, completion_tokens, finish_reason,
                                     observed, requested, disagrees_with_config}
budget_signature                    {turns, turns_that_hit_the_ceiling, ceiling, fraction_capped,
                                     all_turns_capped, reading}
```

**`reasoning_probe` RECORDS WHAT HAPPENED, NOT WHAT WAS ASKED FOR.** The flag says which setting was
requested; the probe says which one the model is actually running under, and **when those two disagree the
disagreement is the finding.** A config field nobody measured is the same class as a legend nobody read.

## 3. AND THE PROBE'S FIRST RESULT IS A NEGATIVE ONE, WHICH IS WHY IT IS A PROBE

**On this box, for `granite-3.3-2b-instruct-critical-thinking`, `--reasoning on` and `--reasoning off` produce
IDENTICAL results on a one-token question: 3 completion tokens and 2, both `finish_reason: stop`, in both
arms.** So **the flag is a NO-OP for this model** — it has no reasoning mode wired into its template — **and
the capping measured below is NOT a reasoning artifact for it.**

**THE FLAG'S EFFECT IS MODEL-DEPENDENT AND IS NOW MEASURED RATHER THAN ASSUMED.** A cabinet that set the flag
and recorded it would have believed it had controlled something. **It had not, for this entrant.**

## 4. THE AUDIT: FIVE CELLS HIT THE CEILING ON EVERY TURN, AND NOBODY HAD CHECKED

**Ran the budget signature retroactively over every artifact that still has per-turn rows:**

```
granite-3.3-2b  01_one_push   OLD arm    turns 40  capped 38   <- the A/B's "locked on U" arm
granite-3.3-2b  02_two_boxes  OLD arm    turns 40  capped 40   <-- BUDGET-CONFOUNDED
Qwen3.5-4B      02_two_boxes             turns 40  capped 40   <-- BUDGET-CONFOUNDED
Qwen3.5-9B      01_one_push              turns 40  capped 40   <-- BUDGET-CONFOUNDED
Qwen3.5-9B      02_two_boxes             turns 40  capped 40   <-- BUDGET-CONFOUNDED
the RECOVERED population run (7 cells)   NO PER-TURN ROWS -- UNKNOWABLE FROM THE RECORD
```

**AND THE HONEST READING, WHICH IS NOT SIMPLY "ALL OF IT IS VOID":**

**The frozen read-grammar reads the FIRST TOKEN of the first line. The cap cut the PROSE AFTER that token.**
For `granite` the tokens were `U` and `R` — **one letter, then a long explanation that ran into the ceiling.**
**So the head readings survive the capping** — a capped turn still has a valid answer at the head, and
`not_an_action` on those cells is still a read of the head.

**THE EXCEPTION IS THE ONE THAT MATTERS, AND IT IS THE CHAIR'S CASE EXACTLY:** **a reasoning model puts its
DELIBERATION where the answer should be and the answer comes AFTER it.** Cap that and there is no head to
read — **2314 tokens, no move.** For those, **the budget signature and the head reading are the same
question**, and the ceiling decides whether an answer exists at all.

**AND ONE CELL IS WORSE THAN CONFOUNDED: THE RECOVERED POPULATION RUN HAS NO PER-TURN ROWS.** Its counters
are exact as printed and **its budget signature is UNKNOWABLE.** That is a hole in the record of the same
shape as the chess one: named, not filled by re-running.

## 5. AND THE BUG THIS FOUND IN MY OWN READER, WHICH IS THE REAL PRIZE

**`ask()` falls back to `reasoning_content` when `content` is empty — and that fallback would have read the
FIRST TOKEN OF A TRUNCATED DELIBERATION AS AN ANSWER.**

**THE ORNITH CASE, SITTING IN MY OWN CODE:** a thinking model caps out mid-deliberation, `content` is empty,
the fallback mines a token out of the deliberation, **and the harness scores a sentence fragment as a legal
action.** That is the greedy-`{.*}` reader, the `RESIGN → R` reader, and the name whitelist, arriving in the
one place none of them were guarding: **the API response.**

**FIXED: the fallback is KEPT — it is the only way a thinking model's answer is ever read — and it now TRAVELS
WITH ITS PROVENANCE.** A turn whose answer came from `reasoning_content` AND hit the ceiling is returned as
**`capped-deliberation-missing-value`**, an EMPTY answer, and the turn carries `missing_value: true`.
**An empty answer the harness produced is a MISSING VALUE — never an illegal move, never scored zero, never
dropped.** That rule was already written for chess; it had not been applied to the transport.

## 6. THE THIRD LEVEL CAUGHT THE FIRST ENTRANT IT EVER SAW, ON MOVE ONE

**Demonstration run, not a scored run — no criteria are frozen for level 03.**

```
granite-3.3-2b on 03_the_corner_waiting, cap 8, reasoning off
  tokens  ['U', 'R', 'R', 'R', 'R', 'R', 'R', 'R']
  moves 4   blocked 4   not_an_action 0   give_up 0
```

**`U` is the PROVEN-FATAL opening move. The entrant took it first, then made four legal walks around a level
that could not be finished.** n=1, and a demonstration, not a verdict — **but the instrument recorded exactly
the behaviour it was built to record, and `sokoban_deadend.py` says why the remaining moves were futile.**

**AND IT EXPOSES A GAP FOR NEXT: the counters cannot distinguish PROGRESS from WALKING AROUND A DEAD LEVEL —
`moves 4` reads as four successful actions either way. The dead-end verdict must travel in the record beside
the counters, not only in the mapper's output.**
