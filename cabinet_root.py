#!/usr/bin/env python3
"""THE DECLARED ROOT, IN ONE PLACE -- and the writer REFUSES rather than falls back.

WHAT THIS REPLACES, and the line it replaces was measured before it was removed
(CABINET_STRUCTURE.md, addendum 2026-10-14; verified at origin/main):

    run_card.py:34   ARENA   = os.path.dirname(os.path.abspath(__file__))
    run_card.py:36   RESULTS = os.path.join(ARENA, "results")      # derived, not overridable
    run_card.py:37   MODELS  = os.environ.get("ARENA_MODELS") or ...

    The comment above those lines read "PORTABLE. Derived from this file, overridable by
    environment." MODELS and SERVER were overridable by environment. RESULTS was not.

    ARENA derives from THIS SCRIPT'S OWN LOCATION, so in a worktree the results root WAS that
    worktree's results/ -- inside a git tree, matched by the sweeps, excluded by nothing.
    A DESCRIPTION STANDING WHERE A MECHANISM SHOULD BE.

THE MECHANISM, in four parts, and each part is deliberate.

 1. THE DECLARATION IS CARRIED BY THE REPOSITORY, NOT BY ANYONE'S MEMORY.

        git config --local arena.cabinetResults /home/chilly1/workspace/cabinet_results

    That config lives in the git COMMON dir -- the one directory every worktree of this repo
    SHARES and none of them contains (verified: `git rev-parse --git-common-dir` from main and
    from all three cabinet worktrees returns the same path). So the declaration is the SAME for
    all four trees and OUTSIDE all four of them, and it is read from git at run time, every time.
    A rule you must remember is a rule that will be missed.

    CABINET_RESULTS overrides it for a single invocation (another machine, a test).

 2. WHICH CABINET IS WHOSE: THE WORKTREE'S OWN BRANCH.

        cabinet/sokoban -> <ROOT>/sokoban      main -> <ROOT>/main

    One definition (the branch), and no second copy of the mapping. A detached HEAD is refused
    rather than guessed at.

 3. AND IT REFUSES RATHER THAN FALLS BACK. No declaration -- or a declaration that resolves
    INSIDE a git working tree, or inside the repository's own git directory -- is a REFUSAL: exit
    non-zero, nothing written, the remedy named.

        THE FALLBACK TO <worktree>/results IS THE DEFECT.

    A fallback that works silently is how a declared root becomes decorative: every run succeeds,
    nothing complains, and the results land in the matchable tree. Note that the environment
    override is checked against the same rule, so `CABINET_RESULTS=<worktree>/results` is refused
    too -- the override moves WHERE the root is, never WHETHER it may be in a git tree.

 4. THE SWEEPS' DOMAIN IS DECLARED TOO -- see domain(). It is a LIST, not a walk: the live
    subtrees under the declared root plus the one legacy record declared in place below. No
    sweep finds its scope by globbing `results/` wherever it happens to be sitting, and none of
    it is found by recursion.

READ IT BACK:  python3 cabinet_root.py       (prints the resolution, the domain, and the refusals)
               python3 test_declared_root.py (the free controls)
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# THE TWO CARRIERS OF THE ONE DECLARATION. Same value, same meaning: the ROOT.
DECLARED_ENV = "CABINET_RESULTS"
DECLARED_KEY = "arena.cabinetResults"
HOWTO = f"declare it once, for the whole repo:  git config --local {DECLARED_KEY} <root>"
# BY NAME, NOT BY LINE NUMBER. The first version of this constant read "CABINET_STRUCTURE.md:30-33",
# and the commit that landed it also EDITED that file -- so the coordinate was stale the moment it
# was written: A LINE NUMBER RESOLVES TO WHATEVER SITS THERE WHEN IT IS READ. A refusal has to send
# its reader to a sentence that will still say the same thing next week.
DOC = ("CABINET_STRUCTURE.md, rule 2 ('ONE OWNER PER FILE' -- the block that names "
       "/home/chilly1/workspace/cabinet_results/<cabinet>/) and its 2026-10-14 addendum, "
       "'WHAT THE MECHANISM MUST BE'")

# --------------------------------------------------------------- THE DOMAIN, DECLARED
# LEGACY, DECLARED IN PLACE. The standing card's record was written before this rule existed and
# it is TRACKED, so it is EVIDENCE rather than litter -- 520 files. It sits inside a git tree, and
# it is named here rather than "solved" by a walk, so the sweeps still count it. Its bytes do not
# move; what changed is that no RUN writes new results into it any more.
LEGACY_RECORD = "/home/chilly1/workspace/ocho_arena/results"
LEGACY_WHY = ("the standing card's record, written before the declaration existed; TRACKED -- 520 "
              "files under it, 317 of them *.json at its top level, all one tree object (0bcaaa01) "
              "-- so declared in place rather than moved")
# AND THE OTHER THREE ARE THE SAME TREE OBJECT, NOT THREE MORE RECORDS. `git rev-parse
# <ref>:results` returns 0bcaaa0188b35f0bdd17e3ca824a977cac2d94a1 for main and for all three
# cabinet branches -- so the 520 x 3 in the cabinet worktrees are DUPLICATE COPIES of the same
# tree. Counting them would multiply the record by four and change a published number without
# changing a single bundle; they are therefore declared as duplicates and kept OUT of the domain.
# test_declared_root.py re-measures that equality: while it holds they are copies, and if it ever
# stops holding the declaration has to be re-decided rather than silently kept.
DUPLICATE_RECORD_TREES = (
    "/home/chilly1/workspace/ocho_arena_cabinets/sokoban/results",
    "/home/chilly1/workspace/ocho_arena_cabinets/missile-command/results",
    "/home/chilly1/workspace/ocho_arena_cabinets/zork/results",
)
DUPLICATE_WHY = ("the same tree object as the legacy record on all four branches (verified with "
                 "git rev-parse <ref>:results), i.e. copies, not additional evidence")

# --------------------------------------------------------------- THE LOGS ARE SCRATCH, DECLARED
# ONE CLASSIFICATION, AND THE DIRECTORY IS THE WHOLE OF IT. logs/ IS SCRATCH.
#
# A RECORD is something a reader may treat as evidence about what happened, whose bytes must not
# move, and which must resolve to a coordinate. A SCRATCH FILE is what a process emits about
# ITSELF while it runs. The difference is not taste and it is not tidiness: IT DECIDES WHETHER A
# WRITE NEEDS A ROOT OUTSIDE EVERY GIT TREE.
#
# AND THE REPOSITORY HAD ALREADY SAID SO, BY MECHANISM, BEFORE THIS BLOCK WAS WRITTEN:
#
#   .gitignore        an ignore rule covering the logs -- a declaration carried by the repo, which
#                     is why a reader can check it (git check-ignore) instead of believing it
#   FINDING 020       "...A LOG IS NOT A RECORD FORMAT, and this result survived by luck."
#   probes/SOKOBAN_RUN_20261009-1247_NEW_LEGEND_RECOVERED_FROM_LOG.json
#                     "THIS RECORD WAS RECOVERED FROM the re-run's log ... the per-turn traces are
#                     LOST, because a log is not a record format" -- i.e. the record that came out
#                     of a log is a record BECAUSE it was re-minted in probes/ WITH its source
#                     named, not because the log is one.
#
# SO THE WRITE DOES NOT MOVE, AND THAT IS THE DECISION RATHER THAN AN OMISSION. A record must sit
# OUTSIDE every git tree because a sweep that can reach it will eventually rewrite it -- that is
# why arena.cabinetResults exists and why results_dir() refuses. Scratch's obligation is the
# INVERSE: it must be unable to ENTER the record. A second declared root for scratch would buy
# nothing the ignore rule does not already buy, and it would buy one thing that is worse than
# nothing: A MISSING SCRATCH DECLARATION WOULD REFUSE A RUN OVER A DIAGNOSTIC FILE. run_card.py's
# own header states the sibling rule -- "SCRATCH, NEVER ABORT" -- and a diagnostic that can stop a
# run is a diagnostic that has been promoted to a gate.
#
# WHAT WAS ACTUALLY WRONG IS TWO THINGS, BOTH MEASURED, AND NEITHER IS THE DIRECTORY:
#
#  1  THE COORDINATE WAS DERIVED FROM THE WRITER'S OWN LOCATION. Measured before this landing:
#     reconcile_and_backfill.py prints "log lines available as SOURCE: 90" run from main and
#     "SOURCE: 0" run from each of the three cabinet worktrees -- ONE DECLARED DOMAIN, THE SAME 64
#     SILENT BUNDLES, AND AN ANSWER THAT DEPENDS ON WHERE THE READER IS SITTING. log_dir(),
#     log_path() and log_for() below are the one definition that removes it.
#
#  2  THE TREE COULD ABSORB A CAPTURE. The ignore rule named ONE EXTENSION, so a capture written
#     with any other one was stageable by `git add -A` -- and nine files under logs/ are TRACKED
#     for exactly that reason. The gap is still live, not historical: scripts/run_guarded.sh
#     writes <workdir>/logs/<UNIT>.out, and `git check-ignore logs/ANYTHING.out` exits non-zero on
#     the commit before this one. The rule is therefore stated FOR THE DIRECTORY (.gitignore now
#     ignores `logs/` whole) rather than for an extension.
LOGS_ARE = "scratch"
LOG_NAME = "card_run.log"

# DECLARED IN PLACE, like the legacy record and for the same reason: their bytes do not move.
# These nine are tracked, so evidence rather than litter -- and ONE OF THEM IS CITED BY PATH IN THE
# PUBLISHED RECORD (FINDINGS/018, FINDINGS/019, NEXT_WINDOW.md, SOKOBAN_VERDICT_1.md all name
# logs/sokoban_rerun.out), so a move would leave four citations with no carrier. Nothing writes
# them; they are the residue of the extension gap above, named here so that "scratch" is not read
# as "disposable": SCRATCH THAT A FINDING CITES IS SCRATCH THAT MUST STILL BE THERE WHEN THE
# FINDING IS READ. Note the qualifier -- the three cabinet branches carry SIX of these nine, not
# nine, so the count is read per tree and never typed.
LEGACY_CAPTURES = (
    "logs/arena_v6.out",
    "logs/cost_probe_wide.out",
    "logs/reasoning_ab.out",
    "logs/sokoban_ab.out",
    "logs/sokoban_first_run.out",
    "logs/sokoban_pop2.out",
    "logs/sokoban_pop3.out",
    "logs/sokoban_repeat.out",
    "logs/sokoban_rerun.out",
)
LEGACY_CAPTURE_WHY = ("captures committed while the ignore rule named an extension (`*.log`) "
                      "instead of the directory; TRACKED, byte-frozen, cited by FINDINGS/018, "
                      "FINDINGS/019, NEXT_WINDOW.md and SOKOBAN_VERDICT_1.md by path -- declared "
                      "in place, and written by nothing")

# THE LEGACY LOG COORDINATE, ALSO DECLARED IN PLACE. Every bundle in the legacy record was written
# by a run in the MAIN worktree -- before the declaration existed, main was the only tree that ran
# -- so the journal that explains those bundles is main's, and it is written down here rather than
# derived from whoever is asking. (It also happens to be the coordinate log_dir() resolves for the
# main worktree today; that equality is a measurement, not the definition.)
LEGACY_LOGS = "/home/chilly1/workspace/ocho_arena/logs"


class Refusal(SystemExit):
    """A refusal IS the short circuit: it costs nothing and it names the remedy.

    Exit code 1, message on stderr, nothing written -- the same shape the game-contract gate uses,
    for the same reason: a warning is not a gate.
    """

    def __init__(self, why):
        super().__init__("REFUSING: " + why)


# --------------------------------------------------------------- git, read but never remembered
def git(*args, repo=HERE):
    """-> stdout.strip(), or None if the command failed or git is absent. Never raises."""
    try:
        p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    except OSError:
        return None
    return p.stdout.strip() if p.returncode == 0 else None


def git_common_dir(repo=HERE):
    """The directory EVERY worktree of this repo shares and NONE of them contains."""
    d = git("rev-parse", "--git-common-dir", repo=repo)
    if not d:
        return None
    return os.path.realpath(d if os.path.isabs(d) else os.path.join(repo, d))


def git_toplevel(path):
    """-> the working tree that `path` sits in, or None if it sits in none.

    The nearest EXISTING ancestor is probed, so a root that does not exist yet is still checked:
    a declaration of a directory that is about to be created inside a git tree is the same defect.
    """
    probe = os.path.abspath(path)
    while probe and not os.path.exists(probe):
        nxt = os.path.dirname(probe)
        if nxt == probe:
            return None
        probe = nxt
    top = git("rev-parse", "--show-toplevel", repo=probe)
    return os.path.realpath(top) if top else None


def git_dirs(repo=HERE):
    """The repo's own git directories: the COMMON dir and THIS worktree's dir.

    `git rev-parse --show-toplevel` does NOT cover these -- inside a git dir it fails outright
    ("this operation must be run in a work tree"), so a root under .git/ would pass the working-tree
    check while sitting in the repository's metadata. Measured, not assumed: that is why this
    function exists.
    """
    out = []
    for arg in ("--git-common-dir", "--git-dir"):
        d = git("rev-parse", arg, repo=repo)
        if d:
            out.append(os.path.realpath(d if os.path.isabs(d) else os.path.join(repo, d)))
    return out


def branch(repo=HERE):
    return git("rev-parse", "--abbrev-ref", "HEAD", repo=repo)


def cabinet(repo=HERE, name=None):
    """WHICH CABINET. The carrier is the worktree's OWN BRANCH -- one definition, no second copy."""
    if name:
        return name
    b = branch(repo)
    if not b or b == "HEAD":
        raise Refusal(
            f"cannot tell which cabinet this worktree is: {repo} is on a detached HEAD, or is not a "
            f"git work tree at all (`git rev-parse --abbrev-ref HEAD` -> {b!r}). Check out the "
            f"worktree's own branch, or pass the name explicitly. NOTHING WAS WRITTEN. ({DOC})")
    return b.split("/")[-1]


