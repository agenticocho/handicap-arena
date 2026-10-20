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
    cannot silently change the test. DEFINITION, ged-v2 (the only accepted form):

        sha256( b"ged-v2\n"
                + for each node a in the file's "nodes" ARRAY, in ARRAY ORDER:
                      a.encode("utf-8") + b"\t"
                    + b",".join(str(int(ged_fwd[a][y])) for y in the SAME array order) + b"\n" )

    THE NODE ORDER IS THE "nodes" ARRAY. NOT the insertion order of the ged_fwd object,
    not sorted order, not any order a JSON serialiser happens to emit. ged-v1 said "file
    order" and that was ambiguous: the file carries TWO orders, the "nodes" array (the
    declared order) and the ged_fwd key order (an artefact of json.dump(sort_keys=True),
    which coincides with alphabetical). Two boxes computed two values under the v1 label
    (798db390… over the array, c7f5eecb… over the keys), so v1 is RETIRED, not adopted.
    Only the array order is content-stable: reverse the ged_fwd keys without changing a
    single distance and the key-order digest moves to 36df4b8e…, while the array-order
    digest does not move at all.

    The file's byte digest is recorded separately (file_sha256) as transport evidence.
    Neither pins the test alone: two boxes can hold byte-identical graphs and derive
    different neighbour sets if symmetrisation or K differ. All of it is recorded.
    Run --self-test for the 2-node test vector; a definition without a test vector is a
    description, and a description is what just cost a day.

EDGE COUNTS (record.graph.edges_used and the basis beside it)
    The record carries the edge count of the relation the run ACTUALLY uses, never a count
    derived from an assumption about symmetry:
        edges_used              arcs under ged_fwd/ged_rev, undirected pairs under min/max
        edges_used_basis        the literal basis of that number ("arcs" / "undirected_pairs")
        edges_directed          sum(out-degree), always
        edges_undirected_pairs  unordered pairs legal in at least one direction
        edges_one_way           pairs legal in exactly one direction (0 iff symmetric)
    On the pinned graph at K=12: min pairs 198 (arcs 396, one-way 0); max pairs 138 (arcs 276,
    one-way 0); ged_fwd and ged_rev 336 arcs, 198 pairs, 60 one-way. The earlier reading took
    sum(out-degree)//2 for every symmetrisation, which reported 168 for a relation with 336
    arcs and no undirected edges. min/max numbers are unchanged by that correction, so schema
    labyrinth-run/2 still describes every row it described before.

ADMISSION (refuses BEFORE the first turn, with a distinguishable exit code)

    The checks that are properties of the ARGUMENTS ALONE run first -- before the graph is
    read, before a slug is computed, before os.makedirs -- because a dispatch that can never
    write a record must never get far enough to name one, or occupy one:
      cap < 1                     exit 2  a cell needs a ply; cap < 1 never enters the walk,
                                          so it can only produce a record of nothing (0 moves,
                                          tokens_total 0) that still claims benchmark_row
      no --dry-run                exit 2  no non-dry dispatch is implemented, with or without
                                          --model. This is the admission check; the in-walk
                                          refusal is an assertion that must stay unreachable
      --model with --dry-run      exit 2  a dry run consults no model, so recording one states
                                          a basis the process never had. One guard closes this
                                          and the rule above, not two.
      --seed-model                exit 2  accepted by argparse and read by NOTHING: no dispatch
                                          consumes it, so a row recorded under it would carry
                                          seed 0 and no model-seed field, and its slug would be
                                          identical to the dispatch that omitted the flag -- the
                                          second honest run for that cell is then refused as a
                                          duplicate (exit 7). Refused on PRESENCE, not on a
                                          truthy value: --seed-model 0 is a value too.
      --out-dir ""                exit 2  an empty path names no directory. Without the check the
                                          dispatch reaches os.makedirs and dies with exit 1 and a
                                          traceback -- an unmapped code for an argument defect.
                                          (--out-dir naming an existing FILE is still an I/O
                                          error and still unmapped: that one is a filesystem fact,
                                          not an argument, and a code for it is a two-box
                                          decision rather than a patch.)
    The class behind --seed-model, closed rather than patched again: every dest the parser
    accepts must be either in CONSUMED_DESTS or in UNIMPLEMENTED_ARGS, and --self-test fails if
    one is in neither. A flag added tomorrow that nothing reads fails the suite instead of
    landing in a record as a value the run contradicts.
    Consequence, stated rather than discovered later: a bad ARGUMENT now outranks bad I/O.
    `--cap 0` with a malformed or missing graph is exit 2, not 3. With no --symmetrisation it
    is still 4, because that check precedes admission.

    2  bad arguments
    3  graph file unreadable / malformed
    4  symmetrisation not named                <- the whole point: no silent default
    5  graph_digest does not match --expect-graph-digest
    6  derivation check failed: at K=12 the derived adjacency disagrees with the
       shipped adjacency_*_K column, so this file is not internally consistent
    7  output path already exists and this record did not take it
       DRY-RUN ONLY until a model path exists: every non-dry dispatch is refused at
       admission, so no other dispatch reaches the slug this check guards. The check stays
       as the guard on the one dispatch that can actually write.
    8  graph disconnected from --rune (no legal move at start)

    Exit 0 on a completed record. --dry-run exits 0 too, but writes a record marked
    dry_run=true and refuses to call it a benchmark row.

