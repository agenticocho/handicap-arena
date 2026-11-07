#!/usr/bin/env python3
"""Stump harness -- two-model wits challenge (task shape: STUMP-1).

Grammar is frozen by digest (arith-singledigit-add-v1). Model A generates n questions
it can answer (a+b, a,b in 1..9); the oracle validates each asker_answer. Model B
answers them (two counters: malformed, wrong). Then roles swap. Best 2 of 3 wins.

Usage:
  python3 stump.py --self-test
  python3 stump.py --round --model-a ornith9b --model-b ornith9b
  python3 stump.py --gen-test --model ornith9b
"""
import argparse, hashlib, json, math, os, random, re, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TRACE_DIR = os.path.join(HERE, "traces")

MODEL_URLS = {
    "ornith9b": "http://127.0.0.1:8360/v1/chat/completions",
    "jang": "http://127.0.0.1:19081/v1/chat/completions",  # unreachable by design; see jarvis note
    "lfm1.7b": "http://127.0.0.1:8362/v1/chat/completions",
    "qwen0.6b": "http://127.0.0.1:8361/v1/chat/completions",
}

# ---------- frozen grammar (from STUMP task template) ----------
GRAMMAR = {
    "id": "word_prob-v1",
    "rule": "Q(a, b, c) = 'Alice has a apples. She buys b more, then gives away c. How many does she have?' with a, b in 1..20, c in 1..(a+b); answer = a + b - c (non-negative)",
    "answer_form": r"^(?:0|[1-9]|[1-3][0-9])$",
    "answer_form_note": "canonical: bare decimal digits, no sign, no spaces, no prose, no units; range 0..39",
    "A_basis": "distinct values of a + b - c for a,b in 1..20, c in 1..(a+b) = 40 distinct answers (0..39)",
    "computes_not_looks_up": True,
    "identity": "Alice has 2 apples. She buys 3 more, then gives away 1. How many does she have? = 4",
    "identity_value": 4,
    "identity_malformed": "four",
}
TOLERANCE = 0.01
P_REF_DEFAULT = 0.90
N_DEFAULT = 5
A_DEFAULT = 40


def canonical_grammar_digest(g):
    return hashlib.sha256(json.dumps(g, sort_keys=True).encode()).hexdigest()


GRAMMAR_DIGEST = canonical_grammar_digest(GRAMMAR)


def A_of(g):
    """The answer space, computed from the grammar's declared ranges."""
    ans = set()
    for a in range(1, 21):
        for b in range(1, 21):
            for c in range(1, a + b + 1):
                v = a + b - c
                if 0 <= v <= 99:
                    ans.add(v)
    return len(ans)


A_VALUE = A_of(GRAMMAR)


def p_coin_wins(n, p, A):
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


# ---------- model call ----------
def model_call(model, messages, max_tokens=800, timeout=180, thinking=True, temperature=0.0):
    url = MODEL_URLS[model]
    content = reasoning = ""
    gen_tokens = 0
    dt = 0.0
    finish = ""
    for attempt in range(2):
        mt = max_tokens * (2 if attempt else 1)
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": mt,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "chat_template_kwargs": {"enable_thinking": thinking},
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            d = json.loads(resp.read())
        dt = time.time() - t0
        m = d["choices"][0]["message"]
        content = m.get("content") or ""
        reasoning = m.get("reasoning_content") or ""
        usage = d.get("usage", {})
        gen_tokens = usage.get("completion_tokens", 0)
        finish = d["choices"][0].get("finish_reason", "")
        if content or reasoning:
            return content, reasoning, gen_tokens, dt, finish
    return content, reasoning, gen_tokens, dt, finish


# ---------- canonical form check ----------
ANSWER_RE = re.compile(GRAMMAR["answer_form"])


def canonical_ok(s):
    return bool(s is not None and ANSWER_RE.match(str(s).strip()))


