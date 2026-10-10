# TASK 2 — A SECOND, DIFFERENTLY-SHAPED TASK. THE RESULT IS SPLIT, AND THE FAILURE IS SPECIFIC.

**The Chair asked for a second task of different shape before three profiles move. This is it, and the answer is
NOT a clean pass — which is the useful part.**

---

## THE TWO TASKS, AND WHY THEY ARE ACTUALLY DIFFERENT

```
TASK 1   write code that CALLS a provided API            shape: LOGIC
         (apply tokens, count outcomes)                  fails by a wrong COUNT
TASK 2   write code that PRODUCES an exact TEXT FORMAT   shape: SERIALIZATION
         from a data structure                           fails by ONE WRONG CHARACTER
```

**Task 2 is not task 1 twice. There is almost no control flow, nothing to consult for the answer, and a single
misplaced glyph fails it. The hardest part of the spec is the two compound rules — a player or a crate standing
ON a target needs a different character than the same thing on bare floor — and those only occur mid-solution,
which is why the check runs EVERY INTERMEDIATE STATE of all three verified solutions rather than the three
initial boards. 22 cases.**

**And the spec is BUILT BY READING `sokoban.py`'s CONSTANTS AT RUN TIME**, so the format cannot drift from the
implementation it is checked against. A format stated from memory of the code is the same defect as a field name
stated from memory of the code.

## THE RESULT

```
task 1  (logic)          5/5 against the frozen simulator     193 tokens  3.4 s  field=content
task 2  (serialization)  DOES NOT COMPILE                     186 tokens  3.1 s  field=content
```

## AND THE FAILURE IS NOT TRUNCATION, NOT A TRACE, AND NOT MY INSTRUMENT

**I did not report this as a model failure until I had eliminated my own instrument, because I made exactly that
mistake once today.** The check, run rather than asserted:

```
finish_reason                     stop
raw text ends its fence           True
extracted code is a prefix of it  True
fenced blocks in the raw text     2
```

**The model's output is COMPLETE. It chose to stop. The extraction cut nothing.**

**And the bug is visible in the model's own source:**

```
line.append('+ if cell in targets else '@')
line.append('* if cell in targets else "$"')
```

**IT WROTE THE CONDITIONAL EXPRESSION INSIDE THE STRING LITERAL.** So `'+ if cell in targets else '` is one
string, the `'` before `@` closes it, and the rest is a `SyntaxError: unterminated string literal`.

**IT GOT THE SIMPLE RULES RIGHT AND THE COMPOUND ONES WRONG.** Walls, floor, targets, the unordered crates — the
model handled all of those. It broke precisely where the spec says a cell needs a DIFFERENT CHARACTER depending
on a SECOND condition, which is the only genuinely two-argument part of the task.

## WHAT THIS SAYS ABOUT THE CAPACITY QUESTION

**One pass, one fail, across two differently-shaped tasks. THAT IS NOT AN EXISTENCE PROOF FOR ANYTHING, AND IT
IS EXACTLY WHY THE CHAIR WAS RIGHT TO WITHHOLD THE MOVE ON ONE TASK.**

**The failure is more informative than the pass would have been alone:**

- **It is SPECIFIC** — one construct, at the compound rules, not a general collapse.
- **It is REPRODUCIBLE** — temperature 0, so this output is deterministic, not one unlucky sample.
  **CORRECTION (added after the N sweep, `N_VERDICT.md`): the claim is narrower than it reads.** Determinism at
  temperature 0 is **a property of the ARM, not of the setting** — an unbudgeted arm reproduced to the token, a
  budgeted one did not, same weights, same box, same task. **This verdict's run was made WITHOUT a budget, so
  the claim stands here; it does not stand as a general statement about temperature 0.**
- **It is LOCALISED** — a model that can produce 24 lines of correct structure and then put a ternary in a string
  is failing at something addressable, not at the task.

**AND IT SHARPENS THE EARLIER `Action(Enum)` OBSERVATION WITHOUT THE ARGUMENT I BUILT ON IT.** I had claimed
*given less room, the model invents its own API.* That claim is retracted. **But there is a weaker, defensible
version visible in both failures: THE MODEL SOMETIMES ANSWERS A QUESTION WITH THE SOURCE TEXT OF THE ANSWER
RATHER THAN ITS VALUE** — it wrote `class Action(Enum): moved = "moved"` where an API call was asked for, and it
wrote `'+ if cell in targets else '@'` where a character was asked for. **Both are a confusion between a thing
and the expression that denotes it. n=2, different settings, different tasks — a hypothesis, not a finding.**

## WHAT I HAVE NOT DONE

**Nothing sent. No profile moved. No config changed.** **And I am not retrying task 2 to get a pass: a second
attempt after seeing the first is not the same measurement, and the honest number is the one above.**
