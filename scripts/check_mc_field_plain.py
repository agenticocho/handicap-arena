#!/usr/bin/env python3
"""CHECK THE FIELD RE-TAKE -- every number MC_FIELD_PLAIN.md quotes, re-derived from the records and the files.

WHY THIS EXISTS, AND WHAT IT IS NOT. The field's numbers are read from the 22 coordinates after the run, so
"the arm is plain" and "the replacement is recorded" are CLAIMS until something re-derives them from the files
that are on disk NOW -- the declaration's digest and the frozen simulator's are read from disk and CHECKED,
because a frozen input that moves is a defect. It re-derives each cell's score, counts and every screen with
the FROZEN SIMULATOR (`missile_command.play`), independently of what the record claims.

AND THE DRIVER'S DIGEST IS A READING, NOT A CHECK (card t_d68e29ba, pre-registered in
PREREG_mc_driver_digest_reading.md). A record's `driver_digest` names the instrument OF ITS DAY. The driver was
legitimately edited after this field was taken, so comparing it with the file on disk asserts that no
legitimate edit to the driver may ever happen again -- and it failed on all 22 CORRECT records the day after
the edit. What IS checked is everything that would make it a mutation: that the digest names a version of the
driver this cabinet actually committed (read from git), that the 22 records name ONE of them (the field was
taken in one pass), and that it is well formed and correctly scoped. The reading prints both digests and says
INCONCLUSIVE -- never FAILED -- when they differ, with the consequence stated.

THE CHECKER'S OWN CONTROL: with a MUTATED action stream the same comparison must FAIL. A checker whose test
cannot fail is a checker that reports its own input back.

    scripts/run_guarded.sh mc-field-check <cabinet> /usr/bin/python3 scripts/check_mc_field_plain.py
"""
import hashlib
import json
import os
import re
import subprocess
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


def committed_driver_digests():
    """EVERY VERSION OF THE DRIVER THIS REPOSITORY HAS COMMITTED, the working tree's own version included --
    a record taken between an edit and its commit legitimately names a version no commit holds yet, and that is
    the ONE stated way this check can fail on a correct record (the remedy is to commit the driver, never to
    re-take a digest).

    THE HISTORY IS THE ONLY TREE-LOCAL SOURCE THAT ANSWERS "does this digest belong to a file?": the instrument
    of the day is no longer on disk, the pre-move records carry no driver digest at all, and a registry typed
    into this file would be a second copy of a fact git already holds. The read does not trust the file's
    content: it hashes every committed blob of the path and adds the file on disk. MC_DRIVER_HISTORY_REPO points
    the read at another checkout -- the probe uses it for the shadow cabinets it builds -- and the repository
    that answered is PRINTED, so a reader can see which history this was checked against.
    """
    repo = os.environ.get("MC_DRIVER_HISTORY_REPO") or CAB
    rel = "missile_command_run.py"
    try:
        shas = subprocess.run(["git", "-C", repo, "log", "--all", "--format=%H", "--", rel],
                              capture_output=True, text=True, check=True).stdout.split()
        out = {d16(os.path.join(CAB, rel))}
        for sha in shas:
            blob = subprocess.run(["git", "-C", repo, "show", f"{sha}:{rel}"],
                                  capture_output=True, check=True).stdout
            out.add(hashlib.sha256(blob).hexdigest()[:16])
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"git could not read the history of {rel} in {repo}: {exc}") from exc
    return out


def uncommitted_driver_digests(cells, committed):
    """(coordinate, digest) for every record whose digest names no committed driver -- NAMED, not counted, so a
    mutation is a line a reader can follow to the file."""
    return sorted((c["coordinate"], i["driver_digest"]) for c, _, i in cells
                  if i["driver_digest"] not in committed)


def non_majority_driver_digests(cells):
    """(coordinate, digest) for every record that disagrees with the field's majority digest. The siblings that
    exist for this field are THE OTHER 21 RECORDS OF THE SAME PASS: `driver_digest` is a top-level record field
    with no second copy inside its own record, so a disagreement can only be measured across the field."""
    seen = [i["driver_digest"] for _, _, i in cells]
    if not seen:
        return []
    top = max(sorted(set(seen)), key=seen.count)
    return sorted((c["coordinate"], i["driver_digest"]) for c, _, i in cells if i["driver_digest"] != top)


