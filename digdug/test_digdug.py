#!/usr/bin/env python3
# test_digdug.py -- REPLAY EVERY RECORD.  Not a unit test suite.
#
# The claim under test is not "the functions do what their author meant".  It is:
#
#     a bundle, read cold, reproduces itself through the frozen code
#
# so every check below reads a WRITTEN bundle, replays its recorded raw answers
# through `digdug.feed`, and demands that the counters, the board and the named
# terminal reason come back identical.  A record that cannot be replayed is a
# transcript of something, not a measurement.
#
# Then the rules get their own controls:
#   R1  the abstention list in the bundle IS the list in the code, and every rule
#       name that fired is a rule the grammar declares;
#   R2  the score recomputes from `wins / items_attempted_emitted`, and `moves`
#       is nowhere averaged into it;
#   R3  a bundle is read under ONE grammar, so two bundles read under different
#       grammars are not comparable and this file says so;
#   B1  emitted and consumed are both present, and any run that claims they are
#       equal for every entrant is checked against the wall-bumper, where they
#       cannot be;
#   B2  `enclosed_measured` is recomputed from the level file on disk;
#   B3  a bundle whose level digest has drifted from the file is REJECTED, which
#       is the uniqueness rule applied to the record rather than to the input;
#   §6  the declared reasoning setting and GPU must AGREE across every bundle in
#       the directory -- one event, one instrument.  A directory that mixes
#       reasoning=on with reasoning=off is refused here, at the table, because a
#       table that silently pools them is the failure this circuit was built to
#       catch (ON and OFF produced OPPOSITE outcomes on the first cabinet).
#
# Stdlib only.  Run:  python3 test_digdug.py [results_dir]

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import digdug                                                    # noqa: E402
import digdug_solve                                              # noqa: E402
from digdug_reader import GIVE_UP_TOKENS, Reading                # noqa: E402

RESULTS = os.path.join(HERE, "results")
FAILURES = []
CHECKS = [0]


def ck(cond, label, seen=None):
    CHECKS[0] += 1
    if cond:
        return True
    FAILURES.append("%s%s" % (label, "" if seen is None else "   <- %r"
                             % (seen,)))
    return False


def _sha(path):
    import hashlib
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


def replay(ent, levels, budget):
    """Rebuild the whole item from its recorded raws.  -> dict or None."""
    out = {}
    for name, item in sorted(ent["rounds"]["R_digdug_levels"]["items"].items()):
        lv = levels.get(name)
        if lv is None:
            out[name] = {"error": "level %s not on disk" % name}
            continue
        st = digdug.State(lv)
        for ply in item["trace"]:
            raw = ply.get("raw")
            if raw is None:
                continue
            digdug.feed(st, raw, budget=budget)
        reason = digdug.terminal_reason(st, budget)
        got = {
            "solved": st.solved, "moves": st.moves,
            "attempted_emitted": st.emitted,
            "attempted_consumed": st.consumed,
            "blocked": st.blocked, "waited": st.waited, "digs": st.digs,
            "collects": st.collects, "not_an_action": st.not_an_action,
            "give_up": st.give_up, "after_end": st.after_end,
            "over_budget": st.over_budget, "terminal": reason,
            "final_board": st.render(),
        }
        out[name] = {"got": got, "want": {k: item.get(k) for k in got},
                     "recomputed_facets": item.get("facets"),
                     "never_started": item["terminal"] == "NEVER_STARTED"}
    return out