# ---------- generation ----------
OPS = ("+", "-", "*", "//")
OP_SYMBOLS = {"+": "+", "-": "-", "*": "*", "//": "/"}


def compute(a, op, b):
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "//":
        if b == 0:
            return None
        return a // b
    return None


def _parse_pairs(content, reasoning):
    for src in (content, reasoning):
        if not src:
            continue
        try:
            obj = json.loads(src)
        except Exception:
            m = re.search(r"\{.*\}", src, re.DOTALL)
            if m:
                try:
                    obj = json.loads(m.group(0))
                except Exception:
                    obj = None
            else:
                obj = None
        if isinstance(obj, dict):
            qs = obj.get("questions")
            if isinstance(qs, list):
                out = []
                for q in qs:
                    if not isinstance(q, dict):
                        continue
                    a = q.get("a")
                    b = q.get("b")
                    c = q.get("c")
                    ans = q.get("answer")
                    if not (isinstance(a, int) and isinstance(b, int) and isinstance(c, int)):
                        continue
                    if not (1 <= a <= 20 and 1 <= b <= 20):
                        continue
                    if not (1 <= c <= a + b):
                        continue
                    v = a + b - c
                    if v < 0 or v > 99:
                        continue
                    if ans is not None and str(ans).strip() != str(v):
                        continue
                    text = "Alice has %d apples. She buys %d more, then gives away %d. How many does she have?" % (a, b, c)
                    if re.search(r"\b%d\b" % v, text):
                        continue
                    out.append((a, b, c, v))
                return out
    return []


def generate_side(model, side, n, max_attempts=5):
    """Return (list of (a,b,c) triples, metrics, fallback_flags) length n."""
    collected = []
    fallback_flags = []
    seen = set()
    metrics = {"secs": 0.0, "gen_tokens": 0, "budget_hits": 0, "attempts": 0, "timeouts": 0}
    pool = []
    for a in range(1, 21):
        for b in range(1, 21):
            for c in range(1, a + b + 1):
                v = a + b - c
                if v < 0 or v > 99:
                    continue
                text = "Alice has %d apples. She buys %d more, then gives away %d. How many does she have?" % (a, b, c)
                if re.search(r"\b%d\b" % v, text):
                    continue
                pool.append((a, b, c))
    random.shuffle(pool)
    pool_idx = 0

    while len(collected) < n and metrics["attempts"] < max_attempts * n:
        metrics["attempts"] += 1
        need = 1
        prompt = (
            "Generate 1 word problem. Alice has a apples, buys b more, gives away c (c <= a+b). "
            "a, b in 1..20. You must answer correctly (answer = a + b - c). Output JSON only:\n"
            '{"questions": [{"a": <int>, "b": <int>, "c": <int>, "answer": <int>}]}'
        )
        try:
            content, reasoning, gt, dt, finish = model_call(model, [{"role": "user", "content": prompt}], max_tokens=1200, timeout=120, thinking=(model == "ornith9b"), temperature=0.7)
        except Exception as e:
            msg = str(e).lower()
            if "timed out" in msg or "timeout" in msg:
                metrics["timeouts"] += 1
                continue
            print("gen error: %s" % e, file=sys.stderr)
            break
        metrics["secs"] += dt
        metrics["gen_tokens"] += gt
        if finish == "length":
            metrics["budget_hits"] += 1
        triples = _parse_pairs(content, reasoning)
        for a, b, c, v in triples:
            if len(collected) >= n:
                break
            if (a, b, c) in seen:
                continue
            text = "Alice has %d apples. She buys %d more, then gives away %d. How many does she have?" % (a, b, c)
            if re.search(r"\b%d\b" % v, text):
                continue
            seen.add((a, b, c))
            collected.append((a, b, c))
            fallback_flags.append(False)

    while len(collected) < n:
        while pool_idx < len(pool) and (pool[pool_idx] in seen):
            pool_idx += 1
        if pool_idx >= len(pool):
            break
        a, b, c = pool[pool_idx]
        pool_idx += 1
        if (a, b, c) in seen:
            continue
        text = "Alice has %d apples. She buys %d more, then gives away %d. How many does she have?" % (a, b, c)
        v = a + b - c
        if re.search(r"\b%d\b" % v, text):
            continue
        seen.add((a, b, c))
        collected.append((a, b, c))
        fallback_flags.append(True)

    return collected, metrics, fallback_flags


