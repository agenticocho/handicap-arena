#!/usr/bin/env python3
"""PROBE -- the A/B artifact's `reading` string: a RECORD of the day it was written, or a LIVE CAPTION the
next run republishes? Model-free: no model, no lease, and no write into the tree (the two artifact fixtures
this probe builds go to a temporary directory under TMPDIR and are deleted on exit).

The subject is ONE SENTENCE inside the `reading` value `missile_command_legend_ab.py` writes into
`probes/MC_LEGEND_AB.json` (`029244b6e5232a6b`): the sentence that asserted, in the present tense, that
`example` WAS STILL the arm of record. `MC_DECLARATION.md` (`2ada03ee2ad1f60b`) has named
`legend_arm plain` since 2026-10-17, so that sentence was TRUE of the day the A/B ran (the artifact was
written 2026-10-17 11:31:43 -0700; the key moved later the same day, after the population run
`MC_POPULATION_20261017-184752`) and FALSE of the live script, which would REPUBLISH it on the next run.

  READING 1  THE TWO COPIES SIDE BY SIDE. The published artifact's `reading` (a RECORD, which the card's
             bounds forbid moving) and the `reading` the LIVE script would publish today, built by running the
             script's own `main()` with the driver's `run()` STUBBED -- no model, no lease, every number zero
             by construction. What is read here is the STRING, which is not a function of the stub.
  READING 2  THE FIELD THE LIVE SCRIPT WOULD PUBLISH, AND WHETHER IT TRACKS THE DECLARATION. Five checks on
             the constructed string (the stale claim gone, the source named, the driver's own reading carried,
             the true selectability claim KEPT), plus THE NON-RECURRENCE CHECK: with the driver's default
             patched in memory to the OTHER arm, the constructed `reading` must follow it. A "fix" that swaps
             the literal `example` for the literal `plain` passes the first check and fails this one -- which
             is the whole reason this card is not a tidy-up.
             ROUND 2 (the Chair's comment 71) adds four more, because two claims in the SAME FIELD were
             asserted rather than measured. F7 reads the digest clause against the cells the script actually
             CONSTRUCTED: a cell that did not load is written by `cell_summary` (:69-71) with NO
             `legend_digest`, and the branch cascade treats that state as expected, so an unqualified "every
             cell carries the digest" is FALSE in a reachable run state. F8 reads that the field NAMES the
             declaration's arm at all -- F3 passes on a `legend_source()` that names no arm, which is exactly
             what it returns inside the run's arm loop -- and F8b/F8c are F8's non-vacuity control and the
             instant check that the field is built with no arm selected.
  READING 3  THE STALE SENTENCE'S CARRIERS. Every tracked file that contains the phrase is listed. After the
             edit the only carriers may be the PUBLISHED RECORD and PRE-REGISTRATIONS (which record what was
             true when written); a live script among them is the defect. **The needle is assembled from
             fragments below so that this instrument is not itself a carrier of the sentence it searches for.**
  READING 4  NOTHING ELSE MOVES. The script's only write is its own artifact (an AST reading, not the
             sentence's own promise); the declaration and the driver agree; no record moved in git; the
             published artifact's sha256 re-computed in full; every frozen input re-read.

Exit 0 only if every check passes; 3 otherwise. `scripts/run_guarded.sh` is the only way this runs.
"""
import ast
import contextlib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import missile_command_legend_ab as A                                           # noqa: E402
import missile_command_run as R                                                 # noqa: E402

MODULE = os.path.join(HERE, "missile_command_legend_ab.py")
PUB_REL = os.path.join("probes", "MC_LEGEND_AB.json")
PUB = os.path.join(HERE, PUB_REL)
PUB_DIGEST = "029244b6e5232a6b77e67cf5e21dea342c7da336a932386b3a16015e96b286c8"

# THE NEEDLE, ASSEMBLED FROM FRAGMENTS ON PURPOSE: an instrument that contains the sentence it hunts is a
# carrier of the defect it is measuring (and the carrier sweep below would find its own source).
STALE = "remains the " + "recorded instrument"

# THE DIGEST CLAUSE, IN ITS TWO FORMS (round 2, the Chair's comment 71 correction 1). A cell that did not load
# is written by `cell_summary` (:69-71) as `{"arm","state","loaded","why","load_failure_class"}` -- NO
# `legend_digest` -- and the branch cascade treats that state as a documented outcome ("NO VERDICT -- one arm
# did not load"). So the unqualified form is FALSE of a reachable run, and it was in the field a run publishes.
# The probe reads WHICH form the live text carries and measures it against the cells the script constructs.
DIGEST_Q = "every cell that loaded carries the digest of the arm it was taken under"
DIGEST_U = "every cell carries the digest of the arm it was taken under"

