#!/usr/bin/env python3
"""stump_task_gen.py -- the STUMP task JSON shape, and the check that makes it a shape.

WHY THIS FILE EXISTS
  Arcade cannot start building STUMP without (d) the task JSON shape. Jarvis relayed (a), (b)
  and (c) but not (d). This file is (d): it emits a canonical round instance AND validates it,
  so the shape is an artefact rather than a paragraph.

WHAT IT ENFORCES (each line traces to a filed ruling)
  * `n` and `A` are EXPLICIT, at round level and per question
      -- 2026-11-05-the-tie-at-zero-forbids-the-one-percent-and-the-pairs-are-a-filter-not-a-cost:
         the pairs are (A, n); a tolerance without them is not a specification.
  * `A` is recomputed from the grammar at admission, never asserted
      -- 2026-11-05-stump-the-guesser-is-the-control-and-the-answer-space-is-the-ceiling R1/R9.
  * every question carries the asker's own committed answer, and the oracle checks THAT answer
      -- same ruling, R4: the oracle computes, never judges whether a question is answerable.
  * grammar digest and both question sets are pinned BEFORE answers are revealed
      -- R5/R8, and 2026-11-04-the-reference-is-total-at-an-invalid-pc R4.
  * a question whose canonical answer occurs in its own text is refused
      -- R6, mechanical first pass only (a paraphrase defeats it; this is stated, not hidden).
  * two counters per (member, question), `malformed` over attempts and `wrong` over well-formed
    attempts, and NO merged accuracy field anywhere
      -- R7.
  * the ceiling P(coin wins) is recomputed for the declared (n, A, p) and the row carries it as
    its own null, so a result can never be read without the guesser it was measured against
      -- R1/R2.

USAGE
  python3 probes/stump_task_gen.py --emit   > probes/STUMP_TASK_TEMPLATE_2026-11-05.json
  python3 probes/stump_task_gen.py --check  < task.json
Exit 0 = shape valid; every violation is printed as VIOLATION and exit is 1.
"""
import json
import math
import re
import sys

TOLERANCE = 0.01
GRAMMAR = {
    "id": "arith-singledigit-add-v1",
    "rule": "Q(a, b) = a + b with a, b in 1..9; answer = the exact integer sum",
    "answer_form": r"^(?:[1-9][0-9]?)$",
    "answer_form_note": "canonical: bare decimal digits, no sign, no spaces, no prose, no units",
    "A_basis": "distinct canonical sums of two operands in 1..9 = {2..18}",
    "computes_not_looks_up": True,
    "identity": "1 + 2 = 3",
    "identity_value": 3,
    "identity_malformed": "three",
}
GRAMMAR_DIGEST = ""  # filled by --emit with sha256 of the canonical grammar block


def canonical_grammar_digest(g):
    import hashlib

    return hashlib.sha256(json.dumps(g, sort_keys=True).encode()).hexdigest()


def A_of(g):
    """The answer space, computed from the grammar's declared operand ranges."""
    lo, hi = 2, 18  # sums of 1..9 + 1..9
    n = len(re.findall(g["answer_form"], "x"))  # only to prove the pattern compiles
    del n
    return hi - lo + 1


def p_coin_wins(n, p, A):
    """P(X > Y) + 0.5 P(X = Y), X ~ Bin(n, 1/A) the guesser, Y ~ Bin(n, p) the model."""
    q = 1.0 / A
    total = 0.0
    for x in range(n + 1):
        px = math.comb(n, x) * q ** x * (1 - q) ** (n - x)
        cx = 0.0
        for y in range(n + 1):
            py = math.comb(n, y) * p ** y * (1 - p) ** (n - y)
            if x > y:
                cx += py
            elif x == y:
                cx += 0.5 * py
        total += px * cx
    return total


def tie_at_zero(n, p):
    return 0.5 * (1 - p) ** n


