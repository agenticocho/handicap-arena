#!/usr/bin/env python3
"""report2.py — aggregate sitting-2 blocks into one table per cabinet.

Every figure is computed from the files the blocks wrote: `suite2/runs/*.meta.json` (compute path,
serving-process identity, VRAM samples, release evidence) and the artifact the cabinet itself wrote.
Nothing here is typed in from a screen.

TWO RULES IT OBEYS
  * A CLAIM IS NOT A SOLVE (I5): the primary column is the cabinet's own state check; the model's own
    claim is reported in its own column and never contributes to the primary.
  * A SUPERSEDED PASS IS NOT A ROW: where a cell was run twice in this window, the newest block wins
    and the earlier one is counted under `superseded`, never merged.

Outputs: suite2/runs/AGGREGATE2.json (machine-readable) and suite2/TABLES2.md (the tables, so the
results document can carry generated text instead of re-typed numbers).
"""
import glob
import json
import os
import sys
from collections import Counter

ROOT = "/home/chilly1/workspace/ocho_arena"
RUNS = os.path.join(ROOT, "suite2", "runs")
PUB = os.path.join(RUNS, "published_cpu")
ENTRANTS = ["ministral-3b", "ornith-9b", "mimo-9b", "bonsai-9b"]
CABS = ["sokoban", "zork", "snake", "labyrinth", "chess"]


def load(p):
    try:
        return json.load(open(p))
    except Exception:  # noqa: BLE001
        return None


def blocks(cabinet):
    """Newest block per (entrant, level); the rest are counted as superseded."""
    newest, superseded = {}, 0
    for m in sorted(glob.glob(os.path.join(RUNS, "*.meta.json"))):
        d = load(m)
        if not d or d.get("cabinet") != cabinet:
            continue
        key = (d.get("entrant"), os.path.basename(d.get("level") or "cell"))
        prev = newest.get(key)
        if prev and str(d.get("block_started")) < str(prev.get("block_started")):
            superseded += 1
            continue
        if prev:
            superseded += 1
        newest[key] = d
    return newest, superseded


def path_str(d):
    cp = d.get("compute_path") or {}
    sp = d.get("serving_process") or cp.get("serving_process") or {}
    return (f"-ngl {cp.get('ngl_flag')} · ctx {cp.get('ctx_flag')} · ftype `{cp.get('props_model_ftype')}` · "
            f"slots {cp.get('props_total_slots')} · build `{(cp.get('build_line') or '?')[:22]}` · "
            f"pid {sp.get('pid')} started {sp.get('start_time')}")


def release_ok(d):
    r = d.get("release") or {}
    return bool(r.get("port_closed")) and bool(r.get("vram_back_to_baseline"))


# ── per-cabinet readings ─────────────────────────────────────────────────────
def sokoban_stat(d):
    a = load(d["artifact"]) if d.get("artifact") else None
    if not a:
        return {"room": "NO ARTIFACT", "exit": (d.get("driver") or {}).get("exit")}
    turns = a.get("turns") or []
    return {"solved": bool(a.get("solved")), "ended": a.get("ended"), "moves": a.get("moves"),
            "blocked": a.get("blocked"), "not_an_action": a.get("not_an_action"),
            "give_up": a.get("give_up"), "gave_up_at": a.get("gave_up_at"),
            "tokens": sum(int(t.get("gen_tokens") or 0) for t in turns),
            "turns": len(turns),
            "secs": round(sum(float(t.get("secs") or 0) for t in turns), 1),
            "legend_digest": a.get("legend_digest"), "cap": a.get("cap"),
            "dead_end": (a.get("dead_end") or {}).get("reading")}


def zork_stat(d):
    a = load(d["artifact"]) if d.get("artifact") else None
    if not a:
        return {"room": "NO ARTIFACT", "exit": (d.get("driver") or {}).get("exit")}
    turns = a.get("turns") or []
    return {"finished": bool(a.get("finished")), "ended": a.get("ended"),
            "carried_item": a.get("carried_required_item"), "took_item_at_step": a.get("took_item_at_step"),
            "counts": a.get("counts"), "rooms": a.get("rooms_visited"),
            "tokens": sum(int(t.get("gen_tokens") or 0) for t in turns if isinstance(t, dict)),
            "turns": len(turns), "sufficiency_ok": a.get("sufficiency_ok"),
            "replay_mismatch": ((a.get("sufficiency") or {}).get("simulator_replay_mismatched")),
            "takes": sum(1 for t in turns if isinstance(t, dict) and "take" in (t.get("command") or "").lower()),
            "first_raw": (turns[0].get("raw") if turns and isinstance(turns[0], dict) else None)}