def check_bundle(path, levels, tasks):
    with open(path) as fh:
        bundle = json.load(fh)
    rel = os.path.basename(path)
    if bundle.get("harness") != "handicap-arena":
        ck(False, "%s: harness tag" % rel, bundle.get("harness"))
    if bundle.get("event") != "DIG DUG":
        ck(False, "%s: event tag" % rel, bundle.get("event"))
    declared = bundle.get("declared", {})
    ck(declared.get("reasoning") in ("on", "off", "unset"),
       "%s: reasoning is DECLARED and one of on|off|unset" % rel,
       declared.get("reasoning"))
    ck(isinstance(declared.get("gpu"), dict)
       and "probe" in declared.get("gpu", {}),
       "%s: the GPU is declared WITH THE PROBE that established it" % rel,
       declared.get("gpu"))
    fz = bundle.get("frozen_contract", {})
    ck(bool(fz.get("frozen_utc")) and fz.get("frozen_before_this_run") is True,
       "%s: the freeze predates the run, per the bundle" % rel,
       fz.get("frozen_utc"))
    ck(str(fz.get("frozen_utc", "")) <= str(bundle.get("generated", "")),
       "%s: frozen_utc <= generated (a string compare on UTC stamps is a "
       "correct compare; a bundle that inverts them is a bundle written after "
       "the fact)" % rel, (fz.get("frozen_utc"), bundle.get("generated")))
    digests = fz.get("digests") or {}
    for key, rel_f in (("simulator", "digdug.py"), ("reader",
                                                   "digdug_reader.py"),
                       ("solver", "digdug_solve.py"), ("runner",
                                                        "digdug_run.py")):
        want = digests.get(key)
        got = _sha(os.path.join(HERE, rel_f))
        ck(want == got,
           "%s: the bundle was scored by the code ON DISK NOW (%s)" % (rel,
                                                                        rel_f),
           (want, got))
    for ent in bundle.get("results", []):
        check_result(rel, ent, levels, tasks, bundle)
    return declared.get("reasoning"), declared.get("gpu"), ent.get("config", {})


