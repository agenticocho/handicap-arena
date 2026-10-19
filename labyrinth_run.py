#!/usr/bin/env python3
"""labyrinth_run.py — one model, one level, one letter at a time.

Scope (agreed with Jarvis, 2026-10-19): a PORTABLE CELL both machines can run, so that
"hard data from both machines" means two measurements of one test. This is a benchmark
driver, not a Hermes optimization: nothing here makes the agent runtime faster.

The oracle is a pure function of a frozen graph file, invoked on demand, which exits.
No daemon, no socket, no resident process.

TEST IDENTITY
    A cell is identified by (graph_digest, symmetrisation, K) + cell_spec_sha256.
    graph_digest is a CONTENT digest, not a byte digest, so re-serialising the JSON
    cannot silently change the test:

        sha256( b"ged-v1\n" + for each node a in file order:
                    a + "\t" + ",".join(str(ged_fwd[a][y]) for y in nodes) + "\n" )

    The file's byte digest is recorded separately (file_sha256) as transport evidence.
    Neither pins the test alone: two boxes can hold byte-identical graphs and derive
    different neighbour sets if symmetrisation or K differ. All of it is recorded.

ADMISSION (refuses BEFORE the first turn, with a distinguishable exit code)
    2  bad arguments
    3  graph file unreadable / malformed
    4  symmetrisation not named                <- the whole point: no silent default
    5  graph_digest does not match --expect-graph-digest
    6  derivation check failed: at K=12 the derived adjacency disagrees with the
       shipped adjacency_*_K column, so this file is not internally consistent
    7  output path already exists and this record did not take it
    8  graph disconnected from --rune (no legal move at start)

    Exit 0 on a completed record. --dry-run exits 0 too, but writes a record marked
    dry_run=true and refuses to call it a benchmark row.

RECORD
    one JSON per cell in probes/, carrying: model, server_argv, server_binary_digest,
    decoder mode, seed, cap, graph identity, every move with its legal set size,
    blocked / not_an_action / give_up counts, per-turn tokens, ended, end_state.
"""
import argparse
import hashlib
import json
import os
import random
import sys

EXIT_BAD_ARGS = 2
EXIT_BAD_GRAPH = 3
EXIT_NO_SYMMETRISATION = 4
EXIT_DIGEST_MISMATCH = 5
EXIT_DERIVATION_MISMATCH = 6
EXIT_RECORD_EXISTS = 7
EXIT_UNREACHABLE = 8

SELF = os.path.abspath(__file__)


