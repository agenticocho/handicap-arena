#!/usr/bin/env python3
"""THE FIELD CENSUS HAS AN ENFORCER -- the package is compared with the WRITER, by ast, in both directions.

WHY THIS EXISTS. `SOKOBAN_CONFORMANCE_PACKAGE.md` carries a census of the record's field names, and
`make_conformance_package.py` carries a second one (`FORMAT`). NEITHER HAD EVER BEEN COMPARED WITH THE CODE
THAT WRITES THE FIELDS. MEASURED (card `t_8dc430a7`, results root `cabinet_results/t_8dc430a7/`): the census
names 70 names; three carriers written by the driver carry 77; 13 are NEVER NAMED BY IT. And the drift began
THREE MINUTES after the census was last derived -- `6d77696` at 2026-10-10 09:17:35, `entrant_digest` landing
in `3923a52` at 09:20:01. Nothing has compared the two in the eight days since.

A READING IS DATED AND A TOOL CANNOT BE EXTENDED BY A DOCUMENT EDIT, so what was needed was not another
reading of the record (three were already taken) but a check that reads THE WRITER: the dict literals that
OWN the fields, by `ast`, and compares them with what the package publishes. That is this file.

WHAT IT READS, AND IT READS EVERY CARRIER OF A NAME THE WRITER USES:

  1  A DICT LITERAL, identified by the keys that can only be that literal -- `(file, function, required keys)`.
     A literal that cannot be found is a MISS and this check FAILS, because a reader that skips what it
     cannot find reports clean for the same reason a dead probe reports success (the defect the package's
     own §2 already documents about itself).
  2  A SPREAD -- `**binary_provenance()` -- resolved to the CALLEE's returned dict literal TOO. Three of the
     names this check exists for (`server_binary_digest`, `_digest_scope`, `_source`) reach the record only
     through a spread, so a reader that stops at the literal misses exactly the newest instrument fields.
  3  A SUBSCRIPT ASSIGNMENT -- `r["ended_why"] = ...`, `r["artifact_replaced"] = ...`. TWO NAMES THE RECORD
     CARRIES ARE NEVER KEYS OF ANY LITERAL, so a literal-only reader is blind to them BY CONSTRUCTION.
  4  A `dict(meta, cells=..., unreadable_note=...)` CALL -- the run record's write-time keys are keywords of
     a call, not members of a literal.

AND WHAT IT DOES WITH WHAT IT FINDS -- THREE CLASSIFICATIONS, NAMED AND DECLARED BELOW, NOT INFERRED SILENTLY:

  BLOCK_BY_REFERENCE  a name whose VALUE is a nested block (`config`, `dead_end`, `host`, ...). The census
                      lists such a name BY NAME at its parent's level and its keys live in the block's own
                      block; so it is RESOLVED by expansion rather than counted as drift in either direction.
  CONDITIONAL         a name the writer emits only on a named execution path (`dead_end`'s proven/unknown
                      branches, the load-failure returns, a replacement, a confounded cell). Absence from one
                      carrier is BY DESIGN. EVERY conditional name must be DECLARED here with its condition:
                      an undeclared one is UNCLASSIFIED and this check FAILS (rc 3), because a classification
                      that is not enforced is decoration, and the next conditional name would arrive
                      unexplained exactly the way the last thirteen did.
  LOCAL               a name the LOCAL/FORMAT split assigns to the local bookkeeping. It is in the package
                      and is NOT required to be in `LIST 1`; it IS still required to be a name the writer
                      emits (a LOCAL name nobody emits is drift like any other).

THE TWO DIRECTIONS, BOTH ENFORCED:

  EMITTED AND UNNAMED     a name the writer emits that the package does not carry anywhere
  NAMED AND UNEMITTED     a name the package carries that the writer does not emit

    python3 check_conformance_census.py [--root DIR] [--package PATH] [--split PATH]

rc 0 no unclassified drift      rc 1 DRIFT      rc 2 THE CHECK COULD NOT READ (a miss, not a pass)
rc 3 A CONDITIONAL NAME IS NOT CLASSIFIED

THE POSITIVE CONTROL IS SEPARATE AND IT IS NOT OPTIONAL: `check_conformance_census_control.py` injects a name
into a COPY of the package and removes one from a COPY of the writer, and watches this check fail naming both.
A check that cannot fail is a resolution, not a mechanism -- which is the finding this file exists to answer.
"""
import ast
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WRITERS = ("sokoban.py", "sokoban_run.py", "sokoban_batch.py")
PACKAGE = "SOKOBAN_CONFORMANCE_PACKAGE.md"
SPLIT = "make_conformance_package.py"

