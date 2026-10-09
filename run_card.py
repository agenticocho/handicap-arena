#!/usr/bin/env python3
"""
Run the standing card across every available text entrant.

DESIGN CONSTRAINTS, all from this project's own findings:

  * DECLARED CONFIG, IDENTICAL FOR EVERY ENTRANT. --ctx 8192 --max-tokens 3000 --trials 3.
    FINDING 001: a smaller --ctx silently caps how much a reasoning model may think, and a
    smaller --max-tokens truncates the trace. A card run at different configs per entrant
    measures the configs, not the models. The config is printed once and never varied.

  * NO --ngl. Omission = llama.cpp auto-fits to free VRAM. FINDINGS/002: passing an
    explicit --n-gpu-layers makes an over-large placement ABORT rather than fall back, and
    a forced footprint that exceeds free VRAM turns a graceful partial offload into a
    crash. On this box the GPU has ~1.6 GB free, so most entrants will run partially
    offloaded and the weigh-in will say so.

  * PATHS, NEVER ALIASES. Two aliases in the local llama-swap config point at GGUFs that
    were deleted; the first version of this arena scored 40% of a field that did not exist.

  * RESUMABLE. A bundle that already exists is skipped, so a long run can be restarted
    without redoing work or overwriting evidence.

  * SMALLEST FIRST. In the order of file size, so results land progressively rather than
    after the slowest model finishes.

  * SCRATCH, NEVER ABORT. A model that cannot serve is recorded as scratched and the run
    continues. One bad entrant must not cost the field.
"""
import glob, json, os, shutil, subprocess, sys, time

# PORTABLE. Derived from this file, overridable by environment. The README says "download it,
# point it at your GGUFs" -- with absolute paths baked in, it could only be downloaded by one
# machine, which is the opposite of the point.
ARENA = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(ARENA, "results")
MODELS = os.environ.get("ARENA_MODELS") or os.path.expanduser("~/moltbook_pipeline/models")
# THE RESOLVER IS arena.py's, AND THERE IS ONLY ONE OF IT.
#
# This used to be:
#     SERVER = (os.environ.get("LLAMA_SERVER") or shutil.which("llama-server") or "llama-server")
#
# The bare string was the bug, and it cost 26 of 46 entrants. systemd's user-manager PATH does not
# include /home/chilly1/llama.cpp/build/bin, so `which` returned None -- and the fallback to the
# literal "llama-server" is TRUTHY. arena.py:225 is `self.binary = binary or find_llama_server()`,
# so a truthy binary means the resolver is NEVER CALLED -- and its list at arena.py:143 contains the
# correct absolute path. The guard at arena.py:275 ("llama-server not found") could never fire,
# because the failure path was being pre-empted by a name.
#
# Every server spawned after that line took effect wrote ZERO BYTES. 26 empty bundles, 26 zero-byte
# logs, GPU at 759 of 8192 MiB, and rc=0 reported for all of them -- a statement about the model
# ("produced nothing") where the truth was a statement about the machine ("the server never existed").
#
# arena.py is importable (it has a __main__ guard), so the fix is not a second resolver -- it is
# calling the one that already exists, and REFUSING when it fails.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arena as _arena                                                    # noqa: E402
# THE GATE'S OWN REVISION, TAKEN FROM THE GATE. Not recomputed here -- a second digest computation would
# be a fifth one-definition failure, and the point of the revision is that it names the instrument.
import test_game_states as _gate                                         # noqa: E402

SERVER = _arena.find_llama_server(os.environ.get("LLAMA_SERVER") or None)
if not SERVER:
    sys.exit("llama-server not found: set LLAMA_SERVER, put it on PATH, or install it under "
             "llama.cpp/build/bin. REFUSING TO START -- a bare name here is truthy, and a truthy "
             "name silently disables arena.py's own resolver. See "
             "governance/rulings/2026-10-07-resolver-fell-back-to-a-bare-name.md")

CTX, MT, TRIALS = 8192, 3000, 3

