# PREREG — THE RECOVERY EXPERIMENT

**Written BEFORE the first number. Committed before the run. The number is not visible to anyone when this is
written, including me.**

---

## THE QUESTION

Task 2 failed. **The failure was SPECIFIC, REPRODUCIBLE and LOCALISED** — the model got every simple rule right
and wrote the conditional expression *inside* the string literal at the two COMPOUND rules. **The Chair's
question is the one that actually decides the capacity move:**

> *is this failure recoverable with a corrective turn?*

**IT IS NOT A RETRY.** A retry asks whether the model can pass on a second independent attempt, which is a
question about LUCK. This asks whether the model can act on FEEDBACK, which is a question about what an agent
actually does. **An agent loop is not one-shot: it runs the code, reads the error, and goes again. If the model
recovers from a real error message, then a local agent is viable AS A NON-ONE-SHOT WORKER — which is a pass for
a different working pattern, not a pass for the one-shot pattern that just failed.**

**THE DECLARATION: if this returns Branch 1, the correct capacity finding is NOT "a local 9B can do cabinet
work" — it is "a local 9B can do cabinet work WITH A COMPILE-AND-FEEDBACK LOOP, and must not be run one-shot."**
**That distinction is the whole point, and it is written down before the number so it cannot be softened after.**

## THE METHOD

**Identical to task 2 in every respect that matters**: same alias, same setting (`enable_thinking=false` — the
Chair's re-taken ruling, sent as the chat-template switch because it travels with the request), the same
22 cases over every intermediate state of the three verified solutions, the same spec derived at run time from
`sokoban.py`'s own constants, and the same reader of record (ruling 79).

**ONE THING IS ADDED, AND ONLY ONE: a SECOND TURN carrying the REAL error.** The model's own code and the actual
`SyntaxError` from `compile()` — with its line and its message — are sent back with a request to fix it.

**NOTHING ELSE CHANGES.** No hint about *what* is wrong beyond what Python's own error says. No mention of the
compound rules. No mention of string literals. **The error message is the whole correction, because that is what
an agent loop would actually have.**

## THE PREDICTION

**I PREDICT BRANCH 2.** The model will fix the line the traceback NAMES and leave the SAME CONSTRUCT standing on
the other compound rule, because both lines carry the identical defect and Python reports only the first one it
hits. **A model that has understood the rule fixes both; a model that has understood the MESSAGE fixes one.**

**I am predicting this because it is the more interesting outcome and I would rather be caught predicting the
hard thing than be right about an easy one.** Recording that motive too, so a correct prediction cannot later be
presented as insight.

## THE BRANCHES

**BRANCH 1 — RECOVERED.** It compiles AND matches the frozen renderer on all 22 cases.
**READING:** the failure was a slip, not a limit. **A local agent is viable as a NON-ONE-SHOT worker** — run with
a compile-and-feedback loop, never one-shot. The capacity move becomes a question about the HARNESS SHAPE, not
about the model.

**BRANCH 2 — PATCHED THE SYMPTOM.** The named line is fixed, the same construct remains on the other compound
rule, and it still does not compile.
**READING:** it acts on the error MESSAGE, not on the rule. **This is the DANGEROUS branch**: a loop that appears
to converge while repeating the same mistake is worse than a model that fails cleanly, because the failure is
hidden inside a fix. **A local agent would need the defect found by a CHECKER, not by the model reading its own
error.** n=1, and one instance is not a pattern.

**BRANCH 3 — STILL BROKEN, DIFFERENTLY.** It compiles but fails cases, or fails to compile for a NEW reason.
**READING:** feedback reached the code but not the defect. **The failure is not addressable by a corrective turn
alone**, and the capacity move should not be made on a feedback loop either.

**BRANCH 4 — NO ANSWER.** The second turn produces no answer field.
**READING:** nothing about recovery is established. Reported as exactly that — a no-answer is not a failure of
the model's ability, it is a turn the harness could not read as an answer.

## WHAT WOULD FALSIFY A BRANCH 1 CLAIM LATER

**A single recovery does not license the move.** If Branch 1 lands, the honest next question is whether recovery
holds on a DIFFERENT task and a DIFFERENT defect class. That is not this experiment, and this experiment does not
answer it.

## AND THE CONFOUND, NAMED BEFORE THE RUN RATHER THAN AFTER

**The second turn is a SECOND SAMPLE, and it is NOT independent of the first** — it has the first turn's failure
in front of it. So this does not become n=2 for the one-shot question, and it must never be counted as one.