def declared_root(repo=HERE, env=None):
    """-> (absolute ROOT, how it was declared). RAISES Refusal. TWO RUNGS AND NO THIRD."""

    env = os.environ if env is None else env
    raw, how = None, None
    if env.get(DECLARED_ENV):
        raw, how = env[DECLARED_ENV], f"{DECLARED_ENV} in the environment"
    else:
        raw = git("config", "--get", DECLARED_KEY, repo=repo)
        if raw:
            how = f"git config --local {DECLARED_KEY}"
    if not raw:
        raise Refusal(
            f"no declared results root. {HOWTO} -- or set {DECLARED_ENV} for one invocation. "
            f"THIS IS THE DEFECT IT REFUSES TO REPEAT: the old fallback was "
            f"<worktree>/results, which is inside a git tree matched by the sweeps and excluded by "
            f"nothing. NOTHING WAS WRITTEN. ({DOC})")

    root = os.path.realpath(os.path.expanduser(raw))
    top = git_toplevel(root)
    if top:
        raise Refusal(
            f"the declared root {root} (from {how}) is INSIDE a git working tree: {top}. A results "
            f"root reachable by a sweep is a results root a sweep will eventually rewrite -- the "
            f"whole point of a separate root is that it is outside every one of them. Declare a "
            f"path outside {top}; the environment override moves WHERE the root is, never WHETHER "
            f"it may sit in a git tree. NOTHING WAS WRITTEN. ({DOC})")
    for gd in git_dirs(repo):
        if root == gd or root.startswith(gd + os.sep):
            raise Refusal(
                f"the declared root {root} (from {how}) is INSIDE the repository's git directory "
                f"{gd}. Results are not repository metadata, and --show-toplevel does not cover this "
                f"case (inside a git dir it fails outright), so it is checked separately rather than "
                f"left to a check that cannot see it. NOTHING WAS WRITTEN. ({DOC})")
    return root, how


