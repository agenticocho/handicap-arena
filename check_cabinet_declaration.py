#!/usr/bin/env python3
"""
check_cabinet_declaration.py -- verify a cabinet's declaration as a MEASUREMENT, not a claim.

WHY THIS EXISTS
A cabinet declares its runs of record in CABINET_DECLARATION_<cabinet>.md. That declaration is a
CLAIM, and the repo's whole discipline is that a claim is only as good as the check behind it. Two
of its statements are mechanically testable and both are load-bearing:

  1. SUPERSEDED IS CONTAINMENT, NOT JUDGEMENT. "A pilot is not superseded because someone says so --
     it is superseded because its entire content is present in another artifact with identical
     counters and nothing of its own left over." That is four assertions: (a) every (entrant, level)
     key of the superseded file also occurs in the incumbent; (b) the superseded file has no key of
     its own; (c) the counters agree on every shared cell; (d) the incumbent carries at least as
     much. All four are computable.

  2. READ AGAINST THE FREEZE IT NAMES. A run carries the instrument digest it was produced under. A
     file whose digest differs from the current freeze is NOT stale -- it is a measurement of a
     different instrument, and must be reported as such. Collapsing two populations under two
     freezes into one "run of record" line makes a reader read an instrument change as a result.

This script does NOT restate the declaration. It reads the artifacts and reports what it finds, so
that a divergence between claim and artifact SHOWS UP instead of being copied forward.

Exit: 0 all checks agree; 1 a contradiction; 2 unreadable (refuse rather than pass).
"""
import hashlib, json, os, re, sys

ROOT = "/home/chilly1/workspace/ocho_arena"
DECL = os.path.join(ROOT, "CABINET_DECLARATION_sokoban.md")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cells_of(path):
    """A run file's cells in EITHER shape.

    A pilot is {run_id, cells:[...]}. A per-entrant probe is a FLAT single-cell record with no
    'cells' key at all. Reading only 'cells' silently reports a probe as empty -- so both shapes
    are named here rather than assumed.
    """
    d = json.load(open(path))
    if isinstance(d.get("cells"), list):
        return d, d["cells"], "pilot (cells[])"
    if "entrant" in d and "level" in d:
        return d, [d], "per-entrant probe (flat)"
    return d, [], "UNKNOWN SHAPE"


def key_of(c):
    return (c.get("entrant"), c.get("level"))


COUNTERS = ["attempted", "blocked", "not_an_action", "give_up", "ended", "solved", "moves"]


