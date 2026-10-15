#!/usr/bin/env python3
"""CONTROL for scripts/prove_declared_slots_parse.py. READ-ONLY against the repo: it writes NOTHING here.

A control for a guard must not write to the record it guards. Every sandbox below is built in a temp
directory and destroyed; the real repository is only ever READ.

WHAT IT EXISTS FOR. Ocho's standing request: *keep the property that the guard goes RED when the contract
and the gate disagree -- if it can pass while they drift, it is a caption.* A check that cannot fail is
decoration, and this repository has paid for that lesson more than once. So the guard is run against five
constructed worlds, and the assertion is on the exit code, the STATE line, AND the record the guard read:

  1 BASELINE              the fixture's OWN record (hermetic)    -> SINGLE SOURCE, exit 0
  2 STALE LITERAL         check hardcodes a dict missing the     -> BLOCKED, exit 1
                          new key while still exposing a parser
  3 NO PARSER             check enforces a copy that MATCHES      -> DRIFTABLE, exit 1
                          the contract but no longer parses it
  4 MARKERS MISSING       contract's marker block is gone         -> BLOCKED, exit 1
  5 ZERO SLOTS            markers present, body empty             -> BLOCKED, exit 1

AND EVERY CASE IS A TRIPLE, THE THIRD ELEMENT BEING WHAT THE GUARD READ. The expectation is
(state, exit code, [(entry kind, bundle name)]) and the third element is the same two fixture-owned
bundles in all five worlds. THAT ELEMENT IS WHAT THE LAST REVISION OF THIS FILE IS FOR (card
t_af7ee63b). `cabinet_root.domain()` appends a `legacy` entry UNCONDITIONALLY -- the Chair's single
definition, not renegotiated here -- and that entry is the real record, so an earlier revision of this
fixture had the guard adjudicate the REPOSITORY's round keys while every case here claimed to be about a
temp directory. Case 1 was then green as a statement about the repo as it stood rather than about the
sandbox, and it could go red for a reason no case made: the record carrying an undeclared round key. The
fixture now carries its OWN legacy record (build_sandbox says how), and the third element is the
measurement rather than the promise -- if a sandbox ever reads a byte that is not its own, every one of
the five cases fails and names the entry it read.

CASE 2 IS THE ONE THAT MATTERS MOST, and it is a real bug this guard had: the first version asked the
module for `parse_declared_slots()` and compared THAT against the contract. A module that exposes a parser
but ENFORCES a hardcoded literal would therefore have been reported green while the gate refused every
bundle -- the guard passing while the thing it guards drifted. Case 2 is the regression test for that.

    python3 scripts/test_declared_slots_guard.py
"""
import glob
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)                      # root scripts: already sys.path[0]; scripts/*: required
import cabinet_root as _root

# THE FIXTURE'S BYTES ARE NAMED AS THE FIXTURE'S. One prefix, declared once, so that nothing built here can
# be mistaken for a record: a reader who sees FIXTURE_ONLY_ in a path knows it is this file's, not the
# repo's. THE TWO NAMES DIFFER ON PURPOSE: the guard under test REFUSES a basename appearing in two domain
# entries (AC2(b)), so a fixture that reused one name across its own two entries would go red for a
# collision the fixture manufactured -- the defect the card names, made worse.
FIXTURE_ONLY = "FIXTURE_ONLY_"
PATTERN = "*cardv6*.json"                            # what the guard under test adjudicates
LIVE_BUNDLE = FIXTURE_ONLY + "cardv6.json"           # -> the sandbox's `live:main` entry
LEGACY_BUNDLE = FIXTURE_ONLY + "cardv6_legacy.json"  # -> the sandbox's `legacy` entry
# THE SAME DECLARATION THE GUARD HAS TO RESOLVE: one `live` entry for the sandbox's own branch, one
# `legacy` entry, and no third thing. Typed here so a case's third element is a literal rather than a
# comparison against itself, and read back from the sandbox's declaration by read_record() below.
OWN_RECORD = sorted([("live:main", LIVE_BUNDLE), ("legacy", LEGACY_BUNDLE)])


def scope(pattern=PATTERN):
    """[(kind, base, [paths])] over the REAL declared domain, entry by entry. This is where the fixture's
    SOURCE bundle comes from -- the declared domain, never `<worktree>/results` (t_fdf55800)."""
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


def bundle_keys(path):
    """-> {round key: how many times} for `path`, read the way the guard under test reads it."""
    try:
        d = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    keys = {}
    for e in (d.get("results") or []):
        for rk in (e.get("rounds") or {}):
            keys[rk] = keys.get(rk, 0) + 1
    return keys


