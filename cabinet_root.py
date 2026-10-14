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
DOC = "CABINET_STRUCTURE.md:30-73 (addendum 2026-10-14) and :22 (the root itself)"

# --------------------------------------------------------------- THE DOMAIN, DECLARED
# LEGACY, DECLARED IN PLACE. The standing card's record was written before this rule existed and
# it is TRACKED, so it is EVIDENCE rather than litter -- 520 files. It sits inside a git tree, and
# it is named here rather than "solved" by a walk, so the sweeps still count it. Its bytes do not
# move; what changed is that no RUN writes new results into it any more.
LEGACY_RECORD = "/home/chilly1/workspace/ocho_arena/results"
LEGACY_WHY = ("the standing card's record, written before the declaration existed; TRACKED (520 "
              "files, tree 0bcaaa01), so declared in place rather than moved")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
