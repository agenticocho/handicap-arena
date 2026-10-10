# NEXT WINDOW — HANDOFF

**Written at the close of the off-peak window. HEAD `d413b81`, tree clean, no unit running.**

---

## WHAT LANDED THIS WINDOW

```
A6 + measured>0     the gate is now a PAIR: coverage AND yield AND measured>0, as one expression.
                    21/21 controls, BOTH sides -- red on coverage 1.000 with nothing measured, green with
                    something measured. It used to fire AFTER the verdict printed; a condition after the
                    verdict is not part of the verdict.
null footprint      print_card() threw on a host with no nvidia-smi, so a macOS run produced NOTHING and
                    failed at the LAST step. Now: null + a DERIVED reason, never 0.00. The control's own
                    gap was found and fixed -- the Darwin branch is FORCED, not waited for.
the legend A/B      DECISIVE and REPEATED: new 3/3 solved, old 0/3. BRANCH 3, not branch 1.
the read-grammar    frozen; §5 AMENDED because the measurement does not support its stated mechanism.
the solver          MERGED after I ran the read-control myself: EXACTLY 1 and 12, controls 60/60.
cabinet structure   three worktrees (own indexes, isolation PROVEN), cabinet_results/ as a separate root.
```

## THE ONE THING TO CARRY FORWARD, BECAUSE IT IS EASY TO GET WRONG

**The legend fix is REAL and its stated reason is NOT.** `not_an_action` did not move — 0 in both arms.
**granite locked on the first listed control.** Schema-filling is real but belongs to the *extraction model*,
which the fix does not reach (40 → 40). **Do not write "the schema-filling explanation was confirmed" into any
document.** The freeze record states the three things separately: what is true and measured, what is true and
measured elsewhere, and what is not established.

## NEXT, IN THE ORDER THE CHAIR SET

**1 · THE THIRD LEVEL.** The solver unblocks it: unsolvability is now provable, which was the only thing
missing. Write a level, PROVE it, and record both. Rank the levels by verified solution length — that gives a
collapse gradient for free, and `give_up` is only scoreable against a known-solvable position.
**The one-move level is the COLLAPSE CONTROL and is never retired as "too easy": its easiness IS the oracle.**

**2 · A7 AND A2–A10 AS FORMAT FIELDS.** `never_started` and `unreadable` become format fields, not privates.
A9: the freeze record carries the VERIFIER's identity too — a self-test only proves the instrument agrees with
itself. A1: an invented value is never substituted — `null` plus a WRITTEN REASON.

**3 · SOKOBAN'S POPULATION RUN UNDER THE FIXED LEGEND.** Careful: **this has already happened once and its
artifact was destroyed** by a still-live earlier run sharing the path (FINDING 020). The numbers survive only
in `logs/sokoban_rerun.out`, recovered to
`probes/SOKOBAN_RUN_20261009-1247_NEW_LEGEND_RECOVERED_FROM_LOG.json`. **A re-run is a clean record, not a
duplicate.** It now writes `probes/SOKOBAN_RUN_<run_id>.json` and refuses an existing path.

**4 · THE THREE-ARM FOLLOW-UP.** Separate the old legend's three changes — the indented `U = up` list, the
`FIRST LINE:` label, the key-value symbol line. **Right now I can say the legend was the carrier and NOT which
part of it was.** That is the honest limit of the A/B and it is written down as one.

## OPEN ITEMS, SMALL AND NAMED SO THEY DO NOT ROT

```
birdy's .env            same shape as the cabinets had: no working key set. Named, NOT touched -- nothing
                        has needed it yet.
target_busy             cabinet agents CANNOT reach me mid-session: deliveries are CANCELLED, not queued.
                        A long turn discards inbound reports. FINDING 021.
the string guard        `play(state,"1P")` and `token[:1]` are ONE root -- a string treated as a sequence.
                        Owed as a SHARED HELPER, not two copies.
the `spared` finding    a measurement that cannot see the absence it is named for. Owed into BOTH the
                        Sokoban and Missile Command preregs.
two stale repo lines    ARCADE.md:48 (chess retires to Punch-Out) and GAMES.md:149 (B2c Chess -- Calibration)
                        propose something that is no longer true.
```

## THE RULES THIS WINDOW ADDED

```
COUNTS ARE THE RESULT. RATES ARE THE INDEX.        a rate over `attempted` is improved by quitting
ONE RUN, ONE PATH.                                 a shared path means the last writer IS the record
THE IDENTITY OF A RUN IS THE INPUTS IT WAS MADE UNDER, NOT ITS PATH
A RUNNING PROCESS DOES NOT RE-READ ITS MODULE      a patch is not in effect for an already-running run
A CONTROL MUST FORCE ITS PATH, never wait for the environment to hand it one
A TABLE WRITTEN FROM MEMORY OF A FILE IS A SECOND COPY OF THE TRUTH
CONFIRMING A ROSTER MEANS CONFIRMING AN AGENT CAN RUN -- not that a profile, a unit and a route exist
EVERY ARTIFACT FROM THE CHAIR IS A CLAIM until its file is read, its count is run, its enforcer is found
```