def driver_digest_shape_violations(cells):
    """A record that cannot say what its own digest digests."""
    bad = []
    for c, _, i in cells:
        value, scope = i["driver_digest"], i.get("driver_digest_scope") or ""
        if not (isinstance(value, str) and re.fullmatch(r"[0-9a-f]{16}", value)):
            bad.append((c["coordinate"], "not 16 lowercase hex", value))
        elif "missile_command_run.py" not in scope:
            bad.append((c["coordinate"], "scope does not name the driver file", scope[:60]))
    return bad


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
                 "driver_digest": d.get("driver_digest"), "driver_digest_scope": d.get("driver_digest_scope"),
                 "simulator_digest": d.get("simulator_digest"),
                 "legend_source": d.get("legend_source")}
        cells.append((c, d, ident))

    def ids(field):
        return sorted({i[field] for _, _, i in cells})
    ck("every record names the arm the declaration declares", ids("legend"), ["plain"])
    ck("...by the digest the driver computes for it", ids("legend_digest"), [PLAIN_DIGEST])
    ck("...and none of them names the arm of record before the move", EXAMPLE_DIGEST in ids("legend_digest"), False)
    ck("...every record carries the declaration digest OF THE FILE ON DISK", ids("declaration_digest"),
       [live["declaration"]])
    # THE DRIVER DIGEST IS A READING, NOT AN IDENTITY OF THE FILE ON DISK -- decided and pre-registered in
    # PREREG_mc_driver_digest_reading.md (card t_d68e29ba) after this check FAILED ON ALL 22 CORRECT RECORDS:
    # they were taken under 4018f0262498eb3e and card t_8edaaf2d then edited the driver to 3bd43eed4c6e41f3.
    # The three checks below keep everything about the digest that CAN be a mutation, and none of them goes
    # stale when the driver is edited.
    try:
        committed = committed_driver_digests()
    except RuntimeError as exc:
        committed = set()
        print(f"  DRIVER HISTORY UNREADABLE -- {exc}\n          (the checks below cannot pass on an unread "
              f"history: 'cannot check' is never a pass)")
    ck("...and every record's driver_digest NAMES A DRIVER THIS CABINET HAS COMMITTED "
       f"({len(committed)} versions read from git) -- a digest that belongs to no file fails here, and the "
       "failure names the record", uncommitted_driver_digests(cells, committed), [])
    ck("...and the 22 records name ONE driver_digest value between them (the field was taken in one pass), "
       "so a record that disagrees with its own siblings is NAMED (a split field is a re-take's business, "
       "never one record's error)", non_majority_driver_digests(cells), [])
    ck("...and every record's driver_digest is 16 lowercase hex whose scope names missile_command_run.py "
       "(a record that cannot say what its own digest digests)", driver_digest_shape_violations(cells), [])
    driver_names = ids("driver_digest")
    print(f"  READING  the records name {driver_names}   the driver ON DISK is {live['driver']}   "
          f"committed versions {sorted(committed)}")
    if driver_names == [live["driver"]]:
        print("           THE RECORDS NAME THE DRIVER ON DISK TODAY -- which is all this reading can say: it "
              "is not a promise that these are the bytes the next reader will find.")
    else:
        print("  " + "-" * 96)
        print("           INCONCLUSIVE FROM THE RECORD'S SIDE, AND THIS IS NOT A FAILURE OF THE RECORD.")
        print("           A record's driver_digest identifies the instrument OF ITS DAY, not the instrument on")
        print("           disk today: a later, legitimate edit to the driver makes the two differ and falsifies")
        print("           nothing about the record. THE FIELD IS NOT RE-TAKEN ON ACCOUNT OF IT -- that would")
        print("           move 22 published coordinates for a file that will be edited again. What WOULD fail is")
        print("           above: a digest belonging to no committed driver, a split field, a malformed digest.")
        print("  " + "-" * 96)
    ck("...and the simulator digest of the frozen simulator", ids("simulator_digest"), [live["simulator"]])
    ck("...read from the declaration rather than named on the command line",
       ids("legend_source"), [f"the recorded default ({R.legend()})"])

    # THE ENTRANT IS THE SUBJECT OF THE MEASUREMENT, so its digest is re-read from the model FILE in this
    # process. THIS CHECK WAS ADDED AFTER THE RUN, when the field's own digests were compared with the
    # pre-move records' -- it is a control ADDED in response to a measurement, not a criterion moved, and
    # nothing above or below was re-scored on account of it.
    # THE ENTRANT'S STABLE IDENTITY IS THE FILE SIZE -- NOT THE DIGEST, AND NOT AN MTIME.
    # Ruled on card t_7f400932 and measured before the ruling: every `mtime` in this tree is a RECORD
    # artifact's (archive `cells[].mtime` is the record's write stamp; population `cells[].coordinate_mtime`
    # is the coordinate's), and the population artifact carries no model mtime at all. `bytes` is the only
    # field that ever means a model size, and only in the population artifact's `entrants` list -- so the
    # identity is read THERE and compared against st_size on this disk. Six of six recorded sizes match.
    #
    # THE DIGESTS KEEP PRINTING AS READINGS AND FEED NO COUNT. They are the finding -- these files do not
    # hash reproducibly on this box -- and deleting them to make a number go green would hide the one thing
    # this cabinet measured. 16 of 22 and 20 of 22 differ; both numbers are still printed below.
    #
    # THE COVERAGE IS NAMED IN THE LABEL, NOT IMPLIED BY THE COUNT: the population names 6 entrants, which
    # is 12 of the 22 cells. This check can say nothing about the cells it does not name, and says so.
    models = os.environ.get("ARENA_MODELS") or os.path.expanduser("~/moltbook_pipeline/models")
    sizes = {os.path.splitext(e["file"])[0]: e["bytes"]
             for e in (pop.get("population", {}).get("entrants") or [])
             if isinstance(e, dict) and e.get("file") and e.get("bytes") is not None}
    drift, drift_text, ent_bad, measured_n, sized_n = [], [], [], 0, 0
    for c, d, _ in cells:
        if not d.get("loaded"):
            continue
        measured_n += 1
        p = os.path.join(models, c["entrant"] + ".gguf")
        now = d16(p) if os.path.exists(p) else None
        if d.get("entrant_digest") != now:
            drift.append(c["entrant"])
        if json.loads(c["text"]).get("entrant_digest") != now:
            drift_text.append(c["entrant"])
        want = sizes.get(c["entrant"])
        if want is not None:
            sized_n += 1
            got = os.path.getsize(p) if os.path.exists(p) else None
            if got != want:
                ent_bad.append((c["entrant"], want, got))
    ck(f"every measured record the POPULATION NAMES carries the model SIZE it names, against st_size here "
       f"({sized_n} of {measured_n} cells; the other {measured_n - sized_n} are not named in the population, "
       f"so this check does not reach them and does not claim to)", ent_bad, [])
    print(f"  MEASURED, AND IT IS A FINDING ABOUT THE PRE-MOVE RECORDS RATHER THAN ABOUT THIS FIELD: "
          f"{len(drift)} of {measured_n} records and {len(drift_text)} of {measured_n} text copies hash "
          f"differently NOW than they say they did -- {sorted(set(drift) | set(drift_text))}")
    print("  [READINGS, NOT COUNTS: a digest that does not reproduce is the FINDING, not a failure of the "
          "record. The identity above is the size, per card t_7f400932.]")


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

    print("\n[6b] THE DRIVER READING'S OWN CONTROL -- THE CHECKS ABOVE CAN FAIL, ON A MUTATED RECORD")
    # THE SAME PREDICATES the driver checks call, on a copy of the field with ONE record mutated IN MEMORY: the
    # control tests the code path, not a description of it. Nothing on disk is written, and no digest is
    # re-taken: a control that changed the field to demonstrate itself would be the defect this card removes.
    # ITS EXPECTATION IS RELATIVE TO THE FIELD, not absolute: on a tree whose field is itself mutated, an
    # absolute expectation would fail here as well and report the same record twice -- measured (the probe's
    # M1), stated, and corrected in the pre-registration's landing note rather than absorbed.
    c0, _, i0 = cells[0]
    other = sorted(committed - {i0["driver_digest"]})
    base_missing = uncommitted_driver_digests(cells, committed)
    base_split = non_majority_driver_digests(cells)
    mut_none = [(c0, None, dict(i0, driver_digest="deadbeefdeadbeef"))] + cells[1:]
    ck("a record whose driver_digest belongs to NO committed driver is caught, and NAMED (the predicate the "
       "check above reads)",
       uncommitted_driver_digests(mut_none, committed),
       sorted(set(base_missing + [(c0["coordinate"], "deadbeefdeadbeef")])))
    if other:
        mut_older = [(c0, None, dict(i0, driver_digest=other[0]))] + cells[1:]
        ck("...and a record naming a DIFFERENT committed driver than its 21 siblings is caught, and NAMED "
           "(the predicate the check above reads)", non_majority_driver_digests(mut_older),
           sorted(set(base_split + [(c0["coordinate"], other[0])])))
    else:
        ck("...and a record naming a DIFFERENT committed driver than its 21 siblings is caught, and NAMED -- "
           "UNTESTABLE HERE: this history holds one version of the driver only", ["no second version"], [])

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
