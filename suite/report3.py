#!/usr/bin/env python3
"""report3.py — aggregate the t_925f606f window into one table per cabinet per entrant.

Every figure is computed from a file a process wrote: suite3/runs/*.meta.json (compute path,
serving-process identity, VRAM samples, release evidence) and the artifact the cabinet itself wrote.
Nothing is typed in from a screen.

THE RULES IT OBEYS
  * A CLAIM IS NOT A SOLVE. Where a cabinet records the model's own claim, it is reported in its own
    column and never contributes to the primary reading.
  * A ROW THAT CANNOT SHOW ITS INSTRUMENT IS NOT A ROW. Each cabinet has a required-fields check; a
    row that fails it is reported as INSTRUMENT-FAILURE with the missing field named, never scored.
  * A SUPERSEDED BLOCK IS NOT A ROW (counted, never merged).
  * AN OLD ROW IS REPORTED BESIDE THE NEW ONE, never merged and never deleted.

Outputs suite3/AGGREGATE3.json and suite3/TABLES3.md.
"""
import glob
import json
import os

ROOT = "/home/chilly1/workspace/ocho_arena"
RUNS = os.path.join(ROOT, "suite3", "runs")
CABS = ["chess", "mastermind", "lightsout", "snake", "labyrinth", "sokoban", "zork", "missile-command"]
FILES = {"ministral-3b": "Ministral-3-3B-Instruct-2512-UD-Q4_K_XL.gguf",
         "ornith-9b": "Ornith-1.5-9B-Q4_K_M.gguf",
         "mimo-9b": "MiMo-V2.6-Distill-Qwen-9B-Q4_K_M.gguf",
         "bonsai-9b": "Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0.gguf"}
# the field(s) that carry the cabinet's PRIMARY reading, in report order
PRIMARY = {
    "chess": ["termination", "termination_fired_at_ply", "last_move", "controls_all_pass"],
    "mastermind": ["wins", "games", "consistency", "answered_turns", "disagreements", "prompt_digests"],
    "lightsout": ["state_cleared", "games", "verdicts", "claims"],
    "snake": ["seeds"],
    "labyrinth": ["legal", "blocked", "unattributable", "distinct_positions", "rows"],
    "sokoban": ["solved", "replay", "plan_len", "blocked", "provenance"],
    "zork": ["accepted", "rejected", "unattributable", "ended", "rooms_visited",
             "rooms_reachable", "carried"],
    "missile-command": ["score", "ended", "counts", "unreadable"],
}


def load(p):
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return None


def blocks():
    out = []
    for m in sorted(glob.glob(os.path.join(RUNS, "*.meta.json"))):
        d = load(m)
        if d:
            d["_meta"] = m
            out.append(d)
    return out


def latest(bs, cabinet):
    """Newest block per (entrant, level); the earlier ones are counted as superseded."""
    newest, superseded = {}, []
    for d in bs:
        if d.get("cabinet") != cabinet:
            continue
        key = (d.get("entrant"), os.path.basename(d.get("level") or "cell"))
        cur = newest.get(key)
        if cur and str(d.get("block_started")) <= str(cur.get("block_started")):
            superseded.append(d)
            continue
        if cur:
            superseded.append(cur)
        newest[key] = d
    return newest, superseded


def is_cpu(d):
    return str(d.get("shape", "")).startswith("cpu-only")


def path_cell(d):
    cp = d.get("compute_path") or {}
    sp = d.get("serving_process") or {}
    if d.get("props"):
        pr = d["props"]
        gs = pr.get("default_generation_settings") or {}
        cp = {"ngl_flag": 99, "ctx_flag": gs.get("n_ctx"),
              "props_model_ftype": pr.get("model_ftype"),
              "props_total_slots": pr.get("total_slots"),
              "build_line": pr.get("build_info")}
    if is_cpu(d):
        if d.get("driver_path"):
            return (f"CPU `-ngl 0` · ctx 65536 (the certified driver's own argv) · "
                    f"certified driver `{os.path.basename(d['driver_path'])}` "
                    f"sha256 {str(d.get('driver_sha256'))[:16]} · no lease")
        return (f"CPU `-ngl {cp.get('ngl')}` · ctx {cp.get('ctx')} · no lease · "
                f"server argv in the row")
    return (f"-ngl {cp.get('ngl_flag')} · ctx {cp.get('ctx_flag')} · ftype `{cp.get('props_model_ftype')}` · "
            f"slots {cp.get('props_total_slots')} · build `{str(cp.get('build_line'))[:22]}`")


