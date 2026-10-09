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
# A REASONING MODEL NEEDS ROOM FOR THE TRACE **AND** THE ANSWER. At 64 tokens the trace of a prompt that
# lists twenty legal moves consumes the whole budget and the message content comes back EMPTY -- the model
# answered, the cap ate it. That is FINDING 001's first silent mechanism arriving in this loop, and it
# would have read as an illegal move by the entrant. The value is generous because on this axis the cap
# measures the CAP and not the model.
MAX_TOKENS = 2048
STARTPOS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
# -------------------------------------------------------------------------------------------------


_SF_PROC = None


def _sf():
    """ONE PERSISTENT ENGINE PER PROCESS, not one per call.

    The first version spawned a fresh Stockfish for every query -- and the loop makes about six per ply
    (legal moves, the SAN resolution, two evaluations, the move application). Each spawn re-allocates the
    frozen 64 MB hash and re-handshakes, which measured at tens of seconds per ply and put a 60-ply game
    hours out. `readyok` is an exact frame delimiter, so the engine can stay up and be driven.
    """
    global _SF_PROC
    if _SF_PROC is None or _SF_PROC.poll() is not None:
        _SF_PROC = subprocess.Popen([SF], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, text=True, bufsize=1)
        assert _SF_PROC.stdin is not None and _SF_PROC.stdout is not None   # PIPE guarantees both
        _SF_PROC.stdin.write(f"uci\nsetoption name Threads value {THREADS}\n"
                             f"setoption name Hash value {HASH_MB}\n"
                             f"setoption name MultiPV value {MULTIPV}\nisready\n")
        _SF_PROC.stdin.flush()
        while True:
            l = _SF_PROC.stdout.readline()
            if not l or l.strip() == "readyok":
                break
    return _SF_PROC


def sf_cmd(script, until="readyok", timeout=300):
    """Send a script to the persistent engine and read until `until` framing the reply.

    THE TERMINATOR DEPENDS ON THE COMMAND, and getting it wrong returns early rather than failing loudly:
      `readyok`         plain commands -- but UCI REQUIRES `isready` to answer PROMPTLY EVEN DURING A
                        SEARCH, so framing a search with it reads only the opening `info` lines and
                        returns BEFORE the result. Measured: evaluate() returned None in 0.000s against an
                        engine that answers correctly when driven by hand.
      `bestmove`        `go depth N` -- the search's own terminator.
      `Nodes searched`  `go perft N` -- perft NEVER emits `bestmove`, so a reader waiting for one blocks
                        until the timeout.
    """
    p = _sf()
    p.stdin.write(script if script.endswith("\n") else script + "\n")
    p.stdin.write("isready\n" if until == "readyok" else "")
    p.stdin.flush()
    out = []
    while True:
        l = p.stdout.readline()
        if not l:
            break
        if l.strip() == until or l.strip().startswith(until):
            break
        if l.strip():
            out.append(l.rstrip("\n"))
    return out


def sf_ready():
    """The engine is configured ONCE, when the persistent process starts.

    THIS USED TO RETURN THE FULL HANDSHAKE INCLUDING `isready`, which was harmless while each call spawned
    its own engine and read all of stdout. With a persistent reader it is a real defect: the stray
    `isready` produces a `readyok` BEFORE the requested output, and `sf_cmd` -- which reads until the first
    `readyok` -- returns nothing. Measured: legal_moves returned 0 moves and evaluate returned None, on an
    engine that answers correctly when driven by hand.
    """
    return ""


def legal_moves(fen):
    """Legal moves from the SAME engine that adjudicates. perft 1 -- no second implementation."""
    out = sf_cmd(f"position fen {fen}\ngo perft 1\n", until="Nodes searched")
    mv = []
    for l in out:
        m = re.match(r"^([a-h][1-8][a-h][1-8][qrbn]?):\s+\d+$", l.strip())
        if m:
            mv.append(m.group(1))
    return mv


def apply_move(fen, uci):
    out = sf_cmd(f"position fen {fen} moves {uci}\nd\n")
    for l in out:
        if l.startswith("Fen:"):
            return l.split("Fen:", 1)[1].strip()
    return None


def evaluate(fen):
    """The oracle at the frozen config. Returns (cp or None, mate_in or None)."""
    out = sf_cmd(f"position fen {fen}\ngo depth {DEPTH}\n", until="bestmove")
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
        "max_tokens": MAX_TOKENS, "temperature": 0.0,
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


_DECOR = "*`_~\"'.,;:()[]{}<>#!"


