#!/usr/bin/env python3
"""CROSSWORD harness -- generated criss-cross puzzles (crate format).

Loads a generated crate (slots, not cells), builds a grid from slot extents,
runs a resident model per clue, fills cells, checks crossings, writes a trace.

Usage:
  python3 crossword.py --crate /path/to/CRATE.json --puzzle 0 --arm published
  python3 crossword.py --crate /path/to/CRATE.json --puzzle 0 --arm permuted
  python3 crossword.py --self-test
"""
import argparse, json, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TRACE_DIR = os.path.join(HERE, "traces")

MODEL_URLS = {
    "ornith9b": "http://127.0.0.1:8360/v1/chat/completions",
    "jang": "http://127.0.0.1:19081/v1/chat/completions",
    "lfm3-1.7b": "http://127.0.0.1:8376/v1/chat/completions",
    "smol3b": "http://127.0.0.1:8380/v1/chat/completions",
    "spark4b-q4": "http://127.0.0.1:8381/v1/chat/completions",
}

# ---------- crate loading ----------
def load_crate(path):
    with open(path) as f:
        return json.load(f)

def make_puzzle(crate, puzzle_index, arm, crate_path=None):
    import hashlib
    p = crate["puzzles"][puzzle_index]
    slots_raw = p["slots"]

    # compute true grid bounds from slot extents (rows/cols in crate are wrong)
    min_r = min_c = 10**9
    max_r = max_c = -10**9
    for s in slots_raw:
        r, c = s["row"], s["col"]
        if s["direction"] == "across":
            rs = [r]; cs = list(range(c, c + s["length"]))
        else:
            rs = list(range(r, r + s["length"])); cs = [c]
        min_r = min(min_r, min(rs)); max_r = max(max_r, max(rs))
        min_c = min(min_c, min(cs)); max_c = max(max_c, max(cs))
    origin_r, origin_c = min_r, min_c
    rows = max_r - min_r + 1
    cols = max_c - min_c + 1

    grid = [[0]*cols for _ in range(rows)]
    slots = []
    for s in slots_raw:
        r, c = s["row"], s["col"]
        cells = []
        for i in range(s["length"]):
            if s["direction"] == "across":
                rr, cc = r, c + i
            else:
                rr, cc = r + i, c
            cells.append((rr - origin_r, cc - origin_c))
            grid[rr - origin_r][cc - origin_c] = 1
        slot = {
            "id": s["id"],
            "direction": s["direction"],
            "row": r - origin_r,
            "col": c - origin_c,
            "abs_row": r,
            "abs_col": c,
            "origin_r": origin_r,
            "origin_c": origin_c,
            "length": s["length"],
            "answer": s["answer"],
            "clue": s["clue"],
            "clue_data": s.get("clue_data", {}),
            "candidates": s.get("candidates", []),
            "clue_candidates": s.get("clue_candidates", 0),
            "published_label": s["clue_to_slot_published"],
            "permuted_label": s["clue_to_slot_permuted"],
            "cells": cells,
        }
        slots.append(slot)

    if arm == "published":
        label_of = {s["id"]: s["published_label"] for s in slots}
    else:
        label_of = {s["id"]: s["permuted_label"] for s in slots}
    slot_by_label = {}
    for s in slots:
        slot_by_label[label_of[s["id"]]] = s

    presented = sorted(slot_by_label.items(), key=lambda kv: kv[0])

    if crate_path and os.path.exists(crate_path):
        crate_digest = hashlib.sha256(open(crate_path, "rb").read()).hexdigest()
    else:
        crate_digest = hashlib.sha256(json.dumps(crate, sort_keys=True).encode()).hexdigest()

    puzzle = {
        "source": "generated",
        "crate_digest": crate_digest,
        "crate_seed": crate.get("seed"),
        "word_list_size": crate.get("word_list_size"),
        "words_sha256": crate.get("words_sha256"),
        "puzzle_index": puzzle_index,
        "arm": arm,
        "rows": rows,
        "cols": cols,
        "grid": grid,
        "slots": slots,
        "presented": presented,
        "grid_sha256": p.get("grid_sha256"),
        "ceiling": p.get("ceiling"),
        "floor": p.get("floor"),
        "unique_fill": p.get("unique_fill"),
    }
    return puzzle

