# PRE-REGISTRATION — SOKOBAN INSTRUMENT CHANGE 4: A RUN REFUSES TO REPLACE A RECORD IT DID NOT TAKE, AND A LOAD FAILURE SAYS WHICH CONDITION IT IS REPORTING

**Written BEFORE the code change**, in the house form of `PREREG_sokoban_instrument1/2/3.md`, and for the same
reason: **a fix whose effect is not predicted in advance cannot distinguish a repaired instrument from a
luckier sample.**

**Card:** `t_8dc430a7` (written by Ocho, assigned to the Chair). **Authority, stated rather than implied: the
CARD ITSELF is the Chair's, and the two subjects below are the two items on it whose disposition is a change to
the driver.** Items 2 and 4 of the same card are carrier decisions, not code, and they are disposed of in
`DECISION_four_dispositions_of_instrument_3.md`, not here. **No ruling is cited because none is needed: the
last card's opened question was *whose call is this*, and this one is the Chair's own.**

**Pre-image, measured at the commit this prereg is written against:**

```
sokoban_run.py   43989 B   sha256 8fe19d2441227e8d964ff24911c9a19fcee38faee5ab907f6f231a53c048a410
                 commit f1c0c5d (2026-10-16 09:52:52 -0700), the tip of main at b36ea6a
```

**AND IT IS IN NO PINNED SET** — `FROZEN_DIGESTS` names `sokoban.py` and the three level files and nothing else,
and a digest of `sokoban_run.py` is asserted nowhere in the tree (checked for instrument 3 and unchanged since).
**The new digest is not predicted and cannot be** — a digest is a function of bytes that do not exist until the
commit is made; it is recorded in the landing note appended to this file after the commit exists.

---

## 1 WHAT CHANGES — TWO SUBJECTS, ONE FILE

**SUBJECT S1 — A RUN REFUSES TO WRITE AN ARTIFACT PATH THAT ALREADY HOLDS A RECORD.** `probes/SOKOBAN_
<entrant>_<level>.json` is today written by an unconditional `json.dump(r, open(out, "w"))`, so **two runs on one
`(entrant, level)` pair write one path and the second deletes the first. MEASURED on the pre-image driver (card
`t_33042da0`, reproduced there and in `FINDINGS/024`): fork then mainline on the same cell, one artifact path, the
first run's record gone, its log gone with it.**

The gate is **at ADMISSION — before `Popen`, not at the write.** A refusal that costs a whole model load, a
whole run, and a GPU minute is not a refusal, it is a report filed afterwards; and the tree already has that
rule (`a refusal must consume nothing`). Placement is also why the log axis is closed by the same change: the
run that never starts overwrites neither the artifact nor the log.

