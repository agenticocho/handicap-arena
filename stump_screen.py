#!/usr/bin/env python3
"""Stump screening -- test candidate question classes for nonzero error (R10).

For each class, generate ~30 items, run against a model, report malformed vs wrong separately.
Usage: python3 stump_screen.py --model ornith9b --class all
"""
import argparse, json, os, re, sys, time, urllib.request, datetime, random

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_URLS = {
    "ornith9b": "http://127.0.0.1:8360/v1/chat/completions",
    "qwen0.6b": "http://127.0.0.1:8361/v1/chat/completions",
    "lfm1.7b": "http://127.0.0.1:8362/v1/chat/completions",
}

def model_call(model, prompt, max_tokens=500, timeout=180, thinking=False):
    url = MODEL_URLS[model]
    for attempt in range(2):
        mt = max_tokens * (2 if attempt else 1)
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
                   "max_tokens": mt, "temperature": 0.0,
                   "response_format": {"type": "json_object"},
                   "chat_template_kwargs": {"enable_thinking": thinking}}
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                d = json.loads(resp.read())
        except Exception as e:
            if attempt == 0:
                continue
            return "", "", 0, time.time() - t0
        dt = time.time() - t0
        m = d["choices"][0]["message"]
        content = m.get("content") or ""
        reasoning = m.get("reasoning_content") or ""
        if content or reasoning:
            return content, reasoning, d.get("usage", {}).get("completion_tokens", 0), dt
    return content, reasoning, d.get("usage", {}).get("completion_tokens", 0), dt

def parse_answer(content, reasoning):
    for src in (content, reasoning):
        if not src:
            continue
        try:
            obj = json.loads(src)
            if isinstance(obj, dict) and "answer" in obj:
                return str(obj["answer"]).strip()
        except Exception:
            pass
        m = re.search(r'"answer"\s*:\s*"([^"]*)"', src)
        if m:
            return m.group(1).strip()
    return None

# ---------- candidate classes ----------

def gen_order_ops():
    items = []
    random.seed(42)
    # expressions with parentheses and negatives, non-negative results
    templates = [
        lambda: (random.randint(-9, 9), random.randint(-9, 9), random.randint(-9, 9)),
    ]
    # Build expressions like (a + b) * c, a + (b * c), etc.
    count = 0
    while len(items) < 30:
        a = random.randint(-9, 9)
        b = random.randint(-9, 9)
        c = random.randint(-9, 9)
        # avoid div by zero and trivial
        exprs = [
            ("(%d + %d) * %d" % (a, b, c), (a + b) * c),
            ("%d + (%d * %d)" % (a, b, c), a + (b * c)),
            ("(%d - %d) + %d" % (a, b, c), (a - b) + c),
            ("%d * (%d + %d)" % (a, b, c), a * (b + c)),
        ]
        expr, val = random.choice(exprs)
        if val < 0 or val > 999:
            continue
        # canonical integer
        items.append({"text": "What is %s?" % expr, "answer": str(val), "cls": "order_ops"})
    return items

def gen_unit_conv():
    items = []
    conversions = [
        (1000, "kilometers to meters", "meters", lambda x: x * 1000),
        (100, "centimeters to meters", "meters", lambda x: x / 100.0),
        (60, "minutes to seconds", "seconds", lambda x: x * 60),
        (24, "hours to days", "days", lambda x: x / 24.0),
        (1000, "grams to kilograms", "kilograms", lambda x: x / 1000.0),
    ]
    random.seed(7)
    count = 0
    while len(items) < 30:
        factor, desc, unit, fn = random.choice(conversions)
        x = random.randint(1, 20)
        res = fn(x)
        # only integer results
        if isinstance(res, float):
            if not res.is_integer():
                continue
            res = int(res)
        if res < 0 or res > 999:
            continue
        items.append({"text": "Convert %d %s. Answer in %s." % (x, desc, unit),
                      "answer": str(res), "cls": "unit_conv"})
    return items

def gen_word_problems():
    items = []
    random.seed(11)
    while len(items) < 30:
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        c = random.randint(1, a + b - 1)
        val = a + b - c
        if val < 0 or val > 999:
            continue
        items.append({"text": "Alice has %d apples. She buys %d more, then gives away %d. How many does she have?" % (a, b, c),
                      "answer": str(val), "cls": "word_prob"})
    return items

def gen_date_arith():
    items = []
    random.seed(13)
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    while len(items) < 30:
        m = random.randint(1, 12)
        d = random.randint(1, 20)
        add = random.randint(1, 15)
        base = datetime.date(2024, m, d)
        res = base + datetime.timedelta(days=add)
        # answer: day of month of result
        items.append({"text": "What day of the month is %d days after %s %d?" % (add, months[m-1], d),
                      "answer": str(res.day), "cls": "date_arith"})
    return items

