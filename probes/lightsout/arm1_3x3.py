"""Arm 1 — 3x3, derivation PERMITTED, 16 pre-registered boards, 1024 tokens.

Pre-registration (from ocho_arena/probes/lightsout/3x3_fixture_16_boards_20261022.json,
sha256 851976c57068bca9; its human-readable twin .md is 2c18e257afe3d066 — two files, two
hashes, and this line names both so neither is attached to the wrong object): the 16 boards
are the images of 16 press strings with x=0 excluded, so the
all-off board is absent BY CONSTRUCTION, and every one of the 512 possible constants scores
exactly one board of the whole space of 512. Over this sample a constant is therefore worth
1/16 if its board is in the set and 0/16 otherwise.

The ONLY difference from the 2x2 arm is that the answer contract is removed: the model may
show working. That is the variable this arm tests — can it derive, or does it label?

Usage:  python3 arm1_3x3.py --dry-run     verify plumbing, no model call
        python3 arm1_3x3.py               run it (~25 min)
"""
import json
import sys
import time
import urllib.request

BASE = "http://127.0.0.1:58595/v1/chat/completions"
MODEL = "prism-bonsai-9b"
FIXTURE = "/home/chilly1/workspace/ocho_arena/probes/lightsout/3x3_fixture_16_boards_20261022.json"
OUT = "/home/chilly1/workspace/ocho_arena/probes/lightsout/arm1_3x3_rows.jsonl"
N = 3
MAX_TOKENS = 1024
DRY = "--dry-run" in sys.argv


def tmap(p):
    r, c = divmod(p, N)
    out = {p}
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            out.add(nr * N + nc)
    return out


TM = [tmap(p) for p in range(N * N)]


def apply(state, presses):
    s = state
    for p in presses:
        for q in TM[p]:
            s ^= 1 << q
    return s


def render(state):
    return "\n".join(" ".join(str(state >> (r * N + c) & 1) for c in range(N)) for r in range(N))


def solve_set(state):
    """every press set that clears the board, by brute force over 2^9 subsets."""
    sols = []
    for m in range(1 << (N * N)):
        ps = [p for p in range(N * N) if m >> p & 1]
        if apply(state, ps) == 0:
            sols.append(ps)
    return sols


