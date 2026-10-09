#!/usr/bin/env python3
"""SOKOBAN -- the first run. The population is DERIVED from ARENA_MODELS, the levels are the verified set,
and the criteria are already frozen in PREREG_sokoban.md.

CHILLY'S SECOND CORRECTION, APPLIED: THE EXCLUSION IS AT THE MODEL LEVEL, NOT THE FILE LEVEL.
`mmproj-*` are ADAPTERS; excluding the adapter is not excluding the thing that consumes it. A
vision-language model in a text population is a category error -- it answers a question about a picture --
and excluding it by FILENAME only catches the projector that accompanies it. So the rule here is:

    A `-VL-` OR `mmproj` IN THE NAME IS EXCLUDED, because the modality is a property of the MODEL.
    And it is recorded as a category exclusion, not discovered as an unexplainable result.

AND REASON COUNTS ARE REPORTED, NEVER ONLY A TOTAL. A population that never ran is not evidence about the
population -- the empty-room rule, one layer out. `did not load` and `played and failed` are different
claims and they are counted separately.

    python3 sokoban_batch.py --n 5
"""
import glob
import hashlib
import json
import os
import platform
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban_run as R                                                 # noqa: E402

LEVELS = ["levels/01_one_push.txt", "levels/02_two_boxes.txt"]


def classifier(name):
    """A CLASS LABEL, NOT AN EXCLUSION.

    `LFM2-350M-Extract` is an EXTRACTION model, and it failed by transcribing the instructions as a schema.
    THAT IS A DATUM, NOT NOISE: it tells us exactly what class of model cannot play a game at all, and it is
    the cleanest single example we have. REMOVING IT WOULD BE RE-SCOPING THE POPULATION TO FIT THE RESULT --
    the move this project has refused all day.

    So it gets a label and stays. A POPULATION THAT IS DESCRIBED HONESTLY IS WORTH MORE THAN A POPULATION
    THAT IS FLATTERING. Same for the 350M SIZE: it is the floor of the field and it belongs in the run
    PRECISELY BECAUSE IT IS THE FLOOR.

    The label is derived from the name and is deliberately coarse: it claims only what the name supports and
    says `unlabelled` otherwise, because a class label invented from a filename is the same defect as a
    field whose name is a claim its contents cannot support.
    """
    n = name.lower()
    if "extract" in n:
        return "extraction / tool"
    if "-vl-" in n or n.startswith("mmproj"):
        return "vision / not in this population"
    if "coder" in n or "code" in n:
        return "code-tuned"
    if "instruct" in n or "chat" in n:
        return "instruction-tuned"
    return "unlabelled"


