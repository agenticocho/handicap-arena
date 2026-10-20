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

THE CANONICAL NODE ORDER IS CHECKED BEFORE THE DIGEST IS COMPUTED (exit 13)
    graph_digest() hashes the nodes array IN WHATEVER ORDER IT IS GIVEN, so the order is part of
    the declaration and cannot be recovered from the number it produces. Measured on the arrived
    file: the same distances with the array in canonical order hash to 596255d9..., and with the
    array sorted alphabetically to fa26e89e.... Both are well-formed ged-v2 digests of the right
    distances; only one of them is about the declared test. Exit 5 cannot catch that, because the
    number it compares is computed after the order has already been lost. So:
        CANONICAL_NODES          the elder-Futhark order the generator carries (RUNE_NAMES)
        CANONICAL_NODES_SHA256   sha256("\n".join(nodes) + "\n") over that order
                                 = 49fa1fb94b71bb934323b626b86ec9f76ff1a646d3a03a40ebc1eac98378cc94
                                 FIXED BY THE RUNE SET, not by a matrix: regeneration moves
                                 distances and re-serialises bytes, never these 24 names in this
                                 order, so the guard survives the very repair it is watching.
        exit 13                  the array is not that order (or --expect-nodes-sha256 names a
                                 different declaration). Refused BEFORE graph_digest() runs, and
                                 the refusal says the digest was NOT computed: a number produced
                                 here would pin the wrong declaration and look correct doing it.
    --expect-nodes-sha256 is compared on the AUDIT path too, so --print-graph-digest cannot print
    a "verified" digest for a wrongly-ordered file.

