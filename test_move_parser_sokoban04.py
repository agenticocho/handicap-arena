"""Parser validation cases for the strict MOVE parser."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sokoban_harness import parse_move

cases = [
    ("clean MOVE: D", "MOVE: D", "D"),
    ("reasoning after first line", "MOVE: D\n\nReasoning here about boxes.", "D"),
    ("plan whose ninth letter is a move must NOT parse", "U D L R U D L R D", None),
    ("plan with ninth move D but MOVE: U committed", "MOVE: U\nPlan: R L R L R L R L D", "U"),
    ("bare letter D -> malformed", "D", None),
    ("empty -> malformed", "", None),
]

def main():
    fails = 0
    for name, text, expected in cases:
        got, status = parse_move(text)
        committed = got if status == "ok" else None
        ok = committed == expected
        print(("PASS" if ok else "FAIL"), "-", name, "->", committed)
        if not ok:
            fails += 1
    # extra: ninth move letter specifically must not equal D when no header
    got, status = parse_move("R L R L R L R L D")
    assert not (status == "ok" and got == "D"), "ninth move committed!"
    print("PASS - ninth-move guard")
    if fails:
        print(f"{fails} FAILED")
        sys.exit(1)
    print("ALL PARSER CASES PASS")
    sys.exit(0)

if __name__ == "__main__":
    main()