def build_qset(side, triples, A, A_source, fallback_flags=None):
    if fallback_flags is None:
        fallback_flags = [False] * len(triples)
    out = []
    for i, (a, b, c) in enumerate(triples, 1):
        v = a + b - c
        ans = str(v)
        text = "Alice has %d apples. She buys %d more, then gives away %d. How many does she have?" % (a, b, c)
        out.append({
            "qid": "%s-%d" % (side, i),
            "side": side,
            "text": text,
            "template": "word_prob(a,b,c): a,b in 1..20, c in 1..(a+b), answer = a+b-c",
            "A": A,
            "A_source": A_source,
            "asker_answer": ans,
            "asker_answer_sha256": hashlib.sha256(ans.encode()).hexdigest(),
            "admissible": True,
            "inadmissible_reason": None,
            "fallback": bool(fallback_flags[i-1]) if i-1 < len(fallback_flags) else False,
        })
    return out


# ---------- answer phase ----------
ANSWER_PROMPT = 'Answer this Stump question. Output JSON only: {"answer": "..."}. Question: %s'


def answer_one(model, q):
    prompt = ANSWER_PROMPT % q["text"]
    messages = [{"role": "user", "content": prompt}]
    t0 = time.time()
    timed_out = False
    try:
        content, reasoning, gt, dt, finish = model_call(model, messages, max_tokens=400, timeout=120, thinking=(model == "ornith9b"))
    except Exception as e:
        msg = str(e).lower()
        if "timed out" in msg or "timeout" in msg:
            timed_out = True
        return None, time.time() - t0, 0, False, str(e), timed_out
    ans = None
    for src in (content, reasoning):
        if not src:
            continue
        try:
            obj = json.loads(src)
            if isinstance(obj, dict) and "answer" in obj:
                ans = str(obj["answer"]).strip()
                break
        except Exception:
            pass
    if ans is None:
        m = re.search(r'"answer"\s*:\s*"([^"]*)"', content + " " + reasoning)
        if m:
            ans = m.group(1).strip()
    bh = (finish == "length")
    return ans, dt, gt, bh, None, timed_out