RECORD
    one JSON per cell in probes/, carrying: model, server_argv, server_binary_digest,
    decoder mode, seed, cap, graph identity, every move with its legal set size,
    blocked / not_an_action / give_up counts, per-turn tokens, ended, end_state.

    THE COUNT BASIS. visited_unique counts POSITIONS, not names: this graph's GED cannot
    separate 24 names into 24 objects, it separates them into 21 (Ansuz/Wunjo/Laguz and
    Perthro/Berkano have identical ged_fwd rows AND columns). A row therefore carries
    visited_unique (positions), visited_names, and visited_count_basis, and the graph object
    carries positions + alias_groups. Counting names on one box and positions on the other
    would differ by up to 3 on the same walk — i.e. by the alias convention rather than by
    the model, in the one field a cross-machine comparison reads.
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
EXIT_SELF_TEST_FAIL = 9

SELF = os.path.abspath(__file__)

# Arguments the parser accepts whose value no dispatch reads. Every one of them must be REFUSED at
# admission while that is true, because a dispatch that types it gets a record contradicting it --
# and here the contradiction is not cosmetic: the flag is absent from the slug too, so the dispatch
# that sets it and the dispatch that omits it collide on one output path and the second is refused
# as a duplicate.
UNIMPLEMENTED_ARGS = {
    "seed_model": "--seed-model is parsed and read by no dispatch: a row under it would record "
                  "seed 0 with no model-seed field, and its slug is identical to the dispatch that "
                  "omits the flag, so the second honest run for that cell exits 7. Refused until a "
                  "model path reads it.",
}

# Every dest the cell semantics actually consume. Anything outside this set must be declared in
# UNIMPLEMENTED_ARGS; parser_audit() fails --self-test otherwise, so a flag nobody reads cannot
# reach a record by being added and forgotten.
CONSUMED_DESTS = {
    "graph", "symmetrisation", "K", "rune", "cap", "seed", "expect_graph_digest",
    "cell_spec", "out_dir", "dry_run", "model", "self_test", "print_graph_digest",
}


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
    """ged-v2. `nodes` MUST be the graph's own "nodes" array, in array order.

    Anything else is a different number under the same name, which is the defect this
    function exists to prevent. Callers pass load_graph()'s nodes; nothing else may.
    """
    h = hashlib.sha256()
    h.update(b"ged-v2\n")
    for a in nodes:
        h.update(a.encode("utf-8") + b"\t")
        h.update(",".join(str(int(F[a][y])) for y in nodes).encode("utf-8") + b"\n")
    return h.hexdigest()


# The test vector. Two nodes, one asymmetric pair, no graph file needed: if a definition
# cannot reproduce THIS, the argument about the 24-node file never needed to happen.
SELF_TEST_GRAPH = {"nodes": ["A", "B"],
                   "ged_fwd": {"A": {"A": 0, "B": 3}, "B": {"A": 9, "B": 0}}}