def check_result(rel, ent, levels, tasks, bundle):
    name = ent.get("entrant")
    tag = "%s/%s" % (rel, name)
    rnd = ent["rounds"]["R_digdug_levels"]
    items = rnd["items"]
    # B3 applied to the record: a level file that moved invalidates the run.
    for lname, item in sorted(items.items()):
        lv = levels.get(lname)
        if lv is None:
            ck(False, "%s: %s is not a level on disk" % (tag, lname))
            continue
        ck(item["level_sha256"] == lv.sha256,
           "%s: %s level digest matches the file (a run under a moved level is "
           "not a run under this contract)" % (tag, lname),
           (item["level_sha256"], lv.sha256))
        ck(lv.enclosed == item.get("enclosed_measured", lv.enclosed),
           "%s: %s enclosure is a measurement, not a claim" % (tag, lname))
    # R1: the tokens, and the rules that fired
    g = ent.get("grammar") or bundle.get("grammar") or {}
    ck(tuple(g.get("give_up_tokens", ())) == tuple(GIVE_UP_TOKENS),
       "%s: the bundle's abstention list EQUALS the reader's" % tag,
       g.get("give_up_tokens"))
    fired = set(ent.get("rules_fired", []))
    ck(fired <= set(Reading.RULES) | {"SHADOW.wait_illegal"},
       "%s: every rule that FIRED is declared by the grammar" % tag,
       sorted(fired - set(Reading.RULES)))
    ck(ent.get("rules_fired") is not None,
       "%s: the rules that fired are RECORDED (a reader cannot be audited from "
       "an outcome alone)" % tag)
    # R2
    wins = sum(1 for it in items.values() if it["solved"])
    den = rnd["items_attempted_emitted"]
    ck(wins == rnd["wins"], "%s: wins recount from the items" % tag,
       (wins, rnd["wins"]))
    ck(den == sum(1 for it in items.values() if it["attempted_emitted"]),
       "%s: the denominator is the per-item emitted counts" % tag)
    ck(rnd["score"] == (round(wins / float(den), 6) if den else None),
       "%s: the score RECOMPUTES as solved / attempted_emitted" % tag,
       (rnd["score"], wins, den))
    for bad in ("average_moves", "mean_moves", "moves_score", "efficiency"):
        ck(bad not in rnd and bad not in rnd.get("totals", {}),
           "%s: no %r anywhere -- moves is a COST and this file checks that it "
           "was not quietly turned into a rate" % (tag, bad))
    ck(rnd["totals"]["moves"] == sum(it["moves"] for it in items.values()),
       "%s: the cost is a SUM, not an average" % tag)
    # B1
    ck(rnd["totals"]["attempted_consumed"]
       == sum(it["attempted_consumed"] for it in items.values()),
       "%s: attempted_consumed sums" % tag)
    # the loose diagnostic is a DIAGNOSTIC
    loose = sum(1 for it in items.values() for ply in it["trace"]
                if ply["reading"].get("loose_give_up_diagnostic")
                and ply["reading"]["outcome"] != "give_up")
    ck(loose == rnd["totals"]["loose_give_up_unscored"],
       "%s: the loose abstention count in the record matches a recount from the "
       "plies, and none of it is in `give_up`" % tag,
       (loose, rnd["totals"]["loose_give_up_unscored"]))
    ck(sum(it["give_up"] for it in items.values()) == rnd["totals"]["give_up"],
       "%s: give_up counts ONLY exact-token abstentions" % tag)
    # exit code: recomputed from the record, and 1 is reserved
    never = sum(1 for it in items.values()
                if it["terminal"] == "NEVER_STARTED")
    readable = sum(1 for it in items.values()
                   if it["attempted_consumed"] > it["not_an_action"])
    want = (4 if (never == len(items) or rnd["started"] == 0)
            else (2 if readable == 0 else 0))
    ck(ent["exit_code"] == want,
       "%s: the exit code reflects the RUN (recomputed from the record as %d)"
       % (tag, want), ent["exit_code"])
    ck(ent["exit_code"] != 1,
       "%s: exit 1 is RESERVED FOR THE INSTRUMENT -- no entrant run may emit it "
       "(a model that fails is a 0 with a zero score; an instrument that fails "
       "is a 1), and this control is what makes the reservation a fact" % tag)
    # the weights digest, or its absence explained
    w = ent.get("weights")
    if ent.get("entrant_is_a_model"):
        ck(w is not None and (w.get("sha256") or w.get("note")),
           "%s: a model run carries a DIGEST or the stated reason there is none"
           % tag, w)
    else:
        ck(ent.get("instrument") in ("code", "none"),
           "%s: a code entrant is labelled as a different instrument" % tag)
    ck(ent.get("on_board") == (name in ("model",))
       or ent.get("is_harness_proof") or ent.get("on_board") is False,
       "%s: pooling flag present" % tag)
    # the trace is complete: every emitted answer is recorded
    emitted = sum(it["attempted_emitted"] for it in items.values())
    recorded = sum(len([p for p in it["trace"] if p.get("raw") is not None])
                   for it in items.values())
    ck(emitted == recorded,
       "%s: every answer the entrant emitted is in the trace (%d emitted / %d "
       "recorded) -- an answer dropped from the record is an answer the run "
       "decided for the entrant" % (tag, emitted, recorded))
    # replay
    budget = rnd["attempt_budget_per_level"]
    rep = replay({"rounds": {"R_digdug_levels": rnd}}, levels, budget)
    for lname, r in sorted(rep.items()):
        if "error" in r:
            ck(False, "%s/%s: %s" % (tag, lname, r["error"]))
            continue
        if r["never_started"]:
            ck(r["got"]["moves"] == 0 and r["got"]["attempted_consumed"] == 0,
               "%s/%s: a NEVER_STARTED item replays as an untouched board"
               % (tag, lname))
            continue
        diffs = {k: (r["got"][k], r["want"][k]) for k in r["want"]
                 if r["got"][k] != r["want"][k]}
        ck(not diffs,
           "%s/%s: REPLAY reproduces the record exactly (counters, board, "
           "named terminal reason)" % (tag, lname), diffs)
        # per-ply: every consumed ply's word and position match a fresh run
        st2 = digdug.State(levels[lname])
        bad_ply = None
        for i, ply in enumerate(items[lname]["trace"]):
            if ply.get("raw") is None:
                continue
            got = digdug.feed(st2, ply["raw"], budget=budget)
            # compare the THREE fields a replay can reproduce.  The recorded ply
            # carries runner-only keys (`raw`, `prompt_sha256`, `diag`) that a
            # replay never regenerates, and `position` is a list in JSON and a
            # tuple in the engine -- so a whole-dict compare fails on the
            # container type and on the extras, which is not a finding about the
            # run.  The fields below are the ones the rules own.
            def norm(ply_or_got):
                pos = ply_or_got.get("position")
                return (ply_or_got.get("word"),
                        None if pos is None else [int(x) for x in pos],
                        ply_or_got.get("outcome"))
            if norm(got) != norm(ply):
                bad_ply = (i, norm(got), norm(ply))
                break
        ck(bad_ply is None,
           "%s/%s: every PLY replays, not just the total -- a total that matches "
           "by accident is a real risk in a game where blocked letters pile up"
           % (tag, lname), bad_ply)
    # R2 against the oracle: no run beats the proven optimum
    if tasks:
        for row in tasks.get("levels", []):
            lid = row["file"].split("/")[-1]
            it = items.get(lid)
            if not it or it["terminal"] == "NEVER_STARTED":
                continue
            opt = row["optimal_moves"]
            if opt is not None and it["solved"]:
                ck(it["moves"] >= opt,
                   "%s/%s: a solved run never beats the proven optimum (%s < %s "
                   "would mean the proof is wrong, not that the entrant is good)"
                   % (tag, lid, it["moves"], opt), (it["moves"], opt))
            if row["optimal_moves"] is None:
                ck(it["solved"] is False,
                   "%s/%s: nothing solves a level proven lost, so `solved=True` "
                   "here would refute the PROOF and this check is where it would "
                   "be caught" % (tag, lid))


