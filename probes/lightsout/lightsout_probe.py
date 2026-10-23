#!/usr/bin/env python3
"""lightsout_probe.py — run local models against Jarvis's Lights Out 4x4 and
score their answers with an INDEPENDENT checker (not the simulator's helpers).

Scores per attempt:
  SOLVED            presses applied reach all-off
  FALSE_SUCCESS     model said SOLVED/UNSOLVABLE but presses do not reach all-off
  FALSE_UNSOLVABLE  model said UNSOLVABLE on a board that is in the image
  NO_SOLVE          honest miss (admitted it could not / garbage presses)
  CORRECT_UNSOLVABLE model said UNSOLVABLE on an unsolvable board
Also records popcount vs the minimal press count (non-minimal detection).
"""
import json, re, sys, time, urllib.request, random
from itertools import product

BASE = "http://127.0.0.1:58595/v1/chat/completions"
OUT = "/home/chilly1/.hermes/profiles/chilly/cache/scratch/results.jsonl"

# Per-call metadata, recorded beside every row so a row can be checked against the
# request and the text it actually describes.
META = {}

def tmap(p):
    r, c = divmod(p, 4)
    out = {p}
    for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
        nr, nc = r+dr, c+dc
        if 0 <= nr < 4 and 0 <= nc < 4:
            out.add(nr*4+nc)
    return out

COLS = [sum(1 << b for b in sorted(tmap(p))) for p in range(16)]

def apply(state, presses):
    m = 0
    for p in presses:
        m ^= COLS[p]
    return state ^ m

# all 16-bit press masks -> resulting board, for solvability + minimality
DIST = {}
for mask in range(65536):
    v = 0
    for p in range(16):
        if mask >> p & 1:
            v ^= COLS[p]
    DIST.setdefault(v, []).append(mask)

def min_presses(state):
    sols = DIST.get(state)
    if not sols:
        return None
    return min(bin(m).count("1") for m in sols)

def render(state):
    lines = ["   1 2 3 4"]
    for r in range(4):
        row = []
        for c in range(4):
            row.append("#" if state >> (r*4+c) & 1 else ".")
        lines.append("ABCD"[r] + "  " + " ".join(row))
    return "\n".join(lines)

PROMPT = """You are solving a Lights Out 4x4 puzzle.

Rules:
- The board is 4 rows (A-D) and 4 columns (1-4). A '#' cell is LIT, a '.' cell is OFF.
- One move = press one cell. Pressing a cell toggles that cell and its orthogonal neighbours (up, down, left, right), each flipping lit<->off.
- The goal is every cell OFF.
- Pressing a cell twice cancels out, so only the SET of pressed cells matters and order is irrelevant.

Board:
{board}

Answer in exactly this form. Do NOT answer in JSON. Do not use any other schema.
Your reply must END with these two lines and nothing after them:
PRESSES: <cells to press, comma-separated like A1,B3, or NONE>
CLAIM: SOLVED if your presses turn every cell off, or UNSOLVABLE if you believe no set of presses can turn every cell off
"""

