#!/usr/bin/env python3
"""Does the CARD bundle carry the clock? Chilly's observation applied to my own artifact.

Chilly's line: "the same fields that make it diagnosable are the ones Ocho just added for the clock."
That is a claim about the CHESS spec, and I just wrote it. The question worth asking is whether the
claim holds for the artifact already on disk -- because if a 38-minute silence was ambiguous for v4 too,
then the fields that resolved it (n_gen, tg, elapsed) live in the SERVER LOG and not in the bundle, which
is the discarded-diagnostic defect one more time.

So: measure what a v4 item record actually carries, and test the two questions a reader would ask --
"did this item think or did it run out?" and "how long did it take?"
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

# What a reader needs to answer the two questions, and where each could live.
WANT_BUNDLE = ["generated", "harness", "results", "version"]
WANT_ENTRY = ["card_version", "config", "sha256", "score", "aggregate"]
WANT_ROUND = ["score", "wins", "trials", "items", "truncated", "ctx_limited_trials",
              "finish_reasons", "max_completion_tokens", "serving_failures"]
WANT_ITEM = ["score", "reason", "raw", "truncated", "secs", "gen_tokens"]


def main():
    files = [p for p in sorted(glob.glob(os.path.join(RESULTS, "*cardv4*.json")))
             if json.load(open(p, encoding="utf-8")).get("harness") == "handicap-arena"
             and (json.load(open(p, encoding="utf-8")).get("results") or [])]
    if not files:
        print("no v4 bundle with a measurement yet")
        return 0

    b = json.load(open(files[0], encoding="utf-8"))
    e = b["results"][0]
    rd = (e.get("rounds") or {}).get("R1_fencing") or {}
    it = next(iter((rd.get("items") or {}).values()), {})

    print(f"inspecting: {os.path.basename(files[0])}")
    print()
    for label, have, want in (("BUNDLE", b, WANT_BUNDLE),
                              ("ENTRY", e, WANT_ENTRY),
                              ("ROUND", rd, WANT_ROUND),
                              ("ITEM", it, WANT_ITEM)):
        print(f"  {label:7} carries:")
        for k in want:
            mark = "PRESENT" if k in have else "--- ABSENT"
            val = ""
            if k in have:
                v = have[k]
                s = repr(v)
                val = "  = " + (s[:58] + "..." if len(s) > 58 else s)
            print(f"      {mark}  {k}{val}")
        print()

    print("  THE TWO QUESTIONS A READER ASKS:")
    q1 = "truncated" in rd or "max_completion_tokens" in rd
    q2 = "secs" in it
    print(f"    did this item think, or did it run out?   ROUND-level {'yes' if q1 else 'NO'}"
          f"   ITEM-level {'yes' if q2 else 'NO'}")
    print(f"    how long did the decision take?           ROUND-level {'yes' if 'secs' in rd else 'NO'}"
          f"   ITEM-level {'yes' if 'secs' in it else 'NO'}")
    print()
    if not q2:
        print("  THE GAP, and it is the same one as the chess clock: at the ITEM level the bundle records")
        print("  what the model SAID (raw), what it SCORED (score) and whether it was CUT OFF (truncated)")
        print("  -- and not HOW LONG IT TOOK, and not HOW MANY TOKENS. Both were measured; the runner")
        print("  writes elapsed seconds to its LOG. A log is discarded relative to the artifact.")
        print()
        print("  Consequence, in the same shape as the 38-minute silence: 'this item took 8 minutes")
        print("  because the model was reasoning' and 'this item took 8 minutes because it ran to the cap'")
        print("  are different claims, and at the item level the bundle cannot currently tell them apart.")
        print("  ROUND-level `truncated` + `max_completion_tokens` answer it for the round as a whole,")
        print("  which is why the field was diagnosable at all -- but per item, a slow item and a")
        print("  truncated item land in the record looking the same.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
