# CORRECTION — THE NOTE BESIDE THIS ARTIFACT ASSERTS A FIELD THE ARTIFACT CARRIES

**Filed 2026-10-16 by the Local Chair, beside the note it corrects, because the note's own closing line is
what sends a careful reader to it.**

---

## THE TWO RECORDS

```
the note   probes/SOKOBAN_Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0_01_one_push.INSTRUMENT-NOTE.md
           committed dc1375b, and it says:

             "NOT RECORDED BY THE ARTIFACT : the record contains no `server_argv` field, so without this
              note the artifact is indistinguishable from one the default binary produced."

the artifact  probes/SOKOBAN_Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0_01_one_push.json
           carries, in the field the note names:

             config.server_argv[0] = /home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server
                                     (the PRISM FORK, not the default binary)
```

**THE ARTIFACT WINS.** `PRECEDENCE.md`: *"the run log vs the artifact → the artifact"*, and *"prefer the
carrier to the claim"*. **`config.server_argv` has been written by `sokoban_run.py` since `2e4e3de`
(2026-10-10, FINDING 022) — six days before this run** — and it recorded the fork because the in-memory
override moved the very constant the field is built from.

## WHAT IS NOT DONE ABOUT IT

**THE NOTE IS NOT REWRITTEN, AND NEITHER IS THE ARTIFACT.** Both are dated, and the loser here is still
evidence: **it is a true measurement of the operator's BELIEF at the time, and that belief is why the driver
had no `--llama-server` flag.** The permanent fix is the flag, and the flag now exists
(`PREREG_sokoban_instrument4.md` carries its own change; the flag itself landed in instrument 3, `f1c0c5d`).

**THIS FILE IS NOT A REPLACEMENT FOR THE NOTE EITHER.** It is a correction filed beside it, which is where
the reader was sent: the note's last line reads *"READ THE INSTRUMENT NOTE BESIDE EACH ARTIFACT BEFORE
CITING EITHER"*, so a correction filed anywhere else would be a correction filed where the reader is not
going.

## THE RULE

**A note that instructs the reader to read it first has taken responsibility for the reader's first
sentence.** If that sentence is false, the correction belongs where the instruction points — beside the
note — and the tree's `CORRECTION_*.md` convention at the root is for claims that are read from the root.
**The measurement is `FINDINGS/024` §2; this file is the pointer a reader of the note can actually reach.**
