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
QUESTION_SET_PATH = os.path.join(TRACE_DIR, "stump_illposed_qset.json")

MODEL_URLS = {
    "ornith9b": "http://127.0.0.1:8360/v1/chat/completions",
    "jang": "http://127.0.0.1:19081/v1/chat/completions",  # unreachable by design; see jarvis note
    "lfm1.7b": "http://127.0.0.1:8362/v1/chat/completions",
    "qwen0.6b": "http://127.0.0.1:8361/v1/chat/completions",
    # registered 2026-11-09: smaller pairing band, per Mike's "save time during testing"
    "spark4b": "http://127.0.0.1:8377/v1/chat/completions",
    "spark4b-q4": "http://127.0.0.1:8381/v1/chat/completions",
    "smol3b": "http://127.0.0.1:8380/v1/chat/completions",
    "qwen2b": "http://127.0.0.1:8378/v1/chat/completions",
    "lfm3-1.7b": "http://127.0.0.1:8376/v1/chat/completions",
}

def free_gb():
    """AVAILABLE physical memory in GB: free + inactive + speculative + purgeable.

    NOT 'Pages free' — macOS keeps that near zero by design because it caches
    aggressively, so reading it reports 0.1 GB on a box with 3+ GB available and
    makes a healthy run look starved (or a starved one look fine).
    """
    try:
        out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5).stdout
        g = lambda k: int((re.search(k + r":\s+(\d+)", out) or [0, 0])[1])
        pages = g("Pages free") + g("Pages inactive") + g("Pages speculative") + g("Pages purgeable")
        return round(pages * 16384 / 1e9, 2) if pages else None
    except Exception:
        return None


# ---------- refusal classifier (illposed-v1) ----------
REFUSAL_PHRASES = ["cannot", "can't", "not enough", "insufficient", "unknown", "not determined",
                    "impossible", "not possible", "don't know", "do not know", "no way to",
                    "missing", "lack", "indeterminate", "can't be determined", "cannot be determined",
                    "undetermined", "enough information", "not specified", "not provided",
                    "unsolvable", "unresolvable", "no solution", "cannot be solved",
                    "can't be solved", "not solvable", "insufficient data"]


def is_refusal(text):
    if text is None:
        return False
    # Normalise typographic apostrophes/quotes first: models emit "can’t" (U+2019),
    # the phrase list holds "can't" (U+0027), and a straight-substring check misses
    # a correct refusal entirely. Verified against spark4b, which emits U+2019.
    low = text.lower().replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    return any(p in low for p in REFUSAL_PHRASES)


def has_variable(text):
    if text is None:
        return False
    return bool(re.search(r"[a-zA-Z]", text))


def has_expression(text):
    if text is None:
        return False
    return bool(re.search(r"[+\-*/=]", text))


def classify_illposed(ans):
    """Return one of: refused, parametric, confabulated, malformed, correct (well-posed handled separately)."""
    if ans is None or str(ans).strip() in ("", "...", "…"):
        return "malformed"
    s = str(ans).strip()
    if s.upper() == "INSUFFICIENT" or is_refusal(s):
        if has_variable(s) and has_expression(s):
            return "parametric"
        return "refused"
    # A bare algebraic answer ("x - 2") is solved AROUND the gap — parametric by
    # definition, and it must not need a refusal word to qualify. Gating this behind
    # is_refusal scored a correct parametric answer as `wrong`.
    if has_variable(s) and has_expression(s):
        return "parametric"
    if re.search(r"^-?\d", s):
        return "confabulated"
    return "wrong"
GRAMMAR = {
    "id": "illposed-v1",
    "rule": "Q is either well-posed (Alice has a apples, buys b, gives away c; answer = a+b-c) or ill-posed (missing information; answer = INSUFFICIENT or parametric). The model must answer INSUFFICIENT or a parametric expression when information is missing, never invent numbers.",
    "answer_form": r"^(?:INSUFFICIENT|[0-9]+|[A-Za-z0-9 _+\-*/()]+)$",
    "answer_form_note": "canonical: INSUFFICIENT for unanswerable, bare integer for well-posed, or parametric expression (e.g. X - 8) for underdetermined",
    "A_basis": "well-posed distinct answers 0..39 (40) plus INSUFFICIENT and parametric forms",
    "computes_not_looks_up": True,
    "identity": "Alice has some apples. She buys more, then gives away 3. How many does she have? = INSUFFICIENT",
    "identity_value": "INSUFFICIENT",
    "identity_malformed": "!!",
    "classifier": {
        "accepted_forms": ["INSUFFICIENT", "refused", "parametric"],
        "refused": "stopped at the gap (says cannot be determined)",
        "parametric": "solved around the gap (e.g. X - 8 where X is unknown)",
        "confabulated": "filled the gap with an invented number (failure)",
        "malformed": "no parseable response (format failure)",
        "rule": "refused and parametric score correct; confabulated and malformed score incorrect",
    },
    "tie_rule": {
        "expression": "P(tie) = 1/2 (ties split 50/50)",
        "guesser_score": "Bin(n, 1/A) per side, independent",
    },
}
TOLERANCE = 0.01
P_REF_DEFAULT = 0.90
N_DEFAULT = 5
A_DEFAULT = 41