# ==================================================================================================
# THE WRITER'S SITES -- DECLARED BY (block, file, function, keys that can only be that literal, condition).
#
# `req` is a set that must be CONTAINED in the literal's keys. It is a fingerprint, not a filter: the keys
# reported are the literal's OWN keys, whatever they are. A site that cannot be found is a MISS (rc 2).
# ==================================================================================================
SITES = [
    # block,                    file,               func,                 req (fingerprint),                  condition
    ("CELL COUNTERS", "sokoban.py", "play", {"solved", "final_board", "trace"},
     None),
    ("CELL RECORD", "sokoban_run.py", "run", {"entrant", "config", "dead_end"},
     None),
    ("CELL RECORD", "sokoban_run.py", "run", {"entrant", "loaded"},
     "only on a LOAD FAILURE: the server exited or never answered /health, so the run returned before "
     "the first turn"),
    ("CONFIG BLOCK", "sokoban_run.py", "run", {"reasoning_argv", "server_argv"},
     None),
    ("REASONING PROBE", "sokoban_run.py", "probe_reasoning", {"answer_from_reasoning_field"},
     None),
    ("REASONING PROBE", "sokoban_run.py", "probe_reasoning", {"error"},
     "only when the probe could not be asked at all: the endpoint raised instead of answering"),
    ("BUDGET SIGNATURE", "sokoban_run.py", "budget_signature", {"turns_that_hit_the_ceiling"},
     None),
    ("DEAD-END CELL", "sokoban_run.py", "dead_end_verdict", {"no_solution_from_here"},
     "the PROVEN branches: a dead end, or a live position -- both need a complete enumeration"),
    ("DEAD-END CELL", "sokoban_run.py", "dead_end_verdict", {"why"},
     "only on the branches that never checked: no tokens produced, or the first token was not an action"),
    ("RUN RECORD", "sokoban_batch.py", "main", {"run_id", "simulator_digest"},
     None),
    ("RUN RECORD", "sokoban_batch.py", "write", {"cells", "unreadable_note"},
     None),
    ("RUN RECORD", "sokoban_batch.py", "main", {"dead_end_verifier"},
     None),
    ("RUN RECORD", "sokoban_batch.py", "main", {"nvidia_smi"},
     None),
    ("LOAD FAILURE", "sokoban_run.py", "load_failure", {"load_failure_class"},
     "only on a LOAD FAILURE, and the class differs per branch (file refusal / unreadable log / no cause "
     "named)"),
    ("ARTIFACT REPLACED", "sokoban_run.py", "artifact_gate", {"reason_given"},
     "only when a run REPLACED a record it did not take, which requires --overwrite-artifact"),
]

# SUBSCRIPT ASSIGNMENTS ONTO THE RECORD -- names that are never keys of any literal.
SUBSCRIPT_SITES = [
    # block,             file,             func,  var,   key,                  condition
    ("CELL RECORD", "sokoban_run.py", "run", "r", "ended_why",
     "only on a confounded cell: every command was an empty answer the HARNESS produced"),
    ("CELL RECORD", "sokoban_run.py", "main", "r", "artifact_replaced",
     "only when a run REPLACED a record it did not take, which requires --overwrite-artifact"),
]

# ==================================================================================================
# THE CLASSIFICATIONS. DECLARED, SO THEY CAN BE CHECKED RATHER THAN BELIEVED.
# ==================================================================================================

# A name whose VALUE is a nested block: the census names it at its parent's level and its keys live in the
# block's own block. RESOLVED BY EXPANSION, never counted as drift.
BLOCK_BY_REFERENCE = {
    "config", "reasoning_probe", "budget_signature", "dead_end", "turns",
    "host", "freeze", "levels", "cells", "artifact_replaced",
}
# ...and the four of those whose keys are ANOTHER DECLARED SITE'S BLOCK, so they are read THERE and not again
# at the parent's level.
BLOCK_REF_HAS_OWN_SITE = {"config", "reasoning_probe", "budget_signature", "dead_end"}

