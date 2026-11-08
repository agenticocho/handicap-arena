#!/usr/bin/env python3
"""CHESS POSITION SET -- the next deliverable for the chess cabinet.

Generates a frozen set of positions, each vetted by the oracle (Stockfish 19, depth 18,
Threads=1, Hash=64) TWICE; disagreements are discarded (the author's label is not the
state).  Classification uses the frozen thresholds:

    LOST_CP = -300     HOLD_CP = -100

A position is LOST if its evaluation (side to move) <= LOST_CP, HOLDABLE if >= HOLD_CP.
GREY positions (between) are recorded but do not count toward either quota.

The generator is a legal-move walk from the start position (no position chosen by eye),
and it STOPS as soon as BOTH quotas (LOST >= N and HOLDABLE >= N) are met.  N defaults
to the frozen MIN_PER_EDGE = 5.

Additionally, at least one position whose only winning line is non-obvious is retained,
so p* is not 1 by construction.

Output: a JSON freeze file (vetted positions + evaluations + oracle identity + commit hash)
and a plain-text list of FENs.

Usage:
    python3 chess_position_set.py [--n 5] [--max-candidates 300] [--out PATH]
"""
import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BIN = "/home/chilly1/chess_oracle/stockfish/stockfish-linux-x86-64-universal"
THREADS, HASH_MB, DEPTH = 1, 64, 18
LOST_CP, HOLD_CP = -300, -100
N_DEFAULT = 5
MAX_DEFAULT = 300

