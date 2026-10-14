#!/usr/bin/env python3
"""Independent level check for the two shipped Sokoban blobs.

Reads the archived blobs (NOT the inbox, which is now empty), hashes them,
BFSes the shortest solution from first principles (stdlib only, no use of the
simulator's own play() to find it), then plays that solution through the FROZEN
simulator bytes and asserts solved=True.

Deliberately independent of sokoban.py for the solve step, so "solvable" is not
the instrument grading itself.
"""
import collections
import hashlib
import importlib.util
import json
import os
import sys

SCRATCH = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(SCRATCH, "sokoban.py")
ARCHIVE = os.path.expanduser("~/workspace/chair-link/archive")

spec = importlib.util.spec_from_file_location("frozen_sim", SIM)
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)

WALL, TARGET, BOX, PLAYER, BOX_T, PLAYER_T = "#", ".", "$", "@", "*", "+"
DIRS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}


def parse_grid(text):
    lines = text.rstrip("\n").split("\n")
    walls, targets, boxes, player = set(), set(), set(), None
    for r, line in enumerate(lines):
        for c, ch in enumerate(line):
            if ch == WALL:
                walls.add((r, c))
            elif ch == TARGET:
                targets.add((r, c))
            elif ch == BOX:
                boxes.add((r, c))
            elif ch == PLAYER:
                player = (r, c)
            elif ch == BOX_T:
                boxes.add((r, c)); targets.add((r, c))
            elif ch == PLAYER_T:
                player = (r, c); targets.add((r, c))
    return walls, targets, frozenset(boxes), player


def bfs_solution(text, cap=400000):
    walls, targets, boxes0, p0 = parse_grid(text)
    start = (p0, boxes0)
    goal = lambda st: st[1] == targets
    if goal(start):
        return ""
    seen, parent = {start}, {start: None}
    q = collections.deque([start])
    n = 0
    while q:
        st = q.popleft()
        n += 1
        if n > cap:
            return None
        p, boxes = st
        for d, (dr, dc) in DIRS.items():
            np = (p[0] + dr, p[1] + dc)
            if np in walls:
                continue
            nboxes = boxes
            if np in boxes:
                nb = (np[0] + dr, np[1] + dc)
                if nb in walls or nb in boxes:
                    continue
                nboxes = frozenset((boxes - {np}) | {nb})
            nst = (np, nboxes)
            if nst in seen:
                continue
            seen.add(nst)
            parent[nst] = (st, d)
            if goal(nst):
                path, cur = [], nst
                while parent[cur] is not None:
                    cur, d2 = parent[cur]
                    path.append(d2)
                return "".join(reversed(path))
            q.append(nst)
    return None


def main():
    files = [("01_one_push.txt", 1), ("02_two_boxes.txt", 12)]
    print(f"  simulator sha256: {hashlib.sha256(open(SIM,'rb').read()).hexdigest()}")
    print(f"  source dir:       {ARCHIVE}")
    print()
    bad = 0
    keys_printed = False
    for name, expected in files:
        path = os.path.join(ARCHIVE, name)
        blob = open(path, encoding="utf-8").read()
        sha = hashlib.sha256(blob.encode()).hexdigest()
        sol = bfs_solution(blob)
        r = sim.play(blob, [c for c in sol]) if sol is not None else None
        ok = sol is not None and r is not None and r["solved"] is True and len(sol) == expected
        bad += 0 if ok else 1
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}")
        print(f"        sha256          {sha}")
        print(f"        digest prefix   {sha[:16]}   (must match the Chief's ruling)")
        print(f"        BFS shortest    {len(sol) if sol is not None else 'NO SOLUTION'}"
              f"  ({sol if sol else '-'})   expected {expected}")
        if r is not None:
            if not keys_printed:
                print(f"        play() keys     {sorted(r.keys())}")
                keys_printed = True
            scalars = {k: v for k, v in r.items() if isinstance(v, (int, str, bool, type(None)))}
            print(f"        played frozen   {json.dumps(scalars, sort_keys=True)}")
    print()
    print(f"  {'BOTH LEVELS VERIFIED' if bad == 0 else str(bad) + ' LEVEL(S) FAILED'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