def results_dir(repo=HERE, name=None, env=None):
    """<declared ROOT>/<this worktree's cabinet> -- the ONE path a run may write results to."""
    root, _how = declared_root(repo=repo, env=env)
    return os.path.join(root, cabinet(repo=repo, name=name))


# --------------------------------------------------------------- the LOGS: scratch, and resolved
def worktrees(repo=HERE):
    """-> {branch name: that worktree's path}. The carrier is git's own worktree list.

    NOT A SECOND COPY OF THE CABINET MAPPING. The name this returns is matched against
    `cabinet()` -- `branch.split("/")[-1]` -- so `cabinet/sokoban` and a card worktree on
    `wt/<id>` both resolve by the SAME rule that decided where their results went. Read from git
    every time, like the declared root, because a rule you must remember is a rule that will be
    missed.
    """
    out, path = {}, None
    for line in (git("worktree", "list", "--porcelain", repo=repo) or "").splitlines():
        if line.startswith("worktree "):
            path = line.split(" ", 1)[1].strip()
        elif line.startswith("branch ") and path:
            out[line.split(" ", 1)[1].strip().replace("refs/heads/", "")] = os.path.realpath(path)
    return out


def log_dir(repo=HERE):
    """-> <the worktree `repo` sits in>/logs. THE ONE DESTINATION FOR A SCRATCH FILE.

    It is inside a git tree, and for SCRATCH that is the correct place: what keeps a log out of
    the record is not a separate root, it is the ignore rule the repository carries
    (.gitignore ignores `logs/`), which is checkable -- `git check-ignore` -- rather than a
    promise. AND IT NEVER REFUSES. A refusal here would stop a run over a diagnostic file, which
    is the priority inverted; `results_dir()` refuses because a result in a matchable tree IS the
    defect, and this function exists because a log in one is not.

    A path that is not in any git work tree (a copied-out script) falls back to its own directory
    rather than to a refusal -- the same reasoning, stated so that the fallback is deliberate.
    """
    return os.path.join(git_toplevel(repo) or os.path.realpath(repo), "logs")