def die(code, msg):
    print(f"labyrinth_run: exit {code}: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_graph(path):
    try:
        raw = open(path, "rb").read()
    except OSError as e:
        die(EXIT_BAD_GRAPH, f"cannot read graph: {e}")
    try:
        g = json.loads(raw)
    except ValueError as e:
        die(EXIT_BAD_GRAPH, f"graph is not JSON: {e}")
    for k in ("nodes", "ged_fwd", "semantics"):
        if k not in g:
            die(EXIT_BAD_GRAPH, f"graph missing key {k!r}")
    nodes = g["nodes"]
    F = g["ged_fwd"]
    if len(nodes) != 24:
        die(EXIT_BAD_GRAPH, f"graph has {len(nodes)} nodes, expected 24")
    if len(set(nodes)) != 24:
        die(EXIT_BAD_GRAPH, "duplicate node names")
    for a in nodes:
        if a not in F or any(y not in F[a] for y in nodes):
            die(EXIT_BAD_GRAPH, f"ged_fwd incomplete at {a}")
    return raw, g, nodes, F


def file_sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def graph_digest(nodes, F):
    h = hashlib.sha256()
    h.update(b"ged-v1\n")
    for a in nodes:
        h.update(a.encode("utf-8") + b"\t")
        h.update(",".join(str(F[a][y]) for y in nodes).encode("utf-8") + b"\n")
    return h.hexdigest()


def d(nodes, F, sym, a, b):
    """distance under the named symmetrisation. No default, no cache, no order dependence."""
    if sym == "min":
        return min(F[a][b], F[b][a])
    if sym == "max":
        return max(F[a][b], F[b][a])
    if sym == "ged_fwd":
        return F[a][b]
    if sym == "ged_rev":
        return F[b][a]
    die(EXIT_NO_SYMMETRISATION, f"unknown symmetrisation {sym!r}")


def neighbours(nodes, F, sym, K, cur):
    return sorted(y for y in nodes
                  if y != cur and 0 < d(nodes, F, sym, cur, y) <= K)


def check_derivation(g, nodes, F):
    """The shipped adjacency_*_K columns must equal what the matrix says at K=12.
    If they disagree the file is not internally consistent and must not be scored."""
    K = g["semantics"].get("K", 12)
    checked = 0
    for sym, key in (("min", "adjacency_min_K"), ("max", "adjacency_max_K")):
        if key not in g:
            continue
        for a in nodes:
            want = sorted(g[key][a])
            got = neighbours(nodes, F, sym, K, a)
            if want != got:
                die(EXIT_DERIVATION_MISMATCH,
                    f"{key}[{a}] disagrees with the matrix at K={K}: "
                    f"shipped {len(want)} neighbours, derived {len(got)}")
            checked += 1
    return checked


def stdout_argv():
    return [os.path.basename(sys.executable), SELF] + sys.argv[1:]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--graph", required=True)
    ap.add_argument("--symmetrisation", default=None,
                    choices=["min", "max", "ged_fwd", "ged_rev"],
                    help="REQUIRED. Which symmetric relation the maze uses.")
    ap.add_argument("--K", type=int, default=None, help="legal-move threshold; default = graph's own")
    ap.add_argument("--rune", required=True, help="sweep start node")
    ap.add_argument("--cap", type=int, default=40)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--expect-graph-digest", default=None)
    ap.add_argument("--cell-spec", default=None, help="path to the frozen cell spec both boxes hash")
    ap.add_argument("--out-dir", default="probes")
    ap.add_argument("--dry-run", action="store_true",
                    help="no model: deterministic seeded walk, proves the plumbing only")
    ap.add_argument("--model", default=None)
    ap.add_argument("--seed-model", dest="seed_model", type=int, default=None)

    a = ap.parse_args()

    if not a.symmetrisation:
        die(EXIT_NO_SYMMETRISATION,
            "no --symmetrisation named. min/max/ged_fwd/ged_rev are four different graphs; "
            "the graph_digest alone does not pin the test, so this driver will not pick one for you.")

    raw, g, nodes, F = load_graph(a.graph)
    fsha = file_sha256(raw)
    gdig = graph_digest(nodes, F)
    K = a.K if a.K is not None else g["semantics"].get("K", 12)

    if a.rune not in nodes:
        die(EXIT_BAD_ARGS, f"start rune {a.rune!r} not in graph")

    cells_checked = check_derivation(g, nodes, F)

    if a.expect_graph_digest and a.expect_graph_digest != gdig:
        die(EXIT_DIGEST_MISMATCH,
            f"graph_digest {gdig} != expected {a.expect_graph_digest}")

    cell_sha = None
    if a.cell_spec:
        try:
            cell_sha = hashlib.sha256(open(a.cell_spec, "rb").read()).hexdigest()
        except OSError as e:
            die(EXIT_BAD_ARGS, f"cannot read cell spec: {e}")

    start_nb = neighbours(nodes, F, a.symmetrisation, K, a.rune)
    if not start_nb:
        die(EXIT_UNREACHABLE,
            f"{a.rune} has no legal move under symmetrisation={a.symmetrisation} K={K} "
            f"(the graph is disconnected from the start node)")

    tag = "DRYRUN_" if a.dry_run else ""
    slug = (f"{tag}{a.symmetrisation}-K{K}-{a.rune}-cap{a.cap}-seed{a.seed}"
            f"-{gdig[:8]}{'-cellspec' + cell_sha[:8] if cell_sha else ''}.json")
    out_path = os.path.join(a.out_dir, slug)
    if os.path.exists(out_path):
        die(EXIT_RECORD_EXISTS,
            f"{out_path} already exists; a record you did not take is not yours to overwrite")
    os.makedirs(a.out_dir, exist_ok=True)

    rng = random.Random(a.seed)
    cur = a.rune
    visited = [cur]
    moves = []
    blocked = not_an_action = give_up = 0
    tokens = []
    end_state = "cap"
    plies = 0
    while plies < a.cap:
        nb = neighbours(nodes, F, a.symmetrisation, K, cur)
        if not nb:
            blocked += 1
            end_state = "dead_end"
            break
        if a.dry_run:
            nxt = nb[rng.randrange(len(nb))]
        else:
            die(EXIT_BAD_ARGS, "model path not implemented yet: run --dry-run until a cell spec hash exists")
        moves.append({"ply": plies, "from": cur, "to": nxt, "legal_moves": len(nb)})
        tokens.append(None)
        cur = nxt
        visited.append(cur)
        plies += 1
    else:
        end_state = "cap"

    rec = {
        "schema": "labyrinth-run/1",
        "dry_run": bool(a.dry_run),
        "benchmark_row": not a.dry_run,
        "driver": {"path": SELF, "sha256": hashlib.sha256(open(SELF, "rb").read()).hexdigest()},
        "model": a.model if a.model else ("dry-run/none" if a.dry_run else None),
        "server_argv": None if a.dry_run else None,
        "server_binary_digest": None,
        "decoder_mode": "none" if a.dry_run else None,
        "seed": a.seed,
        "cap": a.cap,
        "graph": {
            "path": os.path.abspath(a.graph),
            "file_sha256": fsha,
            "graph_digest": gdig,
            "graph_digest_algorithm": "sha256(ged-v1 over nodes in file order + ged_fwd rows)",
            "nodes": len(nodes),
            "symmetrisation": a.symmetrisation,
            "K": K,
            "derivation_columns_checked": cells_checked,
            "edges_used": sum(len(neighbours(nodes, F, a.symmetrisation, K, x)) for x in nodes) // 2,
        },
        "cell_spec_sha256": cell_sha,
        "start_rune": a.rune,
        "end_rune": cur,
        "moves": moves,
        "plies": plies,
        "blocked": blocked,
        "not_an_action": not_an_action,
        "give_up": give_up,
        "ended": end_state != "cap" or plies >= a.cap,
        "end_state": end_state,
        "tokens_per_turn": tokens,
        "tokens_total": None if a.dry_run else sum(t for t in tokens if t),
        "visited_unique": len(set(visited)),
    }
    with open(out_path, "w") as fh:
        fh.write(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({"record": out_path, "end_state": end_state, "plies": plies,
                      "end_rune": cur, "unique_runes": len(set(visited)),
                      "graph_digest": gdig, "file_sha256": fsha,
                      "symmetrisation": a.symmetrisation, "K": K,
                      "derivation_columns_checked": cells_checked}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
