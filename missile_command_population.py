#!/usr/bin/env python3
"""MISSILE COMMAND -- THE POPULATION RUN, AND THE LEGEND ARM AT POPULATION SCALE.

BUILT TO `PREREG_mc_population.md`, which was committed BEFORE this file ran. It imports
`missile_command_run` and reuses its `run()`, `artifact_gate()`, `artifact_path()`, `carried_identity()`
and `binary_guard()` -- so the prompt that is sent, the digest that is recorded, the arm that is used and
the path that is refused have ONE definition (RULING 79's shape, applied to the driver).

WHAT IT DOES, IN THE ORDER THE PRE-REGISTRATION GIVES IT:

  1  DERIVES the population from $ARENA_MODELS -- every *.gguf, the exclusion list applied as a
     case-insensitive SUBSTRING with the reason recorded per file, size-sorted, step-sampled. No entrant
     is named anywhere in this file.
  2  RUNS the arm `MC_DECLARATION.md` NAMES (not an arm this file names) into the PUBLISHED coordinate
     `probes/MC_<entrant>_<level>.json` -- one run, one path -- and ADOPTS a coordinate that already holds
     a record taken under THIS run's own identity, rather than overwriting it or re-running it.
  3  RUNS the other arm (the one that is not of record) whose cells have no coordinate and travel inside the
     run artifact, which is the shape `missile_command_legend_ab.py` used and for the same reason.
  4  COMPUTES the frozen gate (coverage / yield / never_started), C1-C3 as the pre-registration defines
     them, the two per-cell controls, the C3 comparison line re-derived at run time, and the replication
     control against the A/B's own record of the same cell.

    scripts/run_guarded.sh mc-population <cabinet dir> /usr/bin/python3 missile_command_population.py --n 6
    python3 missile_command_population.py --dry-run          # the population and the lines, no model
"""
import argparse
import glob
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import missile_command_run as R                                               # noqa: E402

PREREG = os.path.join(HERE, "PREREG_mc_population.md")
LEVELS = ("levels/mc_01_one_shot.txt", "levels/mc_02_scarcity.txt")
# THE RECORDED ARM OCCUPIES THE PUBLISHED COORDINATE. The comparison arm has no coordinate and travels in
# the run artifact -- the A/B's shape, and for its reason: a second arm at the same path destroys the first.
# THE ARMS THE DRIVER DEFINES ARE READ FROM THE DRIVER. A second copy of the arms' own names is the same
# defect as a second copy of WHICH arm is of record, one layer down.
ARMS = tuple(R.LEGEND_ARMS)
# THE COORDINATE ARM IS THE DECLARATION'S, READ THROUGH THE DRIVER'S OWN READ (`R.LEGEND_DEFAULT` is
# `MC_DECLARATION.md`'s `legend_arm`, and the driver refuses at import if that key is missing). It is NOT a
# module constant and NOT defaulted to a literal, and neither of those is a style preference:
#   * a constant here was a SECOND COPY of a decision the declaration owns, and it went stale -- pinned at
#     `example` after the declaration's key moved to `plain` (2ada03ee2ad1f60b, DECISION_mc_legend_arm.md);
#   * measured, not argued (scripts/probe_coord_arm_adoption.py re-takes both arms over the 22 published
#     coordinates): with the pin at `example`, EVERY ONE of the 22 holds a record whose `legend_digest`
#     disagrees with `run_identity()`, so a re-run records `never_started` -- "the published coordinate holds
#     a record taken under a DIFFERENT instrument" -- where the adoption rule exists precisely to ADOPT it;
#   * hard-coding `plain` would be the same defect with a fresher value: stale again the day the declaration
#     moves, and stale silently.
COORD_ARM = R.LEGEND_DEFAULT
if COORD_ARM not in ARMS:
    raise SystemExit(f"REFUSED: the declaration names legend_arm {COORD_ARM!r}; this runner's arms are {ARMS}.")
if len(ARMS) < 2:
    raise SystemExit(f"REFUSED: the driver defines {len(ARMS)} legend arm(s) {ARMS}; this runner needs an arm "
                     f"of record and one comparison arm, and it will not invent the second.")
