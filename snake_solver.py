#!/usr/bin/env python3
"""SNAKE -- the deterministic baselines. Trivial solvers, so a model's number has something to beat.

THE SEAM IS BORROWED, WITH ATTRIBUTION, FROM `chynl/snake` (MIT, 1,796 stars): a solver is an object with
`next_direct(state) -> "U"|"D"|"L"|"R"`. That repo ships a Hamiltonian-cycle GraphAgent that reaches ~94%
and a DQN at ~50%; the point of shipping the deterministic one here is that an LLM's score must be read
AGAINST a floor, not in a vacuum. THE IMPLEMENTATION IS OURS -- the interface is the part worth carrying.

THE BOARD IS A TORUS. Measured from `snake/snake.html`: the tick wraps `snake.x`/`snake.y` at the canvas
edge, so there are NO WALLS -- the only way to die is to run into your own body. A Hamiltonian cycle over
the torus therefore exists to be followed, and a follower that stays on it CANNOT die while the snake is
shorter than the board.

    CycleAgent          -- follows the cycle exactly. PROVABLY cannot die (length < cells). The floor.
    CycleShortcutAgent  -- follows the cycle but takes a shortcut toward the apple while the shortcut
                           stays inside the free window ahead of the head. Strictly better score; the
                           safety argument is `free window` below and is checked in every run.

NEITHER SOLVER READS THE PIXELS OR THE GAME'S INTERNALS: each is handed (head, direction, body cells,
apple) and returns one letter -- the same object the model arm gets.
"""

DIRS = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}
OPPOSITE = {"U": "D", "D": "U", "L": "R", "R": "L"}


def dir_from_delta(dx, dy):
    """-> the control letter a velocity corresponds to. The game's own units: a pixel delta."""
    if dx == 0 and dy == 0:
        return None
    if dx > 0:
        return "R"
    if dx < 0:
        return "L"
    return "D" if dy > 0 else "U"


def hamiltonian_cycle(w, h):
    """A HAMILTONIAN CYCLE ON THE w x h TORUS, constructed rather than searched.

    THE CONSTRUCTION, and why it needs no search: keep column w-1 as a RETURN CORRIDOR and
    boustrophedon the block of columns 0..w-2. The block ends at its last row; step right into the
    corridor, run the corridor back up to row 0, and one more step right wraps onto (0, 0) -- which is
    where the block started. That closes the cycle and touches every cell exactly once.

    It requires the LAST ROW of the block to be a left-to-right pass, i.e. (h-1) even. When h is even the
    plain boustrophedon already closes (it ends at (0, h-1) and stepping down wraps to (0, 0)), and when
    w is odd instead, the same figure is used transposed. The 25x25 board the game ships hits the FIRST
    case, and the check below is what makes that a measurement instead of a hope:
    `selftest()` asserts every cell is visited exactly once and every consecutive pair (cyclically) is
    adjacent on the torus, for the real size and for a range of others.

    MEASURED AND WORTH STATING: on the 25x25 board the game's own opening direction (dx=+16, right, from
    cell (10,10)) is ALONG this cycle, so the follower is safe from its very first tick rather than after
    a transient. `selftest()` asserts that too.
    """
    if h % 2 == 1:
        cyc = []
        for r in range(h):
            cols = range(w - 1) if r % 2 == 0 else range(w - 2, -1, -1)
            cyc.extend((c, r) for c in cols)
        cyc.extend((w - 1, r) for r in range(h - 1, -1, -1))
        return cyc
    if w % 2 == 1:
        return [(c, r) for (r, c) in hamiltonian_cycle(h, w)]
    cyc = []
    for r in range(h):
        cols = range(w) if r % 2 == 0 else range(w - 1, -1, -1)
        cyc.extend((c, r) for c in cols)
    return cyc


def cycle_next(cell, w, h):
    return ((cell[0] + 1) % w, cell[1]) if cell[0] + 1 < w else (0, cell[1])


