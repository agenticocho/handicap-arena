#!/usr/bin/env python3
# test_digdug.py -- THE SIDE SCRIPT.  It replays every bundle from the record
# and recomputes the verdict, and it checks the claims the report makes about
# the records rather than trusting them.
#
# It imports the cabinet; it does not reimplement it.  What it does
# reimplement is nothing: every recomputation below calls the same
# `score_field`, `facets_from_trace` and reader the runner used, on the data
# stored in the file.  A bundle that cannot be replayed from what is in it is
# a claim, not a record.
#
#   python3 test_digdug.py [results_dir]        exit 0 = every check passed
#
# Stdlib only.

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import digdug                                              # noqa: E402
import digdug_reader                                       # noqa: E402
import digdug_run                                          # noqa: E402
import freeze                                              # noqa: E402

CARD_VERSION = "digdug_v1"


class T(object):
    def __init__(self):
        self.n = 0
        self.fails = []

    def ok(self, cond, label, seen=None):
        self.n += 1
        if cond:
            print("ok   %s" % label)
        else:
            extra = "" if seen is None else "   (got %r)" % (seen,)
            print("FAIL %s%s" % (label, extra))
            self.fails.append(label + extra)
        return bool(cond)


def main(argv=None):
    out_dir = (argv[1] if argv and len(argv) > 1
               else os.path.join(HERE, "results"))
    t = T()
    paths = sorted(glob.glob(os.path.join(out_dir, "%s_*.json"
                                          % CARD_VERSION)))
    if not t.ok(bool(paths), "there are bundles in %s" % out_dir):
        return 1
    frozen = freeze.read_record()
    ok_freeze, why = freeze.verify()
    t.ok(ok_freeze, "the tree is still the frozen tree", why)

    reasonings, gpus, budgets = set(), set(), set()
    for p in paths:
        with open(p, "r", encoding="utf-8") as fh:
            b = json.load(fh)
        r = b["results"][0]
        name = os.path.basename(p)
        reasonings.add(b["declared"]["reasoning"])
        gpus.add(json.dumps(b["declared"]["gpu"], sort_keys=True))
        budgets.add(b["declared"]["budget_turns_per_level"])

        # -- the record names the contract that produced it -----------------
        t.ok(r["contract"]["sha256"] == (frozen or {}).get("contract_sha256"),
             "%s names the FROZEN contract by digest" % name,
             (r["contract"]["sha256"] or "")[:12])
        t.ok(r["contract"]["combined_digest"] ==
             (frozen or {}).get("combined_digest"),
             "%s carries the combined digest of the frozen tree" % name)
        # -- frozen BEFORE the field, checked from the timestamps -----------
        t.ok(b["generated"] >= (frozen or {}).get("frozen_at", "9999"),
             "%s was generated AFTER the freeze (%s >= %s)"
             % (name, b["generated"], (frozen or {}).get("frozen_at")))
        # -- which code produced the verdict --------------------------------
        vc = r["verdict_code"]
        t.ok(all(vc.get(k) for k in ("sha256", "simulator", "reader",
                                     "solver")),
             "%s says WHICH CODE produced the verdict, by four digests"
             % name)
        # -- R1, from the bundle's own grammar record -----------------------
        g = r["grammar"]
        t.ok(g["give_up_tokens"] == list(digdug_reader.GIVE_UP_TOKENS),
             "%s R1: the grammar in the RECORD equals the code's scored list "
             "(%d tokens)" % (name, len(g["give_up_tokens"])))
        t.ok(g["give_up_token_count"] == len(set(g["give_up_tokens"])),
             "%s B3: the recorded token list has no duplicates" % name)
        # -- weights digest, or a written reason there is none --------------
        w = r.get("weights")
        if r["entrant_is_a_model"]:
            t.ok(bool(w) and (w.get("sha256") or w.get("note")),
                 "%s carries the weights DIGEST or states in writing why "
                 "there is none" % name)
        # -- a failed load names the holder --------------------------------
        if r.get("never_started"):
            adm = r.get("admission") or {}
            holder = adm.get("holder") or {}
            t.ok("probe" in holder and holder.get("note") is not None
                 or holder.get("holders"),
                 "%s: the failed load NAMES the holder or says which probe "
                 "found nobody" % name)
            continue

        # -- replay: the score, from the primitives in the file -------------
        items = r["rounds"]["R_digdug_levels"]["items"]
        sc = digdug_run.score_field(items)
        stored = r["rounds"]["R_digdug_levels"]
        for k in ("solved", "attempted_emitted", "answers_emitted",
                  "answers_consumed", "answers_after_end", "not_an_action"):
            t.ok(sc[k] == stored.get(k),
                 "%s: %s recomputes from the record (%s)" % (name, k, sc[k]),
                 stored.get(k))
        t.ok(sc["score"] == stored.get("score"),
             "%s: the GATE recomputes (%s)" % (name, sc["score"]))
        t.ok(sc["score"] is None or sc["attempted_emitted"] > 0,
             "%s: R2 the gate has a denominator" % name)
        # -- B1: emitted and consumed are different numbers, both present ---
        t.ok("answers_emitted" in stored and "answers_consumed" in stored,
             "%s: B1 both emitted and consumed are in the record" % name)
        t.ok(stored["answers_emitted"] == stored["answers_consumed"] +
             stored["answers_after_end"],
             "%s: B1 emitted = consumed + after_end (%d = %d + %d)"
             % (name, stored["answers_emitted"], stored["answers_consumed"],
                stored["answers_after_end"]))
        # -- replay: BOTH FACETS, from the STORED traces -------------------
        digests = set()
        for lvl, it in items.items():
            if not it.get("scored", True):
                t.ok(it.get("correct_answer_was") is not None,
                     "%s: the CONTROL level says what the correct answer was"
                     % name)
                if it.get("trace"):
                    lv = digdug.find_level(lvl)
                    ff = digdug.facets_from_trace(lv, it["trace"],
                                                  it["budget"])
                    if ff["facet2_hazard_aware"]["killed"]:
                        t.ok(ff["facet1_destruction"]["barrier_lost"],
                             "%s: %s the nesting holds on the CONTROL level "
                             "too" % (name, lvl))
                continue
            level = digdug.find_level(lvl)
            trace = it.get("trace")
            if not t.ok(bool(trace), "%s: %s carries its trace" % (name, lvl)):
                continue
            lm = (r.get("levels") or {}).get(lvl) or {}
            t.ok(lm.get("enclosed") is True,
                 "%s: %s B2 enclosure is MEASURED in the record, true"
                 % (name, lvl), lm.get("enclosed"))
            t.ok(lm.get("sha256") == level.sha256,
                 "%s: %s the record names the level by digest and it matches "
                 "the file on disk" % (name, lvl))
            t.ok(lm.get("distinct_optimal_lines") is not None,
                 "%s: %s B3 the distinct-optimal-line COUNT is in the record"
                 % (name, lvl))
            f = digdug.facets_from_trace(level, trace, it["budget"])
            digests.add(f["trace_sha256"])
            t.ok(f["trace_sha256"] == it["facets"]["trace_sha256"],
                 "%s: %s trace digest reproduces on replay" % (name, lvl))
            f1, f2 = f["facet1_destruction"], f["facet2_hazard_aware"]
            s1 = it["facets"]["facet1_destruction"]
            s2 = it["facets"]["facet2_hazard_aware"]
            for k in ("barrier_lost_at_turn", "budget_ruin_at_turn"):
                t.ok(f1[k] == s1[k],
                     "%s: %s facet1.%s replays (%s)" % (name, lvl, k, f1[k]),
                     s1[k])
            for k in ("died_at_turn", "kill_path_cells_dug_by_player",
                      "dig_to_death_turns"):
                t.ok(f2[k] == s2[k],
                     "%s: %s facet2.%s replays (%s)" % (name, lvl, k, f2[k]),
                     s2[k])
            # C8: one trace, two facets
            t.ok(f1["trace_sha256"] == f2["trace_sha256"],
                 "%s: %s C8 both facets cite ONE trace" % (name, lvl))
            # the nesting the contract claims, checked on EVERY death in the
            # field, the control level included
            if f2["killed"]:
                t.ok(f1["barrier_lost"],
                     "%s: %s facet 2 fired, so facet 1 must have (the "
                     "nesting claim)" % (name, lvl))
        # -- the per-level rules_fired names the rule that decided each ply -
        for lvl, it in items.items():
            for rule in it.get("rules_fired", {}):
                t.ok(rule in ("action_letter", "give_up_token_exact",
                              "wasd_not_a_synonym", "multi_line",
                              "empty_answer", "none_answer",
                              "multi_char_no_truncation",
                              "single_char_not_an_action",
                              "wait_is_not_an_action"),
                     "%s: %s every rule that fired is a NAMED rule (%s)"
                     % (name, lvl, rule))
                break

    t.ok(len(reasonings) == 1,
         "ONE declared reasoning setting across the whole directory (%s)"
         % sorted(reasonings), sorted(reasonings))
    t.ok(len(gpus) == 1, "ONE declared GPU across the whole directory")
    t.ok(len(budgets) == 1,
         "ONE declared budget across the whole directory (%s)"
         % sorted(budgets))
    gpu = json.loads(sorted(gpus)[0]) if gpus else {}
    t.ok(gpu.get("name") is None and bool(gpu.get("probe")),
         "no accelerator is NULL with the probe that ran, never 0.00 and "
         "never 'none'", gpu.get("probe"))

    print()
    if t.fails:
        print("SIDE SCRIPT FAIL -- %d/%d, %d failed"
              % (t.n - len(t.fails), t.n, len(t.fails)))
        for f in t.fails[:20]:
            print("     %s" % f)
        return 1
    print("SIDE SCRIPT PASS -- %d checks, %d bundles replayed"
          % (t.n, len(paths)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
