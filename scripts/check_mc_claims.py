#!/usr/bin/env python3
"""CHECK THE CHECKER -- its denominator, its claims, its mutations and its ceiling. Card t_3abd318f.

WHY THIS FILE EXISTS. The published checker (`scripts/check_mc_field_plain.py`) prints **114/115**, and a
number that looks like a score is not evidence until someone asks WHICH check does not pass, WHY, and
whether any input could make it pass. This instrument asks those questions, plus the three the card puts
beside them, and it does all of it with the FROZEN SIMULATOR on the 22 published records.

  [1] CLAIM vs OUTCOME, per row. Each row carries the entrant's tokens (its target-assignment CLAIM) and
      the record's counters and score (the cabinet's CLAIM). This section computes, from the trajectory
      state alone, what each threat actually did -- DESTROYED by an interceptor, HIT a city, or SPARED
      (impacted empty ground) -- and how many threats the entrant never named (NO-FIRE). It prints the
      computed numbers beside the claimed ones and a DISAGREEMENT COUNT, printed even when it is zero.

  [2] THE RECORDED TRAJECTORY IS A CLAIM TOO. Every record carries a `trace` -- one row per tick, with the
      outcome, the cities alive, the ammo and the threats remaining. The published checker NEVER READS IT:
      it re-derives its own trace and stops there. A record whose `trace` says a city died that the
      simulator does not kill is therefore uncaught by the published checker, and [4b] exhibits exactly
      that, with the published checker's own exit code.

  [3] THE REPLICATION READING, and the honest denominator. The published check that does not pass is the
      P2 token-for-token replication check: it asserts that two runs, minutes apart, on model files this
      cabinet has MEASURED not to be reproducible objects, emitted the same completions. 10 of 12 cells
      do; the two that do not are named, and their SCORES agree. An expectation that requires an identity
      the instrument does not have can fail on a CORRECT record -- the same defect the driver-digest card
      (t_d68e29ba) and the entrant-identity card (t_77f73033) removed from this same checker, one clause
      to the left. So it is a READING here, and what replaces it as a check is the part that IS stable and
      IS falsifiable: the SCORE reproduces on all 12 shared cells, and the two runs are the SAME
      instrument (same simulator, arm and state digest). What is lost is stated, not left to be found:
      token identity was the only defence against a self-consistent token substitution, and on this box it
      could not separate that from a re-run of changed bytes, so it was never a defence that held.

  [4] THE MUTATION MATRIX. Ten mutations -- a trajectory, a target assignment, a claimed hit, a recorded
      trace, a claimed score, an instrument digest, a frozen board, one token copy, and two that are meant
      to survive because they are the residual -- each run through the whole audit, with the check that
      catches it NAMED. [4b] (--mutations) then runs the PUBLISHED checker on a shadow cabinet per
      mutation, so its own exit code is on the record, including the mutation it does not catch. A checker
      whose controls cannot fail is a checker reporting its own input back.

  [5] THE CEILING. If a constant policy -- fire at every threat's impact coordinate, in impact order --
      reaches the maximum, then the cabinet's ceiling is not a measurement of a model. It is printed as a
      RATE against the exhaustive optimum on both frozen levels, beside the entrants' own rate.

CPU only. No model call, no GPU, no lease: every number comes from the records, the simulator and git.

    /usr/bin/python3 scripts/check_mc_claims.py                     # [1][2][3][4][5], ~1 s
    /usr/bin/python3 scripts/check_mc_claims.py --denominator       # + the published checker, in-process
    /usr/bin/python3 scripts/check_mc_claims.py --mutations         # + the shadow-cabinet matrix, slow
"""
import argparse
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CAB = os.path.dirname(HERE)
sys.path.insert(0, CAB)
import missile_command as S                                                     # noqa: E402

LEVELS = ("mc_01_one_shot", "mc_02_scarcity")
ARCHIVE = os.path.join(CAB, "probes", "MC_FIELD_EXAMPLE_ARM_ARCHIVE_20261017.json")
POPULATION = os.path.join(CAB, "probes", "MC_POPULATION_20261017-184752.json")
DECLARATION = os.path.join(CAB, "MC_DECLARATION.md")
PUBLISHED = os.path.join(HERE, "check_mc_field_plain.py")

# THE CHECK THAT DOES NOT PASS, NAMED BY ITS OWN LABEL -- not by an ordinal, because an ordinal rots the
# moment a check is added above it, and this project has already been bitten by exactly that (a bare line
# number that rotted three times in one thread). If the published checker stops emitting this label,
# section [0] reports that instead of silently calling a different check "the 115th".
NOT_PASSING_LABEL = "over 12 cells the tokens reproduce TOKEN-FOR-TOKEN (P2)"

fails, checks, QUIET = [], [], False


def ck(name, got, want):
    ok = got == want
    checks.append((name, ok, got, want))
    if not QUIET:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            print(f"          got  {got!r}\n          want {want!r}")
    if not ok:
        fails.append(name)
    return ok


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def d16(path):
    return sha_file(path)[:16]


# ---------------------------------------------------------------------------------------------- the field
def load_field():
    """The 22 published coordinates, read fresh. The archive fixes WHICH coordinates and what they
    replaced; nothing here is typed."""
    art = json.load(open(ARCHIVE))
    out = []
    for c in art["cells"]:
        p = os.path.join(CAB, c["coordinate"])
        out.append({"coordinate": c["coordinate"], "entrant": c["entrant"], "level": c["level"],
                    "rec": json.load(open(p)), "path": p})
    return out, json.load(open(POPULATION))


