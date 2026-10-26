#!/usr/bin/env python3
"""refusals.py — classify EVERY block that did not yield a linked row. Counts computed, never typed.

Four classes, because "no linked artifact" is not one thing:
  REFUSED   the process exited non-zero and no row was written. Named, with the sentence it printed.
  EXPECTED  an exit code the cabinet documents as normal for a model (mastermind's 5 = an answered turn
            inconsistent with feedback); the row EXISTS and is scored.
  MISFILED  exit 0, the row was written, but THIS wrapper's block record failed to link the coordinate
            (a defect of mine, recorded rather than tidied away). The resolved path is written beside it.
  MISSING   none of the above — no row and no explanation. Would be a finding.
"""
import glob
import json
import os
import time

ROOT = "/home/chilly1/workspace/ocho_arena"
RUNS = os.path.join(ROOT, "suite3", "runs")
MODELS = "/home/chilly1/moltbook_pipeline/models"
FILES = {"ministral-3b": "Ministral-3-3B-Instruct-2512-UD-Q4_K_XL.gguf",
         "ornith-9b": "Ornith-1.5-9B-Q4_K_M.gguf",
         "mimo-9b": "MiMo-V2.6-Distill-Qwen-9B-Q4_K_M.gguf",
         "bonsai-9b": "Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0.gguf"}
EXPECTED = {("mastermind", 5): "an answered turn inconsistent with feedback — the cabinet documents this "
                               "as normal for a model (exit_meaning in suite/suite.py)"}


def ts(s):
    return time.mktime(time.strptime(s, "%Y-%m-%dT%H:%M:%S%z"))


def resolve(d):
    """Where the row actually went, for a block whose record missed the coordinate."""
    ent = d.get("entrant")
    lab = FILES[ent].replace(".gguf", "")
    if d.get("cabinet") == "chess":
        return "/home/chilly1/workspace/cabinet_results/main/CHESS_GAME_%s-suite3.json" % ent
    if d.get("cabinet") == "snake":
        return os.path.join(ROOT, "probes", "SNAKE_%s_s1.json" % lab)
    return None


def main():
    buckets = {"REFUSED": [], "EXPECTED": [], "MISFILED": [], "MISSING": []}
    for m in sorted(glob.glob(os.path.join(RUNS, "*.meta.json"))):
        d = json.load(open(m))
        dr = d.get("driver") or {}
        exit_ = dr.get("exit")
        has = bool(d.get("artifact_exists"))
        if has and exit_ == 0:
            continue
        if has and (d.get("cabinet"), exit_) in EXPECTED:
            buckets["EXPECTED"].append((m, d))
            continue
        key = (d.get("cabinet"), exit_)
        if exit_ not in (0, None) and not has:
            buckets["REFUSED"].append((m, d))
        elif has and key in EXPECTED:
            buckets["EXPECTED"].append((m, d))
        elif exit_ == 0 and not has:
            p = resolve(d)
            ok = bool(p and os.path.exists(p) and os.path.getmtime(p) >= ts(d["block_started"]) - 2)
            (buckets["MISFILED"] if ok else buckets["MISSING"]).append((m, d, p))
        else:
            buckets["MISSING"].append((m, d, resolve(d)))

    L = ["# Every block that did not yield a linked row — classified", "",
         "Counts below are computed from the block records in `suite3/runs/`, not typed.", ""]
    L.append(f"* REFUSED: **{len(buckets['REFUSED'])}** — non-zero exit, no row. Nothing was scored.")
    L.append(f"* EXPECTED non-zero exit with a row: **{len(buckets['EXPECTED'])}** — scored.")
    L.append(f"* MISFILED: **{len(buckets['MISFILED'])}** — row written, but this wrapper's block record "
             f"failed to link the coordinate (my instrument defect; the path is resolved here).")
    L.append(f"* MISSING: **{len(buckets['MISSING'])}** — no row and no explanation.")
    L.append("")

    L += ["## REFUSED", ""]
    for m, d in buckets["REFUSED"]:
        dr = d.get("driver") or {}
        txt = ((dr.get("stderr_tail") or "") + (dr.get("stdout_tail") or "")).strip().splitlines()
        txt = [t for t in txt if t.strip()]
        rel = d.get("release") or {}
        L += [f"### {d.get('cabinet')} / {d.get('entrant')} / {d.get('level')}",
              "",
              f"* record `{os.path.basename(m)}` · started {d.get('block_started')} · shape {d.get('shape')}",
              f"* **exit {dr.get('exit')}** after {dr.get('wall_secs')} s · artifact: none",
              f"* it said: `{(txt[-1] if txt else '(no output)')[:500]}`",
              f"* release: port_closed={rel.get('port_closed')} · vram {rel.get('vram_mib_after')} vs "
              f"baseline {rel.get('vram_baseline_mib')} · :58595 {rel.get('resident_health_after')}",
              ""]

    L += ["## EXPECTED non-zero exit, row scored", ""]
    for m, d in buckets["EXPECTED"]:
        dr = d.get("driver") or {}
        L += [f"* {d.get('cabinet')} / {d.get('entrant')} — exit {dr.get('exit')}: "
              f"{EXPECTED[(d.get('cabinet'), dr.get('exit'))]} · `{os.path.basename(m)}`"]
    L.append("")

    L += ["## MISFILED — the row exists, my block record missed it", ""]
    for m, d, p in buckets["MISFILED"]:
        L += [f"* {d.get('cabinet')} / {d.get('entrant')} / {d.get('block_started')} — resolved to "
              f"`{p}` (written inside the block window) · `{os.path.basename(m)}`"]
    L.append("")

    if buckets["MISSING"]:
        L += ["## MISSING", ""]
        for m, d, p in buckets["MISSING"]:
            L += [f"* {d.get('cabinet')} / {d.get('entrant')} — `{os.path.basename(m)}` (looked for `{p}`)"]
        L.append("")

    open(os.path.join(ROOT, "suite3", "WINDOW_REFUSALS.md"), "w").write("\n".join(L) + "\n")
    print(json.dumps({k: len(v) for k, v in buckets.items()}))
    for k, v in buckets.items():
        for item in v:
            print(k, os.path.basename(item[0]))


if __name__ == "__main__":
    main()
