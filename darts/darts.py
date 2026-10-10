#!/usr/bin/env python3
"""
DARTS -- 501 checkouts.  The oracle is ARITHMETIC.

An INDEPENDENT implementation of the Handicap Arena record format for the event
the order lists as #11 (exception -- exact arithmetic, no engine, no freeze, no
depth).  Written from the FORMAT.md / GAME_CONTRACT.md / bundle reading on
Jarvis, NOT ported from Chilly's tree: where the format was ambiguous the
ambiguity is written down rather than guessed at, and every such point is
marked  [A<n>]  at the line that had to decide something.  The list lives in
darts/DARTS_AMBIGUITIES.md.

Standard library ONLY -- argparse json os re sys time hashlib datetime.
No third-party import, so `python3 darts.py --self-test` runs on either box.

  python3 darts.py --self-test
  python3 darts.py instrument-check   # prove the HARNESS with a solver; enters nothing
  python3 darts.py run --entrant reference
  python3 darts.py run --entrant liar        # values that LOOK like arithmetic
  python3 darts.py run --entrant garbage     # malformed -> UNREADABLE, not wrong
  python3 darts.py run --entrant never-starts # -> ERROR, never a score
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

HARNESS = "handicap-arena"
VERSION = "1.1"

# ---------------------------------------------------------------------------
# 1. THE BOARD -- the oracle is this table and nothing else
# ---------------------------------------------------------------------------

def _board():
    """Every throwable segment: label -> (value, is_double).
    is_double is the only property the finish rule needs: a checkout's LAST
    dart must be a double (inner bull 50 counts)."""
    b = {}
    for n in range(1, 21):
        b["S%d" % n] = (n, False)       # singles -- notation often omits the S
        b["D%d" % n] = (2 * n, True)
        b["T%d" % n] = (3 * n, False)
    b["25"] = (25, False)               # outer bull -- NOT a finish
    b["D25"] = (50, True)               # inner bull -- the 50 finish
    return b


BOARD = _board()

# Aliases accepted on READ.  What we EMIT is always T20 / D25 / plain-digit.
# [A5] the rules name the segments but not the tokens a model may write.
ALIASES = {
    "25": "25", "SB": "25", "OB": "25", "OUTERBULL": "25", "S25": "25",
    "BULL": "D25", "BULLSEYE": "D25", "D25": "D25", "DB": "D25", "IB": "D25",
    "INNERBULL": "D25", "S50": "D25", "50": "D25",
    "B": "D25",
}


class ParseError(ValueError):
    pass


def parse_token(tok):
    """One dart token -> (label, value, is_double).  Raises ParseError.
    400ms of thought: the whole verifier is downstream of this function, so a
    token it silently accepts is a hole in the oracle.  It REFUSES rather than
    guessing.  [A5]"""
    up = tok.strip().upper()
    if not up:
        raise ParseError("empty token")
    if up in ALIASES:
        lab = ALIASES[up]
        val, dbl = BOARD[lab]
        return lab, val, dbl
    m = re.fullmatch(r"([SDT])?(\d{1,2})", up)
    if not m:
        raise ParseError("not a dart: %r" % tok)
    prefix, num = m.group(1) or "S", int(m.group(2))
    if not (1 <= num <= 20):
        raise ParseError("no such segment: %r" % tok)
    lab = "%s%d" % (prefix, num)
    val, dbl = BOARD[lab]
    return lab, val, dbl


# ---------------------------------------------------------------------------
# 2. THE ORACLE -- checkouts by enumeration, never by claim
# ---------------------------------------------------------------------------

def checkouts_for(remaining, max_darts=3):
    """Every checkout for `remaining`: ordered dart sequences of length
    1..max_darts, last dart a double, sum exact, and NO prefix may leave 2 or
    fewer... precisely: every prefix before the last must leave >= 2, which is
    the ordinary bust rule (you bust by going below 2, or to 1, or to 0 on a
    non-double).  Returns list of tuples of labels."""
    if remaining < 2 or remaining > 60 * max_darts:
        return []
    segs = [(lab, val, dbl) for lab, (val, dbl) in BOARD.items()]
    out = []

    def rec(rem, darts_left, acc):
        for lab, val, dbl in segs:
            if val > rem:
                continue
            if dbl and val == rem:
                # this dart FINISHES the leg -- a valid checkout of any length
                out.append(tuple(acc + [lab]))
            if darts_left > 1:
                nxt = rem - val
                if nxt >= 2:              # not a bust en route
                    rec(nxt, darts_left - 1, acc + [lab])

    rec(remaining, max_darts, [])
    return out


def canonical(remaining):
    """A display checkout -- FEWEST darts, then a deterministic tie-break.
    This is a PRESENTATION choice, not a rule.  [A3]"""
    outs = checkouts_for(remaining)
    if not outs:
        return None
    def key(seq):
        return (len(seq), [-BOARD[l][0] for l in seq], list(seq))
    return " ".join(min(outs, key=key))


def verify(remaining, tokens):
    """THE ORACLE.  Verdict on a claimed checkout.
    -> (state, reason, total)
       state in {"PASS","FAIL","UNREADABLE"}.
    UNREADABLE is a THIRD state, never folded into FAIL.  A malformed answer
    is not a wrong throw: reading it as wrong is how a legal best move got
    called illegal and nearly published.  [A6]"""
    if not tokens:
        return "UNREADABLE", "no darts in answer", None
    parsed = []
    try:
        for t in tokens:
            parsed.append(parse_token(t))
    except ParseError as e:
        return "UNREADABLE", str(e), None
    if len(parsed) > 3:
        return "UNREADABLE", "more than three darts", None
    total = sum(v for _, v, _ in parsed)
    if total != remaining:
        return "FAIL", "sum %d != remaining %d" % (total, remaining), total
    if not parsed[-1][2]:
        return "FAIL", "last dart %s is not a double" % parsed[-1][0], total
    run = 0
    for lab, val, _ in parsed[:-1]:
        run += val
        if remaining - run < 2:
            return "FAIL", "bust before the finish (%s leaves %d)" % (
                lab, remaining - run), total
    return "PASS", None, total


def is_impossible(remaining):
    return len(checkouts_for(remaining)) == 0


# ---------------------------------------------------------------------------
# 3. THE ITEM SET
# ---------------------------------------------------------------------------

DEFAULT_ITEMS = [
    {
        "id": "D1.1_easy_checkout",
        "difficulty": "easy",
        "remaining": 40,
        "expect": "checkout",
        "prompt": ("You are on 40 with three darts in hand. Give a checkout in "
                   "standard notation. Answer with the darts only, e.g. T20 T20 D25."),
    },
    {
        "id": "D1.2_two_dart_checkout",
        "difficulty": "medium",
        "remaining": 100,
        "expect": "checkout",
        "prompt": ("You are on 100 with three darts in hand. Give a checkout in "
                   "standard notation. Answer with the darts only, e.g. T20 T20 D25."),
    },
    {
        "id": "D1.3_impossible_control",
        "difficulty": "control",
        "remaining": 169,
        "expect": "impossible",
        "prompt": ("You are on 169 with three darts in hand. If a checkout exists, "
                   "give it in standard notation. If NO checkout exists, answer "
                   "exactly: NO CHECKOUT. No prose."),
    },
]


def load_items(path):
    if not path or not os.path.exists(path):
        return DEFAULT_ITEMS
    with open(path) as fh:
        doc = json.load(fh)
    return doc.get("items", doc if isinstance(doc, list) else DEFAULT_ITEMS)


def score_item(item, raw):
    """Score one item from ONE raw answer string.  Returns a per-item row."""
    row = {
        "remaining": item["remaining"],
        "expect": item["expect"],
        "raw": [raw],
        "answer": None,
        "verified_sum": None,
        "state": None,
        "reason": None,
    }
    text = (raw or "").strip()
    if not text:
        row["state"] = "UNREADABLE"
        row["reason"] = "empty answer"
        return row
    # a model that wraps its answer in prose or a fence is a malformed answer,
    # not a wrong throw -- but only the dart SECTION is read, and if that fails
    # it is UNREADABLE.  [A6]
    body = text.strip()
    body = re.sub(r"^```[a-zA-Z]*", "", body).strip()
    body = re.sub(r"```$", "", body).strip()
    first = body.splitlines()[0].strip() if body else ""
    toks = first.split()
    row["answer"] = first
    if re.fullmatch(r"(NO\s+CHECKOUT|IMPOSSIBLE|NONE|NO\s+SOLUTION)[.!]?",
                    first.upper()):
        if item["expect"] == "impossible" and is_impossible(item["remaining"]):
            row["state"] = "PASS"
        else:
            row["state"] = "FAIL"
            row["reason"] = "abstained where a checkout exists"
        return row
    state, reason, total = verify(item["remaining"], toks)
    row["state"] = state
    row["reason"] = reason
    row["verified_sum"] = total
    return row


# ---------------------------------------------------------------------------
# 4. ENTRANTS -- pluggable.  A model entrant is NOT built here.
# ---------------------------------------------------------------------------

class Entrant(object):
    kind = "?"
    def start(self):
        """Admission.  -> (rc, secs, started)"""
        raise NotImplementedError
    def answer(self, item):
        raise NotImplementedError


class ReferenceSolver(Entrant):
    """A stdlib arithmetic solver -- the REFERENCE, not a model.  It exists to
    prove the pipeline and to make the control fire.  It is not an arena
    entrant and this bundle is NOT for the board."""
    kind = "reference-solver"
    def start(self):
        return 0, 0.0, True
    def answer(self, item):
        c = canonical(item["remaining"])
        return c if c else "NO CHECKOUT"
    def source_sha256(self):
        with open(__file__, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()


class Liar(Entrant):
    """Produces things that LOOK like arithmetic.  Does the control fire?"""
    kind = "adversarial-reference"
    def start(self):
        return 0, 0.0, True
    def answer(self, item):
        if item["expect"] == "impossible":
            return "T20 T20 D25"          # a checkout that sums to 170, not 169
        return "T20 T20 T20"              # sums to 180, every dart a triple


class Garbage(Entrant):
    """Malformed answers.  Must read UNREADABLE, never FAIL."""
    kind = "malformed-reference"
    def start(self):
        return 0, 0.0, True
    def answer(self, item):
        return "Sure! The best checkout here would be a couple of big scores, "\
               "you should aim for the treble twenty."


class NeverStarts(Entrant):
    """The population-does-not-load case.  rc=2 in 0.0s -- the exact failure
    that scored COVERAGE 1.000 on Chilly's box.  Must be an ERROR here."""
    kind = "never-started-reference"
    def start(self):
        return 2, 0.0, False
    def answer(self, item):
        raise AssertionError("must never be asked -- the run never started")


