"""Independent re-measurement of a crate from the ARTIFACT, in a fresh process.

Nothing here reads the generator's own report fields as evidence: shape, ceiling and fill are recomputed
from the slots and clue_data the crate carries. Run from the repo root.
"""
import hashlib
import json
import sys
from pathlib import Path

REPO = Path("/home/chilly1/workspace/ocho_arena")
sys.path.insert(0, str(REPO))
import crossword_gen as CG

path = Path(sys.argv[1])
raw = path.read_bytes()
d = json.loads(raw)

print(f"crate            {path}")
print(f"sha256           {hashlib.sha256(raw).hexdigest()}")
print(f"bytes            {len(raw)}")

CG.set_definitions(str(REPO / "definitions.json"))
CG.restrict_to_cluable()

fails = []
def check(name, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))
    if not cond:
        fails.append(name)

# 1. shape and slot count, from the slots' own extents
for i, p in enumerate(d["puzzles"]):
    ext_r = max(s["row"] + (s["length"] - 1 if s["direction"] == "down" else 0) for s in p["slots"]) + 1
    ext_c = max(s["col"] + (s["length"] - 1 if s["direction"] == "across" else 0) for s in p["slots"]) + 1
    check(f"puzzle {i} ({p.get('arm')}/{p.get('grid_group')}) declared {p['rows']}x{p['cols']} == slot extents {ext_r}x{ext_c}",
          (p["rows"], p["cols"]) == (ext_r, ext_c) == (12, 14))
    check(f"puzzle {i} has 10 slots", len(p["slots"]) == 10, f"slots {len(p['slots'])}")

# 2. arms: same puzzle except arm + clue_to_slot
groups = {}
for p in d["puzzles"]:
    groups.setdefault(p["grid_group"], []).append(p)
for g, ps in sorted(groups.items()):
    check(f"group {g} carries both arms", sorted(p["arm"] for p in ps) == ["permuted", "published"])
    stripped = []
    for p in ps:
        q = json.loads(json.dumps(p))
        q.pop("arm")
        for s in q["slots"]:
            s.pop("clue_to_slot")
        stripped.append(json.dumps(q, sort_keys=True))
    check(f"group {g} arms are byte-identical apart from arm/clue_to_slot",
          len(set(stripped)) == 1)
    moved = [sum(1 for s in p["slots"] if s["clue_to_slot"] != s["clue_to_slot_published"])
             for p in ps if p["arm"] == "permuted"]
    check(f"group {g} permuted mapping moves slots", bool(moved) and moved[0] > 0, f"moved {moved[0]}/10")
    check(f"group {g} each arm's mapping is a bijection",
          all(sorted(s["clue_to_slot"] for s in p["slots"]) == sorted(s["id"] for s in p["slots"]) for p in ps))

# 3. recompute the ceiling from clue_data, in this process
for i, p in enumerate(d["puzzles"]):
    recomputed = 0
    mismatch = []
    for s in p["slots"]:
        cands = CG.candidates_of(s["clue_data"])
        if len(cands) != s["clue_candidates"] or cands != s["candidates"]:
            mismatch.append((s["id"], len(cands), s["clue_candidates"]))
        if cands == [s["answer"]]:
            recomputed += 1
    check(f"puzzle {i} recomputed ceiling {recomputed}/10 == declared {p['ceiling']['clue_resolved']}",
          recomputed == p["ceiling"]["clue_resolved"])
    check(f"puzzle {i} every slot's clue_candidates int matches a fresh recompute", not mismatch, str(mismatch))

# 4. unique fill, recomputed
for i, p in enumerate(d["puzzles"]):
    fl = CG.floor_crossing_solve(p["slots"])
    am = fl.get("assignments") or {}
    ok = (fl["verdict"] == "WINNABLE" and fl.get("fills") == 1 and fl.get("exhausted") is True
          and all(am.get(s["id"]) == s["answer"] for s in p["slots"]))
    check(f"puzzle {i} unique_fill_recheck", ok, f"{fl['verdict']} fills {fl.get('fills')} exhausted {fl.get('exhausted')}")

# 5. grid letters agree with the slots
for i, p in enumerate(d["puzzles"]):
    cells, bad = {}, []
    for s in p["slots"]:
        for (r, c), ch in zip(CG.slot_cells(s), s["answer"]):
            if (r, c) in cells and cells[(r, c)] != ch:
                bad.append((s["id"], r, c))
            cells[(r, c)] = ch
    check(f"puzzle {i} crossings agree across every slot pair", not bad, str(bad[:4]))
    check(f"puzzle {i} every slot lies inside the declared grid",
          all(0 <= r < p["rows"] and 0 <= c < p["cols"] for s in p["slots"] for r, c in CG.slot_cells(s)))

print(f"\n{'OK' if not fails else 'FAILURES: ' + str(fails)}")
sys.exit(0 if not fails else 1)