# WHICH CARD. v1 = the retired 3-round card. v2 = the 6-item battery. v3 = R1 rebalanced,
# 6 items, strict scorer. A bundle carries card_version and a _cardN_ filename marker, because
# scores from different cards are different measurements and must never be ranked together.
#
# THIS USED TO BE:
#     CARD = "v2" if ("--card" in sys.argv and "v2" in sys.argv) else "v1"
# which recognises only v2 -- so `--card v3` silently ran **v1**, writing v1 bundles while the
# operator believed it was measuring v3. A wrong-card run that reports success is the most
# dangerous outcome this script can produce: the numbers look fine and measure something else.
# An unrecognised card now ABORTS.
KNOWN_CARDS = _arena.KNOWN_CARDS          # ONE DEFINITION, AND IT LIVES IN arena.py. This was written
                                          # twice; adding v6 to one copy produced a run in which EVERY
                                          # entrant returned rc=2 in 0.0 s and the gate refused a verdict.
CARD = "v1"
if "--card" in sys.argv:
    _i = sys.argv.index("--card")
    if _i + 1 >= len(sys.argv):
        sys.exit(f"--card needs a value: one of {sorted(KNOWN_CARDS)}")
    CARD = sys.argv[_i + 1]
if CARD not in KNOWN_CARDS:
    sys.exit(f"unknown card {CARD!r}; known: {sorted(KNOWN_CARDS)}")
CARD_N = KNOWN_CARDS[CARD]
CARD_TAG = "" if CARD == "v1" else f"_card{CARD}_"

# Excluded because the standing card is TEXT: diffusion, audio, and bare projectors.
EXCLUDE_PAT = ("qwen-image", "audio", "mmproj", "clip", "vae", "embed", "whisper")

os.makedirs(RESULTS, exist_ok=True)


def entrants():
    out = []
    for p in glob.glob(os.path.join(MODELS, "*.gguf")):
        b = os.path.basename(p)
        if any(k in b.lower() for k in EXCLUDE_PAT):
            continue
        out.append((os.path.getsize(p), p, b))
    out.sort()                      # smallest first
    return out


def bundle_has_measurement(path):
    """True only if the bundle at `path` CARRIES A MEASUREMENT.

    A FILE IS NOT A MEASUREMENT. An empty bundle (results: []) is a MISSING VALUE, not a score of zero --
    the rule named in CARD_v4.md before the verdict was attempted. A file that holds no measurement must
    not skip a re-measurement, and a skip whose message says "measured" when it means "a file exists" is
    the same stand-in this repo has found in a filename, a label, and a caption.
    """
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return False
    return d.get("harness") == "handicap-arena" and bool(d.get("results") or [])


def already_measured(path):
    """Has this exact GGUF already been measured at this config, in ANY bundle?

    Keyed on CONTENT, not filename. The first version keyed on the derived output name, which
    only recognised bundles this script had itself created -- so it missed the hand-named
    bundles (Qwen3.5-2B_neutral_ctx8192_mt3000.json) and re-ran a model whose measurement
    already existed. A skip that only recognises your own filenames is not a skip.
    """
    base = os.path.basename(path)
    for bp in glob.glob(os.path.join(RESULTS, "*.json")):
        try:
            d = json.load(open(bp))
        except Exception:                                        # noqa: BLE001
            continue
        for r in (d.get("results") or []):
            if os.path.basename(r.get("gguf") or "") != base:
                continue
            c = r.get("config") or {}
            if (c.get("ctx") == CTX and c.get("max_tokens") == MT
                    and c.get("n_gpu_layers") is None
                    and r.get("card_version", 1) == CARD_N):
                return os.path.basename(bp)
    return None


def bundle_path(stem):
    # Placement is IN THE NAME because it changes the latency conclusion (FINDINGS/004), and
    # this repo's rule is: if it changes what the reader concludes, it belongs in the name.
    # The card version is in the name for the same reason -- a v1 score and a v2 score are
    # different measurements.
    tag = "" if CARD == "v1" else f"_card{CARD}"
    return os.path.join(RESULTS, f"{stem}{tag}_autofit_neutral_ctx{CTX}_mt{MT}.json")