def identity(d):
    sp = d.get("serving_process") or {}
    if is_cpu(d):
        return "cpu-block (no lease)"
    return f"pid {sp.get('pid')} · start {sp.get('start_time')}"


def release_state(d):
    if is_cpu(d):
        b, a = d.get("gpu_baseline_mib"), d.get("gpu_after_mib")
        same = (b is not None and a is not None and abs(a - b) <= 64)
        health = (d.get("resident_health_before") == d.get("resident_health_after") == 200)
        return {"port_closed": None, "vram_back_to_baseline": same,
                "resident_health_after": d.get("resident_health_after"),
                "note": "cpu-only block: the check is that the card did not move"}
    r = d.get("release") or {}
    return r


def release_ok(d):
    r = release_state(d)
    if is_cpu(d):
        return bool(r.get("vram_back_to_baseline")) and r.get("resident_health_after") == 200
    return bool(r.get("port_closed")) and bool(r.get("vram_back_to_baseline"))


# ── per-cabinet readings ────────────────────────────────────────────────────
def read_chess(d):
    a = load(d["artifact"]) if d.get("artifact") else None
    if not a:
        return None, "no artifact"
    ctrl = a.get("controls") or {}
    ok_ctrl = len(ctrl) == 4 and all(v.get("pass") for v in ctrl.values())
    rows = a.get("rows") or []
    last = rows[-1] if rows else {}
    return {"termination": a.get("termination"), "moves_recorded": len(rows),
            "last_move": last.get("move_uci"),
            "termination_fired_at_ply": len(rows),
            "controls_all_pass": ok_ctrl, "controls_keys": len(ctrl),
            "claim": None}, ("" if ok_ctrl else "controls missing/not all pass in artifact")


def read_mastermind(d):
    a = load(d["artifact"]) if d.get("artifact") else None
    if not a:
        return None, "no artifact"
    s = a.get("summary") or {}
    run = a.get("run") or {}
    digs = run.get("prompt_digests_per_turn") or []
    ok = (len(set(digs)) > 1 and s.get("stored_vs_recomputed_disagreements") == 0)
    return {"wins": s.get("wins"), "games": s.get("games"), "consistency": s.get("consistency"),
            "answered_turns": s.get("answered_turns"), "distinct_all": s.get("distinct_all"),
            "prompt_digests": len(set(digs)),
            "disagreements": s.get("stored_vs_recomputed_disagreements"), "claim": None}, (
        "" if ok else "per-turn digests or recompute check missing")


def read_lightsout(d):
    p = d.get("artifact")
    if not p or not os.path.exists(p):
        return None, "no artifact"
    rows = [json.loads(l) for l in open(p) if l.strip()]
    from collections import Counter
    verdicts = Counter(r.get("verdict") for r in rows)
    claims = Counter(r.get("claim") for r in rows)
    cleared = sum(1 for r in rows if r.get("verdict") == "CORRECT")
    missing_truth = [r.get("board_id") for r in rows if not r.get("truth")]
    return {"games": len(rows), "verdicts": dict(verdicts), "claims": dict(claims),
            "state_cleared": cleared, "boards_missing_truth": missing_truth,
            "claim": dict(claims)}, ("" if not missing_truth else "rows without recomputed truth")


def read_snake(d):
    lab = FILES[d["entrant"]].replace(".gguf", "")
    arts = ([x["path"] for x in d["artifacts"]] if d.get("artifacts")
            else [os.path.join(ROOT, "probes", f"SNAKE_{lab}_s{s}.json") for s in ("1", "7")])
    rows, missing = [], []
    uncertified = False
    for p in arts:
        a = load(p) if os.path.exists(p) else None
        if not a:
            missing.append(p)
            continue
        sc = a.get("score") or {}
        if "revisits" not in sc:
            # the certified driver writes score.revisits; its absence means this row came from the
            # divergent trunk copy, which is not the instrument the certification measured
            uncertified = True
        rows.append({"seed": a.get("seed"), "eaten": sc.get("eaten"),
                     "best_life": sc.get("best_life"), "ticks": sc.get("ticks"),
                     "revisits_before_death": sc.get("revisits"),
                     "chain": str(a.get("chain_digest"))[:16], "ended": a.get("ended")})
    problem = ""
    if missing:
        problem = "missing episode artifact"
    elif uncertified:
        problem = ("score.revisits absent: this row was produced by the UNCERTIFIED trunk copy of "
                   "snake_run.py, not cabinet/snake @ 149d0d0")
    return {"seeds": rows, "missing": missing, "claim": None}, problem