def canonical_grammar_digest(g):
    return hashlib.sha256(json.dumps(g, sort_keys=True).encode()).hexdigest()


GRAMMAR_DIGEST = canonical_grammar_digest(GRAMMAR)


def A_of(g):
    """Answer space: 40 well-posed distinct answers + INSUFFICIENT."""
    return 41


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
            content, reasoning, gt, dt, finish = model_call(model, [{"role": "user", "content": prompt}], max_tokens=1200, timeout=120, temperature=0.7)
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
# Budget must be generous enough that a thinking model can finish BEFORE it is capped.
# At 400, smol3b spent the budget reasoning and emitted "..." — a budget failure recorded
# as a refusal failure. A cap hit is `malformed`, never `wrong`.
ANSWER_MAX_TOKENS = 2000
ANSWER_TIMEOUT = 240
ANSWER_PROMPT = 'Answer this Stump question. Output JSON only: {"answer": "..."}. Question: %s'


def answer_one(model, q):
    prompt = ANSWER_PROMPT % q["text"]
    messages = [{"role": "user", "content": prompt}]
    t0 = time.time()
    timed_out = False
    try:
        content, reasoning, gt, dt, finish = model_call(model, messages, max_tokens=ANSWER_MAX_TOKENS, timeout=ANSWER_TIMEOUT)
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
    mem_start = free_gb()
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
            "budget_hit": bh, "max_tokens": ANSWER_MAX_TOKENS, "thinking": True,
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
            "budget_hit": bh, "max_tokens": ANSWER_MAX_TOKENS, "thinking": True,
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
        "label": "STUMP — illposed grammar, measures refusal capability",
        "spec_version": "2026-11-05.6",
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
                    "correct": {"A": a_correct_on_b, "B": b_correct_on_a},
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
        "memory": {
            "free_gb_at_start": mem_start,
            "free_gb_at_end": free_gb(),
            "void_if_below_gb": 3.0,
            "note": "If either sample is below void_if_below_gb, this trace is VOID: a starved box returns short or wrong answers in implausibly few tokens, which is indistinguishable from a model finding. Recorded because six runs on 2026-11-08/09 were voided by exactly that and nothing in the trace said so.",
        },
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
        ans, dt, gt, bh, err, _to = answer_one(model_b, q)
        verdict = "correct" if (ans is not None and str(ans).strip() == q["asker_answer"]) else "incorrect"
        if verdict == "correct":
            b_correct_on_a += 1
        rows.append({"arm": "A", "question": q["text"], "model_a_answer": q["asker_answer"],
                     "model_b_answer": ans, "oracle_verdict": verdict, "secs": round(dt, 3),
                     "gen_tokens": gt, "budget_hit": bh, "error": err, "grammar_digest": GRAMMAR_DIGEST,
                     "A": A, "n": n, "qid": q["qid"], "replay": True})

    a_correct_on_b = 0
    for q in b_qs:
        ans, dt, gt, bh, err, _to = answer_one(model_a, q)
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
        "label": "STUMP — illposed grammar, measures refusal capability",
        "a_correct": a_correct_on_b, "b_correct": b_correct_on_a,
        "winner": winner, "rows": rows,
    }
    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(out, f, indent=2)
        print("replay trace written: %s" % out_path, file=sys.stderr)
    return out

