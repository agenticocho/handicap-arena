#!/usr/bin/env python3
"""THE DEPTH TEST -- run exactly as PREREG_depth_test.md froze it. Read-only apart from its own output.

    candidates       a legal-move walk from the start position. NO POSITION IS CHOSEN BY EYE.
    reference label  d18 at the frozen config, evaluated TWICE; a disagreement DISCARDS the candidate
    at risk          |eval + 300| <= 60  OR  |eval + 100| <= 60      (60 = the one measured d12->d18 shift)
    crossing         a position whose SIDE (LOST / GREY / HOLDABLE) differs between d12 and d18
    secondary        d12 for EVERY candidate, so 'the depths differ' can be told apart from 'the
                     thresholds differ'

TWO OPERATIONAL CHOICES MADE AFTER THE PRE-REGISTRATION AND DECLARED HERE RATHER THAN BURIED:
the candidate COUNT (40) and the PLY RANGE (12..70). The pre-registration omitted both -- a gap. Neither
can bias WHICH positions land near a threshold, because that selection is made by the oracle; the count
affects precision and the ply range affects variety. Recorded as a gap, not as a bias.
"""
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cabinet_root as _root                                          # noqa: E402

BIN = "/home/chilly1/chess_oracle/stockfish/stockfish-linux-x86-64-universal"
D_REF, D_ALT = 18, 12
THREADS, HASH = 1, 64
LOST_CP, HOLD_CP, WINDOW = -300, -100, 60
N_CANDIDATES = 40
PLY_CHOICES = list(range(12, 71, 2))

# NO DESTINATION IS BOUND HERE. The line that used to sit at this position was a module-level
# ABSOLUTE LITERAL naming main's legacy record -- the same literal, in all four trees, at the same
# line -- and main() below opened it for writing. So running this file from ANY worktree overwrote a
# TRACKED file inside main's checkout: a cross-worktree write into the record, in a form the counter's
# two os.path.join patterns could not see. The Chair's ruling on t_5742bdac (a writer is bound by its
# DESTINATION, not by its syntax; 2026-10-14-a-writer-is-bound-by-its-destination-not-its-syntax.md,
# sha256 6309d8a467ccdbc2317e904f98a6222c37f2678f17f2c4e8567d87b5f52232f9) brings this file INTO the
# declaration. The destination is now resolved at the write -- see depth_dir(), and do not put a path
# constant back at module level.


