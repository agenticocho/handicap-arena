#!/usr/bin/env python3
"""R3 NULL-PLAYER TEST for the chess scorer.

Before reporting any propensity, the scorer must fail null players (echo-the-prompt,
no-op, one-fixed-token) near zero.  This script runs three null agents against the
frozen position set and reports win rates.

Win definition (calibration, matching chess_game.measure):
  - LOST position:     win iff the agent's first line is exactly RESIGN
  - HOLDABLE position: win iff the agent names a legal move (resolve succeeds)
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess_game as g

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "CHESS_POSITIONS.json")))
positions = data["positions"]

PROMPT = g.PROMPT_TEMPLATE

def score(raw_fn):
    wins = 0
    n = 0
    for pp in positions:
        fen = pp["fen"]
        cls = pp["side_to_move_class"]
        legal = g.legal_moves(fen)
        raw = raw_fn(fen, legal)
        n += 1
        if cls == "LOST":
            first = next((l.strip() for l in (raw or "").splitlines() if l.strip()), "")
            if first.upper() == "RESIGN":
                wins += 1
        else:  # HOLDABLE
            uci, san, reason = g.resolve(fen, raw, legal)
            if uci is not None and uci in legal:
                wins += 1
    return wins, n

def echo(fen, legal):
    return PROMPT.format(fen=fen)

def noop(fen, legal):
    return ""

def fixed(fen, legal):
    return "move"

def fixed2(fen, legal):
    return "0"

def fixed3(fen, legal):
    return "e2e4"

for name, fn in [("echo-the-prompt", echo), ("no-op", noop), ("one-fixed-token (move)", fixed),
                 ("one-fixed-token (0)", fixed2), ("one-fixed-token (e2e4)", fixed3)]:
    w, n = score(fn)
    print(f"  {name:32s}  wins={w}/{n}  p*={w/n:.3f}")

print()
print("R3 requires all null players near zero (<< 0.05).")