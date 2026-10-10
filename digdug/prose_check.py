#!/usr/bin/env python3
# prose_check.py -- SECTION 4F, MEASURED.
#
# The brief asks for the places where a competent implementer reading that
# paragraph would have built something INCOMPATIBLE with what another
# competent implementer built from the same paragraph -- and for which of them
# the RUNNING settled.
#
# Opinion would be cheap here, so this script measures it.  It takes the
# answer streams the frozen cabinet actually produced (read from the bundles
# on disk, because the record beats a claim about the record), and replays
# them through `alt_reading.py` -- a second implementation of the same
# paragraph that chose the opposite reading on every open clause.
#
# Three things come out:
#
#   1. CROSS-CHECK.  The second implementation, configured with the FROZEN
#      decisions, must reproduce the frozen cabinet's counters.  If it does
#      not, the divergence below is implementation drift and proves nothing.
#   2. THE DIVIDEND.  The same streams under the LITERAL reading: which
#      entrants get a different score, a different death, a different
#      terminal.
#   3. ATTRIBUTION.  Each clause flipped ONE AT A TIME from frozen to
#      literal, so each divergence is attributed to the clause that caused
#      it -- and a clause that changes nothing on this field is reported as
#      NOT EXERCISED, because an unexercised claim has no carrier
#      (PRECEDENCE.md).
#
# Stdlib only.

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import alt_reading                                         # noqa: E402
import digdug                                              # noqa: E402
import digdug_reader                                       # noqa: E402

CARD_VERSION = "digdug_v1"
RESULTS = os.path.join(HERE, "results")

#: The fields a reader would take to the board.  A divergence in one of these
#: is a divergence in the measurement; a divergence anywhere else is trivia.
SCORED_FIELDS = ("solved", "terminal", "died_at_turn", "turns_used", "dug",
                 "moved", "blocked", "collected", "not_an_action", "give_up",
                 "answers_consumed", "answers_after_end")

#: The clauses, with the frozen value and the literal value.  `None` means
#: "handled separately" (the token list is a tuple, not a bool).
CLAUSES = (
    ("U1_hazard_clock_every",
     "a hazard moves once per player turn",
     "a hazard on its own clock, every second turn"),
    ("U2_hazard_starts_in_soil",
     "the player's and every hazard's cell is a tunnel at t=0",
     "'a grid of soil': a hazard stands in soil, has no tunnel, never moves"),
    ("U3_target_persists",
     "a collected target is removed",
     "a collected target persists on the board"),
    ("U4_adjacent_kills",
     "only the SAME cell kills",
     "ADJACENT cells kill"),
    ("U5_wait_is_a_turn",
     "there is no pass action",
     "WAIT is a legal turn"),
    ("U7_collection_after_clock",
     "collecting the last target ends the attempt BEFORE the clock",
     "the turn resolves in full, then the objective is awarded"),
    ("U8_hazards_sequential",
     "hazards move simultaneously from one snapshot",
     "hazards move sequentially in index order"),
    ("U9_grid_wraps",
     "bounded, no wrap; out of bounds is blocked",
     "the grid WRAPS"),
    ("A1_hazards_dig",
     "hazards never dig",
     "hazards dig: the soil barrier does not exist"),
    ("A6_unknown_letter_blocks",
     "step() raises on an unresolved letter",
     "step() is total: anything is a block"),
    ("A8_blocked_is_free",
     "a blocked move costs the turn and ticks the clock",
     "a blocked move is free"),
    ("A11_tokens",
     "31 frozen tokens, exact",
     "two tokens: RESIGN and GIVEUP"),
    ("A13_first_line_is_the_answer",
     "one token per turn, never truncated",
     "the first line, and the first letter in it, is the answer"),
    ("A17_counters_from_state",
     "the counters come from the STATE CHANGE: a move that collects buried "
     "treasure counts as a dig AND a collection",
     "the counters come from the WORD: that move is a collection and not a "
     "dig"),
)


# ---------------------------------------------------------------------------
# PROBES -- for the clauses the FIELD never touched.
#
# A clause the field did not exercise is not thereby settled, and saying so
# would be a claim with no carrier (PRECEDENCE.md).  But "the field did not
# reach it" and "no run could ever reach it" are different findings, and the
# difference matters: the first is a gap in the field, the second is a clause
# that no measurement can arbitrate.  Each probe below is a SYNTHETIC board
# and stream built to reach one clause.  Probes are not levels: they are not
# in the frozen set, they are not scored, and a probe that a probe settles is
# labelled as such.
# ---------------------------------------------------------------------------