# WHICH WRITER BLOCK A DOTTED NAME'S PARENT LIVES IN. A dotted package name (`config.legend`,
# `artifact_replaced.path`, `reasoning_probe.error`) is resolved THROUGH THE BLOCK STRUCTURE rather than at its
# leaf: resolving by leaf alone would let the cell record's `legend` answer for the config block's, which is a
# different field that happens to share a name.
BLOCK_OWNER = {"config": "CONFIG BLOCK", "reasoning_probe": "REASONING PROBE",
               "budget_signature": "BUDGET SIGNATURE", "dead_end": "DEAD-END CELL",
               "host": "RUN RECORD", "freeze": "RUN RECORD", "artifact_replaced": "ARTIFACT REPLACED"}

# EVERY name the writer emits ONLY on a conditional path. An undeclared conditional name is rc 3.
CONDITIONS = {
    "why": "only on a LOAD FAILURE, and only on the dead-end branches that did not check -- the same KEY "
           "on two blocks, and the census names it on neither",
    "load_failure_class": "only on a LOAD FAILURE",
    "error": "only when the reasoning probe could not be asked at all",
    "ended_why": "only on a confounded cell (every command a harness-produced empty)",
    "artifact_replaced": "only when a run replaced a record it did not take",
    "no_solution_from_here": "only on the branches that CHECKED (proven dead end, or proven live)",
    "still_solvable_in": "only on a cell proven NOT a dead end",
    "proof_kind": "only on a cell proven a dead end",
    "proof_rule": "only on a cell proven a dead end",
    "reachable_states_enumerated": "only on a cell proven a dead end",
    "states_expanded": "only on a cell proven a dead end",
    "unknown": "only where the enumeration could not decide",
    "budget": "only where the enumeration ran out of budget",
    "checked": "the dead-end verdict is IN every cell, but every one of its returns is a BRANCH (False where "
               "the verdict never ran, True where the enumeration ran), so its keys are branch-shaped",
    "first_action": "only on the branches where a first token existed -- not on the empty-answer branch",
}
# ==================================================================================================
# THE CENSUS -- the package's own §2 blocks, and the split's LIST 1 / LIST 2 in both of their carriers.
# ==================================================================================================
CENSUS_HEADERS = ["CELL COUNTERS", "CELL RECORD", "CONFIG BLOCK", "REASONING PROBE", "BUDGET SIGNATURE",
                  "DEAD-END CELL", "RUN RECORD"]
NAME = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)?$")


def _fail(msg, code=2):
    print(f"  *** {msg}")
    return code


# ---------------------------------------------------------------------------------- the writer, by ast
def enclosing(tree):
    """node id -> the name of the function it sits in (None at module level)."""
    out = {}

    def walk(node, fn):
        for child in ast.iter_child_nodes(node):
            name = child.name if isinstance(child, ast.FunctionDef) else fn
            out[id(child)] = name
            walk(child, name)
    out[id(tree)] = None
    walk(tree, None)
    return out


def literal_keys(node):
    """-> (keys: [str], spreads: [(lineno, callee_name, ast_node)]) for a Dict literal.

    `**expr` has key None. A spread to a CALL is followed to the callee's own returned literal; any other
    spread is reported so THIS READER can be seen to be incomplete rather than quietly short.
    """
    keys, spreads = [], []
    for k, v in zip(node.keys, node.values):
        if k is None:
            if isinstance(v, ast.Call) and isinstance(v.func, ast.Name):
                spreads.append((node.lineno, v.func.id, v))
            else:
                spreads.append((node.lineno, "UNREADABLE SPREAD: " + ast.unparse(v)[:60], v))
        elif isinstance(k, ast.Constant) and isinstance(k.value, str):
            keys.append(k.value)
        else:
            keys.append("UNREADABLE KEY: " + ast.unparse(k)[:40])
    return keys, spreads


def call_keywords(node):
    """-> (kw names, [positional Names]) for a `dict(...)` call: `dict(meta, cells=...)`."""
    kw = [(k.arg if k.arg else "UNREADABLE KW: " + ast.unparse(k.value)[:40]) for k in node.keywords]
    pos = [a.id if isinstance(a, ast.Name) else "UNREADABLE POS: " + ast.unparse(a)[:40]
           for a in node.args]
    return kw, pos


