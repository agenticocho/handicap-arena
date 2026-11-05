"""crossword_eval.py -- the DEFINITION of eval_before / eval_after for a crossword trace.

WHY THIS FILE EXISTS
    Jarvis's first ornith9b trace carried `eval_before: 'ok'` / `eval_after: 'ok'` on all 92 turns and
    `contradiction_count: 0`.  'ok' is the chess schema's field name inherited into a crossword trace:
    `grep -n "eval_" crossword_gen.py crossword_play.py crossword_rung.py crossword_pilot_ceiling.py`
    returns nothing, and EVENT_chess.md:130 defines the field as "the engine's evaluation at a frozen
    depth".  A crossword has no engine and no depth, so the field was filled with whatever was cheap
    (well-formedness), which cannot fall.  A measure that cannot fall is not a measure.

THE DEFINITION
    eval(state) = the number of slots that remain SATISFIABLE given the letters already on the grid.
                  A slot is satisfiable when at least one of its declared `candidates` agrees with
                  every letter already placed in the cells the slot covers.
                  Range 0..n_slots.  Deterministic, model-free, reproducible from the crate alone.

    eval_before = satisfiable count before the turn's placement.
    eval_after  = satisfiable count after it.
    A turn that places a wrong letter LOWERS the count for every slot that crosses it; a turn that
    places a declared candidate raises or holds it.  The pair therefore says whether the player is
    gaining ground, which is exactly what the chess pair says about a move.

    contradiction = a placement whose letters disagree with a letter already on the grid at a cell the
                    new entry covers.  This is the ONLY consistency relation a crossword has, so the
                    contradiction detector must compare a new fill against the ALREADY-FILLED
                    CROSSINGS.  A checker that only asks "is every cell filled / is every entry the
                    declared length" can return 0 forever, and did.

    Run: python3 crossword_eval.py            (self-test against the crate's own two puzzles)
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CRATE = os.path.join(HERE, "probes", "CROSSWORD_CRATE_2026-11-05.json")


def cells_of(slot):
    """(row, col) of every cell a slot covers, in answer order."""
    r, c = slot["row"], slot["col"]
    if slot["direction"] == "across":
        return [(r, c + i) for i in range(slot["length"])]
    return [(r + i, c) for i in range(slot["length"])]


def pattern_for(slot, grid):
    return "".join(grid.get(cell, "_") for cell in cells_of(slot))


def fits(word, pattern):
    return len(word) == len(pattern) and all(p == "_" or p == w for w, p in zip(word, pattern))


def satisfiable(slot, grid):
    """How many declared candidates survive the letters already on the grid."""
    pat = pattern_for(slot, grid)
    return sum(1 for w in slot["candidates"] if fits(w, pat))


def evaluate(puzzle, grid):
    """eval(state): slots still satisfiable, out of the slots the puzzle declares."""
    return sum(1 for s in puzzle["slots"] if satisfiable(s, grid) > 0)


def contradictions(puzzle, grid, new_cells):
    """A placement is contradictory when it disagrees with a letter already on the grid
    at a cell it covers.  `new_cells` maps (r, c) -> letter for the placement itself."""
    return sum(1 for cell, letter in new_cells.items()
               if cell in grid and grid[cell] != letter)


def place(grid, slot, word):
    out = dict(grid)
    for cell, letter in zip(cells_of(slot), word):
        out[cell] = letter
    return out


def _selftest():
    crate = json.load(open(CRATE))
    print("crate puzzles:", len(crate["puzzles"]))
    for pi, puzzle in enumerate(crate["puzzles"]):
        n = len(puzzle["slots"])
        print(f"\npuzzle {pi}: {puzzle['rows']}x{puzzle['cols']}  slots {n}")

        empty = {}
        print(f"  eval(empty grid)                 = {evaluate(puzzle, empty)}/{n}   all slots reachable")

        solved = {}
        for s in puzzle["slots"]:
            solved = place(solved, s, s["answer"])
        print(f"  eval(crate's own answers)        = {evaluate(puzzle, solved)}/{n}   "
              f"contradictions {contradictions(puzzle, solved, solved)}")

        # The failure mode Jarvis measured: crossword-shaped text, placed letter-by-letter.
        shaped = {}
        junk = "ANSWERCLUEFAKE"
        cells = [c for s in puzzle["slots"] for c in cells_of(s)]
        for i, cell in enumerate(cells):
            shaped[cell] = junk[i % len(junk)]
        print(f"  eval(92 turns of {junk!r} letters)  = {evaluate(puzzle, shaped)}/{n}   "
              f"<- the count this definition CAN make fall; 'ok' could not")

        # One wrong letter inside an otherwise solved grid: the crossing slots lose candidates.
        s0 = puzzle["slots"][0]
        bad = dict(solved)
        for cell in cells_of(s0)[:1]:
            bad[cell] = "Q"
        print(f"  eval(one wrong letter in {s0['id']})      = {evaluate(puzzle, bad)}/{n}   "
              f"(was {n}; a single bad cell is visible)")


if __name__ == "__main__":
    _selftest()