SELF_TEST_BYTES = b'{"ged_fwd":{"A":{"A":0,"B":3},"B":{"A":9,"B":0}},"nodes":["A","B"]}'
SELF_TEST_FILE_SHA = "f700d57a5894fc83e82af4494040b21dc92943d57674c8831b1262707f2535c8"
SELF_TEST_GRAPH_DIGEST = "56a2b3e4ebcf0f7ad0e41c72950c7b9e5dfe00a7d69b3acd2856918dcdeb8714"

# The EDGE-COUNT test vector, and the reason it exists: the field it guards was wrong under
# ged_fwd/ged_rev for a whole evening because the only fixture in the suite was symmetric at
# K=12, where sum(out-degree)//2 and the true count agree. Three nodes, distances 3 and 20
# against K=12, so exactly two pairs are legal in ONE direction only:
#     min      arcs 4, pairs 2, one-way 0  (min is symmetric by construction)
#     max      arcs 0, pairs 0, one-way 0  (nothing within K=12)
#     ged_fwd  arcs 2, pairs 2, one-way 2  <- halving reports 1 here; the relation has 2 arcs
#     ged_rev  arcs 2, pairs 2, one-way 2
EDGE_TEST_GRAPH = {"nodes": ["A", "B", "C"],
                   "ged_fwd": {"A": {"A": 0, "B": 3, "C": 20},
                               "B": {"A": 20, "B": 0, "C": 3},
                               "C": {"A": 20, "B": 20, "C": 0}}}
EDGE_TEST_K = 12


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


def edge_counts(nodes, F, sym, K):
    """Count the edges of the relation actually used, and name the basis beside the number.

    A DIRECTED symmetrisation is not a symmetric relation. Under min/max every legal pair is
    legal both ways, so the relation's edge count is the number of unordered pairs and equals
    sum(out-degree) // 2. Under ged_fwd/ged_rev that halving is wrong: this graph has 336 legal
    arcs under each, 198 pairs legal in at least one direction, and 60 pairs legal in exactly
    one direction -- so the old //2 reported 168 for a relation with no undirected edges.
    Recorded per relation, never by assumption:
        edges_used              the relation's own edge count: arcs for a directed
                                symmetrisation, undirected pairs for a symmetric one
        edges_used_basis        the literal basis of that number, beside it
        edges_directed          sum(out-degree) always (== 2 x pairs when symmetric)
        edges_undirected_pairs  unordered pairs legal in at least one direction
        edges_one_way           pairs legal in exactly one direction (0 iff symmetric)
    """
    outs = {a: neighbours(nodes, F, sym, K, a) for a in nodes}
    directed = sum(len(v) for v in outs.values())
    one_way = pairs = 0
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            ab, ba = b in outs[a], a in outs[b]
            if ab != ba:
                one_way += 1
                pairs += 1
            elif ab:
                pairs += 1
    directed_sym = sym in ("ged_fwd", "ged_rev")
    return {"edges_used": directed if directed_sym else pairs,
            "edges_used_basis": "arcs" if directed_sym else "undirected_pairs",
            "edges_directed": directed,
            "edges_undirected_pairs": pairs,
            "edges_one_way": one_way}


def positions(nodes, F):
    """One position = the names the GED cannot tell apart.

    A position is a set of names with byte-identical ged_fwd ROWS AND COLUMNS — the graph's own
    criterion for d(a,b) == 0 in every direction, which is why the grouping does not depend on
    which symmetrisation the cell names (identical under min, max, ged_fwd and ged_rev). Here
    24 names occupy 21 positions: Ansuz/Wunjo/Laguz and Perthro/Berkano.
    """
    key = {a: (tuple(int(F[a][y]) for y in nodes), tuple(int(F[y][a]) for y in nodes)) for a in nodes}
    groups = {}
    for a in nodes:
        groups.setdefault(key[a], []).append(a)
    return list(groups.values())


def position_index(nodes, F):
    """(name -> position id, list of positions in nodes-array order)."""
    groups = positions(nodes, F)
    return {a: i for i, grp in enumerate(groups) for a in grp}, groups


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


