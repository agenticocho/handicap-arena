#!/usr/bin/env python3
"""VERIFY THE SIX CLAIMS FROM THE INDEPENDENT IMPLEMENTATIONS, AGAINST MY OWN CODE.

Every item in PENDING_RULINGS_independent_implementations.md is a claim about an artifact in THIS repo. A claim
about my artifact gets read from the artifact, not from the document that reports it -- the rule that has held all
night. This script answers each one empirically and prints the evidence, so the ruling rests on what the code does
rather than on what two other implementations say it does.

    python3 verify_pending_rulings.py
"""
import collections
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban as S                                                     # noqa: E402

GRAMMAR = os.path.expanduser("~/.hermes/workspace/SOKOBAN_READ_GRAMMAR.md")
if not os.path.exists(os.path.join(HERE, "SOKOBAN_READ_GRAMMAR.md")):
    GRAMMAR = os.path.join(HERE, "SOKOBAN_READ_GRAMMAR.md")
else:
    GRAMMAR = os.path.join(HERE, "SOKOBAN_READ_GRAMMAR.md")

print("=" * 100)
print("VERIFYING THE SIX CLAIMS AGAINST THE ARTIFACTS")
print("=" * 100)

# ---- R1: IS AN ABSTENTION TOKEN NAMED ANYWHERE?
print("\nR1 -- THE ABSTENTION TOKEN")
print(f"  GIVE_UP_TOKENS in sokoban.py : {sorted(getattr(S, 'GIVE_UP_TOKENS', []))}")
g = open(GRAMMAR).read() if os.path.exists(GRAMMAR) else ""
print(f"  grammar file                 : {'FOUND' if g else 'MISSING'} ({len(g)} chars)")
for tok in ("RESIGN", "RESIGNS", "GIVEUP", "GIVE UP", "STUCK", "ABSTAIN", "SURRENDER", "QUIT"):
    print(f"    {tok!r:12s} appears in the grammar: {tok in g}")

# ---- R2: COUNT THE OPTIMA. Is 'the solution' unique for 02?
print("\nR2 -- HOW MANY OPTIMAL SOLUTIONS DOES EACH LEVEL HAVE?")


def count_optima(level_text, cap_states=200000):
    """Enumerate DISTINCT MOVE SEQUENCES of the optimal length. Returns (optimal_length, count, truncated)."""
    st = S.parse(level_text)
    targets = frozenset(st["targets"])
    start = (st["player"], frozenset(st["boxes"]))
    if frozenset(st["boxes"]) == targets:
        return 0, 1, False
    seen = {start: 0}                       # best depth per state
    frontier = [start]
    depth, expanded = 0, 0
    while frontier and expanded < cap_states:
        depth += 1
        nxt = []
        for state in frontier:
            player, boxes = state
            cur = dict(st, player=player, boxes=set(boxes))
            for a in S.ACTIONS:
                ns, outcome = S.step(cur, a)
                if outcome not in ("moved", "pushed"):
                    continue
                s2 = (ns["player"], frozenset(ns["boxes"]))
                if frozenset(ns["boxes"]) == targets and depth:
                    # count how many optimal sequences reach it, via a second pass below
                    pass
                if seen.get(s2, 10 ** 9) <= depth:
                    continue
                seen[s2] = depth
                nxt.append(s2)
                expanded += 1
        # count sequences reaching solved at THIS depth
        sol = 0
        for state in nxt:
            if frozenset(state[1]) == targets:
                sol += 1
        if sol:
            return depth, sol, expanded >= cap_states
        frontier = nxt
    return None, 0, expanded >= cap_states