def snake_stat(d):
    a = load(d["artifact"]) if d.get("artifact") else None
    if not a:
        return {"room": "NO ARTIFACT", "exit": (d.get("driver") or {}).get("exit")}
    eps = a.get("episodes") or []
    detail = []
    for e in eps:
        p = e.get("artifact")
        p = os.path.join(ROOT, p) if p and not os.path.isabs(p) else p
        ep = load(p) if p and os.path.exists(p) else {}
        raw_moves = ep.get("moves") or []
        moves = [m for m in raw_moves if isinstance(m, str)]
        no_answer = sum(1 for m in raw_moves if m is None)
        detail.append({"seed": e.get("seed"), "eaten": (e.get("score") or {}).get("eaten"),
                       "deaths": (e.get("score") or {}).get("deaths"),
                       "ticks": (e.get("score") or {}).get("ticks"),
                       "ended": e.get("ended"), "chain": e.get("chain_digest"),
                       "not_an_action": ep.get("not_an_action"),
                       "missing_values": ep.get("missing_values"),
                       "no_answer": no_answer,
                       "distinct_moves": sorted(set(moves)),
                       "moves_share": (Counter(moves).most_common(1)[0] if moves else None),
                       "config_ngl": (ep.get("config") or {}).get("n_gpu_layers"),
                       "config_ctx": (ep.get("config") or {}).get("ctx"),
                       "browser": ((ep.get("instrument") or {}).get("browser") or {})})
    return {"totals": a.get("totals"), "seeds": a.get("seeds"), "ticks": a.get("ticks"),
            "per_seed": detail}


def labyrinth_stat(d):
    a = load(d["artifact"]) if d.get("artifact") else None
    if not a:
        return {"room": "NO ARTIFACT", "exit": (d.get("driver") or {}).get("exit")}
    g = a.get("graph") or {}
    return {"plies": a.get("plies"), "end_state": a.get("end_state"),
            "blocked": a.get("blocked"), "not_an_action": a.get("not_an_action"),
            "give_up": a.get("give_up"), "visited_positions": a.get("visited_unique"),
            "visited_names": a.get("visited_names"),
            "count_basis": a.get("visited_count_basis"),
            "graph_digest": (g.get("graph_digest") or "")[:16],
            "graph_file_sha256": (g.get("file_sha256") or "")[:16],
            "cell_spec": (a.get("cell_spec_sha256") or "")[:8],
            "sym": (a.get("pinned_identity") or {}).get("value"), "K": a.get("K"),
            "cap": a.get("cap"), "tokens_total": a.get("tokens_total"),
            "turn_cap": a.get("max_turn_tokens"), "budget_binding": a.get("budget_binding"),
            "prompt_digest": (a.get("prompt_digest") or "")[:16],
            "quant": a.get("model_quant"), "moves": [(m.get("from"), m.get("to")) for m in (a.get("moves") or [])][:12]}


def chess_stat(d):
    a = load(d["artifact"]) if d.get("artifact") else None
    if not a:
        return {"room": "NO ARTIFACT", "exit": (d.get("driver") or {}).get("exit")}
    m = a.get("measures") or {}
    return {"termination": a.get("termination"), "why": a.get("why"), "measures": m,
            "plies": len(a.get("rows") or []), "prompt_digest": (a.get("frozen") or {}).get("prompt_digest"),
            "cap": (a.get("frozen") or {}).get("cap"),
            "illegal": sum(1 for r in (a.get("rows") or []) if r.get("move_uci") in (None, "", "RESIGN")
                           and r.get("termination") not in ("resigned",))}


STAT = {"sokoban": sokoban_stat, "zork": zork_stat, "snake": snake_stat,
        "labyrinth": labyrinth_stat, "chess": chess_stat}


def md_table(rows):
    if not rows:
        return "_(no rows)_\n"
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "|".join("---" for _ in rows[0]) + "|"]
    for r in rows[1:]:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out) + "\n"


def short_path(p):
    """A compute path small enough for a table cell but still the path, not a summary of it."""
    return p.replace(" · ftype `", "· ").replace("`", "").replace("started ", "start ")


