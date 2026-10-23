"""Arm 2 — 3x3 on prism-bonsai-9b, under the SAME conditions as the 4x4 row.

The point is to un-confound the comparison. The 4x4 arm was `prism-bonsai-9b`, answer contract,
256 tokens, one pass. The earlier 3x3 arm was a different model (`ornith9b`) on the peer's seat,
derivation permitted, 1024 tokens. Those differ in model AND format AND rung, so no claim about
scale could survive. This arm fixes model and format and varies only the rung.

Pre-registered fixture: the 16 boards from 3x3_fixture_16_boards_20261022.json, all-off excluded by
construction, labels recomputed from the press matrix rather than trusted.

Records `distinct_answers` first, because both existing files pass a verdict histogram while
measuring a single string.

Cost: 16 boards x ~1.6 s on the resident seat, no lease, no eviction.
"""
import json
import sys
import time
import urllib.request
from collections import Counter

BASE = "http://127.0.0.1:58595/v1/chat/completions"
MODEL = "prism-bonsai-9b"
FIXTURE = "/home/chilly1/workspace/ocho_arena/probes/lightsout/3x3_fixture_16_boards_20261022.json"
OUT = "/home/chilly1/workspace/ocho_arena/probes/lightsout/results_arm2_3x3_same_conditions.jsonl"
N = 3
MAX_TOKENS = 256
CELLS = "ABC"


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


def solve_set(state):
    sols = []
    for m in range(1 << (N * N)):
        ps = [p for p in range(N * N) if m >> p & 1]
        if apply(state, ps) == 0:
            sols.append(ps)
    return sols


def names(presses):
    return " ".join(CELLS[p // N] + str(p % N + 1) for p in sorted(presses))


def render(state):
    return "\n".join(" ".join(str(state >> (r * N + c) & 1) for c in range(N)) for r in range(N))


# the SAME contract the 4x4 arm used, so the only variable is the rung
PROMPT = """Lights Out on a 3x3 grid. 1 = lit, 0 = dark. Pressing a cell toggles it and its
orthogonal neighbours. Pressing a cell twice is the same as not pressing it.
{board}
What presses turn every cell off?

Answer with EXACTLY two lines and nothing else. No derivation, no working, no explanation.
PRESSES: <cells like A1, B2 — or NONE if no presses>
CLAIM: <SOLVED or UNSOLVABLE>"""


def ask(board_text):
    body = json.dumps({"model": MODEL, "temperature": 0.0, "max_tokens": MAX_TOKENS,
                       "chat_template_kwargs": {"enable_thinking": False},
                       "messages": [{"role": "user", "content": PROMPT.format(board=board_text)}]}).encode()
    t0 = time.time()
    req = urllib.request.Request(BASE, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read())
    return d, time.time() - t0


def parse(txt):
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


def main():
    rows = json.load(open(FIXTURE))
    for r in rows:
        truth = solve_set(r["b"])
        assert len(truth) == 1, "board %d not uniquely solvable" % r["b"]
        assert not r.get("correct") or \
            " ".join(sorted(r["correct"].split())) == names(truth[0]), \
            "label %r != computed %r for board %d" % (r.get("correct"), names(truth[0]), r["b"])
        r["truth"] = names(truth[0])
    assert len({r["b"] for r in rows}) == 16 and 0 not in {r["b"] for r in rows}
    print("  pre-registered: 16 boards, labels recomputed, all-off absent", flush=True)

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
            rec = {"model": MODEL, "arm": "3x3_same_conditions_as_4x4", "board_id": r["idx"],
                   "board": render(st).replace("\n", "/"), "state": st,
                   "truth": r["truth"], "claim": claim, "parse_path": path,
                   "out_of_range": bad, "presses": presses, "verdict": verdict,
                   "secs": round(secs, 2), "max_tokens": MAX_TOKENS,
                   "completion_tokens": (d.get("usage") or {}).get("completion_tokens"),
                   "answer_block": ("PRESSES:" in txt and "CLAIM:" in txt), "raw": txt}
            out.append(rec)
            fh.write(json.dumps(rec) + "\n"); fh.flush()
            print("  #%-2s %-9s %-17s %5.1fs tok=%-4s %r"
                  % (r["idx"], rec["board"], verdict, secs,
                     rec["completion_tokens"], txt.strip()[:44]), flush=True)

    raws = Counter((r["raw"] or "").strip() for r in out)
    print()
    print("  DISTINCT ANSWERS: %d of %d rows" % (len(raws), len(out)))
    for a, n in raws.most_common(5):
        print("    x%-3d %r" % (n, a[:70]))
    print("  verdicts: %s" % dict(Counter(r["verdict"] for r in out)))
    print("  correct: %d of %d   elapsed %.0fs"
          % (sum(1 for r in out if r["verdict"] == "CORRECT"), len(out), time.time() - t0))


if __name__ == "__main__":
    main()