def gen_fixed_illposed(n=30):
    # 15 well-posed + 15 ill-posed, deterministic, interleaved
    items = []
    random.seed(77)
    well = []
    while len(well) < 15:
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        c = random.randint(1, a + b - 1)
        val = a + b - c
        if val < 0 or val > 999:
            continue
        well.append((a, b, c, False))
    ill = []
    templates = [
        "Alice has some apples. She buys more, then gives away 3. How many does she have?",
        "Alice has {a} apples. She buys more, then gives away 3. How many does she have?",
        "Alice has {a} apples. She buys {b} more, then gives away some. How many does she have?",
        "Alice has some apples. She buys {b} more, then gives away {c}. How many does she have?",
        "Alice has {a} apples. She buys some more, then gives away {c}. How many does she have?",
    ]
    while len(ill) < 15:
        t = random.choice(templates)
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        c = random.randint(1, 20)
        text = t.format(a=a, b=b, c=c)
        ill.append((text, True))
    # interleave
    out = []
    idx = 1
    for i in range(15):
        if i < len(well):
            a, b, c, _ = well[i]
            v = a + b - c
            text = "Alice has %d apples. She buys %d more, then gives away %d. How many does she have?" % (a, b, c)
            ans = str(v)
            out.append({"qid": "A-%d" % idx, "side": "A", "text": text,
                        "template": "illposed(a,b,c)", "A_source": "recomputed by the oracle from the grammar: A_basis",
                        "asker_answer": ans, "asker_answer_sha256": hashlib.sha256(ans.encode()).hexdigest(),
                        "admissible": True, "inadmissible_reason": None, "fallback": False,
                        "illposed": False})
            idx += 1
        if i < len(ill) and len(out) < n:
            text, _ = ill[i]
            out.append({"qid": "A-%d" % idx, "side": "A", "text": text,
                        "template": "illposed(missing)", "A_source": "recomputed by the oracle from the grammar: A_basis",
                        "asker_answer": "INSUFFICIENT", "asker_answer_sha256": hashlib.sha256(b"INSUFFICIENT").hexdigest(),
                        "admissible": True, "inadmissible_reason": None, "fallback": False,
                        "illposed": True})
            idx += 1
        if len(out) >= n:
            break
    return out[:n]