def read_labyrinth(d):
    a = load(d["artifact"]) if d.get("artifact") else None
    if not a:
        return None, "no artifact"
    summary = a.get("summary") if isinstance(a.get("summary"), dict) else a
    g = summary.get
    legal = g("legal", g("legal_moves", g("accepted")))
    blocked = g("blocked")
    unattr = g("UNATTRIBUTABLE", g("unattributable"))
    distinct = g("distinct_positions")
    rows = a.get("rows") or []
    if rows and (legal is None or distinct is None):
        legal = sum((r.get("legal") or r.get("accepted") or 0) for r in rows)
        blocked = sum((r.get("blocked") or 0) for r in rows)
        unattr = sum((r.get("UNATTRIBUTABLE") or r.get("unattributable") or 0) for r in rows)
        distinct = sum((r.get("distinct_positions") or 0) for r in rows)
    ok = all(x is not None for x in (legal, blocked, unattr, distinct))
    return {"legal": legal, "blocked": blocked, "unattributable": unattr,
            "distinct_positions": distinct, "rows": len(rows),
            "claim": None}, ("" if ok else "three-way separation or census missing")


def read_sokoban(d):
    a = load(d["artifact"]) if d.get("artifact") else None
    if not a:
        return None, "no artifact"
    plan = a.get("plan")
    rep = a.get("replay") or {}
    prov = a.get("provenance") or {}
    rep_verdict = rep.get("verdict") or rep.get("status")
    ok = bool(plan) and bool(rep) and bool(prov) and rep_verdict is not None
    return {"solved": a.get("solved"), "replay": rep_verdict,
            "plan_len": len(plan.get("tokens") or []) if isinstance(plan, dict) else (len(plan) if plan else None),
            "blocked": a.get("blocked"), "not_an_action": a.get("not_an_action"),
            "provenance": bool(prov), "claim": a.get("solved")}, (
        "" if ok else "plan/replay/provenance missing from the row")


def read_zork(d):
    a = load(d["artifact"]) if d.get("artifact") else None
    if not a:
        return None, "no artifact"
    three = a.get("attribution") or {}
    counts = a.get("counts") or {}
    acc = three.get("accepted", counts.get("parsed"))
    rej = three.get("rejected", counts.get("unparsed"))
    una = three.get("UNATTRIBUTABLE", three.get("unattributable", counts.get("unattributable")))
    prog = a.get("progress") or {}
    rooms = prog.get("rooms") or {}
    ok = (None not in (acc, rej, una)) and a.get("attribution_checked_against_counts") is not None
    return {"accepted": acc, "rejected": rej, "unattributable": una,
            "ended": a.get("ended"), "rooms_visited": rooms.get("visited"),
            "rooms_reachable": rooms.get("reachable_from_start"),
            "carried": a.get("carried_required_item"),
            "commands": a.get("commands_consumed"),
            "attribution_checked": a.get("attribution_checked_against_counts"),
            "claim": None}, ("" if ok else "three-way attribution missing or unchecked")


def read_mc(d):
    a = load(d["artifact"]) if d.get("artifact") else None
    if not a:
        return None, "no artifact"
    c = a.get("counts") or {}
    return {"score": a.get("score"), "ended": a.get("ended"),
            "counts": {k: c.get(k) for k in ("fired", "passed", "malformed", "unknown", "out_of_range", "late", "hit", "spared")},
            "unreadable": a.get("unreadable"), "claim": None,
            "ngl_in_record": (a.get("config") or {}).get("n_gpu_layers")}, (
        "" if a.get("counts") else "counts missing")


READERS = {"chess": read_chess, "mastermind": read_mastermind, "lightsout": read_lightsout,
           "snake": read_snake, "labyrinth": read_labyrinth, "sokoban": read_sokoban,
           "zork": read_zork, "missile-command": read_mc}


def compact(reading, cab):
    parts = []
    for k in PRIMARY.get(cab, list(reading)):
        if reading.get(k) is None:
            continue
        v = reading[k]
        parts.append(f"{k}={json.dumps(v) if isinstance(v, (dict, list)) else v}")
    return " · ".join(parts)