def uci(cmds, until):
    """Run a short UCI session, reading until a line STARTS WITH `until`. -> list of lines.

    A SINGLE TERMINATOR STRING, because the commands in this file end differently: `go depth N` ends with
    `bestmove`, `go perft 1` ends with `Nodes searched:`, and `d` prints a `Fen:` line. An earlier version
    tried to accept a tuple of terminators and indexed past the end of a one-element tuple.
    """
    p = subprocess.Popen([BIN], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    for c in cmds:
        p.stdin.write(c + "\n")
    p.stdin.flush()
    lines = []
    while True:
        ln = p.stdout.readline()
        if not ln:
            break
        ln = ln.rstrip("\n")
        lines.append(ln)
        if ln.startswith(until):
            break
    p.stdin.write("quit\n")
    p.stdin.flush()
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    return lines


def legal_moves(fen):
    # `go perft 1` DOES NOT END WITH `bestmove`. It ends with `Nodes searched: N`, so the shared reader
    # must be told a different terminator -- otherwise this blocks forever waiting for a line that never
    # comes, and the whole test hangs with no output at all. (Found by smoke-testing the primitives
    # before spending 120 searches on them.)
    out = uci([f"position fen {fen}", "go perft 1"], until="Nodes searched")
    mv = []
    for ln in out:
        head = ln.split(":")[0].strip() if ":" in ln else ""
        if len(head) in (4, 5) and head[0] in "abcdefgh" and head[2] in "abcdefgh":
            mv.append(head)
    return mv


def eval_at(fen, depth):
    out = uci([f"position fen {fen}", f"go depth {depth}"], until="bestmove")
    sc = bm = None
    for ln in out:
        if ln.startswith("info ") and f" depth {depth} " in ln and " score " in ln:
            t = ln.split()
            for i, x in enumerate(t):
                if x == "score":
                    sc = (t[i + 1], int(t[i + 2]))
        if ln.startswith("bestmove"):
            bm = ln.split()[1]
    if not sc:
        return None, bm
    # ONLY CENTIPAWN SCORES ARE COMPARABLE TO THE THRESHOLDS.
    # A mate score is arguably lost/decided, but converting it into a centipawn number is an invention.
    return (sc[1] if sc[0] == "cp" else None), bm


def side_of(cp):
    if cp is None:
        return None
    if cp <= LOST_CP:
        return "LOST"
    if cp >= HOLD_CP:
        return "HOLDABLE"
    return "GREY"


def depth_dir():
    """-> <declared ROOT>/<this worktree's cabinet>/depth -- THE ONE DESTINATION for this test's output.

    RESOLVED AT THE WRITE, NOT AT THE IMPORT, and that is a measurement rather than a taste: the
    ruling fixes the rule for BOTH depth files for one reason -- depth_test2.py is also a library
    (source_probe3.py:19, source_probe4.py:21, acceptance_smoke.py:20 import it for its uci/eval/fen
    helpers), so a resolution at module level would make three importers refuse over a write they
    never make. This file is imported by nobody today; the rule is kept here anyway, because where a
    destination resolves has to be ONE answer.

    AND IT REFUSES RATHER THAN FALLS BACK. cabinet_root.results_dir() is a Refusal -- a SystemExit
    that names the remedy -- when there is no declared root, or when the declaration resolves inside
    a git working tree or the repository's own git directory. It is NOT caught here: a run that
    cannot declare where its result goes must not write one somewhere else.

    WHY A NAMED SUBTREE AND NOT THE FLAT LEVEL -- the naming is the Chair's, not this file's. The two
    published depth artifacts stay DECLARED IN PLACE inside the legacy record (the record is one tree
    object, 0bcaaa0188b35f0bdd17e3ca824a977cac2d94a1, and removing a file from it changes that
    object), so a flat-level write would put a second file of the same basename under a different
    domain entry -- a basename collision across entries, which the tools that flatten the domain are
    required to refuse. `depth/` is a subtree OF THE DECLARED WRITE SCOPE, not a second root.
    """
    return os.path.join(_root.results_dir(), "depth")


def out_path():
    """-> <declared write scope>/depth/DEPTH_TEST.json, or a refusal. This creates nothing."""
    return os.path.join(depth_dir(), "DEPTH_TEST.json")


def main():
    # NOT `out`: `out` is already the read buffer in the walk below (uci returns lines), and a name
    # that means two things in one function is how a write lands in a list. The linter caught this
    # one; the measurement below is what proves it.
    dest = out_path()                    # the destination, resolved where it is written
    print(f"  destination            {dest}")
    print("                         resolved at the write through cabinet_root.results_dir(), which "
          "REFUSES")
    print("                         rather than falling back to a worktree-local path")
    rnd = random.Random(20261008)          # deterministic; the walk is reproducible
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    seen, cands = set(), []
    target = set(PLY_CHOICES)
    plies = 0
    # ---- 1. the legal-move walk. No position is chosen by eye; the ply set picks them. ----
    while plies < max(PLY_CHOICES) + 4 and len(cands) < N_CANDIDATES:
        mvs = legal_moves(fen)
        if not mvs:
            break
        mv = rnd.choice(mvs)
        # apply by playing through from the start is costly; use the `d` command to read the FEN
        out = uci([f"position fen {fen} moves {mv}", "d"], until="Fen:")
        newfen = None
        for ln in out:
            if ln.startswith("Fen:"):
                newfen = ln.split("Fen:", 1)[1].strip()
        if not newfen:
            break
        fen = newfen
        plies += 1
        if plies in target and fen not in seen:
            seen.add(fen)
            cands.append(fen)
    print(f"  candidates drawn from a legal-move walk: {len(cands)}")

    # ---- 2. the reference label: d18 TWICE; a disagreement discards ----
    rows = []
    for i, f in enumerate(cands, 1):
        a, _ = eval_at(f, D_REF)
        b, _ = eval_at(f, D_REF)
        if a is None or b is None:
            continue
        if a != b:
            print(f"    [{i}] DISCARDED -- d18 disagreed with itself ({a} vs {b})")
            continue
        rows.append({"fen": f, "d18": a, "side18": side_of(a)})
        print(f"    [{i}] d18 {a:6d}  {side_of(a)}")
    print(f"  reproducible at d18: {len(rows)}")

    # ---- 3. the at-risk selection, by the pre-registered window ----
    def at_risk(cp):
        return abs(cp - LOST_CP) <= WINDOW or abs(cp - HOLD_CP) <= WINDOW

    risk = [r for r in rows if at_risk(r["d18"])]
    far = [r for r in rows if not at_risk(r["d18"])]
    print(f"\n  AT RISK (within {WINDOW} cp of either threshold): {len(risk)}")
    print(f"  FAR from both edges: {len(far)}")

    # ---- 4/5. d12 for EVERY candidate; crossing = side changes ----
    for r in rows:
        c, _ = eval_at(r["fen"], D_ALT)
        r["d12"] = c
        r["side12"] = side_of(c)
        r["crossed"] = (r["side12"] is not None and r["side18"] is not None
                        and r["side12"] != r["side18"])
        r["shift"] = (r["d18"] - r["d12"]) if (r["d18"] is not None and r["d12"] is not None) else None

    rc_ = sum(1 for r in risk if r["crossed"])
    fc = sum(1 for r in far if r["crossed"])
    print(f"\n  CROSSINGS among AT-RISK : {rc_} of {len(risk)}")
    print(f"  CROSSINGS among FAR     : {fc} of {len(far)}")
    if risk:
        print("\n  the at-risk set:")
        for r in risk:
            mark = "  <-- CROSSED" if r["crossed"] else ""
            print(f"    d18 {r['d18']:6d} {r['side18']:9s} -> d12 {r['d12']:6d} {str(r['side12']):9s} "
                  f"shift {r['shift']:+5d}{mark}")
    shifts = [r["shift"] for r in rows if r["shift"] is not None]
    if shifts:
        shifts.sort()
        print(f"\n  SHIFT d12->d18 across ALL {len(shifts)} candidates: "
              f"min {shifts[0]:+d}  median {shifts[len(shifts)//2]:+d}  max {shifts[-1]:+d}")

    os.makedirs(depth_dir(), exist_ok=True)
    json.dump({"config": {"engine": "Stockfish 19", "threads": THREADS, "hash": HASH,
                          "d_ref": D_REF, "d_alt": D_ALT, "window": WINDOW},
               "rows": [{k: v for k, v in r.items()} for r in rows],
               "crossings_at_risk": rc_, "crossings_far": fc,
               "n_at_risk": len(risk), "n_far": len(far)},
              open(dest, "w"), indent=1)
    print(f"\n  written: {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