# THE COMPARISON ARM IS DERIVED TOO -- "whichever arm is not of record", not a literal `plain` that goes
# stale the day the declaration names the other one.
COMPARISON_ARM = next(a for a in ARMS if a != COORD_ARM)
# THE PUBLISHED A/B. `arm_effect` (in `verdict_inputs`, below) reports the comparison `PREREG_mc_population.md`
# fixed BEFORE the population ran -- "THE PREDICTION FOR THE ARM, AND ITS BRANCHES": the arm carrying the
# worked example against the arm without it. THAT COMPARISON IS PUBLISHED, in
# `probes/MC_POPULATION_20261017-184752.json` (`verdict_inputs.arm_effect`; sha256
# 9335b2a39b4d1d389b78b4a88a82f576020387bf7ed3ed21b7c2158899d54156), whose OWN `arms` block records the two
# names of the day (`recorded` `example`, `comparison` `plain`). These two constants are therefore NOT a
# second copy of the declaration's decision -- the declaration decides WHICH arm is of record, and this
# block does not read it -- and NOT a second copy of `ARMS` either: they are the two arms the comparison was
# published between. A key is right here only while the driver still defines it as an arm, so the refusal
# below is what keeps the keys from outliving the names they name.
AB_EXAMPLE_ARM, AB_PLAIN_ARM = "example", "plain"
_ab_missing = [a for a in (AB_EXAMPLE_ARM, AB_PLAIN_ARM) if a not in ARMS]
if _ab_missing:
    raise SystemExit(
        f"REFUSED: `arm_effect` reports the A/B comparison PUBLISHED in "
        f"probes/MC_POPULATION_20261017-184752.json (9335b2a39b4d1d38) between the arms {AB_EXAMPLE_ARM!r} "
        f"and {AB_PLAIN_ARM!r}; the driver defines {ARMS}. Those keys are the names of arms that no longer "
        f"exist, and the block would report zeros under a name it does not contain. RE-PUBLISH the "
        f"comparison as a NEW artifact with a NEW digest; do not re-key this block to the declaration.")
