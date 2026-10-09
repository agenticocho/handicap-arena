# FINDING 019 — THE PREDICTION WAS FALSIFIED, AND THE FIX WAS CONFIRMED. BOTH, BY THE SAME RUN.

The controlled A/B, run on one entrant, two verified levels, two legends. **This is the branch the branch
table was written to catch, and it caught it.**

---

## THE RESULT

```
level            arm   moves  attempted  blocked  not_an_action  give_up   first tokens
01_one_push      OLD       0        40       40         0          0       U U U U U ... (all forty)
01_one_push      NEW       1         3        2         0          0       U U R         -> SOLVED
02_two_boxes     OLD       0        40       40         0          0       U U U U U ... (all forty)
02_two_boxes     NEW       4        40       36         0          0       U U R ...     -> four moves
```

**CONTROL ON THE A/B ITSELF, run before any model loaded:** old digest `a9eb82dd2694ac9a`, new digest
`0d86057c46d4c83b`, arms differ, `FIRST LINE` and the key-value legend present only in the old arm.
**The experiment could show a difference and did.**

**AND THE FIRST SOLVED LEVEL IN THE EVENT.** granite-3.3-2b finishes `01_one_push` under the new legend having
made exactly **one move in three attempts.** Under the old legend it made **zero moves in forty.**

## THE PREDICTION WAS FALSIFIED

**PREDICTED: *a legend that does not look like a schema should move `not_an_action` DOWN.***

**`not_an_action` DID NOT MOVE. It was 0 in both arms.** By the branch table this is **BRANCH 3: THE
SCHEMA-FILLING EXPLANATION IS WRONG.** And it is wrong — **for this entrant granite never produced an
unreadable token. It produced a perfectly readable token, `U`, forty times in a row.**

**AND THE PREDICTION WAS FALSIFIED FOR A REASON THAT MAKES THE FALSIFIER WORTH ITS COST: `not_an_action` WAS
THE WRONG METRIC, AND THE BRANCH TABLE SAID SO IN ADVANCE.** A readable-but-illegal action is invisible to a
count of unreadable tokens; it appears in **`blocked`**, which is the counter that exists for it.
**Had the branch table not been written down first, the tempting move would have been to report the
`blocked` movement as the prediction being confirmed — which is the exact retrofitting the prediction
exists to prevent.**

## AND THE FIX WAS CONFIRMED — BY THE COUNTERS THAT COULD SEE IT

```
                    OLD                          NEW
01_one_push   blocked 40, moves 0        blocked  2, moves 1, SOLVED
02_two_boxes  blocked 40, moves 0        blocked 36, moves 4
```

**Forty attempts all blocked becomes two attempts and a solve.** The instrument change is real and its
effect on this entrant is large.

## WHAT THE TOKENS SHOW ABOUT THE MECHANISM — AND WHAT THEY DO NOT

**THE TOLD FACT: under the old legend the entrant is LOCKED. It emits `U` forty times on both levels and
never revises, even though the board it is shown never changes and its own move history is in front of it.
Under the new legend it emits `U U R` and varies.**

**THE MECHANISM I WOULD HAVE GUESSED IS THE MENU DEFECT ARRIVING A SECOND TIME — the old legend presents the
controls as an indented list of pairs (`U = up    D = down    L = left    R = right`) with `U` FIRST, and
the old instruction is `FIRST LINE: your next move as ONE letter`. A model that takes the first item of a
supplied list, and reads `FIRST LINE` as pointing at it, would produce exactly this: `U`, forever.**

**BUT THAT IS A HYPOTHESIS AND I AM NOT RECORDING IT AS THE CAUSE.** The A/B varies the WHOLE legend, so it
cannot separate the list format from the `FIRST LINE:` label from the key-value symbol line. **What is
PROVEN is the effect and its size; what is NOT proven is which of three changes caused it.** Isolating them
is a three-arm follow-up, not a claim.

## AND THE SCHEMA EXPLANATION IS NOT DEAD — IT BELONGS TO A DIFFERENT ENTRANT

**In the same run, LFM2-350M-Extract was unchanged at `not_an_action` 40/40 and still emitted `{`.** That
entrant's failure **is** schema-filling — it literally emits a JSON object keyed on my legend — and **the
legend fix does not reach it, because its cause is intrinsic to what an extraction model does.**

**SO THERE WERE TWO DEFECTS ALL ALONG, IN TWO DIFFERENT ENTRANTS, AND ONE FIX ADDRESSED ONE OF THEM:**

```
granite-3.3-2b      reads the prompt, emits a valid action, LOCKS ON THE FIRST LISTED CONTROL
                    -> the legend's FORMAT. The fix is decisive. 0 moves -> solved.
LFM2-350M-Extract   emits a JSON object keyed on the legend's own tokens
                    -> SCHEMA-FILLING, intrinsic. The fix does not reach it. 40 -> 40.
```

**A FIX CAN BE CORRECT AND ITS STATED REASON WRONG AT THE SAME TIME, AND ONLY A PREDICTION WRITTEN IN
ADVANCE CAN TELL YOU THAT.**

## SCOPE, AND THE ONE CLAIM IN THE FIRST DRAFT THAT WAS WRONG

**n=3 per arm after the repeat test, not n=1.** The repeat exists because a single observation cannot
distinguish a real effect from a lucky sample, and the result is a PERFECT SEPARATION:

```
new legend   n=3   varied 3/3   solved 3/3
old legend   n=3   varied 0/3   solved 0/3
```

**The new arm varies and solves every time; the old arm locks on `U` and exhausts its commands every time.
That is not a sample. It is a mechanism.**

### AND WHAT THE FIRST DRAFT OF THIS FINDING GOT WRONG

**It said the population run was taken under the NEW legend and that granite's solve in it was therefore a
replication of the A/B. THAT IS FALSE.** The artifact on disk
(`probes/SOKOBAN_FIRST_RUN.json`) is the **FIRST** run's output — **taken under the OLD legend**, because the
first run started before the prompt fix and **A RUNNING PROCESS DOES NOT RE-READ ITS MODULE.** Its granite
locked on `U` with 40 blocked, exactly as the old arm does here.

**The RE-RUN did run under the new legend, and its numbers survive in `logs/sokoban_rerun.out` because its
artifact was overwritten** — `granite/01_one_push` there reads `ended=solved`. **So the replication is real
but its evidence is the re-run's LOG, not the artifact, and the artifact must not be cited for it.** See
FINDING 020.

**WHAT STANDS: the legend change is causally responsible for granite's behaviour on this level, the
direction is large, and it reproduces 3/3.**

**WHAT DOES NOT: a population-level effect, or a Sokoban score.** One entrant, two levels. **The population
run of record is the RE-RUN — 10 cells, 7 played, 3 did not load, and one solved cell — read from
`logs/sokoban_rerun.out`, with the artifact on disk belonging to a different run entirely.**