def ask(model, board, timeout=180):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": PROMPT.format(board=board)}],
        "temperature": 0.0,
        "max_tokens": 4096,
        "chat_template_kwargs": {"enable_thinking": False},
        "stream": False,
    }).encode()
    req = urllib.request.Request(BASE, data=body, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    txt = d["choices"][0]["message"].get("content") or ""
    msg = d["choices"][0]["message"]
    META.clear()
    META.update({
        "max_tokens": 4096,
        "completion_tokens": (d.get("usage") or {}).get("completion_tokens"),
        "reasoning_chars": len(msg.get("reasoning_content") or ""),
        "finish_reason": d["choices"][0].get("finish_reason"),
        "answer_block": ("PRESSES:" in txt and "CLAIM:" in txt),
        "raw_exact": txt,
    })
    return txt, time.time() - t0

CELL = re.compile(r"\b([A-D])\s*([1-4])\b", re.I)

# --- echo guard -------------------------------------------------------------
# The prompt itself contains a cell list ("like A1,B3") and the claim word
# ("UNSOLVABLE if you believe..."), so a model that echoes the contract produces
# text that LOOKS like a complete answer. These markers are the prompt's own
# contract lines; if the reply reproduces them the reply is the material it was
# given, not an answer. Fixed 2026-10-22 (Jarvis measured the hole on helper).
ECHO_MARKERS = [
    "you are solving a lights out 4x4 puzzle",
    "cells to press, comma-separated like a1,b3, or none>",
    "solved if your presses turn every cell off, or unsolvable if you believe no set of presses",
]

def _norm(s):
    return re.sub(r"\s+", " ", s or "").strip().casefold()

def is_echo(txt, prompt=None):
    """True when the reply is (or contains) the prompt's own contract text."""
    n = _norm(txt)
    if any(_norm(m) in n for m in ECHO_MARKERS):
        return True
    if prompt:
        for line in prompt.splitlines():
            ln = _norm(line)
            if len(ln) >= 20 and ln in n:
                return True
    return False

def parse(txt, prompt=None):
    """Strict pass first (explicit PRESSES:/CLAIM: lines). If PRESSES is absent,
    a recorded lenient fallback takes the last sentence that names cells after the
    word 'press'. parse_path is stored so the numbers stay auditable.

    Echo guard: if the reply reproduces the prompt's own contract, the row is
    NO_ANSWER (path='echo'). The claim fallback is explicit-line-only: the
    unanchored /unsolv|impossible|no solution/ whole-reply search is gone,
    because it was what turned an echoed contract into a verdict."""
    presses, claim, path = None, None, None
    if is_echo(txt, prompt):
        return None, None, "echo"
    for line in txt.splitlines():
        L = line.strip()
        if re.match(r"(?i)^presses\s*:", L):
            body = L.split(":", 1)[1]
            if re.search(r"(?i)\bNONE\b", body):
                presses = []
            else:
                cells = [(ord(a.upper())-65)*4 + int(b)-1 for a, b in CELL.findall(body)]
                presses = cells if cells else None
        if re.match(r"(?i)^\**\s*claim\s*\**\s*:", L):
            v = L.split(":", 1)[1].upper()
            if "UNSOLV" in v:
                claim = "UNSOLVABLE"
            elif "SOLV" in v:
                claim = "SOLVED"
    if presses is not None:
        path = "explicit"
    else:
        for sentence in reversed(re.split(r"[.\n]", txt)):
            if re.search(r"(?i)\bpress", sentence):
                cells = [(ord(a.upper())-65)*4 + int(b)-1 for a, b in CELL.findall(sentence)]
                if cells:
                    presses, path = cells, "lenient"
                    break
    if presses is None:
        # last resort: a line that is nothing but cell tokens (the model answered
        # with a bare list and no PRESSES: prefix)
        for line in reversed([l.strip() for l in txt.splitlines() if l.strip()]):
            if re.fullmatch(r"(?i)[A-D]\s*[1-4](\s*[,\s]\s*(and\s+)?[A-D]\s*[1-4])*", line):
                cells = [(ord(a.upper())-65)*4 + int(b)-1 for a, b in CELL.findall(line)]
                if cells:
                    presses, path = cells, "lenient_cellline"
                    break
    # A claim is only ever read from an explicit CLAIM: line (handled above).
    # No prose-derived claim: the previous lenient block set a claim from any line that
    # also named cells and contained "solv"/"impossible", which produced rows carrying
    # claim=SOLVED whose own stored raw contained no such token. A column must be
    # derivable from the text that ships with it, or it is not evidence.
    return presses, claim, path

def main():
    models = sys.argv[1].split(",")
    boards = json.load(open("/home/chilly1/.hermes/profiles/chilly/cache/scratch/boards.json"))
    fh = open(OUT, "a")
    for model in models:
        for b in boards:
            state = b["state"]
            try:
                txt, dt = ask(model, render(state))
            except Exception as e:
                rec = {"model": model, "board": b["name"], "error": str(e)[:300], "verdict": "ERROR"}
                fh.write(json.dumps(rec) + "\n"); fh.flush()
                print(f"{model:22s} {b['name']:10s} ERROR {str(e)[:80]}", flush=True)
                continue
            presses, claim, path = parse(txt, PROMPT.format(board=render(state)))
            reached = apply(state, presses) if presses is not None else None
            mp = min_presses(state)
            if path == "echo":
                verdict = "NO_ANSWER"
            elif presses is not None and reached == 0:
                verdict = "SOLVED"
            elif claim == "UNSOLVABLE" and mp is not None:
                verdict = "FALSE_UNSOLVABLE"
            elif claim == "SOLVED":
                verdict = "FALSE_SUCCESS"
            elif claim == "UNSOLVABLE" and mp is None:
                verdict = "CORRECT_UNSOLVABLE"
            else:
                verdict = "NO_SOLVE" if claim is None else "FALSE_SUCCESS"
            rec = {"model": model, "board": b["name"], "solvable": mp is not None,
                   "min_presses": mp, "claim": claim, "parse_path": path,
                   "n_presses": len(presses) if presses is not None else None,
                   "verdict": verdict, "secs": round(dt, 2), "raw": txt, **META}
            fh.write(json.dumps(rec) + "\n"); fh.flush()
            print(f"{model:22s} {b['name']:10s} {verdict:18s} min={mp} n={rec['n_presses']} {dt:.1f}s", flush=True)
    fh.close()

if __name__ == "__main__":
    main()