PROBES = (
    ("U5_wait_is_a_turn",
     "######\n#P H%T#\n######", ["WAIT"],
     "whether WAIT advances the game clock is visible in turns_used"),
    ("U7_collection_after_clock",
     "#######\n#P%TH #\n#######", ["R", "R"],
     "the player collects the last target with a hazard one step behind: "
     "frozen, the objective is awarded before the clock; literal, the clock "
     "runs first and the player dies on the winning move"),
    ("U9_grid_wraps",
     "#####\nP%%%T\n##H##", ["L"],
     "the player stands on the left border: frozen, L is blocked; literal, L "
     "wraps onto the target"),
    ("A6_unknown_letter_blocks",
     "#######\n#P%%%T#\n#H%%%%#\n#######", ["X"],
     "an unresolved letter handed DIRECTLY to the transition function -- no "
     "reader can produce one, so this clause is about a caller that bypasses "
     "the reader: frozen, step() raises; literal, it is a block and a "
     "counter", "step_call"),
)

#: Clauses that no run can arbitrate, with the reason.  Recorded rather than
#: quietly left in the "not exercised" pile, because the two are different
#: claims.
NOT_SETTLEABLE = {
    "U3_target_persists":
        "the two readings differ ONLY in what the board draws after a "
        "collection; `targets_left` shrinks either way, so no scored field "
        "can ever distinguish them.  Settled by looking at a render, not by "
        "a run.",
    "U8_hazards_sequential":
        "MOOT under [A10]: hazards do not block each other and the policy "
        "reads only the tunnel graph and the player's cell, so index order "
        "cannot change any hazard's move.  It becomes observable only if "
        "hazards are made to block each other -- which is a different "
        "contract.",
}


def run_probe(text, tokens, cfg, budget=30, kind="stream"):
    """One probe under one reading.  An exception IS a result here: whether a
    reading crashes or counts is exactly what A6 decides."""
    try:
        if kind == "step_call":
            st = alt_reading.AltState(alt_reading.AltLevel(text, "<probe>"),
                                      cfg)
            _pos, word, _moved = alt_reading.alt_step(st, tokens[0])
            return {"word": word}, None
        return alt_reading.alt_play(text, tokens, cfg=cfg, budget=budget,
                                    name="<probe>"), None
    except Exception as exc:                                   # noqa: BLE001
        return None, "%s: %s" % (exc.__class__.__name__, exc)


def run_probe_frozen_step(text, letter):
    """The frozen transition function, called directly, for the A6 probe."""
    try:
        _s, word = digdug.step(digdug.State(digdug.parse_level(text,
                                                              "<probe>")),
                               letter)
        return {"word": word}, None
    except Exception as exc:                                   # noqa: BLE001
        return None, "%s: %s" % (exc.__class__.__name__, exc)


def probes(verbose=True):
    out = []
    for entry in PROBES:
        key, text, tokens, why = entry[:4]
        kind = entry[4] if len(entry) > 4 else "stream"
        base = frozen_cfg()
        flipped = dict(base)
        flipped[key] = literal_cfg()[key]
        if kind == "step_call":
            a, ea = run_probe_frozen_step(text, tokens[0])
        else:
            a, ea = run_probe(text, tokens, base)
        b, eb = run_probe(text, tokens, flipped, kind=kind)
        if ea or eb:
            differs = True
            detail = {"frozen": ea or "raised nothing",
                      "literal": eb or "raised nothing"}
        else:
            d = _diff(a, b)
            differs = bool(d)
            detail = d
        out.append({"clause": key, "board": text, "stream": tokens,
                    "why": why, "kind": kind, "differs": differs,
                    "detail": detail})
    if verbose:
        print("PROBES -- the clauses the FIELD never reached")
        for r in out:
            print("  [%s] %s" % (r["clause"],
                                 "SETTLED BY A SYNTHETIC PROBE"
                                 if r["differs"] else "no difference"))
            print("      board  : %s" % r["board"].replace("\n", " / "))
            print("      stream : %s" % r["stream"])
            print("      why    : %s" % r["why"])
            print("      kind   : %s" % r.get("kind", "stream"))
            print("      frozen vs literal: %s" % (r["detail"],))
            print()
    return out


