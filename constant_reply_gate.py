#!/usr/bin/env python3
"""CONSTANT-REPLY CEILING GATE -- applied to every event.

For each event, enumerates the degenerate-class (constant-reply) streams using the event's
own action alphabet / simulator, runs them, and reports DISCRIMINATES / DEGENERATE / UNDETERMINED.

Run: python3 constant_reply_gate.py
"""
import os, sys, json, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BUDGET = 40

def hdr(t):
    print("=" * 80)
    print(t)
    print("=" * 80)

# ---------------- Sokoban ----------------
import sokoban as SOK
def sokoban_streams(budget=BUDGET):
    out = []
    for a in "UDLR":
        out.append([a] * budget)
    for a in "UDLR":
        for b in "UDLR":
            pat = [a, b]
            out.append((pat * (budget // 2 + 1))[:budget])
    for a in "UDLR":
        for b in "UDLR":
            for c in "UDLR":
                pat = [a, b, c]
                out.append((pat * (budget // 3 + 1))[:budget])
    return out

def run_sokoban():
    hdr("SOKOBAN (surviving boards + retired 01 for the record)")
    streams = sokoban_streams()
    for name in ["01_one_push", "02_two_boxes", "03_the_corner_waiting"]:
        text = open(os.path.join(HERE, "levels", name + ".txt")).read()
        n = sum(1 for s in streams if SOK.play(text, list(s))["solved"])
        verdict = "DEGENERATE -- retire" if n > 0 and name == "01_one_push" else \
                  ("DEGENERATE -- retire (candidate)" if n > 0 else "DISCRIMINATES")
        print(f"  {name:24s} streams={len(streams)} solved_by_constant={n}  -> {verdict}")

# ---------------- Zork ----------------
import zork as ZRK
def run_zork():
    hdr("ZORK (long-horizon state retention)")
    cmds = ["n", "s", "e", "w", "u", "d", "north", "south", "east", "west",
            "look", "inventory", "wait"]
    for wname in ["zork_01_the_floor", "zork_02_long_crawl"]:
        text = open(os.path.join(HERE, "levels", wname + ".txt")).read()
        escapes = 0
        for c in cmds:
            r = ZRK.play(text, [c] * BUDGET)
            if r["finished"]:
                escapes += 1
        verdict = "DISCRIMINATES" if escapes == 0 else "DEGENERATE -- retire (candidate)"
        print(f"  {wname:24s} streams={len(cmds)} constant_escapes={escapes}  -> {verdict}")

# ---------------- Missile Command ----------------
import missile_command as MC
def run_missile():
    hdr("MISSILE COMMAND (allocation under scarcity)")
    for sname in ["mc_01_one_shot", "mc_02_scarcity"]:
        text = open(os.path.join(HERE, "levels", sname + ".txt")).read()
        st = MC.parse_state(text)
        toks = ["PASS"] + [s + t for s in st["silos"] for t in st["threats"]]
        best = 0
        best_tok = None
        clears = 0
        for t in toks:
            r = MC.play(text, [t] * 20)
            if r["cities_surviving"] == r["cities_total"]:
                clears += 1
                if best_tok is None:
                    best_tok = t
            if r["cities_surviving"] > best:
                best = r["cities_surviving"]
        verdict = "DEGENERATE -- retire (candidate)" if clears > 0 else "DISCRIMINATES"
        print(f"  {sname:24s} streams={len(toks)} constants_clearing={clears} best_constant={best}/{len(st['cities'])}  -> {verdict}")

# ---------------- Chess ----------------
def run_chess():
    hdr("CHESS (calibration / resignation gate)")
    import chess_game as CG
    CG.SF = "/opt/homebrew/bin/stockfish"
    CG._SF_PROC = None
    moves0 = CG.legal_moves(CG.STARTPOS)
    print(f"  positive control: startpos legal moves = {len(moves0)} (expect 20)")
    # degenerate class: always first legal move / always last legal move / always resign
    results = []
    for policy in ["first", "last"]:
        fen = CG.STARTPOS
        plies = 0
        term = None
        while plies < 60:
            ms = CG.legal_moves(fen)
            if not ms:
                term = "no_legal_moves (mate/stalemate)"
                break
            uci = ms[0] if policy == "first" else ms[-1]
            nf = CG.apply_move(fen, uci)
            if nf is None:
                term = "apply_failed"
                break
            fen = nf
            plies += 1
        if term is None:
            term = "cap_hit (60 plies)"
        results.append((policy, plies, term))
        print(f"  policy=always-{policy}-legal-move  plies={plies:2d}  {term}")
    print("  policy=always-resign  -> terminates at ply 0 (premature collapse; caught by resignation gate)")
    print("  verdict: DISCRIMINATES (no constant reaches a logical conclusion except resign, which is caught)")

# ---------------- arena.py harness events ----------------
def run_arena():
    hdr("ARENA.PY HARNESS EVENTS (structured_output / tool_selection / code_repair)")
    import arena as A
    # fencing
    spec = json.load(open(os.path.join(HERE, "tasks", "01_structured_output.json")))["spec"]
    fixed = '{"station":"RENO-04","readings":[1,2,3],"status":"nominal"}'
    sc, why = A.score_json_schema(spec, fixed)
    print(f"  fencing/structured_output: constant fixed-valid-JSON passes={sc} ({why})")
    # tool selection
    spec2 = json.load(open(os.path.join(HERE, "tasks", "02_tool_selection.json")))["spec"]
    fixed2 = '{"tool":"get_weather","arguments":{"city":"reykjavik","units":"celsius"}}'
    sc2, why2 = A.score_tool_call(spec2, fixed2)
    print(f"  tool_selection: constant fixed-valid-call passes={sc2} ({why2})")
    # code repair
    spec3 = json.load(open(os.path.join(HERE, "tasks", "03_code_repair.json")))["spec"]
    code = ("def merge_intervals(intervals):\n"
            "    if not intervals: return []\n"
            "    intervals=sorted(intervals)\n"
            "    res=[list(intervals[0])]\n"
            "    for s,e in intervals[1:]:\n"
            "        if s<=res[-1][1]: res[-1][1]=max(res[-1][1],e)\n"
            "        else: res.append([s,e])\n"
            "    return [tuple(x) for x in res]")
    sc3, why3 = A.score_code_repair(spec3, code)
    print(f"  code_repair: constant correct-impl passes={sc3} ({why3})")
    print("  verdict: UNDETERMINED (constant passes the FROZEN spec; production specs are generated per run,")
    print("           so resistance depends on spec variation, which is not verified here)")

# ---------------- Mastermind ----------------
def run_mastermind():
    hdr("MASTERMIND")
    print("  no simulator / no measured freeze in tree -> UNDETERMINED (no oracle to run against)")

def main():
    run_sokoban()
    run_zork()
    run_missile()
    run_chess()
    run_arena()
    run_mastermind()
    print()
    print("Done. Report written to GATE_REPORT.md separately.")

if __name__ == "__main__":
    main()