# ---------- grid helpers ----------
def blank_grid(puzzle):
    rows, cols = puzzle["rows"], puzzle["cols"]
    g = puzzle["grid"]
    return [[("" if g[r][c] == 1 else None) for c in range(cols)] for r in range(rows)]

def total_white(puzzle):
    return sum(1 for row in puzzle["grid"] for x in row if x == 1)

def grid_state_for_trace(grid):
    out = []
    for row in grid:
        out.append([None if v is None else ("" if v == "" else v) for v in row])
    return out

def apply_fill(grid, r, c, letter):
    if grid[r][c] is None:
        return "black"
    if grid[r][c] == "":
        grid[r][c] = letter
        return "applied"
    if grid[r][c] == letter:
        return "already"
    return "conflict"

def is_solved(puzzle, grid):
    for s in puzzle["slots"]:
        for (r, c), ch in zip(s["cells"], s["answer"]):
            if grid[r][c] != ch:
                return False
    for r in range(puzzle["rows"]):
        for c in range(puzzle["cols"]):
            if puzzle["grid"][r][c] == 1 and grid[r][c] in (None, ""):
                return False
    return True

def count_filled(grid):
    n = 0
    for row in grid:
        for v in row:
            if isinstance(v, str) and v != "":
                n += 1
    return n

def eval_satisfiable(puzzle, grid):
    """Number of slots still satisfiable given current grid.
    A slot is satisfiable if at least one candidate fits the crossing pattern
    (already-filled cells match the candidate letter-by-letter)."""
    count = 0
    for s in puzzle["slots"]:
        cells = s["cells"]
        # if fully filled, check if it matches its answer (still satisfiable trivially)
        if all(isinstance(grid[r][c], str) and grid[r][c] not in ("",) for r, c in cells):
            count += 1
            continue
        pat = []
        for (r, c) in cells:
            v = grid[r][c]
            if isinstance(v, str) and v not in ("",):
                pat.append(v)
            else:
                pat.append(None)
        for cand in s["candidates"]:
            if len(cand) != s["length"]:
                continue
            ok = True
            for i, ch in enumerate(cand):
                if pat[i] is not None and pat[i] != ch:
                    ok = False
                    break
            if ok:
                count += 1
                break
    return count

# ---------- model call ----------
def model_call(model, messages, max_tokens=2000, timeout=300):
    url = MODEL_URLS[model]
    temp = 0.1 if model == "lfm3-1.7b" else 0.0
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temp,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        d = json.loads(resp.read())
    dt = time.time() - t0
    m = d["choices"][0]["message"]
    content = m.get("content") or ""
    reasoning = m.get("reasoning_content") or ""
    usage = d.get("usage", {})
    gen_tokens = usage.get("completion_tokens", 0)
    finish = d["choices"][0].get("finish_reason", "")
    return content, reasoning, gen_tokens, dt, finish

def parse_answer(content, reasoning, candidates):
    """Parse SLOT:/WORD: format. Returns (answer, field) where field is 'content' or 'reasoning'."""
    pat = re.compile(r'SLOT:\s*(\S+)\D+WORD:\s*(\S+)', re.IGNORECASE)
    for field, src in (("content", content), ("reasoning", reasoning)):
        if not src:
            continue
        matches = pat.findall(src)
        if matches:
            last = matches[-1]
            word = last[1].upper().strip(".,;:!?")
            return word, field
    # fallback: last candidate mentioned
    text = (content or "") + " " + (reasoning or "")
    last_cand = None
    for c in candidates:
        idx = text.upper().rfind(c.upper())
        if idx >= 0:
            if last_cand is None or idx > last_cand[0]:
                last_cand = (idx, c.upper())
    if last_cand:
        return last_cand[1], "reasoning"
    return None, None