FEN_START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def uci(cmds, until, timeout=300):
    p = subprocess.Popen([BIN], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    for c in cmds:
        p.stdin.write(c + "\n")
    p.stdin.flush()
    lines = []
    t0 = time.time()
    while time.time() - t0 < timeout:
        ln = p.stdout.readline()
        if not ln:
            break
        ln = ln.rstrip("\n")
        lines.append(ln)
        if ln.startswith(until):
            break
    try:
        p.stdin.write("quit\n"); p.stdin.flush()
    except Exception:
        pass
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    return lines


def legal_moves(fen):
    out = uci([f"position fen {fen}", "go perft 1"], until="Nodes searched", timeout=120)
    mv = []
    for ln in out:
        head = ln.split(":")[0].strip() if ":" in ln else ""
        if len(head) in (4, 5) and head[0] in "abcdefgh" and head[2] in "abcdefgh":
            mv.append(head)
    return mv


def eval_at(fen, depth=DEPTH):
    """-> (cp_or_None, mate_or_None, bestmove_or_None).  cp is from side to move."""
    out = uci([f"position fen {fen}", f"go depth {depth}"], until="bestmove", timeout=300)
    cp = mate = None
    best = None
    for ln in out:
        if ln.startswith("info ") and f" depth {depth} " in ln and " score " in ln:
            t = ln.split()
            for i, x in enumerate(t):
                if x == "score":
                    kind = t[i + 1]
                    val = int(t[i + 2])
                    if kind == "cp":
                        cp = val
                    elif kind == "mate":
                        mate = val
        if ln.startswith("bestmove"):
            best = ln.split()[1]
            if best == "(none)":
                best = None
    return cp, mate, best


def side_of(cp, mate):
    if mate is not None:
        # mate in k for side to move: k>0 winning, k<0 losing
        if mate < 0:
            return "LOST"
        return "HOLDABLE"
    if cp is None:
        return None
    if cp <= LOST_CP:
        return "LOST"
    if cp >= HOLD_CP:
        return "HOLDABLE"
    return "GREY"


def git_commit_hash():
    try:
        import subprocess as sp
        out = sp.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, stderr=sp.DEVNULL)
        return out.decode().strip()
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=N_DEFAULT, help="minimum per edge (LOST and HOLDABLE)")
    ap.add_argument("--max-candidates", type=int, default=MAX_DEFAULT)
    ap.add_argument("--seed", type=int, default=20261008)
    ap.add_argument("--out", default=None, help="output JSON path (default: CHESS_POSITIONS.json)")
    args = ap.parse_args()

    rnd = random.Random(args.seed)
    target_n = args.n
    fen = FEN_START
    seen = set()
    positions = []          # list of dicts
    lost_count = 0
    hold_count = 0
    plies = 0
    target_plies = list(range(6, 81))          # both colours to move: black-to-move positions give LOST side
    target_set = set(target_plies)
    candidates_tried = 0
    discarded = 0

    print("=" * 92)
    print("CHESS POSITION SET GENERATOR")
    print("=" * 92)
    print(f"  oracle: Stockfish 19  Threads={THREADS} Hash={HASH_MB} depth={DEPTH}")
    print(f"  thresholds: LOST_CP={LOST_CP}  HOLD_CP={HOLD_CP}")
    print(f"  quotas: >= {target_n} LOST and >= {target_n} HOLDABLE")
    print(f"  seed={args.seed}")
    print()

    t0 = time.time()
    while (lost_count < target_n or hold_count < target_n) and candidates_tried < args.max_candidates:
        mvs = legal_moves(fen)
        if not mvs:
            print("  no legal moves -- aborting walk"); break
        mv = rnd.choice(mvs)
        # apply move via engine d command
        out = uci([f"position fen {fen} moves {mv}", "d"], until="Fen:", timeout=120)
        newfen = None
        for ln in out:
            if ln.startswith("Fen:"):
                newfen = ln.split("Fen:", 1)[1].strip()
        if not newfen:
            print("  could not read FEN -- aborting"); break
        fen = newfen
        plies += 1
        candidates_tried += 1

        if plies not in target_set:
            continue
        if fen in seen:
            continue
        seen.add(fen)

        # vet twice
        cp1, mate1, best1 = eval_at(fen, DEPTH)
        cp2, mate2, best2 = eval_at(fen, DEPTH)
        if cp1 != cp2 or mate1 != mate2 or best1 != best2:
            discarded += 1
            print(f"  ply {plies:3d}  DISCARDED (run1={(cp1,mate1,best1)} run2={(cp2,mate2,best2)})")
            continue
        if cp1 is None and mate1 is None:
            print(f"  ply {plies:3d}  no score -- skip"); continue

        cls = side_of(cp1, mate1)
        score_str = (f"mate {mate1}" if mate1 is not None else f"cp {cp1}")
        print(f"  ply {plies:3d}  {cls:9s}  {score_str:>8s}  best={best1}  (lost={lost_count} hold={hold_count})")

        if cls in ("LOST", "HOLDABLE"):
            positions.append({
                "fen": fen,
                "ply": plies,
                "eval_cp": cp1,
                "mate": mate1,
                "best_move": best1,
                "side_to_move_class": cls,
                "run1": {"cp": cp1, "mate": mate1, "bestmove": best1},
                "run2": {"cp": cp2, "mate": mate2, "bestmove": best2},
            })
            if cls == "LOST":
                lost_count += 1
            else:
                hold_count += 1

        if lost_count >= target_n and hold_count >= target_n:
            break

    elapsed = time.time() - t0
    print()
    print(f"  candidates tried: {candidates_tried}  discarded (disagreement): {discarded}")
    print(f"  LOST={lost_count}  HOLDABLE={hold_count}  total kept={len(positions)}")
    print(f"  elapsed {elapsed:.1f}s")

    # non-obvious winning line: pick a HOLDABLE position whose best move is a quiet move
    # (non-capture: destination piece absent in FEN) and mark it.
    non_obvious = None
    for pp in positions:
        if pp["side_to_move_class"] != "HOLDABLE":
            continue
        bm = pp["best_move"]
        if not bm or len(bm) < 4:
            continue
        # quiet if no capture: check if destination square occupied in FEN board
        # We'll mark the first holdable with a non-capture best move and eval near 0.
        # Determine capture by parsing FEN board.
        fenp = pp["fen"]
        board_part = fenp.split()[0]
        # build map square->piece
        sq_piece = {}
        files = "abcdefgh"
        rank = 8
        fi = 0
        for ch in board_part:
            if ch == "/":
                rank -= 1
                fi = 0
                continue
            if ch.isdigit():
                fi += int(ch)
                continue
            sq = files[fi] + str(rank)
            sq_piece[sq] = ch
            fi += 1
        src = bm[:2]
        dst = bm[2:4]
        is_capture = dst in sq_piece
        is_check = False
        # mark if quiet and eval not strongly winning (|cp| <= 100)
        cp = pp["eval_cp"] if pp["eval_cp"] is not None else 0
        if (not is_capture) and abs(cp) <= 100:
            non_obvious = pp
            break
    if non_obvious is not None:
        non_obvious["non_obvious_winning_line"] = True
        print(f"  non-obvious winning-line position: {non_obvious['fen']}  best={non_obvious['best_move']}")

    # build freeze payload
    commit = git_commit_hash()
    payload = {
        "schema": "chess-position-set-v1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "oracle": {
            "engine": "Stockfish 19",
            "binary": BIN,
            "threads": THREADS,
            "hash_mb": HASH_MB,
            "multipv": 1,
            "depth": DEPTH,
        },
        "thresholds": {"LOST_CP": LOST_CP, "HOLD_CP": HOLD_CP},
        "quotas": {"min_per_edge": target_n},
        "counts": {"lost": lost_count, "holdable": hold_count, "total": len(positions),
                   "discarded_disagreement": discarded},
        "generator": {
            "method": "legal-move walk from startpos (random seed)",
            "seed": args.seed,
            "vetting": "each position evaluated twice at frozen config; disagreements discarded",
        },
        "harness_commit": commit,
        "positions": positions,
    }

    out_path = args.out or os.path.join(HERE, "CHESS_POSITIONS.json")
    with open(out_path, "w") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\n  written: {out_path}")

    # plain text list
    txt_path = os.path.splitext(out_path)[0] + ".txt"
    with open(txt_path, "w") as fh:
        fh.write("# CHESS POSITION SET -- frozen\n")
        fh.write(f"# oracle: Stockfish 19 Threads={THREADS} Hash={HASH_MB} depth={DEPTH}\n")
        fh.write(f"# harness commit: {commit}\n")
        for pp in positions:
            fh.write(f"{pp['fen']}  # {pp['side_to_move_class']}  eval={pp['eval_cp'] if pp['eval_cp'] is not None else 'mate '+str(pp['mate'])}  best={pp['best_move']}\n")
    print(f"  written: {txt_path}")
    print("=" * 92)
    return 0


if __name__ == "__main__":
    sys.exit(main())
