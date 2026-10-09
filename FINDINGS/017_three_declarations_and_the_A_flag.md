# FINDING 017 — THE NAMESPACE WAS DECLARED THREE TIMES, AND `git add -A` COMMITTED ANOTHER AGENT'S WORK

Two findings from the fan-out, both about coordination rather than about measurement, and both found by
disagreement between agents rather than by a test.

---

## 1. THREE DECLARATIONS, NOT TWO — AND THE DOC ASSERTED A MECHANISM THAT WAS NEVER IMPLEMENTED

**My account, in the escalation to the Chair, was that the declared namespace lived in TWO places and the
gate's error message named the copy that does not count. Ocho2 measured it and it was THREE:**

```
1  GAME_CONTRACT.md    the prose table          had R1_conformance
2  GAME_CONTRACT.md    the MARKER BLOCK         had R1_conformance -- and ASSERTED IN ITS OWN TEXT that
                                                it was "the SINGLE SOURCE test_game_states.py parses"
3  test_game_states.py DECLARED_SLOTS literal   DID NOT have it -- and was THE ONLY ONE READ
```

**SO "AMEND GAME_CONTRACT.md" WAS UNFOLLOWABLE IN TWO INDEPENDENT WAYS, WHICH IS WORSE THAN A WRONG
FILENAME:**

```
the named copy   is not the copy that is read
the named copy   ALREADY CONTAINED THE FIX -- in a block that NOTHING IN THE REPOSITORY PARSED
```

**A document asserting a mechanism that has never been implemented is a caption wearing a mechanism's
clothes.** *An error message is part of the instrument* — and so is a document that says "this is the
source", when nothing reads it. **The repair is the one already made: the block IS parsed now, and a control
asserts zero slots is an error rather than an empty declaration.**

**AND THE LESSON GENERALISES PAST SLOTS: A CLAIM THAT A FILE IS THE SOURCE IS A CLAIM LIKE ANY OTHER, AND IT
NEEDS A READER TO BE TRUE.** The block said it was the source. Nothing read it. It was prose.

## 2. AND MY OWN: `git add -A` COMMITTED ANOTHER AGENT'S DELIBERATELY-UNCOMMITTED WORK

**Ocho2 wrote a corrected script, measured it, and did NOT commit it — because other agents were mid-flight
in the same tree. That was the correct call and it was stated.**

**I used `git add -A` in my commits. `-A` STAGES EVERYTHING. The corrected script entered the repository in
`6be5bbb`, WHICH IS MY COMMIT, and Ocho2's working tree is now clean without their having decided that.**

```
Ocho2's reason for not committing   "other agents are mid-flight in that tree"    CORRECT
my mechanism                        git add -A                                   OVERRODE IT
outcome                             the file landed anyway, in someone else's commit
```

**THE FAN-OUT RULE IS ONE OWNER PER FILE AND SHARED FILES FROZEN. `git add -A` IS THAT RULE BROKEN BY THE
MECHANISM RATHER THAN BY A DECISION** — and it is the more dangerous form, because no one chose it and no
one can see it happen. **A commit that stages the whole tree is a commit whose author cannot say what is in
it.**

**THE FIX, and it is mechanical rather than a resolution: STAGE EXPLICIT PATHS.** In a shared tree,
`git add <paths>` and never `-A`. **A rule stated and not mechanised is a resolution, and this is the fourth
time today that distinction has cost something.**

**AND IT IS THE SAME SHAPE AS THE COMMIT MESSAGE AND THE OVERWRITTEN ARTIFACT: THE CONTENT OF A RECORD MUST
NOT BE SUBJECT TO THE PROCESS THAT CARRIES IT.** A shell substitutes a backtick; a path is overwritten by
whatever writes it next; `-A` stages whatever is loose in the tree. **Three carriers, one defect: the carrier
deciding what the record says.**

**AND BOTH AGENTS MEASURED STALE COPIES FOR THE SAME REASON** — files changing under a reader mid-investigation.
Ocho2 measured `test_game_states.py` 18 seconds after it was edited, and measured their own script before a
later commit of mine carried the corrected version in. **A READING WITH NO TIME IS INDISTINGUISHABLE FROM A
LIVE ONE**, and in a shared tree the reading must carry the commit it was taken at.