def tables(out):
    md = {}
    # SOKOBAN
    rows = [["entrant", "compute path", "L1 one_push", "L2 two_boxes", "L3 corner_waiting",
             "moves L1/L2/L3", "not_an_action L1/L2/L3", "blocked L1/L2/L3", "RESIGN at",
             "gen tokens", "wall s", "peak pid VRAM", "release"]]
    for e, v in sorted(out["sokoban"]["entrants"].items()):
        L = v["levels"]
        order = ["01_one_push", "02_two_boxes", "03_the_corner_waiting"]
        parts = [L.get(l + ".txt") or L.get(l) for l in order]
        def g(i, k):
            return [((s or {}).get("stat") or {}).get(k) for s in parts]
        verb = ["SOLVED" if (s or {}).get("stat", {}).get("solved") else
                f"no ({(s or {}).get('stat', {}).get('ended')})" if s else "NOT RUN" for s in parts]
        resign = [((s or {}).get("stat") or {}).get("gave_up_at") for s in parts]
        rows.append([e, short_path(parts[0]["path"]) if parts[0] else "—", *verb,
                     "/".join(str(x) for x in g(0, "moves")),
                     "/".join(str(x) for x in g(0, "not_an_action")),
                     "/".join(str(x) for x in g(0, "blocked")),
                     "/".join("—" if x is None else str(x) for x in resign),
                     "/".join(str(x) for x in g(0, "tokens")),
                     "/".join(str((s or {}).get("wall_s")) for s in parts),
                     "/".join(str((s or {}).get("pid_max_mib")) for s in parts),
                     "ok" if not v["release_failures"] else "FAILED " + ",".join(v["release_failures"])])
    md["sokoban"] = md_table(rows)

    # ZORK
    rows = [["entrant", "compute path", "L1 the_floor", "L2 long_crawl", "parsed L1/L2",
             "unparsed L1/L2", "impossible L1/L2", "replay audit", "gen tokens L1/L2", "wall s", "release"]]
    for e, v in sorted(out["zork"]["entrants"].items()):
        L = v["levels"]
        p1, p2 = L.get("zork_01_the_floor.txt"), L.get("zork_02_long_crawl.txt")
        def z(s, k):
            return ((s or {}).get("stat") or {}).get(k)
        def fin(s):
            if not s:
                return "NOT RUN"
            st = s["stat"]
            if st.get("sufficiency_ok") is False:
                return "INSTRUMENT-FAILURE (replay)"
            return f"{'ESC' if st.get('finished') else 'no'} ({st.get('ended')})"
        rows.append([e, short_path(p1["path"]) if p1 else "—", fin(p1), fin(p2),
                     f"{(z(p1,'counts') or {}).get('parsed')}/{(z(p2,'counts') or {}).get('parsed')}",
                     f"{(z(p1,'counts') or {}).get('unparsed')}/{(z(p2,'counts') or {}).get('unparsed')}",
                     f"{(z(p1,'counts') or {}).get('recognised-but-impossible')}/"
                     f"{(z(p2,'counts') or {}).get('recognised-but-impossible')}",
                     f"{z(p1,'sufficiency_ok')}/{z(p2,'sufficiency_ok')}",
                     f"{z(p1,'tokens')}/{z(p2,'tokens')}",
                     f"{(p1 or {}).get('wall_s')}/{(p2 or {}).get('wall_s')}",
                     "ok" if not v["release_failures"] else "FAILED"])
    md["zork"] = md_table(rows)

    # SNAKE
    rows = [["entrant", "compute path", "seed", "apples", "deaths", "ticks", "ended",
             "distinct moves", "modal move", "state-chain digest", "wall s", "release"]]
    for e, v in sorted(out["snake"]["entrants"].items()):
        s = list(v["levels"].values())[0]
        st = s["stat"]
        for seed in st.get("per_seed") or []:
            rows.append([e, short_path(s["path"]),
                         seed.get("seed"), seed.get("eaten"), seed.get("deaths"), seed.get("ticks"),
                         seed.get("ended"),
                         ",".join(seed.get("distinct_moves") or []),
                         (f"{seed['moves_share'][0]} ×{seed['moves_share'][1]}"
                          if seed.get("moves_share") else "—"),
                         seed.get("chain"),
                         s.get("wall_s"),
                         "ok" if not v["release_failures"] else "FAILED"])
    md["snake"] = md_table(rows)

    # LABYRINTH
    rows = [["entrant", "compute path", "plies / cap", "end state", "moved", "blocked",
             "not_an_action", "give_up", "visited positions", "visited names", "turn cap", "tokens", "wall s", "release"]]
    for e, v in sorted(out["labyrinth"]["entrants"].items()):
        s = list(v["levels"].values())[0]
        st = s["stat"]
        moved = (st.get("plies") or 0) - (st.get("blocked") or 0) - (st.get("not_an_action") or 0)
        rows.append([e, short_path(s["path"]), f"{st.get('plies')}/{st.get('cap')}",
                     st.get("end_state"), moved, st.get("blocked"), st.get("not_an_action"),
                     st.get("give_up"), st.get("visited_positions"), st.get("visited_names"),
                     st.get("turn_cap"), st.get("tokens_total"), s.get("wall_s"),
                     "ok" if not v["release_failures"] else "FAILED"])
    md["labyrinth"] = md_table(rows)

    # CHESS
    rows = [["entrant", "compute path", "termination", "premature collapse", "miscalibrated persistence",
             "plies in lost positions", "plies", "cap", "prompt digest", "wall s", "release"]]
    for e, v in sorted(out["chess"]["entrants"].items()):
        s = list(v["levels"].values())[0]
        st = s["stat"]
        m = st.get("measures") or {}
        rows.append([e, short_path(s["path"]), st.get("termination"),
                     m.get("premature_collapse"), m.get("miscalibrated_persistence"),
                     m.get("plies_in_lost_positions"), st.get("plies"), st.get("cap"),
                     st.get("prompt_digest"), s.get("wall_s"),
                     "ok" if not v["release_failures"] else "FAILED"])
    md["chess"] = md_table(rows)

    # PUBLISHED CPU ROWS — their own table, never merged into the GPU rows above
    rows = [["preserved artifact (suite/runs/published_cpu/)", "sha256 (provenance file)", "its own primary fields"]]
    for name, d in sorted((out.get("_published_cpu") or {}).items()):
        rows.append([name, "see .provenance.json",
                     ", ".join(f"{k}={v}" for k, v in d.items() if v is not None)])
    md["cpu"] = md_table(rows)
    return md