def self_test():
    """Reproduce the 2-node test vector from the definition alone. Exit 0 iff both match."""
    fx = SELF_TEST_GRAPH
    fsha = hashlib.sha256(SELF_TEST_BYTES).hexdigest()
    gdig = graph_digest(fx["nodes"], fx["ged_fwd"])

    E, GE = EDGE_TEST_GRAPH["nodes"], EDGE_TEST_GRAPH["ged_fwd"]
    got = {s: edge_counts(E, GE, s, EDGE_TEST_K) for s in ("min", "max", "ged_fwd", "ged_rev")}
    want = {"ged_fwd": {"edges_used": 2, "edges_used_basis": "arcs", "edges_directed": 2,
                        "edges_undirected_pairs": 2, "edges_one_way": 2},
            "ged_rev": {"edges_used": 2, "edges_used_basis": "arcs", "edges_directed": 2,
                        "edges_undirected_pairs": 2, "edges_one_way": 2},
            "min": {"edges_used": 2, "edges_used_basis": "undirected_pairs", "edges_directed": 4,
                    "edges_undirected_pairs": 2, "edges_one_way": 0},
            "max": {"edges_used": 0, "edges_used_basis": "undirected_pairs", "edges_directed": 0,
                    "edges_undirected_pairs": 0, "edges_one_way": 0}}
    halving_would_report = got["ged_fwd"]["edges_directed"] // 2
    eok = (got == want and halving_would_report != got["ged_fwd"]["edges_used"])

    aok, admit_rows = admit_test()
    pok, parser_row = parser_audit()
    ok = (fsha == SELF_TEST_FILE_SHA and gdig == SELF_TEST_GRAPH_DIGEST and eok and aok and pok)
    print(json.dumps({"self_test": "ged-v2",
                      "fixture_bytes": SELF_TEST_BYTES.decode(),
                      "preimage": (b"ged-v2\n" + b"".join(
                          a.encode() + b"\t" +
                          ",".join(str(int(fx["ged_fwd"][a][y])) for y in fx["nodes"]).encode() + b"\n"
                          for a in fx["nodes"])).decode().replace("\n", "\\n").replace("\t", "\\t"),
                      "file_sha256": fsha, "expect_file_sha256": SELF_TEST_FILE_SHA,
                      "graph_digest": gdig, "expect_graph_digest": SELF_TEST_GRAPH_DIGEST,
                      "edge_counts": got, "expect_edge_counts": want,
                      "edge_counts_pass": eok,
                      "admission": admit_rows, "admission_pass": aok,
                      "parser_audit": parser_row, "parser_pass": pok,
                      "pass": ok}, indent=1))
    return 0 if ok else EXIT_SELF_TEST_FAIL


ADMIT_TEST_NODES = ["N%02d" % i for i in range(24)]


