"""Rung 1: Lights Out on 2x2, all 16 boards, scored by STATE.

Independent engine — imports nothing from the 4x4 probe except its HTTP call. On 2x2 every
board is solvable with exactly one press set, so "UNSOLVABLE" is always wrong and a constant
cannot score. The empty press set is an ordinary set (the all-off board), not a format error.
"""
import importlib.util
import json
import time
import urllib.request
from itertools import product

# THIS FILE IS A SCRIPT, NOT A MODULE. Its row loop and summary run at module level, so importing it
# for a helper would spend one model call per board. Measured 2026-10-22: two imports to test a guard
# cost 32 model calls and 52 s, and returned byte-identical answers both times (temperature 0).
# Refuse loudly rather than run quietly.
if __name__ != "__main__":
    raise ImportError(
        "rung1_2x2.py is a script: importing it would run %d model calls. "
        "Copy the pure functions into a lib if you need them." % 16)


BASE = "http://127.0.0.1:58595/v1/chat/completions"
MODEL = "prism-bonsai-9b"
OUT = "/home/chilly1/.hermes/profiles/chilly/cache/scratch/results_rung1_2x2.jsonl"
N = 2
CELLS = ["A1", "A2", "B1", "B2"]
OUT_OF_RANGE = []


def tmap(p):
    r, c = divmod(p, N)
    out = {p}
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            out.add(nr * N + nc)
    return out


TMAP = [tmap(p) for p in range(N * N)]


def apply(state, presses):
    s = state
    for p in presses:
        for q in TMAP[p]:
            s ^= 1 << q
    return s


def solve_set(state):
    """exact solution(s) by brute force over the 16 press subsets"""
    sols = []
    for mask in range(1 << (N * N)):
        presses = [p for p in range(N * N) if mask >> p & 1]
        if apply(state, presses) == 0:
            sols.append(presses)
    return sols


def render(state):
    return "\n".join(
        " ".join(str(state >> (r * N + c) & 1) for c in range(N)) for r in range(N))


PROMPT = """Lights Out on a 2x2 grid. 1 = lit, 0 = dark. Pressing a cell toggles it and its
orthogonal neighbours. Pressing a cell twice is the same as not pressing it.
{board}
What presses turn every cell off?

Answer with EXACTLY two lines and nothing else. No derivation, no working, no explanation.
PRESSES: <cells like A1, B2 — or NONE if no presses>
CLAIM: <SOLVED or UNSOLVABLE>"""


def ask(board_text, mx=256):
    body = json.dumps({"model": MODEL, "temperature": 0.0, "max_tokens": mx,
                       "chat_template_kwargs": {"enable_thinking": False},
                       "messages": [{"role": "user", "content": PROMPT.format(board=board_text)}]}).encode()
    t0 = time.time()
    req = urllib.request.Request(BASE, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    return d, time.time() - t0


def parse_2x2(txt):
    """strict: presses only from a PRESSES: line; claim only from a CLAIM: line."""
    presses, claim, path = None, None, None
    for line in txt.splitlines():
        L = line.strip().lstrip("*").strip()
        if L.upper().startswith("PRESSES:"):
            body = L.split(":", 1)[1].strip()
            if body.upper().startswith("NONE") or body == "":
                presses, path = [], "empty_set"
            else:
                cells, bad = [], []
                for tok in body.replace("and", ",").replace(" ", ",").split(","):
                    tok = tok.strip().upper().strip(".")
                    if len(tok) == 2 and tok[0] in "AB" and tok[1] in "12":
                        cells.append((ord(tok[0]) - 65) * N + int(tok[1]) - 1)
                    elif len(tok) == 2 and tok[0].isalpha() and tok[1].isdigit():
                        # a well-formed cell token that does not exist on this board
                        bad.append(tok)
                if cells:
                    presses, path = sorted(set(cells)), "explicit"
                if bad:
                    # never silently drop: an out-of-range cell means the answer was not
                    # about this board, and shortening it hides that.
                    path = "explicit_with_out_of_range"
                    OUT_OF_RANGE.extend(bad)
        if L.upper().startswith("CLAIM:"):
            v = L.split(":", 1)[1].upper()
            claim = "UNSOLVABLE" if "UNSOLV" in v else ("SOLVED" if "SOLV" in v else None)
    return presses, claim, path


# --- 1. the engine, verified before it is used on a model ---------------------
all_boards = list(range(1 << (N * N)))
counts = {}
for st in all_boards:
    sols = solve_set(st)
    counts[st] = len(sols)
print("  boards %d   solution-count histogram %s" % (len(all_boards), dict(sorted(
    {k: list(counts.values()).count(k) for k in set(counts.values())}.items()))))
print("  every board solvable: %s   every board exactly one solution: %s"
      % (all(counts.values()), all(v == 1 for v in counts.values())))
empty_board = 0
print("  all-off board %r has solution %s" % (render(0), solve_set(0)))

# --- 2. the model -------------------------------------------------------------
rows = []
t0 = time.time()
with open(OUT, "w") as fh:
    for st in all_boards:
        bt = render(st)
        try:
            d, secs = ask(bt)
        except Exception as e:
            print("  board %s ERR %s" % (bt.replace("\n", "/"), type(e).__name__))
            continue
        msg = d["choices"][0]["message"]
        txt = msg.get("content") or ""
        presses, claim, path = parse_2x2(txt)
        truth = solve_set(st)[0]
        reached = apply(st, presses) if presses is not None else None
        # scoring by STATE: correct iff the presses actually reach all-off
        # AN OUT-OF-RANGE ANSWER IS NOT A WRONG ANSWER ABOUT THIS BOARD — it is an answer about
        # a different board, so it cannot be scored here. The guard that flags it was added at
        # 12:16:00, eight minutes AFTER these rows were written, and the verdict never read it, so
        # three rows were scored FALSE_SUCCESS off a truncated subset (A1,B1 kept out of
        # A1,B1,C1,D1 — and C1/D1 do not exist on a 2x2 board). Gate first, then score.
        if path == "explicit_with_out_of_range":
            verdict = "UNATTRIBUTABLE"
        elif presses is not None and reached == 0:
            verdict = "CORRECT"
        elif claim == "UNSOLVABLE":
            verdict = "FALSE_UNSOLVABLE"
        elif claim == "SOLVED":
            verdict = "FALSE_SUCCESS"
        else:
            verdict = "NO_ANSWER"
        rec = {"model": MODEL, "board": bt.replace("\n", "/"), "state": st,
               "truth_presses": truth, "claim": claim, "parse_path": path,
               "presses": presses, "verdict": verdict, "secs": round(secs, 2),
               "completion_tokens": (d.get("usage") or {}).get("completion_tokens"),
               "answer_block": ("PRESSES:" in txt and "CLAIM:" in txt), "raw": txt}
        rows.append(rec)
        fh.write(json.dumps(rec) + "\n"); fh.flush()
        print("  %-9s %-17s %5.1fs presses=%-12s claim=%s"
              % (rec["board"], verdict, secs, presses, claim), flush=True)

from collections import Counter
print()
print("  rows %d   elapsed %.0fs" % (len(rows), time.time() - t0))
print("  verdicts %s" % dict(Counter(r["verdict"] for r in rows)))
print("  distinct raw answers %d" % len(set(r["raw"].strip() for r in rows)))
print("  answer blocks %d / %d" % (sum(1 for r in rows if r["answer_block"]), len(rows)))


if __name__ == "__main__":
    main()