# ---------- round ----------
def run_round(model_a, model_b, n, A, p_ref, tolerance, out_path=None):
    t0 = time.time()
    A_source = "recomputed by the oracle from the grammar: A_basis"

    print("A (%s) generating %d questions..." % (model_a, n), file=sys.stderr)
    a_pairs, gen_a, a_fb = generate_side(model_a, "A", n)
    a_qs = build_qset("A", a_pairs, A, A_source, a_fb)
    print("B (%s) generating %d questions..." % (model_b, n), file=sys.stderr)
    b_pairs, gen_b, b_fb = generate_side(model_b, "B", n)
    b_qs = build_qset("B", b_pairs, A, A_source, b_fb)

    rows = []
    b_answers_counters = {}
    b_correct_on_a = 0
    for q in a_qs:
        ans, dt, gt, bh, err, to = answer_one(model_b, q)
        malformed = 0
        wrong = 0
        timeout_flag = to
        if ans is None or not canonical_ok(ans):
            if not timeout_flag:
                malformed = 1
            verdict = "incorrect"
        else:
            if str(ans).strip() == q["asker_answer"]:
                verdict = "correct"
                b_correct_on_a += 1
            else:
                verdict = "incorrect"
                wrong = 1
        b_answers_counters[q["qid"]] = {"attempts": 1, "malformed": malformed, "wrong": wrong, "timeout": timeout_flag}
        rows.append({
            "arm": "A",
            "question": q["text"],
            "type": "math",
            "model_a_answer": q["asker_answer"],
            "model_b_answer": ans,
            "truth": q["asker_answer"],
            "oracle_verdict": verdict,
            "secs": round(dt, 3),
            "gen_tokens": gt,
            "budget_hit": bh,
            "error": err,
            "fallback": bool(q.get("fallback", False)),
            "timeout": bool(timeout_flag),
            "grammar_digest": GRAMMAR_DIGEST,
            "A": A,
            "n": n,
            "qid": q["qid"],
        })

    a_answers_counters = {}
    a_correct_on_b = 0
    for q in b_qs:
        ans, dt, gt, bh, err, to = answer_one(model_a, q)
        malformed = 0
        wrong = 0
        timeout_flag = to
        if ans is None or not canonical_ok(ans):
            if not timeout_flag:
                malformed = 1
            verdict = "incorrect"
        else:
            if str(ans).strip() == q["asker_answer"]:
                verdict = "correct"
                a_correct_on_b += 1
            else:
                verdict = "incorrect"
                wrong = 1
        a_answers_counters[q["qid"]] = {"attempts": 1, "malformed": malformed, "wrong": wrong, "timeout": timeout_flag}
        rows.append({
            "arm": "B",
            "question": q["text"],
            "type": "math",
            "model_a_answer": ans,
            "model_b_answer": q["asker_answer"],
            "truth": q["asker_answer"],
            "oracle_verdict": verdict,
            "secs": round(dt, 3),
            "gen_tokens": gt,
            "budget_hit": bh,
            "error": err,
            "fallback": bool(q.get("fallback", False)),
            "timeout": bool(timeout_flag),
            "grammar_digest": GRAMMAR_DIGEST,
            "A": A,
            "n": n,
            "qid": q["qid"],
        })

    if a_correct_on_b > b_correct_on_a:
        winner = "A"
    elif b_correct_on_a > a_correct_on_b:
        winner = "B"
    else:
        winner = "tie"

    run_type = "smoke" if model_a == model_b else "match"

    # sudden-death tiebreak (determinate result; no ties survive)
    tiebreak = None
    if winner == "tie":
        tb_winner = None
        tb_rounds = 0
        for _ in range(3):
            tb_rounds += 1
            a_pairs, _, a_fb = generate_side(model_a, "A", 1)
            b_pairs, _, b_fb = generate_side(model_b, "B", 1)
            aq = build_qset("A", a_pairs, A, A_source)[0]
            bq = build_qset("B", b_pairs, A, A_source)[0]
            # B answers A's tiebreak q
            ans_b, dt_b, gt_b, bh_b, _, _ = answer_one(model_b, aq)
            b_ok = (ans_b is not None and str(ans_b).strip() == aq["asker_answer"])
            ans_a, dt_a, gt_a, bh_a, _, _ = answer_one(model_a, bq)
            a_ok = (ans_a is not None and str(ans_a).strip() == bq["asker_answer"])
            if a_ok and not b_ok:
                tb_winner = "A"; break
            if b_ok and not a_ok:
                tb_winner = "B"; break
            if a_ok and b_ok:
                # both correct: compare malformed? just continue
                continue
            if (not a_ok) and (not b_ok):
                continue
        if tb_winner is None:
            # fallback: lower total malformed among main counters
            tot_mal_a = sum(a_answers_counters[q]["malformed"] for q in a_answers_counters)
            tot_mal_b = sum(b_answers_counters[q]["malformed"] for q in b_answers_counters)
            if tot_mal_a < tot_mal_b:
                tb_winner = "A"
            elif tot_mal_b < tot_mal_a:
                tb_winner = "B"
            else:
                tb_winner = None  # genuine tie -> DRAW
        if tb_winner is None:
            winner = "DRAW"
        else:
            winner = tb_winner
        tiebreak = {"rounds": tb_rounds, "winner": winner}

    answers_block = {}
    answers_block[model_b] = {qid: b_answers_counters[qid] for qid in b_answers_counters}
    answers_block[model_a] = {qid: a_answers_counters[qid] for qid in a_answers_counters}
    for member in (model_a, model_b):
        for q in a_qs + b_qs:
            if q["qid"] not in answers_block[member]:
                answers_block[member][q["qid"]] = {"attempts": 0, "malformed": 0, "wrong": 0}

    questions_committed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0))
    qsd = hashlib.sha256(json.dumps({"A": a_qs, "B": b_qs}, sort_keys=True).encode()).hexdigest()
    answers_committed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    answers_digest = hashlib.sha256(json.dumps(answers_block, sort_keys=True).encode()).hexdigest()

    ceiling = {
        "P_coin_wins": p_coin_wins(n, p_ref, A),
        "tie_at_zero_limit": tie_at_zero(n, p_ref),
        "recomputed_from": {"n": n, "A": A, "p": p_ref},
        "formula": "P(X>Y) + 0.5 P(X=Y), X~Bin(n,1/A), Y~Bin(n,p)",
    }

    task = {
        "task": "STUMP-1",
        "run_type": run_type,
        "label": "STUMP — word-problem grammar, measures multi-step arithmetic",
        "spec_version": "2026-11-05.5",
        "note": "WORKED EXAMPLE shape; model-generated arithmetic questions.",
        "grammar": dict(GRAMMAR, digest=GRAMMAR_DIGEST),
        "params": {
            "n": n,
            "A": A,
            "tolerance": tolerance,
            "p_ref": p_ref,
            "question_space_size": 8400,
            "distinct_answers": 40,
            "ceiling": ceiling,
            "A_is_free_n_is_paid": "A is checked at admission, zero inference; n costs 2n answers per round",
            "tie_rule": "P(tie) = 1/2 (ties split 50/50); guesser score Bin(n, 1/A) per side, independent",
        },
        "panel": [{"id": "panel-1", "ref": "PLACEHOLDER", "note": "digest-pinned before the run; never edited mid-run"}],
        "rounds": [
            {
                "round": 1,
                "freeze": {
                    "grammar_digest": GRAMMAR_DIGEST,
                    "questions_committed_at": questions_committed_at,
                    "question_sets_digest": qsd,
                    "answers_committed_at": answers_committed_at,
                    "answers_digest": answers_digest,
                    "rule": "both question sets are hashed and exchanged before either side's answers are revealed",
                },
                "questions": {"A": a_qs, "B": b_qs},
                "answers": answers_block,
                "counters_rule": "malformed is over attempts; wrong is over well-formed attempts; the two never merge",
                "result": {
                    "correct": {"A": b_correct_on_a, "B": a_correct_on_b},
                    "winner": winner,
                    "items_graded_per_side": n,
                    "items_graded_total": 2 * n,
                    "null": {"P_coin_wins": p_coin_wins(n, p_ref, A), "cell": {"n": n, "A": A, "p": p_ref}},
                    "note": "a row with no null is not a result",
                    "tiebreak": tiebreak,
                },
            }
        ],
        "model_a": model_a,
        "model_b": model_b,
        "grammar_digest": GRAMMAR_DIGEST,
        "rows": rows,
        "gen_a": gen_a,
        "gen_b": gen_b,
        "secs_total": round(time.time() - t0, 3),
    }

    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(task, f, indent=2)
        print("trace written: %s" % out_path, file=sys.stderr)
    return task