def admit_test():
    """End-to-end admission vectors: every refusal must fire on the path that writes NO record,
    and the harness must be shown to reach the path that DOES write one.

    The defect these guard, in the shape it actually took: the model refusal lived inside the
    walk, so `--cap 0` -- a reachable argument -- never entered the loop body, never reached the
    refusal, and wrote a record with benchmark_row=true, model="dummy", plies=0, moves=[],
    tokens_total=0. The only admission fixture in the suite exercised a cell that runs a ply, so
    a cell that runs none slipped past every check. Hence the control case: without one, this
    test could not tell "the refusal fired" from "nothing ever runs".

    Then the same defect from the other direction: `if model and not dry_run` refused only a
    dispatch that NAMED a model, so the dispatch naming neither --model nor --dry-run walked
    past admission, computed a non-dry slug, created the out-dir, and died inside the walk --
    exit 7 if that slug already existed. A guard whose condition is narrower than its reason has
    a reachable argument on the side it does not cover. Hence `no_model_no_dry`, and hence the
    vector checks the out-dir does not exist as well as the exit code: a refusal that still
    creates the directory has already done the thing admission exists to prevent.
    """
    import tempfile

    nodes = ADMIT_TEST_NODES
    F = {a: {b: (0 if a == b else 1) for b in nodes} for a in nodes}
    root = tempfile.mkdtemp(prefix="labyrinth-admit-")
    gp = os.path.join(root, "g.json")
    with open(gp, "w") as fh:
        json.dump({"nodes": nodes, "ged_fwd": F, "semantics": {"K": 1}}, fh)

    def run(extra, out):
        import contextlib
        import io
        saved = sys.argv
        sys.argv = [SELF, "--graph", gp, "--symmetrisation", "min", "--rune", nodes[0],
                    "--seed", "0", "--out-dir", os.path.join(root, out)] + extra
        said, out_buf = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(said):
                return main(), said.getvalue().strip()
        except SystemExit as e:
            return e.code, said.getvalue().strip()
        finally:
            sys.argv = saved

    def written(out):
        d = os.path.join(root, out)
        return sorted(os.listdir(d)) if os.path.isdir(d) else []

    ok = True
    got = []
    for name, extra, want in (("cap0_model", ["--cap", "0", "--model", "dummy"], EXIT_BAD_ARGS),
                              ("capneg_model", ["--cap", "-1", "--model", "dummy"], EXIT_BAD_ARGS),
                              ("cap0_dry", ["--cap", "0", "--dry-run"], EXIT_BAD_ARGS),
                              ("model_cap40", ["--cap", "40", "--model", "dummy"], EXIT_BAD_ARGS),
                              # neither --model nor --dry-run: the direction the old condition
                              # left uncovered
                              ("no_model_no_dry", [], EXIT_BAD_ARGS),
                              # a dry run that names a model it never consults
                              ("dry_with_model", ["--cap", "2", "--dry-run", "--model", "dummy"],
                               EXIT_BAD_ARGS),
                              # the same flag given an empty value: `if model:` is a truthiness
                              # test on a string, so "" slipped through and wrote a row. The guard
                              # is the PRESENCE of the argument, not its content.
                              ("dry_empty_model", ["--cap", "2", "--dry-run", "--model", ""],
                               EXIT_BAD_ARGS),
                              # the argument the per-flag guards did not know about: accepted by
                              # argparse, read by no dispatch. Presence is the defect, so 0 is
                              # refused exactly like 7 -- `if seed_model:` would have admitted it.
                              ("seed_model_7", ["--cap", "2", "--dry-run", "--seed-model", "7"],
                               EXIT_BAD_ARGS),
                              ("seed_model_0", ["--cap", "2", "--dry-run", "--seed-model", "0"],
                               EXIT_BAD_ARGS),
                              # an argument that names nothing: without this the dispatch reaches
                              # os.makedirs and exits 1 with a traceback, an unmapped code
                              ("empty_out_dir", ["--cap", "2", "--dry-run", "--out-dir", ""],
                               EXIT_BAD_ARGS)):
        code, said = run(extra, name)
        files = written(name)
        made_dir = os.path.isdir(os.path.join(root, name))
        good = (code == want and not files and not made_dir)
        ok = ok and good
        got.append({"case": name, "exit": code, "expected_exit": want,
                    "records_written": files, "out_dir_created": made_dir,
                    "said": said, "pass": good})

    ctrl, said = run(["--cap", "2", "--dry-run"], "control")
    cfiles = written("control")
    cok = False
    if ctrl == 0 and len(cfiles) == 1:
        rec = json.load(open(os.path.join(root, "control", cfiles[0])))
        cok = (rec["plies"] == 2 and rec["dry_run"] is True and rec["benchmark_row"] is False
               and rec["model"] == "dry-run/none")
    ok = ok and cok
    got.append({"case": "control_cap2_dry", "exit": ctrl, "expected_exit": 0,
                "records_written": cfiles, "said": said, "pass": cok})
    return ok, got


