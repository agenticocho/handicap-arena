#!/usr/bin/env python3
"""THE CHESS DERIVATIONS, PUBLISHED AS CODE, BESIDE THE FIELD LIST.

Chilly's pricing of the derivation rule: *carry what cannot be derived, derive what can -- AND PUBLISH
THE DERIVATION beside the field list, so the second implementation inherits the TESTED clause rather than
re-deriving the obvious-and-wrong one.*

This file is that publication, and the en-passant case is why it exists. The obvious clause --

    capture := the destination square is occupied in fen

-- is wrong for exactly one move in the game, silently, and a second implementer would write it and never
see it fail. Its test is below.

WHY THESE LIVE HERE RATHER THAN IN A BUNDLE: every function below is recomputable from `fen` + `move_uci`,
which is the test for whether a field belongs in the record at all. Carrying them would create a second
source for a fact the primitives already state -- and all of today's worst defects are exactly that: a
compact stand-in trusted after the thing it stands for had changed or been approximated.

WHAT IS *NOT* HERE: SAN. Disambiguation (`Nbd2` vs `Nfd2`) needs the OTHER candidate movers, which
`fen` + `move_uci` do not carry -- so SAN is a field, carried for the right reason.

Run: chess_derive.py          -> the tests, including the en-passant case
"""
import sys

EP_TARGET_INDEX = 3          # the fen's fourth field


def parse_fen(fen):
    placement, turn, castling, ep, *_ = fen.split()
    board, rank = {}, 8
    for row in placement.split("/"):
        f = 0
        for ch in row:
            if ch.isdigit():
                f += int(ch)
            else:
                board[chr(ord("a") + f) + str(rank)] = ch
                f += 1
        rank -= 1
    return {"board": board, "turn": turn, "castling": castling, "ep": ep}


def derive_capture(fen, move_uci):
    """TESTED CLAUSE. Two cases, and the second is the one everybody misses.

    1. the destination square is occupied -- the obvious case;
    2. EN PASSANT: the moving piece is a pawn, and the destination IS the fen's en-passant target. The
       destination is EMPTY in that position -- the victim leaves from the square the pawn passed over.

    Verified against Arena's position: `8/8/8/3pP3/8/8/8/4K2k w - d6 0 1`, move `e5d6`. d6 is empty and
    the move IS a capture.
    """
    st = parse_fen(fen)
    src, dst = move_uci[:2], move_uci[2:4]
    piece = st["board"].get(src, "")
    if st["board"].get(dst):
        return True                                   # case 1
    if piece.lower() == "p" and st["ep"] != "-" and dst == st["ep"]:
        return True                                   # case 2 -- en passant
    return False


def derive_promotion(move_uci):
    """The suffix, if the move has one. It is in the notation already."""
    return move_uci[4] if len(move_uci) > 4 else None


def derive_castling(fen, move_uci):
    """A KING moving TWO FILES. The rook's square follows from which two files.

    TWO, not one -- and the test caught that: the first version of this function returned "kingside" for
    any rightward king move, so `e1f1` was classed as castling. A king stepping one square is a king
    stepping one square, and the difference is the entire flag.
    """
    st = parse_fen(fen)
    src, dst = move_uci[:2], move_uci[2:4]
    piece = st["board"].get(src, "")
    if piece.lower() != "k":
        return None
    delta = ord(dst[0]) - ord(src[0])
    if delta == 2:
        return "kingside"
    if delta == -2:
        return "queenside"
    return None


def derive_check(fen, move_uci):
    """COST, stated rather than hidden: applying the move means moving the piece, moving the castling
    rook, removing the en-passant victim, and applying the promotion. LESS THAN A LEGAL-MOVE GENERATOR,
    MORE THAN ZERO -- and shared work for every reader of a bundle.

    NOT IMPLEMENTED HERE, deliberately: a wrong implementation of `check` is worse than none, because it
    looks computational. The clause is stated so a second implementer knows the cost before starting.
    """
    raise NotImplementedError(
        "apply the move (piece, castling rook, en-passant victim, promotion) then test the king square")


# --------------------------------------------------------------------------- tests
def _t(name, got, want):
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"   got {got!r}, want {want!r}"))
    return ok


def main():
    print("  chess derivations -- the TESTED clauses, with the trap cases\n")
    results = []

    # THE EN PASSANT CASE, verified by Arena against the fen.
    ep_fen = "8/8/8/3pP3/8/8/8/4K2k w - d6 0 1"
    results.append(_t("en passant: e5d6 IS a capture onto an EMPTY square",
                      derive_capture(ep_fen, "e5d6"), True))
    results.append(_t("  ...and the destination really is empty in that fen",
                      bool(parse_fen(ep_fen)["board"].get("d6")), False))

    # an ordinary capture, so the fix did not break the obvious case.
    # NOTE: the first version of this test used the EN PASSANT fen for the ordinary case and expected a
    # capture -- d6 is EMPTY in that position, so it failed, and it failed for the original bug's reason.
    # Making a test for "capture" out of a position whose whole point is that the destination is empty is
    # the same confusion, one layer out. This fen has a black pawn ON d6.
    cap_fen = "8/8/3p4/4P3/8/8/8/4K2k w - - 0 1"
    results.append(_t("ordinary capture: e5d6 with a piece on d6", derive_capture(cap_fen, "e5d6"), True))
    results.append(_t("  ...and the destination really is occupied in that fen",
                      bool(parse_fen(cap_fen)["board"].get("d6")), True))

    # a quiet pawn push is NOT a capture
    quiet = "8/8/8/4P3/8/8/8/4K2k w - - 0 1"
    results.append(_t("quiet push: e5e6 is not a capture", derive_capture(quiet, "e5e6"), False))

    # promotion rides in the notation
    results.append(_t("promotion suffix is in the move", derive_promotion("e7e8q"), "q"))
    results.append(_t("no suffix means no promotion", derive_promotion("e2e4"), None))

    # castling is a king moving two files
    results.append(_t("castling: e1g1 is kingside", derive_castling("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "e1g1"), "kingside"))
    results.append(_t("castling: e1c1 is queenside", derive_castling("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "e1c1"), "queenside"))
    results.append(_t("a king's one-square move is not castling",
                      derive_castling("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "e1f1"), None))

    # CHECK is stated, not implemented -- and saying so is the point
    try:
        derive_check(fen=cap_fen, move_uci="e5d6")
        results.append(_t("check raises NotImplementedError rather than guessing", False, True))
    except NotImplementedError:
        results.append(_t("check raises NotImplementedError rather than guessing", True, True))

    print(f"\n  {sum(results)}/{len(results)} passed")
    if not all(results):
        print("  A derivation that is not tested is a derivation that will be re-derived wrong.")
        return 1
    print("  The obvious clause fails the en-passant case; the tested clause does not.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