def run_replay(frozen_path, model_a, model_b, out_path=None):
    with open(frozen_path) as f:
        data = json.load(f)
    r = data["rounds"][0]
    a_qs = r["questions"]["A"]
    b_qs = r["questions"]["B"]
    n = data["params"]["n"]
    A = data["params"]["A"]
    p_ref = data["params"]["p_ref"]
    tolerance = data["params"]["tolerance"]

    rows = []
    b_correct_on_a = 0
    for q in a_qs:
        ans, dt, gt, bh, err = answer_one(model_b, q)
        verdict = "correct" if (ans is not None and str(ans).strip() == q["asker_answer"]) else "incorrect"
        if verdict == "correct":
            b_correct_on_a += 1
        rows.append({"arm": "A", "question": q["text"], "model_a_answer": q["asker_answer"],
                     "model_b_answer": ans, "oracle_verdict": verdict, "secs": round(dt, 3),
                     "gen_tokens": gt, "budget_hit": bh, "error": err, "grammar_digest": GRAMMAR_DIGEST,
                     "A": A, "n": n, "qid": q["qid"], "replay": True})

    a_correct_on_b = 0
    for q in b_qs:
        ans, dt, gt, bh, err = answer_one(model_a, q)
        verdict = "correct" if (ans is not None and str(ans).strip() == q["asker_answer"]) else "incorrect"
        if verdict == "correct":
            a_correct_on_b += 1
        rows.append({"arm": "B", "question": q["text"], "model_a_answer": ans,
                     "model_b_answer": q["asker_answer"], "oracle_verdict": verdict, "secs": round(dt, 3),
                     "gen_tokens": gt, "budget_hit": bh, "error": err, "grammar_digest": GRAMMAR_DIGEST,
                     "A": A, "n": n, "qid": q["qid"], "replay": True})

    winner = "A" if a_correct_on_b > b_correct_on_a else ("B" if b_correct_on_a > a_correct_on_b else "DRAW")
    out = {
        "game": "stump", "replay": True, "frozen": frozen_path,
        "model_a": model_a, "model_b": model_b,
        "A": A, "n": n, "grammar_digest": GRAMMAR_DIGEST,
        "label": "STUMP — word-problem grammar, measures multi-step arithmetic",
        "a_correct": a_correct_on_b, "b_correct": b_correct_on_a,
        "winner": winner, "rows": rows,
    }
    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(out, f, indent=2)
        print("replay trace written: %s" % out_path, file=sys.stderr)
    return out

