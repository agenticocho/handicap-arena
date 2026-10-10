# BUILD THE SOKOBAN CABINET — a brief for an independent implementation

**What is being asked for is a SECOND IMPLEMENTATION, built without copying ours.** Two independent
implementations against one frozen contract is the point: it is how a contract's ambiguities get found — a
second implementation of this project's render format already found ten.

## FROZEN — do not change, do not reinterpret

| artifact | what it is |
|---|---|
| `SOKOBAN_READ_GRAMMAR.md` | how an answer is READ. The rule the axis argument rests on. |
| `levels/01_one_push.txt` | 1 move. Independently BFS-verified. |
| `levels/02_two_boxes.txt` | 12 moves. Independently BFS-verified. |
| `levels/03_the_corner_waiting.txt` | 6 moves. Independently BFS-verified. |
| the transition function | `step()` returns **TWO** values: the position after the action, and a word saying what happened. **Not three.** |
| the criteria | what counts as solved, and what is scored |

**Verify the levels yourself before any entrant runs.** A 0-of-3 against an unverified reference is a
number, not a result.

## BUILD

1. **A simulator** implementing the transition function, passing all three levels.
2. **A runner** that gives the task, collects the answer, and **checks it by executing it** — not by reading it.
3. **A scorer** that reads answers by the read grammar. **ONE reader of record, imported by every side
   script, never reimplemented** — two readers for one record is a defect, and it fails toward the
   better-looking number.

## DONE MEANS MEASURED, NOT CLAIMED

- **The levels' shortest solutions are independently verified** before any entrant runs.
- **Every run writes its record to disk BEFORE the success/failure branch.** The failure path is the one
  where the record matters most, and last time it wrote nothing at all.
- **A failed load NAMES THE HOLDER** — the process holding the memory — never `failed to load`.
- **The record carries the model file's DIGEST**, not only its name. Two same-named files in two directories
  is otherwise an unresolvable confound.
- **The exit code reflects the run.** Ours was a constant `1` for every real invocation and nobody noticed,
  because the self-test never reached the code path that raised.
- **The record says which CODE produced the verdict**, not only the verdict. Without it, "it ignored the
  correction" and "it tried and failed" are indistinguishable — and they are not the same finding.

## THE ONE FIELD THAT DECIDES THE COMPARISON

**State the reasoning setting and the GPU, per run, in the record.** Same weights, thinking ON versus OFF,
produced **opposite outcomes** on this project's cabinet task: the default arm produced no answer at all at
three separate token ceilings, while thinking OFF answered 5 of 5. **A reasoning setting nobody wrote down
is indistinguishable from a decision.**

## WHAT WE WILL COMPARE

Same levels, same read grammar, same criteria — **your implementation against ours, entrant by entrant.**
What we are measuring is not "which code is nicer." It is **whether the two implementations agree on what a
given entrant's output MEANS**, because where they disagree, the contract is ambiguous and neither of us
could see it from one side.
