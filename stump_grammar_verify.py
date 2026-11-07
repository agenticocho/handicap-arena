#!/usr/bin/env python3
"""Verify FROZEN_STUMP_GRAMMAR.json against its own generator. No model, no GPU, stdlib only.

usage: python3 stump_grammar_verify.py [path-to-FROZEN_STUMP_GRAMMAR.json]

Checks, in order:
  1. which serialisation reproduces the stored grammar_digest (and which do not)
  2. the answer space by enumeration: question count, distinct answers, range
  3. the MARGINAL distribution of a+b-c (this is what a guesser faces)
  4. the acceptance bar at n=30 for both a uniform-over-answers null and the
     best fixed-answer null, plus the null accuracy at which 19/30 flips
"""
import collections
import hashlib
import json
import sys
from math import comb

PATH = sys.argv[1] if len(sys.argv) > 1 else "FROZEN_STUMP_GRAMMAR.json"


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def main():
    raw = open(PATH, "rb").read()
    doc = json.loads(raw)
    g = doc["grammar"]
    target = doc["grammar_digest"]

    print("== 1. DIGEST ==")
    print("file bytes: %d   raw sha256: %s" % (len(raw), hashlib.sha256(raw).hexdigest()))
    print("stored grammar_digest: %s" % target)
    variants = {
        "inner object, sort_keys, DEFAULT separators": sha(json.dumps(g, sort_keys=True)),
        "inner object, sort_keys, COMPACT separators": sha(json.dumps(g, sort_keys=True, separators=(",", ":"))),
        "inner object, sort_keys, ensure_ascii=False": sha(json.dumps(g, sort_keys=True, ensure_ascii=False)),
        "whole document, sort_keys, default": sha(json.dumps(doc, sort_keys=True)),
        "whole document, sort_keys, compact": sha(json.dumps(doc, sort_keys=True, separators=(",", ":"))),
        "raw file bytes": hashlib.sha256(raw).hexdigest(),
    }
    for k, v in variants.items():
        print("%s %s  %s" % ("MATCH " if v == target else "      ", v, k))

    print("\n== 2/3. ANSWER SPACE (enumerated from the generator) ==")
    vals = []
    for a in range(1, 21):
        for b in range(1, 21):
            for c in range(1, a + b + 1):
                vals.append(a + b - c)
    cnt = collections.Counter(vals)
    n_q, n_a = len(vals), len(cnt)
    print("questions %d   distinct answers %d   range %d..%d" % (n_q, n_a, min(cnt), max(cnt)))
    print("claimed    %d   %d   %s" % (doc["answer_space"]["question_space_size"],
                                      doc["answer_space"]["distinct_answers"],
                                      doc["answer_space"]["range"]))
    print("marginal, top 8 (answer, count, freq):")
    for v, c in cnt.most_common(8):
        print("   %2d  %5d  %.6f" % (v, c, c / n_q))
    mode_q = cnt.most_common(1)[0][1] / n_q
    print("uniform-over-answers q = 1/%d = %.6f" % (n_a, 1 / n_a))
    print("best fixed-answer    q = %d/%d = %.6f  (A_eff = %.3f)" % (cnt.most_common(1)[0][1], n_q, mode_q, 1 / mode_q))

    print("\n== 4. ACCEPTANCE BAR (tie split 50/50, tolerance 0.01) ==")

    def bp(n, p, k):
        return comb(n, k) * p ** k * (1 - p) ** (n - k)

    def win(n, p, q):
        s = 0.0
        for i in range(n + 1):
            s += bp(n, p, i) * (sum(bp(n, q, j) for j in range(0, i)) + 0.5 * bp(n, q, i))
        return s

    def bar(n, q, tol=0.01):
        lo, hi = 0.0, 1.0
        for _ in range(50):
            mid = (lo + hi) / 2
            if win(n, mid, q) >= 1 - tol:
                hi = mid
            else:
                lo = mid
        return hi

    for label, q in (("uniform over answers", 1 / n_a), ("best fixed answer", mode_q)):
        print("  n=30  %-22s q=%.6f  bar=%.6f" % (label, q, bar(30, q)))
    ent = 19 / 30
    lo, hi = 1e-9, 0.999
    for _ in range(60):
        mid = (lo + hi) / 2
        if bar(30, mid) < ent:
            lo = mid
        else:
            hi = mid
    print("  19/30 = %.6f stays admitted while null accuracy q < %.6f (A_eff > %.4f)" % (ent, hi, 1 / hi))


if __name__ == "__main__":
    main()