def classify(r, state_text):
    """Per-threat outcome from the trajectory the SIMULATOR produces -- not from any claim in the record.

    DESTROYED  an interceptor killed it (the simulator's own `fired` outcome, named in the note)
    HIT        it impacted a city that was still alive
    SPARED     it impacted empty ground
    The simulator resolves anything still airborne after the last action too, so every threat in the state
    is accounted for; the three sets partition the threats, which is what makes the counts add up.
    """
    destroyed, hit, spared = set(), set(), set()
    for row in r["trace"]:
        for part in (row["note"] or "").split("; "):
            m = re.match(r"^(\S+) destroyed$", part)
            if m:
                destroyed.add(m.group(1))
                continue
            m = re.match(r"^(\S+) hit (.+)$", part)
            if m:
                (spared if m.group(2) == "empty ground" else hit).add(m.group(1))
    if r["trace"]:
        leftover = list(r["trace"][-1]["threats_remaining"])
        lost_after = len(r["trace"][-1]["cities_alive"]) - r["cities_surviving"]
    else:
        leftover = sorted(S.parse_state(state_text)["threats"])
        lost_after = S.play(state_text, [])["counts"]["hit"]
    for i, name in enumerate(leftover):
        (hit if i < lost_after else spared).add(name)
    return destroyed, hit, spared


def named_threats(tokens):
    """Which threats the ENTRANT named -- `1P` names P, `PASS` and junk name nothing. This is the entrant's
    claim about what it was engaging; it is compared with the trajectory, never trusted."""
    out = set()
    for tok in tokens:
        t = (tok or "").strip().upper()
        if len(t) == 2 and t != "PASS":
            out.add(t[1])
    return out


def outcome_rows(field):
    rows = []
    for f in field:
        d = f["rec"]
        if not d.get("loaded"):
            rows.append({"entrant": f["entrant"], "level": f["level"], "loaded": False,
                         "why": (d.get("why") or "").splitlines()[0][:50]})
            continue
        r = S.play(d["state_text"], d["tokens"])
        destroyed, hit, spared = classify(r, d["state_text"])
        threats = set(S.parse_state(d["state_text"])["threats"])
        rows.append({
            "entrant": f["entrant"], "level": f["level"], "loaded": True,
            "computed": {"score": r["cities_surviving"], "destroyed": len(destroyed),
                         "hit": len(hit), "spared": len(spared),
                         "no_fire": len(threats - named_threats(d["tokens"])),
                         "threats": len(threats)},
            "claim": {"score": d["score"], "counts": d["counts"]},
            "trace_claim_ok": r["trace"] == d["trace"],
            "token_copies_agree": (d["tokens"] == [t.get("token") for t in d["trace"]]
                                   == [t.get("token") for t in d["turns"]]),
            "recomputed": r,
        })
    return rows


def sim_digest(rec_or_cell, pop=None):
    """The frozen simulator's digest, read from where each artifact actually keeps it: a FIELD RECORD keeps
    it at protocol.clock_audit.simulator_digest, the POPULATION artifact keeps it once for the whole run at
    the same path. Reading it from a key that does not exist would make every comparison None == None and
    call that identity -- the defect this check exists to avoid."""
    if pop is not None and "cells" in pop:  # the population artifact
        return ((pop.get("protocol") or {}).get("clock_audit") or {}).get("simulator_digest")
    return ((rec_or_cell.get("protocol") or {}).get("clock_audit") or {}).get("simulator_digest")


def shared_cells(field, pop):
    pcells = {(c["entrant"], c["level"]): c for c in pop["cells"] if c["arm"] == "plain"}
    out = []
    for f in field:
        k = (f["entrant"], f["level"])
        if k not in pcells or not f["rec"].get("loaded"):
            continue
        p, d = pcells[k], f["rec"]
        a = S.play(d["state_text"], d["tokens"])
        b = S.play(d["state_text"], p["tokens"])
        out.append({"k": k, "d": d, "p": p,
                    "tokens": d["tokens"] == p["tokens"],
                    "score": a["cities_surviving"] == b["cities_surviving"],
                    "counts": a["counts"] == b["counts"],
                    "score_claim": d["score"] == p["score"],
                    "same_instrument": (d.get("state_digest") == p.get("state_digest")
                                        and d.get("legend_digest") == p.get("legend_digest")
                                        and sim_digest(d) == sim_digest(pop, pop)
                                        and d.get("state_path", "").endswith(k[1] + ".txt")),
                    "declaration_digest": (d.get("protocol", {}).get("declaration_digest"),
                                           (pop.get("protocol") or {}).get("declaration_digest")),
                    "server_binary": ((d.get("config") or {}).get("server_binary_digest"),
                                      p.get("server_binary_digest"))})
    return out


# -------------------------------------------------------------------------------------------- the ceiling
def legal_actions(text):
    st = S.parse_state(text)
    return ["PASS"] + [silo + threat for silo, s in st["silos"].items()
                       for threat, t in st["threats"].items()
                       if abs(s["at"] - t["impact"]) <= S.RANGE]