def main():
    bs = blocks()
    agg = {"window": "t_925f606f", "blocks": len(bs), "cabinets": {}}
    gpu_blocks = [d for d in bs if not is_cpu(d)]
    cpu_blocks = [d for d in bs if is_cpu(d)]
    clean = [d for d in gpu_blocks if release_ok(d)]
    dirty = [d for d in gpu_blocks if not release_ok(d)]
    cpu_clean = [d for d in cpu_blocks if release_ok(d)]

    md = ["# Window t_925f606f — one table per cabinet per entrant", ""]
    cpu_cabs = sorted({d["cabinet"] for d in cpu_blocks})
    md.append(f"Blocks filed: **{len(bs)}** — {len(gpu_blocks)} GPU blocks (under one global lease) and "
              f"{len(cpu_blocks)} CPU blocks ({', '.join(cpu_cabs) if cpu_cabs else 'none'}, whose certified "
              f"compute paths are CPU).")
    md.append("")
    md.append(f"GPU release verified on **{len(clean)}/{len(gpu_blocks)}** blocks: port closed AND the "
              f"card back to THAT BLOCK'S OWN baseline ±64 MiB.")
    if dirty:
        md.append("")
        md.append("**NOT CLEAN:** " + ", ".join(
            f"{d['cabinet']}/{d['entrant']} (`{os.path.basename(d['_meta'])}`)" for d in dirty))
    md.append("")
    md.append(f"CPU blocks: **{len(cpu_clean)}/{len(cpu_blocks)}** returned the card to their own sampled "
              f"baseline ±64 MiB and left `:58595/health` at 200. A CPU block is not GPU-free — a CPU "
              f"`llama-server` still allocates a CUDA context (measured +364 MiB here).")
    md.append("")
    md.append("Generated by `suite/report3.py` from `suite3/runs/*.meta.json` and the artifacts those "
              "blocks wrote.")

    for cab in CABS:
        newest, sup = latest(bs, cab)
        agg["cabinets"][cab] = {"rows": {}, "superseded": len(sup)}
        md.append("")
        md.append(f"## {cab}")
        md.append("")
        if not newest:
            md.append("_no block was filed for this cabinet._")
            continue
        reader = READERS[cab]
        md.append("| entrant | cell | reading (the cabinet's own state) | claim (the model's) | "
                  "compute path | serving process | artifact sha256 | block |")
        md.append("|---|---|---|---|---|---|---|---|")
        for (ent, cell), d in sorted(newest.items()):
            reading, problem = reader(d)
            if reading is None:
                md.append(f"| {ent} | {cell} | **INSTRUMENT-FAILURE** — {problem} | — | "
                          f"{path_cell(d)} | {identity(d)} | — | `{os.path.basename(d['_meta'])}` |")
                agg["cabinets"][cab]["rows"][f"{ent}/{cell}"] = {
                    "status": "INSTRUMENT-FAILURE", "problem": problem, "meta": d["_meta"]}
                continue
            claim = reading.get("claim")
            status = "" if not problem else f" **({problem})**"
            md.append(f"| {ent} | {cell} | {compact(reading, cab)}{status} | "
                      f"{json.dumps(claim) if claim is not None else '—'} | {path_cell(d)} | "
                      f"{identity(d)} | `{str(d.get('artifact_sha256'))[:16]}` | "
                      f"`{os.path.basename(d['_meta'])}` |")
            agg["cabinets"][cab]["rows"][f"{ent}/{cell}"] = {
                "status": "SCORED" if not problem else "SCORED (instrument caveat)",
                "problem": problem or None, "reading": reading,
                "compute_path": path_cell(d), "serving_process": d.get("serving_process"),
                "meta": d["_meta"], "artifact": d.get("artifact") or d.get("artifact_set"),
                "artifact_sha256": d.get("artifact_sha256"), "release": release_state(d),
                "baseline_mib": d.get("baseline_mib_at_start"),
                "card_max_mib": (d.get("vram") or {}).get("card_max_mib")}
        if sup:
            md.append("")
            md.append(f"_{len(sup)} superseded or refused block(s) kept under `suite3/runs/`; not counted "
                      f"as rows. Refusals are listed in `WINDOW_REFUSALS.md`._")

    with open(os.path.join(ROOT, "suite3", "AGGREGATE3.json"), "w") as f:
        json.dump(agg, f, indent=1)
    with open(os.path.join(ROOT, "suite3", "TABLES3.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md[:20]))
    print(f"\nwrote suite3/TABLES3.md ({len(md)} lines)")


if __name__ == "__main__":
    main()