def gate_ratios(planned, attempted, measured):
    """CARD_v5.md's gate, as a PURE FUNCTION -- so the runner and its test share ONE definition.

    Kept separate from the printing block because a criterion stated in a card, implemented in a
    runner, and asserted in a test are THREE components, and two components confirming each other is
    not evidence when they share no rule. This is the rule; everything else calls it.

    === THE SECOND CONDITION, RULED IN ===

    `measured > 0` is now PART OF THE GATE EXPRESSION rather than a block printed after the verdict.

    A coverage ratio cannot distinguish "ran completely" from "never started" -- TOTAL FAILURE IS ITS
    PASSING CASE. A better coverage (counting STARTED rather than ATTEMPTED) is better and still not
    sufficient. THE GUARD IS THE PAIR, NOT THE RATIO: `coverage >= 0.95 AND measured > 0`.

    It used to be a separate `if _measured == 0:` block AFTER the gate verdict had already been printed,
    which meant A READER COULD QUOTE "COVERAGE 1.000" BESIDE A RUN THAT PRODUCED NOTHING. A condition
    that fires after the verdict is not part of the verdict.

    BOTH SIDES ARE CONTROL-TESTED: a run that measured nothing must fail the gate even with coverage
    1.000, AND a run that measured something must NOT be failed by this condition.
    """
    coverage = (attempted / planned) if planned else 0.0
    yield_   = (measured / attempted) if attempted else 0.0
    measured_ok = measured > 0
    return {"coverage": coverage, "yield": yield_, "measured": measured,
            "coverage_ok": coverage >= 0.95, "yield_ok": yield_ >= 0.85,
            "measured_ok": measured_ok,
            "gate_met": coverage >= 0.95 and yield_ >= 0.85 and measured_ok}


