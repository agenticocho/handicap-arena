#!/usr/bin/env python3
"""stump_task_selftest.py -- does the shape check actually fire?

A validator that cannot reject anything is the defect the STUMP ruling names as a test whose null
cannot occur. So the check is checked: five mutants, each one violation the shape exists to prevent,
and the validator must reject every one and accept the unmutated template.
"""
import copy
import json
import subprocess
import sys

GEN = "probes/stump_task_gen.py"


def run(payload):
    p = subprocess.run([sys.executable, GEN, "--check"], input=json.dumps(payload),
                       capture_output=True, text=True)
    return p.returncode, p.stdout.strip().splitlines()


base = json.loads(subprocess.run([sys.executable, GEN, "--emit"], capture_output=True, text=True).stdout)

cases = {}


def case(name, fn):
    t = copy.deepcopy(base)
    fn(t)
    cases[name] = t


def drop_A(t):
    t["rounds"][0]["questions"]["A"][0].pop("A")


def merge_accuracy(t):
    t["rounds"][0]["result"]["accuracy"] = 0.9


def unreachable(t):
    t["params"].update({"n": 3, "p_ref": 0.70, "A": 2})
    t["rounds"][0]["questions"]["A"] = t["rounds"][0]["questions"]["A"][:3]
    t["rounds"][0]["questions"]["B"] = t["rounds"][0]["questions"]["B"][:3]
    for side in ("A", "B"):
        for q in t["rounds"][0]["questions"][side]:
            q["A"] = 2
    t["params"]["ceiling"]["P_coin_wins"] = 0.0


def leak_answer(t):
    t["rounds"][0]["questions"]["A"][0]["text"] = "what is 3 + 4, that is 7"


def one_counter(t):
    t["rounds"][0]["answers"]["panel-1"]["A-1"].pop("malformed")


def wrong_ceiling(t):
    t["params"]["ceiling"]["P_coin_wins"] = 0.05


for n, f in [("A not declared on a question", drop_A),
             ("merged accuracy field", merge_accuracy),
             ("tolerance unreachable at n=3 p=0.70 A=2", unreachable),
             ("answer leaked into question text", leak_answer),
             ("one merged counter", one_counter),
             ("declared ceiling disagrees with closed form", wrong_ceiling)]:
    case(n, f)

ok = True
rc, out = run(base)
print("CONTROL (unmutated) rc=%d last=%r" % (rc, out[-1] if out else ""))
if rc != 0:
    ok = False
    print("  CONTROL FAILED -- the validator rejects valid work")

for name, t in cases.items():
    rc, out = run(t)
    vios = [l for l in out if l.startswith("VIOLATION")]
    print("MUTANT %-46s rc=%d violations=%d %s" % (name, rc, len(vios), "REJECTED" if rc != 0 else "ACCEPTED <-- BAD"))
    if rc == 0:
        ok = False
    else:
        print("        %s" % vios[0][:150])

print("SELFTEST %s" % ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