# a cleaner count: enumerate all paths of the optimal length by DFS over the depth-limited DAG
def count_optimal_paths(level_text, cap=2000000):
    st = S.parse(level_text)
    targets = frozenset(st["targets"])
    start = (st["player"], frozenset(st["boxes"]))
    # BFS depth of every state, and the optimal goal depth
    dist = {start: 0}
    q = collections.deque([start])
    goal_depth, expanded = None, 0
    while q and expanded < cap and (goal_depth is None or dist[q[0]] < goal_depth):
        state = q.popleft()
        expanded += 1
        d = dist[state]
        if goal_depth is not None and d >= goal_depth:
            continue
        player, boxes = state
        cur = dict(st, player=player, boxes=set(boxes))
        for a in S.ACTIONS:
            ns, outcome = S.step(cur, a)
            if outcome not in ("moved", "pushed"):
                continue
            s2 = (ns["player"], frozenset(ns["boxes"]))
            if s2 not in dist:
                dist[s2] = d + 1
                if frozenset(ns["boxes"]) == targets:
                    goal_depth = d + 1 if goal_depth is None else min(goal_depth, d + 1)
                else:
                    q.append(s2)
    if goal_depth is None:
        return None, 0
    # count paths: dp over states at each depth reaching the goal
    ways = collections.Counter({start: 1})
    total = 0
    for d in range(goal_depth):
        nw = collections.Counter()
        for state, w in ways.items():
            if dist.get(state, 10 ** 9) != d:
                continue
            player, boxes = state
            cur = dict(st, player=player, boxes=set(boxes))
            for a in S.ACTIONS:
                ns, outcome = S.step(cur, a)
                if outcome not in ("moved", "pushed"):
                    continue
                s2 = (ns["player"], frozenset(ns["boxes"]))
                if frozenset(ns["boxes"]) == targets:
                    if d + 1 == goal_depth:
                        total += w
                elif dist.get(s2) == d + 1:
                    nw[s2] += w
        ways = nw
    return goal_depth, total


for lv in ("levels/01_one_push.txt", "levels/02_two_boxes.txt", "levels/03_the_corner_waiting.txt"):
    if not os.path.exists(os.path.join(HERE, lv)):
        print(f"  {os.path.basename(lv):30s} ABSENT")
        continue
    ln, n = count_optimal_paths(open(os.path.join(HERE, lv)).read())
    print(f"  {os.path.basename(lv):30s} optimal length {ln}   DISTINCT OPTIMAL MOVE SEQUENCES: {n}")

# ---- B2: DOES step() WALK THE PLAYER OFF THE BOARD?
print("\nB2 -- OUT OF BOUNDS")
unenclosed = "###\n#@#\n###\n"        # no, that is enclosed; build an open one
# EXACTLY ONE box and ONE target, or parse() rejects it -- which I learned by having it reject my first two
# attempts. That is itself a finding: the frozen parser validates box/target balance and rejects empties.
open_level = "@   \n.$  \n   #\n"      # 3 rows x 4 cols, open on the bottom edge
print(f"  level:\n{open_level}")
st = S.parse(open_level)
cur = st
for i in range(8):
    cur, outcome = S.step(cur, "D")
    r, c = cur["player"]
    oob = not (0 <= r < cur["rows"] and 0 <= c < cur["cols"])
    print(f"    step S (down) #{i+1}: outcome={outcome:8s} player={cur['player']} "
          f"OUT OF BOUNDS={oob}")
    if oob:
        print(f"      -- and render() on this state:")
        print("      " + S.render(cur).replace("\n", "\n      "))
        break

# ---- B3: A TWO-PLAYER LEVEL
print("\nB3 -- TWO PLAYERS")
two = "#####\n#@ @#\n# $ #\n# . #\n#####\n"
try:
    st2 = S.parse(two)
    print(f"  parsed WITHOUT ERROR. player = {st2['player']}   <- last one wins, silently"
          if True else "")
except Exception as e:                                                  # noqa: BLE001
    print(f"  raised {type(e).__name__}: {e}")

# ---- B1: WHAT DOES attempted MEAN?
print("\nB1 -- `attempted`")
import inspect                                                          # noqa: E402
src = inspect.getsource(S.play)
for i, line in enumerate(src.splitlines()):
    if "attempted" in line or "break" in line or "RESIGN" in line:
        print(f"    {line.strip()[:96]}")

# ---- R3: THE SHAPE OF THE EXCHANGE
print("\nR3 -- WHAT SHAPE DO THE FROZEN ARTIFACTS DECLARE?")
print(f"  play() signature          : {inspect.signature(S.play)}")
for probe in ("exactly one action letter", "move history so far", "move_stream"):
    print(f"    {probe!r:28s} in the grammar: {probe in g}")
