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
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    """A faithful miniature of the repo: contract, check, its import, results, and the guard."""
    d = tempfile.mkdtemp(prefix="slotctl-")
    os.makedirs(os.path.join(d, "scripts"))
    os.makedirs(os.path.join(d, "results"))

    shutil.copy2(os.path.join(HERE, "GAME_CONTRACT.md"), d)
    shutil.copy2(os.path.join(HERE, "annotate_superseded.py"), d)
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

    # one real v6 bundle, so the guard has round keys to adjudicate
    for name in sorted(os.listdir(os.path.join(HERE, "results"))):
        if "cardv6" in name and name.endswith(".json"):
            shutil.copy2(os.path.join(HERE, "results", name),
                         os.path.join(d, "results", name))
            break
    return d


def run_guard(sandbox):
    r = subprocess.run([sys.executable,
                        os.path.join(sandbox, "scripts", "prove_declared_slots_parse.py")],
                       capture_output=True, text=True, cwd=sandbox)
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
        d = build_sandbox(**kw)
        try:
            rc, out = run_guard(d)
            got = (state_of(out), rc)
            ck(name, got, (want_state, want_rc))
            if got != (want_state, want_rc):
                print(f"        --- guard output ---")
                for line in out.strip().splitlines()[-12:]:
                    print(f"        {line}")
        finally:
            shutil.rmtree(d, ignore_errors=True)

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
