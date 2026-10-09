#!/usr/bin/env python3
"""Measure -- do not declare -- the depth at which this engine's answer becomes a FACT.

THE ORDER's rule: "an event is not placeable until its oracle is present AND its freeze is
MEASURED -- a depth at which two runs of the same position disagree is not a fact and must not
be frozen."  This runs each position twice at each depth and reports where the two runs agree.

TWO CRITERIA, TWO LABELS -- they give different numbers and this document's freeze uses the second:

  AGREEMENT DEPTH    first depth at which two independent runs AT THAT DEPTH return the same
                     (move, score).  This is THE ORDER's own test; below it the answer is not a
                     fact.  With a pinned config this is normally the shallowest depth tried,
                     because a pinned engine is deterministic -- so on its own it UNDERSTATES the
                     depth the freeze needs.
  MOVE-CONVERGENCE   first depth from which the chosen MOVE never changes again as depth grows.
                     This is what FREEZE_chess.md freezes on (d12): the verdict is stable while
                     the SCORE never settles.

Reporting one number under the label "FREEZE" is how a check and the document it checks end up
contradicting each other (the first version of this file did exactly that: it printed the
AGREEMENT depth, 8, while the document froze 12).

The BOX is one of the four fields the freeze must record, so the header prints it: a result pasted
without it is not comparable with a result from another machine.  The score series is config-specific
until parity is held field by field -- see FREEZE_chess.md section 2b.

NO THIRD-PARTY IMPORTS -- standard library only.  This file speaks UCI to the engine directly.
Earlier revisions needed the `python-chess` module, and a check that needs a package only installed
on the box that wrote it is a caption, not a check: it would not start on Chilly's Linux box, and it
would not start on Jarvis either until a venv existed here.  UCI is a text protocol on stdin/stdout
and the FEN is handed to the engine verbatim, so the module was never load-bearing -- it was a
dependency you could not see.  There is now nothing to install.
Engine: $STOCKFISH, else argv[1], else PATH, else the platform default.
Run:    python3 freeze_check.py [/path/to/stockfish]
"""
import os
import platform
import re
import shutil
import subprocess
import sys

MATE_SCORE = 100000                     # matches python-chess Score.score(mate_score=100000)
DEFAULT_ENGINE = {"darwin": "/opt/homebrew/bin/stockfish",
                  "linux": "/usr/games/stockfish"}.get(sys.platform, "stockfish")
ENGINE = (os.environ.get("STOCKFISH") or (sys.argv[1] if len(sys.argv) > 1 else "")
          or shutil.which("stockfish") or DEFAULT_ENGINE)

POSITIONS = {
    "kiwipete": "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "italian":  "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
}
DEPTHS = [8, 10, 12, 14, 16, 18, 20, 22]   # covers the table in FREEZE_chess.md
PINNED = {"Threads": 1, "Hash": 16}        # the proposed freeze config
HAZARD = {"Threads": 8, "Hash": 16}        # a config that must not be left undeclared
RUNS = 4                                   # runs per arm in section B
HAZARD_DEPTH = 20                          # the depth FREEZE_chess.md's config finding cites

OPTION_RE = re.compile(r"^option name (\S+) type spin default (-?\d+)")


def spawn():
    """A fresh engine process: no hash and no state carries between runs."""
    return subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, bufsize=1)


def send(p, line):
    p.stdin.write(line + "\n")
    p.stdin.flush()


def read_until(p, token):
    lines = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.strip()
        lines.append(line)
        if line == token or line.startswith(token + " "):
            break
    return lines


def handshake(p):
    """uci handshake; returns (id name, {spin option: declared default})."""
    send(p, "uci")
    name, defaults = None, {}
    for line in read_until(p, "uciok"):
        if line.startswith("id name "):
            name = line[len("id name "):]
        m = OPTION_RE.match(line)
        if m:
            defaults[m.group(1)] = int(m.group(2))
    return name, defaults