def gen_fixed_wordprob(n=30):
    items = []
    random.seed(11)
    while len(items) < n:
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        c = random.randint(1, a + b - 1)
        val = a + b - c
        if val < 0 or val > 999:
            continue
        items.append((a, b, c))
    return items[:n]


def run_calibrated(model_a, model_b, n, out_path=None):
    t0 = time.time()
    A = A_DEFAULT
    p_ref = P_REF_DEFAULT
    tolerance = TOLERANCE
    A_source = "recomputed by the oracle from the grammar: A_basis"
    triples = gen_fixed_wordprob(n)
    qs = build_qset("A", triples, A, A_source)
    # both sides answer the same fixed set
    b_qs = [dict(q, qid=q["qid"].replace("A-", "B-"), side="B") for q in qs]

    rows = []
    b_correct_on_a = 0
    for q in qs:
        ans, dt, gt, bh, err, to = answer_one(model_b, q)
        malformed = 0; wrong = 0; timeout_flag = to
        if ans is None or not canonical_ok(ans):
            if not timeout_flag:
                malformed = 1
            verdict = "incorrect"
        else:
            if str(ans).strip() == q["asker_answer"]:
                verdict = "correct"; b_correct_on_a += 1
            else:
                verdict = "incorrect"; wrong = 1
        rows.append({"arm": "A", "question": q["text"], "type": "word_prob",
            "model_a_answer": q["asker_answer"], "model_b_answer": ans,
            "truth": q["asker_answer"],
            "oracle_verdict": verdict, "secs": round(dt, 3), "gen_tokens": gt,
            "budget_hit": bh, "error": err, "fallback": False, "timeout": bool(timeout_flag),
            "grammar_digest": GRAMMAR_DIGEST, "A": A, "n": n, "qid": q["qid"]})

    a_correct_on_b = 0
    for q in b_qs:
        # find matching original for asker_answer
        orig = qs[[x["qid"].replace("A-","") for x in qs].index(q["qid"].replace("B-",""))]
        ans, dt, gt, bh, err, to = answer_one(model_a, q if False else orig)
        # use original question text
        q2 = orig
        ans, dt, gt, bh, err, to = answer_one(model_a, q2)
        malformed = 0; wrong = 0; timeout_flag = to
        if ans is None or not canonical_ok(ans):
            if not timeout_flag:
                malformed = 1
            verdict = "incorrect"
        else:
            if str(ans).strip() == q2["asker_answer"]:
                verdict = "correct"; a_correct_on_b += 1
            else:
                verdict = "incorrect"; wrong = 1
        rows.append({"arm": "B", "question": q2["text"], "type": "word_prob",
            "model_a_answer": ans, "model_b_answer": q2["asker_answer"],
            "truth": q2["asker_answer"],
            "oracle_verdict": verdict, "secs": round(dt, 3), "gen_tokens": gt,
            "budget_hit": bh, "error": err, "fallback": False, "timeout": bool(timeout_flag),
            "grammar_digest": GRAMMAR_DIGEST, "A": A, "n": n, "qid": q2["qid"]})

    winner = "A" if a_correct_on_b > b_correct_on_a else ("B" if b_correct_on_a > a_correct_on_b else "DRAW")
    task = {
        "task": "STUMP-1", "run_type": "calibrated",
        "label": "STUMP — word-problem grammar, measures multi-step arithmetic",
        "spec_version": "2026-11-05.5",
        "note": "Fixed screening set (30 items) answered by both models. No generation.",
        "grammar": dict(GRAMMAR, digest=GRAMMAR_DIGEST),
        "params": {"n": n, "A": A, "tolerance": tolerance, "p_ref": P_REF_DEFAULT,
                   "question_space_size": 8400, "distinct_answers": 40,
                   "ceiling": {"P_coin_wins": p_coin_wins(n, P_REF_DEFAULT, A),
                               "tie_at_zero_limit": tie_at_zero(n, P_REF_DEFAULT),
                               "recomputed_from": {"n": n, "A": A, "p": P_REF_DEFAULT},
                               "formula": "P(X>Y) + 0.5 P(X=Y), X~Bin(n,1/A), Y~Bin(n,p)"},
                   "A_is_free_n_is_paid": "A is checked at admission, zero inference; n costs 2n answers per round",
                   "tie_rule": "P(tie) = 1/2 (ties split 50/50); guesser score Bin(n, 1/A) per side, independent"},
        "panel": [{"id": "panel-1", "ref": "PLACEHOLDER", "note": "digest-pinned before the run"}],
        "rounds": [{"round": 1, "freeze": {"grammar_digest": GRAMMAR_DIGEST,
            "questions_committed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)),
            "question_sets_digest": hashlib.sha256(json.dumps(qs, sort_keys=True).encode()).hexdigest(),
            "answers_committed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "answers_digest": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
            "rule": "both models answer the same fixed calibrated set"},
            "questions": {"A": qs, "B": [dict(q, qid=q["qid"].replace("A-","B-"), side="B") for q in qs]},
            "answers": {},
            "counters_rule": "malformed is over attempts; wrong is over well-formed attempts; the two never merge",
            "result": {"correct": {"A": b_correct_on_a, "B": a_correct_on_b}, "winner": winner,
                       "items_graded_per_side": n, "items_graded_total": 2 * n,
                       "null": {"P_coin_wins": p_coin_wins(n, P_REF_DEFAULT, A),
                                "cell": {"n": n, "A": A, "p": P_REF_DEFAULT}},
                       "note": "calibrated fixed set; no generation", "tiebreak": None}}],
        "model_a": model_a, "model_b": model_b, "grammar_digest": GRAMMAR_DIGEST,
        "rows": rows, "secs_total": round(time.time() - t0, 3),
    }
    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(task, f, indent=2)
        print("trace written: %s" % out_path, file=sys.stderr)
    return task