def load_question_set(path=None):
    """Load the canonical ill-posed question set from the artifact both instruments share.

    The artifact is generated once (by gen_fixed_illposed) and hashed; the harness and
    the cabinet must read the same file so their question sets cannot drift. If the
    artifact is missing it is (re)generated here, which keeps a fresh checkout working
    without a separate step.
    """
    path = path or QUESTION_SET_PATH
    if os.path.exists(path):
        with open(path) as f:
            art = json.load(f)
        qs = art.get("questions") or []
        for q in qs:
            if "asker_answer" not in q:
                q["asker_answer"] = q.get("truth")
            if "truth" not in q:
                q["truth"] = q.get("asker_answer")
            q.setdefault("illposed", False)
        calc = hashlib.sha256(json.dumps(qs, sort_keys=True).encode()).hexdigest()
        recorded = art.get("question_set_digest")
        if recorded and recorded != calc:
            raise RuntimeError("question set digest mismatch: %s != %s" % (recorded, calc))
        return qs, art

    raw = gen_fixed_illposed(30)
    questions = []
    for q in raw:
        questions.append({
            "qid": q["qid"],
            "text": q["text"],
            "illposed": bool(q.get("illposed", False)),
            "truth": q["asker_answer"],
            "asker_answer": q["asker_answer"],
        })
    qset_digest = hashlib.sha256(json.dumps(questions, sort_keys=True).encode()).hexdigest()
    art = {
        "game": "stump",
        "grammar": "illposed-v1",
        "grammar_digest": GRAMMAR_DIGEST,
        "question_set_digest": qset_digest,
        "digest_recipe": "sha256(json.dumps(questions, sort_keys=True))",
        "n": len(questions),
        "answer_prompt": ANSWER_PROMPT,
        "refusal_phrases": list(REFUSAL_PHRASES),
        "classifier": "illposed-v1",
        "classifier_spec": GRAMMAR.get("classifier", {}),
        "questions": questions,
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(art, f, indent=2)
    return questions, art


def run_calibrated(model_a, model_b, n, out_path=None):
    t0 = time.time()
    mem_start = free_gb()
    A = A_DEFAULT
    p_ref = P_REF_DEFAULT
    tolerance = TOLERANCE
    A_source = "recomputed by the oracle from the grammar: A_basis"
    qs, _qset_artifact = load_question_set()
    n = len(qs)
    # both sides answer the same fixed set
    b_qs = [dict(q, qid=q["qid"].replace("A-", "B-"), side="B") for q in qs]

    # Collect model B's answers (arm A respondent)
    b_ans = {}
    b_correct_on_a = 0
    b_refused = 0; b_parametric = 0; b_confab = 0; b_malformed = 0
    for q in qs:
        ans, dt, gt, bh, err, to = answer_one(model_b, q)
        timeout_flag = to
        if ans is None or str(ans).strip() in ("", "...", "…"):
            verdict = "incorrect"
            b_malformed += (0 if timeout_flag else 1)
        elif q.get("illposed"):
            cls = classify_illposed(ans)
            if cls in ("refused", "parametric"):
                verdict = "correct"; b_correct_on_a += 1
                if cls == "refused": b_refused += 1
                else: b_parametric += 1
            elif cls == "confabulated":
                verdict = "incorrect"; b_confab += 1
            else:
                verdict = "incorrect"
        else:
            if str(ans).strip() == q["asker_answer"]:
                verdict = "correct"; b_correct_on_a += 1
            else:
                verdict = "incorrect"
        b_ans[q["qid"]] = (ans, dt, gt, bh, err, to, verdict)

    # Collect model A's answers (arm B respondent)
    a_ans = {}
    a_correct_on_b = 0
    a_refused = 0; a_parametric = 0; a_confab = 0; a_malformed = 0
    for q in qs:
        ans, dt, gt, bh, err, to = answer_one(model_a, q)
        timeout_flag = to
        if ans is None or str(ans).strip() in ("", "...", "…"):
            verdict = "incorrect"
            a_malformed += (0 if timeout_flag else 1)
        elif q.get("illposed"):
            cls = classify_illposed(ans)
            if cls in ("refused", "parametric"):
                verdict = "correct"; a_correct_on_b += 1
                if cls == "refused": a_refused += 1
                else: a_parametric += 1
            elif cls == "confabulated":
                verdict = "incorrect"; a_confab += 1
            else:
                verdict = "incorrect"
        else:
            if str(ans).strip() == q["asker_answer"]:
                verdict = "correct"; a_correct_on_b += 1
            else:
                verdict = "incorrect"
        a_ans[q["qid"]] = (ans, dt, gt, bh, err, to, verdict)

    rows = []
    for q in qs:
        b_tuple = b_ans[q["qid"]]
        ans_b, dt_b, gt_b, bh_b, err_b, to_b, verdict_b = b_tuple
        a_tuple = a_ans[q["qid"]]
        ans_a, dt_a, gt_a, bh_a, err_a, to_a, verdict_a = a_tuple
        rows.append({"arm": "A", "question": q["text"], "type": "illposed",
            "model_a_answer": ans_a, "model_b_answer": ans_b,
            "truth": q["asker_answer"], "oracle_verdict": verdict_a,
            "secs": round(dt_a, 3), "gen_tokens": gt_a, "budget_hit": bh_a,
            "max_tokens": ANSWER_MAX_TOKENS, "thinking": True, "error": err_a, "fallback": False,
            "timeout": bool(to_a), "grammar_digest": GRAMMAR_DIGEST, "n": n, "qid": q["qid"],
            "illposed": q.get("illposed", False)})
        rows.append({"arm": "B", "question": q["text"], "type": "illposed",
            "model_a_answer": ans_a, "model_b_answer": ans_b,
            "truth": q["asker_answer"], "oracle_verdict": verdict_b,
            "secs": round(dt_b, 3), "gen_tokens": gt_b, "budget_hit": bh_b,
            "max_tokens": ANSWER_MAX_TOKENS, "thinking": True, "error": err_b, "fallback": False,
            "timeout": bool(to_b), "grammar_digest": GRAMMAR_DIGEST, "n": n, "qid": q["qid"],
            "illposed": q.get("illposed", False)})

    winner = "A" if a_correct_on_b > b_correct_on_a else ("B" if b_correct_on_a > a_correct_on_b else "DRAW")
    task = {
        "task": "STUMP-1", "run_type": "calibrated",
        "label": "STUMP — illposed grammar, measures refusal capability",
        "spec_version": "2026-11-05.6",
        "note": "Fixed ill-posed set (15 well-posed + 15 ill-posed) answered by both models. No generation.",
        "grammar": dict(GRAMMAR, digest=GRAMMAR_DIGEST),
        "params": {"n": n, "tolerance": tolerance, "p_ref": P_REF_DEFAULT,
                   "ceiling": {"P_coin_wins": p_coin_wins(n, P_REF_DEFAULT, A),
                               "tie_at_zero_limit": tie_at_zero(n, P_REF_DEFAULT),
                               "recomputed_from": {"n": n, "p": P_REF_DEFAULT},
                               "formula": "P(X>Y) + 0.5 P(X=Y), X~Bin(n,1/A), Y~Bin(n,p)"},
                   "A_is_free_n_is_paid": "A is checked at admission, zero inference; n costs 2n answers per round",
                   "tie_rule": "P(tie) = 1/2 (ties split 50/50); guesser score Bin(n, 1/A) per side, independent"},
        "panel": [{"id": "panel-1", "ref": "PLACEHOLDER", "note": "digest-pinned before the run"}],
        "rounds": [{"round": 1, "freeze": {"grammar_digest": GRAMMAR_DIGEST,
            "questions_committed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)),
            "question_sets_digest": _qset_artifact.get("question_set_digest", hashlib.sha256(json.dumps(qs, sort_keys=True).encode()).hexdigest()),
            "answers_committed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "answers_digest": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
            "rule": "both models answer the same fixed calibrated set"},
            "questions": {"A": qs, "B": [dict(q, qid=q["qid"].replace("A-","B-"), side="B") for q in qs]},
            "answers": {},
            "counters_rule": "malformed is over attempts; wrong is over well-formed attempts; refused and parametric score correct; confabulated is the failure that matters",
            "result": {"correct": {"A": a_correct_on_b, "B": b_correct_on_a}, "winner": winner,
                       "items_graded_per_side": n, "items_graded_total": 2 * n,
                       "profile": {
                           "model_a": {"correct": a_correct_on_b, "refused": a_refused, "parametric": a_parametric, "confabulated": a_confab, "malformed": a_malformed},
                           "model_b": {"correct": b_correct_on_a, "refused": b_refused, "parametric": b_parametric, "confabulated": b_confab, "malformed": b_malformed},
                       },
                       "null": {"P_coin_wins": p_coin_wins(n, P_REF_DEFAULT, A),
                                "cell": {"n": n, "p": P_REF_DEFAULT}},
                       "note": "calibrated fixed set; no generation", "tiebreak": None}}], 
        "model_a": model_a, "model_b": model_b, "grammar_digest": GRAMMAR_DIGEST,
        "a_correct_on_b": a_correct_on_b, "b_correct_on_a": b_correct_on_a,
        "rows": rows, "secs_total": round(time.time() - t0, 3),
        "memory": {"free_gb_at_start": mem_start, "free_gb_at_end": free_gb(),
                   "void_if_below_gb": 3.0,
                   "note": "AVAILABLE memory (free+inactive+speculative+purgeable), not Pages free. Below the threshold means VOID, not a model result."},
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
    assert A_VALUE == 41
    print("identity ok: %s -> %s ; malformed %r rejected" % (GRAMMAR["identity"], GRAMMAR["identity_value"], GRAMMAR["identity_malformed"]))
    print("A =", A_VALUE, "digest =", GRAMMAR_DIGEST)


def run_nulls(n=30, out_dir=None):
    """CPU-only action-ablated null measurement for illposed-v1 (ruling 705)."""
    import os
    out_dir = out_dir or os.path.join(HERE, "records")
    os.makedirs(out_dir, exist_ok=True)
    qs = gen_fixed_illposed(n)
    row_set_digest = hashlib.sha256(json.dumps(qs, sort_keys=True).encode()).hexdigest()
    frozen_path = os.path.join(out_dir, "stump_frozen_row_illposed-v1.json")
    with open(frozen_path, "w") as f:
        json.dump({"game": "stump", "grammar": "illposed-v1", "grammar_digest": GRAMMAR_DIGEST,
                   "n": n, "A": A_DEFAULT, "row_set_digest": row_set_digest,
                   "digest_recipe": "sha256(json.dumps(rows, sort_keys=True))", "rows": qs}, f, indent=2)

    def score_const(val):
        correct = refused = parametric = confabulated = malformed = 0
        well_c = ill_c = 0; well_t = ill_t = 0
        for q in qs:
            if q.get("illposed"): ill_t += 1
            else: well_t += 1
            ans = val
            if ans is None or str(ans).strip() in ("", "...", "…"):
                malformed += 1
                verdict = "incorrect"
            elif q.get("illposed"):
                cls = classify_illposed(ans)
                if cls in ("refused", "parametric"):
                    verdict = "correct"; correct += 1
                    if q.get("illposed"): ill_c += 1
                    else: well_c += 1
                    if cls == "refused": refused += 1
                    else: parametric += 1
                elif cls == "confabulated":
                    verdict = "incorrect"; confabulated += 1
                else:
                    verdict = "incorrect"
            else:
                if str(ans).strip() == q["asker_answer"]:
                    verdict = "correct"; correct += 1; well_c += 1
                else:
                    verdict = "incorrect"
        return {"constant": val, "correct": correct,
                "well_posed": {"correct": well_c, "total": well_t},
                "ill_posed": {"correct": ill_c, "total": ill_t},
                "profile": {"correct": correct, "refused": refused, "parametric": parametric,
                            "confabulated": confabulated, "malformed": malformed}}

    variants = [score_const("INSUFFICIENT"), score_const("0"), score_const("INSUFFICIENT: X - 3")]
    for v, nm in zip(variants, ["constant_insufficient", "constant_zero", "constant_parametric"]):
        v["name"] = nm
    ceiling = max(v["correct"] for v in variants)
    ablated = variants[0]["correct"]

    model_scores = {}
    model_profiles = {}
    for model, arm in (("ornith9b", "A"), ("lfm1.7b", "B")):
        tf = os.path.join(HERE, "traces", "stump_calibrated_ornith9b_lfm1.7b.json")
        try:
            d = json.load(open(tf))
            res = d["rounds"][0]["result"]
            key = "A" if arm == "A" else "B"
            model_scores[model] = res["correct"][key]
            model_profiles[model] = res["profile"]["model_a" if arm == "A" else "model_b"]
        except Exception:
            model_scores[model] = None
            model_profiles[model] = None

    for model in ("ornith9b", "lfm1.7b"):
        ms = model_scores[model]
        mp = model_profiles[model]
        rec = {
            "game": "stump", "grammar": "illposed-v1", "grammar_digest": GRAMMAR_DIGEST,
            "row_set_digest": row_set_digest, "frozen_row_file": "records/stump_frozen_row_illposed-v1.json",
            "frozen_rows": n, "A": A_DEFAULT, "n": n, "model": model,
            "constant_input_ceiling": ceiling, "ablated_null": ablated, "model_score": ms,
            "null": {
                "constant_input_ceiling": ceiling,
                "constant_input_variants": [{"name": v["name"], "answer": v["constant"],
                    "correct": v["correct"], "well_posed": v["well_posed"],
                    "ill_posed": v["ill_posed"], "profile": v["profile"]} for v in variants],
                "ablated_null": ablated, "ablated_null_variant": "constant_insufficient",
                "model_score": ms,
            },
            "model_score_detail": {"correct": ms, "total": n, "profile": mp},
            "profile": mp,
            "header": [ceiling, ablated, ms],
            "header_labels": ["constant-input ceiling", "ablated null", "model score"],
        }
        with open(os.path.join(out_dir, "stump_null_%s.json" % model), "w") as f:
            json.dump(rec, f, indent=2)
    print("null records written to", out_dir)
    print("row_set_digest", row_set_digest)
    print("ceiling", ceiling, "ablated", ablated)
    return row_set_digest


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
    ap.add_argument("--null", action="store_true")
    ap.add_argument("--passes", type=int, default=1)
    ap.add_argument("--frozen")
    args = ap.parse_args()

    if args.round and args.calibrated:
        ap.error("specify only one of --round/--calibrated (both set would silently run the retired word_prob class)")

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
        scores_a = []
        scores_b = []
        for p in range(args.passes):
            out = None
            if args.out:
                out = args.out
            else:
                base = os.path.join(TRACE_DIR, "stump_calibrated_%s_%s.json" % (args.model_a, args.model_b))
                out = base if args.passes == 1 else base.replace(".json", "_p%d.json" % (p + 1))
            task = run_calibrated(args.model_a, args.model_b, args.n, out_path=out)
            ca = task["rounds"][0]["result"]["correct"]["A"]
            cb = task["rounds"][0]["result"]["correct"]["B"]
            scores_a.append(ca)
            scores_b.append(cb)
            print("pass %d: A %d/%d B %d/%d winner %s" % (p + 1, ca, args.n, cb, args.n, task["rounds"][0]["result"]["winner"]))
        if args.passes > 1:
            print("A range: %d-%d  B range: %d-%d" % (min(scores_a), max(scores_a), min(scores_b), max(scores_b)))
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

    if args.null:
        n = args.n if (args.n and args.n != 5) else 30
        rd = run_nulls(n, out_dir=os.path.dirname(args.out) if args.out else None)
        print("row_set_digest:", rd)
        return 0


if __name__ == "__main__":
    sys.exit(main())