def returned_literal(fn_node):
    """-> the Dict literal a function returns, or None. One level, on purpose: a reader that cannot resolve
    a spread must say so, not guess."""
    for n in ast.walk(fn_node):
        if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict):
            return n.value
    return None


def read_writer(root):
    """-> (sites, misses, boundary) where sites = {block: {name: {"at": "file:line", "conds": [cond]}}}.

    A name is TAGGED with the condition of EVERY literal that carries it, so the CONDITIONAL rule is applied
    to something measured rather than to a list somebody remembered to update.

    `boundary` names what this check DOES NOT READ: the inner shape of a block-by-reference name whose value
    is a variable rather than a literal. It is reported rather than left implicit, because "not read" and
    "read and clean" must never print the same way.
    """
    funcs, trees, enc = {}, {}, {}
    for fn in WRITERS:
        path = os.path.join(root, fn)
        if not os.path.exists(path):
            return None, [f"the writer {fn} is not there"], set()
        src = open(path, encoding="utf-8").read()
        trees[fn] = ast.parse(src)
        enc[fn] = enclosing(trees[fn])
        funcs[fn] = {n.name: n for n in ast.walk(trees[fn]) if isinstance(n, ast.FunctionDef)}

    sites, misses, boundary = {}, [], set()
    for block, fn, fname, req, cond in SITES:
        if fname not in funcs[fn]:
            misses.append(f"SITE ({block}) {fn}:{fname}() -- the function is GONE. Fix this reader.")
            continue
        hits = []
        for node in ast.walk(funcs[fn][fname]):
            # ONLY literals that BELONG to this function: a nested def's literal is a different block.
            if isinstance(node, ast.Dict) and enc[fn].get(id(node)) == fname:
                keys, spreads = literal_keys(node)
                if req <= set(keys):
                    hits.append((node.lineno, keys, spreads, node))
            elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict"
                  and enc[fn].get(id(node)) == fname):
                # THE RUN RECORD'S WRITE-TIME KEYS ARE KEYWORDS OF A CALL, NOT MEMBERS OF A LITERAL:
                # `dict(meta, cells=..., never_started=..., unreadable=..., unreadable_note=...)`. A reader
                # that only walks Dict literals reads that record as having lost four of its fields.
                kw, pos = call_keywords(node)
                keys, spreads = list(kw), []
                for name in pos:
                    assign = None
                    # THE ASSIGNMENT IS OFTEN NOT IN THIS FUNCTION: `dict(meta, ...)` sits in `write()`,
                    # a nested closure, while `meta = {...}` is one frame out in `main()`. A reader that
                    # only looks inside the caller reports a miss for a field that is right there.
                    for n2 in ast.walk(trees[fn]):
                        if (isinstance(n2, ast.Assign)
                                and any(getattr(t, "id", None) == name for t in n2.targets)
                                and isinstance(n2.value, ast.Dict)):
                            assign = n2
                    if assign is not None:
                        k2, s2 = literal_keys(assign.value)
                        keys, spreads = keys + k2, spreads + s2
                    else:
                        misses.append(f"dict(...) positional {name!r} at {fn}:{node.lineno} is not an "
                                      f"assignment to a dict literal this reader can read. A MISS, NOT A PASS.")
                if req <= set(keys):
                    hits.append((node.lineno, keys, spreads, node))
        if not hits:
            misses.append(f"SITE ({block}) {fn}:{fname}() -- no literal carries {sorted(req)}. "
                          f"A MISS, NOT A PASS: fix this reader.")
            continue
        for lineno, keys, spreads, node in hits:
            got = keys
            for sl, callee, _ in spreads:
                if callee in funcs[fn]:
                    lit = returned_literal(funcs[fn][callee])
                    if lit is not None:
                        got = got + literal_keys(lit)[0]
                        continue
                misses.append(f"SPREAD into {fn}:{sl} ({callee}) could not be resolved to a returned dict "
                              f"literal. A MISS, NOT A PASS.")
            # ---- WHAT THIS CHECK DOES NOT READ, NAMED RATHER THAN LEFT IMPLICIT.
            # A BLOCK-BY-REFERENCE name's VALUE is a nested block. Where that value is a LITERAL the block's
            # keys are read as a sub-block; where it is a VARIABLE (`turns`, `levels`, `cells` are built before
            # the record is assembled) this check CANNOT read it, and it says so instead of reporting clean.
            inner = {}
            if isinstance(node, ast.Dict):
                for k, v in zip(node.keys, node.values):
                    if isinstance(k, ast.Constant) and k.value in BLOCK_BY_REFERENCE:
                        if k.value in BLOCK_REF_HAS_OWN_SITE:
                            # ITS KEYS ARE ANOTHER DECLARED SITE'S BLOCK (`config` -> CONFIG BLOCK, and the
                            # same for the probe, the budget signature and the dead-end verdict). Expanding
                            # it here would name every one of those keys TWICE, at two levels, and a census
                            # that names a field twice is a census that can disagree with itself.
                            continue
                        if isinstance(v, ast.Dict):
                            inner[k.value] = literal_keys(v)[0]
                        elif isinstance(v, ast.List) and all(isinstance(e, ast.Dict) for e in v.elts):
                            inner[k.value] = [n for e in v.elts for n in literal_keys(e)[0]]
                        else:
                            boundary.add(f"{fn}:{lineno} {k.value} <- its value is a "
                                         f"{type(v).__name__}, not a literal this check can read")
            for name in got:
                at = f"{fn}:{lineno}"
                entry = sites.setdefault(block, {}).setdefault(name, {"at": at, "conds": []})
                # EVERY literal that carries the name records ITS condition. A name is CONDITIONAL only if
                # EVERY literal that carries it is -- so the classification is computed from the writer and
                # not from a table somebody remembered to update.
                entry["conds"].append(cond)
            for parent, kids in inner.items():
                for kid in kids:
                    sites.setdefault(block, {}).setdefault(f"{parent}.{kid}",
                                                           {"at": f"{fn}:{lineno}", "conds": []})
                    sites[block][f"{parent}.{kid}"]["conds"].append(cond)

    for block, fn, fname, var, key, cond in SUBSCRIPT_SITES:
        found = False
        for node in ast.walk(funcs[fn].get(fname, ast.Pass())):
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Subscript)
                    and isinstance(node.targets[0].value, ast.Name)
                    and node.targets[0].value.id == var
                    and isinstance(node.targets[0].slice, ast.Constant)
                    and node.targets[0].slice.value == key
                    and enc[fn].get(id(node)) == fname):
                sites.setdefault(block, {})[key] = {"at": f"{fn}:{node.lineno}", "conds": [cond]}
                found = True
        if not found:
            misses.append(f"SUBSCRIPT ({block}) {fn}:{fname}() {var}[{key!r}] = ... -- not found. "
                          f"A MISS, NOT A PASS.")
    return sites, misses, boundary


