#!/usr/bin/env python3
"""THE DECLARED ROOT'S OWN CONTROLS -- and both refusal directions are FREE.

WHY THIS FILE EXISTS. `run_card.py` stopped writing results into `<worktree>/results` and started
refusing instead. A refusal is testable at zero cost (a refusal IS the short circuit), so the two
directions that matter are exercised here without spawning a model, without a GPU, and without
writing a byte into the record:

  1  NO DECLARATION           -> REFUSE. The old fallback to <worktree>/results must not come back
                                 as a default.
  2  A DECLARATION INSIDE A GIT WORKING TREE -> REFUSE. Including the environment override, because
                                 the override moves WHERE the root is, never WHETHER it may sit in a
                                 git tree.

And the properties the ruling asks for, each MEASURED rather than asserted in prose:

  3  ONE ROOT, THE SAME FOR EVERY WORKTREE OF THIS REPO AND OUTSIDE ALL OF THEM.
  4  THE WRITER writes there, and the old literal is GONE (not merely unused).
  5  THE SWEEPS' DOMAIN IS DECLARED, AND A STRAY `results/` CANNOT JOIN IT BY EXISTING -- including
     one this very test creates inside a git tree.
  6  THE LEGACY RECORD IS DECLARED IN PLACE, and the three cabinet copies really are copies (the
     claim is re-measured; if it ever stops holding the declaration has to be re-decided, and this
     test fails instead of the claim rotting quietly).

Run: python3 test_declared_root.py     -> exit 0 if every direction behaves.
"""
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cabinet_root as _root                                              # noqa: E402

NO_ENV = {}          # an environment where CABINET_RESULTS is not set -- the git config is read
FAILS = []


def check(ok, label, detail=""):
    print(f"  {'ok   ' if ok else 'FAIL '} {label}")
    if detail:
        for line in str(detail).splitlines():
            print(f"         {line}")
    if not ok:
        FAILS.append(label)


def refusal(fn, *a, **kw):
    """-> the message of the Refusal, or None if it did NOT refuse."""
    try:
        fn(*a, **kw)
    except SystemExit as e:
        return str(e)
    except Exception as e:                                        # noqa: BLE001
        return f"WRONG EXCEPTION: {type(e).__name__}: {e}"
    return None


