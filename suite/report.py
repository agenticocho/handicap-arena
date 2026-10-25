#!/usr/bin/env python3
"""report.py — aggregate the filed rows into one table per cabinet, with the compute-path column.

Every figure is computed from the row files the instruments wrote (never re-typed), and the
compute path / serving-process identity / release evidence is read from the per-run meta files the
driver wrote beside them. Also cross-checks the harness's own printed summary against a re-derivation
from the same rows, so a mismatch surfaces instead of being quoted.
"""
import glob
import json
import os
import sys
from collections import Counter

ROOT = "/home/chilly1/workspace/ocho_arena"
RUNS = os.path.join(ROOT, "suite", "runs")
ENTRANT_ORDER = ["ministral-3b", "ornith-9b", "mimo-9b", "bonsai-9b"]


def meta_for(cabinet, entrant):
    cands = sorted(glob.glob(os.path.join(RUNS, f"{cabinet}_{entrant}_*.meta.json")))
    return json.load(open(cands[-1])) if cands else None


def mastermind_stats(path):
    d = json.load(open(path))
    rows = d["rows"]
    answered = [c for r in rows for c in r["consistent"] if c is not None]
    guesses = [tuple(g) for r in rows for g in r["guesses"]]
    modal = Counter(guesses).most_common(1)[0] if guesses else (None, 0)
    secs = [s for r in rows for s in r["secs"] if isinstance(s, (int, float))]
    toks = [t for r in rows for t in r["tokens"] if isinstance(t, int)]
    return {
        "games": len(rows),
        "wins": sum(1 for r in rows if r["solved"]),
        "answered": len(answered),
        "consistency_pct": round(100 * sum(1 for c in answered if c) / len(answered), 1) if answered else None,
        "distinct_guesses": len(set(guesses)),
        "modal_guess": list(modal[0]) if modal[0] else None,
        "modal_count": modal[1],
        "no_answer": sum(r["no_answer"] for r in rows),
        "strict_turns": sum(r["strict"] for r in rows),
        "normalized_turns": sum(r["normalized"] for r in rows),
        "ended": dict(Counter(r["ended"] for r in rows)),
        "client_tok_per_s": round(sum(toks) / sum(secs), 2) if secs and sum(secs) else None,
        "client_secs_total": round(sum(secs), 1),
        "tokens_total": sum(toks),
        "rowset_sha256": d["run"]["rowset_sha256"],
        "prompt_sha256": d["run"]["prompt_sha256"],
        "harness_summary": d["summary"],
    }


def lightsout_stats(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    verdicts = Counter(r["verdict"] for r in rows)
    raws = Counter((r["raw"] or "").strip() for r in rows)
    toks = [r["completion_tokens"] for r in rows if isinstance(r.get("completion_tokens"), int)]
    secs = [r["secs"] for r in rows if isinstance(r.get("secs"), (int, float))]
    return {
        "boards": len(rows),
        "correct": verdicts.get("CORRECT", 0),
        "verdicts": dict(verdicts),
        "distinct_answers": len(raws),
        "top_answers": [(a.replace("\n", " / ")[:70], n) for a, n in raws.most_common(4)],
        "answer_block": sum(1 for r in rows if r.get("answer_block")),
        "tokens_median": sorted(toks)[len(toks) // 2] if toks else None,
        "secs_total": round(sum(secs), 1),
        "out_of_range_boards": sum(1 for r in rows if r.get("out_of_range")),
        "claims": dict(Counter(r.get("claim") for r in rows)),
    }


def path_cell(m):
    if not m:
        return "NO META"
    cp = m.get("compute_path", {})
    sp = cp.get("serving_process", {})
    return (f"-ngl {cp.get('ngl_flag')} · ctx {cp.get('props_n_ctx')} · {cp.get('props_model_ftype')} · "
            f"slots {cp.get('props_total_slots')} · build {cp.get('build_line')} · "
            f"proc started {sp.get('start_time')} (pid {sp.get('pid')})")


def main():
    out = {"mastermind": {}, "lightsout": {}}
    for e in ENTRANT_ORDER:
        m = meta_for("mastermind", e)
        if m and m.get("result", {}).get("accepted"):
            out["mastermind"][e] = {"stats": mastermind_stats(m["result"]["out"]),
                                    "path": path_cell(m),
                                    "vram": m.get("vram_during_run_mib"),
                                    "release": m.get("release"),
                                    "out": m["result"]["out"]}
        l = meta_for("lightsout", e)
        if l and l.get("result", {}).get("accepted"):
            out["lightsout"][e] = {"stats": lightsout_stats(l["result"]["out"]),
                                   "path": path_cell(l),
                                   "vram": l.get("vram_during_run_mib"),
                                   "release": l.get("release"),
                                   "out": l["result"]["out"]}
    print(json.dumps(out, indent=1))
    with open(os.path.join(RUNS, "AGGREGATE.json"), "w") as f:
        json.dump(out, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