def optimal(text):
    """The exhaustive optimum of the step-locked protocol. Small enough to be exact, which is the point:
    the ceiling must be a MEASUREMENT, not an estimate."""
    st = S.parse_state(text)
    cap = max(t["tick"] for t in st["threats"].values()) + 2
    best = {"score": -1, "tokens": None}
    seen = set()

    def rec(tokens):
        pre = S.play(text, tokens) if tokens else None
        if pre is None:
            alive = sorted(st["threats"])
            ammo = tuple(sorted((k, v["ammo"]) for k, v in st["silos"].items()))
            cities = sorted(st["cities"])
        else:
            tr = pre["trace"][-1]
            alive, ammo, cities = tr["threats_remaining"], tuple(sorted(tr["ammo"].items())), tr["cities_alive"]
        key = (len(tokens), tuple(alive), ammo, tuple(cities))
        if key in seen:
            return
        seen.add(key)
        fin = S.play(text, (tokens + ["PASS"] * (cap - len(tokens)))[:cap])
        if fin["cities_surviving"] > best["score"]:
            best.update(score=fin["cities_surviving"], tokens=list(tokens))
        if len(tokens) >= cap:
            return
        tick = st["tick"] + len(tokens)
        for tok in legal_actions(text):
            if tok == "PASS":
                continue
            silo, threat = tok[0], tok[1]
            if threat not in alive or dict(ammo).get(silo, 0) <= 0:
                continue
            if st["threats"][threat]["tick"] <= tick:
                continue
            rec(tokens + [tok])

    rec([])
    return best


def greedy(text, city_bound_only):
    """THE CONSTANT POLICY. At every tick, fire at the next threat to impact, from the nearest silo that
    can reach it and has ammo. `city_bound_only=False` is the card's trivial policy -- fire at every
    descending trail's base, decoys included, which is what 'spend on everything' means here."""
    st = S.parse_state(text)
    cap = max(t["tick"] for t in st["threats"].values()) + 2
    cities_at = set(st["cities"].values())
    threats, ammo = dict(st["threats"]), {k: v["ammo"] for k, v in st["silos"].items()}
    pos = {k: v["at"] for k, v in st["silos"].items()}
    tokens = []
    for i in range(cap):
        tick = st["tick"] + i
        alive = sorted(((n, t) for n, t in threats.items() if t["tick"] > tick),
                       key=lambda kv: (kv[1]["tick"], kv[0]))
        pick = None
        for name, t in alive:
            if city_bound_only and t["impact"] not in cities_at:
                continue
            cands = sorted((abs(p - t["impact"]), s) for s, p in pos.items()
                           if abs(p - t["impact"]) <= S.RANGE and ammo[s] > 0)
            if cands:
                pick = (cands[0][1] + name, name)
                break
        if pick is None:
            tokens.append("PASS")
        else:
            tokens.append(pick[0])
            ammo[pick[0][0]] -= 1
            del threats[pick[1]]
    return tokens


def level_digest_mismatches(levels_dir=None):
    """A level file that no longer hashes to the digest the declaration names. The input can fail, and
    [4]'s M6 exhibits it by appending a city to a copy."""
    md = open(DECLARATION, encoding="utf-8").read()
    out = []
    for lv in LEVELS:
        p = os.path.join(levels_dir or os.path.join(CAB, "levels"), lv + ".txt")
        if d16(p) not in md:
            out.append(lv)
    return out