def probes():
    # ---------------------------------------------------------------- 1 + 2: THE REFUSALS, FREE
    print("\n  1/2  THE TWO REFUSAL DIRECTIONS (each costs nothing and writes nothing)\n")

    tmp = tempfile.mkdtemp(prefix="no_repo_")
    try:
        msg = refusal(_root.declared_root, repo=tmp, env=NO_ENV)
        check(msg is not None and "REFUSING" in msg and _root.DECLARED_ENV in msg,
              "no declaration anywhere -> REFUSES, and names the remedy",
              msg or "IT RETURNED A ROOT -- a silent default is the defect itself")
        msg = refusal(_root.results_dir, repo=tmp, env=NO_ENV)
        check(msg is not None, "and results_dir() refuses with it, so run_card cannot fall back",
              msg or "IT RETURNED A PATH")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    inside = os.path.join(HERE, "results")
    msg = refusal(_root.declared_root, repo=HERE, env={_root.DECLARED_ENV: inside})
    check(msg is not None and "INSIDE a git working tree" in msg,
          f"{_root.DECLARED_ENV}=<worktree>/results -> REFUSES (the override cannot re-create the "
          f"defect)", msg or "IT ACCEPTED A ROOT INSIDE A GIT TREE")

    msg = refusal(_root.declared_root, repo=HERE,
                  env={_root.DECLARED_ENV: _root.git_common_dir()})
    check(msg is not None and "git directory" in msg,
          "and a root inside .git/ is refused too -- `--show-toplevel` cannot see that case, so it "
          "is checked on its own", msg or "IT ACCEPTED THE GIT DIRECTORY")

    # ---------------------------------------------------------------- 3: ONE ROOT, OUTSIDE ALL
    print("\n  3    ONE ROOT, THE SAME FOR EVERY WORKTREE, AND OUTSIDE ALL OF THEM\n")
    listing = _root.git("worktree", "list", "--porcelain") or ""
    trees = [ln.split(" ", 1)[1] for ln in listing.splitlines() if ln.startswith("worktree ")]
    check(len(trees) >= 4, f"worktrees found: {len(trees)}", "\n".join(trees))
    roots = {}
    for wt in trees:
        try:
            # `repo=wt` is what makes this a test OF the carrier: each worktree is asked through
            # its OWN git context, and the answer has to be the same one.
            roots[wt] = _root.declared_root(repo=wt, env=NO_ENV)[0]
        except SystemExit as e:
            roots[wt] = f"REFUSED: {e}"
    uniq = sorted(set(roots.values()))
    check(len(uniq) == 1 and uniq[0].startswith("/"),
          "every worktree of this repo resolves to the SAME root", "\n".join(uniq))
    if len(uniq) == 1:
        root = uniq[0]
        check(_root.git_toplevel(root) is None,
              f"the root is OUTSIDE every git working tree: {root}")
        inside_any = [wt for wt in trees if os.path.realpath(root).startswith(
            os.path.realpath(wt).rstrip("/") + "/")]
        check(not inside_any, "and it is not inside any of the worktrees either",
              "\n".join(inside_any))
        print(f"         carrier: {_root.declared_root(repo=trees[0], env=NO_ENV)[1]}")
        for wt in sorted(roots):
            print(f"         {roots[wt]}   <- {wt}")

    # ---------------------------------------------------------------- 4: THE WRITER
    print("\n  4    THE WRITER WRITES THERE, AND THE OLD LITERAL IS GONE\n")
    src = open(os.path.join(HERE, "run_card.py"), encoding="utf-8").read()
    check('os.path.join(ARENA, "results")' not in
          "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#")),
          "no LIVE line of run_card.py holds `os.path.join(ARENA, \"results\")` (the comments that "
          "quote the line it replaced are not code, and this check reads code)")
    try:
        import run_card                                                # noqa: E402
        want = os.path.join(_root.declared_root(env=NO_ENV)[0], _root.cabinet())
        check(os.path.realpath(run_card.RESULTS) == os.path.realpath(want),
              "run_card.RESULTS is <declared ROOT>/<this worktree's cabinet>",
              f"got {run_card.RESULTS}\nwant {want}")
        check(_root.git_toplevel(run_card.RESULTS) is None,
              "run_card.RESULTS is NOT inside a git working tree",
              f"it is inside {_root.git_toplevel(run_card.RESULTS)}")
        check(os.path.realpath(run_card.RESULTS) != os.path.realpath(os.path.join(HERE, "results")),
              "run_card.RESULTS is NOT this worktree's results/ -- the defect, stated as a check")
    except SystemExit as e:
        check(False, "run_card could not be imported, so three checks did not run", str(e))

    # ---------------------------------------------------------------- 5: THE DOMAIN
    print("\n  5    THE SWEEPS' DOMAIN IS DECLARED, AND NOTHING JOINS IT BY EXISTING\n")
    dom = _root.domain(env=NO_ENV)
    root = _root.declared_root(env=NO_ENV)[0]
    outside = [f"{k}:{b}" for k, b in dom
               if not (os.path.realpath(b).startswith(os.path.realpath(root) + os.sep)
                       or os.path.realpath(b) == os.path.realpath(_root.LEGACY_RECORD))]
    check(not outside, "every entry is under the declared root or is the legacy record in place",
          "\n".join(outside))
    check(all(os.path.realpath(b) != os.path.realpath(os.path.join(HERE, "results"))
              for _k, b in dom),
          "this worktree's own results/ is NOT in the domain")
    check(all(os.path.realpath(b) != os.path.realpath(p)
              for _k, b in dom for p in _root.DUPLICATE_RECORD_TREES),
          "nor are the three declared duplicate copies")

    stray = os.path.join(HERE, "ZZ_stray_domain_probe", "results")
    os.makedirs(stray, exist_ok=True)
    try:
        after = _root.domain(env=NO_ENV)
        check([b for _k, b in after] == [b for _k, b in dom],
              "a stray `results/` created inside a git tree does NOT join the domain",
              f"created {stray}")
    finally:
        shutil.rmtree(os.path.dirname(stray), ignore_errors=True)

    for mod, name in (("reconcile_and_backfill", "reconcile_and_backfill.py"),
                      ("test_game_states", "test_game_states.py")):
        try:
            m = __import__(mod)
            check(m.DOMAIN == dom, f"{name} scans the DECLARED domain, from cabinet_root",
                  "scope: " + ", ".join(f"{k}={b}" for k, b in m.DOMAIN))
        except SystemExit as e:
            check(False, f"{name} could not be imported", str(e))
    for f in ("test_bind_control.py", "test_game_states.py", "reconcile_and_backfill.py"):
        text = open(os.path.join(HERE, f), encoding="utf-8").read()
        check("import cabinet_root" in text and
              not re.search(r'^\s*RESULTS\s*=\s*os\.path\.join\(HERE, "results"\)', text, re.M),
              f"{f} takes its scope from cabinet_root (textual regression guard on the literal)")

    check(_root.in_domain(os.path.join(_root.LEGACY_RECORD, "some_bundle.json"), env=NO_ENV),
          "the write guard ADMITS a file in the legacy record (maintenance is allowed)")
    check(not _root.in_domain(os.path.join(HERE, "results", "some_bundle.json"), env=NO_ENV),
          "and REFUSES one in <worktree>/results, so --apply cannot rewrite a found tree")

    # ---------------------------------------------------------------- 6: DECLARED IN PLACE
    print("\n  6    THE LEGACY RECORD IS DECLARED IN PLACE, AND THE COPIES ARE COPIES\n")
    refs = ["main", "cabinet/sokoban", "cabinet/missile-command", "cabinet/zork"]
    shas = {r: _root.git("rev-parse", f"{r}:results") for r in refs}
    check(len(set(shas.values())) == 1 and None not in shas.values(),
          "all four `results` trees are the SAME tree object -- copies, not four records",
          "\n".join(f"{r}: {s}" for r, s in shas.items()) +
          "\nIF THIS EVER FAILS: a copy has diverged. The declaration in cabinet_root.py has to be "
          "RE-DECIDED (moved, or declared separately) rather than silently kept.")
    n_tracked = len((_root.git("ls-files", "results") or "").splitlines())
    sha0 = (list(shas.values())[0] or "?")[:12]
    print(f"         legacy record: {n_tracked} tracked files here (tree {sha0})")
    print(f"         {_root.LEGACY_WHY}")
    print(f"         {_root.DUPLICATE_WHY}")

    print()
    if FAILS:
        print(f"  {len(FAILS)} failure(s): {FAILS}")
        print("  A control that cannot fail is decoration; these are the directions that must.")
        return 1
    print("  ALL DIRECTIONS BEHAVE: the refusals fire, the root is one root outside every tree,")
    print("  and the domain is a declaration rather than a walk.")
    return 0


if __name__ == "__main__":
    raise SystemExit(probes())