def log_path(repo=HERE):
    """-> <worktree of repo>/logs/card_run.log -- THE RUN JOURNAL, resolved and never remembered."""
    return os.path.join(log_dir(repo), LOG_NAME)


def log_for(bundle, repo=HERE, env=None):
    """-> the journal the writer of `bundle` wrote, or None if `bundle` is in no declared entry.

    PER BUNDLE, AND THAT IS THE WHOLE ANSWER TO THE READ HALF. The admissible coordinate is not
    "logs/ relative to the reader" -- it is the journal of the tree that OWNS THE BUNDLE'S DOMAIN
    ENTRY, because that is the tree the writer ran in. A cabinet's run writes its bundles under the
    declared root and its journal in the cabinet's own worktree, so a sweep launched from main has
    to resolve ACROSS worktrees or it has no admissible line for a cabinet's bundle at all.

    Two details, both deliberate:
      * the legacy entry resolves to LEGACY_LOGS, declared in place above, NOT to the reader's own
        journal -- otherwise running the same sweep from two trees would answer two ways, which is
        the defect this function removes;
      * the coordinate is DECLARED, so it is returned whether or not a file is there. Whether a
        file exists is a separate measurement (os.path.exists), and a reader that treats "no file
        at the declared coordinate" as "use mine instead" has re-created the defect.
    """
    p = os.path.realpath(os.path.abspath(bundle))
    for kind, base in domain(repo=repo, env=env):
        b = os.path.realpath(os.path.abspath(base))
        if not (p == b or p.startswith(b + os.sep)):
            continue
        if kind == "legacy":
            return os.path.join(LEGACY_LOGS, LOG_NAME)
        mate = kind.split(":", 1)[1]
        for br, wt in sorted(worktrees(repo=repo).items()):
            if br.split("/")[-1] == mate:
                return os.path.join(wt, "logs", LOG_NAME)
        return None
    return None


