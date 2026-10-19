#!/usr/bin/env python3
"""PROBE -- is `arm_effect` a READING OF THE DECLARATION, or a PUBLISHED COMPARISON? Model-free.

No model, no lease, no write into the tree. It asks the runner's own `verdict_inputs()` the question the
card is about, over the PUBLISHED artifact's own 24 cells, and reports four readings:

  READING 1  REPLICATION. `verdict_inputs()` over `probes/MC_POPULATION_20261017-184752.json`'s own cells
             must reproduce that artifact's `verdict_inputs.arm_effect` field -- every value, every key,
             the key ORDER and the branch sentence. This is the control that says the block has not moved.
  READING 2  THE NAME IS WHAT IT READS. Relabel every cell `example`<->`plain` and re-run: if the block
             reads the arm NAMES (as published), every sub-dict mirrors and the branch moves to BRANCH 3.
  READING 3  THE CARD'S STATED FAILURE MODE, MEASURED. The card says the keys are "wrong and wrong
             silently" if the declaration ever names `example` again. Exec the runner's SOURCE in memory
             with the driver's `LEGEND_DEFAULT` substituted to `example` (nothing on disk is touched) and
             re-run: the block is compared with the published one. This reading can go either way and the
             pre-registration fixes which way it is expected to go.
  READING 4  THE REAL EXPOSURE. Patch the driver's `LEGEND_ARMS` in memory to RENAME an arm, relabel the
             cells the same way (which is what a future run would produce), and re-run. A key that is no
             longer an arm must REFUSE, not report zeros under a name the field no longer contains.
             **This reading is the positive control: it FAILS before the fix and PASSES after it.**

Exit 0 only if every check passes; 3 otherwise. `scripts/run_guarded.sh` is the only way this runs.
"""
import copy
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import missile_command_population as M                                          # noqa: E402
import missile_command_run as R                                                 # noqa: E402

MODULE = os.path.join(HERE, "missile_command_population.py")
PUB_REL = os.path.join("probes", "MC_POPULATION_20261017-184752.json")
PUB = os.path.join(HERE, PUB_REL)
PUB_DIGEST = "9335b2a39b4d1d389b78b4a88a82f576020387bf7ed3ed21b7c2158899d54156"