def admission_refusal(cap, model, dry_run, seed_model=None, out_dir=None):
    """ADMISSION: refusals that are properties of the ARGUMENTS alone.

    None of these may live in the walk, and none may depend on the graph loading, the digest
    matching, or the out-dir's contents: a dispatch that cannot write a record has no business
    computing that record's slug or creating its directory, and a fabricated row that DOES get
    written then occupies the slug and turns the honest run for that cell into exit 7.

    The condition is the ARGUMENT, not the out-dir. `not dry_run` refuses every dispatch that
    would call itself a benchmark row, because no model path exists to stand behind one -- and
    that includes the dispatch that names no --model at all, which is the direction the older
    `model and not dry_run` guard was walked past from. `model` is refused under --dry-run too:
    a dry run consults no model, so a row naming one states a basis the process never had.

    When a model path lands, delete the `not dry_run` branch and keep the rest; the bound on
    `cap` stays regardless.
    """
    if cap < 1:
        return (EXIT_BAD_ARGS,
                f"--cap {cap}: a cell needs at least one ply, and cap < 1 never enters the walk, "
                f"so it can only produce a record of nothing (0 moves, tokens_total 0) that still "
                f"claims benchmark_row")
    if not dry_run:
        return (EXIT_BAD_ARGS,
                "no non-dry dispatch exists yet: run --dry-run until a model path is implemented "
                "and a cell spec hash exists. Refused at admission, before the slug is computed "
                "and before the out-dir is created -- not inside the walk.")
    if model is not None:
        return (EXIT_BAD_ARGS,
                f"--dry-run consults no model, so it will not record one: got --model {model!r}; "
                f"a dry-run row's model field is 'dry-run/none'")
    if seed_model is not None:
        # Presence, not truthiness: --seed-model 0 sets the model seed to zero, which is a value
        # the record neither carries nor distinguishes. Same test as `model is not None`, for the
        # same reason -- the argument's EXISTENCE is the defect, not its content.
        return (EXIT_BAD_ARGS, f"--seed-model {seed_model}: {UNIMPLEMENTED_ARGS['seed_model']}")
    if out_dir == "":
        # An empty path names no directory. Without this the dispatch reaches os.makedirs and dies
        # on FileNotFoundError with exit 1 and a traceback -- an unmapped code for a defect that is
        # a property of the argument alone, which is this function's whole remit.
        return (EXIT_BAD_ARGS,
                "--out-dir '': an empty path names no directory, so the record has nowhere to go. "
                "Refused at admission rather than raised out of os.makedirs.")
    return None


