#!/usr/bin/env python3
"""THE LEGALITY GATE -- no verdict rests on an empty list, and no checker is trusted until it
has listed the moves of the STARTING position.

TWO CLAIMS A RECORD COULD NOT TELL APART, and this file exists to keep them apart:

    "the engine said nothing"            <- the checker returned ZERO legal moves
    "the model played an illegal move"   <- the checker returned a list WITHOUT the move

Chilly's chess record proved the pair is real, not hypothetical: the game loop called the best
move on the board illegal, the engine settled it (28 legal moves in that position, `f3e5` among
them -- exactly as the model's own reasoning said), and the real termination turned out to be a
token-cap truncation. A MISSING VALUE had been read as a JUDGEMENT, and the record could not
tell the two apart. Two reader defects had hidden it further: the answer arrived in a field the
reader never opened, and at the HEAD.

THE RULE, and it is one line of substance:

    a legality checker that returns ZERO legal moves is an ERROR, never a verdict
    -- and the POSITIVE CONTROL that licenses any verdict it produces is that the same
    checker enumerates the 20 moves of the STARTING position.

A checker that cannot list the one position whose answer nobody disputes cannot be trusted to
call a move illegal in a position nobody has seen.

WHAT THIS IS NOT: a move generator. It is the harness around one. Generating moves is the
oracle's job, and `go perft 1` over UCI is enough to do it with the standard library
(`UCI_MoveLister` below). This file decides WHEN a generator's output may be read as a verdict,
and what a verdict must carry. The candidate COUNT travels with every verdict on purpose: it is
the field that makes an empty list impossible to read as "illegal" downstream -- the same shape
as `placement_source`, where an unread placement says so instead of reading as a measurement.

Run:  python3 legal_gate.py                       -> the controls (fake checkers + real engine)
      STOCKFISH=/usr/games/stockfish python3 legal_gate.py
      python3 legal_gate.py /path/to/stockfish
"""
import os
import shutil
import subprocess
import sys

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
START_MOVES = frozenset("""
a2a3 b2b3 c2c3 d2d3 e2e3 f2f3 g2g3 h2h3
a2a4 b2b4 c2c4 d2d4 e2e4 f2f4 g2g4 h2h4
b1a3 b1c3 g1f3 g1h3
""".split())
DEFAULT_ENGINES = (
    "/opt/homebrew/bin/stockfish",              # macOS / Homebrew (arm64)
    "/usr/local/bin/stockfish",                 # macOS / Intel
    "/usr/games/stockfish",                     # Debian / Ubuntu
    "/usr/bin/stockfish",                       # Fedora / Arch
)


class CheckerError(Exception):
    """The checker failed its own control, or produced nothing to read."""


class NoLegalMoves(CheckerError):
    """The checker listed ZERO legal moves. That is an ERROR -- never 'the model played
    illegally'. `The engine said nothing` and `the model moved illegally` are different claims,
    and collapsing them is what cost Chilly a wrong termination label."""


def positive_control(list_moves, fen=START_FEN, label="checker"):
    """THE ONE-LINE CONTROL, as a function: the checker must list the STARTING position.

    Run before ANY verdict from `list_moves` is believed. Raises with the exact symmetric
    difference, so a checker that is off by one move names the move rather than quietly
    mislabelling every position it is asked about."""
    got = set(list_moves(fen))
    if got != START_MOVES:
        raise CheckerError(
            f"{label} FAILED THE POSITIVE CONTROL on the starting position: "
            f"{len(got)} moves listed, 20 expected; "
            f"missing={sorted(START_MOVES - got)} unexpected={sorted(got - START_MOVES)} "
            f"-- a checker that cannot enumerate THIS position cannot call a move illegal "
            f"in any other")
    return True


def verdict(list_moves, fen, move, label="checker", control=True):
    """Return (verdict, candidates) with verdict in {"legal", "illegal"}.

    The ONLY way to get "illegal" is a non-empty candidate list that does not contain `move`.
    Zero candidates raises `NoLegalMoves` before any verdict is formed."""
    if control:
        positive_control(list_moves, label=label)
    moves = set(list_moves(fen))
    if not moves:
        raise NoLegalMoves(
            f"{label} listed 0 legal moves for {fen!r}; refusing to convert an absent "
            f"measurement into the verdict 'the model played illegally'")
    return ("legal" if move in moves else "illegal"), len(moves)


def parse_perft(stdout):
    """`go perft 1` lines look like `e2e4: 1`. Anything else (id/info/Nodes searched) is
    metadata, not a move -- and `Nodes searched: N` must never be mistaken for a candidate."""
    moves = []
    for raw in stdout.splitlines():
        head = raw.split(":", 1)[0].strip()
        if (len(head) in (4, 5) and head[0] in "abcdefgh" and head[2] in "abcdefgh"
                and head[1] in "12345678" and head[3] in "12345678"):
            moves.append(head)
    return moves