def frozen_cfg():
    cfg = dict(alt_reading.LITERAL)
    cfg.update({
        "U1_hazard_clock_every": 1,
        "U2_hazard_starts_in_soil": False,
        "U3_target_persists": False,
        "U4_adjacent_kills": False,
        "U5_wait_is_a_turn": False,
        "U7_collection_after_clock": False,
        "U8_hazards_sequential": False,
        "U9_grid_wraps": False,
        "A1_hazards_dig": False,
        "A6_unknown_letter_blocks": False,
        "A8_blocked_is_free": False,
        "A11_tokens": tuple(digdug_reader.GIVE_UP_TOKENS),
        "A13_first_line_is_the_answer": False,
        "A17_counters_from_state": True,
    })
    return cfg


def literal_cfg():
    cfg = dict(alt_reading.LITERAL)
    cfg["A11_tokens"] = ("RESIGN", "GIVEUP")
    cfg["A17_counters_from_state"] = False
    return cfg


def streams_from_bundles(out_dir=RESULTS):
    """The answer streams the frozen cabinet actually produced, read from the
    records on disk.  -> {entrant: {level: [raw answers]}}"""
    out = {}
    for p in sorted(glob.glob(os.path.join(out_dir, "%s_*.json"
                                           % CARD_VERSION))):
        with open(p, "r", encoding="utf-8") as fh:
            b = json.load(fh)
        r = b["results"][0]
        if r.get("never_started"):
            continue
        rounds = r.get("rounds", {}).get("R_digdug_levels", {})
        items = rounds.get("items", {})
        per = {}
        for lvl, it in items.items():
            raws = [ply["reading"]["raw"] for ply in it.get("trace", [])]
            per[lvl] = raws
        out[r["entrant"]] = per
    return out


def _diff(a, b):
    return {k: (a.get(k), b.get(k)) for k in SCORED_FIELDS
            if a.get(k) != b.get(k)}


def cross_check(streams, verbose=True):
    """The second implementation, configured with the FROZEN decisions,
    against the frozen cabinet's own recorded counters."""
    cfg = frozen_cfg()
    agree = disagree = 0
    bad = []
    for p in sorted(glob.glob(os.path.join(RESULTS, "%s_*.json"
                                           % CARD_VERSION))):
        with open(p, "r", encoding="utf-8") as fh:
            b = json.load(fh)
        r = b["results"][0]
        if r.get("never_started"):
            continue
        items = r.get("rounds", {}).get("R_digdug_levels", {}).get("items", {})
        for lvl, it in items.items():
            text = digdug.find_level(lvl).text
            alt = alt_reading.alt_play(text, it["trace"] and
                                       [ply["reading"]["raw"]
                                        for ply in it["trace"]] or [],
                                       cfg=cfg, budget=it["budget"],
                                       name=lvl)
            mine = {k: it.get(k) for k in SCORED_FIELDS}
            d = _diff(mine, alt)
            if d:
                disagree += 1
                bad.append((r["entrant"], lvl, d))
            else:
                agree += 1
    if verbose:
        print("CROSS-CHECK -- the second implementation under the FROZEN "
              "decisions vs the frozen cabinet")
        print("  (entrant, level) pairs compared : %d" % (agree + disagree))
        print("  agree                           : %d" % agree)
        print("  DISAGREE                        : %d" % disagree)
        for e, lvl, d in bad[:12]:
            print("    %-16s %-30s %s" % (e, lvl, d))
        print()
    return agree, disagree, bad


def dividend(streams, verbose=True):
    """The same streams under the LITERAL reading."""
    lit = literal_cfg()
    rows = []
    for ent, per in sorted(streams.items()):
        for lvl, raws in sorted(per.items()):
            text = digdug.find_level(lvl).text
            a = alt_reading.alt_play(text, raws, cfg=frozen_cfg(),
                                     budget=30, name=lvl)
            b = alt_reading.alt_play(text, raws, cfg=lit, budget=30, name=lvl)
            d = _diff(a, b)
            if d:
                rows.append((ent, lvl, d))
    if verbose:
        print("THE DIVIDEND -- identical answer streams, the two readings")
        print("  (entrant, level) pairs that differ : %d of %d"
              % (len(rows), sum(len(v) for v in streams.values())))
        for e, lvl, d in rows:
            print("    %-16s %-30s" % (e, lvl))
            for k, (x, y) in sorted(d.items()):
                print("        %-20s frozen %-14s literal %s" % (k, x, y))
        print()
    return rows