def build_parser():
    """The one parser definition. main() and parser_audit() both use THIS object, so the audit
    cannot drift from the dispatch surface by describing a parser nobody runs."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--graph", default=None)
    ap.add_argument("--symmetrisation", default=None,
                    choices=["min", "max", "ged_fwd", "ged_rev"],
                    help="REQUIRED to run a cell. Which symmetric relation the maze uses.")
    ap.add_argument("--K", type=int, default=None, help="legal-move threshold; default = graph's own")
    ap.add_argument("--rune", default=None, help="sweep start node (required to run a cell)")
    ap.add_argument("--cap", type=int, default=40)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--expect-graph-digest", default=None)
    ap.add_argument("--cell-spec", default=None, help="path to the frozen cell spec both boxes hash")
    ap.add_argument("--out-dir", default="probes")
    ap.add_argument("--dry-run", action="store_true",
                    help="no model: deterministic seeded walk, proves the plumbing only")
    ap.add_argument("--model", default=None)
    ap.add_argument("--seed-model", dest="seed_model", type=int, default=None)
    ap.add_argument("--self-test", dest="self_test", action="store_true",
                    help="reproduce the 2-node ged-v2 test vector and exit (no --graph needed)")
    ap.add_argument("--print-graph-digest", dest="print_graph_digest", action="store_true",
                    help="print file_sha256 + graph_digest for --graph and exit. NOT a cell: "
                         "needs no symmetrisation, because it runs no moves.")
    return ap


def parser_audit():
    """Every dest the parser accepts is either consumed or declared unimplemented.

    This is the class, not another instance. The two defects found by hand tonight -- `--model ""`
    (a guard keyed on truthiness) and `--seed-model 7` (a flag nothing reads) -- are both "the
    argument and the record disagree". A per-flag guard closes one argument each time; auditing the
    parser's whole dest list closes the category, because a new flag cannot be added without either
    being read or being refused, and the audit is what fails when it is neither.
    """
    dests = {act.dest for act in build_parser()._actions if act.dest != "help"}
    unread = dests - CONSUMED_DESTS
    missing = CONSUMED_DESTS - dests
    undeclared = unread - set(UNIMPLEMENTED_ARGS)
    ok = not undeclared and not missing
    return ok, {"dests": sorted(dests), "consumed": sorted(CONSUMED_DESTS),
                "declared_unimplemented": sorted(UNIMPLEMENTED_ARGS),
                "accepted_and_undeclared": sorted(undeclared),
                "consumed_but_not_a_dest": sorted(missing), "pass": ok}


def main():
    a = build_parser().parse_args()

    if a.self_test:
        return self_test()

    if not a.graph:
        die(EXIT_BAD_ARGS, "--graph is required (except with --self-test)")

    if a.print_graph_digest:
        raw, g, nodes, F = load_graph(a.graph)
        print(json.dumps({"definition": "ged-v2",
                          "node_order": "nodes array",
                          "nodes": nodes,
                          "file_sha256": file_sha256(raw),
                          "graph_digest": graph_digest(nodes, F)}, indent=1))
        return 0

    if not a.symmetrisation:
        die(EXIT_NO_SYMMETRISATION,
            "no --symmetrisation named. min/max/ged_fwd/ged_rev are four different graphs; "
            "the graph_digest alone does not pin the test, so this driver will not pick one for you.")

    if not a.rune:
        die(EXIT_BAD_ARGS, "--rune is required to run a cell")

    # ADMISSION, before the graph is loaded, before the slug is computed, before os.makedirs:
    # a dispatch that cannot write a record must never get far enough to name one.
    refusal = admission_refusal(a.cap, a.model, a.dry_run, a.seed_model, a.out_dir)
    if refusal:
        die(*refusal)

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

    # Counted once, from the relation the run actually uses, and carried into the record with
    # its basis beside it (edges_used_basis) -- not derived from a symmetry assumption.
    ec = edge_counts(nodes, F, a.symmetrisation, K)

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
            # Unreachable by argument: admission_refusal() refuses every non-dry dispatch. Kept as
            # an assertion so a future model path cannot fall through to a row with no model turn.
            die(EXIT_BAD_ARGS, "internal: non-dry dispatch reached the walk; admission must refuse it")
        moves.append({"ply": plies, "from": cur, "to": nxt, "legal_moves": len(nb)})
        tokens.append(None)
        cur = nxt
        visited.append(cur)
        plies += 1
    else:
        end_state = "cap"

    pos_of, alias_all = position_index(nodes, F)
    alias_multi = [grp for grp in alias_all if len(grp) > 1]
    visited_names = len(set(visited))
    visited_positions = len({pos_of[a] for a in visited})

    rec = {
        "schema": "labyrinth-run/2",
        "dry_run": bool(a.dry_run),
        "benchmark_row": not a.dry_run,
        "driver": {"path": SELF, "sha256": hashlib.sha256(open(SELF, "rb").read()).hexdigest()},
        # a.model is unreachable: admission refuses --model under --dry-run and refuses every
        # non-dry dispatch outright. Kept as a ternary rather than the argument so a future model
        # path cannot restore a model name here without editing admission as well.
        "model": "dry-run/none" if a.dry_run else None,
        "server_argv": None if a.dry_run else None,
        "server_binary_digest": None,
        "decoder_mode": "none" if a.dry_run else None,
        "seed": a.seed,
        "cap": a.cap,
        "graph": {
            "path": os.path.abspath(a.graph),
            "file_sha256": fsha,
            "graph_digest": gdig,
            "graph_digest_algorithm": "sha256(ged-v2: header 'ged-v2\\n', then for each node a in the "
                                      "file's 'nodes' ARRAY in array order: a + '\\t' + "
                                      "','.join(str(int(ged_fwd[a][y])) for y in array order) + '\\n')",
            "graph_digest_node_order": "nodes array (NOT ged_fwd key order)",

            "nodes": len(nodes),
            "positions": len(alias_all),
            "alias_groups": alias_multi,
            "symmetrisation": a.symmetrisation,
            "K": K,
            "derivation_columns_checked": cells_checked,
            **ec,
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
        "visited_unique": visited_positions,
        "visited_names": visited_names,
        "visited_count_basis": "positions",
    }
    with open(out_path, "w") as fh:
        fh.write(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({"record": out_path, "end_state": end_state, "plies": plies,
                      "end_rune": cur, "unique_positions": visited_positions,
                      "unique_names": visited_names,
                      "graph_digest": gdig, "file_sha256": fsha,
                      "symmetrisation": a.symmetrisation, "K": K,
                      "derivation_columns_checked": cells_checked,
                      "edges_used": ec["edges_used"], "edges_used_basis": ec["edges_used_basis"],
                      "edges_directed": ec["edges_directed"], "edges_one_way": ec["edges_one_way"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