# THE RECORD'S OWN WORDS, PINNED. This is the `reading` the published artifact carries; it is pinned here so
# that a reader can see the edit did not reach into the record, and so that a MOVED record fails a check rather
# than passing one. The first two sentences are the ones the edit must NOT touch (R5). The third is assembled
# around the needle for the same reason the needle is: THIS FILE IS NOT A CARRIER.
PUB_PREFIX = ("The prediction and its three branches are in the pre-registration; the branch above is "
              "selected BY THE COUNTERS, not by a preference. Scope: ONE entrant, TWO states, n=1 per "
              "cell -- a demonstration, not a field.")
PUB_READING = (PUB_PREFIX + " The DECLARED ARM DOES NOT MOVE: `example` " + STALE + ", "
                             "and changing it is a separate act with its own reason.")

# THE FROZEN INPUTS `PREREG_mc_ab_reading.md` §4 fixes. Checked, not quoted: this probe recomputes them.
# The module under test (`missile_command_legend_ab.py`) is deliberately NOT here -- it is the drift. Nor is
# `PREREG_mc_ab_reading.md`, which gains a landing note after the governed runs.
FROZEN = {
    "missile_command.py": "eb5ed36591b300e6",
    "missile_command_run.py": "3bd43eed4c6e41f3",
    "PREREG_missile_command.md": "01548e9a866df03e",
    "levels/mc_01_one_shot.txt": "ab101ca955c1c853",
    "levels/mc_02_scarcity.txt": "327d2157bd0b8a83",
    "MC_DECLARATION.md": "2ada03ee2ad1f60b",
    "scripts/run_guarded.sh": "5e34e455b5193e89",
    "PREREG_mc_population.md": "cfedf8b7f5e7d57f",
    "PREREG_mc_legend_ab.md": "49784e02849a401f",
    "PREREG_mc_ab_arm_keys.md": "47db6b9368bae18c",
    "PREREG_mc_ab_arm_names.md": "3f670a15e8e9cb4e",
    "probes/MC_LEGEND_AB.json": "029244b6e5232a6b",
}

# WHERE THE PHRASE IS ALLOWED TO SURVIVE, each with its reason. Anything else that carries it is a live copy.
EXPECTED_CARRIERS = {
    "probes/MC_LEGEND_AB.json": "the PUBLISHED RECORD -- it was true of 2026-10-17 11:31:43 and it stays",
    "PREREG_mc_ab_arm_names.md": "a PRE-REGISTRATION (card t_a74fee86) -- records what was true when written",
    "PREREG_mc_ab_reading.md": "THIS card's pre-registration -- it quotes the sentence it is about",
}

CHECKS = []