# run_card.py's EXCLUDE_PAT, verbatim -- the resolution `PREREG_missile_command.md` names -- applied as a
# case-insensitive SUBSTRING (see the pre-registration: as a PREFIX test, five PROJECTORS enter the field).
EXCLUDE_PAT = ("qwen-image", "audio", "mmproj", "clip", "vae", "embed", "whisper")
EXCLUDE_MODALITY = ("-vl-",)
DEFAULT_N = 6
PREREG_LINE_VALUE = 2                 # the value the pre-registration fixed before the run: 2 of 4
AB_ARTIFACT = os.path.join(HERE, "probes", "MC_LEGEND_AB.json")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------------- the population
def population(n):
    """-> (entrants, removed, excluded_files). DERIVED, NEVER TYPED. Every removal carries its reason."""
    every = sorted(glob.glob(os.path.join(R.MODELS, "*.gguf")))
    kept, removed = [], []
    for p in every:
        low = os.path.basename(p).lower()
        why = next((f"EXCLUDE_PAT {k!r}" for k in EXCLUDE_PAT if k in low), None) \
            or next((f"modality {k!r}" for k in EXCLUDE_MODALITY if k in low), None)
        (removed if why else kept).append((p, why))
    kept.sort(key=lambda t: os.path.getsize(t[0]))
    step = max(1, len(kept) // n) if kept else 1
    return kept[::step][:n], removed, kept, step


# --------------------------------------------------------------------------------- the C3 line
def spend_everything_line(state_text):
    """THE PRE-REGISTERED COMPARISON LINE, AS A RULE -- burned at the earliest-landing threat, using the
    lowest-numbered silo with ammo that can reach it, BLIND to whether the impact is a city or empty
    ground. Computed by the FROZEN simulator, never by a second copy of the rules."""
    st = R.S.parse_state(state_text)
    ammo = {k: v["ammo"] for k, v in st["silos"].items()}
    live = dict(st["threats"])
    toks, tick = [], st["tick"]
    for _ in range(12):
        cand = sorted((t for t, v in live.items() if v["tick"] > tick), key=lambda t: (live[t]["tick"], t))
        pick = None
        for t in cand:
            for s in sorted(ammo):
                if ammo[s] > 0 and abs(st["silos"][s]["at"] - live[t]["impact"]) <= 4:
                    pick = (s, t)
                    break
            if pick:
                break
        if pick is None:
            toks.append("PASS")
        else:
            toks.append(pick[0] + pick[1])
            ammo[pick[0]] -= 1
            live.pop(pick[1], None)
        tick += 1
        if not live:
            break
    return toks


# --------------------------------------------------------------------------------- one cell's row
COUNTER_KEYS = ("fired", "passed", "no_ammo", "out_of_range", "unknown", "malformed", "late", "hit",
                "spared")
PER_TOKEN_COUNTERS = ("fired", "passed", "no_ammo", "out_of_range", "unknown", "malformed", "late")


def cell_controls(row):
    """THE TWO EQUALITIES, PER CELL, IN THE RECORD: every token produces exactly one outcome, and every
    threat is destroyed, hit or spared. A summary that drops a counter fails these instead of reading low."""
    c, toks, n_threats = row["counts"], row["tokens"], row["threats_total"]
    return {"tokens": len(toks),
            "per_token_outcomes": sum(c[k] for k in PER_TOKEN_COUNTERS),
            "every_token_has_exactly_one_outcome": sum(c[k] for k in PER_TOKEN_COUNTERS) == len(toks),
            "threats_in_the_state": n_threats,
            "destroyed_plus_hit_plus_spared": c["fired"] + c["hit"] + c["spared"],
            "every_threat_is_accounted_for": c["fired"] + c["hit"] + c["spared"] == n_threats}


def summary(rec, arm, level, status, entrant_path, **extra):
    """ONE ROW PER CELL. EVERY COUNTER TRAVELS -- a summary that drops one cannot tell a zero from a
    missing row (the A/B's own lesson)."""
    row = {"arm": arm, "level": level, "status": status, "entrant": rec["entrant"],
           "entrant_digest": rec.get("entrant_digest"), "loaded": rec.get("loaded"),
           "legend_digest": rec.get("legend_digest"),
           "server_binary_digest": (rec.get("server_binary_digest")
                                    or (rec.get("config") or {}).get("server_binary_digest")),
           "state_digest": rec.get("state_digest")}
    if rec.get("loaded"):
        c = rec["counts"]
        row.update({"tokens": rec["tokens"], "score": rec["score"], "cities_total": rec["cities_total"],
                    "counts": dict(c),
                    "threats_total": len(R.S.parse_state(rec["state_text"])["threats"]),
                    "silos_that_exist": sorted(R.S.parse_state(rec["state_text"])["silos"]),
                    "silo_digits_in_the_tokens": sorted({t[0] for t in rec["tokens"] if len(t) == 2}),
                    "ended": rec.get("ended"), "missing_values": rec.get("missing_values"),
                    "budget_signature": rec.get("budget_signature"),
                    "sufficiency": rec.get("sufficiency"),
                    "turns": rec.get("turns"),
                    "config": {k: (rec.get("config") or {}).get(k)
                               for k in ("reasoning", "fit_argv", "command_cap", "max_tokens_ceiling",
                                         "server_argv", "legend", "legend_source")},
                    "protocol": {"declaration_digest": (rec.get("protocol") or {}).get("declaration_digest"),
                                 "clock_audit": (rec.get("protocol") or {}).get("clock_audit")}})
        row["controls"] = cell_controls(row)
    else:
        row.update({"why": rec.get("why"), "load_failure_class": rec.get("load_failure_class")})
    row.update(extra)
    return row


def coordinates_row(entrant, state_path):
    """THE PUBLISHED COORDINATE, and a row for a cell that is kept IN the run artifact instead."""
    return R.artifact_path(entrant, state_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=DEFAULT_N)
    ap.add_argument("--port", type=int, default=8763)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--overwrite-artifact", dest="reason", default=None, metavar="REASON")
    a = ap.parse_args()

    if not os.path.exists(PREREG):
        print("  REFUSED: PREREG_mc_population.md is missing -- a population run without its "
              "pre-registration is a result with no prediction to be right or wrong about.")
        return 2

    pop, removed, kept, step = population(a.n)
    lines = {lv: spend_everything_line(open(R.resolve_state(lv), encoding="utf-8").read())
             for lv in LEVELS}

    if a.dry_run:
        print(f"  PREREG      {os.path.relpath(PREREG, HERE)}  digest {R.file_digest(PREREG)}")
        print(f"  ARENA_MODELS {R.MODELS}   *.gguf kept {len(kept)}  removed {len(removed)}"
              f"   n={a.n} step={step} -> {len(pop)} entrants")
        for p, why in sorted(removed, key=lambda t: os.path.getsize(t[0])):
            print(f"    removed {os.path.getsize(p)/1e9:8.3f} GB  {os.path.basename(p):58s} <- {why}")
        for p, _ in pop:
            print(f"    entrant {os.path.getsize(p)/1e9:8.3f} GB  {os.path.basename(p)}")
        print(f"  ARMS        {ARMS}   coordinate arm {COORD_ARM}   (READ from "
              f"{os.path.basename(R.DECLARATION_FILE)} `legend_arm`, declaration digest "
              f"{R.file_digest(R.DECLARATION_FILE)}; comparison arm {COMPARISON_ARM})   "
              f"legend digests {R.legend_arm_digests()}")
        print(f"  BINARY      {R.llama_server()}  digest {R.server_binary_digest()}")
        print(f"  THE FORK    {R.FORK_LLAMA}  (ternary entrants are routed to it by binary_guard's rule)")
        for lv in LEVELS:
            text = open(R.resolve_state(lv), encoding="utf-8").read()
            st = R.S.parse_state(text)
            r = R.S.play(text, lines[lv])
            print(f"  LINE  {os.path.basename(lv):22s} cap {R.clock_cap(text):2d}  "
                  f"spend-on-everything {lines[lv]} -> {r['cities_surviving']}/{len(st['cities'])}")
        print(f"  passive (PASS every tick) on mc_02 -> "
              f"{R.S.play(open(R.resolve_state('levels/mc_02_scarcity.txt'), encoding='utf-8').read(), ['PASS'] * 6)['cities_surviving']}/4")
        return 0

    # ONE RUN, ONE PATH -- the run-level artifact carries the run id, and refuses a path that exists.
    run_id = os.environ.get("MC_RUN_ID") or time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    out = os.path.join(HERE, "probes", f"MC_POPULATION_{run_id}.json")
    ok, msg, replaced = R.artifact_gate(out, a.reason)
    if not ok:
        for line in msg.splitlines():
            print(f"  {line}")
        return 4
    os.makedirs(os.path.join(HERE, "probes"), exist_ok=True)

    cells, never_started = [], []
    meta = {
        "what": "THE POPULATION RUN -- the derived field, the recorded arm at the published coordinate, "
                "the declared comparison arm inside this artifact",
        "run_id": run_id,
        "prereg": os.path.relpath(PREREG, HERE), "prereg_digest": R.file_digest(PREREG),
        "population": {
            "rule": "ARENA_MODELS/*.gguf, EXCLUDE_PAT + -vl- as a case-insensitive SUBSTRING, size-sorted, "
                    "step = max(1, len//n) then files[::step][:n]",
            "arena_models": R.MODELS, "n": a.n, "step": step,
            "kept_files": len(kept), "removed_files": len(removed),
            "entrants": [{"file": os.path.basename(p), "bytes": os.path.getsize(p),
                          "digest": R.file_digest(p)} for p, _ in pop],
            "removed": [{"file": os.path.basename(p), "bytes": os.path.getsize(p), "reason": why}
                        for p, why in removed],
        },
        "levels": {os.path.basename(lv): {"digest": R.file_digest(os.path.join(HERE, lv)),
                                          "cap": R.clock_cap(open(R.resolve_state(lv), encoding="utf-8").read()),
                                          "spend_on_everything_line": lines[lv]}
                   for lv in LEVELS},
        "spend_on_everything_value_preregistered": PREREG_LINE_VALUE,
        "arms": {"recorded": COORD_ARM, "comparison": COMPARISON_ARM, "digests": R.legend_arm_digests(),
                 "arms_text": {a_: R.LEGEND_ARMS[a_] for a_ in ARMS}},
        "binary": R.binary_provenance(), "fork": R.FORK_LLAMA,
        "reader": R.reader_provenance(),
        "protocol": {"play_mode": "step_locked", "clock_audit": R.clock_audit(),
                     "reasoning": R.REASONING, "reasoning_argv": R.reasoning_argv(),
                     "fit_argv": R.fit_argv(), "max_tokens_ceiling": R.MAX_TOKENS,
                     "declaration_digest": R.file_digest(R.DECLARATION_FILE)},
        "host": {"node": __import__("platform").node(),
                 "platform": __import__("platform").platform(),
                 "cpu_count": os.cpu_count()},
    }

    def write():
        payload = dict(meta, cells=cells,
                       never_started=[{k: c[k] for k in ("entrant", "arm", "level", "status", "reason")
                                       if k in c} for c in never_started])
        payload.update(aggregate(cells, meta))
        json.dump(payload, open(out, "w"), indent=1)

    write()

    for entrant, _ in pop:
        if R.ternary_entrant(entrant):
            R.LLAMA_SELECTED = R.FORK_LLAMA          # binary_guard's own remedy, applied per entrant
        else:
            R.LLAMA_SELECTED = None
        ok, msg = R.binary_guard(entrant)
        if not ok:
            for arm in ARMS:
                for lv in LEVELS:
                    row = {"arm": arm, "level": os.path.basename(lv).replace(".txt", ""),
                           "entrant": os.path.basename(entrant).replace(".gguf", ""),
                           "status": "never_started", "reason": msg.splitlines()[0]}
                    cells.append(row)
                    never_started.append(row)
            print(f"  {os.path.basename(entrant):52s} NEVER STARTED -- {msg.splitlines()[0]}")
            write()
            continue

        for arm in ARMS:
            R.LEGEND_ARM = arm
            for lv in LEVELS:
                state_path = R.resolve_state(lv)
                sname = os.path.basename(state_path).replace(".txt", "")
                label = os.path.basename(entrant).replace(".gguf", "")
                coord = coordinates_row(entrant, state_path)
                cap = R.clock_cap(open(state_path, encoding="utf-8").read())
                t0 = time.time()
                if arm == COORD_ARM:
                    if os.path.exists(coord):
                        old = json.load(open(coord))
                        mine, theirs = R.run_identity(), R.carried_identity(old)
                        diff = [k for k in R.IDENTITY_IN_RECORD if theirs[k] != mine[k]]
                        if diff:
                            row = {"arm": arm, "level": sname, "entrant": label, "status": "never_started",
                                   "reason": (f"the published coordinate holds a record taken under a "
                                              f"DIFFERENT instrument: {diff}")}
                            cells.append(row)
                            never_started.append(row)
                            print(f"  {label[:46]:46s} {arm:7s} {sname:14s} NEVER STARTED -- coordinate held "
                                  f"by another instrument {diff}")
                            write()
                            continue
                        cells.append(summary(old, arm, sname, "adopted", entrant,
                                             coordinate=os.path.relpath(coord, HERE),
                                             coordinate_sha256=sha256_file(coord),
                                             coordinate_mtime=time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                                            time.gmtime(os.path.getmtime(coord))),
                                             adopted_note=("ADOPTED, NOT RE-RUN: this coordinate already "
                                                           "held a record taken under THIS run's own "
                                                           "identity, so the cell's measurement exists and a "
                                                           "second run would be a second record of the same "
                                                           "cell at a path that may hold only one.")))
                        c = cells[-1]
                        print(f"  {label[:46]:46s} {arm:7s} {sname:14s} ADOPTED  score {c['score']}/"
                              f"{c['cities_total']}  tokens {c['tokens']}")
                        write()
                        continue
                    gate_ok, gate_msg, rep = R.artifact_gate(coord, None)
                    if not gate_ok:
                        row = {"arm": arm, "level": sname, "entrant": label, "status": "never_started",
                               "reason": "the published coordinate is occupied and the gate refused"}
                        never_started.append(row)
                        print(f"  {label[:46]:46s} {arm:7s} {sname:14s} NEVER STARTED -- {gate_msg[:100]}")
                        write()
                        continue
                    rec = R.run(entrant, state_path, cap, a.port)
                    if rep is not None:
                        rec["artifact_replaced"] = rep
                    json.dump(rec, open(coord, "w"), indent=1)
                    cells.append(summary(rec, arm, sname, "started", entrant,
                                         coordinate=os.path.relpath(coord, HERE),
                                         coordinate_sha256=sha256_file(coord)))
                    c = cells[-1]
                else:
                    rec = R.run(entrant, state_path, cap, a.port)
                    cells.append(summary(rec, arm, sname, "started", entrant,
                                         coordinate=None,
                                         coordinate_note=("NO PUBLISHED COORDINATE: the published path "
                                                          f"probes/MC_{label}_{sname}.json holds the "
                                                          "RECORDED arm's cell, and one run is one path. "
                                                          "This cell travels inside this run artifact."),
                                         full_record=rec))
                    c = cells[-1]
                if c.get("loaded"):
                    print(f"  {c['entrant'][:46]:46s} {arm:7s} {sname:14s} score {c['score']}/"
                          f"{c['cities_total']}  fired {c['counts']['fired']} unknown "
                          f"{c['counts']['unknown']} tokens {c['tokens']}  ({time.time()-t0:.0f}s)")
                else:
                    print(f"  {c['entrant'][:46]:46s} {arm:7s} {sname:14s} DID NOT LOAD -- "
                          f"{c.get('load_failure_class')}")
                write()
    R.LEGEND_ARM = None

    payload = json.load(open(out))
    payload["replication_control"] = replication_control(cells)
    payload["verdict_inputs"] = verdict_inputs(cells, meta)
    json.dump(payload, open(out, "w"), indent=1)
    print_report(payload)
    return 0 if payload["verdict_inputs"]["measured"] else 1