def main():
    if not os.path.exists(DECL):
        print(f"REFUSING: no declaration at {DECL}")
        return 2
    text = open(DECL, encoding="utf-8").read()

    # the declared states, read from the declaration's own table
    declared = {}
    for m in re.finditer(r"\|\s*`(probes/[^`]+)`\s*\|\s*\*\*([A-Z ]+)\*\*\s*\|\s*\*\*([^*]+)\*\*", text):
        declared[m.group(1)] = (m.group(2).strip(), m.group(3).strip())
    if not declared:
        print("REFUSING: could not parse the declaration table -- not guessing at its contents")
        return 2

    print("DECLARED (read from the declaration's table)")
    for p, (state, meaning) in declared.items():
        exists = os.path.exists(os.path.join(ROOT, p))
        print(f"  {p}")
        print(f"    state={state:8s} meaning={meaning[:52]:52s} on_disk={'YES' if exists else 'NO ***'}")

    # --- check 1: superseded is CONTAINMENT ---------------------------------------------
    fails = []
    inc = [p for p, (_, m) in declared.items() if "RUN OF RECORD" in m.upper()]
    sup = [p for p, (_, m) in declared.items() if "superseded" in m.lower()]
    print("\nCHECK 1 -- superseded is containment, not judgement")
    for s in sup:
        if not inc:
            fails.append(f"{s}: nothing declared as incumbent")
            continue
        sd, sc, sshape = cells_of(os.path.join(ROOT, s))
        id_, ic, ishape = cells_of(os.path.join(ROOT, inc[0]))
        sk, ik = {key_of(c) for c in sc}, {key_of(c) for c in ic}
        a_only, shared = sk - ik, sk & ik
        diffs = [k for k in shared
                 if any(c.get(x) != n.get(x) for x in COUNTERS
                        for c in [next(c for c in sc if key_of(c) == k)]
                        for n in [next(n for n in ic if key_of(n) == k)])]
        print(f"  incumbent : {inc[0].split('/')[-1]}  cells={len(ic)}  [{ishape}]")
        print(f"  superseded: {s.split('/')[-1]}  cells={len(sc)}  [{sshape}]")
        print(f"    (a) every key also in incumbent : {'PASS' if not a_only else 'FAIL'}")
        print(f"    (b) nothing of its own left over: {'PASS' if not a_only else f'FAIL {sorted(a_only)}'}")
        print(f"    (c) counters agree on shared    : {'PASS' if not diffs else f'FAIL {sorted(diffs)}'}")
        print(f"    (d) incumbent at least as much  : {'PASS' if len(ic) >= len(sc) else 'FAIL'}")
        print(f"    => containment {'HOLDS' if not (a_only or diffs) else 'FAILS'}; "
              f"summing these two would be {len(ic)+len(sc)} cells where there are {len(ic)}")
        if a_only or diffs or len(ic) < len(sc):
            fails.append(f"{s}: containment fails")

    # --- check 2: every run carries the freeze it was made under -------------------------
    print("\nCHECK 2 -- each population carries its own instrument digest")
    seen = {}
    for p in list(declared) + ["probes/SOKOBAN_RUN_20261010-072252.json"]:
        fp = os.path.join(ROOT, p)
        if not os.path.exists(fp):
            continue
        d, c, shape = cells_of(fp)
        sim = d.get("simulator_digest", "(none)")
        seen.setdefault(sim, []).append(os.path.basename(p))
        print(f"  {os.path.basename(p)[:56]:56s} sim={str(sim)[:16]:16s} cells={len(c):2d}")
    print(f"  distinct instruments: {len(seen)}")
    for sim, files in seen.items():
        print(f"    {sim[:16]}: {len(files)} file(s)")
    if len(seen) > 1:
        print("  => MORE THAN ONE FREEZE IS IN PLAY. A bare 'run of record' line would let a")
        print("     reader compare across freezes and read the instrument change as a result.")
        print("     The line must carry its freeze. (This is the declaration's own finding.)")

    # --- check 3: which runs are on the freeze that is on disk NOW -----------------------
    cur = sha256(os.path.join(ROOT, "sokoban.py"))
    print("\nCHECK 3 -- the freeze on disk now vs what each run records")
    print(f"  sokoban.py on disk : {cur[:16]}")
    for p in declared:
        fp = os.path.join(ROOT, p)
        if not os.path.exists(fp):
            continue
        d, c, _ = cells_of(fp)
        sim = d.get("simulator_digest")
        if sim is None:
            state = "NO DIGEST -- cannot be placed against any freeze"
        elif sim == cur:
            state = "on the CURRENT freeze"
        else:
            state = "a HISTORICAL freeze -- not comparable to a current run"
        print(f"    {os.path.basename(p)[:50]:50s} {state}")
    print("  => a run from a historical freeze is not stale: it is a measurement of a different")
    print("     instrument. Comparing it to a current run measures the instrument change.")

    # --- check 5: the complementary claim -- content is NOT contained ----------------
    # Raised by @sokoban. The declaration says the superseded pilot is contained "with nothing of
    # its own left over". Keys and counters are contained; CONTENT is NOT. That is not a defect in
    # the artifact -- it is the reason the artifact is TRACKED: its turns exist in no other file, and
    # deleting it would delete the only copy (the SOKOBAN_VERDICT_1 / FINDING 020 failure).
    #
    # So the assertion runs the other way: if NOTHING differs at turn level, this artifact IS a
    # duplicate, and the declaration's reason for tracking it does not exist.
    print("\nCHECK 5 -- the superseded file's turn-level content is NOT contained")
    for s in sup:
        if not inc:
            continue
        sd, sc, _ = cells_of(os.path.join(ROOT, s))
        _i, ic, _ = cells_of(os.path.join(ROOT, inc[0]))
        SK = {(c.get("entrant"), c.get("level")): c for c in sc}
        IK = {(c.get("entrant"), c.get("level")): c for c in ic}
        n_diff = n_same = 0
        for k in sorted(set(SK) & set(IK)):
            ca, cb = SK[k], IK[k]
            fields = sorted(set(ca) | set(cb))
            differs = []
            for f in fields:
                va, vb = ca.get(f), cb.get(f)
                if isinstance(va, (list, dict)) or isinstance(vb, (list, dict)):
                    if json.dumps(va, sort_keys=True) != json.dumps(vb, sort_keys=True):
                        differs.append(f)
                elif va != vb:
                    differs.append(f)
            if differs:
                n_diff += 1
                print(f"    DIFFERS  {str(k[0])[:30]:30s} {str(k[1])[:22]:22s} {', '.join(differs)}")
            else:
                n_same += 1
        print(f"    => {n_diff} of {n_diff + n_same} shared cells differ at turn level")
        if n_diff == 0:
            fails.append(f"{s}: NO turn-level difference -- it IS a duplicate, so the stated "
                         f"reason for tracking it does not hold")
            print("    => CONTRADICTION: the file is fully contained, so it need not be tracked.")
        else:
            print(f"    => the declaration's claim of full containment is TOO STRONG; "
                  f"{n_diff} cell(s) exist only here. That is WHY it is tracked.")

    print()
    if fails:
        print("CONTRADICTIONS:", *fails, sep="\n  ")
        return 1
    print("all declared states agree with the artifacts on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