ENTRANTS = {
    "reference": ReferenceSolver,
    "liar": Liar,
    "garbage": Garbage,
    "never-starts": NeverStarts,
}


# ---------------------------------------------------------------------------
# 5. THE RUN -- admission, per-item rows, score, coverage, verdict
# ---------------------------------------------------------------------------

def run_entrant(entrant, items):
    rc, secs, started = entrant.start()
    admission = {"rc": rc, "secs": secs, "started": bool(started),
                 "never_started": (not started)}
    rows = {}
    started_items = 0
    unreadable = 0
    passed = 0
    failed = 0
    for item in items:
        if not started:
            rows[item["id"]] = {
                "remaining": item["remaining"], "expect": item["expect"],
                "raw": [], "answer": None, "verified_sum": None,
                "state": "NOT_STARTED", "reason": "entrant never started "
                "(rc=%s in %ss)" % (rc, secs),
            }
            continue
        t0 = time.perf_counter()
        raw = entrant.answer(item)
        dt = time.perf_counter() - t0
        row = score_item(item, raw)
        row["secs"] = round(dt, 4)
        rows[item["id"]] = row
        started_items += 1
        if row["state"] == "UNREADABLE":
            unreadable += 1
        elif row["state"] == "PASS":
            passed += 1
        elif row["state"] == "FAIL":
            failed += 1

    total = len(items)
    #  [A6 -- RULED 2026-10-09] THE DENOMINATOR IS "TOOK A TURN", NOT "DID WELL".
    #  An item that produced an answer -- right, wrong, or UNREADABLE -- took a
    #  turn and is INSIDE the denominator.  UNREADABLE is a non-pass inside it,
    #  never dropped and never folded into FAIL.  A never-started item took no
    #  turn and is OUTSIDE, counted separately as NOT_STARTED.  Three states,
    #  three treatments; the distinction is DID IT TAKE A TURN.
    trials = started_items
    measured = started_items - unreadable      # a READABLE answer -- the gate
    coverage = (float(started_items) / total) if total else 0.0

    #  THE GUARD IS THE PAIR (coverage AND measured), NOT THE RATIO: coverage
    #  alone can read 1.000 with nothing measured (the garbage run), so the
    #  verdict needs `measured > 0` as a SECOND condition.  [A7]
    if started_items == 0:
        verdict = "ERROR: POPULATION NEVER STARTED"
        aggregate = None
        exit_code = 2
    elif measured == 0:
        verdict = "ERROR: ZERO MEASURED (every answer unreadable)"
        aggregate = None
        exit_code = 2
    else:
        aggregate = round(float(passed) / trials, 6)   # unreadable inside, non-pass
        verdict = "SCORED"
        exit_code = 0

    roundblock = {
        "score": aggregate,
        "wins": passed,
        "trials": trials,               # denominator = items that TOOK A TURN [A6]
        "kind": "exact_arithmetic",
        "class": "CONTEST",
        "oracle": "arithmetic",
        "staged_as": "arcade cabinet -- DARTS: 501 checkouts, the oracle is the sum",
        "denominator_rule": "trials = items that took a turn; UNREADABLE is a "
                            "non-pass INSIDE it; NEVER_STARTED is OUTSIDE [A6]",
        "items": rows,
        "started": started_items,
        "failed": failed,               # a readable wrong throw -- non-pass, inside
        "unreadable": unreadable,       # non-pass, INSIDE the denominator [A6]
        "never_started": total - started_items,   # OUTSIDE, counted separately [A6]
        "measured": measured,           # readable answers -- the gate quantity [A7]
        "coverage": round(coverage, 6),
    }
    return {"admission": admission, "round": roundblock,
            "aggregate": aggregate, "verdict": verdict, "exit_code": exit_code}