# ------------------------------------------------------------------ the package: census, split, doc lists
def read_census(root):
    """-> {header: [(name, ...)]} out of the package's §2 fenced blocks. A header not found is a MISS."""
    path = os.path.join(root, PACKAGE)
    if not os.path.exists(path):
        return None, [f"{PACKAGE} is not there"]
    text = open(path, encoding="utf-8").read()
    out, misses = {}, []
    for header in CENSUS_HEADERS:
        m = re.search(r"\*\*" + re.escape(header) + r"[^\n]*\*\*[^\n]*\n(.*?)```(.*?)```", text, re.S)
        if not m:
            misses.append(f"CENSUS BLOCK {header!r} -- the header is GONE, so nothing was read for it. "
                          f"A MISS, NOT A PASS.")
            continue
        names = []
        for line in m.group(2).splitlines():
            line = line.split("<-")[0]
            names += [t for t in line.replace("::", " ").split() if NAME.match(t)]
        out[header] = names
    return out, misses


def read_split(root):
    """-> (format_names, local_names, misses) from `make_conformance_package.py`, BY ast.

    Read by ast rather than by import: importing a check runs it, and a list read out of a running program
    is a list that can be produced by anything. The literal is the record.
    """
    path = os.path.join(root, SPLIT)
    if not os.path.exists(path):
        return None, None, [f"{SPLIT} is not there"]
    tree = ast.parse(open(path, encoding="utf-8").read())
    fmt, local, misses = None, None, []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if getattr(t, "id", None) == "FORMAT":
                try:
                    fmt = [n for _g, names in ast.literal_eval(node.value) for n in names]
                except ValueError:
                    misses.append("FORMAT is not a literal this reader can read -- fix the reader.")
            elif getattr(t, "id", None) == "LOCAL":
                try:
                    # A PATH: a 1-tuple is a TOP-LEVEL local field (`why`), a 2-tuple a field inside a block.
                    local = [".".join(pair) for pair in ast.literal_eval(node.value)]
                except ValueError:
                    misses.append("LOCAL is not a literal this reader can read -- fix the reader.")
    if fmt is None:
        misses.append("FORMAT not found in the split -- a MISS, NOT A PASS.")
    if local is None:
        misses.append("LOCAL not found in the split -- a MISS, NOT A PASS.")
    return fmt, local, misses