**THE NAME IS NOT MOVED.** `probes/SOKOBAN_<entrant>_<level>.json` is a PUBLISHED convention (cited in
`GAMES.md` and in the conformance package's census), and the last card left it alone for exactly that reason.
**The fix is a refusal, not a rename** — so every existing citation keeps resolving to the same path.

**THE CONDITION, STATED AS A CHAIR DECISION RATHER THAN AS THE CARD'S ONE-LINER.** The card proposed refusing
only when the existing record's `server_binary_digest` DIFFERS. That is strictly weaker than the defect, on
three measured grounds:

```
(a) A PRE-IMAGE RECORD CARRIES NO server_binary_digest AT ALL. MEASURED, this tip: both committed Bonsai
    artifacts and every probes/ artifact written before f1c0c5d have no such key (probe_keys.py over
    SOKOBAN_Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0_01_one_push.json: server_binary_digest ABSENT). A
    digest-equality gate therefore does NOT protect the two records this card exists for -- the first
    record the acceptance run destroyed was one of them.
(b) THE ARTIFACT NAME CARRIES THE BINARY, THE LEGEND AND THE REASONING ARM NOWHERE. The legend and the
    reasoning arm were put into the LOG name for this reason and never into the artifact name
    (FINDING 024 §1), so a same-binary run on the other arm of the A/B would still delete arm A silently.
    A digest-only gate leaves that axis open.
(c) A SAME-INSTRUMENT RE-RUN IS STILL A DISTINCT SAMPLE. MEASURED on the 2B Bonsai: two runs of the SAME
    pre-image driver on the SAME binary emitted 0 and 64 tokens (PREREG instrument 3, §2b). "The same
    instrument" is not "the same record".
```

**SO THE GATE REFUSES ON ANY EXISTING RECORD**, and names which of the three identity values differ when any
do. `FINDING 020`'s own rule is the authority: *"a run must OWN its artifact path -- one run, one file -- and
launching a second run against a live path is not a retry, it is an OVERWRITE."*

**THE ESCAPE HATCH, AND IT CARRIES A REASON.** `--overwrite-artifact "<reason>"`. A bare `--force` is refused by
this tree's own standard — `run_card.py:315` — *"A gate with an override that is not written down is a gate
nobody can audit"* — and here the write is to the record itself, so the reason is written **into the record
that does the replacing** (`artifact_replaced`), together with what the replaced record said about itself before
it was destroyed: its sha256, its size, its mtime, and the identity values it carried. The destroyed record is
still gone; **what survives is the fact that it existed, what it claimed, and who said why.**

**SUBJECT S2 — A LOAD FAILURE SAYS WHICH CONDITION IT REPORTS.** `holder_sentence()` (RULING 82) is appended to
**every** load failure by both failure returns. MEASURED (card `t_33042da0`, and `FINDINGS/024` §3): a CPU-only
run of a file the binary cannot parse prints *"AND THE CARD IS HELD BY: pid 2418 (134 MiB) ... Tenants total 7146
MiB"*, while the cause is two lines further down the log the record does not quote:

```
E gguf_init_from_reader: tensor 'token_embd.weight' has invalid ggml type 142. should be in [0, 43)
```

**RULING 82 IS NOT WEAKENED AND ITS CARRIER IS NOT TOUCHED: `vram_holder.py` is not edited in this change.**
The sentence is kept, verbatim, in the case the ruling was ratified for. What changes is **where it is not
enough**: the driver now reads the server's OWN log at the failure and asks whether it names a cause of its own.
The class is decided by a READING of that log, the matched line is **quoted verbatim with its line number**, and
the record says which of the two conditions is being reported (`load_failure_class`), so a reader can overrule
the class from the carrier rather than trusting it:

```
the log names a READER's refusal of the FILE   -> the line is quoted; the holder sentence is NOT appended,
                                                  and the record says why it is not
the log names no such cause                     -> RULING 82's sentence, UNCHANGED, and the record says
                                                  the log named no cause of its own (its ratified case)
the log cannot be read at all                   -> said out loud, in the record; never reported as absent
```

**AND THE SIGNATURE LIST IS A SNAPSHOT OF ONE BUILD'S WORDING, WHICH IS WHY THE LINE TRAVELS WITH THE CLASS.**
Measured on this box, three independent file refusals, two of them in-tree logs:

```
gguf_init_from_reader: tensor 'output.weight' has invalid ggml type 142 ...   (27B Bonsai, 4B Bonsai)
gguf_init_from_reader: invalid magic characters: 'this', expected 'GGUF'      (a file that is not a gguf)
llama_model_load: error loading model: done_getting_tensors: wrong number of tensors; expected 428, got 426
```

---

## 2 THE PREDICTION, RECORDED BEFORE THE CODE CHANGE

**1. THE ORDINARY FIRST RUN IS UNCHANGED.** A run whose cell has no artifact on disk writes exactly what the
pre-image driver wrote on the same cell and instrument: same rc, and an artifact whose `config` and counters are
identical except for the keys this change adds.
*Falsifier: any pre-existing value differs on the paired arms.*

**2. A SECOND RUN ON A LIVE PATH IS REFUSED, AND THE REFUSAL CONSUMES NOTHING.** rc **4**; the existing record's
bytes, size and mtime unchanged; **no log file written; no server started**; wall time under 2 s.
*Falsifier: the artifact's sha256 changes, a new log appears, or a llama-server is spawned.*

**3. A RECORD THAT NAMES NO INSTRUMENT IS PROTECTED TOO.** A cell whose committed record predates instrument 3
(both Bonsai artifacts, every pre-`f1c0c5d` probe) refuses a run of that cell without the token.
*Falsifier: such a record is replaced by a run that was not told to replace it.*

**4. WHEN TWO INSTRUMENTS DISAGREE, THE REFUSAL NAMES BOTH.** The message carries the path, the recorded digest,
this run's digest, the legend and the reasoning arm on both sides, and which of them differ.
*Falsifier: a refusal whose text does not say what would be destroyed.*

**5. THE OVERRIDE IS A NAMED TOKEN AND ITS REASON TRAVELS.** `--overwrite-artifact "<reason>"` proceeds; the new
record carries `artifact_replaced` = {the replaced record's sha256, bytes, mtime, the identity it carried, the
reason verbatim, and a reading that says the replaced record is not recoverable from this file}. An empty reason
is refused (rc 2) and nothing is written.
*Falsifier: an override that replaces a record without the reason appearing in the replacement.*

**6. THE FAILURE LINE NAMES THE CONDITION, FROM THE LOG, WITH THE LINE QUOTED.** On the parse refusal the new
record carries `load_failure_class` = the file-refusal class, quotes the reader's line and its line number, and
does **not** carry the holder sentence; the pre-image driver's record for the same cell carries the holder
sentence and no class.
*Falsifier: a refusal record that still points at card tenancy for a file the binary cannot read; or a holder
sentence that has gone missing where the log names no cause.*

**7. NOTHING ELSE MOVES.** The repo's controls are rc-identical before and after (the same list the last card
ran); `sokoban_report.py` — the one reader that parses `why` — still runs and still buckets by it; no published
number moves; the file is in no pinned set.
*Falsifier: any control's rc changes; the report raises; a pinned digest moves.*