def attribution(streams, verbose=True):
    """Each clause flipped ONE AT A TIME.  A clause that changes nothing on
    this field is NOT EXERCISED -- the running did not settle it, and saying
    otherwise would be a claim with no carrier."""
    base_cfg = frozen_cfg()
    out = []
    for key, mine, theirs in CLAUSES:
        cfg = dict(base_cfg)
        cfg[key] = literal_cfg()[key]
        changed = []
        for ent, per in sorted(streams.items()):
            for lvl, raws in sorted(per.items()):
                text = digdug.find_level(lvl).text
                a = alt_reading.alt_play(text, raws, cfg=base_cfg, budget=30,
                                         name=lvl)
                b = alt_reading.alt_play(text, raws, cfg=cfg, budget=30,
                                         name=lvl)
                d = _diff(a, b)
                if d:
                    changed.append((ent, lvl, d))
        score_changed = sorted({e for e, _l, d in changed if "solved" in d})
        out.append({
            "clause": key, "frozen_reading": mine, "literal_reading": theirs,
            "pairs_changed": len(changed),
            "entrants_changed": sorted({e for e, _l, _d in changed}),
            "score_changed_for": score_changed,
            "settled_by_the_running": bool(changed),
            "detail": changed[:6],
        })
    if verbose:
        print("ATTRIBUTION -- one clause flipped at a time")
        print()
        for r in out:
            verdict = ("SETTLED BY THE RUNNING -- %d pair(s) differ"
                       % r["pairs_changed"]) if r["settled_by_the_running"] \
                else "NOT EXERCISED -- this field never touched it, so the " \
                     "running did NOT settle it"
            print("  [%s] %s" % (r["clause"], verdict))
            print("      frozen : %s" % r["frozen_reading"])
            print("      literal: %s" % r["literal_reading"])
            if r["score_changed_for"]:
                print("      SCORE differs for: %s" % r["score_changed_for"])
            for e, lvl, d in r["detail"][:3]:
                print("        %-16s %-28s %s" % (e, lvl, d))
            print()
    return out


def main(argv=None):
    out = argv[1] if argv and len(argv) > 1 else RESULTS
    streams = streams_from_bundles(out)
    if not streams:
        print("no bundles in %s -- run the field first" % out)
        return 3
    print("streams read from the records: %d entrants, %d (entrant, level) "
          "pairs" % (len(streams), sum(len(v) for v in streams.values())))
    print()
    agree, disagree, bad = cross_check(streams)
    dividend(streams)
    att = attribution(streams)
    settled = [r["clause"] for r in att if r["settled_by_the_running"]]
    un = [r["clause"] for r in att if not r["settled_by_the_running"]]
    pr = probes()
    by_probe = sorted({r["clause"] for r in pr if r["differs"]} & set(un))
    no_run = sorted(set(NOT_SETTLEABLE) & set(un))
    still_open = sorted(set(un) - set(by_probe) - set(no_run))
    print("SUMMARY -- how each open clause was arbitrated")
    print("  the second implementation agrees under the frozen decisions: %s"
          % (disagree == 0))
    print("  SETTLED BY THE FIELD      : %2d  %s" % (len(settled), settled))
    print("  SETTLED BY A SYNTHETIC PROBE, NOT BY THE FIELD: %d  %s"
          % (len(by_probe), by_probe))
    print("  NOT SETTLEABLE BY ANY RUN : %2d  %s" % (len(no_run), no_run))
    for k in no_run:
        print("      %s -- %s" % (k, NOT_SETTLEABLE[k]))
    print("  STILL OPEN, NO CARRIER    : %2d  %s" % (len(still_open),
                                                    still_open))
    print()
    if disagree:
        print("PROSE CHECK INCONCLUSIVE -- the second implementation does not "
              "reproduce the frozen one under identical decisions, so the "
              "divergences above are not attributable to the clauses.")
        return 1
    print("PROSE CHECK PASSED -- divergences attributed to clauses")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