class Board:
    """The cycle, its index map, and the geometry every agent needs. Built from the size the GAME
    reports (`canvas.width / grid`), never from a number typed in this file."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        cyc = hamiltonian_cycle(w, h)
        assert len(cyc) == w * h, "cycle covers %d cells, board has %d" % (len(cyc), w * h)
        assert len(set(cyc)) == len(cyc), "cycle repeats a cell"
        for i, cell in enumerate(cyc):
            nxt = cyc[(i + 1) % len(cyc)]
            assert abs(cell[0] - nxt[0]) + abs(cell[1] - nxt[1]) == 1 or \
                (abs(cell[0] - nxt[0]) == w - 1 and cell[1] == nxt[1]) or \
                (abs(cell[1] - nxt[1]) == h - 1 and cell[0] == nxt[0]), \
                "cycle step %d: %s -> %s is not a move on the torus" % (i, cell, nxt)
        self.cycle = cyc
        self.pos = {c: i for i, c in enumerate(cyc)}
        self.n = len(cyc)

    def fwd(self, a, b):
        """forward distance a -> b along the cycle, in [0, n)."""
        return (self.pos[b] - self.pos[a]) % self.n

    def neighbours(self, cell):
        c, r = cell
        return [(c + 1) % self.w, r], [(c - 1) % self.w, r], [c, (r + 1) % self.h], [c, (r - 1) % self.h]


def _coords(state):
    """The one place the wrapper's state is turned into a solver's view: cells in GRID COORDINATES and
    the head cell. The game reports pixels; the solver works in cells; the conversion happens once."""
    g = state["grid"]
    head = (state["head"][0] // g, state["head"][1] // g)
    apple = (state["apple"][0] // g, state["apple"][1] // g)
    cells = [(c[0] // g, c[1] // g) for c in state["cells"]]
    return head, apple, cells


class CycleAgent:
    """Follow the cycle. The floor, and the only solver here with a safety PROOF rather than a check."""

    name = "baseline-cycle"

    def __init__(self, board):
        self.board = board

    def next_direct(self, state):
        head, _apple, _cells = _coords(state)
        nxt = self.board.cycle[(self.board.pos[head] + 1) % self.board.n]
        return self._letter(head, nxt)

    def _letter(self, a, b):
        """-> the control letter for a step from cell a to a NEIGHBOUR b on the torus. The deltas are
        taken modulo the board, which is what makes the wrap columns (w-1 steps) read as LEFT/UP."""
        w, h = self.board.w, self.board.h
        dx, dy = (b[0] - a[0]) % w, (b[1] - a[1]) % h
        if dx == 1 and dy == 0:
            return "R"
        if dx == w - 1 and dy == 0:
            return "L"
        if dy == 1 and dx == 0:
            return "D"
        if dy == h - 1 and dx == 0:
            return "U"
        raise AssertionError("not adjacent on the torus: %s -> %s" % (a, b))

    def why(self, state):
        return "cycle step"


class CycleShortcutAgent(CycleAgent):
    """Follow the cycle, and cut the corner toward the apple when the corner is inside the FREE WINDOW.

    THE FREE WINDOW, and this is the whole safety argument: every occupied cell lies inside the forward
    arc [tail .. head] of the cycle. `shortcut()` therefore only ever moves to a cell whose forward
    distance from the head is between 1 and (tail - head - 1) -- strictly inside the empty stretch
    between the head and the tail -- where by the invariant nothing can be occupied. The window is
    computed with the tail cell EXCLUDED, so it is safe in both tail regimes the game has: while the snake
    is still growing (`cells.length < maxCells`) the tail does NOT advance, and a move onto it would be a
    self-collision.

    IT IS NOT A PROOF THAT THE AGENT NEVER DIES -- a shortcut can leave holes in the arc, and the
    invariant is argued rather than verified. So the driver records deaths for both baselines and the
    artifact carries them: the claim is measured on the seed list, not asserted.
    """

    name = "baseline-cycle-shortcut"

    def __init__(self, board, lookahead=False):
        CycleAgent.__init__(self, board)
        self.lookahead = lookahead

    def next_direct(self, state):
        head, apple, cells = _coords(state)
        b = self.board
        if not cells:
            return CycleAgent.next_direct(self, state)
        tail = cells[-1]
        window = (b.pos[tail] - b.pos[head] - 1) % b.n          # free cells strictly between head and tail
        if window < 1:
            return CycleAgent.next_direct(self, state)
        best, best_gain = None, None
        for letter, (dx, dy) in DIRS.items():
            nb = ((head[0] + dx) % b.w, (head[1] + dy) % b.h)
            d = b.fwd(head, nb)
            if d == 0 or d > window:
                continue                                        # occupied arc, or the tail itself
            gain = b.fwd(nb, apple)                             # how far the apple stays ahead
            if best_gain is None or gain < best_gain:
                best, best_gain = letter, gain
        return best or CycleAgent.next_direct(self, state)

    def why(self, state):
        head, apple, cells = _coords(state)
        return "shortcut toward the apple inside the free window" if cells else "cycle step"


class GreedySafeAgent:
    """Shortest path to the apple, screened by "can I still reach my own tail after this step".

    WHY THIS AGENT EXISTS AT ALL, measured rather than assumed: the cycle follower never dies, but it is a
    LAP machine -- from the game's start cell (10,10) the first apple (20,20) sits 20 steps away and the
    follower needs ~273 ticks to arrive, because the cycle crosses rows in order. Over a short horizon the
    follower scores 0 and would make an entrant's own 0 unreadable. So the floor that matters on a short
    list is this one, and BOTH are shipped rather than one chosen for the entrant's benefit.

    THE SCREEN, which is the standard one: after the move, the head must still be able to reach the tail
    through cells the body does not occupy. It is a heuristic with a known failure mode on tight boards --
    it is not a proof -- so deaths are recorded per baseline and reported beside the score.

    THE REVERSAL IS NEVER A CANDIDATE, and that is not a preference: the game's own handler ignores it, so
    asking for it does nothing and the snake keeps its velocity. A solver that believed it had turned
    would be planning against a board that does not exist.
    """

    name = "baseline-greedy-safe"

    def __init__(self, board):
        self.board = board

    def next_direct(self, state):
        b = self.board
        head, apple, cells = _coords(state)
        body = list(cells)
        current = dir_from_delta(*state["dir"])
        blocked = set(body[1:])                       # the head's own cell is about to be vacated
        tail = body[-1] if body else None
        cands = []
        for letter, (dx, dy) in DIRS.items():
            if current and letter == OPPOSITE[current]:
                continue                              # THE REVERSAL: the game's handler ignores it
            nb = ((head[0] + dx) % b.w, (head[1] + dy) % b.h)
            if nb in blocked:
                continue
            cands.append((letter, nb))
        if not cands:
            return CycleShortcutAgent(b).next_direct(state)
        scored = []
        for letter, nb in cands:
            grown = [nb] + body[:max(0, state["maxCells"] - 1)]      # the tail kept: the safe superset
            space = self._free_space(nb, set(grown[1:]))
            dist = self._dist(nb, apple, set(grown)
                              | ({tail} if tail and tail not in grown[1:] else set()))
            scored.append(((dist if dist is not None else 10 ** 6), -space, letter, nb))
        safe = [s for s in scored if self._reaches_tail(s[3], *self._after(s[3], body, state))]
        pool = safe or scored
        pool.sort(key=lambda s: (s[0], s[1], s[2]))
        return pool[0][2]

    @staticmethod
    def _after(nb, body, state):
        grown = [nb] + body[:max(0, state["maxCells"] - 1)]
        return grown[0], grown[-1], set(grown[1:])

    def _neighbours(self, cell, blocked):
        for nb in self.board.neighbours(cell):
            t = tuple(nb)
            if t not in blocked:
                yield t

    def _dist(self, src, dst, blocked):
        """BFS length from src to dst over cells the body does not occupy. Torus-wrapped."""
        if src == dst:
            return 0
        seen = {src}
        q = [(src, 0)]
        while q:
            cur, d = q.pop(0)
            for nb in self._neighbours(cur, blocked):
                if nb == dst:
                    return d + 1
                if nb not in seen:
                    seen.add(nb)
                    q.append((nb, d + 1))
        return None

    def _free_space(self, src, blocked):
        seen, q = {src}, [src]
        while q:
            cur = q.pop()
            for nb in self._neighbours(cur, blocked):
                if nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        return len(seen)

    def _reaches_tail(self, nb, new_head, tail, blocked):
        return self._dist(new_head, tail, blocked) is not None


def selftest():
    """THE CYCLE IS A MEASUREMENT, NOT A HOPE. Three assertions per size: complete coverage, no repeats,
    every step a legal move on the torus -- and, for the board the game actually ships, that the game's
    own opening direction lies along the cycle."""
    bad = 0
    sizes = [(25, 25), (16, 16), (20, 20), (24, 25), (25, 24), (21, 21), (10, 37), (37, 10), (5, 5)]
    for w, h in sizes:
        try:
            Board(w, h)
            print("  ok   cycle %2dx%-2d  %d cells" % (w, h, w * h))
        except AssertionError as e:
            bad += 1
            print("  FAIL cycle %2dx%-2d  %s" % (w, h, e))
    b = Board(25, 25)
    first = b.cycle[(b.pos[(10, 10)] + 1) % b.n]
    along = first == (11, 10)
    print("  game's opening cell (10,10) -> cycle next %s, game's own opening direction is right: %s"
          % (first, "ALONG the cycle" if along else "NOT along the cycle -- the follower needs a transient"))
    if not along:
        bad += 1
    print("  cycle self-test: %d failure(s)" % bad)
    return bad == 0


if __name__ == "__main__":
    import sys
    print("=" * 100)
    print("SNAKE -- the deterministic baselines, self-test")
    print("=" * 100)
    sys.exit(0 if selftest() else 1)