# ------------------------------------------------------------------------------------------ the audit
def audit(field, pop, quiet=False):
    global QUIET
    QUIET = quiet
    rows = outcome_rows(field)
    measured = [r for r in rows if r["loaded"]]

    if not quiet:
        print("\n[1] CLAIM vs OUTCOME -- computed from the trajectory state, beside what was claimed")
        print("    hit = the threat impacted a CITY (a city was lost) · miss = it impacted EMPTY GROUND")
        print("    no-fire = no token ever named it · 'claimed' is the record's own counters\n")
        print(f"    {'entrant':40s} {'level':15s} {'score':>7s} {'hit':>4s} {'miss':>5s} {'no-fire':>8s} "
              f"| {'c.score':>7s} {'c.hit':>5s} {'c.miss':>6s}  disagree")
        disagree = 0
        for r in rows:
            if not r["loaded"]:
                print(f"    {r['entrant'][:40]:40s} {r['level']:15s} ATTEMPT -- {r['why']}")
                continue
            c, k = r["computed"], r["claim"]
            bad = (c["score"] != k["score"] or c["hit"] != k["counts"]["hit"]
                   or c["spared"] != k["counts"]["spared"] or c["destroyed"] != k["counts"]["fired"])
            disagree += bad
            print(f"    {r['entrant'][:40]:40s} {r['level']:15s} {str(c['score']):>7s} {c['hit']:>4d} "
                  f"{c['spared']:>5d} {c['no_fire']:>8d} | {str(k['score']):>7s} {k['counts']['hit']:>5d} "
                  f"{k['counts']['spared']:>6d}  {'DISAGREE' if bad else '-'}")
        n = len(measured)
        print(f"\n    DISAGREEMENTS {disagree} of {n} measured rows (printed even when zero, which is "
              f"the point of printing it)")

    ck("every measured row: the SCORE recomputes from (state_text, tokens) -- the cabinet's claim against "
       "the frozen simulator",
       [(r["entrant"], r["level"]) for r in measured
        if r["recomputed"]["cities_surviving"] != r["claim"]["score"]], [])
    ck("every measured row: the nine COUNTERS recompute -- fired, passed, no_ammo, out_of_range, unknown, "
       "malformed, late, hit, spared",
       [(r["entrant"], r["level"]) for r in measured
        if r["recomputed"]["counts"] != r["claim"]["counts"]], [])
    ck("every measured row: the HIT / MISS / NO-FIRE triple computed FROM THE TRAJECTORY equals the "
       "record's own (hit, spared, fired) -- two routes to the same three numbers",
       [(r["entrant"], r["level"]) for r in measured
        if (r["computed"]["destroyed"], r["computed"]["hit"], r["computed"]["spared"])
        != (r["claim"]["counts"]["fired"], r["claim"]["counts"]["hit"], r["claim"]["counts"]["spared"])], [])
    ck("every measured row: the RECORDED `trace` equals the trace re-derived from (state_text, tokens) -- "
       "a field the published checker never reads",
       [(r["entrant"], r["level"]) for r in measured if not r["trace_claim_ok"]], [])
    ck("every measured row: the token stream, the trace's per-tick `token` and the turn log's per-ply "
       "`token` are ONE SEQUENCE -- three copies of one claim, so a substitution that misses a copy is "
       "caught (a substitution that updates all three is the residual, section [4] M9)",
       [(r["entrant"], r["level"]) for r in measured if not r["token_copies_agree"]], [])

    sh = shared_cells(field, pop)
    if not quiet:
        print("\n[3] THE REPLICATION READING -- the field against the population's `plain` arm, cell by cell")
        print(f"    {'entrant':40s} {'level':15s} tokens  score  counters")
        for s in sh:
            print(f"    {s['k'][0][:40]:40s} {s['k'][1]:15s} "
                  f"{'same' if s['tokens'] else 'DIFF':6s}  {'same' if s['score'] else 'DIFF':5s}  "
                  f"{'same' if s['counts'] else 'DIFF'}")
        nt = sum(1 for s in sh if s["tokens"])
        ns = sum(1 for s in sh if s["score"])
        nc = sum(1 for s in sh if s["counts"])
        print(f"\n    TOKENS   {nt} of {len(sh)} reproduce token-for-token  <- A READING, NOT A CHECK")
        print(f"    SCORE    {ns} of {len(sh)} reproduce               <- A CHECK (below)")
        print(f"    COUNTERS {nc} of {len(sh)} reproduce               <- a reading: one junk token moves a "
              f"counter and not the score")
        for s in sh:
            if not s["tokens"]:
                print(f"      DIFFERS  {s['k'][0]} {s['k'][1]}\n"
                      f"               field {s['d']['tokens']}\n               pop   {s['p']['tokens']}")
        dd = sorted({s["declaration_digest"] for s in sh})
        sb = sorted({s["server_binary"] for s in sh})
        print(f"\n    ONE REAL DIFFERENCE AND ONE THAT IS NOT: the DECLARATION FILE digest is {dd[0][0]} in "
              f"the field\n    and {dd[0][1]} in the population -- the file moved when the arm key moved, while the ARM's own digest\n"
              f"    is identical on all {len(sh)} cells and the arm is the operative identity. The SERVING BINARY digest is\n"
              f"    {sb[0][0]} on both sides: the population artifact's `fork` is a PATH, not a different build, and the\n"
              f"    binary digest is the reading that settles it. Neither difference explains a token stream apart, which\n"
              f"    is why a differing stream is not evidence about the FIELD.")
        print("\n    WHY THIS IS NOT A PASS/FAIL EXPECTATION: the check it replaces asserted that two runs on"
              " model files\n    this cabinet MEASURED not to be reproducible objects (Finding A, "
              "MC_FIELD_PLAIN.md) emitted the\n    same completions. It fails on CORRECT records -- the two "
              "above are correct, and their scores agree -- so it\n    is reported as a rate. The "
              "population's own replication control (4 cells, ONE session, one set of bytes)\n    "
              "reproduced 4 of 4, which is why it was reasonable to PREDICT and is not reasonable to "
              "REQUIRE.")

    ck(f"the SCORE reproduces on every shared cell ({len(sh)} of {len(sh)}) -- the outcome the cabinet "
       f"publishes is the stable thing, and this check CAN fail on a self-consistent substitution",
       [s["k"] for s in sh if not s["score"]], [])
    ck(f"...and those {len(sh)} cells were taken by the SAME INSTRUMENT (simulator, arm and state digest "
       f"identical) -- a score that reproduces across two different instruments reproduces nothing",
       [s["k"] for s in sh if not s["same_instrument"]], [])
    ck("...and the two runs CLAIM the same score for those cells, before either is re-derived",
       [s["k"] for s in sh if not s["score_claim"]], [])

    # [5] the ceiling
    texts = {lv: open(os.path.join(CAB, "levels", lv + ".txt")).read() for lv in LEVELS}
    rates = {}
    if not quiet:
        print("\n[5] THE CEILING -- what a constant policy reaches, which is the baseline any model result "
              "must beat")
        print(f"    {'level':15s} {'policy':46s} {'score':>7s}  rate")
    for lv in LEVELS:
        text = texts[lv]
        optimum = optimal(text)["score"]
        n = S.play(text, [])["cities_total"]
        for label, toks in (("PASS always", ["PASS"] * 8),
                            ("spend on EVERY threat (the trivial policy)", greedy(text, False)),
                            ("spend on every CITY-BOUND threat", greedy(text, True))):
            sc = S.play(text, toks)["cities_surviving"]
            rates[(lv, label)] = sc
            if not quiet:
                print(f"    {lv:15s} {label:46s} {sc}/{n:<5d}  {100.0 * sc / max(optimum, 1):5.1f}% of "
                      f"optimal")
        if not quiet:
            print(f"    {lv:15s} {'OPTIMAL (exhaustive search)':46s} {optimum}/{n:<5d}  100.0%   "
                  f"{optimal(text)['tokens']}")
    if not quiet:
        print("\n    THE RATE THE CONSTANT POLICY ACHIEVES -- the human baseline the cabinet must subtract:")
        for lv in LEVELS:
            opt = optimal(texts[lv])["score"]
            triv = rates[(lv, "spend on EVERY threat (the trivial policy)")]
            print(f"      {lv:15s} {triv}/{opt} = {100.0 * triv / max(opt, 1):5.1f}% of the optimum")
        for lv in LEVELS:
            sc = [r["computed"]["score"] for r in measured if r["level"] == lv]
            opt = optimal(texts[lv])["score"]
            triv = rates[(lv, "spend on EVERY threat (the trivial policy)")]
            print(f"      entrants {lv:15s} mean {sum(sc) / len(sc):.3f} of {opt} "
                  f"({100.0 * (sum(sc) / len(sc)) / max(opt, 1):5.1f}% of optimal); "
                  f"{sum(1 for s in sc if s >= triv)} of {len(sc)} reach the trivial policy's score")

    ck("the two frozen level files hash to the digests MC_DECLARATION.md names (the ceiling is computed on "
       "the board the cabinet declares, not on a file that happens to be there)",
       level_digest_mismatches(), [])
    ck("the exhaustive optimum EQUALS the trivial city-bound policy's score on both levels -- two "
       "implementations agreeing is the only evidence that either is right",
       [lv for lv in LEVELS
        if optimal(texts[lv])["score"] != rates[(lv, "spend on every CITY-BOUND threat")]], [])

    if not quiet:
        print("\n    THE BOARD, CENSUSED FROM THE STATE AND NOT FROM THE LEVEL FILE'S PROSE:")
        for lv in LEVELS:
            st = S.parse_state(texts[lv])
            city_at = set(st["cities"].values())
            bound = sorted(n for n, t in st["threats"].items() if t["impact"] in city_at)
            decoy = sorted(n for n, t in st["threats"].items() if t["impact"] not in city_at)
            print(f"      {lv:15s} threats {len(st['threats'])}  city-bound {len(bound)} {bound}  "
                  f"decoys {len(decoy)} {decoy}  rounds {sum(v['ammo'] for v in st['silos'].values())}")
        print("    AND THE LEVEL FILE'S OWN COMMENT IS WRONG ABOUT ITS OWN BOARD: mc_02's prose says "
              "\"SEVEN THREATS\"\n    (the state has eight) and \"T -> 4 city\" (impact 4 is empty ground: "
              "cities sit at 2, 3, 5 and 6).\n    THE PARSER IGNORES COMMENTS, so no score moves -- and "
              "the file is FROZEN, so it is recorded here\n    and not edited. It matters because T is a "
              "DECOY that the prose calls a city: an entrant that read the prose\n    instead of the state "
              "would spend a round defending nothing, and this ceiling section would report that as\n"
              "    a choice rather than as a misreading.")
    QUIET = False
    return rows, sh