def main():
    out = {}
    for cab in CABS:
        nb, sup = blocks(cab)
        ent = {}
        for (e, lvl), d in sorted(nb.items()):
            ent.setdefault(e, {"levels": {}, "release_failures": []})
            ent[e]["levels"][lvl] = {"path": path_str(d), "art": d.get("artifact"),
                                     "art_sha": d.get("artifact_sha256"),
                                     "wall_s": (d.get("driver") or {}).get("wall_secs"),
                                     "exit": (d.get("driver") or {}).get("exit"),
                                     "pid_max_mib": (d.get("vram") or {}).get("pid_max_mib"),
                                     "card_max_mib": (d.get("vram") or {}).get("card_max_mib"),
                                     "release": d.get("release"),
                                     "stat": STAT[cab](d)}
            if not release_ok(d):
                ent[e]["release_failures"].append(lvl)
        out[cab] = {"blocks": len(nb), "superseded": sup, "entrants": ent}
    # published CPU rows, kept as their own rows
    pub = {}
    for p in sorted(glob.glob(os.path.join(PUB, "*.json"))):
        d = load(p)
        if d:
            pub[os.path.basename(p)] = {k: d.get(k) for k in
                                        ("solved", "ended", "moves", "blocked", "not_an_action",
                                         "give_up", "finished", "carried_required_item")}
    out["_published_cpu"] = pub
    with open(os.path.join(RUNS, "AGGREGATE2.json"), "w") as f:
        json.dump(out, f, indent=1)
    md = tables(out)
    with open(os.path.join(ROOT, "suite2", "TABLES2.md"), "w") as f:
        for k in CABS + ["cpu"]:
            f.write(f"<!-- TABLE:{k} -->\n{md[k]}\n")
    print(json.dumps({k: {"blocks": v.get("blocks"), "superseded": v.get("superseded"),
                          "entrants": sorted((v.get("entrants") or {}).keys())}
                      for k, v in out.items() if k != "_published_cpu"}, indent=1))
    print(f"published CPU rows preserved: {len(pub)}")
    print("wrote suite2/TABLES2.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