# --------------------------------------------------------------------------------- aggregation
def _arm_cells(cells, arm):
    return [c for c in cells if c["arm"] == arm]


def _measured(cells):
    return [c for c in cells if c.get("loaded")]


def aggregate(cells, meta):
    """THE COUNTERS, PER ARM, AS THEY STAND -- written after EVERY cell so a crash keeps its progress."""
    out = {}
    for arm in ARMS:
        got = _arm_cells(cells, arm)
        out[arm] = {
            "cells": len(got),
            "measured": len(_measured(got)),
            "not_loaded": len([c for c in got if c.get("loaded") is False]),
            "adopted": len([c for c in got if c["status"] == "adopted"]),
            "score_total": sum(c.get("score") or 0 for c in _measured(got)),
            "cities_total_sum": sum(c.get("cities_total") or 0 for c in _measured(got)),
            "tokens_generated": sum(len(c.get("tokens") or []) for c in _measured(got)),
            **{k: sum((c.get("counts") or {}).get(k, 0) for c in _measured(got)) for k in COUNTER_KEYS},
        }
    return {"progress": {arm: {k: out[arm][k] for k in ("cells", "measured", "not_loaded", "adopted")}
                         for arm in ARMS}}


def verdict_inputs(cells, meta):
    """THE GATE, AND C1-C3, AS THE PRE-REGISTRATION DEFINES THEM. Every number is quoted with the set it
    was computed over, and the set is named in the key."""
    out = {}
    per_arm = {}
    for arm in ARMS:
        got = _arm_cells(cells, arm)
        planned = len(meta["population"]["entrants"]) * len(LEVELS)
        never = len([c for c in got if c["status"] == "never_started"])
        attempted = planned - never
        measured = len(_measured(got))
        mc01 = [c for c in _measured(got) if c["level"].startswith("mc_01")]
        mc02 = [c for c in _measured(got) if c["level"].startswith("mc_02")]
        scores02 = sorted({c["score"] for c in mc02})
        line = R.S.play(open(R.resolve_state("levels/mc_02_scarcity.txt"), encoding="utf-8").read(),
                        meta["levels"]["mc_02_scarcity.txt"]["spend_on_everything_line"])["cities_surviving"]
        per_arm[arm] = {
            "planned": planned, "never_started": never, "attempted": attempted, "measured": measured,
            "coverage": round(attempted / planned, 4) if planned else None,
            "yield": round(measured / attempted, 4) if attempted else None,
            "gate_met": bool(attempted and measured and attempted / planned >= 0.95
                             and measured / attempted >= 0.85),
            "zero_measured_is_an_error": measured == 0,
            "C1_floor_engaged_mc01": {
                "cells_measured_over": len(mc01),
                "cells_with_fired_ge_1": [c["entrant"] for c in mc01 if (c.get("counts") or {}).get("fired", 0) >= 1],
                "met": any((c.get("counts") or {}).get("fired", 0) >= 1 for c in mc01)},
            "C2_faculty_scores_spread_mc02": {
                "cells_measured_over": len(mc02),
                "scores": [c["score"] for c in mc02],
                "distinct_scores": scores02,
                "met": len(scores02) > 1},
            "C3_decoys_read_mc02": {
                "cells_measured_over": len(mc02),
                "comparison_line_value": line,
                "cells_above_the_line": [[c["entrant"], c["score"]] for c in mc02 if c["score"] > line],
                "met": any(c["score"] > line for c in mc02)},
            "controls_all_pass": all((c.get("controls") or {}).get("every_token_has_exactly_one_outcome")
                                     and (c.get("controls") or {}).get("every_threat_is_accounted_for")
                                     for c in _measured(got)),
        }
    out["per_arm"] = per_arm
    out["cells"] = len(cells)
    out["measured"] = len(_measured(cells))
    out["never_started"] = len([c for c in cells if c["status"] == "never_started"])
    # THE PUBLISHED A/B COMPARISON, KEYED BY THE NAMES IT WAS PUBLISHED UNDER -- not a reading of the
    # declaration, and not derived from COORD_ARM/COMPARISON_ARM. The direction below is a claim about WHAT
    # THE EXAMPLE DOES (`unknown` DOWN and `fired` UP once the example is removed), so it is keyed to which
    # arm carries the example. Deriving it positionally would invert the claim the day the declaration names
    # `example`: COMPARISON_ARM would then be `plain`, and "the comparison arm moved down" would read as
    # "the example arm moved down" -- the opposite of what this block publishes. See `AB_EXAMPLE_ARM`
    # above, where a rename of either arm is refused rather than reported as zeros.
    e = _arm_cells(cells, AB_EXAMPLE_ARM)
    p = _arm_cells(cells, AB_PLAIN_ARM)
    unk_e = sum((c.get("counts") or {}).get("unknown", 0) for c in _measured(e))
    unk_p = sum((c.get("counts") or {}).get("unknown", 0) for c in _measured(p))
    fir_e = sum((c.get("counts") or {}).get("fired", 0) for c in _measured(e))
    fir_p = sum((c.get("counts") or {}).get("fired", 0) for c in _measured(p))
    sc_e = sum(c.get("score") or 0 for c in _measured(e) if c["level"].startswith("mc_02"))
    sc_p = sum(c.get("score") or 0 for c in _measured(p) if c["level"].startswith("mc_02"))
    if not _measured(e) or not _measured(p):
        branch = ("NO BRANCH -- one arm has no measured cell, so there is nothing to compare. The cells "
                  "and their failure classes are in this artifact.")
    elif unk_p < unk_e and fir_p > fir_e:
        branch = ("BRANCH 1 -- THE EXAMPLE IS THE CARRIER, AT POPULATION SCALE: unknown DOWN and fired UP, "
                  "exactly as the pre-registration predicted.")
    elif unk_p == unk_e and fir_p == fir_e:
        branch = ("BRANCH 2 -- NOTHING MOVED: the A/B's explanation does not generalise, so the echo has "
                  "another cause.")
    else:
        branch = ("BRANCH 3 -- THE MOVEMENT IS NOT THE PREDICTED ONE, or the example is load-bearing for "
                  "format compliance. Read the tokens; the counters alone cannot say which.")
    out["arm_effect"] = {"unknown": {AB_EXAMPLE_ARM: unk_e, AB_PLAIN_ARM: unk_p},
                         "fired": {AB_EXAMPLE_ARM: fir_e, AB_PLAIN_ARM: fir_p},
                         "mc02_score_total": {AB_EXAMPLE_ARM: sc_e, AB_PLAIN_ARM: sc_p},
                         "branch": branch}
    out["spend_on_everything_value_preregistered"] = PREREG_LINE_VALUE
    out["spend_on_everything_value_rederived"] = per_arm[AB_EXAMPLE_ARM]["C3_decoys_read_mc02"]["comparison_line_value"]
    out["comparison_line_matches_the_preregistration"] = (
        per_arm[AB_EXAMPLE_ARM]["C3_decoys_read_mc02"]["comparison_line_value"] == PREREG_LINE_VALUE)
    return out