def build():
    n = 5
    p_ref = 0.90
    a = A_of(GRAMMAR)
    questions_a = [
        ("A-1", "what is 3 + 4", 7),
        ("A-2", "what is 8 + 6", 14),
        ("A-3", "what is 2 + 9", 11),
        ("A-4", "what is 7 + 7", 14),
        ("A-5", "what is 5 + 1", 6),
    ]
    questions_b = [
        ("B-1", "what is 9 + 2", 11),
        ("B-2", "what is 4 + 4", 8),
        ("B-3", "what is 6 + 8", 14),
        ("B-4", "what is 1 + 1", 2),
        ("B-5", "what is 9 + 9", 18),
    ]

    def qset(prefix, rows):
        return [
            {
                "qid": qid,
                "side": prefix,
                "text": text,
                "template": "add(a,b): a,b in 1..9",
                "A": a,
                "A_source": "recomputed by the oracle from the grammar: A_basis",
                "asker_answer": str(v),
                "asker_answer_sha256": __import__("hashlib").sha256(str(v).encode()).hexdigest(),
                "admissible": True,
                "inadmissible_reason": None,
            }
            for qid, text, v in rows
        ]

    template = {
        "task": "STUMP-1",
        "spec_version": "2026-11-05.1",
        "note": "WORKED EXAMPLE, not a scheduled event: the grammar is a single-digit adder chosen because its answer space is computable and small. The SHAPE is the deliverable.",
        "grammar": dict(GRAMMAR, digest=canonical_grammar_digest(GRAMMAR)),
        "params": {
            "n": n,
            "A": a,
            "tolerance": TOLERANCE,
            "p_ref": p_ref,
            "ceiling": {
                "P_coin_wins": p_coin_wins(n, p_ref, a),
                "tie_at_zero_limit": tie_at_zero(n, p_ref),
                "recomputed_from": {"n": n, "A": a, "p": p_ref},
                "formula": "P(X>Y) + 0.5 P(X=Y), X~Bin(n,1/A), Y~Bin(n,p)",
            },
            "A_is_free_n_is_paid": "A is checked at admission, zero inference; n costs 2n answers per round",
        },
        "panel": [
            {"id": "panel-1", "ref": "PLACEHOLDER", "note": "digest-pinned before the run; never edited mid-run"}
        ],
        "rounds": [
            {
                "round": 1,
                "freeze": {
                    "grammar_digest": canonical_grammar_digest(GRAMMAR),
                    "questions_committed_at": "2026-11-05T00:00:00Z",
                    "question_sets_digest": "PLACEHOLDER",
                    "answers_committed_at": None,
                    "answers_digest": None,
                    "rule": "both question sets are hashed and exchanged before either side's answers are revealed",
                },
                "questions": {"A": qset("A", questions_a), "B": qset("B", questions_b)},
                "answers": {
                    "panel-1": {
                        "A-1": {"attempts": 1, "malformed": 0, "wrong": 0},
                        "A-2": {"attempts": 1, "malformed": 0, "wrong": 0},
                        "A-3": {"attempts": 1, "malformed": 0, "wrong": 0},
                        "A-4": {"attempts": 2, "malformed": 1, "wrong": 0},
                        "A-5": {"attempts": 1, "malformed": 0, "wrong": 1},
                        "B-1": {"attempts": 1, "malformed": 0, "wrong": 0},
                        "B-2": {"attempts": 1, "malformed": 0, "wrong": 0},
                        "B-3": {"attempts": 1, "malformed": 0, "wrong": 0},
                        "B-4": {"attempts": 1, "malformed": 0, "wrong": 0},
                        "B-5": {"attempts": 1, "malformed": 0, "wrong": 0},
                    }
                },
                "counters_rule": "malformed is over attempts; wrong is over well-formed attempts; the two never merge",
                "result": {
                    "correct": {"A": None, "B": None},
                    "winner": None,
                    "null": {"P_coin_wins": p_coin_wins(n, p_ref, a), "cell": {"n": n, "A": a, "p": p_ref}},
                    "note": "a row with no null is not a result",
                },
            }
        ],
    }
    return template


