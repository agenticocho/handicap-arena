#!/usr/bin/env python3
"""SNAKE -- SEED-SENSITIVITY CONTROL (card t_f17d1fcf)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PROBES = os.path.join(HERE, "probes")
OUT = "/home/chilly1/workspace/cabinet_results/main/SNAKE_SEED_SENSITIVITY.json"


def load(agent, seed):
    p = os.path.join(PROBES, "SNAKE_%s_s%s.json" % (agent, seed))
    with open(p) as f:
        return json.load(f)


def main():
    eating = {}
    for s in (1, 7):
        b = load("baseline-greedy-safe", s)
        eating[s] = {"chain_digest": b["chain_digest"], "eaten": b["score"]["eaten"],
                     "revisits": b["score"].get("revisits")}
    noneat = {}
    for s in (1, 7):
        b = load("baseline-cycle", s)
        noneat[s] = {"chain_digest": b["chain_digest"], "eaten": b["score"]["eaten"],
                     "revisits": b["score"].get("revisits")}

    eat_differs = eating[1]["chain_digest"] != eating[7]["chain_digest"]
    noneat_same = noneat[1]["chain_digest"] == noneat[7]["chain_digest"]
    eat_eats = all(eating[s]["eaten"] > 0 for s in (1, 7))
    noneat_zero = all(noneat[s]["eaten"] == 0 for s in (1, 7))

    result = {
        "control": "seed-sensitivity",
        "eating_policy": {
            "name": "baseline-greedy-safe",
            "eats_apple": True,
            "seeds": eating,
            "chain_differs_across_seeds": eat_differs,
            "pass": bool(eat_differs and eat_eats),
        },
        "non_eating_policy": {
            "name": "baseline-cycle",
            "eats_apple": False,
            "seeds": noneat,
            "chain_identical_across_seeds": noneat_same,
            "pass": bool(noneat_same and noneat_zero),
        },
        "overall_pass": bool(eat_differs and eat_eats and noneat_same and noneat_zero),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))
    return 0 if result["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
EOF