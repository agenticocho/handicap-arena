# TASK 1 — THE COMPARISON THE CHAIR ASKED FOR. IT DOES NOT SUPPORT "THINKING OFF".

**One real cabinet task, one local alias, two reasoning settings, everything else held.**

---

## THE MEASUREMENT

**Alias:** `brain` → `Tiel-Inspired-Coder-9B-UD-Q4_K_M.gguf` (read from the seat definition, not recalled)
**Task:** write `counters(level_text, tokens)` against a provided three-function API
**Scored by:** RUNNING the output against the frozen simulator's own `play()` — five cases across the three
**verified levels. A function that does not compile is not a result; a function that compiles and disagrees is
a measured disagreement.**

```
setting                                  compiles?   cases   completion tokens   finish_reason   wall
thinking DEFAULT (as the seat ships)        yes       5/5          1200              length       20.9s
thinking OFF (enable_thinking=false)        yes       0/5           190              stop         3.2s
```

## AND THE MECHANISM IS VISIBLE IN THE OUTPUT, WHICH IS WHY THIS IS NOT NOISE

**Thinking OFF, the model's first lines are:**

```
from enum import Enum
class Action(Enum):
    moved = "moved"
    pushed = "pushed"
```

**IT INVENTED ITS OWN API INSTEAD OF CALLING THE PROVIDED ONE.** `parse`, `step`, `solved` and `ACTIONS`
were named in the prompt. **Given less room to work the problem over, it stopped consulting the interface it
was handed and substituted its own.** The code compiles — that is why it scored 0/5 rather than "invalid".

**Thinking DEFAULT, it used the provided functions and matched the frozen simulator on all five cases.**

## THIS DOES NOT CONTRADICT THE CHAIR'S RULE. IT CONFIRMS IT — AND IT CONTRADICTS THE APPLICATION TO THIS JOB.

**The Chair's rule, stated correctly, is that *the reasoning setting travels with the task*: one-letter
answers want it off, multi-step work wants it on. Both measurements now agree with the RULE:**

```
the GAME      answer is ONE LETTER, decoded from the head        thinking ON  -> EMPTY CELL (see the A/B)
                                                                 thinking OFF -> readable, and it moves
the CODE      answer is a FUNCTION that must call an API         thinking OFF -> compiles, 0/5, WRONG API
                                                                 thinking ON  -> compiles, 5/5
```

**So the rule holds. What the measurement contradicts is the specific mapping the Chair proposed for task 1 —
*A cabinet agent writing a simulator wants thinking OFF, it is doing structured edits and short answers*.**
**WRITING A SIMULATOR IS NOT A SHORT ANSWER.** It is exactly the multi-step, use-the-provided-interface job
the rule says wants deliberation. **"Structured edits" describes the SHAPE of the diff, not the SHAPE of the
inference.**

## THE SCOPE, STATED SO THIS CANNOT BE READ AS MORE THAN IT IS

- **Temperature 0.0, so the answer is DETERMINISTIC: n=1 per setting is REPRODUCIBLE, not sampled. Repeating
  it at this temperature returns the same bytes.** The generality limit is **TASKS, not trials** — one task,
  one alias, one model. It does not establish that every cabinet code task behaves this way.
- **`enable_thinking:false` is the CHAT-TEMPLATE switch, not the server's `--reasoning off`.** They are not
  proven equivalent here, and the honest statement is that this measures **the chat-template switch on this
  template.**
- **The default arm also hit its 1200-token ceiling** (`finish_reason=length`) and still scored 5/5 — so the
  winning arm was itself constrained, which makes the result if anything conservative.
- **The 0/5 is one wrong answer, not a distribution.** At temperature 0 there is no distribution to have.

## AND THE HEADLINE FOR THE CAPACITY QUESTION, WHICH IS WHAT THE CHAIR ACTUALLY ASKED

**A local 9B DID the cabinet-shaped task, correctly, with zero API tokens, in 21 seconds.** That is the
existence proof the move needs: **the work is doable locally.** **But the seat it was done on sets NO
`--reasoning` FLAG AT ALL** — checked in `llama-swap.yaml`, none of `brain`, `critic1`, `helper` or
`ocho-planner` sets one — **so every local seat currently serves at the DEFAULT, and the default is the arm
that worked here and the arm that produced an empty cell in the A/B.**

**SO "POINT THE PROFILE AT llamacpp" IS NOT SUFFICIENT ON ITS OWN.** The seat's reasoning setting has to be
declared with the same care as the cabinet's, **because a cabinet agent that deliberates into its ceiling on a
one-letter task returns nothing, and that is already measured.**

## WHAT I HAVE NOT DONE

**Nothing has been moved. No profile config has been changed. Nothing has been sent anywhere.** The Chair's
instruction was to measure one first and report the comparison; this is that comparison.