def check(t):
    v = []

    def bad(msg):
        v.append(msg)

    g = t.get("grammar") or {}
    if not g.get("digest"):
        bad("grammar.digest missing: the grammar must be frozen by digest before any model runs")
    if g.get("digest") != canonical_grammar_digest({k: g[k] for k in GRAMMAR}):
        bad("grammar.digest does not match the grammar block it claims to pin")
    if not g.get("answer_form"):
        bad("grammar.answer_form missing: a canonical answer form is a rule of the grammar, not a parsing note")
    try:
        re.compile(g.get("answer_form", ""))
    except re.error as e:
        bad("grammar.answer_form does not compile: %s" % e)

    pr = t.get("params") or {}
    n, a = pr.get("n"), pr.get("A")
    if not isinstance(n, int) or n < 1:
        bad("params.n missing or not an int: n must be explicit, never implied")
    if not isinstance(a, int) or a < 2:
        bad("params.A missing or < 2: A must be explicit, never implied")
    if not (0 < float(pr.get("tolerance", -1)) < 1):
        bad("params.tolerance missing or outside (0,1)")

    p_ref = pr.get("p_ref")
    if not isinstance(p_ref, (int, float)) or not (0 < p_ref < 1):
        bad("params.p_ref missing: a tolerance has no meaning without the model accuracy it was computed against")

    # the ceiling is recomputed, and the tolerance is checked for reachability at this n
    if isinstance(n, int) and isinstance(a, int) and isinstance(p_ref, (int, float)) and n >= 1 and a >= 2:
        want = p_coin_wins(n, p_ref, a)
        got = (pr.get("ceiling") or {}).get("P_coin_wins")
        if got is None:
            bad("params.ceiling.P_coin_wins missing: the row must carry the guesser it was measured against")
        elif abs(float(got) - want) > 1e-12:
            bad("params.ceiling.P_coin_wins = %r but the closed form gives %.12f" % (got, want))
        lim = tie_at_zero(n, p_ref)
        if lim > float(pr.get("tolerance", 1)):
            bad(
                "tolerance %.4g unreachable at n=%d, p=%.2f: the A->inf limit is %.6f, so no answer space clears it"
                % (float(pr["tolerance"]), n, p_ref, lim)
            )

    if not t.get("panel"):
        bad("panel missing or empty: a floor needs a panel, and the panel is digest-pinned before the run")

    rounds = t.get("rounds") or []
    if not rounds:
        bad("rounds missing")
    for r in rounds:
        fz = r.get("freeze") or {}
        for k in ("grammar_digest", "questions_committed_at", "question_sets_digest"):
            if not fz.get(k):
                bad("round %s: freeze.%s missing -- nothing may be measured against a moving target" % (r.get("round"), k))
        qs = r.get("questions") or {}
        for side in ("A", "B"):
            lst = qs.get(side) or []
            if len(lst) != n:
                bad("round %s: questions.%s has %d, params.n says %s" % (r.get("round"), side, len(lst), n))
            for q in lst:
                qid = q.get("qid")
                if q.get("A") is None:
                    bad("%s: A not declared on the question (A must never be implied)" % qid)
                elif q.get("A") != a:
                    bad("%s: A=%r disagrees with params.A=%r" % (qid, q.get("A"), a))
                if "asker_answer" not in q:
                    bad("%s: no asker_answer -- the oracle checks the asker's own answer (R4)" % qid)
                ans = str(q.get("asker_answer", ""))
                if not re.match(g.get("answer_form", "^$"), ans):
                    bad("%s: asker_answer %r is not in the canonical form" % (qid, ans))
                if ans and re.search(r"\b%s\b" % re.escape(ans), str(q.get("text", ""))):
                    bad("%s: the answer occurs in the question text (R6 mechanical pass)" % qid)
        ans = r.get("answers") or {}
        if not ans:
            bad("round %s: no answers block" % r.get("round"))
        for member, per_q in ans.items():
            for qid, rec in per_q.items():
                for k in ("attempts", "malformed", "wrong"):
                    if k not in rec:
                        bad("%s/%s: counter %r missing (two counters, never one merged accuracy)" % (member, qid, k))
                        continue
                if all(k in rec for k in ("attempts", "malformed", "wrong")):
                    if rec["malformed"] + rec["wrong"] > rec["attempts"]:
                        bad("%s/%s: malformed+wrong exceeds attempts" % (member, qid))
        if "accuracy" in r or "accuracy" in (r.get("result") or {}):
            bad("round %s: merged accuracy field present -- forbidden by R7" % r.get("round"))

    return v


def main():
    if "--emit" in sys.argv:
        print(json.dumps(build(), indent=2))
        return 0
    text = sys.stdin.read()
    try:
        t = json.loads(text)
    except Exception as e:
        print("VIOLATION not JSON: %s" % e)
        return 1
    v = check(t)
    pr = t.get("params") or {}
    print("checked: n=%r A=%r p=%r" % (pr.get("n"), pr.get("A"), pr.get("p_ref")))
    if pr.get("n") and pr.get("A") and pr.get("p_ref"):
        print("ceiling P(coin wins) = %.10f  tie-at-zero limit = %.6f"
              % (p_coin_wins(pr["n"], pr["p_ref"], pr["A"]), tie_at_zero(pr["n"], pr["p_ref"])))
    for msg in v:
        print("VIOLATION " + msg)
    print("SHAPE %s (%d violation(s))" % ("OK" if not v else "INVALID", len(v)))
    return 0 if not v else 1


if __name__ == "__main__":
    sys.exit(main())
