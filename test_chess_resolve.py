#!/usr/bin/env python3
"""CONTROLS FOR THE MOVE READER -- the class that produced a published `illegal-move` for the best move.

Chilly's requirement, and it is the general form of the defect: A LEGALITY CHECKER THAT CANNOT LIST THE
MOVES OF THE STARTING POSITION IS NOT A LEGALITY CHECKER. The control is asserted before any termination
may be read as a verdict about an entrant, because a checker handed an empty list calls EVERY move illegal
-- its verdict AGREES WITH ITS OWN FAILURE and reports the model as the cause.

FIVE CASES, AND EACH ONE IS A REAL FAILURE THAT HAPPENED OR WAS REASONED ABOUT RATHER THAN IMAGINED:

  1  the control itself      legal_moves(STARTPOS) == 20 -- nobody has to interpret it
  2  the published case      `**f3e5**` + the reasoning that mentions "the d5 pawn". This is the record
                             that said illegal-move for the best move on the board.
  3  genuinely ambiguous     two moves named in the HEAD -- must still refuse, because refusing to guess
                             is correct; only REASONING is not ambiguity
  4  empty list              a checker given no moves must say SO, not agree that everything is illegal
  5  regressions             SAN, bare UCI, decorated UCI, promotion piece, castling, illegal moves

    python3 test_chess_resolve.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess_game as g                                                # noqa: E402

POS = "rnbqkbnr/ppp2ppp/8/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3"
fails = []


def ck(name, got, want):
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        print(f"          got  {got!r}\n          want {want!r}")
        fails.append(name)


print("=" * 94)
print("MOVE READER CONTROLS")
print("=" * 94)

# --- 1. THE CONTROL ITSELF -------------------------------------------------------------------------
print("\n[1] the positive control -- before any termination may be trusted")
ck("legal_moves(STARTPOS) == 20  (a reader that cannot do this is not a reader)",
   len(g.legal_moves(g.STARTPOS)), 20)

# --- 2. THE PUBLISHED CASE -------------------------------------------------------------------------
print("\n[2] THE PUBLISHED CASE -- the record that called the best move illegal")
LEG = g.legal_moves(POS)
ck("the position has 28 legal moves", len(LEG), 28)
ck("f3e5 IS legal (the engine is the authority)", "f3e5" in LEG, True)
# the model's exact output, reconstructed from the record's own why field
MODEL_TEXT = "**f3e5**\n\nThe black pawn on e5 is undefended (the d5 pawn defends nothing here)."
ck("the answer is read from the HEAD, not mined from the reasoning",
   g.resolve(POS, MODEL_TEXT, LEG)[:2], ("f3e5", "f3e5"))
ck("and it says WHERE it was found", g.resolve(POS, MODEL_TEXT, LEG)[2], "resolved-head")
# and the failure is shown to be reachable: mining the WHOLE text does find two moves
ck("the reasoning DOES name a second legal move (this is why the old guard refused)",
   sorted(g._extract(POS, MODEL_TEXT, LEG)), ["e4d5", "f3e5"])

# --- 3. GENUINELY AMBIGUOUS -- the guard must still work --------------------------------------------
print("\n[3] genuinely ambiguous -- refusing to guess is correct and must survive the fix")
ck("two moves in the HEAD refuses",
   g.resolve(POS, "f3e5 or e4d5", LEG)[0], None)
ck("and the reason names ambiguity rather than illegality",
   g.resolve(POS, "f3e5 or e4d5", LEG)[2].split(":")[0], "ambiguous")

# --- 4. THE EMPTY LIST ------------------------------------------------------------------------------
print("\n[4] a checker handed NO moves must say so, not agree that everything is illegal")
ck("empty list -> refuses AND names the instrument",
   g.resolve(POS, "f3e5", [])[2].split(":")[0], "no-legal-moves-supplied")
ck("empty model output -> unreadable, not illegal",
   g.resolve(POS, "", LEG)[2].split(":")[0], "unreadable")

# --- 5. REGRESSIONS: the three earlier false verdicts, plus notation ---------------------------------
print("\n[5] regressions -- every false verdict this reader has already produced")
ck("(1) SAN `e4`", g.resolve(g.STARTPOS, "e4", g.legal_moves(g.STARTPOS))[0], "e2e4")
ck("(2) UCI `g1f3` is NOT read as a pawn from g1",
   g.resolve(g.STARTPOS, "g1f3", g.legal_moves(g.STARTPOS))[0], "g1f3")
ck("(2b) SAN `Nf3`", g.resolve(g.STARTPOS, "Nf3", g.legal_moves(g.STARTPOS))[0], "g1f3")
ck("(3) decorated `**e2e4**`", g.resolve(g.STARTPOS, "**e2e4**", g.legal_moves(g.STARTPOS))[0], "e2e4")
ck("(3b) decorated SAN in backticks", g.resolve(g.STARTPOS, "`Nf3`", g.legal_moves(g.STARTPOS))[0], "g1f3")
ck("prose with the move on line 1", g.resolve(g.STARTPOS, "I play e2e4.\nbecause it is good.",
                                             g.legal_moves(g.STARTPOS))[0], "e2e4")
ck("an ILLEGAL move is still refused (Qh5 from the startpos)",
   g.resolve(g.STARTPOS, "Qh5", g.legal_moves(g.STARTPOS))[0], None)
ck("nonsense is still refused", g.resolve(g.STARTPOS, "xyz", g.legal_moves(g.STARTPOS))[0], None)
ck("castling", g.resolve("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1", "O-O",
                         g.legal_moves("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"))[0], "e1g1")
ck("promotion names its piece", g.resolve("8/P7/8/8/8/8/8/k6K w - - 0 1", "a8=Q",
                                          g.legal_moves("8/P7/8/8/8/8/8/k6K w - - 0 1"))[0], "a7a8q")
ck("a bare pawn push to the last rank is refused (promotion is mandatory)",
   g.resolve("8/P7/8/8/8/8/8/k6K w - - 0 1", "a7a8", g.legal_moves("8/P7/8/8/8/8/8/k6K w - - 0 1"))[0], None)

print("\n" + "=" * 94)
n = 20 - len(fails)
print(f"{'ALL CONTROLS PASS' if not fails else str(len(fails)) + ' FAILED'}   --  {n}/20")
if fails:
    for f in fails:
        print(f"  FAILED: {f}")
print("=" * 94)
sys.exit(1 if fails else 0)