def one(fen, depth, cfg):
    """One independent run: fresh process, so no hash or state carries between runs.

    Returns (uci move, score) with the score in WHITE's point of view, cp -- the convention
    python-chess's `info['score'].pov(chess.WHITE).score(mate_score=100000)` produced, so this
    file's numbers are directly comparable with every result already in the record.
    """
    p = spawn()
    try:
        handshake(p)
        for k, v in (cfg or {}).items():
            send(p, f"setoption name {k} value {v}")
        send(p, "isready")
        read_until(p, "readyok")
        send(p, f"position fen {fen}")
        send(p, f"go depth {depth}")
        move, cp = None, None
        while True:
            line = p.stdout.readline()
            if not line:
                break
            line = line.strip()
            if line.startswith("bestmove"):
                break
            if not line.startswith("info"):
                continue
            toks = line.split()
            if "score" in toks:
                i = toks.index("score")
                kind, val = toks[i + 1], int(toks[i + 2])
                if kind == "cp":
                    cp = val
                elif kind == "mate":            # UCI, side-to-move POV; python-chess convention
                    cp = MATE_SCORE - abs(val) + 1
                    if val < 0:
                        cp = -cp
            if "pv" in toks:
                j = toks.index("pv")
                if j + 1 < len(toks):
                    move = toks[j + 1]
    finally:
        try:
            send(p, "quit")
        except Exception:
            pass
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()
    if cp is not None and fen.split()[1] == "b":
        cp = -cp                                 # to White's point of view
    return (move, cp)


def move_convergence(moves):
    """First depth from which the move never changes again (None if it never settles)."""
    for i in range(len(moves)):
        if all(m == moves[i] for m in moves[i:]):
            return DEPTHS[i]
    return None


def main():
    if not os.path.exists(ENGINE):
        sys.exit(f"engine not found: {ENGINE}\n  set $STOCKFISH, or pass the path as argv[1]")

    print(f"oracle: {ENGINE}")
    print(f"box   : {platform.system()} {platform.release()} {platform.machine()}"
          f" · node {platform.node()} · {os.cpu_count()} logical cores")
    p = spawn()
    try:
        name, defaults = handshake(p)
    finally:
        send(p, "quit")
        p.wait(timeout=10)
    print(f"id    : {name}")
    print("declared defaults -- read from the engine, not assumed:")
    for opt in ("Threads", "Hash", "MultiPV"):
        if opt in defaults:
            print(f"      {opt:8} = {defaults[opt]}")
    print()

    print(f"A. PINNED config {PINNED}  -- two independent runs per depth")
    print(f"   {'position':10} {'depth':>5}  {'run1 (move, cp)':>22}  {'run2':>22}  agree")
    agreement, convergence = {}, {}
    for name, fen in POSITIONS.items():
        first_agree, moves = None, []
        for d in DEPTHS:
            a = one(fen, d, PINNED)
            b = one(fen, d, PINNED)
            moves.append(a[0])
            ok = a == b
            if ok and first_agree is None:
                first_agree = d
            print(f"   {name:10} {d:>5}  {str(a):>22}  {str(b):>22}  "
                  f"{'YES' if ok else 'NO  <-- not a fact at this depth'}")
        agreement[name] = first_agree
        convergence[name] = move_convergence(moves)

    print()
    print(f"B. WHAT MUST BE DECLARED -- {RUNS} runs at depth {HAZARD_DEPTH}, one position,")
    print("   varying ONLY the configuration.  The engine's own declared default is one arm,")
    print("   because 'the default is nondeterministic' is a measurement, not an assumption.")
    fen = POSITIONS["kiwipete"]
    for label, cfg in (("declared default (no configure)", None),
                       (f"explicit {HAZARD}", HAZARD)):
        res = [one(fen, HAZARD_DEPTH, cfg) for _ in range(RUNS)]
        for r in res:
            print(f"      {label:28}  {r}")
        scores = [s for _, s in res]
        print(f"      -> {label:28}  distinct moves {sorted({m for m, _ in res})}"
              f"  distinct scores {sorted(set(scores))}"
              f"  spread {max(scores) - min(scores)} cp")

    print()
    print("FREEZE, both criteria (they are not the same number):")
    for name in POSITIONS:
        a, c = agreement[name], convergence[name]
        print(f"   {name:10} AGREEMENT depth "
              f"{a if a else 'NONE up to d' + str(DEPTHS[-1])}"
              f"   ·   MOVE-CONVERGENCE depth {c if c else 'NONE'}"
              f"{'   <-- the freeze uses this one' if c else ''}")


if __name__ == "__main__":
    main()