# THE FROZEN INPUTS `PREREG_mc_ab_arm_keys.md` §4 fixes. Checked, not quoted: this probe recomputes them.
FROZEN = {
    "missile_command.py": "eb5ed36591b300e6",
    "missile_command_run.py": "3bd43eed4c6e41f3",
    "PREREG_missile_command.md": "01548e9a866df03e",
    "levels/mc_01_one_shot.txt": "ab101ca955c1c853",
    "levels/mc_02_scarcity.txt": "327d2157bd0b8a83",
    "MC_DECLARATION.md": "2ada03ee2ad1f60b",
    "scripts/run_guarded.sh": "5e34e455b5193e89",
    "PREREG_mc_population.md": "cfedf8b7f5e7d57f",
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


def run_source(source, filename, patches):
    """EXEC THE RUNNER'S OWN SOURCE with driver attributes substituted AT TEST TIME.

    Nothing on disk is touched and nothing is rewritten: the driver module is patched in memory for the
    duration of the exec and restored in `finally`, so the module is the one the tree holds and the ONE
    value under test is the only difference. -> (namespace | None, refusal text | exception text,
    exception class)"""
    saved = {k: getattr(R, k) for k in patches}
    ns = {"__name__": "mc_population_under_test", "__file__": MODULE}
    try:
        for k, v in patches.items():
            setattr(R, k, v)
        exec(compile(source, filename, "exec"), ns)                              # noqa: S102
        return ns, None, None
    except SystemExit as e:
        return None, str(e), "SystemExit"
    except BaseException as e:                                                   # noqa: BLE001
        return None, f"{type(e).__name__}: {e}", type(e).__name__
    finally:
        for k, v in saved.items():
            setattr(R, k, v)


def block_fn(ns):
    """The live module and an exec'd namespace are two containers of the same function."""
    return ns["verdict_inputs"] if isinstance(ns, dict) else ns.verdict_inputs


def call_block(ns, cells, meta):
    """-> (arm_effect | None, exception class | None, exception text)"""
    try:
        return block_fn(ns)(cells, meta)["arm_effect"], None, None
    except BaseException as e:                                                   # noqa: BLE001
        return None, type(e).__name__, str(e)


def relabel(cells, mapping):
    out = copy.deepcopy(cells)
    for c in out:
        c["arm"] = mapping[c["arm"]]
    return out


def fmt(value, cls, txt):
    """One line for a reading that may have been a value, a refusal or a crash."""
    return json.dumps(value) if value is not None else f"{cls}: {txt}"


def main():
    print("PROBE ab-arm-keys -- `arm_effect` is a PUBLISHED comparison; its exposure is the DRIVER's arm names")
    print("=" * 106)
    print(f"  instrument  missile_command_population.py  digest {sha256_file(MODULE)[:16]}  ({MODULE})")
    pub = json.load(open(PUB, encoding="utf-8"))
    cells = pub["cells"]
    published = pub["verdict_inputs"]["arm_effect"]
    print(f"  published   {PUB_REL}  sha256 RE-COMPUTED here: {sha256_file(PUB)}")
    print(f"  cells       {len(cells)} read from the artifact, {len([c for c in cells if c.get('loaded')])} measured")
    print(f"  arms        driver {tuple(R.LEGEND_ARMS)}  declaration LEGEND_DEFAULT {R.LEGEND_DEFAULT!r}  "
          f"runner COORD_ARM {M.COORD_ARM!r} / COMPARISON_ARM {M.COMPARISON_ARM!r}")

    # ---------------------------------------------------------------- READING 1: replication of the field
    print("\nREADING 1  REPLICATION -- verdict_inputs() over the PUBLISHED artifact's own cells")
    af1, exc1, txt1 = call_block(M, copy.deepcopy(cells), pub)
    print(f"  published  {json.dumps(published)}")
    print(f"  computed   {fmt(af1, exc1, txt1)}")
    ck("C1  the block reproduces the published field, value for value", published, af1)
    ck("C2  the key ORDER is the published order", [list(v) for v in published.values() if isinstance(v, dict)],
       [list(v) for v in (af1 or {}).values() if isinstance(v, dict)])

    # ---------------------------------------------------------------- READING 2: the name is what it reads
    print("\nREADING 2  THE NAME IS WHAT IT READS -- every cell relabeled example<->plain")
    af2, exc2, txt2 = call_block(M, relabel(cells, {"example": "plain", "plain": "example"}), pub)
    print(f"  computed   {fmt(af2, exc2, txt2)}")
    mirrored = {"unknown": {"example": 7, "plain": 27}, "fired": {"example": 8, "plain": 2},
                "mc02_score_total": {"example": 1, "plain": 0}}
    ck("C3  every sub-dict is MIRRORED (the block reads the names, not the roles)",
       mirrored, {k: (af2 or {}).get(k) for k in mirrored})
    ck("C4  and the branch moves to BRANCH 3 -- the direction claim is name-sensitive",
       True, bool(af2 and af2.get("branch", "").startswith("BRANCH 3")))

    # ---------------------------------------------------------------- READING 3: the card's stated risk
    print("\nREADING 3  THE CARD'S STATED FAILURE MODE, MEASURED -- the declaration names `example` again")
    src = open(MODULE, encoding="utf-8").read()
    ns3, ref3, exc3 = run_source(src, MODULE, {"LEGEND_DEFAULT": "example"})
    if ns3 is None:
        print(f"  the source REFUSED to import under that substitution: {exc3}: {ref3}")
    af3 = None
    if ns3 is not None:
        print(f"  under test  COORD_ARM {ns3['COORD_ARM']!r}  COMPARISON_ARM {ns3['COMPARISON_ARM']!r}")
        af3, e3, t3 = call_block(ns3, copy.deepcopy(cells), pub)
        print(f"  computed    {fmt(af3, e3, t3)}")
    ck("C5  with the declaration naming `example` the block is UNCHANGED from the published reading",
       published, af3)

    # ---------------------------------------------------------------- READING 4: the real exposure
    print("\nREADING 4  THE REAL EXPOSURE -- the driver's arms RENAMED and the cells relabeled to match")
    # 4a: `plain` renamed. The published key `plain` is then not an arm, and its cells do not exist.
    print("  4a  LEGEND_ARMS ('example','terse'), LEGEND_DEFAULT 'terse'   cells 'plain' -> 'terse'")
    ns4, ref4, exc4 = run_source(src, MODULE, {"LEGEND_ARMS": {"example": R.PROMPT_EXAMPLE,
                                                               "terse": R.PROMPT_PLAIN},
                                               "LEGEND_DEFAULT": "terse"})
    if ns4 is None:
        print(f"      import  {exc4}: {ref4}")
        got4, cls4, txt4 = None, exc4, ref4
    else:
        got4, cls4, txt4 = call_block(ns4, relabel(cells, {"example": "example", "plain": "terse"}), pub)
        print(f"      block   {fmt(got4, cls4, txt4)}")
    ck("C6  4a REFUSES, and the refusal names the published artifact and its digest",
       ("SystemExit", True),
       (cls4, bool((txt4 or "").find("MC_POPULATION_20261017-184752.json") >= 0
                   and (txt4 or "").find("9335b2a39b4d1d38") >= 0)))
    # 4b: `example` renamed -- the other key, and the arm the block's own last two lines index by name.
    print("  4b  LEGEND_ARMS ('worked','plain'), LEGEND_DEFAULT 'plain'   cells 'example' -> 'worked'")
    ns5, ref5, exc5 = run_source(src, MODULE, {"LEGEND_ARMS": {"worked": R.PROMPT_EXAMPLE,
                                                               "plain": R.PROMPT_PLAIN},
                                               "LEGEND_DEFAULT": "plain"})
    if ns5 is None:
        print(f"      import  {exc5}: {ref5}")
        got5, cls5, txt5 = None, exc5, ref5
    else:
        got5, cls5, txt5 = call_block(ns5, relabel(cells, {"example": "worked", "plain": "plain"}), pub)
        print(f"      block   {fmt(got5, cls5, txt5)}")
    ck("C7  4b REFUSES, and the refusal names the published artifact and its digest",
       ("SystemExit", True),
       (cls5, bool((txt5 or "").find("MC_POPULATION_20261017-184752.json") >= 0
                   and (txt5 or "").find("9335b2a39b4d1d38") >= 0)))

    # ---------------------------------------------------------------- READING 5: nothing moved
    print("\nREADING 5  NOTHING MOVED -- the records, the artifact, the frozen inputs")
    st = subprocess.run(["git", "-C", HERE, "status", "--porcelain", "--", "probes/", "results/"],
                        capture_output=True, text=True)
    dirty = [ln for ln in st.stdout.splitlines() if ln.strip()]
    print(f"  git status --porcelain probes/ results/  ->  {len(dirty)} line(s)"
          + ("" if not dirty else "\n" + "\n".join("    " + ln for ln in dirty)))
    ck("C8  no record moved", 0, len(dirty))
    ck("C9  the published population artifact's digest is the one the card quotes", PUB_DIGEST,
       sha256_file(PUB))
    moved = {k: (v, sha256_file(os.path.join(HERE, k))[:16]) for k, v in FROZEN.items()
             if sha256_file(os.path.join(HERE, k))[:16] != v}
    print(f"  frozen inputs: {len(FROZEN)} re-read, {len(moved)} moved" + ("" if not moved else f": {moved}"))
    ck("C10 every frozen input is unchanged", {}, moved)
    ck("C11 the driver still defines the two published arms (so readings 1-3 are about the real state)",
       ("example", "plain"), tuple(R.LEGEND_ARMS))

    bad = [n for n, ok, *_ in CHECKS if not ok]
    print("\n" + "=" * 106)
    print(f"  {len(CHECKS) - len(bad)}/{len(CHECKS)} checks PASS"
          + ("" if not bad else "\n  FAILED: " + "; ".join(bad)))
    print(f"  VERDICT {'PASS' if not bad else 'FAIL'}  (rc {0 if not bad else 3})")
    return 0 if not bad else 3


if __name__ == "__main__":
    sys.exit(main())
