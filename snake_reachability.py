#!/usr/bin/env python3
"""SNAKE -- APPLE REACHABILITY CONTROL (card t_f17d1fcf).

For each seed (level), prove an apple is reachable within the cabinet's step cap (120) by
exhibiting a COMPUTED clearing plan (BFS on the 25x25 torus), not an assertion. Also reports
the first-eat tick actually achieved by the greedy-safe baseline on that seed.

If a seed's apple were unreachable, that seed (level) is labelled UNSCORABLE.
"""
import json
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PROBES = os.path.join(HERE, "probes")
OUT = "/home/chilly1/workspace/cabinet_results/main/SNAKE_REACHABILITY.json"
CAP = 120
W = H = 25


def bfs_plan(start, goal):
    """Shortest path on the torus from start cell to goal cell (no obstacles at plan time)."""
    if start == goal:
        return []
    # BFS over (x,y)
    q = deque()
    q.append((start, []))
    seen = {start}
    while q:
        (x, y), path = q.popleft()
        for dx, dy, letter in ((1, 0, "R"), (-1, 0, "L"), (0, 1, "D"), (0, -1, "U")):
            nx, ny = (x + dx) % W, (y + dy) % H
            if (nx, ny) in seen:
                continue
            npath = path + [letter]
            if (nx, ny) == goal:
                return npath
            seen.add((nx, ny))
            q.append(((nx, ny), npath))
    return None


def load(agent, seed):
    p = os.path.join(PROBES, "SNAKE_%s_s%s.json" % (agent, seed))
    with open(p) as f:
        return json.load(f)


def first_eat_tick(probe):
    for row in probe["trace"]:
        if row["after"].get("rng_calls", 0) - row["before"].get("rng_calls", 0) >= 2:
            # an eat happened if respawn count minus reset > 0
            pass
    # simpler: find first tick where eaten cumulative > 0 using score per_tick? not stored. Use rng delta.
    for row in probe["trace"]:
        d = row["after"]["rng_calls"] - row["before"]["rng_calls"]
        reset = row["after"]["length"] == 0
        ate = d // 2 - (1 if reset else 0)
        if ate > 0:
            return row["tick"]
    return None


def main():
    start = (10, 10)
    first_apple = (20, 20)  # fixed by snake/snake.html
    plan = bfs_plan(start, first_apple)
    plan_len = len(plan) if plan else None
    reachable = plan is not None and plan_len is not None and plan_len <= CAP

    levels = {}
    for seed in (1, 7, 13, 42):
        probe = load("baseline-greedy-safe", seed)
        fe = first_eat_tick(probe)
        levels[str(seed)] = {
            "first_apple_cell": list(first_apple),
            "start_cell": list(start),
            "computed_plan": plan,
            "computed_plan_length": plan_len,
            "within_cap": bool(plan_len is not None and plan_len <= CAP),
            "greedy_safe_first_eat_tick": fe,
            "greedy_safe_eaten_total": probe["score"]["eaten"],
            "scorable": bool(reachable),
            "verdict": "SCORABLE" if reachable else "UNSCORABLE",
        }

    result = {
        "control": "apple-reachability",
        "step_cap": CAP,
        "board": "%dx%d torus" % (W, H),
        "first_apple_fixed_by_file": True,
        "reachable": reachable,
        "plan_length": plan_len,
        "levels": levels,
        "unscoreable_levels": [s for s in levels if levels[s]["verdict"] == "UNSCORABLE"],
        "overall_pass": reachable,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))
    return 0 if reachable else 1


if __name__ == "__main__":
    sys.exit(main())