# ------------------------------------------------------------------------------------------ mutation test
def mutate(field, pop, which):
    """One named mutation on deep copies. The mutation does not decide which check catches it: the audit
    does."""
    f, p = copy.deepcopy(field), copy.deepcopy(pop)

    def rec_of(entrant, level):
        return next(x for x in f if x["entrant"] == entrant and x["level"] == level)

    def pop_cell(entrant="Qwen3.5-2B-UD-Q4_K_XL", level="mc_01_one_shot"):
        return next(c for c in p["cells"] if c["arm"] == "plain" and c["entrant"] == entrant
                    and c["level"] == level)

    if which == "M1 trajectory: a threat's impact moves from a city to empty ground":
        x = rec_of("Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0", "mc_02_scarcity")["rec"]
        x["state_text"] = x["state_text"].replace("threat S impact 6 tick 4", "threat S impact 8 tick 4")
    elif which == "M2 target assignment: a token names another threat":
        rec_of("OculusMind-ToolCall-8B-v2.i1-Q4_K_M", "mc_01_one_shot")["rec"]["tokens"] = ["1Q"]
    elif which == "M3 claimed hit: counts.hit +1 and the score and the record paid for it":
        x = rec_of("Mellum2.1-12B-A2.5B-Thinking-Q4_K_M", "mc_01_one_shot")["rec"]
        x["counts"]["hit"] += 1
        x["score"] -= 1
        x["cities_surviving"] -= 1
    elif which == "M4 recorded trajectory: the trace says a city died":
        rec_of("Qwen3.5-2B-UD-Q4_K_XL", "mc_01_one_shot")["rec"]["trace"][0]["cities_alive"] = []
    elif which == "M5 claim: the population's claimed score is altered on a shared cell":
        pop_cell()["score"] = 0
    elif which == "M6 instrument: the population's simulator_digest is altered on a shared cell":
        p["protocol"]["clock_audit"]["simulator_digest"] = "deadbeefdeadbeef"
    elif which == "M10 token copies: ONE copy of the token stream is substituted":
        rec_of("LFM2-350M-Extract-Q4_K_M", "mc_01_one_shot")["rec"]["tokens"] = ["Q", "Q", "Q"]
    else:
        raise SystemExit(f"unknown mutation {which}")
    return f, p


FAST_MUTATIONS = [
    "M1 trajectory: a threat's impact moves from a city to empty ground",
    "M2 target assignment: a token names another threat",
    "M3 claimed hit: counts.hit +1 and the score and the record paid for it",
    "M4 recorded trajectory: the trace says a city died",
    "M5 claim: the population's claimed score is altered on a shared cell",
    "M6 instrument: the population's simulator_digest is altered on a shared cell",
    "M10 token copies: ONE copy of the token stream is substituted",
]


def isolated_audit(field, pop):
    """Run the whole audit with its output swallowed and return (its check results, failures)."""
    saved_checks, saved_fails = list(checks), list(fails)
    checks.clear()
    fails.clear()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        audit(field, pop, quiet=True)
    result = list(checks)
    fired = [c for c, ok, _, _ in result if not ok]
    checks.clear()
    checks.extend(saved_checks)
    fails.clear()
    fails.extend(saved_fails)
    return result, fired