def read_doc_lists(root):
    """-> (LIST 1 names, LIST 2 names) as PUBLISHED, so the doc and the script cannot drift apart.

    LIST 1 is a two-column block: a GROUP HEADER starts at column 0, its names follow in the same column
    (`IDENTITY   run_id  entrant ...`) and CONTINUE on indented lines. The header is not a name; the indented
    lines carry names only. Read by that structure rather than by a guess at the first token.
    """
    text = open(os.path.join(root, PACKAGE), encoding="utf-8").read()
    one = re.search(r"### LIST 1[^\n]*\n(.*?)```(.*?)```", text, re.S)
    two = re.search(r"### LIST 2[^\n]*\n(.*?)```(.*?)```", text, re.S)
    l1 = []
    if one:
        for line in one.group(2).splitlines():
            if not line.strip():
                continue
            parts = re.split(r"\s{2,}", line.rstrip())
            if not line.startswith(" "):
                parts = parts[1:]                      # the first column is the GROUP HEADER
            l1 += [t for t in parts if NAME.match(t)]
    l2 = []
    if two:
        for line in two.group(2).splitlines():
            # AN ENTRY IN LIST 2 IS `path = what it is`. A line with no `=` is PROSE (the wrapped tail of the
            # previous entry) and carries no name; skipping it cannot hide a name, because a name that stops
            # being counted shows up as a carrier mismatch and FAILS the check rather than passing quietly.
            if "=" not in line:
                continue
            head = line.split("=")[0]
            l2 += [t for t in head.split() if NAME.match(t)]
    return l1, l2


