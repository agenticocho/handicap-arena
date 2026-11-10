#!/usr/bin/env python3
"""Sokoban player for 02_two_boxes. Model plays, simulator judges."""
import json, os, sys, time, urllib.request, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban

LEVEL = os.path.join(HERE, "levels", "04_the_long_road.txt")
MODEL_URL = "http://127.0.0.1:8360/v1/chat/completions"
MODEL_NAME = "ornith9b"
BUDGET = 5

def model_call(prompt, max_tokens=3000):
    payload = json.dumps({
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.0,
    }).encode()
    req = urllib.request.Request(MODEL_URL, data=payload, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read())
    secs = time.time() - t0
    msg = data["choices"][0]["message"]
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning_content") or ""
    tokens = data.get("usage", {}).get("completion_tokens", 0)
    return content, reasoning, secs, tokens

def parse_move(text):
    """Strict parse: ^MOVE:\\s*([UDLR]) on first line. No match = malformed."""
    text = (text or "").strip()
    m = re.search(r'^MOVE:\s*([UDLR])', text, re.IGNORECASE)
    if m:
        return m.group(1).upper(), "ok"
    return None, "malformed"

def main():
    level_text = open(LEVEL).read()
    st = sokoban.parse(level_text)
    trace = []
    moves = 0
    pushes = 0
    blocked = 0
    malformed = 0
    solved = False
    deadlock = False

    for i in range(BUDGET):
        board = sokoban.render(st)
        prompt = f"""You are playing Sokoban. The board is:

{board}

Legend: # wall, . target, $ box, @ player, * box on target, + player on target, (space) floor.

Goal: push all boxes ($) onto targets (.).

Rules: U=up, D=down, L=left, R=right. A move into # (wall) is illegal. Pushing a box into a wall or another box is illegal.

First line exactly: MOVE: <one of U D L R>
Then your reasoning."""

        try:
            content, reasoning, secs, tokens = model_call(prompt)
        except Exception as e:
            print(f"Model call failed: {e}", file=sys.stderr)
            break

        # Parse content first, then reasoning
        text = content if content.strip() else reasoning
        action, status = parse_move(text)
        if status == "malformed":
            malformed += 1
            trace.append({"turn": i, "board": board, "content": content, "reasoning": reasoning, "action": None, "outcome": "malformed", "secs": secs, "tokens": tokens, "completion_tok": tokens})
            print(f"Turn {i}: MALFORMED (tok={tokens})")
            continue

        new_st, outcome = sokoban.step(st, action)
        if outcome == "pushed":
            pushes += 1
        elif outcome == "blocked":
            blocked += 1
        if outcome in ("moved", "pushed"):
            moves += 1
        st = new_st
        trace.append({"turn": i, "board": board, "content": content, "reasoning": reasoning, "action": action, "outcome": outcome, "secs": secs, "tokens": tokens, "completion_tok": tokens})
        print(f"Turn {i}: {action} -> {outcome} (moves={moves}, pushes={pushes}, tok={tokens})")

        if sokoban.solved(st):
            solved = True
            print(f"SOLVED in {moves} moves, {pushes} pushes!")
            break

    # Write trace
    out = {
        "level": "02_two_boxes",
        "model": "ornith9b (resident, :8360)",
        "max_tokens": 3000,
        "budget": BUDGET,
        "solved": solved,
        "moves": moves,
        "pushes": pushes,
        "blocked": blocked,
        "malformed": malformed,
        "turns": len(trace),
        "trace": trace,
        "final_board": sokoban.render(st),
    }
    out_path = os.path.join(HERE, "traces", "sokoban_02_two_boxes_ornith9b.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nTrace written to {out_path}")
    print(f"Verdict: {'SOLVED' if solved else 'UNSOLVED'}")
    print(f"Moves: {moves}, Pushes: {pushes}, Blocked: {blocked}, Malformed: {malformed}")

if __name__ == "__main__":
    main()
