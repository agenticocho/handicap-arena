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
import json
import os
import re
import shutil
import subprocess
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
    # `main` is the case that makes this a real check rather than a slogan: ITS OWN results/ IS
    # the legacy record, so it IS in the domain -- as `legacy`, declared in place. The claim that
    # survives in every worktree is the one that matters: nothing a RUN can write lands there.
    mine = os.path.realpath(os.path.join(HERE, "results"))
    as_live = [k for k, b in dom if os.path.realpath(b) == mine and not k.startswith("legacy")]
    as_legacy = [k for k, b in dom if os.path.realpath(b) == mine and k.startswith("legacy")]
    check(not as_live,
          "this worktree's own results/ is NOT in the domain as a LIVE entry -- no run writes there",
          f"it appears as {as_live}")
    if as_legacy:
        print(f"         (this worktree's results/ IS the declared legacy record: it appears only "
              f"as {as_legacy}, in place, and not because a walk found it)")
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
          "the write guard ADMITS a file in the legacy record (declared maintenance is allowed)")
    undeclared = os.path.join(HERE, "logs", "some_bundle.json")
    check(not _root.in_domain(undeclared, env=NO_ENV),
          "and REFUSES a file that is inside this worktree's git tree and is NOT declared",
          undeclared)
    here_res = os.path.join(HERE, "results", "some_bundle.json")
    check(_root.in_domain(here_res, env=NO_ENV) == bool(as_legacy),
          "a file in THIS worktree's results/ is admitted only where that tree IS the declared "
          "legacy record (main), and refused where it is an undeclared copy (the cabinets)",
          f"{here_res} -> in_domain={_root.in_domain(here_res, env=NO_ENV)}, "
          f"is_the_legacy_record={bool(as_legacy)}")

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

    # ---------------------------------------------------------------- 7: THE LOGS ARE SCRATCH
    print("\n  7    THE LOGS ARE SCRATCH, THE COORDINATE IS DECLARED PER BUNDLE, AND A CAPTURE\n"
          "       CANNOT ENTER THE RECORD\n")
    check(_root.LOGS_ARE == "scratch",
          "the classification is stated in the one definition: logs/ IS SCRATCH",
          f"LOGS_ARE={_root.LOGS_ARE!r}")
    check(os.path.realpath(_root.log_dir(HERE)) == os.path.realpath(os.path.join(HERE, "logs")),
          "log_dir() resolves to THIS worktree's logs/ -- the writer's destination, not a second copy "
          "of the rule",
          f"got {_root.log_dir(HERE)}")
    check(_root.git_toplevel(_root.log_dir(HERE)) is not None,
          "and it is INSIDE a git tree, which is correct FOR SCRATCH: what keeps a log out of the "
          "record is the ignore rule, not a separate root -- and results_dir() still refuses, "
          "because a RESULT in a matchable tree is the defect and a log in one is not")
    check(_root.log_path(HERE).endswith(os.sep + _root.LOG_NAME),
          f"the run journal is <worktree>/logs/{_root.LOG_NAME}, resolved and not remembered")

    # THE COORDINATE IS A PROPERTY OF THE BUNDLE, NOT OF THE READER. This is the whole of the read
    # half of t_c442023d: measured before it landed, one sweep over one declared domain resolved 31
    # admissible log lines from main and 0 from each cabinet worktree -- the answer changed with
    # where the reader was sitting.
    probes = {k: _root.log_for(os.path.join(b, "ANY_BUNDLE.json"), env=NO_ENV)
              for k, b in dom}
    wts = _root.worktrees()
    _myname = _root.cabinet()
    # THE OTHER CABINETS THAT ARE ACTUALLY IN THE DOMAIN -- a worktree that owns no declared entry
    # is not a second opinion, it is a different question.
    others = sorted({k.split(":", 1)[1] for k in probes if k.startswith("live:")} - {_myname})
    live_vals = {k: v for k, v in probes.items() if k.startswith("live:")}
    check(len(set(live_vals.values())) == len(live_vals),
          "each live cabinet entry resolves its OWN journal -- not one journal for the whole domain",
          "\n".join(f"{k} -> {v}" for k, v in sorted(live_vals.items())))
    check(all(v for v in probes.values()),
          "and no entry resolves to nothing (an entry may not delegate its coordinate to the reader)")
    print(f"         the legacy entry and live:{_myname} resolve to the SAME journal only in the "
          f"worktree the legacy runs were made in -- a measurement, not the definition")
    if others:
        other = wts[[br for br in sorted(wts) if br.split("/")[-1] == others[0]][0]]
        same = all(_root.log_for(os.path.join(b, "ANY_BUNDLE.json"), env=NO_ENV) ==
                   _root.log_for(os.path.join(b, "ANY_BUNDLE.json"), repo=other, env=NO_ENV)
                   for _k, b in dom)
        check(same,
              f"THE SAME BUNDLE RESOLVES TO THE SAME JOURNAL FROM ANOTHER WORKTREE "
              f"({_myname} vs {others[0]}): an answer that changes with the reader is an answer "
              f"about the reader")
        mine_k, their_k = "live:" + _myname, "live:" + others[0]
        check(probes.get(mine_k) != probes.get(their_k),
              f"and a {others[0]} bundle does NOT resolve to this worktree's journal",
              f"{mine_k} -> {probes.get(mine_k)}\n{their_k} -> {probes.get(their_k)}")

    # THE TREE CANNOT ABSORB A CAPTURE. The ignore rule has to name the DIRECTORY: naming an
    # extension is what let NINE captures be committed, and scripts/run_guarded.sh still writes
    # <workdir>/logs/<UNIT>.out.
    def ignored(rel):
        return subprocess.run(["git", "-C", HERE, "check-ignore", "-q", rel]).returncode == 0
    check(ignored("logs/ZZ_a_new_capture.out") and ignored("logs/ZZ_a_new_capture.log"),
          "a NEW capture in logs/ is IGNORED whatever its extension -- `git add -A` cannot stage "
          "one, so no capture enters the record except by a deliberate `git add -f`")
    tracked = sorted((_root.git("ls-files", "logs", repo=HERE) or "").splitlines())
    undeclared = [f for f in tracked if f not in _root.LEGACY_CAPTURES]
    gone = [f for f in tracked if not os.path.exists(os.path.join(HERE, f))]
    check(not undeclared,
          f"every one of the {len(tracked)} tracked file(s) under logs/ is a DECLARED capture "
          f"(LEGACY_CAPTURES) -- a tenth one cannot be committed unnoticed", "\n".join(undeclared))
    check(not gone,
          "and every declared capture is still ON DISK -- FINDINGS/018, FINDINGS/019, "
          "NEXT_WINDOW.md and SOKOBAN_VERDICT_1.md cite logs/sokoban_rerun.out BY PATH",
          "\n".join(gone))
    print(f"         {len(tracked)} tracked here; {len(_root.LEGACY_CAPTURES)} declared in "
          f"cabinet_root.py (the three cabinet branches carry a SUBSET -- 6, not 9 -- so the "
          f"number is read per tree)")

    # AND THE EDGE LIST IS CHECKED, NOT REMEMBERED. Every live construction of a log path must be
    # in LOG_EDGES.json with a status and an anchor; every anchor must still be there; and a file
    # listed as migrated must NOT have started constructing one again.
    man_path = os.path.join(HERE, "LOG_EDGES.json")
    try:
        man = json.load(open(man_path, encoding="utf-8"))
    except Exception as e:                                        # noqa: BLE001
        man = None
        check(False, "LOG_EDGES.json could not be read", f"{type(e).__name__}: {e}")
    if man:
        edge_re = re.compile(r'(os\.path\.join\([^)\n]*["\']logs["\']|["\']logs/|logs/\$\{)')
        found = {}
        for f in (_root.git("ls-files", "*.py", "*.sh", repo=HERE) or "").splitlines():
            try:
                text = open(os.path.join(HERE, f), encoding="utf-8").read()
            except OSError:
                continue
            for line in text.splitlines():
                if line.lstrip().startswith("#"):
                    continue                    # A COMMENT IS NOT CODE, and this check reads code
                if edge_re.search(line):
                    found[f] = line.strip()
        declared = {e["file"]: e for e in man.get("edges", [])}
        undeclared_edges = sorted(set(found) - set(declared))
        # THE ANCHOR IS CHECKED AGAINST THE FILE, NOT AGAINST THE MATCHING LINE: an anchor names
        # the line the edge RESOLVED TO (usually cabinet_root.log_dir/…, which is exactly the line
        # the edge predicate no longer matches -- that is the point of migrating it).
        missing_anchor = []
        for f, e in declared.items():
            if f not in found or not e.get("anchor"):
                continue
            try:
                _text = open(os.path.join(HERE, f), encoding="utf-8").read()
            except OSError:
                missing_anchor.append(f)
                continue
            if e["anchor"] not in _text:
                missing_anchor.append(f)
        check(not undeclared_edges,
              f"every live log-path construction in the tree is DECLARED ({len(declared)} entries, "
              f"{len(found)} file(s) construct one)", "\n".join(undeclared_edges))
        check(not missing_anchor,
              "and every declared anchor is still the line it named -- an edge that changes shape "
              "without re-declaring itself FAILS", "\n".join(missing_anchor))
        back = [m["file"] for m in man.get("migrated", [])
                if m["file"] in found and not m["file"].endswith("test_declared_root.py")]
        check(not back,
              "and no file listed as MIGRATED has started constructing a log path again "
              "(a revert cannot pass quietly)", "\n".join(back))
        check(man.get("declares") == "DECISION_logs_are_scratch.md"
              and os.path.exists(os.path.join(HERE, man["declares"])),
              "the manifest names the decision and the decision is in the tree")
        statuses = sorted({e.get("status", "?") for e in man.get("edges", [])})
        print(f"         edge statuses: {', '.join(statuses)}")
        print(f"         migrated: {len(man.get('migrated', []))} edge(s) now resolve through "
              f"cabinet_root.log_dir()/log_for()")

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
