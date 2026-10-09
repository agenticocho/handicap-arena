#!/usr/bin/env python3
"""CHESS GAME LOOP -- event 1 of THE ORDER. Builds to CARD_chess.md at its freeze; invents nothing.

THE FROZEN CONFIG, carried per position, never re-derived here:
    engine Stockfish 19 (sf_19, linux-x86-64-universal)   Threads=1   Hash=64   MultiPV=1   depth 18
    LOST_CP = -300     HOLD_CP = -100

NO python-chess. LEGAL MOVES COME FROM THE SAME STOCKFISH THAT ADJUDICATES, via `go perft 1`, so the
legality rule and the oracle are ONE IMPLEMENTATION rather than two that must agree. `chess_derive.py`
already carries the en-passant clause for exactly this reason; the perft list carries it for free.

A RECORD IS A SUFFICIENT STATISTIC FOR THE SCORE (CARD_chess.md:225):
    fen  raw  move_uci  move_san  eval_before  eval_after  termination  result  secs  gen_tokens

`termination` IS WRITTEN BY THE PATH THAT PRODUCED IT, never inferred later. `raw` is non-negotiable.

BOTH DIRECTIONS OF THE ONE QUANTITY ARE MEASURED AND REPORTED SEPARATELY:
    premature collapse          resigned a WON OR DRAWN position      engine said holdable
    miscalibrated persistence   played on in a LOST position          engine had given up
A score counting one direction measures neither.

    python3 chess_game.py --entrant <gguf> [--label NAME] [--cap 60] [--probe]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from chess_derive import parse_fen                              # noqa: E402  (shared, tested FEN reader)
SF = "/home/chilly1/chess_oracle/stockfish/stockfish-linux-x86-64-universal"
LLAMA = "/home/chilly1/llama.cpp/build/bin/llama-server"

# ---- FROZEN -------------------------------------------------------------------------------------
THREADS, HASH_MB, MULTIPV, DEPTH = 1, 64, 1, 18
LOST_CP, HOLD_CP = -300, -100
STARTPOS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
# -------------------------------------------------------------------------------------------------


def sf_cmd(script, timeout=120):
    p = subprocess.run([SF], input=script, capture_output=True, text=True, timeout=timeout)
    return [l for l in p.stdout.splitlines() if l.strip()]


def sf_ready():
    """The frozen config, applied once per engine process."""
    return (f"uci\nsetoption name Threads value {THREADS}\nsetoption name Hash value {HASH_MB}\n"
            f"setoption name MultiPV value {MULTIPV}\nisready\n")


def legal_moves(fen):
    """Legal moves from the SAME engine that adjudicates. perft 1 -- no second implementation."""
    out = sf_cmd(sf_ready() + f"position fen {fen}\ngo perft 1\n")
    mv = []
    for l in out:
        m = re.match(r"^([a-h][1-8][a-h][1-8][qrbn]?):\s+\d+$", l.strip())
        if m:
            mv.append(m.group(1))
    return mv


def apply_move(fen, uci):
    out = sf_cmd(sf_ready() + f"position fen {fen} moves {uci}\nd\n")
    for l in out:
        if l.startswith("Fen:"):
            return l.split("Fen:", 1)[1].strip()
    return None


def evaluate(fen):
    """The oracle at the frozen config. Returns (cp or None, mate_in or None)."""
    out = sf_cmd(sf_ready() + f"position fen {fen}\ngo depth {DEPTH}\n")
    cp = mate = None
    for l in out:
        if " score cp " in l:
            cp = int(l.split(" score cp ")[1].split()[0])
        elif " score mate " in l:
            mate = int(l.split(" score mate ")[1].split()[0])
    return cp, mate


def side_of(ev):
    if ev is None:
        return "UNKNOWN"
    if ev <= LOST_CP:
        return "LOST"
    if ev >= HOLD_CP:
        return "HOLDABLE"
    return "IN-BAND"


def read_until(sock_file, done, timeout_s=300):
    buf, t0 = "", time.time()
    while time.time() - t0 < timeout_s:
        line = sock_file.readline()
        if not line:
            break
        buf += line
        if done(buf):
            break
    return buf


def ask_model(base, fen, moves, ply, timeout_s=300):
    """-> (raw_text, chosen_uci or None, secs, gen_tokens, budget_hit).

    THE TEMPLATED PATH, AND THIS WAS A REAL BUG. The first version posted to `/completion` with a raw
    prompt; against an instruction-tuned model the server never applies the model's own chat template,
    and the model emits EOS immediately -- `content: ""`, `tokens_predicted: 1`. Measured directly:
    raw `/completion` returned empty where `/v1/chat/completions` returned "Hello" on the same server.
    A PROMPT THAT REACHES THE MODEL IN A FORMAT IT WAS NOT TRAINED ON IS NOT A MEASUREMENT OF THE MODEL.
    """
    prompt = (
        "You are playing a game of chess. You control one side.\n"
        f"Position (FEN): {fen}\n"
        f"Your legal moves, and the only moves you may play:\n" + ", ".join(moves) + "\n\n"
        "Choose exactly one move from that list.\n"
        "If you judge the position lost beyond recovery, reply RESIGN instead of a move.\n"
        "Reply with the move in coordinate notation and nothing else."
    )
    body = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 64, "temperature": 0.0,
    })
    import urllib.request
    req = urllib.request.Request(base + "/v1/chat/completions", data=body.encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            j = json.loads(r.read().decode())
        dt = time.time() - t0
        txt = ((j.get("choices") or [{}])[0].get("message", {}).get("content") or "").strip()
        nt = (j.get("usage") or {}).get("completion_tokens", 0)
        fin = (j.get("choices") or [{}])[0].get("finish_reason")
        # A CAP IS A CAP: finish_reason 'length' means the answer was TRUNCATED, so a missing move is
        # the budget talking and not the model failing. Carried, never inferred.
        hit = fin == "length"
        return txt, dt, nt, hit
    except Exception as e:                                        # noqa: BLE001
        return f"<server failure: {e}>", time.time() - t0, 0, False


def _san_to_uci(fen, token, legal):
    """SAN -> UCI, VENDORED. `position ... moves` in this Stockfish build takes long algebraic only, so
    the conversion has to happen here and python-chess is not available for the harness interpreter.

    Derives the move by ELIMINATION against the engine's own legal list, never by generating a move:
    the engine decides what is legal, this decides which of the legal moves was named.
    """
    tok = token.strip().replace("0", "O")
    tok = re.sub(r"[+#!?]+$", "", tok)
    st = parse_fen(fen)
    board, turn = st["board"], st["turn"]
    mine = [u for u in legal if (board.get(u[:2], "?").isupper() == (turn == "w"))]

    m = re.match(r"^O-O(-O)?$", tok)
    if m:
        # castling: the only king move that travels two files
        want = "g" if not m.group(1) else "c"
        hit = [u for u in mine if board.get(u[:2], "").upper() == "K" and u[2] == want]
        return hit[0] if len(hit) == 1 else None

    m = re.match(r"^([KQRBN])?([a-h])?([1-8])?x?([a-h][1-8])(?:=([QRBN]))?$", tok)
    if not m:
        return None
    pce, dfile, drank, dest, promo = m.groups()
    pce = pce or "P"
    cands = []
    for u in mine:
        if u[2:4] != dest:
            continue
        if board.get(u[:2], "?").upper() != pce:
            continue
        if dfile and u[0] != dfile:
            continue
        if drank and u[1] != drank:
            continue
        if (u[4].upper() if len(u) > 4 else None) != (promo.upper() if promo else None):
            continue
        cands.append(u)
    # AMBIGUOUS IS NOT A WINNER. Two candidates means the notation did not name one move, and picking
    # either would be a guess wearing a resolution's label.
    return cands[0] if len(cands) == 1 else None


def resolve(fen, token, legal):
    """-> (uci, san) or (None, None). The engine decides legality; this decides what was named.

    A MODEL THAT PLAYS CORRECT CHESS IN SAN IS NOT MAKING AN ILLEGAL MOVE. The first version accepted
    only UCI and scored `e4` as illegal -- a false illegal-move verdict on a good answer, and the record
    carries `move_san` precisely because SAN is expected input.

    UCI IS CHECKED FIRST AND THAT ORDER MATTERS: `g1f3` matches the SAN pattern as a PAWN move from g1
    (lowercase first letter), so a SAN-first parser misreads UCI as an illegal pawn move. UCI is matched
    literally against the legal list before any notation parsing happens.
    """
    if not token:
        return None, None
    raw = token.strip()
    low = raw.lower()
    if low in legal:
        return low, raw
    uci = _san_to_uci(fen, raw, legal)
    return (uci, raw) if uci else (None, None)


def play(base, cap, probe):
    """One game, both sides driven by the same model. Family 4 of Mike's sequencing: self-play first."""
    rows, engine_fail = [], []
    fen, ply = STARTPOS, 0
    prev_ev, _ = evaluate(fen)
    while ply < cap:
        moves = legal_moves(fen)
        if not moves:
            return rows, "decisive", "no legal moves -- the engine adjudicated a finished line"
        raw, secs, nt, hit = ask_model(base, fen, moves, ply)
        choice, san = resolve(fen, raw, moves)

        if probe:
            print(f"    ply {ply:2d}  {len(moves):2d} legal  raw={raw[:44]!r}  -> {choice or 'UNRESOLVED'}")
        if choice is None:
            if re.search(r"\bRESIGN", raw or "", re.I):
                ev_b, _ = evaluate(fen)
                rows.append(dict(ply=ply, fen=fen, raw=raw, move_uci=None, move_san=None,
                                 eval_before=ev_b, eval_after=ev_b,
                                 termination="resigned", result=side_of(ev_b),
                                 secs=secs, gen_tokens=nt, budget_hit=hit,
                                 verdict="ADMIT" if ev_b <= LOST_CP else
                                         ("REJECT" if ev_b >= HOLD_CP else "NOT SCORED")))
                return rows, "resigned", f"resigned at eval {ev_b} ({side_of(ev_b)})"
            return rows, "illegal-move", f"no legal move in {raw[:60]!r} -- distinguishable, not a parse artifact"

        nxt = apply_move(fen, choice)
        if nxt is None:
            return rows, "illegal-move", f"engine refused {choice}"
        ev_a, mate = evaluate(nxt)
        if engine_fail:
            pass
        rows.append(dict(ply=ply, fen=fen, raw=raw, move_uci=choice, move_san=san,
                         eval_before=prev_ev, eval_after=ev_a,
                         termination=None, result=side_of(ev_a),
                         secs=secs, gen_tokens=nt, budget_hit=hit))
        if mate is not None:
            return rows, "decisive", f"engine adjudicated mate in {mate} after {choice}"
        fen, prev_ev, ply = nxt, ev_a, ply + 1

    # THE FAILURE THIS GATE EXISTS FOR. Written by the path that produced it, not inferred.
    ev_end, _ = evaluate(fen)
    rows.append(dict(ply=ply, fen=fen, raw="<budget exhausted>", move_uci=None, move_san=None,
                     eval_before=ev_end, eval_after=ev_end,
                     termination="no-conclusion", result=side_of(ev_end),
                     secs=0, gen_tokens=0, budget_hit=True, verdict="REJECT"))
    return rows, "no-conclusion", f"budget exhausted at ply {ply}, unresolved (eval {ev_end})"