def run_mutations(field, pop):
    print("\n[4] THE MUTATION MATRIX -- every mutation must be caught by a NAMED check")
    survivors = []
    for m in FAST_MUTATIONS:
        f2, p2 = mutate(field, pop, m)
        _, fired = isolated_audit(f2, p2)
        print(f"  {'CAUGHT ' if fired else 'SURVIVED'}  {m}")
        for name in fired:
            print(f"             fired: {name}")
        if not fired:
            survivors.append(m)

    # M7 is on the frozen board, not the field: append a city to a COPY of the level file and read the
    # digest check against that copy.
    tmp = tempfile.mkdtemp(prefix="mc-level-")
    os.makedirs(os.path.join(tmp, "levels"))
    for lv in LEVELS:
        shutil.copy(os.path.join(CAB, "levels", lv + ".txt"), os.path.join(tmp, "levels", lv + ".txt"))
    with open(os.path.join(tmp, "levels", "mc_01_one_shot.txt"), "a", encoding="utf-8") as fh:
        fh.write("city B at 9\n")
    got = level_digest_mismatches(os.path.join(tmp, "levels"))
    ok = bool(got) and not level_digest_mismatches()
    print(f"  {'CAUGHT ' if ok else 'SURVIVED'}  M7 frozen board: a level file gains a city")
    if got:
        print(f"             fired: the level-digest check would name {got}")
    if not ok:
        survivors.append("M7 frozen board: a level file gains a city")
    shutil.rmtree(tmp, ignore_errors=True)

    # M8 is the CEILING's own control: the "two implementations agree" check is only evidence if a policy
    # that is NOT optimal makes it fail. Feed it the wrong policy and it must name the level.
    texts = {lv: open(os.path.join(CAB, "levels", lv + ".txt")).read() for lv in LEVELS}
    wrong = [lv for lv in LEVELS
             if optimal(texts[lv])["score"] != S.play(texts[lv], greedy(texts[lv], False))["cities_surviving"]]
    print(f"  {'CAUGHT ' if wrong else 'SURVIVED'}  M8 the ceiling's own control: the wrong policy (spend on "
          f"EVERY threat) disagrees with the optimum")
    if wrong:
        print(f"             fired: the two-implementation check would name {wrong}")
    if not wrong:
        survivors.append("M8 the ceiling's own control")

    ck("every mutation M1-M8 is caught by at least one NAMED check", survivors, [])

    # M9 IS THE RESIDUAL, AND IT IS MEANT TO SURVIVE. A token stream is the record's own account of what
    # the entrant said; for a cell the population never measured there is no second copy, so a substitution
    # that preserves every counter is invisible. This is not a defect of the mutation -- it is the coverage
    # the cabinet does not have, asserted as a check so that it FIRES if someone ever closes it.
    f9, p9 = copy.deepcopy(field), copy.deepcopy(pop)
    x9 = next(x for x in f9 if x["entrant"].startswith("LFM2-350M") and x["level"] == "mc_01_one_shot")["rec"]
    x9["tokens"] = ["Q", "Q", "Q"]      # junk for junk: three malformed tokens either way
    x9["trace"] = S.play(x9["state_text"], x9["tokens"])["trace"]   # RE-RECORDED, not edited
    x9["counts"] = S.play(x9["state_text"], x9["tokens"])["counts"]
    for t in x9["turns"]:
        t["token"] = "Q"
    _, fired9 = isolated_audit(f9, p9)
    print(f"  {'SURVIVED' if not fired9 else 'CAUGHT  '}  M9 a SELF-CONSISTENT token substitution on a cell "
          f"the population never measured (`{{`x3 -> `Q`x3, all three copies)")
    if fired9:
        for name in fired9:
            print(f"             fired: {name}")
    ck("...and the RESIDUAL is real: a substitution that changes no counter and sits on one of the 10 cells "
       "the population never measured passes EVERY check -- the cabinet cannot separate it from the record "
       "it replaced, because the record is its own only copy (if this ever fails, the residual has closed)",
       not fired9, True)


# ------------------------------------------------------------------------- [4b] the published checker
SHADOW_MUTATIONS = [
    ("P0  no mutation -- the copy is faithful", None),
    ("P1  recorded trajectory (`trace`) altered", ("trace", "Qwen3.5-2B-UD-Q4_K_XL", "mc_01_one_shot")),
    ("P2  claimed hit altered (counts.hit +1, score -1)", ("hit", "Mellum2.1-12B-A2.5B-Thinking-Q4_K_M", "mc_01_one_shot")),
    ("P3  target assignment altered (`1P` -> `1Q`)", ("tokens", "OculusMind-ToolCall-8B-v2.i1-Q4_K_M", "mc_01_one_shot")),
    ("P4  state trajectory altered (S impacts empty ground)", ("state", "Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0", "mc_02_scarcity")),
    ("P5  the population's two differing token lists set equal", ("pop", None, None)),
    ("P6  the guard at #115: the two differing cells leave the shared set, so it holds 10", ("poplabel", None, None)),
]


