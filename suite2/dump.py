#!/usr/bin/env python3
"""dump.py — what the blocks filed: one line per block, then the artifact's own keys.

A reading tool, not a result: it prints what the files say and computes nothing that a table will
later need. Every field printed here is read from `suite2/runs/*.meta.json` (the wrapper's
compute-path / process-identity / release evidence) and from the artifact the cabinet wrote.
"""
import glob
import json
import os
import sys

RUNS = "/home/chilly1/workspace/ocho_arena/suite2/runs"


def main(cab=None, keys=False):
    for m in sorted(glob.glob(os.path.join(RUNS, "*.meta.json"))):
        d = json.load(open(m))
        if cab and d.get("cabinet") != cab:
            continue
        art = d.get("artifact")
        a = json.load(open(art)) if art and os.path.exists(art) else {}
        cp = d.get("compute_path") or {}
        sp = d.get("serving_process") or {}
        rel = d.get("release") or {}
        print(json.dumps({
            "cabinet": d.get("cabinet"), "entrant": d.get("entrant"),
            "level": os.path.basename(d.get("level") or ""),
            "exit": (d.get("driver") or {}).get("exit"),
            "wall_s": (d.get("driver") or {}).get("wall_secs"),
            "artifact": os.path.basename(art) if art else None,
            "ftype": cp.get("props_model_ftype"), "ctx": cp.get("ctx_flag"),
            "slots": cp.get("props_total_slots"), "build": (cp.get("build_line") or "")[:40],
            "pid": sp.get("pid"), "proc_start": sp.get("start_time"),
            "pid_max_mib": (d.get("vram") or {}).get("pid_max_mib"),
            "card_max": (d.get("vram") or {}).get("card_max_mib"),
            "vram_delta": rel.get("vram_delta_mib"), "port_closed": rel.get("port_closed"),
            "art_keys": list(a.keys())[:14] if a else None,
        }, ensure_ascii=False))
        if keys and a:
            print("   ", {k: a[k] for k in list(a.keys())[:20] if not isinstance(a[k], (list, dict))})


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None, "--keys" in sys.argv)