THE PIN: PIN THE GRAPH DIGEST, NEVER THE FILE HASH
    Measured on this box on the arrived file: repairing `semantics` from a string to an object
    carrying K:12, and regenerating the two adjacency columns, leaves graph_digest at 596255d9...
    while file_sha256 moves off ea33eedc.... A spec pinned to the file hash would therefore die on
    exactly the repair it asks for. So:
        graph_digest        the PINNED IDENTITY of the test. It is what --expect-graph-digest
                            compares, what a row carries in `pinned_identity`, and what every
                            refusal message about the graph names.
        file_sha256         a READING about the bytes (transport evidence, "did this file change
                            in transit?"). Never the identity of the test, never a pin.
    Two boxes can hold byte-identical graphs and run different tests (different symmetrisation or
    K); one graph can arrive in two serialisations. The digest is the only field that survives
    both, so it is the only field a spec may pin.

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

    THE ARM TRAVELS WITH THE COUNT. edges_used is arm-dependent -- measured at K=12 on the arrived
    regeneration: min 196, max 139, ged_fwd/ged_rev 335 arcs (on the pre-correction graph the same
    field read 198 / 138 / 336) -- so a row carries edges_used_arm beside edges_used, and an
    edges_used_statement string that cannot be quoted without its basis:
        edges_used=196 (basis=undirected_pairs, arm=min)
    A count published without its arm is a value without its basis, and the two arms differ by 57
    on this graph: enough to be read as a difference between machines when it is a difference
    between derivations.

ADMISSION (refuses BEFORE the first turn, with a distinguishable exit code)

    The checks that are properties of the ARGUMENTS ALONE run first -- before the graph is
    read, before a slug is computed, before os.makedirs -- because a dispatch that can never
    write a record must never get far enough to name one, or occupy one:
      cap < 1                     exit 2  a cell needs a ply; cap < 1 never enters the walk,
                                          so it can only produce a record of nothing (0 moves,
                                          tokens_total 0) that still claims benchmark_row
      no --model, no --dry-run    exit 2  a non-dry dispatch is ONE MODEL'S ANSWER per ply and
                                          there is no other instrument. (Was the blanket
                                          `not dry_run` refusal until the model path landed; the
                                          thing refused -- a row with no model behind it -- is
                                          the same.)
      --model with --dry-run      exit 2  a dry run consults no model, so recording one states
                                          a basis the process never had.
      --model-identity with
      --dry-run                   exit 2  same rule: the card exists only to say which weights
                                          answered, and none did.
      --seed-model (dry)          exit 2  a dry run has no model seed. CONSUMED since the model
                                          path landed (sent as the request seed, recorded in the
                                          row and in the slug); refused under --dry-run on
                                          PRESENCE, not truthiness -- 0 is a value too.
      --out-dir ""                exit 2  an empty path names no directory. Without the check the
                                          dispatch reaches os.makedirs and dies with exit 1 and a
                                          traceback -- an unmapped code for an argument defect.
                                          (--out-dir naming an existing FILE, or a path with a file
                                          in its middle, or a directory that refuses a write, is a
                                          filesystem fact rather than an argument fact: it is
                                          ADMITTED and then refused at 10, after the slug is named.
                                          See OUT-DIR: EXIT 10.)
      no --model-identity (live)  exit 11 the weights that answered cannot be stated: spec §3
                                          wants model id + quant + argv + binary digest and the
                                          api id names no quant. A row that cannot say which
                                          weights answered is not a benchmark row.
    The class behind --seed-model, closed rather than patched again: every dest the parser
    accepts must be either in CONSUMED_DESTS or in UNIMPLEMENTED_ARGS, and --self-test fails if
    one is in neither. A flag added tomorrow that nothing reads fails the suite instead of
    landing in a record as a value the run contradicts. UNIMPLEMENTED_ARGS is EMPTY now, and the
    audit still runs: an empty dict is a passing audit, not an absent one.
    Consequence, stated rather than discovered later: a bad ARGUMENT now outranks bad I/O.
    `--cap 0` with a malformed or missing graph is exit 2, not 3. With no --symmetrisation it
    is still 4, because that check precedes admission.

    ONE VALIDATION PATH -- why --print-graph-digest and a dispatch cannot disagree
    A predicate that says "this file is the test" must fail wherever a dispatch fails, or it
    certifies what admission refuses. It did. Measured on the arrived file before this revision:
    `--print-graph-digest` exited 0 and printed graph_digest 596255d9..., while the same file in a
    dispatch died at exit 1 -- an UNDECLARED code, an AttributeError out of
    `g["semantics"].get("K", 12)` because "semantics" was a STRING -- and that digest was then
    quoted by all three parties as though it certified the file. validate_graph() is now the only
    place a graph is accepted and BOTH paths call it, in this order:
        structural (3) -> canonical node order (13) -> start rune (2, dispatch only)
        -> derivation columns (6) -> digest (5)
    No graph defect can reach a traceback: every one lands on a numbered exit, and --self-test runs
    each malformed fixture down both paths and requires the SAME exit from each.

    2  bad arguments
    3  graph file unreadable / malformed
    4  symmetrisation not named                <- the whole point: no silent default
    5  graph_digest does not match --expect-graph-digest
    6  derivation check failed: at K=12 the derived adjacency disagrees with the
       shipped adjacency_*_K column, so this file is not internally consistent
    7  output path already exists and this record did not take it
       THE ONE DISPATCH THAT CAN WRITE IS NOW REACHABLE: a live run with a verified identity
       writes to (and therefore guards) a slug. A repeated cell is exit 7, measured, not asserted.
       The slug is CLAIMED, not overwritten: see PUBLISHING below. Exit 7 survives in every
       publish tier -- the prohibition is a rule; only the exclusivity is a capability.
    8  graph disconnected from --rune (no legal move at start)
   10  the out-dir cannot hold a record (see OUT-DIR: EXIT 10 below)
   11  the model path cannot state its identity (see THE MODEL PATH below)
   12  the model path cannot complete (see THE MODEL PATH below)
   13  the nodes array is not the canonical elder-Futhark order, or --expect-nodes-sha256 names a
       different declaration. A DECLARATION defect, distinct from 3 (this is not a graph) and from
       6 (this graph contradicts itself): the file loads and its distances are the right ones, but
       it declares them under the wrong order -- so the fix is to reorder the array, not to
       regenerate the bytes. Checked BEFORE graph_digest() is computed, and the refusal says so.

   Exit 0 on a completed record. --dry-run exits 0 too, but writes a record marked
    dry_run=true and refuses to call it a benchmark row.

THE MODEL PATH (--model): proposal -> parse -> legal-move check -> per-turn tokens -> record
    A non-dry dispatch is ONE MODEL'S ANSWER PER PLY. `--model` names the API id; because the api id
    carries NO quant, the row's weight identity comes from `--model-identity CARD`, a JSON card with
    the four fields spec §3 makes required and none substitutable:
        api_model_id            must equal --model
        quant                   e.g. "Q4_K_M"; must appear in the gguf name the argv loads
        server_argv             the argv ARRAY of the server that answers. A string is refused: it
                                cannot be checked, and an unchecked argv is a claim, not evidence.
        server_binary_digest    sha256 of that binary, RECOMPUTED here, never trusted as given.
    A lease-wrapped server (gpu-lease.sh ... -- llama-server ...) may also carry an optional
    `server_binary`: the binary further down the argv that actually answers. Without it argv[0] is the
    subject, and an argv that does not launch the digest's subject is refused either way.
    The driver additionally refuses to run if the api id is not served by --base-url, and checks on
    EVERY turn that the weights the server reports answering are the file the argv names -- a swap
    mid-cell is the one way a row can quietly stop being about the model it names.

    THE READ GRAMMAR (this paragraph is the whole rule; nothing is inferred from a prompt):
        exactly one rune name, alone on the first non-empty line, case-insensitive, surrounding
        quotes/backticks stripped          -> a proposal; the legal set decides moved vs blocked
        one of the eight abstention tokens  -> give_up; the cell ENDS and the row says so
        anything else -- prose, punctuation, a trailing full stop, two names, fences, JSON --
        -> not_an_action. NEVER truncated, and never read for a move.
    The prompt names the rune ALPHABET (24 invented names are not derivable from anything) and NEVER
    the legal set: a position that arrives with its candidates listed is a menu, and choosing from a
    menu measures the menu. Its text and its digest travel in every row.

    per-turn tokens are the server's own usage.completion_tokens for that turn; tokens_total is their
    sum. A turn with no usage block is REFUSED, not recorded as 0 -- a row that cannot say what it
    spent is not a measurement.

    OUT-DIR: EXIT 10 (EXIT_OUT_DIR_UNUSABLE)
    An out-dir that cannot hold a record used to die as a raw traceback at exit 1, which a second box
    cannot key on. Measured on this box, all three shapes come out of os.makedirs -- and one out of
    the file write -- with no code of their own:
        FileExistsError     [Errno 17]  --out-dir IS an existing regular file
        NotADirectoryError  [Errno 20]  --out-dir has a file in its middle (<file>/sub)
        PermissionError     [Errno 13]  --the directory exists and refuses a new file
        OSError EFBIG/ENOSPC from the record write itself, on a full or limited filesystem
    All of them are exit 10, decided AFTER admission (an admitted dispatch with a bad out-dir is a
    different fact from a refused dispatch, and refusal codes do not move) and BEFORE the walk (a
    directory that cannot hold the record must not cost a model forty plies). The guard covers both
    os.makedirs and the publish, and covers the WHOLE `with open(...)` block rather than write()
    alone. That scope is measured, not assumed: the record is buffered text -- 2,370 B for a dry
    record here, 17,508 B for the first real row -- against a text buffer of io.DEFAULT_BUFFER_SIZE
    (8,192 B on most builds, 131,072 B on this box). On this box the dry record's failure surfaces
    at the CLOSE (measured: write() returns, close() raises EFBIG), which a guard around write()
    would not catch; a record larger than the buffer would fail at write() instead. Covering the
    block covers both boundaries.

PUBLISHING: <slug>.<pid>.tmp, three tiers, and the tier in the record
    Two dispatches of one cell must not be able to splice one record out of two runs. A FIXED temp
    name allows exactly that: both writers open the same inode and the rename publishes whichever
    tail landed last (measured on the peer box: an exit-0 slug holding {"writer":"B"} + NULs +
    another writer's tail). The temp is therefore <slug>.<pid>.tmp -- one inode per writer -- and
    the SLUG is claimed exclusively, by the strongest mechanism the out-dir's filesystem supports:

        link-exclusive                os.link(tmp, slug): one syscall, no window, the kernel
                                      refuses to create over an existing name
        excl-claim                    os.link is ENOTSUP (exFAT): CLAIM the slug with
                                      O_CREAT|O_EXCL|O_WRONLY -- which exFAT does support -- then
                                      os.replace(tmp, slug). A second claim is EEXIST.
        replace-no-exclusive-support  neither works: os.replace alone, with the duplicate check on
                                      the slug immediately before it. The weakest publish this
                                      driver will make, and it says so in the row.

    The tier is PROBED in the record's own directory before the walk, recorded as `publish`, and then
    the mechanism that runs IS that one -- so the field names what this process invoked, not what the
    filesystem was thought capable of. os.replace alone is never the only mechanism, because it
    returns None and silently overwrites: something that can be made exclusive, is. And exit 7 holds
    in ALL THREE tiers: exclusivity is a capability that may degrade, the prohibition is a rule.

   11  the model path cannot state its identity: missing or incomplete card, api id mismatch with
       --model, an argv that is not an array, a binary whose digest does not match the card, an api id
       this server does not serve, or a reply from weights the argv does not name
   12  the model path cannot complete: no answer, an HTTP error, or no per-turn token count

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
import errno
import hashlib
import json
import os
import random
import shutil
import sys
import urllib.error
import urllib.request
from typing import NoReturn

EXIT_BAD_ARGS = 2
EXIT_BAD_GRAPH = 3
EXIT_NO_SYMMETRISATION = 4
EXIT_DIGEST_MISMATCH = 5
EXIT_DERIVATION_MISMATCH = 6
EXIT_RECORD_EXISTS = 7
EXIT_UNREACHABLE = 8
EXIT_SELF_TEST_FAIL = 9
EXIT_OUT_DIR_UNUSABLE = 10
EXIT_MODEL_IDENTITY = 11
EXIT_MODEL_TRANSPORT = 12
# A DECLARATION defect, not a data defect. 3 says "this is not a graph"; 13 says "this is a graph,
# and it declares itself under the wrong order" -- different instruction to the peer: reorder the
# array, do not regenerate the distances. Numbers 2-10 and 11-12 were already taken, so this takes
# the next free code rather than folding into 3 (which would lose the distinction above).
EXIT_NODE_ORDER = 13

# THE CANONICAL NODE ORDER. Elder Futhark, the order the generator's RUNE_NAMES carries -- and the
# order the nodes array must be in before anything is hashed, because graph_digest() hashes
# whatever order it is handed. A sorted array therefore produces a well-formed digest of the right
# distances under the wrong declaration (measured on the arrived file: array order 596255d9...,
# sorted fa26e89e...), which no downstream check can detect.
CANONICAL_NODES = ("Fehu", "Uruz", "Thurisaz", "Ansuz", "Raidho", "Kenaz", "Gebo", "Wunjo",
                   "Hagalaz", "Nauthiz", "Isa", "Jera", "Eihwaz", "Perthro", "Elhaz", "Sowilo",
                   "Tiwaz", "Berkano", "Ehwaz", "Mannaz", "Laguz", "Ingwaz", "Dagaz", "Othala")

# sha256("\n".join(nodes) + "\n") over the order above. FIXED BY THE RUNE SET, NOT BY A MATRIX:
# regeneration moves distances and re-serialises bytes and leaves this constant alone, which is
# what makes it usable as a guard on a graph that is still being repaired. Reproduced to the
# character by the peer from the arrived file's own nodes array.
CANONICAL_NODES_SHA256 = "49fa1fb94b71bb934323b626b86ec9f76ff1a646d3a03a40ebc1eac98378cc94"

# HOW the record reached its name. Three values, and the value travels in every record, because a
# weaker publish that travels unnamed is indistinguishable to a later reader from a strong one.
#   link-exclusive                os.link(tmp, slug) -- one syscall, and a slug cannot be created
#                                 over an existing one: the kernel does the exclusivity
#   excl-claim                    os.link is ENOTSUP here (exFAT). So CLAIM the slug with
#                                 O_CREAT|O_EXCL (which exFAT does support), then publish the bytes
#                                 from <slug>.<pid>.tmp with os.replace. A second claim is EEXIST.
#   replace-no-exclusive-support  neither works: os.replace alone, which returns None and silently
#                                 overwrites. The duplicate check is therefore made on the slug
#                                 first, and that is the weakest this driver ever publishes.
# IN EVERY TIER A SLUG THAT ALREADY EXISTS IS STILL REFUSED WITH EXIT 7. Exclusivity is a
# capability the filesystem may lack; the prohibition on overwriting a record you did not take is a
# rule, and only the capability degrades.
PUBLISH_LINK_EXCLUSIVE = "link-exclusive"
PUBLISH_EXCL_CLAIM = "excl-claim"
PUBLISH_REPLACE_ONLY = "replace-no-exclusive-support"
PUBLISH_TIERS = (PUBLISH_LINK_EXCLUSIVE, PUBLISH_EXCL_CLAIM, PUBLISH_REPLACE_ONLY)

# The errnos that mean "this filesystem does not implement hard links", as distinct from "you may
# not write here" (EACCES/EROFS/ENOSPC), which must NOT degrade the tier: a directory that refuses
# the probe is exit 10, not a weaker publish. ENOTSUP is what the exFAT driver returns (measured on
# a real exFAT image); ENOSYS/EPERM are the shapes other kernels and FUSE mounts use for the same
# fact, and they are listed so the fallback is a decision rather than an accident.
LINK_UNSUPPORTED_ERRNOS = frozenset({errno.ENOTSUP, errno.EOPNOTSUPP, errno.ENOSYS, errno.EPERM})
CLAIM_UNSUPPORTED_ERRNOS = frozenset({errno.ENOTSUP, errno.EOPNOTSUPP, errno.ENOSYS, errno.EPERM,
                                      errno.EINVAL})

SELF = os.path.abspath(__file__)

# Arguments the parser accepts whose value no dispatch reads. Every one of them must be REFUSED at
# admission while that is true, because a dispatch that types it gets a record contradicting it --
# and here the contradiction is not cosmetic: the flag is absent from the slug too, so the dispatch
# that sets it and the dispatch that omits it collide on one output path and the second is refused
# as a duplicate.
#
# EMPTY NOW, AND THE EMPTINESS IS THE POINT: its one member (--seed-model) graduated into
# CONSUMED_DESTS when the model path landed and started sending it as the request seed. The DICT stays
# because the CLASS it guards does not go away: a flag added tomorrow that nothing reads must still
# fail --self-test instead of landing in a record as a value the run contradicts.
UNIMPLEMENTED_ARGS = {}

# Every dest the cell semantics actually consume. Anything outside this set must be declared in
# UNIMPLEMENTED_ARGS; parser_audit() fails --self-test otherwise, so a flag nobody reads cannot
# reach a record by being added and forgotten.
CONSUMED_DESTS = {
    "graph", "symmetrisation", "K", "rune", "cap", "seed", "seed_model", "expect_graph_digest",
    "expect_nodes_sha256", "cell_spec", "out_dir", "dry_run", "model", "model_identity", "base_url",
    "no_think", "self_test", "print_graph_digest",
}


def die(code, msg) -> NoReturn:
    print(f"labyrinth_run: exit {code}: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_graph(path):
    """Structural validity ONLY, and every failure is a numbered exit (3), never a traceback.

    The type checks are not pedantry: each one is a shape this driver used to dereference before
    checking, so a malformed file produced `AttributeError`/`TypeError` at exit 1 -- an undeclared
    code a second box cannot key on. Measured on the arrived file: `"semantics"` was a STRING and
    the dispatch died at `g["semantics"].get("K", 12)`.
    """
    try:
        raw = open(path, "rb").read()
    except OSError as e:
        die(EXIT_BAD_GRAPH, f"cannot read graph: {e}")
    try:
        g = json.loads(raw)
    except ValueError as e:
        die(EXIT_BAD_GRAPH, f"graph is not JSON: {e}")
    if not isinstance(g, dict):
        die(EXIT_BAD_GRAPH, f"graph is a JSON {type(g).__name__}, not an object")
    for k in ("nodes", "ged_fwd", "semantics"):
        if k not in g:
            die(EXIT_BAD_GRAPH, f"graph missing key {k!r}")
    nodes = g["nodes"]
    F = g["ged_fwd"]
    if not isinstance(nodes, list):
        die(EXIT_BAD_GRAPH, f"graph 'nodes' is {type(nodes).__name__}, not an array")
    if len(nodes) != 24:
        die(EXIT_BAD_GRAPH, f"graph has {len(nodes)} nodes, expected 24")
    if any(not isinstance(a, str) for a in nodes):
        die(EXIT_BAD_GRAPH, "graph 'nodes' carries a non-string entry")
    if len(set(nodes)) != 24:
        die(EXIT_BAD_GRAPH, "duplicate node names")
    if not isinstance(F, dict):
        die(EXIT_BAD_GRAPH, f"graph 'ged_fwd' is {type(F).__name__}, not an object")
    for a in nodes:
        if a not in F or not isinstance(F[a], dict) or any(y not in F[a] for y in nodes):
            die(EXIT_BAD_GRAPH, f"ged_fwd incomplete at {a}")
        for y in nodes:
            v = F[a][y]
            # int(), not float(): graph_digest() coerces with int(), so 3.0 and 3 would hash
            # alike while a row would record two different matrices. Bool is an int in Python
            # and a distance of True is a defect, not a 1.
            if isinstance(v, bool) or not isinstance(v, int):
                die(EXIT_BAD_GRAPH,
                    f"ged_fwd[{a!r}][{y!r}] is {type(v).__name__} ({v!r}), not an int: the digest "
                    f"coerces with int(), so a non-int distance is a matrix this driver cannot "
                    f"read without inventing a value")
            if v < 0:
                die(EXIT_BAD_GRAPH, f"ged_fwd[{a!r}][{y!r}] is {v}, a negative distance")
    graph_semantics(g)
    return raw, g, nodes, F


def graph_semantics(g):
    """The graph's own `semantics` object, checked as a SHAPE, once, for every caller.

    Measured defect this exists for: the arrived file carried "semantics" as a string. The audit
    path certified it (exit 0, digest 596255d9...) and a dispatch died on it (exit 1,
    AttributeError). A file the walk cannot load is not a file the audit may certify, so the shape
    is a load-time fact and not a dispatch-time accident.
    """
    sem = g["semantics"]
    if not isinstance(sem, dict):
        die(EXIT_BAD_GRAPH,
            f"graph 'semantics' is {type(sem).__name__}, not an object: {sem!r:.160}. K is read "
            f"from it, so no dispatch can load this file -- and the audit path refuses it too, "
            f"because a predicate may not certify what admission refuses. The repair is in the "
            f"generator: semantics must be an object carrying K (the frozen cell uses K:12).")
    return sem


def semantics_K(g):
    """The graph's declared K, or 12. Shape-checked here so no caller can meet a TypeError."""
    K = graph_semantics(g).get("K", 12)
    if isinstance(K, bool) or not isinstance(K, int) or K < 1:
        die(EXIT_BAD_GRAPH,
            f"graph semantics K={K!r} is not an int >= 1; a threshold that is absent from the "
            f"arithmetic, or a string compared against a distance, is a graph defect")
    return K


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


def nodes_sha256(nodes):
    """The DECLARATION, hashed without any matrix: sha256("\\n".join(nodes) + "\\n").

    Deliberately trivial and deliberately separate from graph_digest(): the point is that the
    order can be pinned by something a regeneration cannot move, so a graph that is being repaired
    still has a stable name for "the same runes, the same order".
    """
    return hashlib.sha256(("\n".join(nodes) + "\n").encode("utf-8")).hexdigest()


def check_node_order(nodes, expect_nodes_sha256=None):
    """The nodes array must BE the canonical order, and this runs BEFORE graph_digest().

    That placement is the whole guard. graph_digest() hashes whatever array it is handed, so a
    sorted array yields a well-formed digest of the correct distances under the wrong declaration
    (measured: the arrived file's distances hash to 596255d9... in array order and fa26e89e... with
    the array sorted). Nothing downstream can tell those apart -- exit 5 compares a number that was
    computed after the order was already lost -- so the check cannot be downstream.
    """
    got = nodes_sha256(nodes)
    if expect_nodes_sha256 is not None and got != expect_nodes_sha256:
        die(EXIT_NODE_ORDER,
            f"nodes declaration {got} != --expect-nodes-sha256 {expect_nodes_sha256}. The nodes "
            f"array IS the declaration that graph_digest hashes, so graph_digest was NOT computed "
            f"here: a number produced from the wrong declaration would pin the wrong test and look "
            f"correct. file_sha256 ({'a reading about the bytes'}) is not the identity of the test "
            f"either -- the pinned identity is graph_digest, and it cannot be stated until the "
            f"declaration is the expected one.")
    if got != CANONICAL_NODES_SHA256:
        first = next((i for i, (a, b) in enumerate(zip(nodes, CANONICAL_NODES)) if a != b), None)
        where = (f"first divergence at index {first}: file {nodes[first]!r} vs canonical "
                 f"{CANONICAL_NODES[first]!r}" if first is not None else
                 f"the arrays differ only in length ({len(nodes)} vs {len(CANONICAL_NODES)})")
        same_set = sorted(nodes) == sorted(CANONICAL_NODES)
        die(EXIT_NODE_ORDER,
            f"nodes array is not the canonical elder-Futhark order: nodes_sha256 {got} != "
            f"canonical {CANONICAL_NODES_SHA256}; {where}; same rune SET: {same_set}. graph_digest "
            f"was NOT computed -- hashing a wrongly-ordered array produces a well-formed number "
            f"about the wrong declaration, which is exactly what exit 5 can never see. The repair "
            f"is to reorder the array to CANONICAL_NODES, not to regenerate the distances: a file "
            f"that carries the same rune set in sorted order (same_set True) is the same matrix "
            f"under a different declaration.")


def validate_graph(path, expect_graph_digest=None, expect_nodes_sha256=None, rune=None):
    """THE ONE VALIDATION PATH. Both --print-graph-digest and a dispatch call THIS function.

    Order, and every step is a numbered exit -- nothing reachable from here may traceback:
        1 structural        exit 3   unreadable / not JSON / not an object / missing key / not 24
                                      names / duplicate or non-string names / incomplete or non-int
                                      ged_fwd / 'semantics' not an object / malformed adjacency
                                      column
        2 node order        exit 13  the array must BE CANONICAL_NODES (see check_node_order)
        3 start rune        exit 2   dispatch only: --rune must name a node
        4 digest computed            only NOW, because only now is the declaration known
        5 derivation        exit 6   shipped adjacency_*_K vs the matrix at the graph's K, named
                                      by the pinned identity
        6 digest compared   exit 5   last, and only against the declared identity
    Step 4 sits between 3 and 5 on purpose: the digest is a READING until the declaration is
    right, but the derivation refusal needs the pinned identity to name it, and the derivation
    check must keep its precedence over the digest comparison (6 before 5, unchanged).
    """
    raw, g, nodes, F = load_graph(path)
    fsha = file_sha256(raw)
    check_node_order(nodes, expect_nodes_sha256)
    if rune is not None and rune not in nodes:
        die(EXIT_BAD_ARGS, f"start rune {rune!r} not in graph")
    K = semantics_K(g)
    gdig = graph_digest(nodes, F)
    cells_checked = check_derivation(g, nodes, F, gdig)
    if expect_graph_digest and expect_graph_digest != gdig:
        die(EXIT_DIGEST_MISMATCH,
            f"graph_digest {gdig} != expected {expect_graph_digest}. graph_digest is the pinned "
            f"identity of the test; this file's file_sha256 is {fsha}, which is a reading about "
            f"the bytes and moves whenever the serialisation does -- it is not the identity.")
    return {"raw": raw, "g": g, "nodes": nodes, "F": F, "file_sha256": fsha,
            "graph_digest": gdig, "nodes_sha256": nodes_sha256(nodes),
            "canonical_nodes_sha256": CANONICAL_NODES_SHA256,
            "graph_K": K, "derivation_columns_checked": cells_checked}


def audit_report(f):
    """What --print-graph-digest prints. Every field is a fact validated by validate_graph().

    The report is not a summary of a different path: it is the same call a dispatch makes, so its
    exit 0 means "a dispatch would get past every graph check", and nothing more.
    """
    return {
        "definition": "ged-v2",
        "node_order": "nodes array",
        "nodes": f["nodes"],
        "nodes_sha256": f["nodes_sha256"],
        "canonical_nodes_sha256": f["canonical_nodes_sha256"],
        "node_order_canonical": f["nodes_sha256"] == CANONICAL_NODES_SHA256,
        "file_sha256": f["file_sha256"],
        "file_sha256_role": "transport evidence about the bytes; NEVER the identity of the test",
        "graph_digest": f["graph_digest"],
        "pinned_identity": {"field": "graph_digest", "value": f["graph_digest"]},
        "derivation_columns_checked": f["derivation_columns_checked"],
        "derivation_basis": ("shipped adjacency_*_K columns compared with the matrix at the "
                             "graph's K; 0 means the file carries no such column, NOT that the "
                             "columns agreed"),
        "checks_run": ("structural(3) -> node order(13) -> derivation(6) -> digest(5): the same "
                       "path a dispatch runs, so this file cannot be certified here and refused "
                       "there"),
    }


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


def check_derivation(g, nodes, F, graph_digest_value):
    """The shipped adjacency_*_K columns must equal what the matrix says at the graph's K.
    If they disagree the file is not internally consistent and must not be scored.

    A column that is PRESENT but the wrong shape used to raise (TypeError/KeyError) at exit 1, or
    -- worse for a string value -- be sorted happily as characters and compared against a list of
    names. Shape is checked before comparison, and every refusal names the PINNED IDENTITY
    (graph_digest), not just the K: a reader who receives "the derivation disagrees at K=12" cannot
    tell which graph was being discussed without it.
    """
    K = semantics_K(g)
    checked = 0
    for sym, key in (("min", "adjacency_min_K"), ("max", "adjacency_max_K")):
        if key not in g:
            # 0 checked is a READING, not a pass: a file that carries no adjacency column has not
            # been shown to agree with anything. The row records the count beside its basis.
            continue
        col = g[key]
        if not isinstance(col, dict):
            die(EXIT_BAD_GRAPH,
                f"{key} is {type(col).__name__}, not an object of node -> [neighbours]; a column "
                f"this shape cannot be compared with the matrix at K={K}")
        for a in nodes:
            if a not in col:
                die(EXIT_BAD_GRAPH,
                    f"{key} has no entry for {a!r}: an incomplete column is not a column that "
                    f"agrees, it is one that was never compared")
            shipped = col[a]
            if not isinstance(shipped, list) or any(not isinstance(y, str) for y in shipped):
                die(EXIT_BAD_GRAPH,
                    f"{key}[{a!r}] is {type(shipped).__name__}, not an array of node names; "
                    f"sorting a string compares characters, not neighbours")
            want = sorted(shipped)
            got = neighbours(nodes, F, sym, K, a)
            if want != got:
                die(EXIT_DERIVATION_MISMATCH,
                    f"{key}[{a}] disagrees with the matrix at K={K} (graph_digest "
                    f"{graph_digest_value}): shipped {len(want)} neighbours, derived {len(got)}. "
                    f"graph_digest is the pinned identity of the graph this refusal is about; "
                    f"file_sha256 is only a reading about the bytes.")
            checked += 1
    return checked


def stdout_argv():
    return [os.path.basename(sys.executable), SELF] + sys.argv[1:]


# ==================================================================================================
# THE MODEL PATH. proposal -> parse -> legal-move check -> per-turn tokens -> record.
#
# The frozen spec fixes THE TEST (graph, min, K=12, cap, seed, the decoder pair) and records THE MODEL
# per box. Everything below is the part the spec leaves to the driver: how a question is asked, how a
# reply is read, and what makes a reply a MOVE rather than a wish. The read grammar is stated in one
# place (read_proposal's docstring + the module docstring) because two readers of one record is how a
# field and its meaning drift apart.
# ==================================================================================================
TURN_TIMEOUT_S = 300
MAX_TURN_TOKENS = 32
DEFAULT_BASE_URL = "http://127.0.0.1:8080"
IDENTITY_FIELDS = ("api_model_id", "quant", "server_argv", "server_binary_digest")

# The eight abstention tokens, BORROWED VERBATIM from the sokoban read-grammar §2a list (R1, ratified
# 2026-10-13) because a second list would be a second convention for the same act: a model that is
# offered nine ways to abstain on one cabinet and eight on another is being measured on two rules
# under one name. One token, whitespace removed, matched case-insensitively.
ABSTENTION_TOKENS = ("RESIGN", "RESIGNS", "RESIGNED", "GIVEUP", "SURRENDER",
                     "IQUIT", "QUIT", "FORFEIT")

# The question. It names the rune ALPHABET -- 24 invented names are not derivable, and a model asked
# to guess them would be measured on its vocabulary rather than on its walk -- and NEVER the legal
# set. A position that arrives with its candidates listed is a menu; choosing from a menu measures
# the menu. The text and its digest travel in every row, so a prompt cannot move silently.
PROMPT_TEMPLATE = (
    "You are walking a labyrinth of runes.\n"
    "A move from one rune to another is legal when the graph distance between them is more than 0 "
    "and at most {K}. Both directions use the same rule.\n"
    "The runes are: {alphabet}.\n"
    "You are at {cur}.\n"
    "Reply with exactly one rune name from that list and nothing else.\n"
    "If you cannot move, reply GIVE UP.\n"
)


def _first_line(text):
    for line in (text or "").splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def _undelimit(s):
    """Strip ONE layer of surrounding quotes/backticks: a delimiter is not content."""
    while len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'`":
        s = s[1:-1].strip()
    return s


def read_proposal(text, names, legal):
    """-> (kind, canonical name or None, what was actually read).

    THE GRAMMAR, stated once and applied without rescue: exactly one rune name, alone on the first
    non-empty line, case-insensitive, surrounding quotes/backticks stripped. A name that exists but is
    NOT in `legal` is `blocked` -- a legal ACT the maze refused, which is a different finding from an
    unreadable turn. One of the abstention tokens is `give_up` and ENDS the cell. Anything else is
    `not_an_action`: prose, punctuation, a trailing full stop, two names, fences, JSON. NEVER
    truncated, never first-token, never fuzzy-matched -- every one of those rescues turns a reading
    rule into a guess, and the record has no field for "a guess".
    """
    line = _undelimit(_first_line(text))
    if "".join(line.split()).upper() in ABSTENTION_TOKENS:
        return "give_up", None, line
    canon = {n.upper(): n for n in names}
    if line.upper() in canon:
        name = canon[line.upper()]
        return ("move" if name in legal else "blocked"), name, line
    return "not_an_action", None, line


def _argv_gguf(argv):
    for i, x in enumerate(argv[:-1]):
        if x in ("--model", "-m"):
            return argv[i + 1]
    return None


def verify_model_identity(path, model):
    """-> (identity dict, None) or (None, (exit, message)). THE CARD IS CHECKED, NOT BELIEVED.

    Spec §3 makes four fields required and none substitutable, because the api id carries no quant:
    a row naming only `ornith9b` does not say which weights answered. So this function does not copy
    the card into the row -- it RE-DERIVES what can be re-derived on this box (the binary's digest,
    the quant in the gguf name the argv loads) and refuses on any disagreement. Every refusal is exit
    11 and names the missing or contradicted field: the alternative is a row that claims weights
    nothing named, which is the one thing a benchmark row may never do.
    """
    if not path:
        return None, (EXIT_MODEL_IDENTITY,
                      "a non-dry dispatch must name the weights that answered (spec §3: model id, "
                      "quant, server_argv, server_binary_digest). --model names only the api id, and "
                      "the api id carries NO quant. Missing: --model-identity")
    try:
        card = json.loads(open(path, "rb").read())
    except OSError as e:
        return None, (EXIT_MODEL_IDENTITY, f"cannot read the model identity card {path}: {e}")
    except ValueError as e:
        return None, (EXIT_MODEL_IDENTITY, f"the model identity card {path} is not JSON: {e}")
    if not isinstance(card, dict):
        return None, (EXIT_MODEL_IDENTITY, f"the model identity card {path} is not a JSON object")
    missing = [k for k in IDENTITY_FIELDS if card.get(k) in (None, "", [], {})]
    if missing:
        return None, (EXIT_MODEL_IDENTITY,
                      f"the model identity card {path} is missing {', '.join(missing)}; spec §3 makes "
                      f"all four required and none substitutable")
    if card["api_model_id"] != model:
        return None, (EXIT_MODEL_IDENTITY,
                      f"the card names api_model_id {card['api_model_id']!r} but --model is {model!r}; "
                      f"one of the two is not the model that will answer")
    argv = card["server_argv"]
    if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
        return None, (EXIT_MODEL_IDENTITY,
                      "server_argv must be the argv ARRAY (a non-empty list of non-empty strings). A "
                      "one-line string cannot be checked against anything, and an unchecked argv is a "
                      "claim, not evidence")
    gguf = _argv_gguf(argv)
    if not gguf:
        return None, (EXIT_MODEL_IDENTITY,
                      "server_argv names no --model/-m file, so which weights it loads is stated "
                      "nowhere in the card")
    if card["quant"] not in os.path.basename(gguf):
        return None, (EXIT_MODEL_IDENTITY,
                      f"the card's quant {card['quant']!r} does not appear in the gguf name {gguf!r}: "
                      f"the argv does not load the quant the card claims")
    binary = card.get("server_binary") or argv[0]
    # A LEASE-WRAPPED SERVER IS THE NORMAL CASE ON THIS BOX: the argv starts at gpu-lease.sh and the
    # binary that actually answers is further down the array. So the binary is named explicitly when
    # the card can, and the check is that the argv really launches it -- not that it is argv[0].
    bpath = binary if os.path.isabs(binary) else shutil.which(binary)
    if not bpath or not os.path.isfile(bpath):
        return None, (EXIT_MODEL_IDENTITY,
                      f"the card's server binary {binary!r} is not a file on this box, so the "
                      f"binary's digest cannot be recomputed -- and a digest nobody recomputed is a "
                      f"quotation")
    if not any(x == binary or os.path.basename(x) == os.path.basename(bpath) for x in argv):
        return None, (EXIT_MODEL_IDENTITY,
                      f"the card's server binary {binary!r} does not appear in server_argv: the argv "
                      f"recorded is not the argv that launches the binary whose digest is claimed")
    got = hashlib.sha256(open(bpath, "rb").read()).hexdigest()
    if got != card["server_binary_digest"]:
        return None, (EXIT_MODEL_IDENTITY,
                      f"server_argv[0] {bpath} hashes to {got}, not the card's "
                      f"{card['server_binary_digest']}: the binary that would answer is not the one "
                      f"the card names")
    return {"api_model_id": card["api_model_id"], "quant": card["quant"],
            "server_argv": argv, "server_binary_digest": card["server_binary_digest"],
            "server_binary_path": os.path.abspath(bpath), "model_file": gguf}, None


def preflight_models(base_url, api_id, timeout=60):
    """The api id must be one this endpoint actually serves. -> refusal (exit, msg) or None."""
    url = base_url.rstrip("/") + "/v1/models"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            j = json.loads(r.read().decode())
    except Exception as e:                                             # noqa: BLE001
        return (EXIT_MODEL_TRANSPORT,
                f"the model path could not complete: cannot reach {url} to list models "
                f"({type(e).__name__}: {e})")
    ids = [m.get("id") for m in (j.get("data") or []) if isinstance(m, dict)]
    if api_id not in ids:
        return (EXIT_MODEL_IDENTITY,
                f"api id {api_id!r} is not served by {url}; served: {', '.join(map(str, ids))}")
    return None


def check_served(served, ident, ply):
    """The weights that ANSWERED must be the file the argv names. Checked every turn: a swapping
    server (llama-swap) can put a different model behind the same api id between two plies, and that
    is the one way a row quietly stops being about the model it names."""
    if not served:
        die(EXIT_MODEL_IDENTITY,
            f"ply {ply}: the server did not report which model answered; the row would claim weights "
            f"nothing named")
    ok = (served == ident["api_model_id"]
          or served == os.path.basename(ident["model_file"])
          or os.path.realpath(served) == os.path.realpath(ident["model_file"]))
    if not ok:
        die(EXIT_MODEL_IDENTITY,
            f"ply {ply}: the server reports {served!r} answered, but the card's argv loads "
            f"{ident['model_file']!r}. A row about one model measured from another is not a row")


def model_turn(base_url, api_id, prompt, no_think, seed_model, timeout=TURN_TIMEOUT_S):
    """One ply's question -> dict(text, field, completion_tokens, prompt_tokens, finish_reason,
    served_model). Dies 12 rather than returning a partial answer: a turn with no answer or no token
    count cannot become a row honestly, and a 0 would be a measurement we did not make."""
    body = {"model": api_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": MAX_TURN_TOKENS, "temperature": 0.0, "seed": seed_model}
    if no_think:
        # The build's own switch: llama.cpp server-common parses OAI `reasoning_effort`, and "none"
        # disables reasoning (the --reasoning flag's per-request form). Recorded as decoder_mode
        # "off". Nothing is sent for "on": `on` IS the harness default, and a decoder recorded by
        # what was SENT is a fact, while one recorded by what was hoped is a wish.
        body["reasoning_effort"] = "none"
    url = base_url.rstrip("/") + "/v1/chat/completions"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            j = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read()[:400].decode("utf-8", "replace")
        die(EXIT_MODEL_TRANSPORT,
            f"the model path could not complete: HTTP {e.code} from {url}: {detail}")
    except Exception as e:                                             # noqa: BLE001
        die(EXIT_MODEL_TRANSPORT,
            f"the model path could not complete: {type(e).__name__} from {url}: {e}")
    if not isinstance(j, dict) or not j.get("choices"):
        die(EXIT_MODEL_TRANSPORT, "the model path could not complete: the answer carries no choices")
    usage = j.get("usage") or {}
    ct = usage.get("completion_tokens")
    if not isinstance(ct, int):
        die(EXIT_MODEL_TRANSPORT,
            "the model path could not complete: the answer carries no usage.completion_tokens, so "
            "the turn's cost cannot be recorded and a 0 would be invented")
    msg = j["choices"][0].get("message") or {}
    text, field = msg.get("content") or "", "content"
    if not text.strip() and (msg.get("reasoning_content") or "").strip():
        # Some templates put the only text in the reasoning field. WHICH FIELD IT CAME FROM travels
        # in the row: "the model answered" and "the model thought and did not answer" are different
        # findings, and a reader who cannot tell them will call the second one the first.
        text, field = msg["reasoning_content"], "reasoning_content"
    return {"text": text, "field": field, "completion_tokens": ct,
            "prompt_tokens": usage.get("prompt_tokens"),
            "finish_reason": j["choices"][0].get("finish_reason"),
            "served_model": j.get("model")}


def model_walk(nodes, F, sym, K, rune, cap, ident, base_url, no_think, seed_model):
    """The cell, played by one model. -> the pieces main() puts in the record."""
    alphabet = ", ".join(nodes)
    cur = rune
    visited = [cur]
    moves, tokens = [], []
    blocked = not_an_action = give_up = 0
    end_state, plies = "cap", 0
    while plies < cap:
        nb = neighbours(nodes, F, sym, K, cur)
        if not nb:
            # The MAZE offers nothing. Counted in `blocked` exactly where the dry path counts it, so
            # one field means one thing on both paths.
            blocked += 1
            end_state = "dead_end"
            break
        prompt = PROMPT_TEMPLATE.format(K=K, alphabet=alphabet, cur=cur)
        ans = model_turn(base_url, ident["api_model_id"], prompt, no_think, seed_model)
        check_served(ans["served_model"], ident, plies)
        kind, name, read_as = read_proposal(ans["text"], nodes, nb)
        entry = {"ply": plies, "from": cur, "to": None, "legal_moves": len(nb),
                 "read": kind, "proposal": ans["text"], "proposal_field": ans["field"],
                 "read_as": read_as,
                 "completion_tokens": ans["completion_tokens"],
                 "prompt_tokens": ans["prompt_tokens"],
                 "finish_reason": ans["finish_reason"],
                 "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()}
        if kind == "move":
            entry["to"] = name
            cur = name
            visited.append(name)
        elif kind == "blocked":
            entry["proposed"] = name
            blocked += 1
        elif kind == "give_up":
            give_up += 1
            end_state = "give_up"
        else:
            not_an_action += 1
        moves.append(entry)
        tokens.append(ans["completion_tokens"])
        plies += 1
        if kind == "give_up":
            break
    return {"cur": cur, "visited": visited, "moves": moves, "tokens": tokens,
            "blocked": blocked, "not_an_action": not_an_action, "give_up": give_up,
            "end_state": end_state, "plies": plies}


def slug_part(s):
    return "".join(ch if ch.isalnum() or ch in "-._" else "-" for ch in s)


# ==== PUBLISHING THE RECORD =======================================================================
# Two writers on one cell must not be able to splice one record out of two runs, and the reason is
# measured, not theoretical: with a FIXED temp name both writers open the same inode, and the rename
# that follows publishes whichever tail was written last. The peer box produced an exit-0 slug whose
# bytes were {"writer":"B"} + NULs + the other writer's tail. So:
#   the temp is <slug>.<pid>.tmp -- one inode per writer, no shared buffer, nothing to splice
#   the SLUG is claimed exclusively, by the strongest mechanism the out-dir's filesystem supports
#   WHICH mechanism is decided by a probe of that same directory, recorded in the row as "publish",
#   and then used -- so the value in the row is not a claim about what the filesystem can do, it is
#   the mechanism that this run actually invoked.
# The probe happens before the walk, so an out-dir that cannot hold a record refuses BEFORE the
# model is asked anything: 40 plies of GPU time spent on a record with nowhere to go is a cost this
# driver does not need to pay, and the refusal is a property of the out-dir, not of the run.

def probe_publish_tier(out_path, link=None, claim_open=None):
    """Which exclusive-publish mechanism the record's own directory supports.

    Probes the directory the slug lives in, not a temp dir: hard-link support is a property of that
    filesystem, and it is the one the record is published onto.

    Raises OSError when the directory cannot hold a file at all (EACCES on a read-only dir, ENOSPC
    on a full one, ENOTDIR); the caller maps that to EXIT_OUT_DIR_UNUSABLE. It deliberately does
    NOT swallow those into a weaker tier: "link is not implemented here" (ENOTSUP) is a capability
    answer, "you may not write here" is not.
    """
    link = os.link if link is None else link
    claim_open = os.open if claim_open is None else claim_open
    # A short, pid-scoped name in the record's own directory: the directory is what is under test,
    # and a name derived from the slug would add ~20 bytes to a slug that is already long.
    src = os.path.join(os.path.dirname(out_path) or ".", f".labyrinth-publish-probe.{os.getpid()}")
    lnk = src + ".link"
    claim = src + ".claim"
    try:
        with open(src, "wb") as fh:
            fh.write(b"publish-probe\n")
        try:
            link(src, lnk)
        except OSError as e:
            if e.errno not in LINK_UNSUPPORTED_ERRNOS:
                raise
        else:
            return PUBLISH_LINK_EXCLUSIVE
        try:
            fd = claim_open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)
        except OSError as e:
            if e.errno not in CLAIM_UNSUPPORTED_ERRNOS:
                raise
        else:
            os.close(fd)
            return PUBLISH_EXCL_CLAIM
        return PUBLISH_REPLACE_ONLY
    finally:
        for p in (src, lnk, claim):
            try:
                os.unlink(p)
            except OSError:
                pass


def publish_record(out_path, payload, tier, pid=None):
    """Publish `payload` at `out_path` with the exclusivity `tier` allows.

    The whole `with open(tmp, "w")` block is inside the caller's OSError guard ON PURPOSE, and the
    scope is measured rather than assumed. The record is buffered text: this box's dry record is
    2,370 B and the first real row was 17,508 B, while the text buffer is io.DEFAULT_BUFFER_SIZE --
    8,192 B on most CPython builds, 131,072 B on this one. Which call fails therefore depends on the
    record size AND the build: on this box a 2,370 B record's failure surfaces at the CLOSE (write()
    returns, close() raises EFBIG under RLIMIT_FSIZE), and a record over the buffer's size would fail
    at write() instead. A guard around write() alone misses the first; a guard around the open/close
    but not the write misses the second. So the guard covers the block.

    Exit 7 in every tier: an existing slug is refused, never replaced, whether the exclusivity came
    from link, from a claim, or from neither.
    """
    if tier not in PUBLISH_TIERS:
        raise ValueError(f"unknown publish tier {tier!r}")
    pid = os.getpid() if pid is None else pid
    tmp = f"{out_path}.{pid}.tmp"
    try:
        with open(tmp, "w") as fh:
            fh.write(payload)
        if tier == PUBLISH_LINK_EXCLUSIVE:
            try:
                os.link(tmp, out_path)
            except FileExistsError:
                die(EXIT_RECORD_EXISTS,
                    f"{out_path} already exists; a record you did not take is not yours to "
                    f"overwrite (publish={tier})")
            return
        if tier == PUBLISH_EXCL_CLAIM:
            try:
                fd = os.open(out_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)
            except FileExistsError:
                die(EXIT_RECORD_EXISTS,
                    f"{out_path} already exists; a record you did not take is not yours to "
                    f"overwrite (publish={tier})")
            # The slug is OURS now (an empty file, created by the exclusive claim). Publishing the
            # bytes over it is a replace of a file this process owns. If we die before the replace,
            # what is left behind is an EMPTY slug -- visibly not a record -- which is a far better
            # failure than a slug holding somebody else's tail.
            os.close(fd)
            os.replace(tmp, out_path)
            return
        # replace-no-exclusive-support: os.replace cannot refuse, so the refusal is made here, on
        # the slug, immediately before the replace.
        if os.path.exists(out_path):
            die(EXIT_RECORD_EXISTS,
                f"{out_path} already exists; a record you did not take is not yours to overwrite "
                f"(publish={tier}: this filesystem supports neither a hard link nor an exclusive "
                f"claim, so the check is a check and not a guarantee)")
        os.replace(tmp, out_path)
    finally:
        # The temp must never survive -- not on success, not on a refusal, not on an exception.
        # A leftover <slug>.<pid>.tmp is not a record and nothing downstream may mistake it for one.
        try:
            os.unlink(tmp)
        except OSError:
            pass


# ==== THE MODEL PATH'S TWO TEST VECTORS ===========================================================
# A read grammar is a promise about bytes, so it gets read out loud on bytes that were chosen to be
# awkward: a trailing full stop, two names, a fence, JSON, an alias of itself (distance 0, so NOT a
# move), and the eight abstentions. If a future edit "improves" the reader by trimming a full stop or
# taking the first token, `Uruz.` and `I move to Uruz` stop being not_an_action and this fails.
PARSE_TEST_NAMES = ("Fehu", "Uruz", "Othala")
PARSE_TEST_LEGAL = ("Uruz",)
PARSE_TEST_VECTOR = [
    ("Uruz", "move", "Uruz"),
    ("  uruz  \n", "move", "Uruz"),
    ('"Uruz"', "move", "Uruz"),
    ("`Uruz`", "move", "Uruz"),
    ("Othala", "blocked", "Othala"),
    ("Fehu", "blocked", "Fehu"),
    ("Uruz.", "not_an_action", None),
    ("I move to Uruz", "not_an_action", None),
    ("Uruz, then Othala", "not_an_action", None),
    ("```\nUruz\n```", "not_an_action", None),
    ("{\n  \"rune\": \"Uruz\"\n}", "not_an_action", None),
    ("", "not_an_action", None),
    ("GIVE UP", "give_up", None),
    ("give up", "give_up", None),
    ("I QUIT", "give_up", None),
    ("resign", "give_up", None),
]


def parse_test():
    rows, ok = [], True
    for text, want_kind, want_name in PARSE_TEST_VECTOR:
        kind, name, read_as = read_proposal(text, PARSE_TEST_NAMES, PARSE_TEST_LEGAL)
        good = (kind == want_kind and name == want_name)
        ok = ok and good
        rows.append({"input": text, "read_as": read_as, "kind": kind, "name": name,
                     "expect_kind": want_kind, "expect_name": want_name, "pass": good})
    return ok, rows


def identity_test():
    """The card is CHECKED, not believed. One card that should pass, five that must be refused.

    The binary digest is recomputed against a real file (this interpreter), so the check that matters
    most -- "the binary that would answer is the one the card names" -- is exercised for real, not
    asserted. No network, no model.
    """
    import tempfile
    root = tempfile.mkdtemp(prefix="labyrinth-identity-")
    gguf = os.path.join(root, "SMOKE-Test-Model-Q4_K_M.gguf")
    with open(gguf, "w") as fh:
        fh.write("not weights\n")
    binary = sys.executable
    digest = hashlib.sha256(open(binary, "rb").read()).hexdigest()
    base = {"api_model_id": "smoke-test", "quant": "Q4_K_M",
            "server_argv": [binary, "--model", gguf, "--port", "9999"],
            "server_binary_digest": digest}

    def card(name, **over):
        c = dict(base)
        c.update(over)
        path = os.path.join(root, name + ".json")
        with open(path, "w") as fh:
            json.dump(c, fh)
        return path

    rows, ok = [], True
    for name, path, want_exit in (
            ("good", card("good"), None),
            # the lease-wrapped shape this box actually runs: argv[0] is a wrapper, the binary that
            # answers is further down, and it must be named or the digest check has no subject
            ("good_lease_wrapped",
             card("good_lease_wrapped",
                  server_argv=["/bin/sh", "gpu-lease.sh", "run", "--", binary, "--model", gguf],
                  server_binary=binary), None),
            ("binary_not_in_argv",
             card("binary_not_in_argv", server_argv=["/bin/sh", "--model", gguf],
                  server_binary=binary), EXIT_MODEL_IDENTITY),
            ("digest_lie", card("digest_lie", server_binary_digest="0" * 64), EXIT_MODEL_IDENTITY),
            ("quant_lie", card("quant_lie", quant="Q8_0"), EXIT_MODEL_IDENTITY),
            ("argv_string", card("argv_string", server_argv="llama-server --model x"),
             EXIT_MODEL_IDENTITY),
            ("missing_quant", card("missing_quant", quant=""), EXIT_MODEL_IDENTITY),
            ("api_id_mismatch", card("api_id_mismatch", api_model_id="other"), EXIT_MODEL_IDENTITY)):
        ident, refusal = verify_model_identity(path, base["api_model_id"])
        code = refusal[0] if refusal else None
        good = (code == want_exit) and ((ident is not None) == (want_exit is None))
        ok = ok and good
        rows.append({"case": name, "exit": code, "expected_exit": want_exit,
                     "said": (refusal[1][:150] if refusal else ""), "pass": good})
    return ok, rows


def publish_test():
    """The three tiers, the exit-7 rule in EACH of them, and the no-splice property, on real bytes.

    Each case asserts BOTH halves, because either alone is uninformative: "the refusal fired" and
    "nothing ever ran" are the same observation unless the control case is also shown to publish.
    That is why every tier has a fresh-slug control (record written, bytes exact, temp gone) beside
    its existing-slug refusal (exit 7, the existing bytes untouched, temp gone).

    The two weaker tiers are reached by INJECTING the errno the filesystem would raise: ext4 and
    tmpfs -- the only filesystems this box mounts without root -- both implement hard links, so the
    fallback cannot be reached by configuring a directory here. What is under test is the driver's
    DECISION on a real OSError object, and a decision cannot be tested by the capability the test
    box happens to have. The exFAT measurement itself is the peer's: link ENOTSUP, claim OK, second
    claim EEXIST, replace works.
    """
    import contextlib
    import io
    import tempfile

    root = tempfile.mkdtemp(prefix="labyrinth-publish-")
    rows, ok = [], True

    def link_enotsup(src, dst):
        raise OSError(errno.ENOTSUP, "Operation not supported")

    def claim_enotsup(path, flags, mode=0o666):
        raise OSError(errno.ENOTSUP, "Operation not supported")

    def link_eacces(src, dst):
        raise OSError(errno.EACCES, "Permission denied")

    def attempt(fn, *a, **k):
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                v = fn(*a, **k)
            return ("ok", v), err.getvalue().strip()
        except SystemExit as e:
            return ("exit", e.code), err.getvalue().strip()
        except OSError as e:
            return ("oserror", e.errno), err.getvalue().strip()
        except ValueError as e:
            return ("valueerror", str(e)), err.getvalue().strip()

    def fresh(name):
        d = os.path.join(root, name)
        os.makedirs(d)
        return d, os.path.join(d, "S.json")

    def residue(d):
        return sorted(f for f in os.listdir(d) if f.endswith(".tmp") or "publish-probe" in f)

    def case(name, got, want, **extra):
        nonlocal ok
        good = got == want
        ok = ok and good
        rows.append({"case": name, "got": list(got) if isinstance(got, tuple) else got,
                     "expected": list(want) if isinstance(want, tuple) else want,
                     "pass": good, **extra})

    A = '{"writer": "A"}\n'
    B = '{"writer": "B"}\n'

    # --- tier 1: link-exclusive, on a filesystem that has real hard links ---
    d, p = fresh("tier1")
    case("probe_tier1", attempt(probe_publish_tier, p)[0], ("ok", PUBLISH_LINK_EXCLUSIVE))
    case("publish_tier1", attempt(publish_record, p, A, PUBLISH_LINK_EXCLUSIVE)[0], ("ok", None))
    case("publish_tier1_bytes", open(p).read(), A, on_disk="exact")
    case("publish_tier1_temp_gone", residue(d), [])
    case("publish_tier1_existing",
         attempt(publish_record, p, B, PUBLISH_LINK_EXCLUSIVE, 4242)[0], ("exit", 7))
    case("publish_tier1_existing_bytes_kept", open(p).read(), A, on_disk="refused_overwrite")
    case("publish_tier1_existing_temp_gone", residue(d), [])

    # --- tier 2: link is ENOTSUP (exFAT), so the slug is CLAIMED ---
    d, p = fresh("tier2")
    case("probe_tier2", attempt(probe_publish_tier, p, link_enotsup)[0],
         ("ok", PUBLISH_EXCL_CLAIM))
    case("publish_tier2", attempt(publish_record, p, A, PUBLISH_EXCL_CLAIM)[0], ("ok", None))
    case("publish_tier2_bytes", open(p).read(), A, on_disk="exact")
    case("publish_tier2_temp_gone", residue(d), [])
    case("publish_tier2_existing",
         attempt(publish_record, p, B, PUBLISH_EXCL_CLAIM, 4243)[0], ("exit", 7))
    case("publish_tier2_existing_bytes_kept", open(p).read(), A, on_disk="refused_overwrite")
    case("publish_tier2_existing_temp_gone", residue(d), [])

    # --- tier 3: neither works; os.replace alone, with the check in front ---
    d, p = fresh("tier3")
    case("probe_tier3", attempt(probe_publish_tier, p, link_enotsup, claim_enotsup)[0],
         ("ok", PUBLISH_REPLACE_ONLY))
    case("publish_tier3", attempt(publish_record, p, A, PUBLISH_REPLACE_ONLY)[0], ("ok", None))
    case("publish_tier3_bytes", open(p).read(), A, on_disk="exact")
    case("publish_tier3_temp_gone", residue(d), [])
    case("publish_tier3_existing",
         attempt(publish_record, p, B, PUBLISH_REPLACE_ONLY, 4244)[0], ("exit", 7))
    case("publish_tier3_existing_bytes_kept", open(p).read(), A, on_disk="refused_overwrite")
    case("publish_tier3_existing_temp_gone", residue(d), [])

    # --- the fallback must be a CAPABILITY answer only: "you may not write here" does not degrade
    d, p = fresh("denied")
    case("probe_link_eacces_is_error", attempt(probe_publish_tier, p, link_eacces)[0],
         ("oserror", errno.EACCES))
    case("probe_link_eacces_leaves_no_residue", residue(d), [])

    # --- the defect this replaced: two writers, one slug, no splice ---
    d, p = fresh("splice")
    first = attempt(publish_record, p, A, PUBLISH_LINK_EXCLUSIVE, 5001)[0]
    second = attempt(publish_record, p, B, PUBLISH_LINK_EXCLUSIVE, 5002)[0]
    body = open(p, "rb").read()
    case("splice_exactly_one_publish", (first == ("ok", None)) + (second == ("ok", None)), 1)
    case("splice_second_refused", second, ("exit", 7))
    case("splice_bytes_are_one_writer", body in (A.encode(), B.encode()), True,
         on_disk="no splice")
    case("splice_no_nul_padding", b"\x00" in body, False)
    case("splice_temp_gone", residue(d), [])

    # --- the tier is validated, not interpolated ---
    d, p = fresh("badtier")
    case("unknown_tier_refused", attempt(publish_record, p, A, "whatever")[0][0], "valueerror")
    case("unknown_tier_wrote_nothing", os.listdir(d), [])
    return ok, rows


def _quiet(fn, *args, **kwargs):
    """Run fn, capturing both streams. Returns (result, exit_code_or_None, stderr_text).

    The suite must be able to ASSERT on a refusal without the refusal printing into the JSON on
    stdout, and it must be able to read the exit code a refusal chose.
    """
    import contextlib
    import io
    said, buf = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(said):
            return fn(*args, **kwargs), None, said.getvalue().strip()
    except SystemExit as e:
        return None, e.code, said.getvalue().strip()


def _run_main(argv):
    """main() with a fresh sys.argv, captured. (result, exit_code, stderr).

    A normal return carries main()'s own value as the exit code (0 for a completed dispatch), so the
    two paths are compared on the number a shell would see either way.
    """
    saved = sys.argv
    sys.argv = [SELF] + list(argv)
    try:
        result, code, said = _quiet(main)
    finally:
        sys.argv = saved
    if code is None:
        code = result if isinstance(result, int) else 0
    return result, code, said


def node_order_test():
    """The canonical-order guard, exercised on a file it must REFUSE.

    A guard tested only on files it passes is decoration. The failing vector is the one the peer
    would have shipped: the same 24 runes, the same distances, the array sorted alphabetically. Its
    ged-v2 digest is a well-formed 64-hex number -- that is precisely the point, exit 5 could never
    catch it -- and the guard must stop it at 13 before any digest is computed.
    """
    canon = list(CANONICAL_NODES)
    sorted_nodes = sorted(CANONICAL_NODES)
    F = {a: {b: (0 if a == b else (i * 7 + j * 3) % 20 + 1) for j, b in enumerate(canon)}
         for i, a in enumerate(canon)}
    got = nodes_sha256(canon)
    sorted_sha = nodes_sha256(sorted_nodes)
    digest_canon = graph_digest(canon, F)
    digest_sorted = graph_digest(sorted_nodes, F)
    const_ok = got == CANONICAL_NODES_SHA256
    distinct_ok = sorted_sha != CANONICAL_NODES_SHA256 and len(sorted_sha) == 64
    digest_ok = (digest_canon != digest_sorted and len(digest_sorted) == 64
                 and all(c in "0123456789abcdef" for c in digest_sorted))
    pass_ok = check_node_order(canon) is None
    _, refused_exit, _ = _quiet(check_node_order, sorted_nodes)
    refused_ok = refused_exit == EXIT_NODE_ORDER
    _, pin_exit, _ = _quiet(check_node_order, canon, sorted_sha)
    pin_ok = pin_exit == EXIT_NODE_ORDER
    ok = const_ok and distinct_ok and digest_ok and pass_ok and refused_ok and pin_ok
    return ok, {
        "canonical_nodes_sha256": got, "expect": CANONICAL_NODES_SHA256,
        "constant_reproduces": const_ok,
        "sorted_nodes_sha256": sorted_sha, "sorted_declaration_differs": distinct_ok,
        "graph_digest_canonical": digest_canon, "graph_digest_sorted": digest_sorted,
        "sorted_digest_well_formed_but_about_the_wrong_declaration": digest_ok,
        "canonical_passes": pass_ok,
        "sorted_refused_exit": refused_exit, "expect_exit": EXIT_NODE_ORDER,
        "sorted_refused_at_13": refused_ok,
        "wrong_expect_pin_refused_exit": pin_exit, "wrong_expect_pin_refused": pin_ok,
        "failing_vector": "the same 24 runes and the same distances with the nodes array sorted "
                          "alphabetically: a well-formed ged-v2 digest that no exit-5 check can "
                          "distinguish from the real one",
        "pass": ok}


def graph_audit_test():
    """THE AUDIT PATH MUST NOT CERTIFY WHAT ADMISSION REFUSES -- asserted as an end-to-end PAIR.

    Every fixture is fed to BOTH paths (--print-graph-digest and a real --dry-run dispatch) and
    the two must return the SAME exit, that exit must be the declared one, and the refusal must be
    a `labyrinth_run: exit N:` line rather than a traceback. This is the defect in the shape it
    actually took: the audit exited 0 and printed a digest for a file the dispatch died on, and the
    digest was then quoted as a certificate by all three parties.
    """
    import tempfile

    root = tempfile.mkdtemp(prefix="labyrinth-audit-")
    canon = list(CANONICAL_NODES)
    F = {a: {b: (0 if a == b else (i * 7 + j * 3) % 20 + 1) for j, b in enumerate(canon)}
         for i, a in enumerate(canon)}
    base = {"nodes": canon, "ged_fwd": F, "semantics": {"K": 12}}

    def write(name, obj):
        p = os.path.join(root, name)
        with open(p, "w") as fh:
            json.dump(obj, fh)
        return p

    good_min = {a: neighbours(canon, F, "min", 12, a) for a in canon}
    bad_min = dict(good_min)
    bad_min[canon[0]] = []          # a shipped column that contradicts the matrix
    fixtures = [
        # the shape the arrived bytes actually have: semantics is a STRING
        ("semantics_is_a_string", write("sem.json", dict(base, semantics="Raw directed GED.")),
         EXIT_BAD_GRAPH, []),
        # the peer's second instance: same runes, same distances, array SORTED
        ("nodes_sorted", write("sorted.json", {"nodes": sorted(canon), "ged_fwd": F,
                                               "semantics": {"K": 12}}), EXIT_NODE_ORDER, []),
        # a shipped adjacency column that contradicts the matrix
        ("adjacency_contradicts", write("der.json", dict(base, adjacency_min_K=bad_min)),
         EXIT_DERIVATION_MISMATCH, []),
        # --expect-nodes-sha256 names a different declaration: refused on BOTH paths
        ("wrong_declaration_pin", write("ok2.json", dict(base, adjacency_min_K=good_min)),
         EXIT_NODE_ORDER, ["--expect-nodes-sha256", "0" * 64]),
        # control: a valid file, 0 on both paths, and the dispatch really does write a record
        ("valid_control", write("ok.json", dict(base, adjacency_min_K=good_min)), 0, []),
    ]
    ok = True
    rows = []
    for name, path, want, extra in fixtures:
        _, audit_code, audit_said = _run_main(["--graph", path, "--print-graph-digest"] + extra)
        out = os.path.join(root, "out_" + name)
        _, disp_code, disp_said = _run_main(["--graph", path, "--symmetrisation", "min",
                                             "--rune", canon[0], "--cap", "1", "--dry-run",
                                             "--out-dir", out] + extra)
        made = os.path.isdir(out)
        if want == 0:
            declared = True
        else:
            prefix = f"labyrinth_run: exit {want}:"
            declared = audit_said.startswith(prefix) and disp_said.startswith(prefix)
        good = (audit_code == want and disp_code == want
                and declared and (want == 0 or not made))
        ok = ok and good
        rows.append({"case": name, "audit_exit": audit_code, "dispatch_exit": disp_code,
                     "expected_exit": want, "out_dir_created": made,
                     "no_traceback": declared,
                     "audit_said": audit_said.splitlines()[:1],
                     "dispatch_said": disp_said.splitlines()[-1:], "pass": good})
    return ok, rows


def pin_rule_test():
    """PIN THE GRAPH DIGEST, NEVER THE FILE HASH -- shown on two serialisations of ONE graph.

    `before` is the arrived shape (semantics a string); `after` is the repair the spec asks for
    (semantics an object with K:12, the adjacency columns regenerated, keys re-serialised). The two
    are two file_sha256 values and ONE graph_digest. A spec pinned to the bytes would die on exactly
    the repair it asks for, which is why the pin is the digest.
    """
    canon = list(CANONICAL_NODES)
    F = {a: {b: (0 if a == b else (i + 1) * (j + 1) % 15 + 1) for j, b in enumerate(canon)}
         for i, a in enumerate(canon)}
    before = {"nodes": canon, "ged_fwd": F, "semantics": "Raw directed GED."}
    after = {"semantics": {"K": 12}, "ged_fwd": F, "nodes": canon,
             "adjacency_min_K": {a: neighbours(canon, F, "min", 12, a) for a in canon}}
    raw_b, raw_a = json.dumps(before, sort_keys=True).encode(), json.dumps(
        after, sort_keys=True).encode()
    sha_b, sha_a = file_sha256(raw_b), file_sha256(raw_a)
    dig_b = graph_digest(before["nodes"], before["ged_fwd"])
    dig_a = graph_digest(after["nodes"], after["ged_fwd"])
    digest_ok = dig_b == dig_a and len(dig_b) == 64
    bytes_ok = sha_b != sha_a
    ok = digest_ok and bytes_ok
    return ok, {"file_sha256_before": sha_b, "file_sha256_after": sha_a,
                "file_sha256_moves_with_the_repair": bytes_ok,
                "graph_digest_before": dig_b, "graph_digest_after": dig_a,
                "graph_digest_unchanged_by_the_repair": digest_ok,
                "repair": "semantics string -> object with K:12, adjacency_min_K added, keys "
                          "re-serialised",
                "pin": "graph_digest", "reading": "file_sha256", "pass": ok}


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
    bok, publish_rows = publish_test()
    qok, parse_rows = parse_test()
    iok, identity_rows = identity_test()
    nok, node_rows = node_order_test()
    gok, audit_rows = graph_audit_test()
    rok, pin_row = pin_rule_test()
    ok = (fsha == SELF_TEST_FILE_SHA and gdig == SELF_TEST_GRAPH_DIGEST and eok and aok and pok
          and bok and qok and iok and nok and gok and rok)
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
                      "publish": publish_rows, "publish_pass": bok,
                      "read_grammar": parse_rows, "parse_pass": qok,
                      "model_identity": identity_rows, "identity_pass": iok,
                      "node_order": node_rows, "node_order_pass": nok,
                      "graph_audit": audit_rows, "graph_audit_pass": gok,
                      "pin_rule": pin_row, "pin_rule_pass": rok,
                      "pass": ok}, indent=1))
    return 0 if ok else EXIT_SELF_TEST_FAIL


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

    # CANONICAL NAMES on purpose: admission is checked before the graph is loaded, so these
    # vectors never needed a loadable file -- but the CONTROL case walks past admission and does
    # load, and the canonical node order (exit 13) would refuse invented names. A control that
    # cannot reach the write path tests nothing.
    nodes = list(CANONICAL_NODES)
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
                              # a non-dry dispatch that NAMES a model but cannot state its weights:
                              # 11, not 2. The refusal moved code when the model path landed; the
                              # thing refused (a row about weights nothing named) did not move.
                              ("model_no_identity", ["--cap", "40", "--model", "dummy"],
                               EXIT_MODEL_IDENTITY),
                              # neither --model nor --dry-run: the direction the old condition
                              # left uncovered
                              ("no_model_no_dry", [], EXIT_BAD_ARGS),
                              # a dry run that names a model it never consults
                              ("dry_with_model", ["--cap", "2", "--dry-run", "--model", "dummy"],
                               EXIT_BAD_ARGS),
                              # ...and the same rule for the identity card, which exists only to
                              # say which weights answered
                              ("dry_with_identity",
                               ["--cap", "2", "--dry-run", "--model-identity", "card.json"],
                               EXIT_BAD_ARGS),
                              # the same flag given an empty value: `if model:` is a truthiness
                              # test on a string, so "" slipped through and wrote a row. The guard
                              # is the PRESENCE of the argument, not its content.
                              ("dry_empty_model", ["--cap", "2", "--dry-run", "--model", ""],
                               EXIT_BAD_ARGS),
                              # --seed-model is CONSUMED by the model path now, so under --dry-run
                              # the reason has changed but the refusal has not: no model answered,
                              # so no model seed. Presence, not truthiness -- 0 is refused like 7.
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


def admission_refusal(cap, model, dry_run, seed_model=None, out_dir=None, model_identity=None):
    """ADMISSION: refusals that are properties of the ARGUMENTS alone.

    None of these may live in the walk, and none may depend on the graph loading, the digest
    matching, or the out-dir's contents: a dispatch that cannot write a record has no business
    computing that record's slug or creating its directory, and a fabricated row that DOES get
    written then occupies the slug and turns the honest run for that cell into exit 7.

    The condition is the ARGUMENT, not the out-dir. `not dry_run and model is None` replaces the
    older blanket `not dry_run`: a non-dry dispatch is a MODEL's answer and there is no other
    instrument, so naming no model is still refused (2) -- but naming one is now the path that
    exists. `model` is still refused under --dry-run, because a dry run consults no model and a row
    naming one would state a basis the process never had; the same rule now covers --model-identity,
    whose only purpose is to say which weights answered.

    --seed-model is NO LONGER REFUSED as unimplemented: the model path sends it as the request seed
    and the row records it, which is what its old refusal said it was waiting for. Under --dry-run it
    is still refused, for the same reason as --model: nothing consulted a model, so a model seed is a
    setting the run never had.

    The identity CARD is a file, not an argument, so its contents are checked later (exit 11) -- but
    its ABSENCE is an argument fact and is refused HERE, at 11, before any path is named.
    """
    if cap < 1:
        return (EXIT_BAD_ARGS,
                f"--cap {cap}: a cell needs at least one ply, and cap < 1 never enters the walk, "
                f"so it can only produce a record of nothing (0 moves, tokens_total 0) that still "
                f"claims benchmark_row")
    if not dry_run and model is None:
        return (EXIT_BAD_ARGS,
                "a non-dry dispatch needs --model: a benchmark row is one model's answer per ply, "
                "and there is no other instrument. Refused at admission, before the slug is computed "
                "and before the out-dir is created. (A dry run is --dry-run.)")
    if model is not None and dry_run:
        return (EXIT_BAD_ARGS,
                f"--dry-run consults no model, so it will not record one: got --model {model!r}; "
                f"a dry-run row's model field is 'dry-run/none'")
    if model_identity is not None and dry_run:
        return (EXIT_BAD_ARGS,
                f"--dry-run consults no model, so it will not record a model's identity: got "
                f"--model-identity {model_identity!r}. A dry-run row names no weights because none "
                f"answered.")
    if seed_model is not None and dry_run:
        # Presence, not truthiness: --seed-model 0 is still a value the run never used. The test is
        # `is not None`, the same one the old unimplemented-flag refusal used -- only the reason has
        # changed, from "nothing reads it" to "nothing consulted a model to read it for".
        return (EXIT_BAD_ARGS,
                f"--seed-model {seed_model} under --dry-run: a dry run consults no model, so it has "
                f"no model seed and will not record one")
    if out_dir == "":
        # An empty path names no directory. Without this the dispatch reaches os.makedirs and dies
        # on FileNotFoundError with exit 1 and a traceback -- an unmapped code for a defect that is
        # a property of the argument alone, which is this function's whole remit.
        return (EXIT_BAD_ARGS,
                "--out-dir '': an empty path names no directory, so the record has nowhere to go. "
                "Refused at admission rather than raised out of os.makedirs.")
    if not dry_run and model_identity is None:
        return (EXIT_MODEL_IDENTITY,
                "a non-dry dispatch must name the weights that answered: spec §3 requires model id, "
                "quant, server_argv and server_binary_digest, and --model carries only the api id, "
                "which names NO quant. Missing: --model-identity. No record is written and no "
                "out-dir is created until the weights can be stated.")
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
    ap.add_argument("--expect-nodes-sha256", dest="expect_nodes_sha256", default=None,
                    help="pin the DECLARATION: sha256('\\n'.join(nodes) + '\\n') must equal this, "
                         "checked BEFORE graph_digest is computed and on --print-graph-digest too, "
                         "so the audit path cannot certify a wrongly-ordered file")
    ap.add_argument("--cell-spec", default=None, help="path to the frozen cell spec both boxes hash")
    ap.add_argument("--out-dir", default="probes")
    ap.add_argument("--dry-run", action="store_true",
                    help="no model: deterministic seeded walk, proves the plumbing only")
    ap.add_argument("--model", default=None,
                    help="API model id to play the cell. Required for a non-dry dispatch; the id "
                         "carries NO quant, so --model-identity must name the weights as well.")
    ap.add_argument("--model-identity", dest="model_identity", default=None,
                    help="JSON card naming the weights that answer (spec §3): api_model_id, quant, "
                         "server_argv, server_binary_digest. Required with --model; checked, not "
                         "believed.")
    ap.add_argument("--base-url", dest="base_url", default=DEFAULT_BASE_URL,
                    help=f"OpenAI-compatible endpoint for --model (default {DEFAULT_BASE_URL})")
    ap.add_argument("--no-think", dest="no_think", action="store_true",
                    help="decoder `thinking: off` -- sends reasoning_effort=none per turn. Without "
                         "it the decoder is `on`, the harness default, and nothing is sent.")
    ap.add_argument("--seed-model", dest="seed_model", type=int, default=None,
                    help="seed sent with every model turn; spec fixes it at 0")
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
        # THE AUDIT PATH IS THE ADMISSION PATH: the same call, the same checks, the same exits.
        # Before this revision this branch printed graph_digest 596255d9... and exited 0 for a file
        # no dispatch could load ("semantics" was a string; the dispatch died at exit 1).
        facts = validate_graph(a.graph, a.expect_graph_digest, a.expect_nodes_sha256)
        print(json.dumps(audit_report(facts), indent=1))
        return 0

    if not a.symmetrisation:
        die(EXIT_NO_SYMMETRISATION,
            "no --symmetrisation named. min/max/ged_fwd/ged_rev are four different graphs; "
            "the graph_digest alone does not pin the test, so this driver will not pick one for you.")

    if not a.rune:
        die(EXIT_BAD_ARGS, "--rune is required to run a cell")

    # ADMISSION, before the graph is loaded, before the slug is computed, before os.makedirs:
    # a dispatch that cannot write a record must never get far enough to name one.
    refusal = admission_refusal(a.cap, a.model, a.dry_run, a.seed_model, a.out_dir,
                                a.model_identity)
    if refusal:
        die(*refusal)

    # THE MODEL'S IDENTITY, before any path is named. A dispatch whose weights cannot be stated must
    # not create an out-dir or occupy a slug -- what it would write there is not a benchmark row.
    ident: dict = {}
    seed_model = None
    if not a.dry_run:
        checked, refusal = verify_model_identity(a.model_identity, a.model)
        if refusal:
            die(*refusal)
        assert checked is not None
        ident = checked
        refusal = preflight_models(a.base_url, a.model)
        if refusal:
            die(*refusal)
        # Spec §1 fixes seed_model at 0. Not naming it is not a different run, it is the same value
        # unstated -- and now that the model path READS it, defaulting is honest. The old refusal
        # existed because the value was dropped while the slug could not tell two dispatches apart.
        seed_model = 0 if a.seed_model is None else a.seed_model

    # THE ONE GRAPH VALIDATION PATH, shared with --print-graph-digest: structural (3), canonical
    # node order (13), start rune (2), derivation columns (6), digest comparison (5). No graph
    # defect can reach a traceback any more, and the audit path cannot certify what this refuses.
    facts = validate_graph(a.graph, a.expect_graph_digest, a.expect_nodes_sha256, a.rune)
    raw, g, nodes, F = facts["raw"], facts["g"], facts["nodes"], facts["F"]
    fsha = facts["file_sha256"]
    gdig = facts["graph_digest"]
    cells_checked = facts["derivation_columns_checked"]
    K = a.K if a.K is not None else facts["graph_K"]

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
    # its basis beside it (edges_used_basis) -- not derived from a symmetry assumption. The ARM is
    # written beside the number as well (edges_used_arm) and again in one quotable string
    # (edges_used_statement), because edges_used is arm-dependent: a count that travels without its
    # arm is a value without its basis, and the four arms differ by up to 57 edges on this graph.
    ec = edge_counts(nodes, F, a.symmetrisation, K)
    ec_named = {
        "edges_used": ec["edges_used"],
        "edges_used_arm": a.symmetrisation,
        "edges_used_basis": ec["edges_used_basis"],
        "edges_used_statement": (f"edges_used={ec['edges_used']} "
                                 f"(basis={ec['edges_used_basis']}, arm={a.symmetrisation})"),
        "edges_directed": ec["edges_directed"],
        "edges_undirected_pairs": ec["edges_undirected_pairs"],
        "edges_one_way": ec["edges_one_way"],
    }

    # THE NAME OF THE RECORD IS THE IDENTITY OF THE DISPATCH. The dry slug is UNCHANGED (records
    # already published under it are still the same test); the model slug leads with the model,
    # because that is the field a reader sorts by, and carries the decoder pair and seed_model,
    # because two runs that differ in either are two measurements and must not collide on exit 7.
    if a.dry_run:
        slug = (f"DRYRUN_{a.symmetrisation}-K{K}-{a.rune}-cap{a.cap}-seed{a.seed}"
                f"-{gdig[:8]}{'-cellspec' + cell_sha[:8] if cell_sha else ''}.json")
    else:
        slug = (f"{slug_part(a.model)}-{a.symmetrisation}-K{K}-{a.rune}-cap{a.cap}-seed{a.seed}"
                f"-sm{seed_model}-{'nothink' if a.no_think else 'think'}"
                f"-{gdig[:8]}{'-cellspec' + cell_sha[:8] if cell_sha else ''}.json")
    out_path = os.path.join(a.out_dir, slug)
    # THE OUT-DIR IS NOW A MAPPED FACT, NOT A TRACEBACK. Measured on this box, all three shapes come
    # out of os.makedirs as raw OSErrors a second machine cannot key on:
    #     FileExistsError     [Errno 17] --out-dir names an existing FILE
    #     NotADirectoryError  [Errno 20] --out-dir has a FILE in its middle, e.g. <file>/sub
    #     PermissionError     [Errno 13] -- the directory exists and refuses a file
    # So the guard covers BOTH os.makedirs AND everything that writes into the directory: the probe
    # below (which creates a real file) and the publish at the end. It sits AFTER admission on
    # purpose -- an admitted dispatch with a bad out-dir is a different fact from a refused
    # dispatch, and admission refusals keep their own codes.
    try:
        if os.path.exists(out_path):
            die(EXIT_RECORD_EXISTS,
                f"{out_path} already exists; a record you did not take is not yours to overwrite")
        os.makedirs(a.out_dir, exist_ok=True)
        # Decided HERE, before the walk, and recorded in the row: the tier is a property of the
        # directory, so it is knowable before a single ply is played -- and a directory that cannot
        # hold a record must not cost a model 40 turns.
        publish = probe_publish_tier(out_path)
    except OSError as e:
        die(EXIT_OUT_DIR_UNUSABLE,
            f"--out-dir {a.out_dir!r} cannot hold a record: {type(e).__name__} "
            f"[Errno {e.errno}] {e.strerror or e}. No record was written.")

    if a.dry_run:
        # THE DRY WALK: a seeded random step over the SAME legal set the model will face. Plumbing,
        # not data -- and named DRYRUN_ so it cannot be mistaken for a row about a model. The random
        # step is not a stand-in for a model here: it is the control that proves the maze is walkable.
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
            nxt = nb[rng.randrange(len(nb))]
            moves.append({"ply": plies, "from": cur, "to": nxt, "legal_moves": len(nb)})
            tokens.append(None)
            cur = nxt
            visited.append(cur)
            plies += 1
    else:
        # THE MODEL WALK: proposal -> parse -> legal-move check, one turn per ply. No randomness and
        # no fallback step: if the model cannot answer, the row records what it did instead of
        # substituting a move the model never made.
        w = model_walk(nodes, F, a.symmetrisation, K, a.rune, a.cap, ident, a.base_url,
                       a.no_think, seed_model)
        cur, visited, moves, tokens = w["cur"], w["visited"], w["moves"], w["tokens"]
        blocked, not_an_action, give_up = w["blocked"], w["not_an_action"], w["give_up"]
        end_state, plies = w["end_state"], w["plies"]

    pos_of, alias_all = position_index(nodes, F)
    alias_multi = [grp for grp in alias_all if len(grp) > 1]
    visited_names = len(set(visited))
    visited_positions = len({pos_of[a] for a in visited})

    rec = {
        "schema": "labyrinth-run/2",
        "dry_run": bool(a.dry_run),
        "benchmark_row": not a.dry_run,
        "driver": {"path": SELF, "sha256": hashlib.sha256(open(SELF, "rb").read()).hexdigest()},
        # HOW this record reached its name, beside the machine-readable basis fields above it in
        # spirit: link-exclusive / excl-claim / replace-no-exclusive-support. Probed before the
        # walk and then USED, so it names the mechanism this run invoked rather than what the
        # filesystem was thought capable of. A reader comparing two boxes can see whether the
        # exclusivity held, instead of assuming every `exit 7` came from the same guarantee.
        "publish": publish,
        # THE PINNED IDENTITY OF THE TEST. graph_digest, never file_sha256: measured on the arrived
        # file, repairing `semantics` and regenerating the adjacency columns leaves graph_digest at
        # 596255d9... while file_sha256 moves off ea33eedc.... A spec pinned to the bytes would die
        # on exactly the repair it asks for, so the pin travels here, named, in every row.
        "pinned_identity": {"field": "graph_digest", "value": gdig},
        "pinned_identity_rule": ("pin the GRAPH DIGEST, never the FILE HASH: graph_digest is the "
                                 "identity of the test; file_sha256 is transport evidence about "
                                 "the bytes and moves with a repair that leaves the test unchanged"),
        # MODEL IDENTITY, spec §3, four fields and none substitutable. On a dry run all four are null
        # and the model field says 'dry-run/none' -- a dry row is plumbing and may not name weights.
        "model": "dry-run/none" if a.dry_run else ident["api_model_id"],
        "model_quant": None if a.dry_run else ident["quant"],
        "model_file": None if a.dry_run else ident["model_file"],
        "server_argv": None if a.dry_run else ident["server_argv"],
        "server_binary_digest": None if a.dry_run else ident["server_binary_digest"],
        "server_binary_path": None if a.dry_run else ident["server_binary_path"],
        # WHERE it was asked, and WHICH DECODER answered. decoder_mode is the spec's pair (on|off):
        # 'off' sent reasoning_effort=none, 'on' sent nothing because on IS the harness default. The
        # exact control travels beside the label so the label is checkable rather than trusted.
        "model_endpoint": None if a.dry_run else a.base_url.rstrip("/"),
        "decoder_mode": "none" if a.dry_run else ("off" if a.no_think else "on"),
        "thinking": None if a.dry_run else (not a.no_think),
        "decoder_control": (None if a.dry_run or not a.no_think
                            else {"reasoning_effort": "none"}),
        "max_turn_tokens": None if a.dry_run else MAX_TURN_TOKENS,
        "prompt_digest": (None if a.dry_run
                          else hashlib.sha256(PROMPT_TEMPLATE.encode()).hexdigest()),
        "prompt_template": None if a.dry_run else PROMPT_TEMPLATE,
        "read_grammar": (None if a.dry_run else
                         "one rune name alone on the first non-empty line, case-insensitive, "
                         "surrounding quotes/backticks stripped; one of the eight abstention tokens "
                         "= give_up; anything else = not_an_action, never truncated"),
        "seed": a.seed,
        "seed_model": seed_model,
        "cap": a.cap,
        "graph": {
            "path": os.path.abspath(a.graph),
            "file_sha256": fsha,
            "file_sha256_role": "transport evidence about the bytes; NEVER the identity of the test",
            "graph_digest": gdig,
            "graph_digest_pinned": True,
            "graph_digest_algorithm": "sha256(ged-v2: header 'ged-v2\\n', then for each node a in the "
                                      "file's 'nodes' ARRAY in array order: a + '\\t' + "
                                      "','.join(str(int(ged_fwd[a][y])) for y in array order) + '\\n')",
            "graph_digest_node_order": "nodes array (NOT ged_fwd key order)",
            # THE DECLARATION, pinned by the rune set rather than by the matrix: the order check
            # refuses anything else (exit 13), so these two are equal in every row that exists.
            "nodes_sha256": facts["nodes_sha256"],
            "canonical_nodes_sha256": CANONICAL_NODES_SHA256,

            "nodes": len(nodes),
            "positions": len(alias_all),
            "alias_groups": alias_multi,
            "symmetrisation": a.symmetrisation,
            "K": K,
            "derivation_columns_checked": cells_checked,
            "derivation_basis": ("shipped adjacency_*_K columns compared with the matrix at the "
                                 "graph's K; 0 means the file carries no such column, NOT that "
                                 "the columns agreed"),
            **ec_named,
        },
        "cell_spec_sha256": cell_sha,
        "start_rune": a.rune,
        "end_rune": cur,
        "moves": moves,
        "plies": plies,
        "blocked": blocked,
        "not_an_action": not_an_action,
        "give_up": give_up,
        "counts_basis": (None if a.dry_run else
                         "per turn: moved = a proposal in the legal set; blocked = a named rune that is "
                         "not a legal move from here, or a position with no legal move; give_up = an "
                         "abstention token (the cell ends); not_an_action = anything the read grammar "
                         "could not read"),
        "ended": end_state != "cap" or plies >= a.cap,
        "end_state": end_state,
        "tokens_per_turn": tokens,
        "tokens_total": None if a.dry_run else sum(tokens),
        "tokens_basis": (None if a.dry_run else
                         "usage.completion_tokens per turn; tokens_total is their sum"),
        "visited_unique": visited_positions,
        "visited_names": visited_names,
        "visited_count_basis": "positions",
    }
    payload = json.dumps(rec, indent=1) + "\n"
    try:
        # The guard covers the WHOLE publish -- open, write, flush and close -- because the record
        # fits the 8 kB text buffer and the failure therefore surfaces at the close, not at
        # write(). Exit 7 comes out of publish_record as SystemExit and is not touched by this.
        publish_record(out_path, payload, publish)
    except OSError as e:
        die(EXIT_OUT_DIR_UNUSABLE,
            f"the record could not be published into {a.out_dir!r}: {type(e).__name__} "
            f"[Errno {e.errno}] {e.strerror or e}. publish={publish}; no record was written and any "
            f"temp has been removed.")
    print(json.dumps({"record": out_path, "publish": publish,
                      "end_state": end_state, "plies": plies,
                      "end_rune": cur, "unique_positions": visited_positions,
                      "unique_names": visited_names,
                      "model": rec["model"], "decoder_mode": rec["decoder_mode"],
                      "seed_model": seed_model, "tokens_total": rec["tokens_total"],
                      "blocked": blocked, "not_an_action": not_an_action, "give_up": give_up,
                      "graph_digest": gdig, "pinned_identity": rec["pinned_identity"],
                      "file_sha256": fsha, "file_sha256_role": rec["graph"]["file_sha256_role"],
                      "symmetrisation": a.symmetrisation, "K": K,
                      "derivation_columns_checked": cells_checked,
                      # the count with its arm and basis beside it, so a one-line summary cannot
                      # be quoted as a bare number either
                      "edges_used": ec_named["edges_used"],
                      "edges_used_arm": ec_named["edges_used_arm"],
                      "edges_used_basis": ec_named["edges_used_basis"],
                      "edges_used_statement": ec_named["edges_used_statement"],
                      "edges_directed": ec_named["edges_directed"],
                      "edges_undirected_pairs": ec_named["edges_undirected_pairs"],
                      "edges_one_way": ec_named["edges_one_way"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