def apply_shadow(root, mutation):
    if mutation is None:
        return
    kind, entrant, level = mutation
    if kind == "pop":
        p = os.path.join(root, "probes", os.path.basename(POPULATION))
        pop = json.load(open(p))
        for c in pop["cells"]:
            if c["arm"] != "plain":
                continue
            f = json.load(open(os.path.join(CAB, "probes", f"MC_{c['entrant']}_{c['level']}.json")))
            if f.get("loaded"):
                c["tokens"] = f["tokens"]
        json.dump(pop, open(p, "w"))
        return
    if kind == "poplabel":
        p = os.path.join(root, "probes", os.path.basename(POPULATION))
        pop = json.load(open(p))
        for entrant, level in (("Mellum2.1-12B-A2.5B-Thinking-Q4_K_M", "mc_01_one_shot"),
                               ("MiMo-V2.6-Distill-Qwen-9B-Q4_K_M", "mc_02_scarcity")):
            c = next(c for c in pop["cells"] if c["arm"] == "plain"
                     and c["entrant"] == entrant and c["level"] == level)
            c["entrant"] = c["entrant"] + "-LABEL-CHANGED"
        json.dump(pop, open(p, "w"))
        return
    path = os.path.join(root, "probes", f"MC_{entrant}_{level}.json")
    d = json.load(open(path))
    if kind == "trace":
        d["trace"][0]["cities_alive"] = []
    elif kind == "hit":
        d["counts"]["hit"] += 1
        d["score"] -= 1
        d["cities_surviving"] -= 1
    elif kind == "tokens":
        d["tokens"] = ["1Q"]
    elif kind == "state":
        d["state_text"] = d["state_text"].replace("threat S impact 6 tick 4", "threat S impact 8 tick 4")
    json.dump(d, open(path, "w"))


def shadow_matrix():
    print("\n[4b] THE PUBLISHED CHECKER ON A SHADOW CABINET -- its own exit code per mutation")
    print("     (a copy of this tree in a temp dir; the real tree is never written; git history is read "
          "from the real\n     tree through MC_DRIVER_HISTORY_REPO, which the checker supports)")
    env = dict(os.environ, MC_DRIVER_HISTORY_REPO=CAB)
    res = {}
    for label, mutation in SHADOW_MUTATIONS:
        tmp = tempfile.mkdtemp(prefix="mc-shadow-")
        root = os.path.join(tmp, "cab")
        shutil.copytree(CAB, root, ignore=shutil.ignore_patterns("__pycache__", ".git", "logs"),
                        copy_function=shutil.copy2)
        apply_shadow(root, mutation)
        r = subprocess.run([sys.executable, os.path.join(root, "scripts", "check_mc_field_plain.py")],
                           cwd=root, capture_output=True, text=True, env=env)
        bad = [ln[len("  FAIL  "):].strip() for ln in r.stdout.splitlines() if ln.startswith("  FAIL  ")]
        total = ""
        for ln in r.stdout.splitlines():
            m = re.search(r"(\d+)/(\d+)\s*$", ln)
            if m:
                total = m.group(0)
        res[label[:2]] = {"rc": r.returncode, "bad": bad, "total": total}
        print(f"  rc {r.returncode}  {total:>7s}  {label}")
        for b in bad:
            print(f"          FAIL  {b}")
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n     READ THE COLUMN, NOT THE HEADLINE: P1 (the recorded trajectory) leaves the published "
          "checker at the\n     same 114/115, rc 1 -- the same single failure as the unmutated field. The "
          "checker cannot see the\n     record's own trace. P5 is the demoted check made to PASS on a "
          "mutated population artifact: 115/115, rc 0 --\n     which is the proof that it is a LIVE "
          "control and not one that cannot fire, and the proof that what it\n     measures is the token "
          "stream, not the cabinet. P6 makes the GUARD BELOW IT fire by removing a shared cell\n     from "
          "the comparison: the non-vacuity check is live too. P0 is the copy's own control.")

    caught = []
    for p, entrant in (("P2", "Mellum2.1-12B"), ("P3", "OculusMind-ToolCall-8B"), ("P4", "Ternary-Bonsai-2-9B")):
        ok = res[p]["rc"] != 0 and any(entrant in b for b in res[p]["bad"])
        caught.append(p if ok else f"{p} NOT CAUGHT")
    ck("the published checker CATCHES the claimed-hit, target-assignment and state-trajectory mutations, "
       "naming the mutated record's own coordinate", caught, ["P2", "P3", "P4"])
    ck("...is FALSIFIABLE IN THE OTHER DIRECTION: with the two differing token lists made equal (P5) the "
       "same check PASSES and the checker reports 115/115, rc 0 -- it is not a control that cannot fire",
       [res["P5"]["rc"], res["P5"]["total"]], [0, "115/115"])
    ck("...and the non-vacuity guard BELOW it (the literal 115th emitted check) fires when the shared set "
       "drops to 10, while #114 PASSES -- the guard is live AND is not a copy of the check above",
       [res["P6"]["rc"], "over exactly 12 cells" in " ".join(res["P6"]["bad"]),
        NOT_PASSING_LABEL in " ".join(res["P6"]["bad"])], [1, True, False])
    ck("...and the RECORDED TRAJECTORY is INVISIBLE to it: P1's failure set is IDENTICAL to the "
       "unmutated copy's (P0) -- measured, not assumed; if this ever fails, the gap has been closed and "
       "this finding must be revised",
       [res["P1"]["rc"], res["P1"]["bad"]], [res["P0"]["rc"], res["P0"]["bad"]])


# ------------------------------------------------------------------------------------ [0] the denominator
def run_published():
    """Run the published checker IN THIS PROCESS so its checks can be enumerated in its own order, without
    editing it. Returns (rc, [(ordinal, ok, label, got, want)], captured output)."""
    spec = importlib.util.spec_from_file_location("mc_published_under_audit", PUBLISHED)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    got = []
    real = mod.ck

    def ck_wrap(name, g, w):
        ok = real(name, g, w)
        got.append((len(got) + 1, ok, name, g, w))
        return ok

    mod.ck = ck_wrap
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.main()
    return rc, got, buf.getvalue()


