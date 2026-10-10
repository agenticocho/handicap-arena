#!/usr/bin/env python3
# freeze.py -- THE FREEZE.  Standing demand E: write the contract, then FREEZE
# it BEFORE any entrant runs, WITH A DIGEST.
#
# "Frozen" is a claim this repository has no reason to trust on its own word,
# so it is enforced instead of asserted:
#
#   * `python3 freeze.py`            writes FROZEN.json: the sha256 of the
#                                    contract, of every normative code file,
#                                    of every level, and a combined digest.
#   * `python3 freeze.py --check`    recomputes and compares.  Exit 1 if the
#                                    tree is not the frozen tree.
#   * the RUNNER calls verify() before it will run a single entrant, and
#                                    refuses with EXIT_NOT_FROZEN (6).
#
# So "frozen before any entrant ran" is not a sentence in a report; it is a
# precondition of the run, and a control in the self-test perturbs a copy and
# watches the refusal fire.
#
# The freeze also carries the DECISION REGISTER: every [U<n>]/[A<n>] marker in
# the normative code must appear in the contract and vice versa.  A decision
# the code made and the contract does not mention is a decision nobody
# recorded, which is exactly what standing rule E exists to prevent.
#
# Stdlib only.

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

CONTRACT = os.path.join(HERE, "CONTRACT_DIGDUG.md")
RECORD = os.path.join(HERE, "FROZEN.json")

#: The normative set: everything a re-implementation would have to agree with
#: to reproduce a number in a bundle.  A file that is not in this list cannot
#: change what the cabinet measures, and if it can, it belongs in this list.
NORMATIVE = (
    ("CONTRACT_DIGDUG.md", "the contract (standing demand E)"),
    ("digdug_reader.py", "the read grammar -- the answer shape and the "
                         "frozen abstention list"),
    ("digdug.py", "the transition function, the turn order, the facets"),
    ("digdug_solve.py", "the solver that proves the optima and the counts"),
    ("digdug_run.py", "the runner and the SCORER -- which code produced "
                      "the verdict"),
    ("tasks/digdug_v1.json", "the item set, with the proven optima"),
    ("levels/01_first_blood.txt", "level 01"),
    ("levels/02_the_long_way_round.txt", "level 02"),
    ("levels/03_the_open_door.txt", "level 03"),
    ("levels/04_no_safe_line.txt", "level 04 -- CONTROL, not scored"),
)

_MARKER = re.compile(r"\[(U\d+|A\d+)\]")


def sha256_file(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def digests():
    out = {}
    for rel, _role in NORMATIVE:
        out[rel] = sha256_file(os.path.join(HERE, rel))
    return out


def combined(digs=None):
    digs = digs or digests()
    blob = "\n".join("%s %s" % (k, digs[k]) for k in sorted(digs))
    return sha256_bytes(blob.encode("utf-8"))


def markers_in_text(text):
    return sorted(set(_MARKER.findall(text)))


def markers():
    """The decision register, from the code and from the contract."""
    code = set()
    for rel, _role in NORMATIVE:
        if rel.endswith(".py"):
            p = os.path.join(HERE, rel)
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    code.update(_MARKER.findall(fh.read()))
            except OSError:
                pass
    doc = set()
    try:
        with open(CONTRACT, "r", encoding="utf-8") as fh:
            doc.update(_MARKER.findall(fh.read()))
    except OSError:
        pass
    return {
        "code": sorted(code),
        "contract": sorted(doc),
        "in_code_not_contract": sorted(code - doc),
        "in_contract_not_code": sorted(doc - code),
        "n_decisions_recorded": len(code | doc),
    }


def token_block_state():
    import digdug_reader
    agrees, detail = digdug_reader.contract_agrees_with_code(CONTRACT)
    return {"agrees": agrees, "count": len(digdug_reader.GIVE_UP_TOKENS),
            "why": detail.get("why"),
            "uniqueness_problems": detail.get("uniqueness_problems"),
            "in_code_not_contract": detail.get("in_code_not_contract", []),
            "in_contract_not_code": detail.get("in_contract_not_code", [])}


def build_record():
    digs = digests()
    return {
        "event": "DIG DUG",
        "cabinet": "digdug/",
        "frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": "WRITTEN BEFORE ANY ENTRANT RAN.  The runner refuses to run "
                "unless verify() passes, so this file is a precondition of "
                "every bundle, not a description of it.",
        "contract_path": "digdug/CONTRACT_DIGDUG.md",
        "contract_sha256": digs.get("CONTRACT_DIGDUG.md"),
        "combined_digest": combined(digs),
        "digest_of": "sha256 over the sorted 'path sha256' lines of every "
                     "normative file below",
        "files": [{"path": rel, "role": role, "sha256": digs.get(rel)}
                  for rel, role in NORMATIVE],
        "decision_register": markers(),
        "abstention_tokens": token_block_state(),
    }


def write_record(path=RECORD):
    rec = build_record()
    tmp = path + ".partial"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)
    return rec