def _self_test_identity():
    assert canonical_ok(str(GRAMMAR["identity_value"]))
    assert not canonical_ok(GRAMMAR["identity_malformed"])
    assert A_VALUE == 40
    print("identity ok: %s -> %s ; malformed %r rejected" % (GRAMMAR["identity"], GRAMMAR["identity_value"], GRAMMAR["identity_malformed"]))
    print("A =", A_VALUE, "digest =", GRAMMAR_DIGEST)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--gen-test", action="store_true")
    ap.add_argument("--round", action="store_true")
    ap.add_argument("--model", default="ornith9b")
    ap.add_argument("--model-a", default="ornith9b")
    ap.add_argument("--model-b", default="ornith9b")
    ap.add_argument("--n", type=int, default=N_DEFAULT)
    ap.add_argument("--A", type=int, default=A_DEFAULT, dest="A")
    ap.add_argument("--p-ref", type=float, default=P_REF_DEFAULT)
    ap.add_argument("--tolerance", type=float, default=TOLERANCE)
    ap.add_argument("--out")
    ap.add_argument("--calibrated", action="store_true")
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--frozen")
    args = ap.parse_args()

    if args.self_test:
        _self_test_identity()
        import subprocess
        probe = os.path.join(HERE, "probes", "stump_task_gen.py")
        if os.path.exists(probe):
            out = os.path.join(TRACE_DIR, "stump_selftest.json")
            os.makedirs(TRACE_DIR, exist_ok=True)
            task = run_round("ornith9b", "ornith9b", args.n, args.A, args.p_ref, args.tolerance, out_path=out)
            r = subprocess.run(["python3", probe, "--check"], input=json.dumps(task), capture_output=True, text=True)
            print(r.stdout.strip())
            print("SHAPE %s" % ("OK" if r.returncode == 0 else "INVALID"))
            if r.returncode != 0:
                print(r.stderr)
            return 0 if r.returncode == 0 else 1
        return 0

    if args.gen_test:
        pairs, m, _ = generate_side(args.model, "A", args.n)
        print(json.dumps({"pairs": pairs, "metrics": m}, indent=2))
        return 0

    if args.round:
        out = args.out or os.path.join(TRACE_DIR, "stump_round_%s_%s.json" % (args.model_a, args.model_b))
        task = run_round(args.model_a, args.model_b, args.n, args.A, args.p_ref, args.tolerance, out_path=out)
        print("winner:", task["rounds"][0]["result"]["winner"])
        print("A: %d/%d  B: %d/%d  (%d items graded total)" % (task["rounds"][0]["result"]["correct"]["B"], args.n,
                                      task["rounds"][0]["result"]["correct"]["A"], args.n,
                                      task["rounds"][0]["result"]["items_graded_total"]))
        print("trace:", out)
        return 0

    if args.calibrated:
        out = args.out or os.path.join(TRACE_DIR, "stump_calibrated_%s_%s.json" % (args.model_a, args.model_b))
        task = run_calibrated(args.model_a, args.model_b, args.n, out_path=out)
        print("winner:", task["rounds"][0]["result"]["winner"])
        print("A: %d/%d  B: %d/%d  (%d items graded total)" % (task["rounds"][0]["result"]["correct"]["B"], args.n,
                                      task["rounds"][0]["result"]["correct"]["A"], args.n,
                                      task["rounds"][0]["result"]["items_graded_total"]))
        print("trace:", out)
        return 0

    if args.replay:
        if not args.frozen:
            ap.error("--frozen required for --replay")
        out = args.out or os.path.join(TRACE_DIR, "stump_replay_%s_%s.json" % (args.model_a, args.model_b))
        task = run_replay(args.frozen, args.model_a, args.model_b, out_path=out)
        print("winner:", task["winner"])
        print("A: %d/%d  B: %d/%d" % (task["a_correct"], task["n"], task["b_correct"], task["n"]))
        print("trace:", out)
        return 0


if __name__ == "__main__":
    sys.exit(main())