def denominator():
    print("\n[0] THE DENOMINATOR -- the published checker, run in this process and enumerated in its own "
          "order")
    rc, got, out = run_published()
    bad = [g for g in got if not g[1]]
    print(f"    checks emitted {len(got)}   passing {len(got) - len(bad)}   failing {len(bad)}   exit code "
          f"{rc}")
    for n, ok, name, g, w in bad:
        print(f"      #{n} FAIL  {name}")
        print(f"            got  {g!r}")
        print(f"            want {w!r}")
    ck("the check that does not pass is the one this file names in its header -- by LABEL, because an "
       "ordinal rots when a check is added above it",
       [g[2] for g in bad], [NOT_PASSING_LABEL])
    if not bad:
        print("    THE PUBLISHED CHECKER HAS NO FAILING CHECK IN THIS TREE -- the premise of this card's "
              "denominator question is gone, and section [3] is the reading that has to be re-taken.")
        return
    n = bad[0][0]
    print(f"""
    THE DECISION -- THE CHECK THAT DOES NOT PASS IS THE P2 REPLICATION CHECK, #{n} OF {len(got)} IN THE
    CHECKER'S OWN ORDER, AND IT IS DEMOTED TO A READING.
      IS THERE AN INPUT THAT MAKES IT FAIL?  YES, and it is on disk at this commit: the 22 published
        records plus the population artifact, exit {rc}. Section [4]'s M1-M7 and [4b]'s P1-P4 exhibit
        further ones.
      IS THERE AN INPUT THAT MAKES IT PASS?  YES: [4b]'s P5 sets the two differing token lists in a COPY
        of the population artifact to the field's own and the checker reports {len(got)}/{len(got)}, rc 0.
        So it is a LIVE control: neither dead code nor a control that cannot fire.
      THEN WHY DEMOTE IT?  Because its pass condition is an identity this cabinet MEASURED NOT TO EXIST.
        It requires two runs, minutes apart, to emit identical completions from model files whose bytes
        the cabinet measured to be non-reproducible (Finding A). 10 of 12 cells reproduce; the two that
        do not are CORRECT records -- their scores agree, and the cabinet's own filed explanation
        (Finding B) says why. An expectation that fails on a correct record is a permanent red lamp, and
        a permanent red lamp hides the next real regression inside a failure that is expected every run.
        This is the third instance of one class in this one checker, after t_d68e29ba (driver digest) and
        t_77f73033 (entrant identity): AN IDENTITY ASSERTED THAT WAS MEASURED NOT TO EXIST.
      THE HONEST DENOMINATOR AFTER THE DEMOTION: {len(got) - 1}/{len(got) - 1}.
      WHAT COVERAGE IS LOST, NAMED: token-level provenance against an independent run, over the 12 shared
        cells -- previously the only thing that could notice a token stream substituted for another that
        scores the same. It is lost because it could not be relied on: on this box a genuine re-run trips
        it too, so it could not separate a substitution from a changed entrant file. What is KEPT as a
        check is the part that IS stable and IS falsifiable: the SCORE reproduces on 12 of 12, and the
        two runs are the same instrument. What no check can do on this box is stated in the report.""")


# --------------------------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--denominator", action="store_true", help="run the published checker in-process")
    ap.add_argument("--mutations", action="store_true", help="run the shadow-cabinet matrix (slow)")
    a = ap.parse_args()

    print("=" * 100)
    print("CHECK THE CHECKER -- claims, trajectory, denominator, mutations, ceiling (card t_3abd318f)")
    print("=" * 100)
    print(f"  cabinet {CAB}")
    print(f"  driver {d16(os.path.join(CAB, 'missile_command_run.py'))}   "
          f"simulator {d16(os.path.join(CAB, 'missile_command.py'))}   "
          f"declaration {d16(DECLARATION)}")

    field, pop = load_field()
    audit(field, pop)
    run_mutations(field, pop)
    if a.mutations:
        shadow_matrix()
    if a.denominator:
        denominator()

    print("""
[6] WHAT THIS CABINET CANNOT SEPARATE -- stated, because a score without its residual is a claim
    1. A DIFFERING TOKEN STREAM FROM A CHANGED ENTRANT. The model files are not reproducible objects on
       this box (Finding A): two runs that record the same `entrant_digest` may not have read the same
       bytes, and the same session is the only setting in which replication was measured to hold (4 of 4
       cells). So a token stream that differs from the population's is not evidence about the record.
    2. A SELF-CONSISTENT SUBSTITUTION ON THE 10 CELLS THE POPULATION NEVER MEASURED. [4] M9 re-records one
       of them with a different token stream that produces the same counters: no check fires, because the
       record is its own only copy. The 12 shared cells are covered for anything that moves the SCORE;
       a substitution that moves no number is covered only where a second copy exists, and it is lost
       precisely because the copy it was compared against is not a stable object either.
    3. A MODEL FROM A FOUR-LINE PROGRAM. The exhaustive optimum is reached by a constant policy that
       reads the impact coordinates and fires at the city-bound threats in impact order: 1/1 on mc_01
       and 4/4 on mc_02. The score therefore cannot separate a model that plays from a policy that reads.
    4. ONE RUN FROM ANOTHER. n = 1 per cell, one state set, one arm. There is no within-cell variance to
       measure, so 'this model plays better' is a statement about two single runs on a box whose entrant
       bytes move between them.
    5. THE ENTRANT'S BYTES FROM A FILE OF THE SAME SIZE. Per the ruling on t_7f400932 the identity is
       st_size, because the digest does not reproduce. Two rows with the same size are not thereby the
       same weights, and no field in the records can settle it.""")

    print("\n" + "=" * 100)
    print(f"{'ALL CHECKS PASS' if not fails else str(len(fails)) + ' CHECKS FAILED'}   --  "
          f"{len(checks) - len(fails)}/{len(checks)}")
    print("=" * 100)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
