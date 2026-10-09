#!/usr/bin/env python3
"""THE COST OF AN ENTRANT THAT CAN COMPLETE A GAME HERE -- measured, not estimated.

Chilly's ask: the head-to-head needs an entrant that can finish, so the scale decision has to be made
before the contest rather than discovered during it. This measures the one number that decides it --
PER MOVE, for each candidate, against the SAME position with the SAME frozen prompt.

THE POSITION IS THE ONE THE ORNITH RUN DIED AT: 28 legal moves, no move list supplied. It is the hard case
on the axis that matters (many candidates to derive), so a model that clears it clears easier ones.

    python3 cost_probe.py
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess_game as g                                                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FEN = "rnbqkbnr/ppp2ppp/8/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3"
LLAMA = "/home/chilly1/llama.cpp/build/bin/llama-server"
MODELS = "/home/chilly1/.hermes/models"
PORT = 8741

# smallest first, so the table fills in cheaply and a slow entrant is the only long wait
CANDIDATES = [
    ("Ministral-3-3B-Instruct-2512-UD-Q4_K_XL.gguf", "Ministral-3B"),
    ("Tiel-Inspired-Coder-9B-UD-Q4_K_M.gguf", "Tiel-Inspired-9B"),
    ("Ornith-1.5-9B-Q4_K_M.gguf", "Ornith-9B"),
]


def probe(path, label):
    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    log = os.path.join(HERE, "logs", f"COST_PROBE_{label}.log")
    srv = subprocess.Popen([LLAMA, "-m", path, "-c", "8192", "-ngl", "0", "--port", str(PORT),
                            "--no-webui"], stdout=open(log, "w"), stderr=subprocess.STDOUT)
    row: dict = dict(entrant=label, loaded_s=None, committed=None, tokens=None, secs=None, move=None,
                     reason=None, viable=None)
    try:
        t0 = time.time()
        up = False
        while time.time() - t0 < 600:
            if srv.poll() is not None:
                row["reason"] = f"server exited rc={srv.returncode}"
                return row
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=3).read()
                up = True
                break
            except Exception:                                         # noqa: BLE001
                time.sleep(3)
        if not up:
            row["reason"] = "never answered /health in 600 s"
            return row
        row["loaded_s"] = round(time.time() - t0, 1)

        legal = g.legal_moves(FEN)
        body = json.dumps({"messages": [{"role": "user", "content": g.PROMPT_TEMPLATE.format(fen=FEN)}],
                           "max_tokens": g.MAX_TOKENS, "temperature": 0.0})
        req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions",
                                     data=body.encode(), headers={"Content-Type": "application/json"})
        t0 = time.time()
        j = json.loads(urllib.request.urlopen(req, timeout=900).read().decode())
        row["secs"] = round(time.time() - t0, 1)
        msg = (j.get("choices") or [{}])[0].get("message") or {}
        row["tokens"] = (j.get("usage") or {}).get("completion_tokens")
        content = (msg.get("content") or "").strip()
        uci, san, why = g.resolve(FEN, content, legal)
        row["committed"] = uci is not None
        row["move"] = uci or san
        row["reason"] = why.split(":")[0]
        row["reasoning_chars"] = len(msg.get("reasoning_content") or "")
        # VIABLE = commits to a legal move, so a 60-ply event costs secs*60 and can be budgeted
        row["viable"] = bool(uci)
        row["a_60ply_event_min"] = round(row["secs"] * 60 / 60, 1) if row["secs"] else None
        return row
    except Exception as e:                                            # noqa: BLE001
        row["reason"] = f"probe error: {e}"
        return row
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=30)
        except Exception:                                             # noqa: BLE001
            srv.kill()


def main():
    print("=" * 96)
    print("COST OF AN ENTRANT THAT CAN COMPLETE A GAME HERE -- one move, the hard position, frozen prompt")
    print("=" * 96)
    print(f"  position: {FEN}")
    print(f"  {len(g.legal_moves(FEN))} legal moves, none of them supplied")
    print(f"  prompt digest {g.PROMPT_DIGEST}, max_tokens {g.MAX_TOKENS}, all-CPU (ngl=0)")
    print()
    rows = []
    for fn, label in CANDIDATES:
        p = os.path.join(MODELS, fn)
        if not os.path.exists(p):
            print(f"  {label:18s} ABSENT")
            continue
        print(f"  {label:18s} probing ...", flush=True)
        r = probe(p, label)
        rows.append(r)
        print(f"  {label:18s} load {r['loaded_s']}s | {r['secs']}s | {r['tokens']} tok | "
              f"committed={r['committed']} | {r['move']} | {r['reason']}")
    print()
    print("  === THE TABLE ===")
    print(f"  {'entrant':18s} {'load':>7s} {'sec/move':>9s} {'tokens':>7s} {'commits':>8s} "
          f"{'60-ply event':>13s}")
    for r in rows:
        print(f"  {r['entrant']:18s} {str(r['loaded_s']):>7s} {str(r['secs']):>9s} {str(r['tokens']):>7s} "
              f"{str(r['committed']):>8s} {str(r.get('a_60ply_event_min')):>10s} min")
    print()
    viable = [r for r in rows if r.get("viable")]
    print(f"  VIABLE (commits to a legal move): {len(viable)} of {len(rows)}")
    for r in viable:
        print(f"    {r['entrant']:18s} a 60-ply event costs about {r['a_60ply_event_min']} min on this box")
    out = os.path.join(HERE, "results", "COST_PROBE.json")
    json.dump(rows, open(out, "w"), indent=1)
    print(f"\n  artifact: {os.path.relpath(out, HERE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
