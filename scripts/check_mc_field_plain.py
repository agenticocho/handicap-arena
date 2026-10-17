#!/usr/bin/env python3
"""CHECK THE FIELD RE-TAKE -- every number MC_FIELD_PLAIN.md quotes, re-derived from the records and the files.

WHY THIS EXISTS, AND WHAT IT IS NOT. The field's numbers are read from the 22 coordinates after the run, so
"the arm is plain" and "the replacement is recorded" are CLAIMS until something re-derives them from the files
that are on disk NOW -- including the digest of the declaration, the driver and the simulator, which are read
from disk rather than compared against a copy carried in the record. It re-derives each cell's score, counts
and every screen with the FROZEN SIMULATOR (`missile_command.play`), independently of what the record claims.

THE CHECKER'S OWN CONTROL: with a MUTATED action stream the same comparison must FAIL. A checker whose test
cannot fail is a checker that reports its own input back.

    scripts/run_guarded.sh mc-field-check <cabinet> /usr/bin/python3 scripts/check_mc_field_plain.py
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAB = os.path.dirname(HERE)
sys.path.insert(0, CAB)
import missile_command as S                                                     # noqa: E402
import missile_command_run as R                                                 # noqa: E402

ARCHIVE = os.path.join(CAB, "probes", "MC_FIELD_EXAMPLE_ARM_ARCHIVE_20261017.json")
POPULATION = os.path.join(CAB, "probes", "MC_POPULATION_20261017-184752.json")
PREREG = os.path.join(CAB, "PREREG_mc_field_plain.md")
LEVELS = ("mc_01_one_shot", "mc_02_scarcity")
PLAIN_DIGEST = "d8ee3da099c1a0c2"
EXAMPLE_DIGEST = "ec59f2dc5fd35518"

fails, checks = [], []


def ck(name, got, want):
    ok = got == want
    checks.append((name, ok, got, want))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        print(f"          got  {got!r}\n          want {want!r}")
        fails.append(name)
    return ok


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def d16(path):
    return sha_file(path)[:16]


def squash(s):
    return re.sub(r"\s+", " ", s or "").strip()


def coordinates_on_disk():
    out = []
    for name in sorted(os.listdir(os.path.join(CAB, "probes"))):
        if not (name.startswith("MC_") and name.endswith(".json")):
            continue
        if name.startswith("MC_POPULATION") or name.startswith("MC_LEGEND_AB") \
                or name.startswith("MC_FIELD_EXAMPLE_ARM_ARCHIVE") or name.startswith("MC_FIELD_PLAIN"):
            continue
        stem = name[:-len(".json")]
        if any(stem.endswith("_" + lv) for lv in LEVELS):
            out.append("probes/" + name)
    return out


def pre_registered_reason():
    """THE REASON STRING IS READ FROM THE PRE-REGISTRATION, not typed here -- a second copy of it in this file
    would be the one-definition defect applied to the very string that says what replaced what."""
    txt = open(PREREG, encoding="utf-8").read()
    for block in re.findall(r"```\n(.*?)```", txt, re.S):
        if "THE COORDINATE HELD AN example-ARM RECORD" in block:
            return squash(block)
    return None


def main():
    live = {"declaration": d16(os.path.join(CAB, "MC_DECLARATION.md")),
            "driver": d16(os.path.join(CAB, "missile_command_run.py")),
            "simulator": d16(os.path.join(CAB, "missile_command.py"))}
    print("=" * 100)
    print("CHECK -- THE FIELD RE-TAKE UNDER THE DECLARED ARM (card t_ec0b0420)")
    print("=" * 100)
    print(f"\n  declaration {live['declaration']}   driver {live['driver']}   simulator {live['simulator']}")
    print(f"  legend      {R.legend()}  digest {R.legend_digest()}  source {R.legend_source()}")

    art = json.load(open(ARCHIVE))
    pop = json.load(open(POPULATION))
    reason = pre_registered_reason()

    print("\n[1] THE FIELD IS THE SAME SET OF COORDINATES IT WAS ARCHIVED FROM")
    ck("the archive holds 22 cells over 11 entrants, as the pre-registration says",
       (len(art["cells"]), len({c["entrant"] for c in art["cells"]})), (22, 11))
    ck("...and every coordinate on disk is one of the archived cells (no cell added, none dropped)",
       sorted(coordinates_on_disk()), sorted(c["coordinate"] for c in art["cells"]))
    ck("...and the pre-registered reason is readable from PREREG_mc_field_plain.md", reason is not None, True)

    print("\n[2] EVERY ARCHIVED RECORD'S BYTES STILL HASH TO WHAT THE ARCHIVE SAYS THEY WERE")
    bad = [c["coordinate"] for c in art["cells"]
           if hashlib.sha256(c["text"].encode()).hexdigest() != c["sha256"]]
    ck("22/22 archived byte copies hash to their own stated digest", bad, [])
    pop_coords = {c["coordinate"]: c.get("coordinate_sha256") for c in pop["cells"] if c.get("coordinate")}
    xchk = [c["coordinate"] for c in art["cells"]
            if c["coordinate"] in pop_coords and pop_coords[c["coordinate"]] != c["sha256"]]
    ck("...and the 12 cells the POPULATION artifact also records agree with ITS digest of the same file "
       "(taken by another instrument, before this card)", xchk, [])
    ck("...over a cross-check of exactly 12 cells", len([c for c in art["cells"] if c["coordinate"] in pop_coords]), 12)

    print("\n[3] THE ARM, THE DECLARATION AND THE DRIVER, READ FROM THE FILES ON DISK")
    cells, rows = [], []
    for c in art["cells"]:
        p = os.path.join(CAB, c["coordinate"])
        d = json.load(open(p))
        proto = d.get("protocol") if isinstance(d.get("protocol"), dict) else {}
        ident = {"legend": d.get("legend"), "legend_digest": d.get("legend_digest"),
                 "declaration_digest": proto.get("declaration_digest"),
                 "driver_digest": d.get("driver_digest"), "simulator_digest": d.get("simulator_digest"),
                 "legend_source": d.get("legend_source")}
        cells.append((c, d, ident))

    def ids(field):
        return sorted({i[field] for _, _, i in cells})
    ck("every record names the arm the declaration declares", ids("legend"), ["plain"])
    ck("...by the digest the driver computes for it", ids("legend_digest"), [PLAIN_DIGEST])
    ck("...and none of them names the arm of record before the move", EXAMPLE_DIGEST in ids("legend_digest"), False)
    ck("...every record carries the declaration digest OF THE FILE ON DISK", ids("declaration_digest"),
       [live["declaration"]])
    ck("...and the DRIVER digest of the driver that is on disk -- the gap F2 closed", ids("driver_digest"),
       [live["driver"]])
    ck("...and the simulator digest of the frozen simulator", ids("simulator_digest"), [live["simulator"]])
    ck("...read from the declaration rather than named on the command line",
       ids("legend_source"), [f"the recorded default ({R.legend()})"])

    # THE ENTRANT IS THE SUBJECT OF THE MEASUREMENT, so its digest is re-read from the model FILE in this
    # process. THIS CHECK WAS ADDED AFTER THE RUN, when the field's own digests were compared with the
    # pre-move records' -- it is a control ADDED in response to a measurement, not a criterion moved, and
    # nothing above or below was re-scored on account of it.
    models = os.environ.get("ARENA_MODELS") or os.path.expanduser("~/moltbook_pipeline/models")
    drift, ent_bad, measured_n = [], [], 0
    for c, d, _ in cells:
        if not d.get("loaded"):
            continue
        measured_n += 1
        p = os.path.join(models, c["entrant"] + ".gguf")
        now = d16(p) if os.path.exists(p) else None
        if d.get("entrant_digest") != now:
            ent_bad.append((c["entrant"], d.get("entrant_digest"), now))
        if json.loads(c["text"]).get("entrant_digest") != now:
            drift.append(c["entrant"])
    ck("every measured record's entrant digest IS the digest of the model file on disk (a fresh read here)",
       ent_bad, [])
    print(f"  MEASURED, AND IT IS A FINDING ABOUT THE PRE-MOVE RECORDS RATHER THAN ABOUT THIS FIELD: "
          f"{len(drift)} of {measured_n} entrant files hash differently NOW than the PRE-MOVE records say "
          f"they did -- {sorted(drift)}")

    print("\n[4] THE REPLACEMENT IS RECORDED, AGAINST THE PRE-REGISTERED REASON")
    miss = [c["coordinate"] for c, d, _ in cells if not d.get("artifact_replaced")]
    ck("every one of the 22 records carries artifact_replaced", miss, [])
    mismatch = [(c["coordinate"], d["artifact_replaced"]["sha256"]) for c, d, _ in cells
                if d.get("artifact_replaced", {}).get("sha256") != c["sha256"]]
    ck("...and its digest is the digest of the record this one replaced, from the ARCHIVE", mismatch, [])
    byt = [c["coordinate"] for c, d, _ in cells
           if d.get("artifact_replaced", {}).get("bytes") != c["bytes"]]
    ck("...and the byte count too", byt, [])
    rsn = [c["coordinate"] for c, d, _ in cells
           if squash(d.get("artifact_replaced", {}).get("reason_given")) != reason]
    ck("...and every reason is the string the pre-registration fixed BEFORE the run", rsn, [])
    named = [(c["coordinate"], d["artifact_replaced"]["it_named"]["legend_digest"]) for c, d, _ in cells
             if d["artifact_replaced"]["it_named"]["legend_digest"]
             != json.loads(c["text"]).get("legend_digest")]
    ck("...and each replacement says what the REPLACED RECORD ITSELF claimed about its arm (the two ATTEMPTS "
       "claimed none)", named, [])
    ck("...and the two that claimed no arm are exactly the two archived ATTEMPTS",
       sorted(c["coordinate"] for c in art["cells"] if json.loads(c["text"]).get("legend_digest") is None),
       sorted(c["coordinate"] for c in art["cells"] if not json.loads(c["text"]).get("loaded")))

    print("\n[5] THE MEASUREMENT, RE-DERIVED FROM (state_text, tokens) -- NOT READ FROM THE RECORD")
    for c, d, _ in cells:
        if not d.get("loaded"):
            rows.append({"entrant": c["entrant"], "level": c["level"], "loaded": False,
                         "why": (d.get("why") or "").splitlines()[0][:60]})
            continue
        r = S.play(d["state_text"], d["tokens"])
        ck(f"{c['entrant']} {c['level']}: the score recomputes", r["cities_surviving"], d["score"])
        ck(f"{c['entrant']} {c['level']}: the counters recompute", r["counts"], d["counts"])
        ck(f"{c['entrant']} {c['level']}: one outcome per token, every threat DESTROYED, HIT or SPARED "
           f"(`fired` is the simulator's own outcome for a threat killed by an interceptor)",
           (len(r["trace"]), r["counts"]["fired"] + r["counts"]["hit"] + r["counts"]["spared"]),
           (len(d["tokens"]), len(S.parse_state(d["state_text"])["threats"])))
        ck(f"{c['entrant']} {c['level']}: sufficiency re-derived", bool(d["sufficiency"]["screens_reproduce"]), True)
        rows.append({"entrant": c["entrant"], "level": c["level"], "loaded": True, "score": d["score"],
                     "cities_total": d["cities_total"], "tokens": d["tokens"], "counts": d["counts"],
                     "ended": d["ended"],
                     "budget": d["budget_signature"]["reading"][:50]})

    print("\n[6] THE CHECKER'S OWN CONTROL -- THE COMPARISON ABOVE CAN FAIL")
    worse = []
    for c, d, _ in cells:
        if not d.get("loaded"):
            continue
        r = S.play(d["state_text"], d["tokens"][:-1] or ["RESIGN"])
        if (r["cities_surviving"], r["counts"]) == (d["score"], d["counts"]):
            worse.append((c["entrant"], c["level"]))
    ck("a MUTATED action stream does NOT reproduce the record's score and counters (22 cells)", worse, [])

    print("\n[7] THE REPLICATION CONTROL -- THE CELLS THE POPULATION RUN ALREADY MEASURED UNDER `plain`")
    pcells = {(c["entrant"], c["level"]): c for c in pop["cells"] if c["arm"] == "plain"}
    rep, same = [], []
    for c, d, _ in cells:
        k = (c["entrant"], c["level"])
        if k in pcells and d.get("loaded"):
            ok = pcells[k]["tokens"] == d["tokens"]
            rep.append({"entrant": k[0], "level": k[1], "tokens_now": d["tokens"],
                        "tokens_then": pcells[k]["tokens"], "reproduced_token_for_token": ok})
            same.append((k, ok))
    ck("over 12 cells the tokens reproduce TOKEN-FOR-TOKEN (P2)", [s for s, ok in same if not ok], [])
    ck("...over exactly 12 cells", len(same), 12)
    for r in rep:
        if not r["reproduced_token_for_token"]:
            print(f"        {r['entrant']} {r['level']}: now {r['tokens_now']}  then {r['tokens_then']}")

    print("\n[8] THE FIELD AGAINST THE ARCHIVED ARM -- REPORTED, NOT SCORED (no criterion is read here)")
    ex, chg, tok_same, ceil = {}, [], 0, 0
    for c, d, _ in cells:
        was = json.loads(c["text"])
        if not (d.get("loaded") and was.get("loaded")):
            continue
        a = S.play(was["state_text"], was["tokens"])
        b = S.play(d["state_text"], d["tokens"])
        ex[c["coordinate"]] = a
        if a["counts"] != b["counts"]:
            chg.append((c["entrant"], c["level"]))
        if was["tokens"] == d["tokens"]:
            tok_same += 1
        if (was.get("budget_signature") or {}).get("all_turns_capped") or \
                (d.get("budget_signature") or {}).get("all_turns_capped"):
            ceil += 1
    print(f"  the same cell, one arm apart: tokens IDENTICAL in {tok_same} of {len(ex)} paired cells; "
          f"the simulator's counters differ in {len(chg)}")
    for e, lv in chg:
        k = [kk for kk in ex if kk.startswith("probes/MC_" + e) and lv in kk][0]
        a = ex[k]
        d = [dd for c, dd, _ in cells if c["coordinate"] == k][0]
        print(f"        {e} {lv}: example (fired {a['counts']['fired']} unknown {a['counts']['unknown']} "
              f"score {a['cities_surviving']}) -> plain (fired {d['counts']['fired']} "
              f"unknown {d['counts']['unknown']} score {d['score']})")
    for arm, pick in (("example (archived)", lambda c: json.loads(c["text"])),
                      ("plain   (this run)", None)):
        tot = {x: 0 for x in ("fired", "passed", "unknown", "out_of_range", "malformed", "late", "no_ammo")}
        scores = []
        for c, d, _ in cells:
            r = pick(c) if pick else d
            if not r.get("loaded"):
                continue
            p = S.play(r["state_text"], r["tokens"])
            for x in tot:
                tot[x] += p["counts"][x]
            scores.append(p["cities_surviving"])
        print(f"  ARM {arm}   cells {len(scores)}   scores {scores}")
        print(f"      " + "  ".join(f"{x} {v}" for x, v in tot.items()))
    print(f"  CEILING CAVEAT: {ceil} of {len(ex)} paired cells had EVERY turn cut at the ceiling in at "
          f"least one arm -- part of any movement is the ceiling moving, not the arm.")
    print("  AND THE TWO ARMS' RECORDS ARE SEPARATED BY MORE THAN THE ARM: the archived records were taken "
          "under an earlier driver digest, an earlier declaration digest, and -- MEASURED above -- against "
          "readings of entrant files that are not reproducible. The comparison is reported; it is not a "
          "criterion and no criterion is read from it.")

    print("\n" + "-" * 100)
    print("THE FIELD, CELL BY CELL")
    print("-" * 100)
    for r in rows:
        if not r["loaded"]:
            print(f"  {r['entrant'][:44]:44s} {r['level']:14s} ATTEMPT -- {r['why']}")
            continue
        ct = r["counts"]
        print(f"  {r['entrant'][:44]:44s} {r['level']:14s} {r['score']}/{r['cities_total']}  "
              f"fired {ct['fired']} passed {ct['passed']} unknown {ct['unknown']} oor {ct['out_of_range']} "
              f"malformed {ct['malformed']} late {ct['late']} no_ammo {ct['no_ammo']}  "
              f"| {r['tokens']}  [{r['ended']}]")

    loaded = [r for r in rows if r["loaded"]]
    tot = {k: sum(r["counts"][k] for r in loaded) for k in
           ("fired", "passed", "unknown", "out_of_range", "malformed", "late", "no_ammo")}
    for lv in LEVELS:
        s = [r for r in loaded if r["level"] == lv]
        print(f"\n  {lv:14s} measured {len(s)}  scores {[r['score'] for r in s]}")
    print(f"\n  ARM TOTALS over {len(loaded)} measured cells: " + "  ".join(f"{k} {v}" for k, v in tot.items()))
    print(f"  attempts {len(rows) - len(loaded)}  measured {len(loaded)}  planned {len(rows)}")

    print("\n" + "=" * 100)
    print(f"{'ALL CHECKS PASS' if not fails else str(len(fails)) + ' CHECKS FAILED'}   --  "
          f"{len(checks) - len(fails)}/{len(checks)}")
    print("=" * 100)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
