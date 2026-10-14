#!/usr/bin/env python3
"""CONTROL for scripts/prove_declared_slots_parse.py. READ-ONLY against the repo: it writes NOTHING here.

A control for a guard must not write to the record it guards. Every sandbox below is built in a temp
directory and destroyed; the real repository is only ever READ.

WHAT IT EXISTS FOR. Ocho's standing request: *keep the property that the guard goes RED when the contract
and the gate disagree -- if it can pass while they drift, it is a caption.* A check that cannot fail is
decoration, and this repository has paid for that lesson more than once. So the guard is run against five
constructed worlds, and the assertion is on BOTH the exit code and the STATE line:

  1 BASELINE              faithful copy of the repo           -> SINGLE SOURCE, exit 0
  2 STALE LITERAL         check hardcodes a dict missing the  -> BLOCKED, exit 1
                          new key while still exposing a parser
  3 NO PARSER             check enforces a copy that MATCHES   -> DRIFTABLE, exit 1
                          the contract but no longer parses it
  4 MARKERS MISSING       contract's marker block is gone      -> BLOCKED, exit 1
  5 ZERO SLOTS            markers present, body empty          -> BLOCKED, exit 1

CASE 2 IS THE ONE THAT MATTERS MOST, and it is a real bug this guard had: the first version asked the
module for `parse_declared_slots()` and compared THAT against the contract. A module that exposes a parser
but ENFORCES a hardcoded literal would therefore have been reported green while the gate refused every
bundle -- the guard passing while the thing it guards drifted. Case 2 is the regression test for that.

    python3 scripts/test_declared_slots_guard.py
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)                      # root scripts: already sys.path[0]; scripts/*: required
import cabinet_root as _root


def scope(pattern="*.json"):
    """[(kind, base, [paths])] over the DECLARED domain, entry by entry. No pattern is widened,
    no directory joins by existing."""
    rows = []
    for kind, base in _root.domain():
        rows.append((kind, base, sorted(glob.glob(os.path.join(base, pattern)))))
    return rows


def print_scope(rows, pattern):
    # THE SCOPE IS PRINTED WITH THE COUNT IT CONTRIBUTED: a count without its scope is not a count.
    for kind, base, hits in rows:
        print(f"  scope  {kind:16} {len(hits):4} {pattern}  {base}")

GUARD = os.path.join(HERE, "scripts", "prove_declared_slots_parse.py")
CHECK = "test_game_states.py"

STALE_LITERAL = '''DECLARED_SLOTS = {
    "R1_fencing": "structured-output conformance (schema strictness, scalar types, sequences)",
    "R2_chess": "tool selection (the right call, and the reflex to abstain)",
    "R3_pitstop": "code repair (a fix that breaks the other cases scores zero)",
}'''

MATCHING_LITERAL = '''DECLARED_SLOTS = {
    "R1_fencing": "structured-output conformance (schema strictness, scalar types, sequences)",
    "R2_chess": "tool selection (the right call, and the reflex to abstain)",
    "R3_pitstop": "code repair (a fix that breaks the other cases scores zero)",
    "R1_conformance": "structured-output conformance -- the representation of absence (v6, neutral key)",
}'''


def build_sandbox(mutate_check=None, mutate_contract=None):
    """A faithful miniature of the repo: contract, check, its imports, the DECLARATION, results, guard.

    A MINIATURE THAT CANNOT DECLARE A ROOT IS NOT A MINIATURE OF THIS REPO. Every reader here --
    the guard under test, and the check it adjudicates -- resolves its scope through
    cabinet_root.domain(), and domain() REFUSES without a declaration. So the sandbox carries the
    same three things the real tree carries, and only these three:

      * the one declaration                      `cabinet_root.py`
      * a WORK TREE, because the cabinet is resolved from the BRANCH and from nothing else
      * a DECLARED ROOT OUTSIDE that work tree   `CABINET_RESULTS` for the one invocation

    The first version carried none of them, and the two controls it was built to prove went red for
    that reason rather than for a drift: the checker could not import, so the check enforced
    ABSENT and every world answered BLOCKED. A fixture that fails everything for one reason it does
    not name is a caption in the other direction.
    """
    d = tempfile.mkdtemp(prefix="slotctl-")
    root = tempfile.mkdtemp(prefix="slotroot-")          # the DECLARED ROOT: outside every git tree
    os.makedirs(os.path.join(d, "scripts"))
    os.makedirs(os.path.join(d, "results"))
    subprocess.run(["git", "init", "-q", "-b", "main", d], check=True)
    # AN UNBORN BRANCH HAS NO NAME TO READ: `rev-parse --abbrev-ref HEAD` fails until there is a
    # commit, and cabinet_root refuses a work tree whose cabinet it cannot tell. One empty commit.
    subprocess.run(["git", "-C", d, "-c", "user.name=fixture", "-c", "user.email=fixture@invalid",
                    "commit", "-q", "--allow-empty", "-m", "fixture"], check=True)
    live = os.path.join(root, "main")                    # domain() -> live:<branch under the root>
    os.makedirs(live)

    shutil.copy2(os.path.join(HERE, "GAME_CONTRACT.md"), d)
    shutil.copy2(os.path.join(HERE, "annotate_superseded.py"), d)
    # THE MINIATURE CARRIES THE ONE DECLARATION. Every reader here -- the guard under test and the
    # check it adjudicates -- imports cabinet_root; a sandbox without it does not run the thing it
    # is a sandbox FOR, it dies on the import and reports an ImportError where a drift belongs.
    shutil.copy2(os.path.join(HERE, "cabinet_root.py"), d)
    shutil.copy2(GUARD, os.path.join(d, "scripts"))

    check_src = open(os.path.join(HERE, CHECK), encoding="utf-8").read()
    if mutate_check:
        check_src = mutate_check(check_src)
    with open(os.path.join(d, CHECK), "w", encoding="utf-8") as f:
        f.write(check_src)

    if mutate_contract:
        cpath = os.path.join(d, "GAME_CONTRACT.md")
        with open(cpath, encoding="utf-8") as f:
            ctext = f.read()
        with open(cpath, "w", encoding="utf-8") as f:
            f.write(mutate_contract(ctext))

    # one real v6 bundle, so the guard has round keys to adjudicate. THE SOURCE MOVES TO THE DECLARED
    # DOMAIN; the sandbox's own `results` (built above, inside d/) is the FIXTURE's and stays.
    _src = None
    for _kind, _base, _hits in scope("*cardv6*.json"):
        if _hits:
            _src = _hits[0]
            break
    if _src:
        # THE FIXTURE'S OWN `results` (built above, inside d/), NOT A SECOND ENTRY IN THE DOMAIN: the
        # domain ALWAYS carries the real `legacy` record, so a copy under `live:main` would put the
        # same basename in two entries -- and the guard under test refuses that as a basename
        # collision, which a fixture must not manufacture.
        shutil.copy2(_src, os.path.join(d, "results", os.path.basename(_src)))
    return d, root


def run_guard(sandbox, root):
    # ONE DECLARATION, FOR ONE INVOCATION: the sandbox is a tree of its own, and its scope must be
    # its own -- otherwise the guard under test would be reading the real record from a fixture.
    env = dict(os.environ, CABINET_RESULTS=root)
    r = subprocess.run([sys.executable,
                        os.path.join(sandbox, "scripts", "prove_declared_slots_parse.py")],
                       capture_output=True, text=True, cwd=sandbox, env=env)
    return r.returncode, r.stdout + r.stderr


def state_of(out):
    for line in out.splitlines():
        if line.startswith("STATE:"):
            return line.split(".", 1)[0].replace("STATE:", "").strip()
    return "(no STATE line)"


def main():
    fails = []
    total = 0

    def ck(name, got, want):
        nonlocal total
        total += 1
        ok = got == want
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            print(f"          got  {got!r}\n          want {want!r}")
            fails.append(name)

    print("=" * 98)
    print("CONTROL -- the declared-slots guard must be able to PASS and able to FAIL")
    print("=" * 98)

    cases = [
        ("[1] BASELINE: the repo as it stands -> GREEN",
         dict(), "SINGLE SOURCE", 0),
        ("[2] THE GUARD'S OWN BUG: parser exposed, literal enforced, key missing -> RED",
         dict(mutate_check=lambda s: s.replace("DECLARED_SLOTS = parse_declared_slots()",
                                               STALE_LITERAL)), "BLOCKED", 1),
        ("[3] NO PARSER: copies agree today but nothing keeps them in step -> RED",
         dict(mutate_check=lambda s: s.replace("def parse_declared_slots(",
                                               "def _retired_parse_declared_slots(")
              .replace("DECLARED_SLOTS = parse_declared_slots()", MATCHING_LITERAL)),
         "DRIFTABLE", 1),
        ("[4] MARKERS MISSING from the contract -> RED",
         dict(mutate_contract=lambda t: t.replace("=== DECLARED_SLOTS BEGIN ===", "=== GONE ===")),
         "BLOCKED", 1),
        ("[5] ZERO SLOTS between the markers -> RED",
         dict(mutate_contract=lambda t: t.split("=== DECLARED_SLOTS BEGIN ===")[0]
              + "=== DECLARED_SLOTS BEGIN ===\n=== DECLARED_SLOTS END ===\n"
              + t.split("=== DECLARED_SLOTS END ===")[-1]),
         "BLOCKED", 1),
    ]

    for name, kw, want_state, want_rc in cases:
        d, root = build_sandbox(**kw)
        try:
            rc, out = run_guard(d, root)
            got = (state_of(out), rc)
            ck(name, got, (want_state, want_rc))
            if got != (want_state, want_rc):
                print(f"        --- guard output ---")
                for line in out.strip().splitlines()[-12:]:
                    print(f"        {line}")
        finally:
            shutil.rmtree(d, ignore_errors=True)
            shutil.rmtree(root, ignore_errors=True)

    print()
    print("=" * 98)
    print(f"{'ALL CONTROLS PASS' if not fails else str(len(fails)) + ' FAILED'}   --  "
          f"{total - len(fails)}/{total}")
    print("=" * 98)
    if not fails:
        print("THE GUARD CAN FAIL. Cases 2-5 are four different drifts and each one goes red, so a red")
        print("from this guard is a real signal rather than noise -- which is what it was asked to be.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