def build_bundle(entrant_name, result, items, items_path):
    ent = ENTRANTS[entrant_name]() if entrant_name in ENTRANTS else ReferenceSolver()
    sha = ent.source_sha256() if hasattr(ent, "source_sha256") else None
    return {
        "harness": HARNESS,
        "version": VERSION,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "DARTS",
        "card_version": "darts_v1",
        "results": [
            {
                # [A1 -- RULED 2026-10-09] the entrant block DECLARES model|code.
                # A CODE entrant is a DIFFERENT INSTRUMENT and is never pooled
                # into a model table.  The format's entrant fields (gguf, sha256,
                # footprint_gb, division, weigh_in, cord, n_gpu_layers) all
                # presuppose weights, so for a code entrant they are STATED not
                # applicable rather than faked.
                "entrant": entrant_name,
                "kind": ent.kind,
                "instrument": "code",
                "instrument_note": "CODE entrant, not a model -- a DIFFERENT "
                                   "INSTRUMENT; never pooled into a model table [A1].",
                "entrant_is_a_model": False,
                "weights_sha256": None,
                "weights_note": "no weights: this entrant is code, not a GGUF. "
                                "The oracle is arithmetic and the entrant played "
                                "no model.",
                "solver_source_sha256": sha,
                "division": None,
                "division_note": "NOT MEASURED -- a footprint is a property of "
                                 "weights; this entrant has none. Never 0.00.",
                "cord": None,
                "config": {
                    "temperature": None,
                    "max_tokens": None,
                    "trials": 1,
                    "ctx": None,
                    "n_gpu_layers": None,
                    "server_flags": None,
                    "config_note": "RUN_FACTS that do not exist for a solver are "
                                   "null, not omitted and not zeroed. [A2]",
                },
                "admission": result["admission"],
                "rounds": {"R_darts_checkouts": result["round"]},
                "aggregate": result["aggregate"],
                "coverage": result["round"]["coverage"],
                "verdict": result["verdict"],
                "certification": "REFERENCE RUN -- not an entrant, not for the board.",
                "on_board": False,
                "tasks": items_path,
                "ambiguities": "darts/DARTS_AMBIGUITIES.md",
            }
        ],
    }


