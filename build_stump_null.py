#!/usr/bin/env python3
"""Build frozen row set + action-ablated null records for illposed-v1 (CPU only)."""
import hashlib, json, os, sys, random

HERE = os.path.dirname(os.path.abspath(__file__))
RECORDS = os.path.join(HERE, "records")
sys.path.insert(0, HERE)
import stump  # noqa

N = 30
GRAMMAR_DIGEST = stump.GRAMMAR_DIGEST
A = stump.A_DEFAULT

# ---- 1. Freeze the row set ----
qs = stump.gen_fixed_illposed(N)
# canonical frozen row: list of question dicts (sorted keys)
row_canonical = json.dumps(qs, sort_keys=True)
row_set_digest = hashlib.sha256(row_canonical.encode()).hexdigest()

frozen_row = {
    "game": "stump",
    "grammar": "illposed-v1",
    "grammar_digest": GRAMMAR_DIGEST,
    "n": N,
    "A": A,
    "spec_version": "2026-11-07",
    "note": "Frozen row set for illposed-v1 action-ablated null (ruling 705). 15 well-posed + 15 ill-posed. Digest computed before any null measurement.",
    "row_set_digest": row_set_digest,
    "digest_recipe": "sha256(json.dumps(rows, sort_keys=True))",
    "rows": qs,
}
frozen_path = os.path.join(RECORDS, "stump_frozen_row_illposed-v1.json")
os.makedirs(RECORDS, exist_ok=True)
with open(frozen_path, "w") as f:
    json.dump(frozen_row, f, indent=2)
print("frozen row written:", frozen_path)
print("row_set_digest:", row_set_digest)

# ---- 2. Score the action-ablated nulls (constant predictors) ----
CONSTANTS = [
    ("constant_insufficient", "INSUFFICIENT"),
    ("constant_zero", "0"),
    ("constant_parametric", "INSUFFICIENT: X - 3"),
]

def score_constant(const_val, qs):
    correct = 0
    refused = 0; parametric = 0; confabulated = 0; malformed = 0
    well_correct = 0; ill_correct = 0
    well_total = 0; ill_total = 0
    rows_out = []
    for q in qs:
        ans = const_val
        timeout_flag = False
        if q.get("illposed"):
            ill_total += 1
        else:
            well_total += 1
        if ans is None or str(ans).strip() in ("", "...", "…"):
            if not timeout_flag:
                malformed += 1
            verdict = "incorrect"
        elif q.get("illposed"):
            cls = stump.classify_illposed(ans)
            if cls in ("refused", "parametric"):
                verdict = "correct"; correct += 1
                if q.get("illposed"):
                    ill_correct += 1
                else:
                    well_correct += 1
                if cls == "refused":
                    refused += 1
                else:
                    parametric += 1
            elif cls == "confabulated":
                verdict = "incorrect"; confabulated += 1
            else:
                verdict = "incorrect"
        else:
            if str(ans).strip() == q["asker_answer"]:
                verdict = "correct"; correct += 1
                well_correct += 1
            else:
                verdict = "incorrect"
        # well_correct tracking for ill-posed branch already above? fix: track by q
        rows_out.append({"qid": q["qid"], "illposed": q.get("illposed", False),
                        "answer": ans, "verdict": verdict})
    # recompute well/ill correct cleanly
    well_correct = sum(1 for r, q in zip(rows_out, qs) if not q.get("illposed") and r["verdict"] == "correct")
    ill_correct = sum(1 for r, q in zip(rows_out, qs) if q.get("illposed") and r["verdict"] == "correct")
    return {
        "constant": const_val,
        "correct": correct,
        "well_posed": {"correct": well_correct, "total": well_total},
        "ill_posed": {"correct": ill_correct, "total": ill_total},
        "profile": {
            "correct": correct,
            "refused": refused,
            "parametric": parametric,
            "confabulated": confabulated,
            "malformed": malformed,
        },
    }

null_variants = []
for name, val in CONSTANTS:
    r = score_constant(val, qs)
    r["name"] = name
    null_variants.append(r)
    print(name, val, "->", r["correct"], "/30", r["profile"])

# headline ablated null = constant INSUFFICIENT
headline = next(v for v in null_variants if v["name"] == "constant_insufficient")
ablated_null_score = headline["correct"]
ceiling = max(v["correct"] for v in null_variants)
print("ceiling:", ceiling, "ablated_null:", ablated_null_score)

# ---- 3. Model scores from existing calibrated traces ----
model_scores = {}
model_profiles = {}
for model, trace_file, arm in [("ornith9b", "traces/stump_calibrated_ornith9b_lfm1.7b.json", "A"),
                               ("lfm1.7b", "traces/stump_calibrated_ornith9b_lfm1.7b.json", "B")]:
    path = os.path.join(HERE, trace_file)
    d = json.load(open(path))
    res = d["rounds"][0]["result"]
    prof = res["profile"]["model_a" if arm == "A" else "model_b"]
    score = res["correct"]["A" if arm == "A" else "B"]
    model_scores[model] = score
    model_profiles[model] = prof
    print(model, score, prof)

# ---- 4. Write per-model records ----
for model in ["ornith9b", "lfm1.7b"]:
    ms = model_scores[model]
    mp = model_profiles[model]
    record = {
        "game": "stump",
        "source": "calibrated fixed set (illposed-v1)",
        "grammar": "illposed-v1",
        "grammar_digest": GRAMMAR_DIGEST,
        "row_set_digest": row_set_digest,
        "frozen_row_file": "records/stump_frozen_row_illposed-v1.json",
        "frozen_rows": N,
        "A": A,
        "n": N,
        "model": model,
        "null": {
            "constant_input_ceiling": ceiling,
            "constant_input_variants": [
                {"name": v["name"], "answer": v["constant"], "correct": v["correct"],
                 "well_posed": v["well_posed"], "ill_posed": v["ill_posed"], "profile": v["profile"]}
                for v in null_variants
            ],
            "ablated_null": ablated_null_score,
            "ablated_null_variant": "constant_insufficient",
            "model_score": ms,
        },
        "constant_input_ceiling": ceiling,
        "ablated_null": ablated_null_score,
        "model_score": ms,
        "model_score_detail": {
            "correct": ms,
            "total": N,
            "profile": mp,
        },
        "profile": mp,
        "header": [ceiling, ablated_null_score, ms],
        "header_labels": ["constant-input ceiling", "ablated null", "model score"],
        "notes": "CPU only, no GPU. Nulls measured on the frozen row set (digest above). "
                 "constant INSUFFICIENT scores 15/30 (0/15 well-posed, 15/15 ill-posed refused), "
                 "matching lfm1.7b's 15/30 by opposite profile; tie visible via header.",
    }
    out_path = os.path.join(RECORDS, "stump_null_%s.json" % model)
    with open(out_path, "w") as f:
        json.dump(record, f, indent=2)
    print("record written:", out_path)

print("DONE")
