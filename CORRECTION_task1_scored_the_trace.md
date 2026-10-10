# CORRECTION — MY "5/5" WAS SCORED ON THE MODEL'S THINKING, NOT ON ITS ANSWER

**This retracts a claim I reported. It is the most important finding of this work, because the retracted claim
was the evidence for moving three profiles off the API.**

---

## WHAT I REPORTED

> *"A local 9B did the cabinet-shaped task correctly, zero API tokens, in 21 seconds. The work is doable
> locally."* — `brain` = Tiel-Inspired-Coder-9B, 5/5 cases matching the frozen simulator.

## WHAT THE N SWEEP SHOWED, ON THE SAME MODEL, PROMPT AND TEMPERATURE

```
N=-1 (shipped default)   stop   179 tokens   1/5
N=0                      stop   189 tokens   3/5
N=256                    stop   196 tokens   1/5
N=512                    stop   558 tokens   0/5
```

**Every arm self-terminated. The ceiling sweep never did — 1200, 2048 and 4096, all `finish_reason=length`.**
**Same model, same prompt, same temperature, opposite behaviour. That inconsistency is what sent me to the raw
text, and the raw text is unambiguous:**

```
ceiling sweep arm   head = "Let me parse the requirements carefully.  We have three functions: ..."
                                                                          <- A THINKING TRACE

N sweep arm         head = "```python\ndef counters(level, tokens):\n    pos = parse(level)\n    coun"
                                                                          <- THE ANSWER
```

## THE MECHANISM, AND IT IS MY INSTRUMENT'S FAULT

**On the seat there is no `--reasoning` flag, so the model thinks. The server left `content` EMPTY and put the
deliberation in `reasoning_content`. My measuring script does:**

```python
txt = (msg.get("content") or "").strip() or (msg.get("reasoning_content") or "").strip()
```

**That fallback is CORRECT in the cabinet — a thinking model's answer has to be readable from somewhere. But in
`local_task_compare.py` I used it and then scored whatever the extraction found in the result. On the seat it
found the code INSIDE THE THINKING TRACE and called it 5/5.**

**SO THE 5/5 MEASURED THE MODEL'S DELIBERATION, NOT ITS ANSWER. THE REAL ANSWER RATE IS 1/5 TO 3/5.**

## AND THIS IS THE CABINET'S OWN DEFECT, WHICH I BUILT CORRECTLY THERE AND THEN MADE MYSELF

**`sokoban_run.py` already distinguishes this exactly:**

```
answer_field    'content'  vs  'reasoning_content'
                and a capped fallback is 'capped-deliberation-missing-value', a MISSING VALUE, never scored
```

**with the comment written on the day:**

> *"Falling back to it is right WHEN THE DELIBERATION CONTAINS THE ANSWER. IT IS WRONG WHEN THE TURN WAS CUT
> OFF AT THE CEILING, because then the first token of the deliberation is NOT an answer. Reading that fallback
> as a token would score a TRUNCATION ARTIFACT as a legal action."*

**I wrote that, and then scored a deliberation as an answer in a different script on the same day, because the
cabinet enforced the rule and my side-script did not. A DISCIPLINE THAT LIVES IN ONE FILE AND NOT IN THE
INSTRUMENT AROUND IT IS A DISCIPLINE THAT HOLDS UNTIL IT IS INCONVENIENT.**

## WHAT THIS DOES TO THE TWO DECISIONS IT WAS SUPPOSED TO SUPPORT

**1. THE CAPACITY MOVE IS NOT EVIDENCED.** *"A local 9B did the task 5/5"* was the existence proof for moving
`sokoban`, `missile-command` and `zork` off `deepseek-flash`. **The corrected answer is 1/5–3/5, at temperature
0, on one task.** That is not an existence proof for anything, and it must not be used as one. **No profile
should move on this evidence.**

**2. N CANNOT BE DECLARED, AND THE SWEEP SAYS SO ITSELF.** The script's own branch fired:
*NO BUDGET PRODUCED A CORRECT ANSWER. THE DECLARATION SHOULD NOT BE MADE.* **Which is what a pre-registered
branch is for — it produced the answer "don't" without anyone having to be brave about it.**

## AND WHAT SURVIVES, BECAUSE NOT EVERYTHING IS RETRACTED

- **The A/B is untouched.** It was measured inside the cabinet, which distinguishes `content` from
  `reasoning_content` and records `answer_field` on every turn. **Its cells were never scored on a trace.**
- **The `finish_reason=length` rule is untouched and is now better supported**: the ceiling sweep's `length` at
  every size was *"we stopped it, and it kept thinking"* — the very case `cap_cut` now names.
- **The entrant digest is untouched** and its independent verification (`sha256sum`) stands.
- **AND THE FAILURE MODE IS CONSISTENT ACROSS EVERY ARM THAT HAD NO ROOM**: N=256 wrote
  `class Action(Enum): RESIGN = "RES"`, N=512 wrote `class Token:`. **Given less room, the model invents its own
  API instead of calling the one it was handed** — the same failure as the thinking-off arm, now seen four
  times. **That is a real, repeatable observation about this model and it is worth more than the number it
  replaced.**

## WHAT I HAVE NOT DONE

**Nothing sent. No profile moved. No config changed.** **And I have not deleted the earlier document: the
5/5 claim stands in `TASK1_LOCAL_AGENT_COMPARISON.md` with this correction pointing at it, because a retracted
number that vanishes cannot be checked by anyone.**