**8. FALSIFIERS, NAMED SO THE PREDICTION CAN FAIL:** the ordinary first run refused; a refusal that writes
anything at all; a refusal that misses a differing instrument; an override without a reason in the record; a
holder sentence lost in the case RULING 82 was ratified for; a class asserted with no line quoted; or the
`/health` branch drifting from the load-exit branch in wording or in class.

---

## 3 WHAT IS **NOT** IN THIS CHANGE, DISPOSED OF ONE BY ONE

*(A carrier is disposed of explicitly or not at all.)*

**(a) THE LOG NAME STILL CARRIES NO BINARY — AND NOW IT DOES NOT NEED TO.** `logs/SOKOBAN_<entrant>_<level>_
<legend>_rea-<arm>.log` is DECLARED SCRATCH (`DECISION_logs_are_scratch.md`; `LOG_EDGES.json` declares this
launch path's log coordinate an open, deliberate edge) and it already carries the legend and the reasoning arm.
**The collision at the log axis is closed by S1 at admission**: the run that would overwrite the log refuses
before it opens it. Adding the binary to a path that is not a record would move a convention to protect
something the gate already protects.

**(b) THE TWO FALSE INSTRUMENT NOTES ARE NOT EDITED.** `FINDINGS/024` §2 and the decision document; records are
not rewritten, and a correction beside a note is a decision taken on item 2 of the card, not an instrument
change.

**(c) THE CONFORMANCE PACKAGE'S CENSUS IS NOT AMENDED HERE.** Item 4 of the card; measured (this tip: the census
never names 10 names the record carries, three of them instrument 3's and seven of them older than this card)
and decided in the decision document, in its own commit.

**(d) THE `--entrant`/`--level` INTERFACE IS UNCHANGED**, and no new field carries a path: `artifact_replaced`
carries a REPO-RELATIVE path inside the record's own tree, so `make_conformance_package.py`'s LOCAL/FORMAT split
stays true — and its FORMAT list is not extended here, which is item 4's business, not this change's.

**IT IS NOT A CLAIM ABOUT THE MODELS. Nothing here says what any entrant can do, and no probe, population,
prereg, freeze record, grammar or declaration is edited.**

---

## 4 THE MEASUREMENT SCALE

No arm below changes a published number. The two refusals cost nothing (they run before `exec`); the three real
runs are on a small entrant and one level each. **Evidence lands at the declared results root,
`/home/chilly1/workspace/cabinet_results/t_8dc430a7/`, outside every git tree.**

---

# LANDED — 2026-10-16. THE PREDICTIONS ABOVE WERE WRITTEN FIRST AND ARE VERIFIED, NOT RESTATED.

**APPENDED, NOT REWRITTEN:** everything above is the pre-registration as it was committed, before the code
change. This note is added after it, and it is dated.

**THE DIGEST, BEFORE → AFTER:**

```
sokoban_run.py  43989 B  sha256 8fe19d2441227e8d964ff24911c9a19fcee38faee5ab907f6f231a53c048a410
             -> 58642 B  sha256 e3f20b3ba561376197ca0cea8dc64ac33a515f7015e99518002314ca02beed62
   commit c015995, ordered AFTER this file's commit c6cd542 and AFTER nothing else
   (a) S1 the artifact gate at admission, and its reason-carrying override
   (b) S2 the failure class, quoted from the server's own log, with vram_holder.py UNTOUCHED
NO PINNED SET MOVED, and none exists for this file: FROZEN_DIGESTS still names sokoban.py and the three
levels, byte for byte, and no cell of any population is re-scored. vram_holder.py is byte-identical to
its committed blob (it is not in the diff).
```

**EVERY PREDICTION HELD, WITH THE MEASUREMENT THAT SAYS SO** — `arms.py`, `arms2.py`, `final_checks.py`,
`classifier_control.py` and `controls.py` at the results root; each row below is a line one of them printed:

```
1  THE ORDINARY FIRST RUN IS UNCHANGED. Paired fresh-path arm, one cell (4B Bonsai, level 03), one
   instrument (prism b10777), one port, pre-image driver vs this change: keys only in the new record
   [], keys only in the pre record [], config values that MOVED {}, server_argv identical True. The
   ONLY difference anywhere is one turn's timing (secs 1.0 -> 0.9, same token R, same board, same
   gen_tokens 2) -- the class the last card's landing note also enumerated, and the reason it is
   named here rather than waved away.
2  A SECOND RUN ON A LIVE PATH IS REFUSED AND CONSUMES NOTHING. rc 4, wall 0.06-0.09 s, the record's
   sha256 UNTOUCHED, logs+0, and the process table identical across the refusal (7 llama-server
   processes before and after, none started) -- MEASURED, because "nothing has been written" is a
   sentence the gate prints and a sentence is not a measurement.
3  A RECORD THAT NAMES NO INSTRUMENT IS PROTECTED. The committed Bonsai 4B level-01 record (no
   server_binary_digest) -> rc 4, and the file is BYTE-IDENTICAL to `git show b36ea6a:` of it
   (93ed747458525cf62ce6e17748813fc3a012fc560b2c9939f396f52eb59b72c0). This is the arm the narrower,
   digest-only gate the card proposed WOULD NOT HAVE CAUGHT.
4  THE REFUSAL NAMES BOTH SIDES AND THE AXIS. Measured text: "it says about itself
   server_binary_digest='3c7090fb24b84615' ... this run would write server_binary_digest='0d5393431782ddf8'
   ... AND THESE DO NOT MATCH: server_binary_digest (record '3c7090fb24b84615' -> this run
   '0d5393431782ddf8')" -- and on the same-instrument arm it says so instead: "THE TWO ARE THE SAME
   INSTRUMENT AND THE SAME ARMS ... AND THE REPLACEMENT IS STILL REFUSED".
5  THE OVERRIDE IS A NAMED TOKEN AND ITS REASON TRAVELS. --overwrite-artifact "<reason>" -> rc 0 and the
   new record carries artifact_replaced whose sha256 EQUALS the record it replaced (8499ecd7ae5e6d78...,
   4438 B, mtime 2026-10-16T17:09:02Z -- the same three values the refusal arm had printed for that
   record), plus it_named {server_binary_digest 3c7090fb24b84615, legend_digest 0d86057c46d4c83b,
   reasoning off} and the reason verbatim. An EMPTY reason -> rc 2, nothing written.
6  THE FAILURE LINE NAMES THE CONDITION. One refused file (27B Bonsai, level 01, the default binary),
   two records: PRE-IMAGE `why` = "server exited rc=1." + "AND THE CARD IS HELD BY: pid 2418 (134 MiB)
   ... Tenants total 4754 MiB"; THIS CHANGE `why` = "server exited rc=1." + "THE BINARY REFUSED THE
   FILE -- log line 10, quoted verbatim: 0.00.103.582 E gguf_init_from_reader: tensor 'output.weight'
   has invalid ggml type 142. should be in [0, 43)" + the sentence saying the holder sentence is not
   reported here and why. The record also carries load_failure_class. The quoted line and its number
   are checkable against the log itself, and the CLASSIFIER CONTROL (`classifier_control.py`) runs both
   directions over SIX inputs and can fail: 3 real logs that name a reader's refusal -> no holder
   sentence; RULING 82's transcribed `failed to load`-only log, an empty log, and an unreadable log ->
   the holder sentence, verbatim, as ratified. 6/6 as predicted, exit 0. IT FAILED ON ITS FIRST RUN,
   on an expectation table I had written wrong -- which is the only reason to believe it can fail at all.
7  NOTHING ELSE MOVES. The repo's controls: 16/16 rc-IDENTICAL (controls_pre2.json vs controls_new.json).
   Three are byte-different with rc identical, and each was DIFFED rather than characterised: one solver
   TIMING (0.0071s -> 0.0075s, same moves/pushes/solution/expanded), and worktree-name strings inside
   two checks' own output. `sokoban_report.py` runs rc 0 and its output on the run of record
   (probes/SOKOBAN_RUN_20261010-072252.json) is BYTE-IDENTICAL before and after.
```

**AND THREE THINGS THIS MEASUREMENT GOT WRONG ON THE WAY, RECORDED RATHER THAN TIDIED:**

```
(i)  `arms.py` MEASURED THE ARTIFACT AT THE WRONG PATH. It handed its state reader the artifact NAME
     instead of `probes/<name>`, so every before/after was None == None and it printed UNCHANGED for
     arms that had just written a file. The rc of every arm, the log-directory deltas and the wall
     times survived; the artifact claims did NOT and were RE-MEASURED in arms2.py. A measurement that
     reports "unchanged" because it looked at nothing is the class this project keeps finding, caught
     this time in my own harness.
(ii) THE FIRST CONTROL COMPARISON WAS CONTAMINATED BY MY CHOICE OF PRE-IMAGE WORKTREE. It was on a
     DETACHED HEAD, and two of the sixteen controls (`check_field_semantics.py`, `verify_scope.py`)
     refuse to run without a branch because the branch is how a worktree is known to be a cabinet --
     so they returned rc 1 in the pre-image tree and rc 0 in the new one, for a reason that has nothing
     to do with this change. Re-run in a pre-image worktree ON A BRANCH: 16/16 rc-identical.
     `cabinet_root.cabinet()` is the enforcer, and it was right.
(iii) THE REPORT'S REASON BUCKET MOVES, AND THE REPORT WAS DELIBERATELY NOT CHANGED. `sokoban_report.py`
     buckets a non-loading cell by `why.split(" -- ")[0][:44]`; the new prose contains " -- " INSIDE the
     sentence (so the bucket label becomes "server exited rc=1.\nTHE BINARY REFUSED"), where before it
     was the first 44 characters of the holder sentence. The report still runs (rc 0, rc-identical on
     the run of record) and its numbers do not move -- it is a LABEL. **It is not fixed here because
     prediction 7 predicted this file stays as it is**, and a fix landed after its own prereg would be
     a change nobody predicted. It is filed as a follow-up: the record now carries
     `load_failure_class`, so the bucket should READ THE FIELD rather than split the prose.
```

**THE EVIDENCE, AT THE DECLARED RESULTS ROOT** (`/home/chilly1/workspace/cabinet_results/t_8dc430a7/`,
outside every git tree): `arm_*.json` and `arm2_*.json` (every arm's rc, stdout, artifact state before and
after, log delta, wall time), `pre_4B03.json`, `pre_4B03_p8792.json`, `new_4B03.json`,
`override_4B03.json`, `override2_4B03.json`, `s2_pair.json` (the two failure records side by side),
`classifier_control.py` + `classifier_raw.json` + `classifier_verdict.json`, `controls_pre2.json`,
`controls_new.json`, `controls_diff2.txt`, `controls_diff_detail2.txt`, `final_checks_out.txt`, the census
measurement (`measure_census.py`, `census_measure.txt`) and `git_committed_4B01_sha.txt`.

**AND THE TWO RECORDS THESE ARMS WROTE INTO THIS WORKTREE'S `probes/` ARE DELIBERATELY NOT COMMITTED** — the
27B level-01 failure record and the 4B level-03 record (the override's replacement). They are RECORDS OF RUNS
ON CELLS NO CRITERIA ARE FROZEN FOR: committing them would add entries to the domain every sweep reads, after
the sixteen controls above were measured against it. Their content is in the evidence (`s2_pair.json`,
`override2_4B03.json`), and the digest of the one the last card's acceptance run destroyed is in the chapter
above.