# --------------------------------------------------------------------------------------------- the check
def main(argv):
    root, package = HERE, None
    for i, a in enumerate(argv):
        if a == "--root":
            root = os.path.abspath(argv[i + 1])
        elif a == "--package":
            package = argv[i + 1]
    if package:
        global PACKAGE
        PACKAGE = package
    print("=" * 100)
    print("THE FIELD CENSUS, COMPARED WITH THE WRITER THAT EMITS IT")
    print(f"  writer   : {', '.join(WRITERS)}")
    print(f"  package  : {PACKAGE}")
    print(f"  split    : {SPLIT}")
    print("=" * 100)

    sites, misses, boundary = read_writer(root)
    if sites is None:
        return _fail(misses[0])
    census, c_misses = read_census(root)
    if census is None:
        return _fail(c_misses[0])
    fmt, local, s_misses = read_split(root)
    misses += c_misses + s_misses

    if misses:
        print("\n  THE CHECK COULD NOT READ THESE -- A MISS IS NOT A PASS:")
        for m in misses:
            print(f"    {m}")
        return 2

    l1, l2 = read_doc_lists(root)
    # A NAME IS CONDITIONAL ONLY IF EVERY LITERAL THAT CARRIES IT -- IN ANY BLOCK -- IS. Measured off the
    # writer, so a name that gains an unconditional carrier stops being conditional without anyone editing
    # this check. (`reading` carries this: it is in the budget signature unconditionally and in the dead-end
    # verdict's branches, so it is NOT conditional, and a per-block test would have said it was.)
    conds_of = {}
    for b in sites:
        for n, m in sites[b].items():
            conds_of.setdefault(n, []).extend(m["conds"])
    conditional = {n for n, cs in conds_of.items() if all(c is not None for c in cs)}
    print("\n  THE WRITER, BLOCK BY BLOCK (read out of the source by ast):")
    for block in sorted(sites):
        tag = "" if block in CENSUS_HEADERS else "   <- NO CENSUS BLOCK NAMES THIS BLOCK"
        print(f"    {block:20s} {len(sites[block]):3d} names{tag}")
    print(f"    {'':20s} {sum(len(v) for v in sites.values()):3d} name/block pairs, "
          f"{len(conditional)} CONDITIONAL names (emitted on a named path only)")
    print(f"\n  NOT READ BY THIS CHECK, NAMED SO THAT 'NOT READ' CANNOT RENDER AS 'CLEAN' "
          f"({len(boundary)}):")
    for b in sorted(boundary):
        print(f"    {b}")

    # ---------- the package's names, as a set, with their carrier ----------
    named, provenance = {}, {}
    for block, names in census.items():
        for n in names:
            if n not in named or "census" not in provenance[n]:
                named.setdefault(n, set()).add(block)
                provenance.setdefault(n, set()).add("census")
    for n in (fmt or []) + (local or []):
        named.setdefault(n, set()).add("LIST 1" if n in (fmt or []) else "LIST 2")
        provenance.setdefault(n, set()).add("split")

    # ---- THE CONDITIONAL RULE, ENFORCED: a PACKAGE-NAMED name whose emission is conditional must be
    # DECLARED with its condition. An undeclared one is rc 3. It is checked against the package because
    # that is where it can do damage: a reader of a carrier sees the name absent and calls it drift.
    unclassified = sorted(n for n in conditional
                          if n.split(".")[-1] in named and n not in CONDITIONS)
    if unclassified:
        print("\n  A CONDITIONAL NAME IS NOT CLASSIFIED (rc 3):")
        for n in unclassified:
            at, why = "", ""
            for b in sorted(sites):
                if n in sites[b] and any(c is not None for c in sites[b][n]["conds"]):
                    at = sites[b][n]["at"]
                    why = next(c for c in sites[b][n]["conds"] if c)
                    break
            print(f"    {n:34s} {at:22s} emitted only on a conditional path ({why[:70]}...)")
            print(f"      {'':34s} and it is NAMED BY THE PACKAGE, so its absence from a carrier will be "
                  f"read as drift unless the condition is DECLARED in CONDITIONS.")
        return 3

    # ---------- DIRECTION 1: the writer emits it, the package does not carry it ----------
    emitted = {}
    for block, names in sites.items():
        for n, meta in names.items():
            emitted.setdefault(n, []).append((block, meta))

    def named_by_package(n, block):
        """A name is CARRIED BY THE PACKAGE if the package names it. THREE WAYS, because the two censuses were
        written in two notations and this check is the one that has to be indifferent to that, not the reader:

          * the name itself -- the census names a top-level field bare;
          * the LEAF of a dotted writer path, matched IN ITS OWN BLOCK, because a census names a SUB-BLOCK's
            keys bare under the block that owns them (`freeze :: simulator verifier ...`);
          * the DOTTED package name whose parent is the block the writer name lives in (`artifact_replaced.path`
            answers for the writer's `path` in ARTIFACT REPLACED and for nothing else).

        BLOCK-SCOPED ON PURPOSE: matching by leaf alone would let `config.legend` be satisfied by the cell
        record's `legend`, which is a different field that happens to share a name.
        """
        if n in named:
            return True
        if "." in n:
            return n.split(".")[-1] in census.get(block, [])
        return block in dotted_owner.get(n, ())

    dotted_owner = {}
    for _n in named:
        if "." in _n:
            _head, _tail = _n.rsplit(".", 1)
            if _head in BLOCK_OWNER:
                dotted_owner.setdefault(_tail, set()).add(BLOCK_OWNER[_head])

    drift_out = sorted(n for n in emitted
                       if not any(named_by_package(n, b) for b, _m in emitted[n]))

    # ---------- DIRECTION 2: the package carries it, the writer does not emit it ----------
    # A split name is resolved THROUGH THE BLOCK STRUCTURE where it is dotted (BLOCK_OWNER, declared above):
    # `config.legend` is satisfied by the config literal's `legend`, and NOT by the cell record's, which is a
    # different field that happens to share a leaf. RESOLVING BY LEAF ALONE IS HOW A CHECK PASSES WHILE THE
    # FIELD IT NAMES IS GONE.
    drift_in, by_ref_verified = [], []
    for n in sorted(named):
        if "." in n:
            head, tail = n.split(".", 1)
            owner = BLOCK_OWNER.get(head)
            if owner is None or tail not in sites.get(owner, {}):
                drift_in.append((n, f"dotted: {n} does not resolve in the writer's {owner or 'UNKNOWN'}"))
            continue
        owners = [b for b in named[n] if b in sites]
        if not owners:
            # A BARE split name the census does not name is one of the names this card lands, and it has no
            # block attributed anywhere: it must be emitted SOMEWHERE, which is all the split claims about a
            # top-level name. Where the census DOES name it, the match is confined to that block.
            owners = list(sites)
        # A sub-block's keys are carried BARE by the census and DOTTED by this reader (`freeze.dead_end_verifier`
        # vs the census's `dead_end_verifier`), so the match is at the leaf WITHIN THE OWNING BLOCK -- a leaf
        # match anywhere would let one block's `legend` answer for another's.
        if any(n in sites.get(b, {}) or any(x.split(".")[-1] == n for x in sites.get(b, {}))
               for b in owners):
            if n in BLOCK_BY_REFERENCE:
                by_ref_verified.append(n)
            continue
        # A CENSUS BLOCK LISTS A NESTED BLOCK BY NAME; the name is a key of a literal all the same, so this
        # branch is only reached when a declared block-by-reference name is NOT a key anywhere -- which is
        # the case worth failing on, not the case worth waving through.
        drift_in.append((n, f"named by {sorted(named[n])} and emitted by no literal, spread or "
                            f"subscript this check reads"))

    print("\n  DIRECTION 1 -- EMITTED BY THE WRITER, UNNAMED BY THE PACKAGE:")
    if drift_out:
        for n in drift_out:
            for block, meta in emitted[n]:
                print(f"    {n:44s} {block:16s} {meta['at']}")
    else:
        print("    none")

    print("\n  DIRECTION 2 -- NAMED BY THE PACKAGE, EMITTED BY NO LITERAL THE WRITER OWNS:")
    if drift_in:
        for n, why in drift_in:
            print(f"    {n:44s} {why}")
    else:
        print("    none")

    print(f"\n  CLASSIFICATION, ENFORCED RATHER THAN ASSERTED: {len(by_ref_verified)} name(s) are "
          f"BLOCK-BY-REFERENCE and every one of them was RESOLVED to a key of the writer's literal:")
    print(f"    {sorted(by_ref_verified)}")

    # ---------- the reading that is NOT a failure: the two censuses are not the same age ----------
    census_set = {n for names in census.values() for n in names}
    split_set = set(fmt or []) | set(local or [])
    split_leaves = {n.split(".")[-1] for n in split_set}
    census_not_split = sorted(n for n in census_set if n not in split_leaves)
    split_not_census = sorted(n for n in split_leaves if n not in census_set)
    print("\n  THE TWO CENSUSES (a reading, not a failure). The package's §2 census is DATED 2026-10-10 and")
    print("  its lists are not edited; the split is the surface this check ENFORCES, so a name may be in the")
    print("  split and not in the dated census without being drift. Leaf-level, so it is a reading:")
    print(f"    in the §2 census and not in the split : {len(census_not_split)}  {census_not_split}")
    print(f"    in the split and not in the §2 census : {len(split_not_census)}  {split_not_census}")

    print("\n  THE DOC AND THE SCRIPT, WHICH ARE ONE LIST IN TWO CARRIERS:")
    parity = []
    if set(l1) != set(fmt or []):
        parity.append(("LIST 1 (§1 of the package) vs FORMAT (the split)", sorted(set(l1) ^ set(fmt or []))))
    if set(l2) != set(local or []):
        parity.append(("LIST 2 (§1 of the package) vs LOCAL (the split)", sorted(set(l2) ^ set(local or []))))
    if parity:
        for what, diff in parity:
            print(f"    *** {what}: SYMMETRIC DIFFERENCE {diff}")
    else:
        print(f"    identical: LIST 1 and FORMAT both name {len(fmt or [])}; LIST 2 and LOCAL both name "
              f"{len(local or [])}")

    print()
    print("=" * 100)
    if drift_out or drift_in or parity:
        print(f"  *** DRIFT. {len(drift_out)} name(s) the writer emits and the package does not carry; "
              f"{len(drift_in)} name(s) the package carries and the writer does not emit; "
              f"{len(parity)} carrier mismatch(es). ***")
        return 1
    print("  NO UNCLASSIFIED DRIFT: every name the writer emits is carried by the package, every name the")
    print("  package carries is emitted by the writer, and the two carriers of the split agree.")
    print("  AND THIS IS A MEASUREMENT RATHER THAN A RESOLUTION -- the control injects a name and watches")
    print("  this check fail on it (check_conformance_census_control.py).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