def replication_control(cells):
    """THE A/B MEASURED THIS CELL BEFORE. A re-run under the same instrument must reproduce it."""
    if not os.path.exists(AB_ARTIFACT):
        return {"available": False, "why": "probes/MC_LEGEND_AB.json is not present"}
    ab = json.load(open(AB_ARTIFACT))
    out = {"available": True, "artifact": os.path.relpath(AB_ARTIFACT, HERE),
           "artifact_digest": R.file_digest(AB_ARTIFACT), "cells": []}
    for c in cells:
        for old in ab.get("cells") or []:
            if (c["arm"] == old.get("arm") and c["level"] == old.get("state")
                    and c["entrant"] == ab.get("entrant") and c.get("loaded") and old.get("loaded")):
                same = (list(c.get("tokens") or []) == list(old.get("tokens") or [])
                        and c.get("score") == old.get("score"))
                out["cells"].append({"entrant": c["entrant"], "arm": c["arm"], "level": c["level"],
                                     "tokens_now": c.get("tokens"), "tokens_then": old.get("tokens"),
                                     "score_now": c.get("score"), "score_then": old.get("score"),
                                     "reproduced_token_for_token": same})
    out["all_reproduced"] = bool(out["cells"]) and all(c["reproduced_token_for_token"] for c in out["cells"])
    out["reading"] = ("A RE-RUN THAT DISAGREES WITH ITSELF IS THE FINDING: the same entrant, arm and state "
                      "under the same instrument must give the same tokens."
                      if out["cells"] else "no cell of this run overlaps the A/B's, so nothing to check")
    return out


