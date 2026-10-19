#!/usr/bin/env python3
"""PROBE -- are the A/B's two arm names a READING of the driver, or the names the comparison was PUBLISHED
under? Model-free: no model, no lease, and no write into the tree (the one artifact this probe produces goes
to a temporary directory under TMPDIR and is deleted on exit).

The question is the one card `t_d21287e4` answered for `missile_command_population.py`'s `arm_effect`, asked
one layer further out about `missile_command_legend_ab.py` -- THE SCRIPT THAT PRODUCED
`probes/MC_LEGEND_AB.json` (`029244b6e5232a6b`), where the two names appear as literals at three sites (the
arm SET, and the two key sites its `totals` are built from).

  READING 1  REPLICATION. The script's own `arm_totals()`, over the PUBLISHED artifact's own four cells,
             must reproduce that artifact's `totals` -- every value, every key, and the key ORDER. This is
             the control that says the function the keys are handed to has not moved.
  READING 2  THE NAME IS WHAT THE ROW IS KEYED BY. Relabel every published cell `example`<->`plain` and
             recompute: if the rows are keyed by the arm NAMES, each name's row becomes the other's.
  READING 3  THE ARTIFACT'S OWN KEYS, from the script's own `main()`, with the driver's `run()` STUBBED to a
             not-loaded record. No model is loaded and no lease is taken, so the numbers are all zero and are
             NOT a measurement of anything -- what is read here is the KEY STRUCTURE of the artifact this
             script would publish, which is where the literals at the two key sites end up.
  READING 4  THE REAL EXPOSURE -- THE POSITIVE CONTROL. The driver's arms are RENAMED in memory and the
             published cells are relabeled to match (which is what a future run under renamed arms would
             produce). Three setups: 4a `plain` -> `terse`, 4b `example` -> `worked`, and 4c the pair moved
             in memory while the two key sites stay as they are (the future move that updates the arm SET and
             not the keys below it). A name that is no longer an arm must REFUSE; pre-edit it does not, and
             what it does instead is printed with its numbers. **These are the checks that FAIL before the
             fix and PASS after it.**
  READING 5  ONE COPY OF THE NAMES (shape, and its limit is stated). An AST over the live source counts every
             string constant that is EXACTLY a published arm name, and every one of them that does not sit on
             the `AB_*_ARM` assignment. The limit: an AST cannot see comments or prose, so this says nothing
             about captions -- only about the names written into code.
  READING 6  NOTHING MOVED. `git status --porcelain probes/ results/`, the published artifact's sha256
             re-computed in full, and every frozen input in `PREREG_mc_ab_arm_names.md` §4 re-read.

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

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import missile_command_legend_ab as A                                           # noqa: E402
import missile_command_run as R                                                 # noqa: E402

MODULE = os.path.join(HERE, "missile_command_legend_ab.py")
PUB_REL = os.path.join("probes", "MC_LEGEND_AB.json")
PUB = os.path.join(HERE, PUB_REL)
PUB_DIGEST = "029244b6e5232a6b77e67cf5e21dea342c7da336a932386b3a16015e96b286c8"

# THE FROZEN INPUTS `PREREG_mc_ab_arm_names.md` §4 fixes. Checked, not quoted: this probe recomputes them.
# The module under test (`missile_command_legend_ab.py`) is deliberately NOT here -- it is the drift.
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
    "probes/MC_LEGEND_AB.json": "029244b6e5232a6b",
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
    """The driver's attributes substituted AT TEST TIME, restored in `finally`. Nothing on disk is touched:
    the ONE value under test is the only difference between the reachable state and the fixture."""
    saved = {k: getattr(R, k) for k in patches}
    try:
        for k, v in patches.items():
            setattr(R, k, v)
        yield
    finally:
        for k, v in saved.items():
            setattr(R, k, v)


def stub_run(*_a, **_k):
    """NO MODEL IS LOADED. `run()` never reaches a server, so no lease is taken and no token is generated;
    every cell below is a not-loaded row and every number in the artifact is zero BY CONSTRUCTION."""
    return {"loaded": False, "why": "STUBBED BY THE PROBE -- no model, no lease",
            "load_failure_class": "PROBE_STUB"}


def ab_import(source, patches):
    """EXEC THE SCRIPT'S OWN SOURCE with driver attributes substituted at test time, so an IMPORT-TIME
    refusal can be seen. -> (namespace | None, message, exception class | None)"""
    try:
        with patched(**patches):
            ns = {"__name__": "mc_legend_ab_under_test", "__file__": MODULE}
            exec(compile(source, MODULE, "exec"), ns)                            # noqa: S102
            return ns, None, None
    except SystemExit as e:
        return None, str(e), "SystemExit"
    except BaseException as e:                                                   # noqa: BLE001
        return None, f"{type(e).__name__}: {e}", type(e).__name__


def ns_get(ns, key):
    return ns[key] if isinstance(ns, dict) else getattr(ns, key)


def ns_set(ns, key, value):
    if isinstance(ns, dict):
        ns[key] = value
    else:
        setattr(ns, key, value)


def stub_main(ns, out_path):
    """The script's own `main()`, with `run()` stubbed and OUT redirected to a scratch path. -> rc,
    artifact. `argv` is set as a run would set it, so the argument path is the real one."""
    saved_run, saved_out, saved_argv = R.run, ns_get(ns, "OUT"), sys.argv[:]
    try:
        R.run = stub_run
        ns_set(ns, "OUT", out_path)
        sys.argv = ["probe-ab-arm-names", "--entrant", ns_get(ns, "ENTRANT")]
        rc = ns_get(ns, "main")()
    finally:
        R.run = saved_run
        ns_set(ns, "OUT", saved_out)
        sys.argv = saved_argv
    art = json.load(open(out_path, encoding="utf-8")) if os.path.exists(out_path) else None
    return rc, art


def relabel(cells, mapping):
    out = json.loads(json.dumps(cells))
    for c in out:
        c["arm"] = mapping[c["arm"]]
    return out


def name_literal_sites(source, names, const_name):
    """-> (every exact-name string constant with its line, the lines of those OUTSIDE the constant
    assignment, the constant assignment's own lines). AST only: comments and prose are invisible here."""
    tree = ast.parse(source)

    def names_in(target):
        if isinstance(target, ast.Name):
            return {target.id}
        if isinstance(target, (ast.Tuple, ast.List)):
            return {n for e in target.elts for n in names_in(e)}
        return set()

    const_lines = {n.lineno for n in ast.walk(tree)
                   if isinstance(n, ast.Assign) and any(const_name in names_in(t) for t in n.targets)}
    sites = sorted((n.lineno, n.value) for n in ast.walk(tree)
                   if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in names)
    outside = sorted({ln for ln, _ in sites if ln not in const_lines})
    return sites, outside, sorted(const_lines)


def main():
    print("PROBE ab-arm-names -- the A/B's two arm names are the names it was PUBLISHED under")
    print("=" * 106)
    pub = json.load(open(PUB, encoding="utf-8"))
    cells = pub["cells"]
    published = pub["totals"]
    pub_arms = tuple(published)
    print(f"  instrument  {os.path.relpath(MODULE, HERE)}  digest {sha256_file(MODULE)[:16]}")
    print(f"  published   {PUB_REL}  sha256 RE-COMPUTED here: {sha256_file(PUB)}")
    print(f"  cells       {len(cells)} read from the artifact, "
          f"{len([c for c in cells if c.get('loaded')])} measured")
    print(f"  arms        published {pub_arms}  module ARMS {tuple(A.ARMS)}  "
          f"driver {tuple(R.LEGEND_ARMS)}  declaration LEGEND_DEFAULT {R.LEGEND_DEFAULT!r}")
    src = open(MODULE, encoding="utf-8").read()
    scratch = tempfile.mkdtemp(prefix="mc-ab-arm-names-")

    # ---------------------------------------------------------------- READING 1: replication of the totals
    print("\nREADING 1  REPLICATION -- the script's own arm_totals() over the PUBLISHED artifact's own cells")
    got = {name: A.arm_totals(cells, name) for name in pub_arms}
    for name in pub_arms:
        print(f"  {name:<8} published cells={published[name]['cells']} unknown={published[name]['unknown']} "
              f"fired={published[name]['fired']}  computed equal: {got[name] == published[name]}")
    ck("C1  every published totals row is reproduced, value for value", published, got)
    ck("C2  and the key ORDER is the published order, rows and outer dict",
       [list(v) for v in published.values()] + [list(published)],
       [list(v) for v in got.values()] + [list(got)])

    # ---------------------------------------------------------------- READING 2: the name keys the row
    print("\nREADING 2  THE NAME IS WHAT THE ROW IS KEYED BY -- every published cell relabeled example<->plain")
    mirrored_cells = relabel(cells, {"example": "plain", "plain": "example"})
    mirrored = {name: A.arm_totals(mirrored_cells, name) for name in pub_arms}
    for name in pub_arms:
        other = pub_arms[1] if name == pub_arms[0] else pub_arms[0]
        print(f"  relabeled cells: the row under {name!r} == the published row under {other!r}: "
              f"{mirrored[name] == published[other]}")
    ck("C3  the two rows MIRROR (the names key the rows, not a role)",
       {pub_arms[0]: published[pub_arms[1]], pub_arms[1]: published[pub_arms[0]]}, mirrored)
    ck("C4  and the two published rows DIFFER, so C3 is not satisfied by a constant",
       True, published[pub_arms[0]] != published[pub_arms[1]])

    # ---------------------------------------------------------------- READING 3: the artifact's own keys
    print("\nREADING 3  THE ARTIFACT'S OWN KEYS -- main() with the driver's run() STUBBED (no model, no lease)")
    print("           (every number below is zero BY CONSTRUCTION; the KEYS are what is read here)")
    out3 = os.path.join(scratch, "ab_stub.json")
    rc3, art3 = stub_main(A, out3)
    if art3 is None:
        raise SystemExit(f"PROBE DEFECT: main() produced no artifact at {out3} (rc {rc3})")
    print(f"  main() rc {rc3}  artifact {os.path.relpath(out3, HERE)}")
    print(f"  arms keys  {list(art3['arms'])}\n  totals keys {list(art3['totals'])}")
    print(f"  branch     {art3['branch'][:96]}")
    ck("C5  the artifact's `arms` keys are the published `arms` keys", list(pub["arms"]), list(art3["arms"]))
    ck("C6  and its `totals` keys are the published `totals` keys, in order",
       list(published), list(art3["totals"]))
    ck("C7  the arm SET the script runs is the published pair, in the published order",
       pub_arms, tuple(A.ARMS))
    ck("C7b and that pair is the driver's own arms (so the reachable state is the measured one)",
       pub_arms, tuple(R.LEGEND_ARMS))

    # ---------------------------------------------------------------- READING 4: the real exposure
    print("\nREADING 4  THE REAL EXPOSURE -- the driver's arms RENAMED in memory, cells relabeled to match")

    def renamed(who, to):
        """The driver's arm dict with ONE name replaced, order preserved -- the same two prompt bodies, one
        of them under a name the published record never used."""
        return {to if a == who else a: R.LEGEND_ARMS[a] for a in ("example", "plain")}

    def report_rename(tag, who, to):
        """-> (ns | None, message, class, refusal_ok)"""
        arms = renamed(who, to)
        patches = {"LEGEND_ARMS": arms, "LEGEND_DEFAULT": to, "run": stub_run}
        print(f"  {tag}  LEGEND_ARMS {tuple(arms)}  LEGEND_DEFAULT {to!r}  cells {who!r} -> {to!r}")
        ns, msg, cls = ab_import(src, patches)
        if ns is None:
            print(f"      import     {cls}: {msg}")
            return ns, msg, cls, True
        relabeled = relabel(cells, {"example": "example", "plain": "plain", who: to})
        with patched(**patches):
            for name in pub_arms:
                try:
                    print(f"      run path   legend_digest({name!r}) = {R.legend_digest(name)}")
                except BaseException as e:                                       # noqa: BLE001
                    print(f"      run path   legend_digest({name!r}) raised {type(e).__name__}: {e}")
            for name in pub_arms + (to,):
                t = ns["arm_totals"](relabeled, name)
                print(f"      totals row arm_totals(relabeled cells, {name!r}) -> cells {t['cells']} "
                      f"unknown {t['unknown']} fired {t['fired']} controls_pass {t['controls_pass']} "
                      f"best_cell_score {t['best_cell_score']!r}")
        return ns, msg, cls, False

    ns4a, msg4a, cls4a, ok4a = report_rename("4a", "plain", "terse")
    ck("C8  4a REFUSES at import, and the refusal names the published artifact and its digest",
       ("SystemExit", True), (cls4a, bool((msg4a or "").find("MC_LEGEND_AB.json") >= 0
                                          and (msg4a or "").find("029244b6e5232a6b") >= 0)))
    ns4b, msg4b, cls4b, ok4b = report_rename("4b", "example", "worked")
    ck("C9  4b REFUSES at import, and the refusal names the published artifact and its digest",
       ("SystemExit", True), (cls4b, bool((msg4b or "").find("MC_LEGEND_AB.json") >= 0
                                          and (msg4b or "").find("029244b6e5232a6b") >= 0)))

    print("  4c  THE SILENT HALF -- the pair MOVED and the two key sites left as written (a driver whose arms\n"
          "      are ('example','terse'), with ARMS moved to match in memory); main() run under the stub")
    arms4c = {"example": R.PROMPT_EXAMPLE, "terse": R.PROMPT_PLAIN}
    patches4c = {"LEGEND_ARMS": arms4c, "LEGEND_DEFAULT": "terse", "run": stub_run}
    out4c = os.path.join(scratch, "ab_stub_moved.json")
    ns4c, msg4c, cls4c = ab_import(src, patches4c)
    got4c = ("SystemExit", None)
    if ns4c is None:
        print(f"      import     {cls4c}: {msg4c}")
    else:
        with patched(**patches4c):
            ns_set(ns4c, "ARMS", ("example", "terse"))     # THE MOVE, IN MEMORY ONLY
            rc4c, art4c = stub_main(ns4c, out4c)
        if art4c is None:
            raise SystemExit(f"PROBE DEFECT: 4c produced no artifact at {out4c} (rc {rc4c})")
        agreed = list(art4c["arms"]) == list(art4c["totals"])
        got4c = ("imported", agreed)
        print(f"      main() rc {rc4c}  -- the run COMPLETED and would publish")
        print(f"      arms keys   {list(art4c['arms'])}")
        print(f"      totals keys {list(art4c['totals'])}")
        for name in art4c["totals"]:
            t = art4c["totals"][name]
            print(f"        totals[{name!r}] cells {t['cells']} controls_pass {t['controls_pass']} "
                  f"unknown {t['unknown']} fired {t['fired']}")
        print(f"      the same artifact is keyed two ways: {'YES' if not agreed else 'no'}")
    ck("C10 4c REFUSES at import -- a moved pair is refused, not published under the old keys",
       ("SystemExit", None), got4c)

    # ---------------------------------------------------------------- READING 5: one copy of the names
    print("\nREADING 5  ONE COPY OF THE NAMES -- exact arm-name string constants in the live source (AST)")
    sites, outside, const_lines = name_literal_sites(src, set(pub_arms), "AB_EXAMPLE_ARM")
    for line, value in sites:
        print(f"      line {line:<4} {value!r}{'   <- the AB_*_ARM assignment' if line in const_lines else ''}")
    print(f"      {len(sites)} exact name constant(s) in {len({l for l, _ in sites})} line(s); "
          f"outside the AB_*_ARM assignment: {outside}")
    ck("C11 no exact arm name is written anywhere but the AB_*_ARM assignment "
       "(comments are invisible to AST: this is about code, not prose)", [], outside)

    # ---------------------------------------------------------------- READING 6: nothing moved
    print("\nREADING 6  NOTHING MOVED -- the records, the artifact, the frozen inputs")
    st = subprocess.run(["git", "-C", HERE, "status", "--porcelain", "--", "probes/", "results/"],
                        capture_output=True, text=True)
    dirty = [ln for ln in st.stdout.splitlines() if ln.strip()]
    print(f"  git status --porcelain probes/ results/  ->  {len(dirty)} line(s)"
          + ("" if not dirty else "\n" + "\n".join("    " + ln for ln in dirty)))
    ck("C12 no record moved", 0, len(dirty))
    ck("C13 the published artifact's sha256 is the one the card quotes", PUB_DIGEST, sha256_file(PUB))
    moved = {k: (v, sha256_file(os.path.join(HERE, k))[:16]) for k, v in FROZEN.items()
             if sha256_file(os.path.join(HERE, k))[:16] != v}
    print(f"  frozen inputs: {len(FROZEN)} re-read, {len(moved)} moved"
          + ("" if not moved else f": {moved}"))
    ck("C14 every frozen input is unchanged", {}, moved)

    shutil.rmtree(scratch, ignore_errors=True)
    bad = [n for n, ok, *_ in CHECKS if not ok]
    print("\n" + "=" * 106)
    print(f"  {len(CHECKS) - len(bad)}/{len(CHECKS)} checks PASS"
          + ("" if not bad else "\n  FAILED: " + "; ".join(bad)))
    print(f"  VERDICT {'PASS' if not bad else 'FAIL'}  (rc {0 if not bad else 3})")
    return 0 if not bad else 3


if __name__ == "__main__":
    sys.exit(main())