def ck(name, want, got):
    ok = want == got
    CHECKS.append((name, ok, want, got))
    print(f"  CHECK  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        print(f"         want {want!r}\n         got  {got!r}")
    return ok


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@contextlib.contextmanager
def patched(**patches):
    """The driver's attributes substituted AT TEST TIME, restored in `finally`. Nothing on disk is touched."""
    saved = {k: getattr(R, k) for k in patches}
    try:
        for k, v in patches.items():
            setattr(R, k, v)
        yield
    finally:
        for k, v in saved.items():
            setattr(R, k, v)


@contextlib.contextmanager
def legend_source_watch(sink):
    """Record `(R.LEGEND_ARM, the returned string)` at EVERY instant `legend_source()` is called while the
    artifact is built, and return the driver's own answer unchanged. Restored in `finally`.

    WHY THIS IS A CHECK AND NOT A COMMENT (round 2, the Chair's comment 71 correction 2): `legend_source()`
    returns "selected at call time (--legend or MC_LEGEND)" -- naming NO arm -- whenever `R.LEGEND_ARM` is
    set, and the run clears it only at :184, AFTER the arm loop. A refactor that built the artifact inside that
    loop would publish a field with no arm of record while every check that only asked "does the string
    contain legend_source()?" still passed. This reads the instant instead of trusting the line order."""
    real = R.legend_source

    def watched():
        at_call = R.LEGEND_ARM
        out = real()
        sink.append((at_call, out))
        return out

    R.legend_source = watched
    try:
        yield sink
    finally:
        R.legend_source = real


def cell_digest_counts(cells):
    """-> (cells, loaded, carrying a `legend_digest`, not-loaded but carrying a `load_failure_class`).
    The second and third counts are what the digest clause's SCOPE is measured against; the fourth is what a
    not-loaded cell carries INSTEAD of a digest (`cell_summary`, :69-71)."""
    loaded = [c for c in cells if c.get("loaded")]
    return (len(cells), len(loaded), sum(1 for c in cells if c.get("legend_digest")),
            sum(1 for c in cells if not c.get("loaded") and c.get("load_failure_class")))


def stub_run(*_a, **_k):
    """NO MODEL IS LOADED. `run()` never reaches a server, so no lease is taken and no token is generated;
    every cell below is a not-loaded row and every number in the artifact is zero BY CONSTRUCTION. The
    `reading` string is NOT a function of the cells -- it is built from prose and from the driver's own
    reading of the declaration -- which is why it can be read out of a stubbed run at all."""
    return {"loaded": False, "why": "STUBBED BY THE PROBE -- no model, no lease",
            "load_failure_class": "PROBE_STUB"}


def stub_main(out_path):
    """The script's own `main()`, with `run()` stubbed and OUT redirected to a scratch path. -> rc, artifact.
    `argv` is set as a run would set it, so the argument path is the real one."""
    saved_run, saved_out, saved_argv = R.run, A.OUT, sys.argv[:]
    try:
        R.run = stub_run
        A.OUT = out_path
        sys.argv = ["probe-ab-reading", "--entrant", A.ENTRANT]
        rc = A.main()
    finally:
        R.run = saved_run
        A.OUT = saved_out
        sys.argv = saved_argv
    art = json.load(open(out_path, encoding="utf-8")) if os.path.exists(out_path) else None
    return rc, art


def carriers(needle):
    """Every TRACKED file containing `needle`, with the files too large to read named rather than skipped
    silently. `git ls-files` is the domain: untracked scratch (logs/, __pycache__) is not part of the record."""
    raw = subprocess.run(["git", "-C", HERE, "ls-files", "-z"], capture_output=True).stdout.split(b"\0")
    hits, skipped = [], []
    for entry in raw:
        if not entry:
            continue
        rel = entry.decode()
        path = os.path.join(HERE, rel)
        try:
            if os.path.getsize(path) > 8_000_000:
                skipped.append(rel)
                continue
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if needle in text:
            hits.append(rel)
    return sorted(hits), sorted(skipped)


def write_sites(source):
    """THE SCRIPT'S ONLY WRITE, read from its OWN SOURCE (AST) rather than from the sentence that promises it.
    -> (opens with a write mode, other mutating calls, makedirs targets, json.dump targets)

    TWO DEFECTS THIS FUNCTION HAD IN ITS FIRST VERSION, NAMED HERE BECAUSE THEY ARE THE CLASS THIS CABINET
    KEEPS CATCHING: (a) an `open()` with NO mode argument was counted as a WRITE -- it is a READ (`open(p,
    encoding="utf-8")` at :176), so the check failed on a file whose only write is its artifact; (b) every
    call named `replace` was counted as `os.replace`, and `str.replace` is not a write at all (:179, :210).
    A checker that cannot read its own subject is the empty-room defect aimed at a checker."""
    tree = ast.parse(source)
    w_opens, mutators, makedirs, dumps = [], [], [], []
    os_attr_mutators = ("remove", "unlink", "replace", "rename", "rmtree", "truncate", "chmod", "symlink")
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        owner = getattr(getattr(fn, "value", None), "id", None)
        attr = getattr(fn, "attr", None)
        bare = getattr(fn, "id", None)
        if bare == "open":
            mode = "r"                          # NO mode argument IS a read, not a write
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                mode = node.args[1].value
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value
            if isinstance(mode, str) and any(c in mode for c in "wax+"):
                w_opens.append((node.lineno, mode, ast.unparse(node.args[0]) if node.args else ""))
        elif owner in ("os", "shutil") and attr in os_attr_mutators + ("write_text", "write_bytes"):
            mutators.append((node.lineno, f"{owner}.{attr}", ast.unparse(node)))
        elif owner == "os" and attr == "makedirs":
            makedirs.append(ast.unparse(node.args[0]) if node.args else ast.unparse(node))
        elif owner == "json" and attr == "dump":
            dumps.append(ast.unparse(node.args[1]) if len(node.args) > 1 else "")
    return w_opens, mutators, makedirs, dumps


def main():
    print(f"PROBE ab-reading -- the A/B's `reading` string: does the LIVE script still assert the arm of record?")
    print(f"  taken      {time.strftime('%Y-%m-%dT%H:%M:%S%z')}")
    print("=" * 106)
    pub = json.load(open(PUB, encoding="utf-8"))
    src = open(MODULE, encoding="utf-8").read()
    if not PUB_READING.startswith(PUB_PREFIX):
        raise SystemExit("PROBE DEFECT: PUB_PREFIX is not a prefix of PUB_READING -- fix the probe, not the code")
    print(f"  instrument  {os.path.relpath(MODULE, HERE)}  digest {sha256_file(MODULE)[:16]}")
    print(f"  published   {PUB_REL}  sha256 RE-COMPUTED here: {sha256_file(PUB)}")
    print(f"  driver      arms {tuple(R.LEGEND_ARMS)}  LEGEND_DEFAULT {R.LEGEND_DEFAULT!r}  "
          f"declaration legend_arm {R.DECL.get('legend_arm')!r}")
    print(f"              legend_source() -> {R.legend_source()!r}   digests {R.legend_arm_digests()}")
    scratch = tempfile.mkdtemp(prefix="mc-ab-reading-")

    # ---------------------------------------------------------------- READING 1: the two copies
    print("\nREADING 1  THE TWO COPIES -- the published RECORD, and the `reading` the LIVE script would publish")
    out1 = os.path.join(scratch, "ab_live.json")
    watch = []
    with legend_source_watch(watch):
        rc1, art1 = stub_main(out1)
    if art1 is None:
        raise SystemExit(f"PROBE DEFECT: main() produced no artifact at {out1} (rc {rc1})")
    live = art1["reading"]
    print(f"  main() rc {rc1}  artifact built at {os.path.relpath(out1, HERE)}  (run() STUBBED: no model, no lease)")
    print(f"\n  PUBLISHED (the record, 2026-10-17 11:31:43 -0700)\n    {pub['reading']}\n")
    print(f"  LIVE SCRIPT would publish TODAY\n    {live}\n")
    print(f"  THE LIVE COPY IS THE PUBLISHED COPY: {live == pub['reading']}"
          + ("   <-- the record and the caption are the same sentence, which is the defect" if live == pub["reading"]
             else "   <-- they differ: the live text has already moved away from the record"))
    ck("R1  the published artifact's sha256 is the one the card quotes", PUB_DIGEST, sha256_file(PUB))
    ck("R2  the published artifact's `reading` is the record's own words, unchanged", PUB_READING, pub["reading"])

    # ---------------------------------------------------------------- READING 2: the live field
    print("\nREADING 2  THE FIELD THE LIVE SCRIPT WOULD PUBLISH -- nine checks, and whether it TRACKS the "
          "declaration")
    other = next(a for a in R.LEGEND_ARMS if a != R.LEGEND_DEFAULT)
    out2 = os.path.join(scratch, "ab_patched.json")
    with patched(LEGEND_DEFAULT=other):
        patched_source = R.legend_source()
        rc2, art2 = stub_main(out2)
    if art2 is None:
        raise SystemExit(f"PROBE DEFECT: the patched-default run produced no artifact at {out2} (rc {rc2})")
    patched_reading = art2["reading"]
    print(f"  the driver's own reading of the declaration, AS ON DISK: {R.legend_source()!r}")
    print(f"  and with the driver's default patched IN MEMORY to {other!r}: {patched_source!r}")
    print(f"  the two constructed readings are the same string: {live == patched_reading}"
          + ("   <-- the text does NOT follow the declaration" if live == patched_reading else
             "   <-- the text follows the declaration"))
    ck("F1  the live `reading` no longer asserts that `example` is the arm of record", True, STALE not in live)
    ck("F2  and it NAMES the file the arm of record is read from", True, "MC_DECLARATION.md" in live)
    ck("F3  and it carries the driver's own reading of that key at the instant of the run",
       True, R.legend_source() in live)
    ck("F4  NON-RECURRENCE: with the default patched to the other arm the constructed `reading` follows it "
       "(a swapped literal would not)", True,
       bool(live != patched_reading and patched_source in patched_reading
            and f"({other})" not in patched_reading.replace(patched_source, "")))
    ck("F5  and the TRUE claim is KEPT: both arms stay selectable at the driver's call time",
       True, all(tok in live for tok in ("--legend", "MC_LEGEND", "example")))

    # ---------------------------------------------------------------- ROUND 2: the two clauses this field
    # ASSERTED and did not MEASURE (the Chair's comment 71, corrections 1 and 2). Both sit inside the SAME
    # sentence, and neither is a new defect class: both are "a caption that will lie on the next run".
    print("\n  -- CORRECTION 1: the digest clause is measured against the cells this run CONSTRUCTED")
    c_cells, c_loaded, c_with, c_fail = cell_digest_counts(art1["cells"])
    p_cells, p_loaded, p_with, _p_fail = cell_digest_counts(pub["cells"])
    print(f"      constructed {c_cells} cell(s): {c_loaded} loaded, {c_with} carrying a legend_digest, "
          f"{c_fail} not-loaded carrying a load_failure_class   (run() STUBBED: this is the NO-VERDICT state)")
    print(f"      published   {p_cells} cell(s): {p_loaded} loaded, {p_with} carrying a legend_digest")
    ck("F7  the digest clause is SCOPED and TRUE: it claims a digest only of the cells that LOADED, and that "
       "claim is measured true of the constructed cells (none carried one) and of the published record's (all "
       "did) -- the UNQUALIFIED form, which the field carried, would be FALSE of the constructed cells",
       {"qualified form present": True, "unqualified form present": False,
        "cells loaded in the constructed run (stubbed: 0)": 0,
        "unqualified claim would be true of the constructed cells": False,
        "qualified claim true of the constructed cells": True,
        "qualified claim true of the published record's cells": True,
        "published cells carry a digest AND there is at least one (non-vacuity)": True,
        "constructed not-loaded cells all carry a load_failure_class": True},
       {"qualified form present": DIGEST_Q in live, "unqualified form present": DIGEST_U in live,
        "cells loaded in the constructed run (stubbed: 0)": c_loaded,
        "unqualified claim would be true of the constructed cells": c_with == c_cells,
        "qualified claim true of the constructed cells": c_with == c_loaded,
        "qualified claim true of the published record's cells": p_with == p_loaded,
        "published cells carry a digest AND there is at least one (non-vacuity)": p_with == p_cells and p_with > 0,
        "constructed not-loaded cells all carry a load_failure_class": c_fail == c_cells - c_loaded})

    print("\n  -- CORRECTION 2: the field NAMES the arm of record, and the instant it is built from")
    print(f"      the declaration's arm {R.DECL.get('legend_arm')!r};  legend_source() calls while the "
          f"artifact was built: {watch}")
    ck("F8  the constructed `reading` NAMES the declaration's arm -- F4's shape read the OTHER way (F4 asks "
       "whether the text FOLLOWS the driver; this asks whether an arm is named at all)",
       True, R.DECL["legend_arm"] in live)
    with patched(LEGEND_ARM=R.DECL["legend_arm"]):
        in_loop = R.legend_source()
    print(f"      CONTROL -- with R.LEGEND_ARM set (the state the run's own arm loop is in) the driver's "
          f"reading is {in_loop!r}: it names NO arm of {tuple(R.LEGEND_ARMS)}")
    ck("F8b AND F8 IS NOT VACUOUS: in the arm-loop state `legend_source()` names no arm at all, so an artifact "
       "built there would carry no arm of record and F8 would fail -- the check is not passing by accident",
       (False, False), (any(a in in_loop for a in R.LEGEND_ARMS), R.DECL["legend_arm"] in in_loop))
    ck("F8c AND THE FIELD IS BUILT WITH NO ARM SELECTED: R.LEGEND_ARM was None at EVERY instant the reading "
       "was taken (an instrument that read the line order instead would not know)",
       (True, True), (len(watch) > 0, all(arm is None for arm, _s in watch)))

    # ---------------------------------------------------------------- READING 3: the carriers
    print("\nREADING 3  THE STALE SENTENCE'S CARRIERS -- every tracked file that contains the phrase")
    hits, skipped = carriers(STALE)
    for rel in hits:
        print(f"      {rel:<38} {EXPECTED_CARRIERS.get(rel, '*** NOT ACCOUNTED FOR ***')}")
    print(f"      {len(hits)} carrier(s); files too large to read: {skipped}")
    ck("F6  the stale sentence survives ONLY where a record or a pre-registration keeps it -- "
       "nowhere in a live script", sorted(EXPECTED_CARRIERS), hits)

    # ---------------------------------------------------------------- READING 4: nothing else moves
    print("\nREADING 4  NOTHING ELSE MOVES -- the script's only write, the state, the record, the inputs")
    w_opens, mutators, makedirs, dumps = write_sites(src)
    print(f"  write-mode open() call sites   {w_opens}")
    print(f"  other mutating calls           {mutators}")
    print(f"  os.makedirs                    {makedirs}")
    print(f"  json.dump targets              {dumps}")
    ck("R3  the A/B's only write is its own artifact -- read from its SOURCE, not from its sentence",
       ([("w", "OUT")], [], ["os.path.dirname(OUT)"], ["open(OUT, 'w')"]),
       ([(mode, target) for (_ln, mode, target) in w_opens], mutators, makedirs, dumps))
    print(f"      the one write sits at source line(s) {[ln for ln, _m, _t in w_opens]}")
    synth = 'import json\njson.dump({}, open("MC_DECLARATION.md", "a"), indent=1)\n'
    sw, sm, sd, sdp = write_sites(synth)
    print(f"  the detector's own control (a SYNTHETIC source that writes the declaration): {sw} {sd} {sdp}")
    synth_ok = bool(len(sw) == 1 and sw[0][1] == "a" and "MC_DECLARATION.md" in sw[0][2]
                    and sd == [] and sdp == ["open('MC_DECLARATION.md', 'a')"])
    ck("R3b AND THE DETECTOR IS NOT VACUOUS: a write to another path IS reported, and its open() is not a read",
       True, synth_ok)
    state = {"declaration_and_driver_agree": R.DECL.get("legend_arm") == R.LEGEND_DEFAULT,
             "default_is_an_arm": R.LEGEND_DEFAULT in R.LEGEND_ARMS,
             "two_arms": len(R.LEGEND_ARMS)}
    ck("R4  the reachable state: the declaration's key IS the driver's default, and it is an arm",
       {"declaration_and_driver_agree": True, "default_is_an_arm": True, "two_arms": 2}, state)
    ck("R5  the edit did not reach the first two sentences -- they are still the published words",
       PUB_PREFIX, live[:len(PUB_PREFIX)])
    pub_keys = sorted(set(pub) - {"artifact_replaced"})
    art_keys = sorted(set(art1) - {"artifact_replaced"})
    print(f"  published fields {pub_keys}\n  constructed      {art_keys}")
    print("  (artifact_replaced excluded: it is written only by a REPLACING run, and this fixture writes to a "
          "fresh path -- the published artifact's own replacement is part of the record)")
    ck("R8  the field set the script publishes is the published field set (minus the replacement marker)",
       pub_keys, art_keys)
    stable = {k: art1[k] for k in art1
              if k not in ("reading", "cells", "totals", "branch", "entrant_digest", "artifact_replaced")}
    print("  FINGERPRINT of every field that is neither the reading nor a function of the stub "
          "(reading, cells, totals, branch) nor the box's unreproducible entrant digest:")
    print(f"      sha256[:16] = {hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()[:16]}"
          "   <- IDENTICAL before and after the edit is the claim; both logs carry it")
    st = subprocess.run(["git", "-C", HERE, "status", "--porcelain", "--", "probes/", "results/"],
                        capture_output=True, text=True)
    dirty = [ln for ln in st.stdout.splitlines() if ln.strip()]
    print(f"  git status --porcelain probes/ results/  ->  {len(dirty)} line(s)"
          + ("" if not dirty else "\n" + "\n".join("    " + ln for ln in dirty)))
    ck("R6  no record moved", 0, len(dirty))
    moved = {k: (v, sha256_file(os.path.join(HERE, k))[:16]) for k, v in FROZEN.items()
             if sha256_file(os.path.join(HERE, k))[:16] != v}
    print(f"  frozen inputs: {len(FROZEN)} re-read, {len(moved)} moved"
          + ("" if not moved else f": {moved}"))
    ck("R7  every frozen input is unchanged", {}, moved)

    shutil.rmtree(scratch, ignore_errors=True)
    bad = [n for n, ok, *_ in CHECKS if not ok]
    print("\n" + "=" * 106)
    print(f"  {len(CHECKS) - len(bad)}/{len(CHECKS)} checks PASS"
          + ("" if not bad else "\n  FAILED: " + "; ".join(bad)))
    print(f"  VERDICT {'PASS' if not bad else 'FAIL'}  (rc {0 if not bad else 3})")
    print(f"  PROBE EXIT rc={0 if not bad else 3}")
    return 0 if not bad else 3


if __name__ == "__main__":
    sys.exit(main())
