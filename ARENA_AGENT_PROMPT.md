# PROMPT FOR ARENA.AI'S AGENT — paste this into the agent box

You are building an independent Sokoban cabinet for The Handicap Arena, in this repo.

**This is a SECOND, INDEPENDENT implementation. Do not read `sokoban.py` or `sokoban_run.py` until you
have finished and are ready to diff against them.** The value of this exercise is finding where the
contract is ambiguous — and that only works if you are not looking at the first implementation. Reading
it early destroys the entire result. You may diff at the end; you will be asked to.

## READ FIRST, IN THIS ORDER

1. `SOKOBAN_READ_GRAMMAR.md` — how an answer is READ. This is frozen. Do not reinterpret it.
2. `levels/01_one_push.txt`, `levels/02_two_boxes.txt`, `levels/03_the_corner_waiting.txt`
3. `CABINET_SOKOBAN_DOSSIER.md` — section 12 states what has already been run and what it found
4. `ARENA_AGENT_BRIEF_sokoban.md` — the full brief, if it is present in the branch you are reading

## FROZEN — DO NOT CHANGE

- **The levels and their shortest solutions.** Independent answers: 1, 12, and 6 moves.
  **Verify them yourself before any entrant runs.** A result measured against an unverified reference is a
  number, not a finding.
- **The transition function**: `step()` returns **TWO** values — the position after the action, and a word
  saying what happened. **Not three.** (An entrant got this wrong once and every call raised.)
- **The criteria**: what counts as solved, and what is scored.

## BUILD

1. **A simulator** implementing the transition function, passing all three levels.
2. **A runner** that gives the task, collects the answer, and **checks the answer by executing it** — never
   by reading it.
3. **A scorer** that reads answers by the read grammar. **ONE reader of record, imported by every side
   script, never reimplemented.** Two readers for one record is a defect, and it fails toward the
   better-looking number.

## DONE MEANS MEASURED, NOT CLAIMED

- Every run **writes its record to disk BEFORE the success/failure branch.** The failure path is where the
  record matters most; ours wrote nothing there.
- A failed load **NAMES THE HOLDER** — the process holding the memory — never `failed to load`.
- The record carries the model file's **DIGEST**, not only its name. Two same-named files in two
  directories is otherwise an unresolvable confound.
- **The record says which CODE produced the verdict**, not only the verdict. Without it, *"it ignored the
  correction"* and *"it tried and failed"* are indistinguishable — and they are not the same finding.
- **The exit code reflects the run.** Ours was a constant `1` for every real invocation and nobody caught
  it, because the self-test never reached the code path that raised.

## AND STATE THE TWO FIELDS THAT DECIDE EVERYTHING

Per run, in the record: **the reasoning setting** and **the GPU**. Same weights with thinking ON versus OFF
produced **opposite outcomes** on this project's cabinet task — the default produced no answer at all at
three separate token ceilings, while thinking OFF answered 5 of 5. **A setting nobody wrote down is
indistinguishable from a decision.**

## REPORT WHEN YOU ARE DONE

1. **What you built**, and what you verified independently.
2. **What you ran**, entrant by entrant, with the numbers.
3. **THE THREE THINGS IN THE CONTRACT YOU HAD TO GUESS AT.**

**That third item is the result we actually want.** A second implementation exists to find where the
contract does not speak — a second implementation of this project's render format already found ten
ambiguities that neither side could see alone. **Name them; do not paper over them.**

**And name anything you think is WRONG in the frozen artifacts.** A disagreement you can evidence is worth
more to us than agreement.