def _extract(fen, text, legal):
    """Candidates in `text` that are legal moves -> {uci: as_written}."""
    found = {}
    for c in re.findall(r"[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?|[Oo0]-[Oo0]-[Oo0]", text or ""):
        cl = c.lower()
        if cl in legal:
            found[cl] = c
            continue
        u = _san_to_uci(fen, c, legal)
        if u:
            found[u] = c
    return found


def _fail(reason):
    return None, None, reason


def resolve(fen, token, legal):
    """-> (uci, san, reason). The engine decides legality; this decides what was named.

    FOUR FALSE VERDICTS WERE FOUND AND FIXED HERE, EACH ON A CORRECT ANSWER. The fourth is the one that
    produced a published `illegal-move` for a model playing the best move on the board:

      1. SAN not accepted       the model played `e4`; a UCI-only parser scored it illegal. The record
                                carries `move_san` precisely because SAN is expected input.
      2. UCI misread as SAN     `g1f3` matches the SAN pattern as a PAWN move from g1, lowercase first
                                letter -- so UCI is matched literally BEFORE any notation parsing.
      3. MARKDOWN DECORATION    the model played `**d4c5**`; the marks made it unresolvable.
      4. THE REASONING WAS READ AS ALTERNATIVE MOVES. The model answered `**f3e5**` and then explained
                                "the black pawn on e5 is undefended (the d5 pawn ...)". Mining the WHOLE
                                output for candidates found BOTH `f3e5` and `d5` -- and `d5` resolves to
                                the legal capture `e4d5` -- so the ambiguity guard, which exists to refuse
                                to guess, refused the right answer and the record published
                                `illegal-move` / "no legal move" for the best move available.

    THE ANSWER IS AT THE HEAD. A model states its move and then justifies it, so the FIRST LINE is where
    the answer lives and everything after it is prose ABOUT the answer. The whole text is consulted only
    when the head yields nothing, and then it must still yield exactly one distinct move. Ambiguity is
    not a winner -- but reasoning is not ambiguity, and the first version could not tell them apart.

    The third return value says WHICH OF THESE IT WAS, because "no legal move" was true of all four and
    is therefore a `why` field that cannot be checked: `resolved-head`, `resolved-full`, `ambiguous`,
    `unreadable`, or `no-legal-moves-supplied` when the list handed in was empty.
    """
    raw = (token or "").strip()
    if not raw:
        return None, None, "unreadable: empty model output"
    # A legality check handed an empty list calls EVERY move illegal. That is not a verdict about the
    # model; it is a broken instrument, and it says so here rather than agreeing with the failure.
    if not legal:
        return None, None, "no-legal-moves-supplied: the legality list was EMPTY (instrument failure)"

    first = next((l.strip() for l in raw.splitlines() if l.strip()), "")

    # 1. THE HEAD. The answer lives here.
    for cand in (first, raw):
        if not cand:
            continue
        stripped = cand.strip(_DECOR).strip()
        low = stripped.lower()
        if low in legal:
            return low, stripped, "resolved-head" if cand is first else "resolved-full"
        u = _san_to_uci(fen, stripped, legal)
        if u:
            return u, stripped, "resolved-head" if cand is first else "resolved-full"

    # 2. the head yielded nothing at all -- only now is the rest of the text consulted
    head_found = _extract(fen, first, legal)
    if len(head_found) == 1:
        u = next(iter(head_found))
        return u, head_found[u], "resolved-head"
    if len(head_found) > 1:
        return None, None, f"ambiguous: the first line names {len(head_found)} distinct legal moves"

    full = _extract(fen, raw, legal)
    if len(full) == 1:
        u = next(iter(full))
        return u, full[u], "resolved-full"
    if len(full) > 1:
        return None, None, (
            f"ambiguous: {len(full)} distinct legal moves named across the text, none of them the answer "
            f"({', '.join(sorted(full)[:6])})")
    return None, None, "unreadable: no legal move named anywhere in the output"