def crossing_pattern(puzzle, grid, slot):
    pat = []
    for (r, c) in slot["cells"]:
        v = grid[r][c]
        if isinstance(v, str) and v not in ("",):
            pat.append(v)
        else:
            pat.append("?")
    return "".join(pat)

def build_prompt(puzzle, grid, label, slot):
    pat = crossing_pattern(puzzle, grid, slot)
    cands = slot["candidates"]
    clue = slot["clue"]
    cd = slot.get("clue_data", {})
    kind = cd.get("kind", "")
    extra = ""
    if kind == "anagram":
        extra = "Anagram: unscramble the letters '%s' into a word." % cd.get("letters", "")
    elif kind == "decoy":
        extra = "Decoy: subtract the word '%s' from the letters '%s' to get the answer." % (cd.get("decoy", ""), cd.get("letters", ""))
    ln = slot["length"]
    # explicit crossing letters
    crossing_info = []
    for i, (r, c) in enumerate(slot["cells"]):
        v = grid[r][c]
        if isinstance(v, str) and v not in ("",):
            crossing_info.append("position %d = %s" % (i+1, v))
    crossing_text = ", ".join(crossing_info) if crossing_info else "none yet"
    # filter candidates by crossing pattern
    matching = []
    for cand in cands:
        ok = True
        for i, ch in enumerate(cand):
            if i < len(pat) and pat[i] != "?" and pat[i] != ch:
                ok = False
                break
        if ok and len(cand) == ln:
            matching.append(cand)
    matching_text = ", ".join(matching) if matching else "(none)"
    msg = (
        "Criss-cross puzzle. Slot %s (%s, length %d).\n"
        "Clue: \"%s\"\n"
        "%s\n"
        "Candidates: %s\n"
        "Crossing pattern: %s (? = unknown)\n"
        "Letters already fixed at crossings: %s\n"
        "Candidates that match crossings: %s\n"
        "You MUST attempt every slot. Use the crossing letters to narrow the candidates, then commit the best candidate. Do not skip a slot.\n"
        "Pick the candidate that fits the clue and the crossing pattern.\n"
        "IMPORTANT: First line must be exactly: SLOT: %s · WORD: <answer>\n"
        "Then explain your reasoning.\n"
    ) % (label, slot["direction"], ln, clue, extra, ", ".join(cands), pat, crossing_text, matching_text, label)
    return msg

def available_memory_mb():
    """Available memory on macOS: free + inactive + speculative + purgeable (in MB)."""
    import subprocess, re
    try:
        out = subprocess.check_output(["vm_stat"], text=True)
    except Exception:
        return None
    page_size = 4096
    m = re.search(r"page size of (\d+) bytes", out)
    if m:
        page_size = int(m.group(1))
    def pages(label):
        mm = re.search(label + r":\s+(\d+)\.", out)
        return int(mm.group(1)) if mm else 0
    free = pages("Pages free")
    inactive = pages("Pages inactive")
    speculative = pages("Pages speculative")
    purgeable = pages("Pages purgeable")
    total_pages = free + inactive + speculative + purgeable
    return round(total_pages * page_size / (1024*1024), 1)

VOID_THRESHOLD_MB = 1024