def cmd_run(args):
    items = load_items(args.tasks)
    if args.entrant not in ENTRANTS:
        print("unknown entrant %r; choose from %s" % (
            args.entrant, ", ".join(sorted(ENTRANTS))), file=sys.stderr)
        return 2
    result = run_entrant(ENTRANTS[args.entrant](), items)
    bundle = build_bundle(args.entrant, result, items, args.tasks)
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "darts_v1_%s.json" % args.entrant)
    with open(path, "w") as fh:
        json.dump(bundle, fh, indent=2)
        fh.write("\n")
    print("wrote %s" % path)
    print("  %-14s aggregate=%s  coverage=%.3f  %s" % (
        args.entrant, result["aggregate"], result["round"]["coverage"],
        result["verdict"]))
    return result["exit_code"]


# ---------------------------------------------------------------------------
# 5b. THE INSTRUMENT CHECK -- prove the HARNESS, enter nothing
# ---------------------------------------------------------------------------

def instrument_check(out_dir=None):
    """[INSTRUMENT CHECK]  Prove the harness can RUN the event, with a
    known-good solver as the entrant -- NOT a contest.

    This is the sequencing split (Jarvis's own note to Chilly, 2026-10-09):
    ask (a) CAN THE HARNESS RUN DARTS? separately from (b) CAN A MODEL PLAY IT?
    A solver run exercises the four things that need no model -- the STATE KIND,
    the ORACLE, the BUNDLE SHAPE and the SCORING PATH -- so that if a model
    later fails, the harness is already proven and the failure is the model's.

    It ENTERS NOTHING: the bundle is labelled INSTRUMENT CHECK, on_board False,
    instrument code, and is written under its own name so it cannot be swept
    into a model table (A1/A8).  Exit 1 if the instrument is not proven."""
    ok = True
    here = os.path.dirname(__file__)
    items = load_items(os.path.join(here, "tasks", "darts_v1.json"))
    result = run_entrant(ReferenceSolver(), items)
    bundle = build_bundle("reference", result, items, "tasks/darts_v1.json")
    ent = bundle["results"][0]
    ent["certification"] = ("INSTRUMENT CHECK -- the solver-as-entrant path; "
                            "proves the harness and ENTERS NOTHING. Not a contest.")
    ent["on_board"] = False

    print("INSTRUMENT CHECK -- solver-as-entrant; proves the harness, enters nothing.")
    #  1. THE ORACLE -- a known-good solver must score the item set exactly.
    ok &= _assert(result["aggregate"] == 1.0,
                  "ORACLE: solver scores 1.0 on the item set", result["aggregate"])
    #  2. THE STATE KIND -- PASS is reached, and the impossible item's correct
    #     answer is an ABSTENTION which must PASS.
    states = sorted({r["state"] for r in result["round"]["items"].values()})
    ok &= _assert(states == ["PASS"], "STATE KIND: every item PASS (abstention too)",
                  states)
    #  3. THE BUNDLE SHAPE -- the record carries what the format requires.
    for key in ("harness", "version", "event", "card_version", "results"):
        ok &= _assert(key in bundle, "BUNDLE SHAPE: has %r" % key, sorted(bundle))
    for key in ("tasks", "ambiguities", "instrument", "admission", "rounds"):
        ok &= _assert(key in ent, "BUNDLE SHAPE: result carries %r" % key, sorted(ent))
    ok &= _assert(
        all(k in result["round"] for k in
            ("score", "wins", "trials", "started", "unreadable",
             "never_started", "measured", "coverage")),
        "BUNDLE SHAPE: round block carries the full count set",
        sorted(result["round"]))
    #  4. THE SCORING PATH -- score is wins/trials, trials counts TURNS taken.
    rnd = result["round"]
    ok &= _assert(rnd["score"] == round(rnd["wins"] / float(rnd["trials"]), 6),
                  "SCORING PATH: score == wins/trials", rnd["score"])
    ok &= _assert(rnd["trials"] == rnd["started"] and rnd["never_started"] == 0,
                  "SCORING PATH: trials == started; never_started OUTSIDE [A6]",
                  (rnd["trials"], rnd["started"], rnd["never_started"]))
    #  LABEL -- a code entrant is a different instrument and is not on the board.
    ok &= _assert(ent["instrument"] == "code" and ent["on_board"] is False,
                  "LABEL: instrument=code, on_board=False", ent.get("instrument"))

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "darts_v1_instrument-check.json")
        with open(path, "w") as fh:
            json.dump(bundle, fh, indent=2)
            fh.write("\n")
        print("wrote %s" % path)
    print("")
    print("INSTRUMENT CHECK %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# 6. SELF-TEST -- the controls, run here, exit 1 if any fails
# ---------------------------------------------------------------------------

def _assert(cond, label, seen=None):
    mark = "ok  " if cond else "FAIL"
    print("  %s %s%s" % (mark, label, "" if cond or seen is None else "  <- %r" % (seen,)))
    return bool(cond)


def self_test():
    ok = True
    print("checkout oracle -- facts it must reproduce:")
    ok &= _assert(canonical(170) == "T20 T20 D25", "170 -> T20 T20 D25",
                  canonical(170))
    ok &= _assert(len(checkouts_for(170)) == 1, "170 has exactly one checkout",
                  len(checkouts_for(170)))
    ok &= _assert(canonical(40) == "D20", "40 -> D20", canonical(40))
    ok &= _assert(canonical(2) == "D1", "2 -> D1 (the minimum finish)",
                  canonical(2))
    ok &= _assert(canonical(100) == "T20 D20", "100 -> T20 D20", canonical(100))
    ok &= _assert(is_impossible(169) and is_impossible(1) and is_impossible(171),
                  "169 / 1 / 171 have NO checkout")
    ok &= _assert(not is_impossible(170), "170 is not impossible")

    print("verifier -- accepts the true, refuses the false, abstains on the unreadable:")
    st, why, tot = verify(170, ["T20", "T20", "D25"])
    ok &= _assert(st == "PASS", "accepts T20 T20 D25 on 170", (st, why))
    st, why, tot = verify(100, ["T20", "T20"])
    ok &= _assert(st == "FAIL" and "sum" in (why or ""),
                  "refuses a wrong sum (T20 T20 on 100)", (st, why))
    st, why, tot = verify(60, ["T20"])
    ok &= _assert(st == "FAIL" and "double" in (why or ""),
                  "refuses a finish that does not end on a double (T20 on 60)",
                  (st, why))
    st, why, tot = verify(60, ["60"])
    ok &= _assert(st == "UNREADABLE", "60 alone is not a segment -> UNREADABLE",
                  (st, why))
    st, why, tot = verify(40, "aim for the treble twenty".split())
    ok &= _assert(st == "UNREADABLE",
                  "prose is UNREADABLE, never a wrong throw", (st, why))
    st, why, tot = verify(2, ["D1"])
    ok &= _assert(st == "PASS", "accepts D1 on 2", (st, why))

    print("control -- the impossible item must fire:")
    items = DEFAULT_ITEMS
    control = [i for i in items if i["expect"] == "impossible"][0]
    row = score_item(control, "T20 T20 D25")
    ok &= _assert(row["state"] == "FAIL",
                  "a claimed checkout on 169 FAILS", row)
    row = score_item(control, "NO CHECKOUT")
    ok &= _assert(row["state"] == "PASS",
                  "abstaining on 169 PASSES", row)

    print("coverage -- a population that never started must NOT score:")
    res = run_entrant(NeverStarts(), items)
    ok &= _assert(res["exit_code"] == 2,
                  "never-started run exits 2", res["exit_code"])
    ok &= _assert(res["aggregate"] is None,
                  "never-started run has NO aggregate (not 0.0)", res["aggregate"])
    ok &= _assert(res["round"]["never_started"] == len(items),
                  "never_started counted per item", res["round"]["never_started"])
    ok &= _assert(res["round"]["trials"] == 0,
                  "never-started run has trials 0 (nothing took a turn)",
                  res["round"]["trials"])
    res = run_entrant(ReferenceSolver(), items)
    ok &= _assert(res["aggregate"] == 1.0 and res["exit_code"] == 0,
                  "reference solver scores 1.0 on the item set", res["aggregate"])
    res = run_entrant(Garbage(), items)
    ok &= _assert(res["exit_code"] == 2 and res["aggregate"] is None,
                  "all-unreadable run is an ERROR, not a 0.0",
                  (res["exit_code"], res["aggregate"]))
    ok &= _assert(res["round"]["coverage"] == 1.0 and res["round"]["measured"] == 0,
                  "garbage: coverage 1.000 AND measured 0 -- the ratio is not the guard",
                  (res["round"]["coverage"], res["round"]["measured"]))

    print("A6 -- UNREADABLE is INSIDE the denominator as a non-pass:")
    class _Mixed(Entrant):
        kind = "mixed-reference"
        def start(self):
            return 0, 0.0, True
        def answer(self, item):
            # right on the easy item; prose (UNREADABLE) on the other two
            return "D20" if item["remaining"] == 40 else "hmm, maybe not"
    res = run_entrant(_Mixed(), items)
    rnd = res["round"]
    ok &= _assert(rnd["started"] == 3 and rnd["trials"] == 3,
                  "denominator counts every item that TOOK A TURN (3)",
                  (rnd["started"], rnd["trials"]))
    ok &= _assert(rnd["unreadable"] == 2 and rnd["measured"] == 1,
                  "unreadable 2 (INSIDE, non-pass) / measured 1 (the gate)",
                  (rnd["unreadable"], rnd["measured"]))
    ok &= _assert(rnd["never_started"] == 0,
                  "no item was never-started, so none is OUTSIDE", rnd["never_started"])
    ok &= _assert(res["aggregate"] == round(1.0 / 3.0, 6),
                  "score = passed/trials, so the unreadables DRAG it (1/3)",
                  res["aggregate"])
    ok &= _assert(res["aggregate"] != 1.0,
                  "the reader that EXCLUDED unreadable would have said 1.0 -- it does not",
                  res["aggregate"])

    print("A1 -- a code entrant DECLARES itself and is not a model:")
    b = build_bundle("reference", run_entrant(ReferenceSolver(), items), items, None)
    ent = b["results"][0]
    ok &= _assert(ent["instrument"] == "code" and ent["entrant_is_a_model"] is False,
                  "entrant block declares instrument=code, model=False",
                  ent["instrument"])
    ok &= _assert(ent["division"] is None and ent["weights_sha256"] is None,
                  "no footprint / no weights invented for a code entrant (never 0.00)",
                  (ent["division"], ent["weights_sha256"]))

    print("")
    print("SELF-TEST %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="DARTS -- 501 checkouts, oracle=arithmetic")
    ap.add_argument("--self-test", action="store_true",
                    help="run the controls and exit 1 if any fails")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="play one entrant and write a bundle")
    r.add_argument("--entrant", default="reference", choices=sorted(ENTRANTS))
    r.add_argument("--tasks", default=os.path.join(os.path.dirname(__file__),
                                                  "tasks", "darts_v1.json"))
    r.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "results"))
    ic = sub.add_parser("instrument-check",
                        help="prove the harness with a solver entrant; enters nothing")
    ic.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "results"))
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "instrument-check":
        return instrument_check(args.out)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