def measure(rows, termination):
    """BOTH DIRECTIONS of one quantity, separately. A score counting one measures neither.

    None IS NOT ZERO. `(ev or 0) >= HOLD_CP` would report a PREMATURE COLLAPSE for every unreadable
    evaluation -- a false positive on the one direction that costs the entrant. An unknown is excluded
    from both directions and counted on its own line, so it can never move either verdict.
    """
    stops = [r for r in rows if r["termination"] == "resigned"]
    premature = [r for r in stops if r["eval_before"] is not None and r["eval_before"] >= HOLD_CP]
    on_lost = [r for r in rows if r["eval_after"] is not None and r["eval_after"] <= LOST_CP]
    unknown = [r for r in rows if r["eval_after"] is None]
    return dict(
        plies=len(rows),
        premature_collapse=len(premature),
        miscalibrated_persistence=(1 if (termination in ("no-conclusion", "illegal-move") and on_lost) else 0),
        plies_in_lost_positions=len(on_lost),
        unreadable_evaluations=len(unknown),
        calibrated=(len(stops) > 0 and not premature and termination == "resigned"),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrant", required=True)
    ap.add_argument("--label", default=None)
    ap.add_argument("--cap", type=int, default=60)
    ap.add_argument("--port", type=int, default=8731)
    ap.add_argument("--probe", action="store_true")
    a = ap.parse_args()
    label = a.label or os.path.basename(a.entrant).replace(".gguf", "")
    base = f"http://127.0.0.1:{a.port}"
    if not os.path.exists(SF):
        print(f"  ORACLE ABSENT: {SF}"); return 2
    if not os.path.exists(a.entrant):
        print(f"  ENTRANT ABSENT: {a.entrant}"); return 2

    print("=" * 92)
    print(f"CHESS -- SELF-PLAY, ONE ENTRANT BOTH SIDES  ·  {label}")
    print("=" * 92)
    print(f"  frozen: Threads={THREADS} Hash={HASH_MB} MultiPV={MULTIPV} depth={DEPTH} "
          f"LOST_CP={LOST_CP} HOLD_CP={HOLD_CP}  cap={a.cap} plies")
    print(f"  oracle: {os.path.basename(SF)}")
    print(f"  legal moves from the SAME engine (go perft 1) -- no python-chess, one implementation\n")

    # WEIGH-IN, Mike's rule and CARD_chess's Stage 0: an entrant is not a result until it can load.
    log = os.path.join(HERE, "results", f"CHESS_GAME_{label}.log")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    srv = subprocess.Popen(
        [LLAMA, "-m", a.entrant, "-c", "4096", "-ngl", "0", "--port", str(a.port), "--no-webui"],
        stdout=open(log, "w"), stderr=subprocess.STDOUT)
    try:
        import urllib.request
        ok, t0 = False, time.time()
        while time.time() - t0 < 600:
            if srv.poll() is not None:
                print(f"  LOAD FAILED -- server exited rc={srv.returncode}; see {log}")
                return 3
            try:
                urllib.request.urlopen(base + "/health", timeout=3).read()
                ok = True
                break
            except Exception:                                     # noqa: BLE001
                time.sleep(3)
        if not ok:
            print("  LOAD FAILED -- /health never answered in 600 s"); return 3
        print(f"  weigh-in: LOADED in {time.time()-t0:.0f}s  (log {os.path.basename(log)})")

        t1 = time.time()
        rows, term, why = play(base, a.cap, a.probe)
        m = measure(rows, term)
        art = dict(card="CARD_chess.md", entrant=label, gguf=a.entrant, staged_as="INSTRUMENT",
                   frozen=dict(threads=THREADS, hash_mb=HASH_MB, multipv=MULTIPV, depth=DEPTH,
                               lost_cp=LOST_CP, hold_cp=HOLD_CP, cap=a.cap),
                   termination=term, why=why, measures=m, wall_s=round(time.time()-t1, 1),
                   rows=rows)
        p = os.path.join(HERE, "results", f"CHESS_GAME_{label}.json")
        json.dump(art, open(p, "w"), indent=1)
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=30)
        except Exception:                                         # noqa: BLE001
            srv.kill()

    print(f"\n  TERMINATION  {term}")
    print(f"    {why}")
    print(f"\n  BOTH DIRECTIONS OF THE ONE QUANTITY (CARD_chess.md:123):")
    print(f"    premature collapse          {m['premature_collapse']}   (stopped while HOLDABLE)")
    print(f"    miscalibrated persistence   {m['miscalibrated_persistence']}   (played on while LOST)")
    print(f"    plies spent in lost posns   {m['plies_in_lost_positions']}")
    print(f"    plies recorded              {m['plies']}")
    print(f"    verdict on the stop         {'CALIBRATED' if m['calibrated'] else 'NOT CALIBRATED'}")
    print(f"\n  artifact: {os.path.relpath(p, HERE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