def print_report(payload):
    vi = payload["verdict_inputs"]
    print("\n" + "=" * 100)
    print("POPULATION RUN -- THE FROZEN GATE, AND THE CRITERIA AS OPERATIONS")
    print("=" * 100)
    for arm in ARMS:
        p = vi["per_arm"][arm]
        print(f"\n  ARM {arm}   (recorded arm occupies the published coordinate)"
              if arm == COORD_ARM else f"\n  ARM {arm}   (comparison arm, carried in this artifact)")
        print(f"    gate        planned {p['planned']}  never_started {p['never_started']}  "
              f"attempted {p['attempted']}  measured {p['measured']}  "
              f"coverage {p['coverage']}  yield {p['yield']}  GATE {'MET' if p['gate_met'] else 'UNMET'}")
        print(f"    controls    every cell's controls pass: {p['controls_all_pass']}")
        print(f"    C1 floor    {p['C1_floor_engaged_mc01']}")
        print(f"    C2 spread   {p['C2_faculty_scores_spread_mc02']}")
        print(f"    C3 decoys   {p['C3_decoys_read_mc02']}")
    print(f"\n  ARM EFFECT  {vi['arm_effect']}")
    print(f"  C3 line     pre-registered {vi['spend_on_everything_value_preregistered']}  "
          f"re-derived {vi['spend_on_everything_value_rederived']}  "
          f"match {vi['comparison_line_matches_the_preregistration']}")
    print(f"  REPLICATION {payload.get('replication_control')}")
    print(f"  artifact    probes/MC_POPULATION_{payload['run_id']}.json")


if __name__ == "__main__":
    sys.exit(main())