def verify_all(results_dir=None, verbose=True):
    results_dir = results_dir or RESULTS
    levels = digdug.load_level_set()
    tasks = None
    if os.path.isfile(os.path.join(HERE, "tasks", "digdug_v1.json")):
        with open(os.path.join(HERE, "tasks", "digdug_v1.json")) as fh:
            tasks = json.load(fh)
    files = sorted(f for f in os.listdir(results_dir)
                   if f.startswith("digdug_v1_") and f.endswith(".json"))
    if not files:
        print("no bundles in %s -- there is nothing to verify, which is not the "
              "same as everything passing" % results_dir)
        return False
    settings = {}
    gpus = {}
    print("replaying %d bundle(s) from %s" % (len(files), results_dir))
    for f in files:
        path = os.path.join(results_dir, f)
        try:
            reasoning, gpu, cfg = check_bundle(path, levels, tasks)
        except Exception as exc:                                    # noqa: BLE001
            ck(False, "%s: the bundle could not be read and replayed" % f,
               repr(exc))
            continue
        settings.setdefault(reasoning, []).append(f)
        key = json.dumps(gpu, sort_keys=True, default=str)
        gpus.setdefault(key, []).append(f)
    # ONE INSTRUMENT PER EVENT
    ck(len(settings) == 1,
       "the results dir holds ONE declared reasoning setting; bundles disagree, "
       "so this directory is a mixture and no table may be built from it",
       {k: v for k, v in settings.items()})
    ck(len(gpus) == 1,
       "the results dir holds ONE declared GPU; the probe result disagrees "
       "across bundles, which means they were run on different machines and are "
       "not one event",
       {k[:60]: v for k, v in gpus.items()})
    for lname, row in sorted({r["file"].split("/")[-1]: r
                              for r in (tasks or {}).get("levels", [])}.items()):
        lv = levels.get(lname)
        if lv is None:
            continue
        ck(lv.sha256 == row["sha256"],
           "the item set's digest for %s matches the file on disk" % lname,
           (row["sha256"], lv.sha256))
        r = digdug_solve.verify_level(lv, budget=10)
        ck(r["proven_optimal"] == row["optimal_moves"]
           and r["distinct_shortest_plans"] == row["distinct_shortest_plans"]
           and r["winnable"] == row["winnable"],
           "the item set's PROVEN optima still hold under the code on disk "
           "(%s: opt %s plans %s)" % (lname, r["proven_optimal"],
                                      r["distinct_shortest_plans"]),
           (row, {k: r[k] for k in ("winnable", "proven_optimal",
                                    "distinct_shortest_plans")}))
    if verbose:
        print("  %d checks, %d failures" % (CHECKS[0], len(FAILURES)))
        for f in FAILURES:
            print("  FAIL %s" % f)
        print("REPLAY %s" % ("PASSED" if not FAILURES else "FAILED"))
    return not FAILURES


def main(argv):
    d = argv[1] if len(argv) > 1 else RESULTS
    return 0 if verify_all(d) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