def domain(repo=HERE, env=None):
    """-> [(kind, path)] THE SWEEPS' DOMAIN. A LIST, AND NEVER A WALK.

    Two kinds of entry, both declared:

      live:<cabinet>  this worktree's own subtree under the root, ALWAYS PRESENT whether or not it
                      exists yet -- a declared path, not a discovered one. The root's other
                      children are added when they exist: nothing but this mechanism can create
                      one, so a child of the declared root is in the record BY CONSTRUCTION.
      legacy          the record declared in place above.

    What is deliberately NOT here: `<worktree>/results` (any of them) and the duplicate copies.
    A directory does not enter the domain by existing; it enters by being declared, which is the
    property the old `os.path.join(HERE, "results")` + `**` glob did not have.
    """
    root, _how = declared_root(repo=repo, env=env)
    mine = cabinet(repo=repo)
    entries, seen = [("live:" + mine, os.path.join(root, mine))], set()
    seen.add(os.path.realpath(entries[0][1]))
    if os.path.isdir(root):
        for child in sorted(os.listdir(root)):
            p = os.path.join(root, child)
            if os.path.isdir(p) and os.path.realpath(p) not in seen:
                seen.add(os.path.realpath(p))
                entries.append(("live:" + child, p))
    entries.append(("legacy", LEGACY_RECORD))
    return entries