def fixture_source():
    """-> (path, {key: n}) for ONE bundle out of the DECLARED DOMAIN, or (None, None).

    A HIT COUNT IS NOT THE SAME AS ROUND KEYS. The first v6 bundle in the record is not necessarily one
    that carries any: this record holds one such bundle today, and the previous revision of this fixture
    took `hits[0]` without asking. That was survivable only while the real legacy record supplied the keys.
    In a hermetic fixture the fixture's own bytes ARE the keys, so a keyless source is a SILENT ZERO --
    the guard would adjudicate nothing and report SINGLE SOURCE. Ask for the keys, not for the hits.
    """
    for _kind, _base, hits in scope():
        for p in hits:
            keys = bundle_keys(p)
            if keys:
                return p, keys
    return None, None


def build_sandbox(src, mutate_check=None, mutate_contract=None):
    """A faithful miniature of the repo: contract, check, its imports, the DECLARATION, the fixture's own
    record, and the guard.

    A MINIATURE THAT CANNOT DECLARE A ROOT IS NOT A MINIATURE OF THIS REPO. Every reader here -- the guard
    under test, and the check it adjudicates -- resolves its scope through cabinet_root.domain(), and
    domain() REFUSES without a declaration. So the sandbox carries the same three things the real tree
    carries, and only these three:

      * the one declaration                      `cabinet_root.py`
      * a WORK TREE, because the cabinet is resolved from the BRANCH and from nothing else
      * a DECLARED ROOT OUTSIDE that work tree   `CABINET_RESULTS` for the one invocation

    The first version carried none of them, and the two controls it was built to prove went red for that
    reason rather than for a drift: the checker could not import, so the check enforced ABSENT and every
    world answered BLOCKED. A fixture that fails everything for one reason it does not name is a caption
    in the other direction.

    AND A FOURTH THING (t_af7ee63b): THE FIXTURE'S OWN RECORD, DECLARED TO THE SANDBOX'S OWN DECLARATION.
    domain() is REQUIRED to append a `legacy` entry, and it appends it unconditionally -- the Chair's single
    definition, and this fixture does not renegotiate it and adds no fallback to it. What the fixture holds
    is WHERE that entry points: the entry's path is repository DATA (`LEGACY_RECORD`, the standing card's
    record, one absolute path in a tree of this repo), not mechanism, exactly as GAME_CONTRACT.md, the
    check and the bundle are data this fixture already replaces with its own copies. So the copy of the
    declaration the sandbox runs carries the sandbox's own record at `<sandbox>/legacy/` -- INSIDE the
    sandbox's work tree, which is where the real one sits too -- and the fixture's bundle is copied into
    it. The shape of domain() and declared_root() is untouched, and if that declaration ever fails to land
    the cases below do not pass quietly: they FAIL and name the entry they read.

    The live bundle goes to `<declared ROOT>/main`, i.e. into the entry the sandbox's own branch resolves
    to, so the fixture exercises the `live:<cabinet>` arm of the domain and not only the legacy one.
    """
    d = tempfile.mkdtemp(prefix="slotctl-")
    root = tempfile.mkdtemp(prefix="slotroot-")          # the DECLARED ROOT: outside every git tree
    os.makedirs(os.path.join(d, "scripts"))
    subprocess.run(["git", "init", "-q", "-b", "main", d], check=True)
    # AN UNBORN BRANCH HAS NO NAME TO READ: `rev-parse --abbrev-ref HEAD` fails until there is a
    # commit, and cabinet_root refuses a work tree whose cabinet it cannot tell. One empty commit.
    subprocess.run(["git", "-C", d, "-c", "user.name=fixture", "-c", "user.email=fixture@invalid",
                    "commit", "-q", "--allow-empty", "-m", "fixture"], check=True)
    live = os.path.join(root, "main")                    # domain() -> live:<branch under the root>
    os.makedirs(live)
    record = os.path.join(d, "legacy")                   # the sandbox's OWN legacy record
    os.makedirs(record)

    shutil.copy2(os.path.join(HERE, "GAME_CONTRACT.md"), d)
    shutil.copy2(os.path.join(HERE, "annotate_superseded.py"), d)
    # THE MINIATURE CARRIES THE ONE DECLARATION. Every reader here -- the guard under test and the
    # check it adjudicates -- imports cabinet_root; a sandbox without it does not run the thing it
    # is a sandbox FOR, it dies on the import and reports an ImportError where a drift belongs.
    shutil.copy2(os.path.join(HERE, "cabinet_root.py"), d)
    shutil.copy2(GUARD, os.path.join(d, "scripts"))

    # ... AND THE SANDBOX'S DECLARATION CARRIES THE SANDBOX'S RECORD. Appended rather than substituted:
    # LEGACY_RECORD is read as a module global when domain() runs, so rebinding it here is the whole
    # change, and it is a change of DATA (which record this tree's declaration names) and not of shape.
    with open(os.path.join(d, "cabinet_root.py"), "a", encoding="utf-8") as f:
        f.write(
            "\n\n# --- FIXTURE-ONLY (appended by scripts/test_declared_slots_guard.py) ------------------\n"
            "# --- domain() appends the `legacy` entry unconditionally, and in THIS tree that entry is\n"
            "# --- this tree's own record: nothing the fixture builds may make the sandbox read the\n"
            "# --- repository's. The mechanism is untouched; only the path it appends is the fixture's.\n"
            f"LEGACY_RECORD = {record!r}\n")

    shutil.copy2(src, os.path.join(live, LIVE_BUNDLE))
    shutil.copy2(src, os.path.join(record, LEGACY_BUNDLE))

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

    return d, root