# ---------- solving loop ----------
def solve(puzzle, model, max_turns=200, trace_path=None):
    mem_start = available_memory_mb()
    grid = blank_grid(puzzle)
    slots = puzzle["slots"]
    presented = puzzle["presented"]

    trace = {
        "puzzle": {"index": puzzle["puzzle_index"], "arm": puzzle["arm"],
                   "rows": puzzle["rows"], "cols": puzzle["cols"],
                   "grid_sha256": puzzle.get("grid_sha256")},
        "model": model,
        "model_url": MODEL_URLS.get(model),
        "max_tokens": 2000,
        "temperature": 0.1 if model == "lfm3-1.7b" else 0.0,
        "prompt_version": "crossword-harness-v2",
        "arm": puzzle["arm"],
        "mapping": [lbl for lbl, _ in presented],
        "card_version": "quiptic-generated",
        "freeze_digest": "crossword-harness-v2",
        "crate_digest": puzzle.get("crate_digest"),
        "crate_seed": puzzle.get("crate_seed"),
        "word_list_size": puzzle.get("word_list_size"),
        "words_sha256": puzzle.get("words_sha256"),
        "slot_clue_candidates": {s["id"]: s.get("clue_candidates", 0) for s in puzzle["slots"]},
        "slot_candidates": {s["id"]: s.get("candidates", []) for s in puzzle["slots"]},
        "ccr_status": "resolved: 6/18 (fills with occupied crossing consistent; 8/20 all fills)",
        "ccr_definition": "fills consistent with all already-filled crossings / fills that had at least one occupied crossing",
        "gates": {
            "degenerate_ceiling": "crate ceiling clue_resolved/slots (see crate)",
            "winnability_floor": puzzle.get("floor", {}).get("verdict") if isinstance(puzzle.get("floor"), dict) else puzzle.get("floor"),
            "freshness": "generated (grid did not exist before run)",
            "mapping_permutation": puzzle["arm"],
        },
        "turns": [],
        "termination": None,
        "fill_rate": 0.0,
        "contradiction_count": 0,
        "total_cells": total_white(puzzle),
        "filled_slots": 0,
        "correct_slots": 0,
        "slots_attempted": 0,
        "malformed_count": 0,
        "wrong_count": 0,
        "timeout_count": 0,
        "secs_total": 0.0,
        "gen_tokens_total": 0,
        "budget_hits": 0,
        "crossing_consistency_rate": 0.0,
        "mem_available_mb_start": mem_start,
        "mem_available_mb_end": None,
        "mem_void_threshold_mb": VOID_THRESHOLD_MB,
        "mem_void": (mem_start is not None and mem_start < VOID_THRESHOLD_MB),
    }

    solved_slots = set()
    contradictions = 0
    turn_idx = 0
    secs_total = 0.0
    gen_total = 0
    budget_hits = 0
    abandoned = False
    attempted_slots = set()
    malformed_count = 0
    wrong_count = 0
    timeout_count = 0

    max_passes = 3
    progress = True
    pass_num = 0
    while progress and pass_num < max_passes and turn_idx < max_turns and not is_solved(puzzle, grid):
        progress = False
        pass_num += 1
        for lbl, sl in presented:
            if sl["id"] in solved_slots:
                continue
            cells = sl["cells"]
            if all(isinstance(grid[r][c], str) and grid[r][c] not in ("",) for r, c in cells):
                solved_slots.add(sl["id"])
                continue
            if turn_idx >= max_turns:
                break
            print("PASS", pass_num, "CLUE", lbl, sl["id"], sl["clue"], flush=True, file=sys.stderr)
            last_wrong = None
            for attempt in range(2):
                msg = build_prompt(puzzle, grid, lbl, sl)
                if attempt > 0 and last_wrong:
                    msg += "\nPrevious answer '%s' invalid. Try another." % last_wrong
                messages = [{"role": "user", "content": msg}]
                try:
                    content, reasoning, gen_tokens, dt, finish = model_call(model, messages, max_tokens=2000, timeout=300)
                except Exception as ex:
                    timeout_count += 1
                    trace["turns"].append({"turn": turn_idx, "grid_state": grid_state_for_trace(grid),
                        "fill": {"slot": sl["id"], "word": None, "contradiction": False, "clue_candidates": sl.get("clue_candidates", 0)},
                        "eval_before": "error", "eval_after": "error", "secs": 0.0, "gen_tokens": 0,
                        "budget_hit": False, "error": str(ex),
                        "slot": sl["id"], "answer_submitted": None, "accepted": False,
                        "conflicts_with_crossings": False,
                        "answer_field": None})
                    # do not abandon on a single serving failure; skip this slot
                    break
                if abandoned:
                    break
                secs_total += dt
                gen_total += gen_tokens
                if finish == "length":
                    budget_hits += 1
                ans, ans_field = parse_answer(content, reasoning, sl["candidates"])
                if ans is not None:
                    attempted_slots.add(sl["id"])
                eval_before = eval_satisfiable(puzzle, grid)
                consistent = True
                if ans is None:
                    consistent = False
                else:
                    for (r, c), ch in zip(sl["cells"], ans):
                        cur = grid[r][c]
                        if isinstance(cur, str) and cur not in ("",) and cur != ch:
                            consistent = False
                            break
                cand_ok = ans is not None and ans in [c.upper() for c in sl["candidates"]] and len(ans) == sl["length"]
                contradiction = (ans is not None and not consistent)

                if ans is not None and consistent and cand_ok:
                    # apply whole slot at once
                    for (r, c), ch in zip(sl["cells"], ans):
                        apply_fill(grid, r, c, ch)
                    trace["turns"].append({"turn": turn_idx, "grid_state": grid_state_for_trace(grid),
                        "fill": {"slot": sl["id"], "word": ans, "contradiction": False, "clue_candidates": sl.get("clue_candidates", 0)},
                        "eval_before": eval_before, "eval_after": eval_satisfiable(puzzle, grid),
                        "secs": round(dt, 3), "gen_tokens": gen_tokens, "budget_hit": finish == "length",
                        "slot": sl["id"], "answer_submitted": ans, "accepted": True,
                        "conflicts_with_crossings": False,
                        "answer_field": ans_field})
                    turn_idx += 1
                    solved_slots.add(sl["id"])
                    progress = True
                    break
                else:
                    last_wrong = ans
                    if ans is None or not cand_ok:
                        malformed_count += 1
                    elif not consistent:
                        wrong_count += 1
                    trace["turns"].append({"turn": turn_idx, "grid_state": grid_state_for_trace(grid),
                        "fill": {"slot": sl["id"], "word": ans if ans else None, "contradiction": contradiction, "clue_candidates": sl.get("clue_candidates", 0)},
                        "eval_before": eval_before, "eval_after": eval_satisfiable(puzzle, grid),
                        "secs": round(dt, 3), "gen_tokens": gen_tokens, "budget_hit": finish == "length",
                        "slot": sl["id"], "answer_submitted": ans, "accepted": False,
                        "conflicts_with_crossings": (not consistent if ans is not None else False),
                        "answer_field": ans_field})
                    turn_idx += 1
                    if ans is not None and not consistent:
                        contradictions += 1
            if abandoned:
                break
        if abandoned:
            break
        flush_trace(trace, trace_path)

    consistent_count = sum(1 for t in trace["turns"] if t.get("fill", {}).get("word") is not None and not t.get("conflicts_with_crossings", False))
    fill_turns = sum(1 for t in trace["turns"] if t.get("fill", {}).get("word") is not None)
    # CCR resolved: consistent / fills with at least one occupied crossing (Jarvis definition)
    consistent_with_crossing = 0
    with_crossing = 0
    for t in trace["turns"]:
        f = t.get("fill", {})
        w = f.get("word") if isinstance(f, dict) else None
        if w is None:
            continue
        eb = t.get("eval_before")
        total_slots = len(puzzle["slots"])
        if isinstance(eb, int) and eb < total_slots:
            with_crossing += 1
            if not t.get("conflicts_with_crossings", False):
                consistent_with_crossing += 1
    ccr_resolved = (consistent_with_crossing / with_crossing) if with_crossing else 0.0
    ccr_all = (consistent_count / fill_turns) if fill_turns else 0.0
    trace["crossing_consistency_rate"] = round(ccr_resolved, 4)
    trace["ccr_all_fills"] = round(ccr_all, 4)
    trace["ccr_with_crossing_denominator"] = "%d/%d" % (consistent_with_crossing, with_crossing)
    trace["ccr_all_fills_denominator"] = "%d/%d" % (consistent_count, fill_turns)

    if is_solved(puzzle, grid):
        trace["termination"] = "solved"
    elif contradictions > 0:
        trace["termination"] = "contradicted"
    else:
        trace["termination"] = "abandoned"

    trace["contradiction_count"] = contradictions
    trace["filled_cells"] = count_filled(grid)
    trace["correct_cells"] = sum(1 for s in puzzle["slots"] for (r, c), ch in zip(s["cells"], s["answer"]) if grid[r][c] == ch)
    trace["filled_slots"] = sum(1 for s in puzzle["slots"] if all(isinstance(grid[r][c], str) and grid[r][c] not in ("",) for r, c in s["cells"]))
    trace["correct_slots"] = sum(1 for s in puzzle["slots"] if all(grid[r][c] == ch for (r, c), ch in zip(s["cells"], s["answer"])))
    trace["slots_attempted"] = len(attempted_slots)
    trace["malformed_count"] = malformed_count
    trace["wrong_count"] = wrong_count
    trace["timeout_count"] = timeout_count
    trace["fill_rate"] = count_filled(grid) / total_white(puzzle) if total_white(puzzle) else 0.0
    trace["secs_total"] = round(secs_total, 3)
    trace["gen_tokens_total"] = gen_total
    trace["budget_hits"] = budget_hits
    trace["mem_available_mb_end"] = available_memory_mb()
    trace["mem_void"] = trace["mem_void"] or (trace["mem_available_mb_end"] is not None and trace["mem_available_mb_end"] < VOID_THRESHOLD_MB)
    trace["solved"] = trace["termination"] == "solved" and trace["correct_cells"] == total_white(puzzle)

    if trace_path:
        os.makedirs(os.path.dirname(trace_path), exist_ok=True)
        with open(trace_path, "w") as f:
            json.dump(trace, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
    return trace

def flush_trace(trace, trace_path):
    if not trace_path:
        return
    os.makedirs(os.path.dirname(trace_path), exist_ok=True)
    with open(trace_path, "w") as f:
        json.dump(trace, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
def _self_test():
    crate = load_crate("/Users/mikebird/workspace/chair-link/archive/CROSSWORD_CRATE_2026-11-05.json")
    pz = make_puzzle(crate, 0, "published")
    print("puzzle 0 published: rows", pz["rows"], "cols", pz["cols"], "slots", len(pz["slots"]), "white", total_white(pz))
    g = blank_grid(pz)
    print("blank grid ok, white cells:", sum(1 for row in g for v in row if v == ""))
    for s in pz["slots"]:
        for (r, c), ch in zip(s["cells"], s["answer"]):
            g[r][c] = ch
    print("ground truth solved?", is_solved(pz, g))
    pz2 = make_puzzle(crate, 0, "permuted")
    print("permuted arm presented labels:", [lbl for lbl, _ in pz2["presented"]])
    print("SELF-TEST DONE")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crate")
    ap.add_argument("--puzzle", type=int, default=0)
    ap.add_argument("--arm", default="published", choices=["published", "permuted"])
    ap.add_argument("--model", default="ornith9b")
    ap.add_argument("--max-turns", type=int, default=200)
    ap.add_argument("--out")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return _self_test()
    if not args.crate:
        ap.error("--crate required")
    crate = load_crate(args.crate)
    pz_arm = crate["puzzles"][args.puzzle].get("arm", args.arm)
    pz = make_puzzle(crate, args.puzzle, pz_arm, crate_path=args.crate)
    out = args.out or os.path.join(TRACE_DIR, "crate_p%d_%s_%s.json" % (args.puzzle, pz_arm, args.model))
    trace = solve(pz, args.model, max_turns=args.max_turns, trace_path=out)
    print("termination:", trace["termination"])
    print("solved:", trace["solved"])
    print("filled:", trace["filled_cells"], "/", trace["total_cells"])
    print("correct:", trace["correct_cells"], "/", trace["total_cells"])
    print("filled_slots:", trace["filled_slots"], "/", len(pz["slots"]))
    print("correct_slots:", trace["correct_slots"], "/", len(pz["slots"]))
    print("contradictions:", trace["contradiction_count"])
    print("ccr:", trace["crossing_consistency_rate"])
    print("turns:", len(trace["turns"]))
    print("trace:", out)
    return 0

if __name__ == "__main__":
    sys.exit(main())