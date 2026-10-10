#!/usr/bin/env python3
# test_sokoban2.py -- the side script.  Reads every bundle in results/ and
# RECOMPUTES the result from the record.
#
# It imports the one reader of record.  It does NOT reimplement it: there is no
# copy of the token rules in this file, and the test would fail if there were
# one that disagreed.  Where this file needs to know what an answer means, it
# asks sokoban_reader.
#
# The standard it enforces is GAME_CONTRACT.md's:
#   "Can a stranger reconstruct the game from the recorded bundle?"
# So it does not re-read the summary fields and believe them -- it replays the
# recorded raws through the reader and step() and checks it gets the same
# numbers the bundle claims.

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from sokoban_reader import grammar_as_record, read_answer, reader_sha256  # noqa
import sokoban2                                                          # noqa
from sokoban2 import State, feed                                         # noqa
import sokoban2_run                                                      # noqa

RESULTS = os.path.join(HERE, "results")
LEVEL_FILES = sokoban2.LEVEL_FILES


def _say(cond, label, seen=None):
    print("  %s %s%s" % ("ok  " if cond else "FAIL", label,
                         "" if cond or seen is None else "   <- %r" % (seen,)))
    return bool(cond)


def _sha(path):
    import hashlib
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def verify_bundle(path, levels, declared=None):
    """Replay one bundle.  -> (n_checks, n_failed, declared_fields)."""
    ok = True
    with open(path) as fh:
        b = json.load(fh)
    name = os.path.basename(path)
    print("  -- %s" % name)

    ent = b["results"][0]
    rnd = ent["rounds"]["R_sokoban_levels"]

    # 1. PROVENANCE -- the record names the code that produced the verdict.
    ok &= _say(ent["verdict_code"]["sha256"]
               == _sha(os.path.join(HERE, "sokoban2_run.py")),
               "%s: verdict_code digest matches sokoban2_run.py" % name,
               ent["verdict_code"]["sha256"])
    ok &= _say(ent["verdict_code"]["reader"]["sha256"] == reader_sha256(),
               "%s: the bundle names the reader that read it" % name)
    ok &= _say(ent["verdict_code"]["simulator"]["sha256"]
               == _sha(os.path.join(HERE, "sokoban2.py")),
               "%s: the bundle names the simulator that played it" % name)

    # 2. THE GRAMMAR IS IN THE RECORD -- you cannot compare two bundles read
    #    under different rules.
    g = ent.get("grammar") or {}
    ok &= _say(g.get("reader_sha256") == reader_sha256(),
               "%s: the grammar block carries the reader's digest" % name)
    ok &= _say(bool(g.get("give_up_tokens")),
               "%s: the abstention token set is in the record" % name)
    ok &= _say(g.get("truncation", "").startswith("NEVER"),
               "%s: the record says the reader never truncates" % name)

    # 3. THE TWO DECLARED FIELDS -- present, and the SAME across the run.
    ok &= _say(b["declared"]["reasoning"] in ("on", "off", "unset"),
               "%s: reasoning is DECLARED" % name,
               b["declared"]["reasoning"])
    ok &= _say("gpu" in b["declared"] and "probe" in b["declared"]["gpu"],
               "%s: the GPU is DECLARED, with the probe that ran" % name)
    ok &= _say(ent["config"].get("reasoning") == b["declared"]["reasoning"],
               "%s: config.reasoning agrees with the run's declaration" % name,
               (ent["config"].get("reasoning"), b["declared"]["reasoning"]))

    # 4. THE EXIT CODE IS IN THE RECORD AND MATCHES THE VERDICT.
    code = ent.get("exit_code")
    verdict = ent.get("verdict", "")
    consistent = (
        (verdict == "SCORED" and code == sokoban2_run.EXIT_SCORED)
        or (verdict.startswith("ERROR: ZERO MEASURED")
            and code == sokoban2_run.EXIT_ZERO_MEASURED)
        or (verdict.startswith("ERROR: POPULATION NEVER STARTED")
            and code == sokoban2_run.EXIT_NEVER_STARTED))
    ok &= _say(consistent, "%s: exit %s is consistent with verdict %r"
               % (name, code, verdict))

    # 5. THE ZERO RULE -- coverage 1.000 with readable 0 is an ERROR.
    if rnd["coverage"] == 1.0 and rnd["readable"] == 0:
        ok &= _say(code != sokoban2_run.EXIT_SCORED,
                   "%s: coverage 1.000 with readable 0 is an ERROR, not a "
                   "verdict" % name, code)

    # 6. REPLAY.  The record is a sufficient statistic: replaying the recorded
    #    raws through the one reader and the frozen step() must reproduce the
    #    recorded counters exactly.
    tot = {"moves": 0, "attempted": 0, "blocked": 0, "not_an_action": 0,
           "give_up": 0}
    for lname in LEVEL_FILES:
        it = rnd["items"][lname]
        level = levels[lname]
        st = State(level)
        raws = [p["raw"] for p in it["trace"]]
        for raw in raws:
            feed(st, raw)
            if st.ended:
                break
        got = {"moves": st.moves, "attempted": st.attempted,
               "blocked": st.blocked, "not_an_action": st.not_an_action,
               "give_up": st.give_up, "after_end": st.after_end}
        want = {k: it[k] for k in got}
        ok &= _say(got == want,
                   "%s/%s: replaying the %d recorded raws reproduces the "
                   "counters" % (name, lname, len(raws)), (got, want))
        ok &= _say(st.solved == it["solved"],
                   "%s/%s: replay reproduces solved=%s"
                   % (name, lname, it["solved"]), st.solved)
        ok &= _say(st.render() == it["final_board"],
                   "%s/%s: replay reproduces the final board" % (name, lname))
        for k in tot:
            tot[k] += it[k]
    ok &= _say(tot == {k: rnd["totals"][k] for k in tot},
               "%s: the recorded totals are the sum of the per-level counters"
               % name, (tot, rnd["totals"]))

    # 7. THE RAW SURVIVES.  An extraction is a claim about the output; the raw
    #    is the only thing that can falsify it. (PRECEDENCE.md)
    ok &= _say(all("raw" in p for it in rnd["items"].values()
                   for p in it["trace"]),
               "%s: every ply carries the raw answer" % name)

    # 8. THE DIGEST, NOT ONLY THE NAME -- for a model entrant.
    if ent.get("entrant_is_a_model"):
        # The rule is NOT "a digest is present".  It is: a digest, or a
        # WRITTEN REASON why there is none.  A missing digest with no note is
        # the defect; a null digest with a note is the instrument being honest.
        w = ent.get("weights") or {}
        ok &= _say(bool(w.get("sha256")) or bool(w.get("note")),
                   "%s: a model entrant carries the weights DIGEST, or states "
                   "in writing why there is none" % name, w)
    return ok, {"reasoning": b["declared"]["reasoning"],
                "gpu": (b["declared"]["gpu"] or {}).get("name"),
                "gpu_probe": (b["declared"]["gpu"] or {}).get("probe")}


def verify_all(results_dir=RESULTS):
    ok = True
    levels = sokoban2.load_level_set()
    paths = sorted(glob.glob(os.path.join(results_dir, "sokoban_v1_*.json")))
    if not paths:
        print("  FAIL no bundles in %s" % results_dir)
        return False
    print("BUNDLE VERIFICATION -- %d bundles, replayed from the record."
          % len(paths))
    declared = []
    for p in paths:
        good, dec = verify_bundle(p, levels)
        ok &= good
        declared.append(dec)

    # A11 -- two bundles for the same event must not declare different
    # instruments.  If they do, they are not the same measurement and neither
    # file says so.
    reasons = sorted({d["reasoning"] for d in declared})
    gpus = sorted({repr(d["gpu"]) for d in declared})
    ok &= _say(len(reasons) == 1,
               "A11: every bundle declares the SAME reasoning setting %s"
               % reasons, reasons)
    ok &= _say(len(gpus) == 1,
               "A11: every bundle declares the SAME GPU %s" % gpus, gpus)
    print("")
    print("BUNDLE VERIFICATION %s" % ("PASSED" if ok else "FAILED"))
    return ok


if __name__ == "__main__":
    sys.exit(0 if verify_all() else 1)