def read_record(sandbox, root):
    """-> [(entry kind, bundle name)] THE RECORD THE SANDBOX'S OWN DECLARATION RESOLVES TO.

    THE RESIDUAL, MEASURED PER CASE RATHER THAN ARGUED. The declaration the sandbox runs is loaded BY PATH:
    the repository's cabinet_root is already imported in this process, and asking that one would answer
    about the repository -- which is the question this function exists to stop asking by accident. Names
    and kinds only, so a case's expectation is a literal and not a temp path.
    """
    spec = importlib.util.spec_from_file_location("sandbox_cabinet_root",
                                                 os.path.join(sandbox, "cabinet_root.py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules["sandbox_cabinet_root"] = m
    spec.loader.exec_module(m)
    out = []
    for kind, base in m.domain(env=dict(os.environ, **{_root.DECLARED_ENV: root})):
        out.extend((kind, os.path.basename(p)) for p in glob.glob(os.path.join(base, PATTERN)))
    return sorted(out)


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

    def ck(name, want_state, want_rc, read, rc, out):
        """ONE CASE, ONE CHECK, THREE ASSERTIONS -- and a failure says WHICH one, because the third is
        this file's whole point and a 38-entry repr of the record it read is not a diagnostic."""
        nonlocal total
        total += 1
        state = state_of(out)
        bad_state, bad_rc, bad_record = state != want_state, rc != want_rc, read != OWN_RECORD
        ok = not (bad_state or bad_rc or bad_record)
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if ok:
            return
        if bad_state or bad_rc:
            print(f"          got  ({state!r}, {rc})\n          want ({want_state!r}, {want_rc})")
        if bad_record:
            stray = [f"{k} {n}" for k, n in read if (k, n) not in OWN_RECORD]
            print(f"          THE RECORD THIS CASE READ IS NOT THE FIXTURE'S: {len(read)} bundle(s), "
                  f"{len(stray)} of them not the fixture's --")
            for e in stray[:4]:
                print(f"            {e}")
            if len(stray) > 4:
                print(f"            ... and {len(stray) - 4} more")
            for k, n in OWN_RECORD:
                if (k, n) not in read:
                    print(f"          and an entry the fixture DOES declare is missing: {k} {n}")
        print(f"        --- guard output ---")
        for line in out.strip().splitlines()[-12:]:
            print(f"        {line}")
        fails.append(name)

    print("=" * 98)
    print("CONTROL -- the declared-slots guard must be able to PASS and able to FAIL")
    print("=" * 98)

    # A FIXTURE THAT CANNOT BE BUILT IS NOT FIVE SKIPS. Without a bundle carrying round keys there is
    # nothing for the guard to adjudicate, and it would say SINGLE SOURCE about that nothing: the empty
    # list rule, pointed at this file. So the search is done ONCE, here, and its failure is named.
    src, src_keys = fixture_source()
    if src is None:
        print(f"\nTHE FIXTURE CANNOT BE BUILT, so no case below would be a statement about anything.")
        print(f"  no bundle matching {PATTERN} in the DECLARED DOMAIN carries a round key:")
        print_scope(scope(), PATTERN)
        print("  A fixture with no round keys adjudicates NOTHING and reports SINGLE SOURCE -- the silent")
        print("  zero the empty-list rule exists to refuse. THIS IS A FAILURE, NOT A SKIP.")
        return 1
    print(f"  source      one bundle out of the DECLARED DOMAIN, renamed FIXTURE_ONLY:")
    print(f"                {src}")
    print(f"                keys {sorted(src_keys)} -> {LIVE_BUNDLE} (live entry), "
          f"{LEGACY_BUNDLE} (legacy entry)")
    print(f"  the record every case must READ: {OWN_RECORD}")

    cases = [
        ("[1] BASELINE: the fixture's own record -> GREEN",
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
        d, root = build_sandbox(src, **kw)
        try:
            # READ FIRST, SO THE RECORD THE CASE RAN AGAINST IS PART OF ITS RESULT: a red from a case
            # whose sandbox was not reading its own record says nothing about the mutation.
            read = read_record(d, root)
            rc, out = run_guard(d, root)
            ck(name, want_state, want_rc, read, rc, out)
            # THE GUARD'S OWN SCOPE LINES, ECHOED: it prints the entries it read with the count each
            # contributed, and those two lines are what "the fixture's own record" means in its output.
            for line in out.splitlines():
                if line.strip().startswith("scope "):
                    print(f"        {line.strip()}")
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
        print("AND THE GREEN IS ABOUT THE FIXTURE: every case read the two bundles above and nothing")
        print("else, so case 1 is a statement about a sandbox rather than about the repo as it stands.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