def gen_trap():
    items = []
    random.seed(2024)
    # Family 1: bat and ball in cents
    for _ in range(10):
        ball = random.randint(1, 20)
        diff = random.choice([1, 2, 3, 5, 10, 15, 20, 25, 50])
        total = 2 * ball + diff
        intuitive = total - diff  # the trap answer (forgetting to divide by 2)
        items.append({"text": "A bat and a ball cost %d cents together. The bat costs %d cents more than the ball. How many cents does the ball cost?" % (total, diff),
                      "answer": str(ball), "intuitive": str(intuitive), "cls": "trap"})
    # Family 2: widget scaling
    for m in [3, 4, 5, 6, 7, 8, 9, 10, 12, 15]:
        items.append({"text": "If %d machines make %d widgets in %d minutes, how long would it take 100 machines to make 100 widgets?" % (m, m, m),
                      "answer": str(m), "intuitive": "100", "cls": "trap"})
    # Family 3: lily pad
    for d in [7, 10, 12, 14, 18, 24, 30, 40, 48, 60]:
        items.append({"text": "A lily pad doubles in size every day. If it takes %d days to cover the entire lake, how many days to cover half the lake?" % d,
                      "answer": str(d - 1), "intuitive": str(d // 2), "cls": "trap"})
    return items[:30]

def gen_illposed():
    items = []
    random.seed(77)
    # well-posed: answer integer
    for _ in range(15):
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        c = random.randint(1, a + b - 1)
        items.append({"text": "Alice has %d apples. She buys %d more, then gives away %d. How many does she have?" % (a, b, c),
                      "answer": str(a + b - c), "illposed": False, "cls": "illposed"})
    # ill-posed: missing information -> INSUFFICIENT
    templates = [
        "Alice has some apples. She buys more, then gives away 3. How many does she have?",
        "Alice has {a} apples. She buys more, then gives away 3. How many does she have?",
        "Alice has {a} apples. She buys {b} more, then gives away some. How many does she have?",
        "Alice has some apples. She buys {b} more, then gives away {c}. How many does she have?",
        "Alice has {a} apples. She buys some more, then gives away {c}. How many does she have?",
    ]
    for _ in range(15):
        t = random.choice(templates)
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        c = random.randint(1, 20)
        text = t.format(a=a, b=b, c=c)
        items.append({"text": text, "answer": "INSUFFICIENT", "illposed": True, "cls": "illposed"})
    return items[:30]

CLASSES = {
    "order_ops": gen_order_ops,
    "unit_conv": gen_unit_conv,
    "word_prob": gen_word_problems,
    "date_arith": gen_date_arith,
    "trap": gen_trap,
    "illposed": gen_illposed,
}

REFUSAL_PHRASES = ["cannot", "can't", "not enough", "insufficient", "unknown", "not determined",
                    "impossible", "not possible", "don't know", "do not know", "no way to",
                    "missing", "lack", "indeterminate", "can't be determined", "cannot be determined",
                    "undetermined", "enough information", "not specified", "not provided"]


def is_refusal(text):
    if text is None:
        return False
    low = text.lower()
    return any(p in low for p in REFUSAL_PHRASES)


def has_variable(text):
    if text is None:
        return False
    return bool(re.search(r"[a-zA-Z]", text))


def has_expression(text):
    if text is None:
        return False
    return bool(re.search(r"[+\-*/=]", text))

def screen(model, items, thinking=False):
    malformed = 0
    wrong = 0
    correct = 0
    confabulated = 0
    parametric = 0
    refused = 0
    details = []
    for it in items:
        prompt = 'Answer this question. Output JSON only: {"answer": "..."}. Question: %s' % it["text"]
        content, reasoning, gt, dt = model_call(model, prompt, thinking=thinking)
        ans = parse_answer(content, reasoning)
        # normalize: extract leading number only if not a refusal
        if ans is not None and not is_refusal(ans) and ans.strip().upper() != "INSUFFICIENT":
            mnum = re.search(r"-?\d+(?:\.\d+)?", ans)
            if mnum:
                ans = mnum.group(0)
        if ans is None or ans.strip() in ("", "...", "…", "…"):
            malformed += 1
            verdict = "malformed"
        elif it.get("illposed"):
            # ill-posed: correct behavior is refusal
            if ans.strip().upper() == "INSUFFICIENT" or is_refusal(ans):
                # refused vs parametric
                if has_variable(ans) and has_expression(ans):
                    parametric += 1
                    correct += 1
                    verdict = "parametric"
                else:
                    correct += 1
                    refused += 1
                    verdict = "refused"
            elif re.search(r"^-?\d", ans.strip()):
                confabulated += 1
                verdict = "confabulated"
            else:
                wrong += 1
                verdict = "wrong"
        else:
            if ans.strip().upper() == it["answer"].strip().upper():
                correct += 1
                verdict = "correct"
            else:
                wrong += 1
                verdict = "wrong"
        details.append({"text": it["text"], "expected": it["answer"], "illposed": it.get("illposed", False),
                        "intuitive": it.get("intuitive"), "got": ans, "verdict": verdict})
    return {"n": len(items), "correct": correct, "malformed": malformed, "wrong": wrong,
            "confabulated": confabulated, "refused": refused, "parametric": parametric, "details": details}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="ornith9b")
    ap.add_argument("--class", dest="cls", default="all")
    ap.add_argument("--thinking", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    classes = list(CLASSES.keys()) if args.cls == "all" else [args.cls]
    results = {}
    for c in classes:
        print("=== Screening class: %s ===" % c, file=sys.stderr)
        items = CLASSES[c]()
        r = screen(args.model, items, thinking=args.thinking)
        results[c] = r
        print("%s: n=%d correct=%d malformed=%d wrong=%d" % (c, r["n"], r["correct"], r["malformed"], r["wrong"]), file=sys.stderr)
        # show a few wrong/malformed examples
        for d in r["details"]:
            if d["verdict"] != "correct":
                print("  [%s] %s -> got %s (expected %s)" % (d["verdict"], d["text"], d["got"], d["expected"]), file=sys.stderr)

    if args.out:
        with open(args.out, "w") as f:
            json.dump(results, f, indent=2)
        print("written:", args.out, file=sys.stderr)

if __name__ == "__main__":
    main()