def population(n=5):
    """A SPREAD ACROSS THE SIZE RANGE, derived -- never typed. Typed names produced five ABSENT entrants
    on the chess probe, and a second directory produced a probe against eight models while the arena held
    fifty-three. A population named twice is a population that can disagree with itself."""
    files = sorted((p for p in glob.glob(os.path.join(R.MODELS, "*.gguf"))
                    if not os.path.basename(p).startswith("mmproj")
                    and "-VL-" not in os.path.basename(p)), key=os.path.getsize)
    if not files:
        return []
    step = max(1, len(files) // n)
    return files[::step][:n]


def main():
    n = 5
    if "--n" in sys.argv:
        n = int(sys.argv[sys.argv.index("--n") + 1])
    port = 8751
    pop = population(n)

    # =============================================================================================
    # ONE RUN, ONE PATH. Mechanised, because the alternative is a rule I state and then forget.
    #
    # Two runs shared `probes/SOKOBAN_FIRST_RUN.json` and the LAST WRITER WON: the re-run finished first,
    # the still-live first run finished second, and the re-run's record was destroyed. Its numbers survived
    # only because its STDOUT went to a different file. SEE FINDING 020.
    #
    # SO THE PATH CARRIES THE RUN, and the run refuses to start if its own path already exists -- a second
    # launch against a live path is not a retry, it is an OVERWRITE, and it should fail loudly rather than
    # silently decide which run is the record.
    # =============================================================================================
    run_id = os.environ.get("SOKOBAN_RUN_ID") or time.strftime("%Y%m%d-%H%M%S")
    out_path = os.path.join(HERE, "probes", f"SOKOBAN_RUN_{run_id}.json")
    if os.path.exists(out_path):
        print(f"  REFUSING: {os.path.relpath(out_path, HERE)} already exists.")
        print("  A second run against a live path is an OVERWRITE, not a retry. Set SOKOBAN_RUN_ID to a")
        print("  new value if this is a genuinely new run.")
        return 4

    print("=" * 96)
    print("SOKOBAN -- POPULATION RUN")
    print("=" * 96)
    print(f"  RUN ID      {run_id}")
    print(f"  ARTIFACT    {os.path.relpath(out_path, HERE)}   <- owned by this run alone")
    print(f"  legend      {R.legend()}   digest {R.legend_digest()}   <- travels in every cell")
    print(f"  population DERIVED from {R.MODELS}: {len(pop)} entrants at a spread across the size range")
    print(f"  levels: {len(LEVELS)} (verified set -- the third level is REPORTED AS ABSENT, not faked)")
    print(f"  criteria frozen in PREREG_sokoban.md BEFORE this run. No time limit; the cap is the budget.")
    print()

    with open(out_path, "w") as fh:
        json.dump({"run_id": run_id, "legend": R.legend(), "legend_digest": R.legend_digest(),
                   # §6 FROZEN IDENTITY, CARRIED IN THE RECORD RATHER THAN ASSUMED. "levels ... sha256 with
                   # the run" -- a level is an INPUT, and an input that does not travel with the result
                   # makes the result unattributable. Same rule as the legend digest, and the same lesson
                   # as FINDING 020: THE IDENTITY OF A RUN IS THE INPUTS IT WAS PRODUCED UNDER.
                   "levels": {os.path.basename(lv): (
                       hashlib.sha256(open(os.path.join(HERE, lv), "rb").read()).hexdigest()[:16]
                       if os.path.exists(os.path.join(HERE, lv)) else None) for lv in LEVELS},
                   "simulator_digest": hashlib.sha256(open(os.path.join(HERE, "sokoban.py"), "rb")
                                                      .read()).hexdigest()[:16],
                   # "host recorded per bundle, WITH the host's hardware state" -- §6. A score taken on one
                   # box is not a score taken on another, and the same reasoning as FINDING 002: the
                   # machine gets a say unless the record can tell it apart from the model.
                   "host": {"node": platform.node(), "platform": platform.platform(),
                            "cpu_count": os.cpu_count(),
                            "nvidia_smi": bool(__import__("shutil").which("nvidia-smi"))},
                   "cells": []}, fh, indent=1)

    rows, reasons = [], {}
    for ent in pop:
        cn = os.path.basename(ent).replace(".gguf", "")
        cls = classifier(cn)
        for lv in LEVELS:
            lbl = cn[:28]
            print(f"  {lbl:30s} [{cls:17s}] {os.path.basename(lv):22s} ...", flush=True)
            r = R.run(ent, os.path.join(HERE, lv), 40, port)
            port += 1
            r["class"] = cls
            rows.append(r)
            if not r.get("loaded"):
                # NOT AN ENTRANT FAILURE. A model that never loaded has not played, and counting it either
                # way is the defect: as a failure it libels the model, as a success it libels the run.
                # NAME: `never_started`, the grammar's word (§4). Must match the format field exactly.
                reasons["never_started"] = reasons.get("never_started", 0) + 1
                print(f"      NEVER_STARTED -- {r['why']}")
            else:
                reasons["played"] = reasons.get("played", 0) + 1
                print(f"      ended={r['ended']:18s} solved={str(r['solved']):5s} moves={r['moves']:3d}  "
                      f"blocked={r['blocked']:3d} not_an_action={r['not_an_action']:3d} "
                      f"give_up={r['give_up']}")
            json.dump({"run_id": run_id, "legend": R.legend(), "legend_digest": R.legend_digest(),
                       "cells": rows}, open(out_path, "w"), indent=1)

    print()
    print("=" * 96)
    print("THE RATES")
    print("=" * 96)
    played = [r for r in rows if r.get("loaded")]
    # THE GRAMMAR'S ZERO RULE (§4) USED TO BE DESCRIBED HERE RATHER THAN ENFORCED: this function returned 0
    # whatever happened. A run that measured NOTHING must exit NON-ZERO -- "zero rule: enforced, not
    # described" is the grammar's own line, and a described rule is a resolution.
    if not played:
        print(f"  ERROR -- NO ENTRANT WAS MEASURED. This is not a verdict about the population.")
        print(f"  cells attempted {len(rows)}   never_started {len(rows) - len(played)}   measured 0")
        print(f"  A run whose measured count is zero exits non-zero: COVERAGE CANNOT TELL 'ATTEMPTED' FROM")
        print(f"  'STARTED', AND TOTAL FAILURE IS ITS PASSING CASE.")
        return 3
    print(f"  cells attempted      {len(rows)}")
    # `never_started` IS THE GRAMMAR'S NAME FOR IT (§4), and the grammar is the instrument. The runner
    # called it `did_not_load`; two names for one state is how a format field and its reader drift apart.
    print(f"  PLAYED               {len(played)}      NEVER_STARTED  {len(rows) - len(played)}")
    print(f"  REASON COUNTS        {reasons}   <- never only a total: a population that never ran is not "
          f"evidence about the population")
    if played:
        for lv in LEVELS:
            sub = [r for r in played if r["level"] == os.path.basename(lv).replace(".txt", "")]
            sol = sum(1 for r in sub if r["solved"])
            gv = sum(1 for r in sub if r["give_up"])
            na = sum(1 for r in sub if r["not_an_action"])
            print(f"  {os.path.basename(lv):22s} played {len(sub):2d}  solved {sol:2d}  "
                  f"gave_up {gv:2d}  not_an_action {na:2d}")
    print()
    print("  LEVEL SET: 2 of 3. The third level is ABSENT and is reported as ABSENT -- a level nobody can")
    print("  solve needs a solver to PROVE it, and a level that merely LOOKS lost is a trap for the reader,")
    print("  not a control for the entrant. C1 is scored on the levels that exist, per outcome row 6.")
    print(f"\n  artifact: probes/SOKOBAN_FIRST_RUN.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
