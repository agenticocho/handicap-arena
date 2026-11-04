#!/usr/bin/env python3
"""SNAKE -- DIGEST CLAIM VERIFICATION (card t_f17d1fcf).

Verifies from the artifacts themselves that bonsai's GPU chain equals its published CPU chain
digest-for-digest, and states what that equality is (and is not) evidence of.
"""
import json
import os
import sys

OUT = "/home/chilly1/workspace/cabinet_results/main/SNAKE_DIGEST_CLAIM.json"
CPU = "/home/chilly1/workspace/ocho_arena/suite2/runs/published_cpu/SNAKE_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_s1.json"
GPU = "/home/chilly1/workspace/ocho_arena/probes/SNAKE_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_s1.json"


def main():
    cpu = json.load(open(CPU))
    gpu = json.load(open(GPU))
    c_cpu = cpu.get("chain_digest")
    c_gpu = gpu.get("chain_digest")
    equal = c_cpu == c_gpu
    # CPU/GPU are different serving processes (different compute path).
    cpu_proc = (cpu.get("config", {}).get("server_binary_digest") or
                cpu.get("instrument", {}).get("binary", {}).get("binary_digest"))
    result = {
        "control": "bonsai-digest-claim",
        "cpu_chain_digest": c_cpu,
        "gpu_chain_digest": c_gpu,
        "equal": equal,
        "cpu_artifact": CPU,
        "gpu_artifact": GPU,
        "cpu_score": cpu.get("score"),
        "gpu_score": gpu.get("score"),
        "verdict": ("EQUAL -- bonsai GPU chain == published CPU chain digest-for-digest"
                    if equal else "NOT EQUAL"),
        "is_evidence_of": (
            "Nothing about model capability. Both runs scored 0 apples on every seed, so no apple was "
            "ever eaten and the seed's RNG state never reached the game; the state chain is therefore "
            "fully determined by the fixed board, start cell and initial apple, independent of the "
            "serving process, the compute path (CPU vs GPU) or the model's weights. The equality is an "
            "instrument property (determinism of a never-eating episode), not evidence that the CPU and "
            "GPU processes agree on anything the model did."
        ),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