def domain_paths(pattern="*.json", recursive=False, repo=HERE, env=None):
    """Every match of `pattern` inside the DECLARED DOMAIN, sorted. Non-recursive by default --
    the same shape the sweeps used, but the scope is declared instead of found."""
    out = []
    for _kind, base in domain(repo=repo, env=env):
        out.extend(glob.glob(os.path.join(base, pattern), recursive=recursive))
    return sorted(out)


def domain_find(*parts, repo=HERE, env=None):
    """-> the first declared entry that holds <parts>, or None. For named records (supersessions)."""
    for _kind, base in domain(repo=repo, env=env):
        p = os.path.join(base, *parts)
        if os.path.exists(p):
            return p
    return None


def in_domain(path, repo=HERE, env=None):
    """Is `path` inside one of the declared entries? The WRITE guard: a sweep may only rewrite
    what its declaration names."""
    p = os.path.realpath(os.path.abspath(path))
    for _kind, base in domain(repo=repo, env=env):
        b = os.path.realpath(os.path.abspath(base))
        if p == b or p.startswith(b + os.sep):
            return True
    return False


def main():
    print("THE DECLARED ROOT, READ BACK FROM THE MECHANISM\n")
    commit = git("rev-parse", "HEAD") or "?"
    print(f"  worktree      {HERE}")
    print(f"  commit        {commit}")
    print(f"  common dir    {git_common_dir()}")
    print(f"  branch        {branch()}")
    try:
        root, how = declared_root()
        cab = cabinet()
        res = results_dir()
    except SystemExit as e:
        print(f"  {e}")
        return 2
    print(f"  declared root {root}")
    print(f"                via {how}")
    print(f"  cabinet       {cab}")
    print(f"  RESULTS       {res}")
    top = git_toplevel(res)
    print(f"  in a git tree {'YES -- ' + str(top) if top else 'no'}"
          f"   <- the defect was: {os.path.join(HERE, 'results')}")
    print(f"  root in tree  {git_toplevel(root) or 'no'}")
    print("\n  THE DOMAIN THE SWEEPS READ (declared, never walked):")
    for kind, base in domain():
        n = len(glob.glob(os.path.join(base, "*.json")))
        print(f"    {kind:16} {n:4} *.json   {base}")
    print("\n  DECLARED IN PLACE (kept out of the domain):")
    for p in DUPLICATE_RECORD_TREES:
        print(f"    duplicate        {p}")
    print(f"\n  legacy: {LEGACY_WHY}")
    print(f"  duplicates: {DUPLICATE_WHY}")
    print(f"\n  THE LOGS ARE {LOGS_ARE.upper()} (DECISION_logs_are_scratch.md), and the coordinate is"
          f"\n  declared PER BUNDLE rather than derived from the reader:")
    print(f"    this worktree    {log_path()}"
          f"   {'(file is there)' if os.path.exists(log_path()) else '(no file there)'}")
    print(f"    legacy record    {os.path.join(LEGACY_LOGS, LOG_NAME)}"
          f"   {'(file is there)' if os.path.exists(os.path.join(LEGACY_LOGS, LOG_NAME)) else '(no file there)'}")
    for kind, base in domain():
        probe = os.path.join(base, "ANY_BUNDLE.json")
        print(f"    {kind:16} -> {log_for(probe)}")
    print(f"  legacy captures in place: {len(LEGACY_CAPTURES)} declared; "
          f"{len((git('ls-files', 'logs', repo=HERE) or '').splitlines())} tracked under logs/ in this tree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