def resolve_engine(argv_path=None):
    """$STOCKFISH -> argv[1] -> PATH -> platform default, failing loudly rather than falling
    through to a bare name (the shape freeze_check.py uses)."""
    for cand in (os.environ.get("STOCKFISH"), argv_path, shutil.which("stockfish")):
        if cand:
            if os.path.exists(cand):
                return cand
            raise SystemExit(f"engine not found: {cand}\n  set $STOCKFISH, or pass the path as argv[1]")
    for cand in DEFAULT_ENGINES:
        if os.path.exists(cand):
            return cand
    return None


class UCI_MoveLister:
    """A move lister that needs nothing but the standard library and a UCI engine binary."""

    def __init__(self, engine, timeout=30):
        self.engine, self.timeout = engine, timeout

    def __call__(self, fen):
        p = subprocess.run([self.engine],
                           input=f"uci\nposition fen {fen}\ngo perft 1\nquit\n",
                           capture_output=True, text=True, timeout=self.timeout)
        return parse_perft(p.stdout)


# ------------------------------------------------------------------ controls
def _t(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail and not ok else ""))
    return ok


def main():
    print("  the legality gate -- an empty list is an ERROR, and the start position is the control\n")
    results = []
    unseen_fen = "8/8/8/3pP3/8/8/8/4K2k w - d6 0 1"
    unseen_moves = ["e5d6", "e5e6", "e1d1", "e1d2", "e1e2", "e1f2", "e1f1", "h1g1"]

    # 0. the control on the control: this list is 20 moves, and the engine agrees.
    results.append(_t("the control itself is 20 moves", len(START_MOVES) == 20,
                      f"got {len(START_MOVES)}"))

    # 1. THE DEFECT SHAPE. A checker that is CORRECT on the start position and SILENT on the
    #    position being judged. This is not a hypothetical: it is the exact shape that produced
    #    Chilly's wrong termination label, and the front half passing is what made it invisible.
    def silent_when_it_matters(fen):
        return sorted(START_MOVES) if fen == START_FEN else []

    try:
        v = verdict(silent_when_it_matters, unseen_fen, "e5d6")
        results.append(_t("a silent checker never yields 'illegal'", False, f"returned {v!r}"))
    except NoLegalMoves as e:
        results.append(_t("a silent checker never yields 'illegal' (raises instead)",
                          "0 legal moves" in str(e)))

    # 2. AND IT STILL FAILS THE CONTROL'S SIBLING. A checker off by ONE move on the start
    #    position must be refused outright -- it would otherwise mislabel positions quietly.
    def off_by_one(fen):
        return sorted(START_MOVES - {"g1h3"}) if fen == START_FEN else unseen_moves

    try:
        verdict(off_by_one, unseen_fen, "e5d6")
        results.append(_t("a checker off by one move on startpos is refused", False))
    except CheckerError as e:
        results.append(_t("a checker off by one move on startpos is refused",
                          "missing=['g1h3']" in str(e)))

    # 3. A CORRECT checker: legal and illegal both carry a NON-ZERO candidate count.
    def correct(fen):
        return sorted(START_MOVES) if fen == START_FEN else list(unseen_moves)

    v_ok, n_ok = verdict(correct, unseen_fen, "e5d6")
    v_no, n_no = verdict(correct, unseen_fen, "a1a8")
    results.append(_t("a correct checker: the legal move reads legal", (v_ok, n_ok) == ("legal", 8)))
    results.append(_t("a correct checker: an illegal move reads illegal WITH its candidate count",
                      (v_no, n_no) == ("illegal", 8)))

    # 4. THE REAL ENGINE, when one resolves. The gate must pass on it, and the illegal verdict
    #    must come from a measured list -- 20 candidates on the start position, and a real,
    #    non-empty count on a position the model would be asked about.
    engine = resolve_engine(sys.argv[1] if len(sys.argv) > 1 else None)
    if engine is None:
        print("\n  engine: NOT RESOLVED -- $STOCKFISH, argv[1], PATH and the platform defaults all")
        print("  missed. The four controls above are stdlib-only and did not need it; the real-engine")
        print("  arm is UNMEASURED here, which is this script's own rule applied to itself.")
    else:
        lister = UCI_MoveLister(engine)
        print(f"\n  engine: {engine}")
        results.append(_t("real engine passes the positive control",
                          positive_control(lister, label=os.path.basename(engine))))
        real_fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1"
        v, n = verdict(lister, real_fen, "e2e4", label="stockfish")
        results.append(_t("real engine: a genuine illegal move reads illegal on a measured list",
                          v == "illegal" and n > 0, f"v={v} n={n}"))
        print(f"    verdict={v}  candidates={n}  <- the count is what makes the label auditable")

    print(f"\n  {sum(results)}/{len(results)} passed")
    if not all(results):
        print("  A verdict from an unlisted position is a caption, not a measurement.")
        return 1
    print("  'The engine said nothing' is now structurally distinct from 'the model played illegally'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