def read_record(path=RECORD):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def verify(path=RECORD):
    """-> (ok, why).  The runner will not start an entrant unless this is ok."""
    rec = read_record(path)
    if rec is None:
        return False, "NO FREEZE RECORD: %s does not exist -- run freeze.py" % path
    now = digests()
    bad = []
    for f in rec.get("files", []):
        cur = now.get(f["path"])
        if cur != f["sha256"]:
            bad.append("%s (frozen %s, now %s)" % (f["path"],
                                                   (f["sha256"] or "")[:12],
                                                   (cur or "MISSING")[:12]))
    missing = [rel for rel, _r in NORMATIVE
               if rel not in {f["path"] for f in rec.get("files", [])}]
    if missing:
        bad.append("normative files added since the freeze: %s" % missing)
    if rec.get("combined_digest") != combined(now):
        bad.append("combined digest differs")
    tk = token_block_state()
    if not tk["agrees"]:
        bad.append("R1: the contract's abstention list != the code's (%s)"
                   % tk["why"])
    mk = markers()
    if mk["in_code_not_contract"]:
        bad.append("decisions in the code the contract does not record: %s"
                   % mk["in_code_not_contract"])
    if bad:
        return False, "NOT FROZEN: " + "; ".join(bad)
    return True, "frozen: combined %s" % rec["combined_digest"][:16]


# ---------------------------------------------------------------------------
# the token block: generated FROM the code, so the document cannot drift
# ---------------------------------------------------------------------------

_START = "<!-- ABSTENTION-TOKENS:START -->"
_END = "<!-- ABSTENTION-TOKENS:END -->"


def write_tokens(contract_path=CONTRACT):
    import digdug_reader
    try:
        with open(contract_path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return False
    if _START not in text or _END not in text:
        return False
    body = ["# generated from digdug_reader.GIVE_UP_TOKENS by freeze.py",
            "# --write-tokens.  Do not edit by hand: the runner compares",
            "# this block to the code's scored list (standing rule R1)."]
    body += ["`%s`" % t for t in digdug_reader.GIVE_UP_TOKENS]
    block = _START + "\n" + "\n".join(body) + "\n" + _END
    new = text.split(_START, 1)[0] + block + text.split(_END, 1)[1]
    if new != text:
        with open(contract_path, "w", encoding="utf-8") as fh:
            fh.write(new)
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="freeze the DIG DUG contract")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write-tokens", action="store_true")
    a = ap.parse_args(argv)
    if a.write_tokens:
        ok = write_tokens()
        print("token block %s" % ("regenerated" if ok else "NOT WRITTEN -- "
                                  "the contract has no marked block"))
        return 0 if ok else 1
    if a.check:
        ok, why = verify()
        print(why)
        return 0 if ok else 1
    rec = write_record()
    print("FROZEN at %s" % rec["frozen_at"])
    print("  contract  %s" % rec["contract_sha256"])
    print("  combined  %s" % rec["combined_digest"])
    print("  decisions recorded: %d  (code %d, contract %d)" % (
        rec["decision_register"]["n_decisions_recorded"],
        len(rec["decision_register"]["code"]),
        len(rec["decision_register"]["contract"])))
    print("  abstention tokens: %d, lists agree: %s" % (
        rec["abstention_tokens"]["count"],
        rec["abstention_tokens"]["agrees"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