def permanently_failed(base):
    """-> the record files IF EVERY recorded attempt for this entrant was EMPTY, else None.

    A RECORDED RESULT, NOT A QUEUE. CARD_v5.md: these entrants have failed THREE TIMES EACH --
    original run, re-run, re-attempt. A fourth attempt would spend the night re-confirming a number
    we already have.

    AND THE RECORD IS NOT ONE FILENAME. A failed bundle is MOVED ASIDE BY NAME before a re-attempt
    (`.attemptN.empty.json`, `_EMPTY_*.json`), so THE CANONICAL PATH IS EMPTY for exactly the entrants
    that must not be re-run. Measured both ways:

        by canonical path only    ->  7 excluded, 1 "no bundle at all", planned 39
        by record, all name forms ->  8 excluded, 0 unrecorded,      planned 38

    The missing one is `Kev-4B-Q4_K_M` (3.03 GB). A PATH TEST IS NOT A RECORD TEST.
    """
    stem = base.replace(".gguf", "")
    forms = set()
    for pat in (f"{stem}_card*.json", f"{stem}*_EMPTY_*.json", f"{stem}*attempt*.json"):
        forms.update(glob.glob(os.path.join(RESULTS, pat)))
    forms = sorted(forms)
    # NO RECORD IS NOT A PERMANENT FAILURE -- an entrant never attempted must still be attempted.
    if not forms:
        return None
    for f in forms:
        try:
            with open(f, encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception:                                        # noqa: BLE001
            continue
        if d.get("harness") != "handicap-arena":
            continue
        # ANY attempt that measured means this entrant is not permanently failed.
        if d.get("results"):
            return None
    return forms


def game_contract_gate():
    """-> (ok, detail). READ THE DECISION, DO NOT RUN THE PROGRAM.

    A SUBPROCESS, not an import: it reads the exit status cleanly and avoids coupling to the
    test_game_states <-> annotate_superseded import pair (the checker imports stem_of at module level; the
    generator imports the checker inside a function). A gate that shares a module with the thing it gates
    inherits its failure modes.

    ** AND THIS FUNCTION EXISTS SO THE GATE CAN BE TESTED WITHOUT RUNNING WHAT IT PERMITS. **
    The first version of the control ran `run_card.py` whole to see the gate pass -- and passing the gate
    STARTS THE WORK, so the control spawned servers, reached entrants, and wrote `results/` artifacts,
    which then went into the commit whose own message claimed "0 control artifacts left behind."

      A CONTROL FOR A GATE MUST NOT WRITE TO THE RECORD IT CONTROLS.
      TESTING A REFUSAL IS FREE -- the refusal IS the short circuit.
      TESTING A PERMISSION IS NOT FREE, BECAUSE THE PERMISSION'S ONLY OBSERVABLE EFFECT IS THE PERMITTED
      WORK. Nobody prices in the cost of the thing being permitted.

    Returning the decision makes both directions free, and the caller is the only thing that proceeds.
    """
    gate = subprocess.run(
        [sys.executable, os.path.join(ARENA, "test_game_states.py")],
        capture_output=True, text=True,
    )
    tail = "\n".join((gate.stdout or "").strip().splitlines()[-14:])
    return gate.returncode == 0, tail


def main():
    ents = entrants()
    print(f"entrants: {len(ents)}   config: ctx={CTX} mt={MT} trials={TRIALS} ngl=auto-fit")
    print("=" * 96, flush=True)
    # REFUSE TO START IF results/ HOLDS A LOG. results/ holds result bundles and nothing else; a .log
    # among them is the file a reader counts as an entrant (the Chair's objection about the empty
    # bundle). The fix is a CHECK, not a migration -- a migration stops holding the moment someone
    # adds the next log by hand, and then there are two eras and a reader has to know which.
    _stray = glob.glob(os.path.join(RESULTS, "*.log"))
    if _stray:
        sys.exit(f"refusing to start: {len(_stray)} log file(s) in results/, which holds result "
                 f"bundles and nothing else:\n  " + "\n  ".join(os.path.basename(p) for p in _stray)
                 + "\nMove them to logs/ and re-run.")

    log = os.path.join(ARENA, "logs", "card_run.log")
    with open(log, "a") as lf:
        lf.write(f"\n=== card run started {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} "
                 f"ctx={CTX} mt={MT} trials={TRIALS} ===\n")

    # ---- THE GAME-CONTRACT GATE, AT ADMISSION -- BEFORE ANY MODEL IS SPAWNED ---------------
    #
    # At admission rather than during the run: the same shape as the weigh-in and as C4's partition. The
    # field is checked before it starts, not while it is halfway through writing evidence.
    #
    # HARD REFUSE. A warning is not a gate -- that is the whole reason this gate exists.
    #
    # THE ESCAPE HATCH, and this sentence is why a hard refuse is safe:
    #   IF A FUTURE CASE IS LEGITIMATE, AMEND GAME_CONTRACT.md -- a deliberate, recorded act -- AND NEVER
    #   IGNORE THIS EXIT CODE. A gate with an override that is not written down is a gate nobody can audit.
    # The person who hits this at 2am is the person who needs to read it, so it lives here, next to the
    # call, not in a document they will not open.
    gate_ok, gate_detail = game_contract_gate()
    if not gate_ok:
        print("REFUSED: the game contract is violated by a NEW round or task file.")
        print("  test_game_states.py exited non-zero -- no model was spawned.")
        print()
        print(gate_detail)
        print()
        print("  THE REMEDY IS NOT TO IGNORE THIS. Amend GAME_CONTRACT.md -- a deliberate, recorded act --")
        print("  or fix the task file / round that caused it. The historical violations are annotated and")
        print("  do NOT trip this gate; only a NEW one does.")
        return 1
    # AND THE RUN RECORDS THE GATE REVISION THAT ADMITTED IT. A digest of GAME_CONTRACT.md travels into
    # the run's own log, so a run and the gate that admitted it are linked by more than a timestamp --
    # v5 taught us that a card and its criteria linked only by file timestamps is not a link, and that
    # lesson was paid for once already.
    print(f"game contract: OK ({gate_detail.strip().splitlines()[-3] if gate_detail else 'clean'})")
    print(f"GATE REVISION  {_gate.GATE_REVISION}   (sha256 of GAME_CONTRACT.md, first 16)")

    done = scratched = skipped = excluded = 0
    # AN ENTRANT THAT RETURNED IN ~ZERO SECONDS WITH A NONZERO CODE WAS NEVER STARTED.
    #
    # This counter exists because COVERAGE CANNOT TELL "ATTEMPTED" FROM "STARTED", and its PASSING
    # CONDITION IS TOTAL FAILURE. Measured: `--card v6` was rejected by arena.py's argparse (the registry
    # was defined twice), so every entrant returned rc=2 in 0.0 s -- and the gate reported
    #     COVERAGE attempted/planned  1.000  OK
    #     YIELD    measured/attempted 0.000  UNMET
    # A run that never started scored FULL MARKS on the completeness metric, because `attempted` was
    # COMPUTED as len(ents) - excluded rather than COUNTED. Same defect as the empty bundle: a quantity
    # named for what happened, whose value comes from what was planned.
    never_started = 0
    t_start = time.time()
    for i, (size, path, base) in enumerate(ents, 1):
        stem = base.replace(".gguf", "")
        outp = bundle_path(stem)
        # A RECORDED RESULT IS NOT A QUEUE. CARD_v5.md: do NOT re-run an entrant whose every recorded
        # attempt was empty. Three failures each is a finding, not a backlog.
        _perm = permanently_failed(base)
        if _perm:
            print(f"[{i:2d}/{len(ents)}] EXCLUDED (permanent failure: {len(_perm)} record(s), empty in "
                  f"every attempt -- a RECORDED RESULT, NOT A QUEUE)")
            excluded += 1
            continue
        prior = already_measured(path)
        # A FILE IS NOT A MEASUREMENT. This test used to be `os.path.exists(outp) or prior` -- so a
        # bundle that came back EMPTY (results: []) short-circuited the run exactly as though it had
        # been measured, AND THE SKIP MESSAGE SAID "already measured" WHILE MEANING "a file is there".
        # That is the rule this repo has applied everywhere else, unimplemented one level up in the
        # runner: bundle=True must mean "contains a measurement".
        #
        # The empty is NOT discarded -- it is evidence, and it is moved aside by name before the
        # re-attempt, so the failure survives and the re-measurement is not an overwrite of history.
        carries = bundle_has_measurement(outp)
        if carries or prior:
            src = prior or os.path.basename(outp)
            print(f"[{i:2d}/{len(ents)}] SKIP (MEASURED -- {src})")
            skipped += 1
            continue
        if os.path.exists(outp):
            n = 1
            while os.path.exists(f"{outp}.attempt{n}.empty.json"):
                n += 1
            os.rename(outp, f"{outp}.attempt{n}.empty.json")
            print(f"[{i:2d}/{len(ents)}] RE-ATTEMPT (prior bundle held no measurement; "
                  f"preserved as {os.path.basename(outp)}.attempt{n}.empty.json)")

        print(f"[{i:2d}/{len(ents)}] {size/2**30:5.2f} GB  {stem}", flush=True)
        t0 = time.time()
        cmd = [sys.executable, "-u", os.path.join(ARENA, "arena.py"),
               "--model", path, "--ctx", str(CTX), "--max-tokens", str(MT),
               "--trials", str(TRIALS), "--card", CARD, "--out", outp,
               "--llama-server", SERVER]
        try:
            r = subprocess.run(cmd, cwd=ARENA, capture_output=True, text=True, timeout=5400)
            dt = time.time() - t0
            well = [l for l in (r.stdout or "").splitlines()
                    if any(k in l for k in ("DIVISION", "AGG", "belt", "BELT", "SCRATCHED",
                                            "MEASURED", "PARTIAL", "wrote", "bundle"))]
            for l in well[-6:]:
                print("      " + l.strip())

            # A bundle can EXIST and be EMPTY: the harness writes one even when the entrant is
            # scratched at weigh-in. rc=0 with an empty results list is not a score.
            #
            # bundle=True used to test that a FILE EXISTS, which cannot detect the failure it
            # most needs to catch -- a run that measured nothing reports success. The Chair
            # found one: laya_english_f16, results: [], logged as `rc=0 2s bundle=True`. A
            # 2-second "success" is the most dangerous row on a board: it looks like a result.
            #
            # So: a bundle only counts if it CONTAINS a measurement -- non-empty results, with a
            # config and a sha256. This is the repo's own README contract, enforced rather than
            # asserted.
            scored_ok, why_empty = False, ""
            if r.returncode == 0 and os.path.exists(outp):
                try:
                    d = json.load(open(outp))
                    res = d.get("results") or []
                    r0 = res[0] if res else {}
                    if not res:
                        why_empty = "results list is EMPTY (measured nothing)"
                    elif not (r0.get("config") and r0.get("sha256")):
                        why_empty = "entry lacks config and/or sha256 — violates results/README"
                    else:
                        scored_ok = True
                except Exception as e:                            # noqa: BLE001
                    why_empty = f"unreadable: {type(e).__name__}"
            if scored_ok:
                done += 1
                print(f"      -> scored in {dt/60:.1f} min", flush=True)
            else:
                scratched += 1
                if r.returncode != 0 and dt < 5.0:
                    never_started += 1
                    print(f"      -> NEVER STARTED: rc={r.returncode} in {dt:.1f}s "
                          f"(not an attempt -- the runner never reached the model)", flush=True)
                # THE REASON MUST TRAVEL WITH THE ARTIFACT, NOT JUST THE LOG.
                #
                # `why_empty` was computed here and written to stdout and to the log -- both of which
                # are NOT the bundle. The only mark that reached the file was the filename rewrite
                # below, so `X_cardv4_autofit_EMPTY_ctx8192_mt3000.json` was A LABEL WITH NOTHING
                # BEHIND IT: a reader could see the entrant failed and not why, and a consumer counting
                # files read it as a completed entrant. Four of the first 33 v4 bundles shipped that
                # way, and the same four shipped that way in v3 -- so it is systematic, not a hiccup.
                #
                # This is FINDING 007's rule one level ABOVE the item: no verdict may depend on data
                # discarded at scoring time, and a log is discarded relative to the artifact.
                #
                # A bundle that never reaches scoring has no scoring path to write a failure class, so
                # the class is written by the path that DID run -- the runner -- and C3 of CARD_v4.md
                # is widened to cover pre-scoring failures.
                failure = {"class": "empty" if "EMPTY" in why_empty.upper()
                           else ("rc" if r.returncode != 0 else "unreadable-or-unscored"),
                           "reason": why_empty or f"rc={r.returncode}",
                           "rc": r.returncode,
                           "secs": round(dt, 1),
                           "written_by": "run_card.py (pre-scoring failure: the run produced no bundle "
                                         "with a measurement, so no scoring path existed to record it)"}
                if os.path.exists(outp):
                    try:
                        _d = json.load(open(outp))
                        _d["failure"] = failure
                        with open(outp, "w") as _f:
                            json.dump(_d, _f, indent=1)
                    except Exception:                             # noqa: BLE001
                        # last resort: write a standalone record beside the bundle rather than lose
                        # the reason. A reason in the wrong place beats no reason at all.
                        try:
                            with open(outp + ".failure.json", "w") as _f:
                                json.dump(failure, _f, indent=1)
                        except Exception:                         # noqa: BLE001
                            pass
                # mark the artifact itself, so an `ls` cannot present it as an entrant
                try:
                    if os.path.exists(outp):
                        stem = os.path.basename(outp).replace(".json", "")
                        marked = os.path.join(RESULTS,
                                              stem.replace("_neutral_", "_EMPTY_")
                                              .replace("_GRAMMAR_", "_EMPTY_") + ".json")
                        if marked != outp and not os.path.exists(marked):
                            os.rename(outp, marked)
                            print(f"      -> marked {os.path.basename(marked)}")
                except Exception:                                 # noqa: BLE001
                    pass
                print(f"      -> NOT SCORED {why_empty or 'rc=' + str(r.returncode)} "
                      f"({dt/60:.1f} min)", flush=True)
            with open(log, "a") as lf:
                lf.write(f"{stem}\trc={r.returncode}\tscored={scored_ok}\t{dt:.0f}s\t"
                         f"{why_empty}\n")
        except subprocess.TimeoutExpired:
            scratched += 1
            print(f"      -> TIMEOUT after 90 min, moving on", flush=True)
            with open(log, "a") as lf:
                lf.write(f"{stem}\tTIMEOUT\n")

    print("=" * 96)
    print(f"scored {done}   scratched/not-scored {scratched}   skipped {skipped}   "
          f"excluded {excluded}   total {(time.time()-t_start)/60:.1f} min")

    # THE GATE READS FRACTIONS, SO THE RUN PRINTS THEM. CARD_v5.md names four denominators; a runner
    # that prints only a count leaves the reader to supply the denominator, which is how v4 produced
    # four numbers where the documents said one.
    #
    # COVERAGE DIVIDES BY *PLANNED*, NOT BY ADMITTED -- and this was caught by dry-running before the
    # run. CARD_v5.md froze `attempted / planned`. The first version of this block divided by the
    # admitted set (46), so a COMPLETE, CORRECT run of the planned population (38) scored 0.826 and
    # FAILED ITS OWN GATE. That is v4's defect exactly: a gate whose satisfiability depends on a number
    # the population decided. A criterion and its implementation are two components; where they disagree,
    # the CODE is believed and the frozen card is not.
    _planned   = len(ents) - excluded
    # ATTEMPTED IS COUNTED, NOT COMPUTED. It used to read len(ents) - excluded, which asserts that every
    # planned entrant was tried -- so a runner that never reached a single model still reported that it
    # had attempted all of them. Subtract the ones the runner demonstrably never started.
    _attempted = len(ents) - excluded - never_started
    # A SKIP (MEASURED) IS A MEASUREMENT -- the skip message says so in its own words.
    #
    # `_measured = done` ALONE MADE A RESUMED RUN UNABLE TO PASS ITS OWN YIELD GATE. `done` counts only
    # entrants measured IN THIS INVOCATION; an entrant skipped because it was already measured ticks
    # `skipped`. So a resume that re-measured nothing scored yield 0.000 while the field was complete --
    # and this invocation, resuming 19 of 38, had a ceiling of 19/38 = 0.50 against a 0.85 floor, and
    # printed 0.474. THE GATE WAS UNSATISFIABLE BY CONSTRUCTION, not by any property of the field.
    #
    # AND NOBODY TOUCHED THE GATE TO BREAK IT. Making the runner resumable was a correct fix for a real
    # problem, and that fix changed the gate's inputs. A criterion is only as sound as its numerator's
    # definition of the thing it counts -- and this one counted a different thing than it named.
    #
    # The tell was on screen: `skipped 19` and `measured 18` printed on adjacent lines, both correct,
    # contradicting each other, visible only if you add them.
    _measured  = done + skipped
    _g = gate_ratios(_planned, _attempted, _measured)
    print(f"DENOMINATORS  applicants {len(ents)}   planned {_planned}   attempted {_attempted}   "
          f"excluded {excluded}   measured {_measured}  (this invocation {done} + already-measured {skipped})")
    print(f"GATE  COVERAGE attempted/planned    {_g['coverage']:.3f}  (>= 0.95)   "
          f"{'OK' if _g['coverage_ok'] else 'UNMET'}")
    print(f"      YIELD    measured/attempted  {_g['yield']:.3f}  (>= 0.85)   "
          f"{'OK' if _g['yield_ok'] else 'UNMET'}")
    # THE SECOND CONDITION PRINTS BESIDE THE RATIOS, because THE GUARD IS THE PAIR, NOT THE RATIO. A
    # coverage of 1.000 with nothing measured is the shape of total failure passing its own test, and the
    # reader must see the conjunction rather than two ratios that look satisfied.
    print(f"      MEASURED > 0                {_g['measured']:d}                "
          f"{'OK' if _g['measured_ok'] else 'UNMET'}")
    print(f"      GATE (coverage AND yield AND measured>0) "
          f"{'MET -- outcome 2 or 3 may be called' if _g['gate_met'] else 'UNMET -- outcome 1: NO VERDICT'}")
    # AND A RUN THAT MEASURED NOTHING IS AN ERROR, NOT A VERDICT -- the second half of the coverage fix.
    # Coverage cannot distinguish "ran completely" from "never started", and its passing condition is
    # total failure; yield catches that for THIS run, but a gate verdict printed at all lets a reader
    # quote "COVERAGE 1.000" beside a run that produced nothing. An empty field is not a measurement of
    # an empty field; it is a broken runner, and it must say so and exit non-zero.
    if _measured == 0:
        print()
        print("=" * 96)
        print("ERROR -- NO MEASUREMENT WAS PRODUCED. This is not a verdict about the population.")
        print(f"  planned {_planned}   attempted {_attempted}   never started {never_started}   measured 0")
        if never_started:
            print(f"  {never_started} entrant(s) returned a NONZERO code in under 5 s, so the runner never")
            print("  reached a model. That is a broken invocation, not a field of failures.")
        print("  A run whose measured count is zero reports an ERROR rather than a verdict, because")
        print("  COVERAGE CANNOT TELL 'ATTEMPTED' FROM 'STARTED' AND TOTAL FAILURE IS ITS PASSING CASE.")
        print("=" * 96)
        return 3
    print(f"log: {log}")
    ls = sorted(glob.glob(os.path.join(RESULTS, "*_neutral_ctx*_mt*.json")))
    print(f"bundles now on disk: {len(ls)}")


if __name__ == "__main__":
    # THE REFUSE MUST BE HARD, AND THIS IS WHAT MAKES IT HARD. This called `main()` and discarded its
    # return, so a REFUSED gate still exited 0 -- a warning wearing an exit code. **A WARNING IS NOT A
    # GATE**, which is the whole reason the gate exists.
    #
    # Caught by the control, and caught in the right way: the planted violation produced the correct
    # MESSAGE and the wrong STATUS. Reading the output would have called this fixed; reading the EXIT CODE
    # showed it was not. That is the difference between a log line and a gate.
    raise SystemExit(main())
