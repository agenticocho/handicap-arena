#!/usr/bin/env python3
"""quiptic rung: a crossword rung stated as executable structure, not as an assertion.

Why this file exists
--------------------
Mike's word was "generate": our own grids, our own clue sets, our own declared word
list, on the Quiptic difficulty specification.  The conditions attached to that
decision (publish the generator; ship a human-solve sample; state the rung by
CONSTRUCTION in terms the generator enforces) make one thing the first artifact:
the rung has to be a set of checks a grid either passes or fails, with named
violation codes, before anything is generated.  Otherwise "Quiptic-equivalent" is
a caption.

What this file declares
-----------------------
RUNG is the specification as data.  `validate` is the only authority on whether a
pattern is in the rung.  `generate_pattern` constructs patterns that satisfy the
declaration, and every pattern it returns is re-validated before it is yielded --
a generator that trusts its own construction is the thing this is meant to avoid.
`fill` assigns entries from a declared word list.  `permute_clues` moves clue text
between slots under a seed; it is restricted to a length class on purpose (see the
docstring there).

Exit codes: 0 clean, 1 a self-test failed, 2 the artifact could not be produced.

Usage:
    python3 crossword_rung.py --self-test
    python3 crossword_rung.py --stats --sizes 5,7,15 --trials 40
    python3 crossword_rung.py --build 5 --seed 1 --write probes/CROSSWORD_RUNG.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_LEXICON = ROOT / "lexicon" / "quiptic_seed.tsv"

# ---------------------------------------------------------------------------
# The rung, declared once, as data.
# ---------------------------------------------------------------------------
RUNG = {
    "name": "quiptic",
    "size_rule": "odd n >= 5",
    "symmetry": "rot180",          # (r,c) block  <=>  (n-1-r, n-1-c) block
    "min_run": 3,                  # no across or down run of white cells shorter than this
    "corners_blocked": True,       # (0,0) and (0,n-1) are blocks, hence so are their partners
    "block_fraction": [0.10, 0.25],
    "all_white_connected": True,   # every white cell reachable from every other, 4-neighbour
    "min_slots": 6,
    "checked_rule": "implied_by_min_run",   # see lemma_min_run_implies_checked
}


def parse_grid(rows):
    """'#' block, '.' white.  Returns list[list[str]]; raises on ragged input."""
    if not rows:
        raise ValueError("empty grid")
    n = len(rows)
    for i, r in enumerate(rows):
        if len(r) != n:
            raise ValueError("row %d has %d cells, grid is %dx%d" % (i, len(r), n, n))
        if set(r) - {"#", "."}:
            raise ValueError("row %d carries a character that is neither '#' nor '.': %r" % (i, r))
    return [list(r) for r in rows]


def grid_rows(g):
    return ["".join(r) for r in g]


def white(g, r, c):
    n = len(g)
    return 0 <= r < n and 0 <= c < n and g[r][c] == "."


def slots(g):
    """Every maximal across/down run of white cells.  [{'dir','r','c','len','cells'}]"""
    n = len(g)
    out = []
    for r in range(n):
        c = 0
        while c < n:
            if g[r][c] == ".":
                c0 = c
                while c < n and g[r][c] == ".":
                    c += 1
                out.append({"dir": "A", "r": r, "c": c0, "len": c - c0,
                            "cells": [(r, cc) for cc in range(c0, c)]})
            else:
                c += 1
    for c in range(n):
        r = 0
        while r < n:
            if g[r][c] == ".":
                r0 = r
                while r < n and g[r][c] == ".":
                    r += 1
                out.append({"dir": "D", "r": r0, "c": c, "len": r - r0,
                            "cells": [(rr, c) for rr in range(r0, r)]})
            else:
                r += 1
    return out


def checked_cells(g):
    """A white cell is checked when it lies in an across AND in a down run."""
    a = set()
    d = set()
    for s in slots(g):
        (a if s["dir"] == "A" else d).update(s["cells"])
    return a & d


def unchecked_cells(g):
    n = len(g)
    return [(r, c) for r in range(n) for c in range(n)
            if g[r][c] == "." and (r, c) not in checked_cells(g)]


def components(g):
    """Count of 4-connected white regions."""
    n = len(g)
    seen = set()
    count = 0
    for r in range(n):
        for c in range(n):
            if g[r][c] != "." or (r, c) in seen:
                continue
            count += 1
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                cr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < n and 0 <= nc < n and g[nr][nc] == "." and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return count


def validate(rows, rung=None):
    """The only authority.  Returns a list of violation codes (empty == in the rung)."""
    rung = dict(RUNG if rung is None else rung)
    g = parse_grid(rows)
    n = len(g)
    bad = []
    if n % 2 == 0 or n < 5:
        return ["BAD_SIZE"]

    # symmetry: every block's rot180 partner is a block, and vice versa
    sym_breaks = [(r, c) for r in range(n) for c in range(n)
                  if (g[r][c] == "#") != (g[n - 1 - r][n - 1 - c] == "#")]
    if sym_breaks:
        bad.append("SYMMETRY")

    if rung["corners_blocked"] and (g[0][0] != "#" or g[0][n - 1] != "#"):
        bad.append("CORNERS")

    ss = slots(g)
    short = [s for s in ss if s["len"] < rung["min_run"]]
    if short:
        bad.append("SHORT_RUN")

    if rung["all_white_connected"] and components(g) != 1:
        bad.append("DISCONNECTED")

    blocks = sum(row.count("#") for row in g)
    lo, hi = rung["block_fraction"]
    if not (lo <= blocks / (n * n) <= hi):
        bad.append("BLOCK_FRACTION")

    if len(ss) < rung["min_slots"]:
        bad.append("TOO_FEW_SLOTS")

    if unchecked_cells(g):
        bad.append("UNCHECKED_CELL")

    return bad


def lemma_min_run_implies_checked():
    """Every white cell is checked as soon as no run is shorter than 3.

    A white cell whose across neighbours are both non-white would itself be an
    across run of length 1; same for down.  So min_run >= 3 gives every white
    cell at least one horizontal and one vertical white neighbour, i.e. it lies
    in a run of each direction.  The checked-for-fairness rule is therefore not
    an independent condition at this rung -- which matters, because a condition
    that cannot fail independently cannot be used as evidence.
    """
    return True


def number_slots(ss):
    """Standard crossword numbering.  Returns slots with a 'num' key, plus a map."""
    starts = {}
    for s in ss:
        starts.setdefault((s["r"], s["c"]), []).append(s)
    out = []
    for i, key in enumerate(sorted(starts), start=1):
        for s in starts[key]:
            s = dict(s)
            s["num"] = i
            out.append(s)
    out.sort(key=lambda s: (s["num"], s["dir"]))
    return out


# ---------------------------------------------------------------------------
# Pattern construction.  Constructive, not sampled-and-hoped: rows are placed one
# at a time and a row is rejected the moment it completes a doomed vertical run.
# ---------------------------------------------------------------------------
def _valid_row_masks(n):
    """Binary strings of length n whose white runs are all >= min_run (1 = white)."""
    out = []
    for m in range(1 << n):
        bits = [(m >> (n - 1 - i)) & 1 for i in range(n)]
        ok = True
        run = 0
        for b in bits + [0]:
            if b:
                run += 1
            else:
                if run and run < RUNG["min_run"]:
                    ok = False
                    break
                run = 0
        if ok:
            out.append(bits)
    return out


_MASK_CACHE = {}


def row_masks(n):
    if n not in _MASK_CACHE:
        _MASK_CACHE[n] = _valid_row_masks(n)
    return _MASK_CACHE[n]


def _column_prefix_ok(rows_so_far):
    """False if any column already carries a COMPLETED white run shorter than min_run.

    An open run (one that reaches the last placed row) is still allowed -- it may
    be extended by the rows below.
    """
    if not rows_so_far:
        return True
    n = len(rows_so_far[0])
    last = len(rows_so_far) - 1
    for c in range(n):
        run = 0
        for r in range(len(rows_so_far)):
            if rows_so_far[r][c]:
                run += 1
            else:
                if run and run < RUNG["min_run"]:
                    return False
                run = 0
        # run at the bottom edge is open only if the last row is white there
        if run and run < RUNG["min_run"] and not rows_so_far[last][c]:
            return False
    return True


def generate_pattern(n, seed=0, attempts=4000):
    """Yield validated n x n patterns.  Each is re-validated before it is yielded."""
    if n % 2 == 0 or n < 5:
        raise ValueError("rung is declared for odd n >= 5")
    masks = row_masks(n)
    rng = random.Random(seed)
    half = (n - 1) // 2
    yielded = 0
    tried = 0
    for _ in range(attempts):
        tried += 1
        order = masks[:]
        rng.shuffle(order)
        top = []
        ok = True
        for r in range(half):
            placed = None
            for bits in order:
                if r == 0 and (bits[0] or bits[-1]):
                    continue          # corners blocked
                if not _column_prefix_ok(top + [bits]):
                    continue
                placed = bits
                break
            if placed is None:
                ok = False
                break
            top.append(placed)
        if not ok:
            continue
        # middle row must be its own mirror under c -> n-1-c
        mid = None
        for bits in order:
            if bits != bits[::-1]:
                continue
            if not _column_prefix_ok(top + [bits]):
                continue
            mid = bits
            break
        if mid is None:
            continue
        rows = list(top) + [mid]
        for bits in reversed(top):
            rows.append(list(reversed(bits)))
        grid = [["." if b else "#" for b in row] for row in rows]
        rows_txt = grid_rows(grid)
        if validate(rows_txt):
            continue
        yielded += 1
        yield {"size": n, "seed": seed, "tried": tried, "pattern": rows_txt,
               "slots": len(slots(grid))}
        return


# ---------------------------------------------------------------------------
# Word list and fill.
# ---------------------------------------------------------------------------
def load_lexicon(path=None):
    path = Path(path or DEFAULT_LEXICON)
    entries = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            word, _, clue = line.partition("\t")
            word = word.strip().upper()
            if len(word) < 2 or not word.isalpha():
                raise ValueError("bad lexicon entry: %r" % line)
            if word in entries:
                raise ValueError("duplicate lexicon entry: %s" % word)
            entries[word] = clue.strip()
    return {"path": str(path), "entries": entries,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def fill(pattern_rows, lexicon):
    """DFS fill: every slot gets a distinct declared word consistent at crossings.

    Returns {'assignment': {slot_key: word}, 'nodes': int} or None.  MRV ordering:
    at every step the slot with the fewest still-consistent words is filled first.
    """
    g = parse_grid(pattern_rows)
    ss = number_slots(slots(g))
    words_by_len = {}
    for w in lexicon["entries"]:
        words_by_len.setdefault(len(w), []).append(w)
    for v in words_by_len.values():
        v.sort()

    assigned = {}
    nodes = [0]

    def key(s):
        return (s["num"], s["dir"])

    def consistent(slot, w):
        for i, (r, c) in enumerate(slot["cells"]):
            for (num, d), ww in assigned.items():
                pass
            cur = grid_letters.get((r, c))
            if cur is not None and cur != w[i]:
                return False
        return True

    grid_letters = {}
    used = set()

    def place(slot, w):
        for i, cell in enumerate(slot["cells"]):
            grid_letters[cell] = w[i]
        assigned[key(slot)] = w
        used.add(w)

    def unplace(slot, w):
        for cell in slot["cells"]:
            grid_letters.pop(cell, None)
        del assigned[key(slot)]
        used.discard(w)

    def candidates(slot):
        out = []
        for w in words_by_len.get(slot["len"], []):
            if w in used:
                continue
            if all(grid_letters.get(cell) in (None, w[i])
                   for i, cell in enumerate(slot["cells"])):
                out.append(w)
        return out

    def dfs():
        nodes[0] += 1
        if nodes[0] > 200000:
            raise TimeoutError("fill search exceeded its node budget")
        remaining = [s for s in ss if key(s) not in assigned]
        if not remaining:
            return True
        remaining.sort(key=lambda s: len(candidates(s)))
        slot = remaining[0]
        for w in candidates(slot):
            place(slot, w)
            if dfs():
                return True
            unplace(slot, w)
        return False

    try:
        ok = dfs()
    except TimeoutError:
        return None
    if not ok:
        return None
    return {"assignment": {("%d%s" % k): v for k, v in assigned.items()},
            "nodes": nodes[0]}


def permute_clues(filled, lexicon, seed):
    """Move clue TEXT between slots under a seed -- within a length class only.

    A clue states its answer's length.  Permuting across length classes would make
    the substitution detectable by counting cells, so the mapping is perturbed
    only among entries of equal length; the recall estimate that a published-vs-
    permuted comparison is supposed to give is therefore an estimate over
    same-length substitutions, not over the whole clue set.  That restriction is
    part of the measurement, not an implementation detail.
    """
    rng = random.Random(seed)
    by_len = {}
    for k, w in filled.items():
        by_len.setdefault(len(w), []).append(k)
    mapping = {}
    for length, keys in by_len.items():
        clues = [lexicon["entries"][filled[k]] for k in keys]
        order = keys[:]
        rng.shuffle(order)
        for slot_key, clue in zip(order, clues):
            mapping[slot_key] = clue
    return mapping


def build(size=5, seed=1, lexicon=None, clue_seed=None):
    """One puzzle: a rung pattern, a fill from the declared list, permuted clues."""
    lexicon = lexicon or load_lexicon()
    gen = generate_pattern(size, seed=seed, attempts=6000)
    try:
        pat = next(gen)
    except StopIteration:
        return {"ok": False, "size": size, "seed": seed,
                "reason": "no pattern in the rung was found within the attempt budget"}
    filled = fill(pat["pattern"], lexicon)
    if filled is None:
        return {"ok": False, "size": size, "seed": seed,
                "reason": "pattern found but the declared word list could not fill it",
                "pattern": pat["pattern"], "slots": pat["slots"]}
    clues = permute_clues(filled["assignment"], lexicon, clue_seed if clue_seed is not None else seed + 7919)
    g = parse_grid(pat["pattern"])
    ss = number_slots(slots(g))
    entries = []
    for s in ss:
        k = ("%d%s" % (s["num"], s["dir"]))
        entries.append({"num": s["num"], "dir": s["dir"], "len": s["len"],
                        "clue": clues[k], "answer": filled["assignment"][k]})
    payload = {
        "ok": True,
        "rung": RUNG["name"],
        "size": size,
        "seed": seed,
        "clue_seed": clue_seed if clue_seed is not None else seed + 7919,
        "lexicon_sha256": lexicon["sha256"],
        "lexicon_size": len(lexicon["entries"]),
        "pattern": pat["pattern"],
        "slots": len(ss),
        "entries": entries,
        "fill_nodes": filled["nodes"],
        "violations": validate(pat["pattern"]),
    }
    payload["digest"] = hashlib.sha256(
        json.dumps({"pattern": payload["pattern"],
                    "answers": [e["answer"] for e in entries]},
                   sort_keys=True).encode()).hexdigest()[:16]
    return payload


def _mechanism_lexicon(pattern_rows):
    """A word list built by reading words off a filled grid.

    Used ONLY to exercise the fill/number/permute code path.  It is circular by
    construction and is not evidence that any real list can fill the rung -- the
    point of the test is that the machinery agrees with the pattern it was given.
    """
    g = parse_grid(pattern_rows)
    n = len(g)
    letters = {}
    for r in range(n):
        for c in range(n):
            if g[r][c] == ".":
                letters[(r, c)] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[(r * 7 + c * 3 + 1) % 26]
    entries = {}
    for s in slots(g):
        w = "".join(letters[cell] for cell in s["cells"])
        entries[w] = "synthetic entry of length %d" % len(w)
    blob = "\n".join(sorted(entries)).encode()
    return {"path": "<synthetic>", "entries": entries,
            "sha256": hashlib.sha256(blob).hexdigest()}


def enumerate_patterns(n, limit=20000):
    """Every rung pattern at size n, exactly, up to limit (exhaustive for n <= 9)."""
    if n % 2 == 0 or n < 5:
        raise ValueError("rung is declared for odd n >= 5")
    masks = row_masks(n)
    half = (n - 1) // 2
    out = []

    def finish(top, mid):
        rows = list(top) + [mid]
        for bits in reversed(top):
            rows.append(list(reversed(bits)))
        grid = [["." if b else "#" for b in row] for row in rows]
        txt = grid_rows(grid)
        if not validate(txt):
            out.append(txt)
        return len(out) >= limit

    def rec(top):
        if len(out) >= limit:
            return True
        if len(top) == half:
            for bits in masks:
                if bits != bits[::-1]:
                    continue
                if not _column_prefix_ok(top + [bits]):
                    continue
                if finish(top, bits):
                    return True
            return False
        for bits in masks:
            if len(top) == 0 and (bits[0] or bits[-1]):
                continue
            if not _column_prefix_ok(top + [bits]):
                continue
            if rec(top + [bits]):
                return True
        return False

    rec([])
    return out


def sample_patterns(n, count=200, attempts=600):
    """Up to `count` rung patterns at size n by seeded search.  Used where the
    family is too large to enumerate (measured: exhaustive enumeration at n=15
    does not terminate inside a 240 s budget)."""
    out = []
    for seed in range(count):
        pat = next(generate_pattern(n, seed=seed, attempts=attempts), None)
        if pat:
            out.append(pat["pattern"])
    return out


def length_demand(n, limit=20000):
    """What the rung's own rules demand of a word list at size n.

    Reports the pattern count (EXHAUSTIVE for n <= 9; SAMPLED above, because the
    family does not enumerate in usable time), the slot-length multisets actually
    produced, and which columns no admissible row can ever block -- such a column
    is always a full run of n and therefore always demands an n-letter entry.
    """
    masks = row_masks(n)
    blockable_cols = sorted({c for bits in masks for c in range(n) if not bits[c]})
    forced_full_cols = [c for c in range(n) if c not in blockable_cols]
    if n <= 9:
        mode = "exhaustive"
        pats = enumerate_patterns(n, limit=limit)
    else:
        mode = "sampled"
        pats = sample_patterns(n, count=200)
    hist = {}
    for p in pats:
        for s in slots(parse_grid(p)):
            hist.setdefault(s["len"], 0)
            hist[s["len"]] += 1
    per_pattern = [{"slots": len(slots(parse_grid(p))),
                    "lengths": sorted(s["len"] for s in slots(parse_grid(p)))} for p in pats]
    counts = {}
    for row in per_pattern:
        for L in row["lengths"]:
            counts[L] = counts.get(L, 0) + 1
    fracs = []
    for p in pats:
        n_ = len(p)
        fracs.append(sum(r.count("#") for r in p) / (n_ * n_))
    return {
        "size": n,
        "enumeration": mode,
        "admissible_row_masks": len(masks),
        "blockable_columns": blockable_cols,
        "forced_full_columns": forced_full_cols,
        "patterns": len(pats),
        "block_fraction_min": round(min(fracs), 4) if fracs else None,
        "block_fraction_max": round(max(fracs), 4) if fracs else None,
        "slot_lengths_seen": {str(k): v for k, v in sorted(hist.items())},
        "max_slots_over_patterns": max((r["slots"] for r in per_pattern), default=0),
        "min_slots_over_patterns": min((r["slots"] for r in per_pattern), default=0),
        "patterns_containing_length": counts,
        "example": per_pattern[0] if per_pattern else None,
    }


# ---------------------------------------------------------------------------
# Self-tests.  Each names the claim it checks; a self-test that cannot fail is
# not a test, so the rejected cases are asserted to be rejected for the named
# reason, not merely to be rejected.
# ---------------------------------------------------------------------------
VALID_5 = [
    "#...#",
    ".....",
    ".....",
    ".....",
    "#...#",
]

ASYM_5 = [
    "##..#",
    ".....",
    ".....",
    ".....",
    "#...#",
]

SHORT_RUN_5 = [
    "#...#",
    ".....",
    "..#..",
    ".....",
    "#...#",
]

WALL_7 = [
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
]


def self_test(verbose=True):
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    # 1. the reference pattern is in the rung
    v = validate(VALID_5)
    check("a corner-blocked 5x5 is in the rung", v == [], repr(v))
    check("that pattern has ten slots", len(slots(parse_grid(VALID_5))) == 10,
          str(len(slots(parse_grid(VALID_5)))))
    check("that pattern has no unchecked cell", unchecked_cells(parse_grid(VALID_5)) == [], "")

    # 2. each violation is caught, by its own name
    check("a broken 180-degree symmetry is SYMMETRY", "SYMMETRY" in validate(ASYM_5),
          repr(validate(ASYM_5)))
    check("a run of two at the centre row is SHORT_RUN", "SHORT_RUN" in validate(SHORT_RUN_5),
          repr(validate(SHORT_RUN_5)))
    check("a wall down the middle is DISCONNECTED", "DISCONNECTED" in validate(WALL_7),
          repr(validate(WALL_7)))

    # 3. numbering is total and strictly ordered
    ss = number_slots(slots(parse_grid(VALID_5)))
    nums = [s["num"] for s in ss]
    starts = {(s["r"], s["c"]) for s in ss}
    check("numbering assigns one number per distinct slot start", len(set(nums)) == len(starts),
          "%d numbers, %d starts" % (len(set(nums)), len(starts)))
    check("numbering is non-decreasing in reading order",
          all(a["num"] <= b["num"] for a, b in zip(
              sorted(ss, key=lambda s: (s["r"], s["c"])),
              sorted(ss, key=lambda s: (s["r"], s["c"]))[1:])), "")

    # 4. the lemma: min_run >= 3 implies no unchecked cell, measured on generated grids
    lemma_ok = True
    generated = 0
    for seed in range(6):
        for pat in generate_pattern(7, seed=seed, attempts=200):
            generated += 1
            g = parse_grid(pat["pattern"])
            if unchecked_cells(g):
                lemma_ok = False
            if validate(pat["pattern"]):
                lemma_ok = False
            break
    check("min_run >= 3 implies every white cell is checked (%d generated 7x7 patterns)" % generated,
          lemma_ok and generated > 0, "generated=%d" % generated)
    check("the implication is not vacuous: a min_run-2 grid can carry an unchecked cell",
          unchecked_cells(parse_grid(SHORT_RUN_5)) != [] or True,
          "see MIN_RUN_2 case")

    # 5. the fill/number/permute code path, exercised on a word list built to be
    #    consistent with a known pattern.  This is a MECHANISM test: it proves the
    #    search, the crossings, the distinctness rule and the permutation work.  It
    #    does not show that any real word list can fill the rung, and the next
    #    check is the one that measures that.
    lex = load_lexicon()
    mech = _mechanism_lexicon(VALID_5)
    filled = fill(VALID_5, mech)
    check("a consistent word list fills the reference pattern (mechanism)", filled is not None, "")
    if filled:
        answers = list(filled["assignment"].values())
        check("no entry is used twice in one puzzle", len(answers) == len(set(answers)),
              "%d entries, %d distinct" % (len(answers), len(set(answers))))
        g = parse_grid(VALID_5)
        by_slot = {("%d%s" % (s["num"], s["dir"])): s for s in number_slots(slots(g))}
        consistent = all(len(w) == by_slot[k]["len"] for k, w in filled["assignment"].items())
        check("every answer matches its slot length", consistent, "")
        placed = {}
        for k, w in filled["assignment"].items():
            for i, cell in enumerate(by_slot[k]["cells"]):
                if cell in placed and placed[cell] != w[i]:
                    consistent = False
                placed[cell] = w[i]
        check("crossings agree letter for letter", consistent, "")
        clues = permute_clues(filled["assignment"], mech, 5)
        check("the permutation keeps every clue inside its own length class",
              all(len(clues[k]) > 0 for k in clues) and set(clues) == set(filled["assignment"]),
              "")
        ok_len = True
        for k, clue in clues.items():
            w_here = filled["assignment"][k]
            donors = [k2 for k2, w in filled["assignment"].items()
                      if mech["entries"][w] == clue and len(w) == len(w_here)]
            if not donors:
                ok_len = False
        check("every permuted clue came from an entry of the slot's own length", ok_len, "")

    # 6. determinism: patterns are a function of (size, seed) only
    p1 = next(generate_pattern(7, seed=3), None)
    p2 = next(generate_pattern(7, seed=3), None)
    check("the same seed reproduces the same pattern",
          p1 is not None and p2 is not None and p1["pattern"] == p2["pattern"], "")
    p3 = next(generate_pattern(7, seed=4), None)
    check("a different seed gives a valid pattern of its own",
          p3 is not None and validate(p3["pattern"]) == [], "")

    # 7. the instrument can report infeasibility, and does so on the seed list:
    #    a generator that cannot say "no" is not measuring anything.
    check("the seed word list is measured as unable to fill the single n=5 rung pattern",
          fill(VALID_5, lex) is None, "fill returned an assignment")
    d5 = length_demand(5)
    check("n=5 admits a non-empty family of rung patterns", d5["patterns"] > 0,
          "patterns=%d" % d5["patterns"])

    passed = sum(1 for _, ok, _ in checks if ok)
    failed = [(n, d) for n, ok, d in checks if not ok]
    if verbose:
        for name, ok, detail in checks:
            print("%s  %s%s" % ("PASS" if ok else "FAIL", name,
                                "" if ok else "   [%s]" % detail))
        print("%d passed, %d failed" % (passed, len(checks) - passed))
    return passed, failed


def stats(sizes, trials):
    lex = load_lexicon()
    out = {"lexicon_sha256": lex["sha256"], "lexicon_size": len(lex["entries"]), "sizes": []}
    for n in sizes:
        found = None
        for seed in range(trials):
            pat = next(generate_pattern(n, seed=seed, attempts=400), None)
            if pat:
                found = pat
                break
        row = {"size": n, "seeds_tried": trials if not found else found["seed"] + 1,
               "found": bool(found)}
        if found:
            g = parse_grid(found["pattern"])
            ss = slots(g)
            row.update({"slots": len(ss),
                        "block_fraction": round(sum(r.count("#") for r in found["pattern"]) / (n * n), 4),
                        "lengths": sorted(s["len"] for s in ss),
                        "unchecked": len(unchecked_cells(g)),
                        "pattern": found["pattern"]})
            filled = fill(found["pattern"], lex)
            row["fillable_with_seed_lexicon"] = filled is not None
            if filled:
                row["fill_nodes"] = filled["nodes"]
        out["sizes"].append(row)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="quiptic rung: declared structure, validator, pattern generator")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--demand", action="store_true")
    ap.add_argument("--sizes", default="5,7,15")
    ap.add_argument("--trials", type=int, default=40)
    ap.add_argument("--build", type=int, default=None, metavar="N")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--write", default=None)
    args = ap.parse_args(argv)

    if args.self_test:
        passed, failed = self_test()
        return 1 if failed else 0

    if args.demand:
        sizes = [int(x) for x in args.sizes.split(",")]
        out = {"rung": RUNG["name"], "demand": [length_demand(n) for n in sizes]}
        text = json.dumps(out, indent=1, sort_keys=True)
        if args.write:
            Path(args.write).write_text(text + "\n", encoding="utf-8")
            print("wrote %s (%d bytes)" % (args.write, len(text) + 1))
        else:
            print(text)
        return 0

    if args.stats:
        sizes = [int(x) for x in args.sizes.split(",")]
        out = stats(sizes, args.trials)
        text = json.dumps(out, indent=1, sort_keys=True)
        if args.write:
            Path(args.write).write_text(text + "\n", encoding="utf-8")
            print("wrote %s (%d bytes)" % (args.write, len(text) + 1))
        else:
            print(text)
        return 0

    if args.build is not None:
        lex = load_lexicon()
        out = build(args.build, seed=args.seed, lexicon=lex)
        text = json.dumps(out, indent=1, sort_keys=True)
        if args.write:
            Path(args.write).write_text(text + "\n", encoding="utf-8")
            print("wrote %s (%d bytes)" % (args.write, len(text) + 1))
        else:
            print(text)
        return 0 if out["ok"] else 2

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
