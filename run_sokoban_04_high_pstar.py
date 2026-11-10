#!/usr/bin/env python3
"""Axis-labelled Sokoban harness for board records/04_high_pstar.json.

Renders the board with explicit row/column indices + a legality-rules block
(bare ASCII boards are forbidden -- R/L were unstable without indices).
Prompts the model to emit `MOVE: <U|D|L|R>` on the first line, then reasoning.
Parses ONLY `^MOVE:\\s*([UDLR])` (multiline) -- no last-standalone-letter fallback,
so a plan's ninth move can never be committed as the chosen move.

Usage:
  python3 sokoban_harness.py --self-test            # parser + render checks
  python3 sokoban_harness.py --dry-run              # full flow against an in-process stub
  python3 sokoban_harness.py                       # real run vs ornith9b on :8360
  python3 sokoban_harness.py --base-dir /path      # override arena root (records/traces)
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request

DEFAULT_BASE = "/Users/mikebird/arena/handicap-arena"
BOARD_NAME = "04_high_pstar"
MODEL_NAME = "ornith9b"
MODEL_URL_DEFAULT = "http://127.0.0.1:8360/v1/chat/completions"
TURNS = 30
MAX_TOKENS = 6000
HTTP_TIMEOUT = 300
CONTROL_TIMEOUT = 300
CONTROL_PROMPT = "Reply with the single letter D"
VOID_LATENCY_S = 60

MOVE_RE = re.compile(r"^MOVE:\s*([UDLR])", re.IGNORECASE | re.MULTILINE)


def parse_move(text):
    """Return (move_letter_or_None, status). status in {'ok','malformed'}.

    NO last-standalone-letter fallback. A plan whose ninth character is a move
    letter does NOT parse, because there is no MOVE: header on the first line.
    """
    if not text:
        return None, "malformed"
    m = re.search(r"^MOVE:\s*([UDLR])", text, re.IGNORECASE | re.MULTILINE)
    if m:
        return m.group(1).upper(), "ok"
    return None, "malformed"


def _import_sokoban(base_dir):
    sys.path.insert(0, base_dir)
    import sokoban as S
    return S


def _level_text(base_dir, board_name):
    rec_path = os.path.join(base_dir, "records", board_name + ".json")
    rec = {}
    if os.path.exists(rec_path):
        with open(rec_path) as f:
            rec = json.load(f)
        rel = rec.get("file") or ("levels/" + board_name + ".txt")
        p = os.path.join(base_dir, rel)
        if os.path.exists(p):
            return open(p).read(), rec
    p = os.path.join(base_dir, "levels", board_name + ".txt")
    return open(p).read(), rec


def render_axis(st, S):
    rows = st["rows"]
    cols = st["cols"]
    board_lines = S.render(st).splitlines()
    header = "    " + " ".join(str(c % 10) for c in range(cols))
    ruler = "    " + "-" * (cols * 2 - 1)
    out = []
    out.append("Columns: " + ", ".join(str(c) for c in range(cols)))
    out.append("Rows:    " + ", ".join(str(r) for r in range(rows)))
    out.append("")
    out.append(header)
    out.append(ruler)
    for r, line in enumerate(board_lines):
        out.append(f"{r:2d} | " + " ".join(ch for ch in line.ljust(cols)))
    out.append("")
    out.append("Legend: # wall, . target, $ box, @ player, * box on target, + player on target, (space) floor.")
    out.append("Rules:  U=up D=down L=left R=right.")
    out.append("        A move into a wall (#) or off the board is ILLEGAL (blocked, no-op).")
    out.append("        Pushing a box into a wall, another box, or off the board is ILLEGAL (blocked, no-op).")
    out.append("        A move onto a target (.) or a box push onto a target is LEGAL.")
    out.append("        Boxes can be pushed but never pulled; one wrong push can end the level.")
    return "\n".join(out)


def build_prompt(board_text_axis, recent):
    return (
        "You are playing Sokoban. Goal: push all boxes ($) onto targets (.).\n\n"
        "Board (axis-labelled; indices are 0-based row/col):\n\n"
        + board_text_axis
        + "\n\n"
        + "Moves made so far: " + (recent if recent else "(none)") + "\n\n"
        + "First line exactly: MOVE: <one of U D L R>\n"
        + "Then your reasoning."
    )


def model_call(url, prompt, max_tokens, timeout):
    payload = json.dumps({
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.0,
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return None, None, time.time() - t0, None, str(e)
    secs = time.time() - t0
    msg = data.get("choices", [{}])[0].get("message", {})
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning_content") or ""
    tokens = data.get("usage", {}).get("completion_tokens", 0)
    return content, reasoning, secs, tokens, None


class StubModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.i = 0

    def call(self, url, prompt, max_tokens, timeout):
        r = self.responses[self.i % len(self.responses)]
        self.i += 1
        return r.get("content", ""), r.get("reasoning", ""), 0.01, r.get("tokens", 5), None

    def control(self, url, timeout):
        return 0.01, "D", 1, None


STUB_RESPONSES = [
    {"content": "MOVE: D\nReasoning: go down one step.", "reasoning": "", "tokens": 12},
    {"content": "MOVE: R\n\nBecause the box must move right.", "reasoning": "", "tokens": 15},
    {"content": "U D L R U D L R D", "reasoning": "", "tokens": 20},
    {"content": "MOVE: L\nPlan continues: R L R L R L R L D", "reasoning": "", "tokens": 18},
    {"content": "MOVE: U\nReasoning: up is safe.", "reasoning": "", "tokens": 10},
]


def self_test(base_dir):
    S = _import_sokoban(base_dir)
    fails = []

    def ck(name, got, want):
        nonlocal fails
        ok = got == want
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            print(f"          got  {got!r}\n          want {want!r}")
            fails.append(name)

    print("=" * 70)
    print("PARSER + RENDER SELF-TEST")
    print("=" * 70)

    print("\n[parser]")
    m, st = parse_move("MOVE: D")
    ck("clean MOVE: D -> D", (m, st), ("D", "ok"))
    m, st = parse_move("MOVE: D\n\nReasoning: go down.")
    ck("reasoning after first line -> D", (m, st), ("D", "ok"))
    m, st = parse_move("U D L R U D L R D")
    ck("plan ninth move must NOT parse", (m, st), (None, "malformed"))
    m, st = parse_move("MOVE: U\nPlan: R L R L R L R L D")
    ck("MOVE: U with plan ninth D -> U (not D)", (m, st), ("U", "ok"))
    m, st = parse_move("")
    ck("empty -> malformed", (m, st), (None, "malformed"))
    m, st = parse_move("D")
    ck("bare letter -> malformed (no fallback)", (m, st), (None, "malformed"))
    m, st = parse_move("  MOVE: D")
    ck("leading whitespace -> malformed (strict)", (m, st), (None, "malformed"))

    print("\n[render]")
    level_text, rec = _level_text(base_dir, BOARD_NAME)
    st0 = S.parse(level_text)
    r = render_axis(st0, S)
    ck("render contains column indices", "Columns:" in r, True)
    ck("render contains row indices", "Rows:" in r, True)
    ck("render contains legality rules", "ILLEGAL" in r, True)
    ck("render contains legend", "Legend:" in r, True)
    ck("render is not bare board", r != S.render(st0), True)

    print("\n" + "=" * 70)
    if fails:
        print(f"FAILED: {len(fails)} case(s): {fails}")
        return 1
    print("ALL SELF-TESTS PASS")
    return 0


def run(base_dir, dry_run=False, turns=TURNS, trace_dir=None):
    S = _import_sokoban(base_dir)
    level_text, rec = _level_text(base_dir, BOARD_NAME)
    st = S.parse(level_text)

    if dry_run:
        model = StubModel(STUB_RESPONSES)
        url = "stub://local"
    else:
        model = None
        url = MODEL_URL_DEFAULT

    def call(prompt, max_tokens, timeout):
        if dry_run:
            return model.call(url, prompt, max_tokens, timeout)
        return model_call(url, prompt, max_tokens, timeout)

    def control():
        if dry_run:
            return model.control(url, CONTROL_TIMEOUT)
        secs, content, reasoning, tokens, err = model_call(url, CONTROL_PROMPT, 64, CONTROL_TIMEOUT)
        return secs, (content or reasoning or "").strip(), tokens, err

    print("Running BEFORE control...")
    cb = control()
    if isinstance(cb, tuple) and len(cb) == 4:
        before_secs, before_resp, before_tokens, before_err = cb
    else:
        before_secs, before_resp = cb
        before_tokens, before_err = 0, None
    print(f"  BEFORE control: {before_secs:.2f}s -> {before_resp!r}")
    if before_err:
        print(f"  ERROR: {before_err}")
    if (before_err is not None) or (before_secs > VOID_LATENCY_S):
        print("VOID: BEFORE control failed/stalled. Recording nothing.")
        return 2

    trace = []
    moves = 0
    pushes = 0
    blocked = 0
    malformed = 0
    solved = False
    recent = []

    for i in range(turns):
        board_axis = render_axis(st, S)
        prompt = build_prompt(board_axis, ", ".join(recent[-5:]))
        try:
            content, reasoning, secs, tokens, err = call(prompt, MAX_TOKENS, HTTP_TIMEOUT)
        except Exception as e:
            err = str(e)
            content, reasoning, secs, tokens = None, None, 0, None
        if err:
            print(f"Turn {i}: STALL/ERROR ({err}) - recorded as stall, not malformed")
            trace.append({
                "turn": i,
                "raw_response": None,
                "raw_content": None,
                "raw_reasoning": None,
                "parsed_move": None,
                "status": "stall",
                "error": err,
                "secs": secs,
                "completion_tokens": tokens,
                "board_state": S.render(st),
                "board_axis": board_axis,
                "legality": "stall",
                "outcome": "stall",
            })
            break
        raw_text = content if (content or "").strip() else (reasoning or "")
        move, status = parse_move(raw_text)
        if status == "malformed":
            malformed += 1
            legality = "malformed"
            outcome = "malformed"
            new_st = st
        else:
            new_st, outcome = S.step(st, move)
            if outcome == "pushed":
                pushes += 1
            elif outcome == "blocked":
                blocked += 1
            if outcome in ("moved", "pushed"):
                moves += 1
            st = new_st
            if move in ("U", "D", "L", "R"):
                recent.append(move)
            legality = outcome
        trace.append({
            "turn": i,
            "raw_response": raw_text,
            "raw_content": content,
            "raw_reasoning": reasoning,
            "parsed_move": (None if status == "malformed" else move),
            "status": status,
            "secs": secs,
            "completion_tokens": tokens,
            "board_state": S.render(st),
            "board_axis": board_axis,
            "legality": legality,
            "outcome": outcome,
        })
        print(f"Turn {i}: parsed={move if status!='malformed' else None} status={status} outcome={outcome} moves={moves} pushes={pushes} tok={tokens} ({secs:.1f}s)")

        if S.solved(st):
            solved = True
            print(f"SOLVED in {moves} moves, {pushes} pushes!")
            break

    print("Running AFTER control...")
    ca = control()
    if isinstance(ca, tuple) and len(ca) == 4:
        after_secs, after_resp, after_tokens, after_err = ca
    else:
        after_secs, after_resp = ca
        after_tokens, after_err = 0, None
    print(f"  AFTER control: {after_secs:.2f}s -> {after_resp!r}")
    if after_err:
        print(f"  ERROR: {after_err}")

    void = False
    if before_err is not None or after_err is not None:
        void = True
    if before_secs > VOID_LATENCY_S or after_secs > VOID_LATENCY_S:
        void = True

    if void:
        print("VOID: a control failed/stalled (>60s or error). Recording nothing (no trace).")
        return 3

    ts = time.strftime("%Y%m%dT%H%M%S")
    prefix = "sokoban_04_high_pstar_STUB" if dry_run else "sokoban_04_high_pstar_ornith9b"
    if trace_dir is None:
        trace_dir = os.path.join(base_dir, "traces")
    os.makedirs(trace_dir, exist_ok=True)
    out_path = os.path.join(trace_dir, f"{prefix}_{ts}.json")
    out = {
        "board": BOARD_NAME,
        "model": "stub" if dry_run else MODEL_NAME,
        "endpoint": "stub" if dry_run else url,
        "max_tokens": MAX_TOKENS,
        "turns_budget": turns,
        "turns_used": len(trace),
        "solved": solved,
        "moves": moves,
        "pushes": pushes,
        "blocked": blocked,
        "malformed": malformed,
        "optimal_moves": rec.get("optimal_moves"),
        "gate_width": rec.get("gate_width"),
        "p_star": rec.get("p_star"),
        "before_control": {"latency_s": before_secs, "response": before_resp, "completion_tokens": before_tokens},
        "after_control": {"latency_s": after_secs, "response": after_resp, "completion_tokens": after_tokens},
        "trace": trace,
        "final_board": S.render(st),
    }
    with open(out_path, "x") as f:
        json.dump(out, f, indent=2)
    print(f"\nTrace written (once): {out_path}")
    print(f"Verdict: {'SOLVED' if solved else 'UNSOLVED'} | moves={moves} pushes={pushes} blocked={blocked} malformed={malformed} turns={len(trace)}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", default=DEFAULT_BASE, help="arena root (records/, levels/, traces/)")
    ap.add_argument("--dry-run", action="store_true", help="run against in-process stub model")
    ap.add_argument("--self-test", action="store_true", help="run parser + render checks")
    ap.add_argument("--turns", type=int, default=TURNS)
    ap.add_argument("--trace-dir", default=None, help="override trace output directory")
    args = ap.parse_args()

    base_dir = args.base_dir

    if args.self_test:
        sys.exit(self_test(base_dir))

    rc = run(base_dir, dry_run=args.dry_run, turns=args.turns, trace_dir=args.trace_dir)
    sys.exit(rc)


if __name__ == "__main__":
    main()