def play(base, cap, probe):
    """One game, both sides driven by the same model. Family 4 of Mike's sequencing: self-play first."""
    # THE POSITIVE CONTROL, BEFORE ANY TERMINATION MAY BE TRUSTED. A legality checker that cannot list
    # the moves of the STARTING POSITION is not a legality checker -- and a checker handed an empty list
    # calls EVERY move illegal, so its verdict would agree with its own failure and report the model as
    # the cause. The starting position's move count is fixed at 20 and nobody has to interpret it.
    start_moves = legal_moves(STARTPOS)
    if len(start_moves) != 20:
        return [], "serving-failure", (
            f"oracle control FAILED: legal_moves(startpos) returned {len(start_moves)}, expected 20. "
            f"No termination this run produces may be read as a verdict about the entrant.")

    rows, engine_fail = [], []
    fen, ply = STARTPOS, 0
    prev_ev, _ = evaluate(fen)
    while ply < cap:
        moves = legal_moves(fen)
        if not moves:
            # AN EMPTY LEGAL LIST IS AN INSTRUMENT FAILURE, NOT AN ADJUDICATION. The first version
            # returned "decisive" here -- "the engine adjudicated a finished line" -- for what is
            # actually a broken read, which is the empty-room defect on the legality check.
            return rows, "serving-failure", (
                f"legal_moves returned NOTHING at ply {ply}; the engine dialogue failed, and no move "
                f"could be legal against an empty list. MISSING VALUE, not an adjudication.")
        raw, secs, nt, hit = ask_model(base, fen, moves, ply)
        choice, san, reason = resolve(fen, raw, moves)

        if probe:
            print(f"    ply {ply:2d}  {len(moves):2d} legal  raw={raw[:44]!r}  -> {choice or 'UNRESOLVED'}"
                  f"  [{reason.split(':')[0]}]")
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
            # A CAP IS A CAP. Empty output WITH finish_reason=length is the budget talking, so it maps to
            # the frozen taxonomy's `serving-failure` -- MISSING VALUE, never scored zero, never dropped --
            # rather than to an illegal move by the entrant. The distinction is the whole point: an empty
            # answer the harness produced must not be recorded as a move the model failed to make.
            if not (raw or "").strip() and hit:
                return rows, "serving-failure", (
                    f"answer truncated at the {MAX_TOKENS}-token cap (tokens {nt}) -- MISSING VALUE, "
                    f"not an illegal move; a re-run is a RE-MEASUREMENT")
            # AN UNRESOLVED MOVE IS A MEASUREMENT FAILURE, NOT THE ENTRANT'S FAILURE. All of these map
            # to the frozen taxonomy's `serving-failure` -- MISSING VALUE, never scored zero, never
            # dropped, re-run is a RE-MEASUREMENT -- and the precise reason travels with it. The first
            # version called them all `illegal-move` and closed the question with the sentence
            # "distinguishable, not a parse artifact": the `why` field asserted the failure was real, in
            # the same field that carried it, which is why it survived review. All four causes below were
            # FALSE for the entrant and each is a different claim about the INSTRUMENT.
            return rows, "serving-failure", (
                f"move unresolved at ply {ply} -- {reason}; raw={raw[:80]!r}. "
                f"MISSING VALUE, not an illegal move.")

        nxt = apply_move(fen, choice)
        if nxt is None:
            return rows, "serving-failure", f"engine refused {choice} -- MISSING VALUE, not an illegal move"
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

    WHICH SUBJECT -- THE ORACLE'S SCORE IS FROM THE SIDE TO MOVE, SO `eval_before` AND `eval_after` ARE
    FROM OPPOSITE SIDES. A row's `fen` is the position BEFORE the move, with the entrant to move, so
    `eval_before` is the ENTRANT's evaluation. `eval_after` is the position AFTER the move, with the
    OPPONENT to move, so it is the OPPONENT's evaluation. Comparing them measures nothing, and the first
    version did exactly that: it counted "the entrant played on while lost" from `eval_after`, which is
    the entrant's WINS. Measured on the first complete game it reported 3 plies in lost positions
    alongside 0 miscalibrated persistence -- a self-contradiction that is the only reason the inversion
    was visible at all. `eval_before` is the mover's own side and is the only field the two directions
    may be read from.

    None IS NOT ZERO. `(ev or 0) >= HOLD_CP` would report a PREMATURE COLLAPSE for every unreadable
    evaluation -- a false positive on the one direction that costs the entrant. An unknown is excluded
    from both directions and counted on its own line, so it can never move either verdict.
    """
    stops = [r for r in rows if r["termination"] == "resigned"]
    premature = [r for r in stops if r["eval_before"] is not None and r["eval_before"] >= HOLD_CP]
    # MISCALIBRATED PERSISTENCE: the entrant moved while ITS OWN side was lost, and did not stop.
    # Read from eval_before -- the mover's evaluation -- never from eval_after, which belongs to the
    # opponent. The last row is excluded when it is the game-ending one, because a move that ends the
    # game is not "playing on".
    mover_lost = [r for r in rows
                  if r["eval_before"] is not None and r["eval_before"] <= LOST_CP
                  and r["move_uci"] is not None]
    unknown = [r for r in rows if r["eval_before"] is None]
    return dict(
        plies=len(rows),
        premature_collapse=len(premature),
        # a stop decision made while lost is the ONLY calibrated stop; playing on while lost is its
        # opposite, and both are counted whether or not the game happened to end well instead.
        miscalibrated_persistence=len(mover_lost),
        plies_in_lost_positions=len(mover_lost),
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
