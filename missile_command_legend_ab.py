#!/usr/bin/env python3
"""THE LEGEND A/B -- one entrant, two states, two arms, ONE CLAUSE APART.

PRE-REGISTERED IN `PREREG_mc_legend_ab.md` BEFORE THE SECOND ARM WAS RUN, with its prediction and its three
branches. This script is only the carrier: **it imports the driver and reuses its `run()`**, so the arm
that is sent, the digest that is recorded and the log's name have ONE definition (RULING 79's shape, applied
to the driver rather than to the reader).

WHY ITS OWN ARTIFACT (`probes/MC_LEGEND_AB.json`) AND NOT THE PER-CELL COORDINATES: the per-cell name
`probes/MC_<entrant>_<level>.json` is the PUBLISHED coordinate and does not move -- one run, one path -- so
an A/B that overwrote a cell for its second arm would destroy the first arm's record. Both arms' cells
therefore travel in ONE run-level file, which is the shape the sokoban cabinet's `REASONING_AB.json` has.

    scripts/run_guarded.sh mc-legend-ab <cabinet dir> /usr/bin/python3 missile_command_legend_ab.py
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import missile_command_run as R                                               # noqa: E402

PREREG = os.path.join(HERE, "PREREG_mc_legend_ab.md")
ENTRANT = "Qwen3.5-2B-UD-Q4_K_XL.gguf"          # the entrant whose example-arm cells are on disk already
STATES = ("levels/mc_01_one_shot.txt", "levels/mc_02_scarcity.txt")

# ==================================================================================================
# THE TWO ARMS, NAMED ONCE -- AND WHY THEY ARE NOT READ FROM THE DRIVER'S ARM SET.
#
# THESE TWO NAMES ARE THE COMPARISON AS PUBLISHED. They are the arms of the A/B in
# `probes/MC_LEGEND_AB.json` (sha256
# 029244b6e5232a6b77e67cf5e21dea342c7da336a932386b3a16015e96b286c8), whose own `arms`, `legend_arms`,
# `cells` and `totals` fields are keyed by exactly these two strings -- the entrant's cells for both arms
# travelled in that ONE run-level file, which is why the pair cannot be re-derived from the driver without
# re-keying a published record (`PREREG_mc_ab_arm_keys.md`, card t_d21287e4, refused the same derivation
# one layer in: the direction of the comparison is WHICH ARM CARRIES THE WORKED EXAMPLE, not which arm is
# of record).
#
# `missile_command_run.LEGEND_ARMS` IS THE SET OF ARMS THAT EXIST; this is the PAIR THAT WAS COMPARED, and
# deriving it from that dict would do two wrong things at once: an added third arm would silently turn a
# two-arm A/B into a three-arm run and publish it under `PREREG_mc_legend_ab.md` (whose digest the artifact
# carries), and the run order and the key order of the published `totals` would follow another file's dict.
#
# A KEY IS RIGHT ONLY WHILE THE DRIVER STILL DEFINES IT AS AN ARM. The refusal below is what stops these
# names outliving the arms they name: without it a rename reports an arm that no longer exists as
# `{"cells": 0, ...}` -- every counter zero and `controls_pass` TRUE, because zero cells satisfy both
# equalities trivially -- and a publication under a name that measured nothing reads exactly like one that
# measured something. Measured rather than argued: `scripts/probe_ab_arm_names.py`, readings 4a/4b/4c.
AB_EXAMPLE_ARM, AB_PLAIN_ARM = "example", "plain"
ARMS = (AB_EXAMPLE_ARM, AB_PLAIN_ARM)          # ONE COPY OF THE PAIR: run order, and the keys below
_ab_missing = [a for a in ARMS if a not in R.LEGEND_ARMS]
if _ab_missing:
    raise SystemExit(
        f"REFUSED: this script is the A/B comparison PUBLISHED in probes/MC_LEGEND_AB.json "
        f"(029244b6e5232a6b) between the arms {AB_EXAMPLE_ARM!r} and {AB_PLAIN_ARM!r}; the driver defines "
        f"{tuple(R.LEGEND_ARMS)}. Those two names are the arms the comparison was published under, and one "
        f"that is no longer an arm would be published as zero cells under a label that measured nothing. "
        f"RE-PUBLISH the A/B as a NEW artifact with a NEW digest; do not re-key this script to the "
        f"declaration or to the driver's arm set.")
OUT = os.path.join(HERE, "probes", "MC_LEGEND_AB.json")
PORT = 8762


def cell_summary(r, arm, state):
    """ONE ROW PER CELL, and the columns are the PREDICTION'S OWN: `unknown` and `fired` are what the
    branches are read from, so they travel beside the tokens that produced them."""
    if not r.get("loaded"):
        return {"arm": arm, "state": state, "loaded": False, "why": r.get("why"),
                "load_failure_class": r.get("load_failure_class")}
    c = r["counts"]
    ttotal = len(R.S.parse_state(r["state_text"])["threats"])
    return {"arm": arm, "state": state, "loaded": True,
            "legend_digest": r["legend_digest"], "confidence": None,
            "tokens": r["tokens"], "score": r["score"], "cities_total": r["cities_total"],
            # THE COUNTERS ARE THE RESULT, SO ALL OF THEM TRAVEL -- EVERY COUNTER, VERBATIM. The first
            # version of this row carried a CHOSEN SUBSET (fired/unknown/malformed/passed/out_of_range/
            # no_ammo/hit/spared) and left `late` out, so the plain arm's mc_02 cell read "out_of_range 2,
            # fired 0, unknown 0" against SIX tokens and four of them were invisible. A summary that drops
            # a counter is the same defect as a counter that drops an outcome: the reader cannot tell a
            # zero from a missing row.
            "counts": dict(c),
            **{k: c[k] for k in c},
            "silos_that_exist": sorted(R.S.parse_state(r["state_text"])["silos"]),
            "threats_total": len(R.S.parse_state(r["state_text"])["threats"]),
            "silo_digits_in_the_tokens": sorted({t[0] for t in r["tokens"] if len(t) == 2}),
            "entrant_digest": r["entrant_digest"],
            "server_binary_digest": R.carried_identity(r)["server_binary_digest"],
            "server_argv": r["config"]["server_argv"],
            "sufficiency": r["sufficiency"],
            "budget_signature": r["budget_signature"],
            "controls": cell_controls({"counts": c, "tokens": r["tokens"], "threats_total": ttotal})}


COUNTER_KEYS = ("fired", "passed", "no_ammo", "out_of_range", "unknown", "malformed", "late", "hit",
                "spared")
# TWO KINDS OF COUNTER, AND THEY OBEY TWO DIFFERENT EQUALITIES. Merging them is how a control reads False
# on a correct record -- which is what the first version of this check did, loudly, on nine tokens against
# eighteen outcomes.
PER_TOKEN_COUNTERS = ("fired", "passed", "no_ammo", "out_of_range", "unknown", "malformed", "late")
IMPACT_COUNTERS = ("hit", "spared")


def cell_controls(loaded):
    """THE TWO EQUALITIES, PER CELL, IN THE RECORD RATHER THAN IN A READER'S HEAD.

      1. EVERY TOKEN PRODUCES EXACTLY ONE OUTCOME: fired + passed + no_ammo + out_of_range + unknown +
         malformed + late == tokens. A summary that drops a counter fails this instead of reading lower.
      2. EVERY THREAT IS ACCOUNTED FOR: fired + hit + spared == the number of threats in the state. A
         threat is DESTROYED by an interceptor, HITS a city, or is SPARED on empty ground -- and nothing
         else can happen to it. `spared` is the counter that shows the decoy was correctly ignored, so a
         record that loses it loses the faculty.
    """
    c = loaded["counts"]
    return {"tokens": len(loaded["tokens"]),
            "per_token_outcomes": sum(c[k] for k in PER_TOKEN_COUNTERS),
            "every_token_has_exactly_one_outcome":
                sum(c[k] for k in PER_TOKEN_COUNTERS) == len(loaded["tokens"]),
            "threats_in_the_state": loaded["threats_total"],
            "destroyed_plus_hit_plus_spared": c["fired"] + c["hit"] + c["spared"],
            "every_threat_is_accounted_for":
                c["fired"] + c["hit"] + c["spared"] == loaded["threats_total"]}


def arm_totals(cells, arm):
    """EVERY COUNTER, SUMMED, WITH THE CONTROLS CARRIED ALONGSIDE THEM."""
    got = [c for c in cells if c["arm"] == arm and c.get("loaded")]
    t = {"cells": len(got),
         "score": sum(c["score"] for c in got),
         "cities_total": sum(c["cities_total"] for c in got),
         "tokens_generated": sum(len(c["tokens"]) for c in got),
         "threats_total": sum(c["threats_total"] for c in got),
         "best_cell_score": (max(c["score"] for c in got) if got else None)}
    for k in COUNTER_KEYS:
        t[k] = sum(c.get("counts", {}).get(k, 0) for c in got)
    t["sum_of_per_token_outcomes"] = sum(t[k] for k in PER_TOKEN_COUNTERS)
    t["every_token_has_exactly_one_outcome"] = t["sum_of_per_token_outcomes"] == t["tokens_generated"]
    t["destroyed_plus_hit_plus_spared"] = t["fired"] + t["hit"] + t["spared"]
    t["every_threat_is_accounted_for"] = t["destroyed_plus_hit_plus_spared"] == t["threats_total"]
    t["controls_pass"] = (t["every_token_has_exactly_one_outcome"]
                          and t["every_threat_is_accounted_for"])
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrant", default=ENTRANT)
    ap.add_argument("--overwrite-artifact", dest="reason", default=None, metavar="REASON")
    ap.add_argument("--port", type=int, default=PORT)
    a = ap.parse_args()

    if not os.path.exists(PREREG):
        print(f"  REFUSED: {PREREG} is missing -- an A/B without its pre-registration is a result with no "
              f"prediction to be right or wrong about."); return 2
    entrant = a.entrant if os.path.exists(a.entrant) else os.path.join(R.MODELS, a.entrant)
    if not os.path.exists(entrant):
        print(f"  ENTRANT ABSENT: {a.entrant}"); return 2
    ok, msg = R.binary_guard(entrant)
    if not ok:
        print(msg); return 2

    gate_ok, gate_msg, replaced = R.artifact_gate(OUT, a.reason)
    if not gate_ok:
        for line in gate_msg.splitlines():
            print(f"  {line}")
        return 4

    cells = []
    for arm in ARMS:
        R.LEGEND_ARM = arm                       # read at CALL TIME by the driver, one definition
        for state in STATES:
            p = R.resolve_state(state)
            if p is None:
                print(f"  STATE ABSENT: {state}"); return 2
            cap = R.clock_cap(open(p, encoding="utf-8").read())
            print(f"  === {arm} / {os.path.basename(p)}  (cap {cap}, legend {R.legend_digest(arm)})")
            r = R.run(entrant, p, cap, a.port)
            cells.append(cell_summary(r, arm, os.path.basename(p).replace(".txt", "")))
            c = cells[-1]
            print("      " + ("LOADED  score %s/%s  fired %s unknown %s tokens %s"
                              % (c["score"], c["cities_total"], c["fired"], c["unknown"], c["tokens"])
                              if c.get("loaded") else f"DID NOT LOAD -- {c['load_failure_class']}"))
    R.LEGEND_ARM = None

    ex, pl = arm_totals(cells, AB_EXAMPLE_ARM), arm_totals(cells, AB_PLAIN_ARM)
    controls_ok = all(c.get("controls", {}).get("every_token_has_exactly_one_outcome", False)
                      and c.get("controls", {}).get("every_threat_is_accounted_for", False)
                      for c in cells if c.get("loaded"))
    if not ex["cells"] or not pl["cells"]:
        branch = ("NO VERDICT -- one arm did not load, so there is nothing to compare. The cells and their "
                  "failure classes are recorded above; this is a measurement of the CARD, not of the model.")
    elif not controls_ok:
        branch = ("NO VERDICT -- THE RECORD'S OWN CONTROLS DO NOT PASS (see each cell's `controls`): every "
                  "token must produce exactly one outcome, and every threat must be destroyed, hit or "
                  "spared. Until that holds, the comparison below is not a measurement.")
    elif pl["unknown"] < ex["unknown"] and pl["fired"] > ex["fired"]:
        branch = ("BRANCH 1 -- THE EXAMPLE WAS THE CARRIER: `unknown` DOWN and `fired` UP, exactly as the "
                  "pre-registration predicted.")
    elif pl["unknown"] == ex["unknown"] and pl["fired"] == ex["fired"]:
        branch = ("BRANCH 2 -- THE EXPLANATION IS WRONG: nothing moved, so the echo has another cause and "
                  "the example is not what supplies the value.")
    else:
        branch = ("BRANCH 3 -- THE EXAMPLE WAS LOAD-BEARING FOR FORMAT COMPLIANCE, or the movement is not "
                  "the predicted one. Read the tokens; the counters alone cannot say which.")

    art = {
        "what": "THE LEGEND A/B -- one entrant, two states, two arms, ONE CLAUSE APART",
        "prereg": os.path.relpath(PREREG, HERE), "prereg_digest": R.file_digest(PREREG),
        "entrant": os.path.basename(entrant).replace(".gguf", ""),
        "entrant_digest": R.file_digest(entrant),
        "legend_arms": R.legend_arm_digests(),
        "arms": {a_: R.LEGEND_ARMS[a_] for a_ in ARMS},
        "protocol": {"play_mode": "step_locked", "clock_audit": R.clock_audit(),
                     "reasoning": R.REASONING, "reasoning_argv": R.reasoning_argv(),
                     "fit_argv": R.fit_argv(), "max_tokens_ceiling": R.MAX_TOKENS},
        "binary": R.binary_provenance(),
        "reader": R.reader_provenance(),
        "cells": cells,
        "totals": {AB_EXAMPLE_ARM: ex, AB_PLAIN_ARM: pl},
        "branch": branch,
        "reading": ("The prediction and its three branches are in the pre-registration; the branch above is "
                    "selected BY THE COUNTERS, not by a preference. Scope: ONE entrant, TWO states, n=1 per "
                    "cell -- a demonstration, not a field. THE DECLARED ARM DOES NOT MOVE AND IS NOT "
                    "ASSERTED HERE: this A/B writes nothing but this artifact, the arm of record is named by "
                    "`MC_DECLARATION.md`'s `legend_arm` and read by the driver (it reported it as "
                    f"`{R.legend_source()}` when this artifact was written), and changing it is a separate "
                    "act with its own reason (`DECISION_mc_legend_arm.md`). BOTH ARMS REMAIN SELECTABLE at "
                    "the driver's call time (`--legend example` / `MC_LEGEND=example`): this A/B runs both, "
                    "and every cell carries the digest of the arm it was taken under."),
    }
    if replaced is not None:
        art["artifact_replaced"] = replaced
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(art, open(OUT, "w"), indent=1)
    print(f"\n  totals example {ex}")
    print(f"  totals plain   {pl}")
    print(f"  {branch}")
    print(f"  artifact  {os.path.relpath(OUT, HERE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