def _names(presses):
    return " ".join(CELLS[p // N] + str(p % N + 1) for p in sorted(presses))


def _normalise(s):
    return " ".join(sorted(t.strip().upper() for t in s.replace(",", " ").split() if t.strip()))


# deliberately NO answer contract: derivation is permitted, which is what this arm varies
PROMPT = """Lights Out on a 3x3 grid. 1 = lit, 0 = dark. Pressing a cell toggles it and its
orthogonal neighbours. Pressing a cell twice is the same as not pressing it.
{board}
What presses turn every cell off?
"""

CELLS = "ABC"


def parse(txt):
    """presses from a PRESSES: line only; claim from a CLAIM: line only. Anything else = none."""
    presses, claim, path, bad = None, None, None, []
    for line in txt.splitlines():
        L = line.strip().lstrip("*").strip()
        U = L.upper()
        if U.startswith("PRESSES:"):
            body = L.split(":", 1)[1].strip()
            if body.upper().startswith("NONE") or body == "":
                presses, path = [], "empty_set"
            else:
                cells = []
                for tok in body.replace("and", ",").replace(" ", ",").split(","):
                    tok = tok.strip().upper().strip(".")
                    if len(tok) == 2 and tok[0] in CELLS and tok[1] in "123":
                        cells.append(CELLS.index(tok[0]) * N + int(tok[1]) - 1)
                    elif len(tok) == 2 and tok[0].isalpha() and tok[1].isdigit():
                        bad.append(tok)
                if cells:
                    presses, path = sorted(set(cells)), "explicit"
                if bad:
                    path = "explicit_with_out_of_range"
        elif U.startswith("CLAIM:"):
            v = U.split(":", 1)[1]
            claim = "UNSOLVABLE" if "UNSOLV" in v else ("SOLVED" if "SOLV" in v else None)
    return presses, claim, path, bad


def ask(board_text):
    body = json.dumps({"model": MODEL, "temperature": 0.0, "max_tokens": MAX_TOKENS,
                       "chat_template_kwargs": {"enable_thinking": False},
                       "messages": [{"role": "user", "content": PROMPT.format(board=board_text)}]}).encode()
    t0 = time.time()
    req = urllib.request.Request(BASE, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read())
    return d, time.time() - t0


def main():
    rows = json.load(open(FIXTURE))
    # pre-registration checks, before any model call
    boards = [r["b"] for r in rows]
    assert len(rows) == 16, "fixture is not 16 boards"
    assert len(set(boards)) == 16, "duplicate boards in fixture"
    assert 0 not in boards, "the all-off board must be absent by construction"
    # The fixture's `correct` label is NOT trusted: it is recomputed from the press matrix here,
    # because a mutation of that field alone survives every verifier we have (measured: A1->B2
    # in the json and A1->C3 in the md both return ALL CHECKS PASS). A label is a claim; the
    # board is the datum.
    for r in rows:
        truth = solve_set(r["b"])
        assert len(truth) == 1, "board %d does not have exactly one solution" % r["b"]
        if r.get("correct"):
            assert _normalise(r["correct"]) == _names(truth[0]), (
                "fixture label %r for board %d does not match the computed solution %r"
                % (r["correct"], r["b"], _names(truth[0])))
        r["truth_computed"] = _names(truth[0])
    print("  pre-registered: %d boards, distinct, all-off absent, labels recomputed" % len(boards))

    if DRY:
        for r in rows[:3]:
            txt = "PRESSES: A1, B2\nCLAIM: SOLVED\n"
            p, c, path, bad = parse(txt)
            st = r["b"]
            print("    dry board %-4d prompt_chars=%-4d parse=%s presses=%s reaches=%s"
                  % (st, len(PROMPT.format(board=render(st))), path, p, apply(st, p)))
        print("  DRY RUN OK — no model call made")
        return

    out = []
    t0 = time.time()
    with open(OUT, "w") as fh:
        for r in rows:
            st = r["b"]
            d, secs = ask(render(st))
            msg = d["choices"][0]["message"]
            txt = msg.get("content") or ""
            presses, claim, path, bad = parse(txt)
            reached = apply(st, presses) if presses is not None else None
            if presses is not None and reached == 0:
                verdict = "CORRECT"
            elif claim == "UNSOLVABLE":
                verdict = "FALSE_UNSOLVABLE"
            elif claim == "SOLVED":
                verdict = "FALSE_SUCCESS"
            else:
                verdict = "NO_ANSWER"
            rec = {"model": MODEL, "arm": "3x3_derivation_permitted",
                   "board_id": r.get("idx"), "board": render(st).replace("\n", "/"),
                   "truth_presses": r["correct"], "claim": claim, "parse_path": path,
                   "out_of_range": bad, "presses": presses, "verdict": verdict,
                   "secs": round(secs, 2), "max_tokens": MAX_TOKENS,
                   "completion_tokens": (d.get("usage") or {}).get("completion_tokens"),
                   "finish_reason": d["choices"][0].get("finish_reason"),
                   "answer_block": ("PRESSES:" in txt), "raw": txt}
            out.append(rec)
            fh.write(json.dumps(rec) + "\n"); fh.flush()
            print("  #%-2s %-9s %-16s %6.1fs tok=%-4s %s"
                  % (r.get("idx"), rec["board"], verdict, secs,
                     rec["completion_tokens"], rec["answer_block"]), flush=True)

    from collections import Counter
    print()
    print("  rows %d   elapsed %.0fs   verdicts %s"
          % (len(out), time.time() - t0, dict(Counter(r["verdict"] for r in out))))
    print("  answer blocks %d/%d   distinct raw answers %d"
          % (sum(1 for r in out if r["answer_block"]), len(out),
             len(set(r["raw"].strip() for r in out))))


if __name__ == "__main__":
    main()
