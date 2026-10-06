#!/usr/bin/env python3
"""
arena_v0.1.py -- Handicap Arena, corrected harness.

WHAT v0 GOT WRONG (kept here deliberately, because it is the whole lesson):
  1. Two entrants in the field did not exist on disk. The server config had stale entries pointing
     at deleted GGUFs, so 40% of the "field" 404'd and was scored 0.00 as if it were a model result.
  2. A reasoning model returns its answer in `reasoning_content` with `content` EMPTY. The scorer
     read only `content`, so a strong model scored 0.00 across the board.

BOTH FAILURES WERE HARNESS FAILURES WEARING A LEADERBOARD'S CLOTHES. Which is the entire argument
for this project: standardised, VERIFIED execution is the scarce thing. A leaderboard built on an
unverified harness is worse than no leaderboard, because it is confidently wrong.

FIXES:
  * PRE-FLIGHT: every entrant must prove it serves before it is allowed to be scored.
  * MESSAGE EXTRACTION: content -> falls back to reasoning_content when content is empty.
  * PROVENANCE: records finish_reason, whether reasoning was used, and the model file size
    (which is what defines the weight class, not the parameter count).
  * Config is locked and printed with the run.

SCORING: no LLM judge anywhere. Parsers, and executing generated code against a test suite.
"""
import json, urllib.request, time, statistics as st, subprocess, sys, os, tempfile, re, glob

BASE = "http://127.0.0.1:8080/v1/chat/completions"
CFG = dict(temperature=0.0, max_tokens=1200, trials=3)
CUTOFF_S = 300

# (alias, label, class) -- aliases verified to exist; stale config entries removed after diagnosis
ENTRANTS = [
    ("critic3",           "Meta-Llama-3.1-8B-Instruct-Q4_K_M",     "Lightweight"),
    ("ocho-planner",      "Qwen3.5-9B-UD-Q4_K_XL",                 "Lightweight"),
    ("ocho-planner-4b",   "Qwen3.5-4B-UD-Q4_K_XL",                 "Featherweight"),
    ("ocho-planner-smol", "SmolLM3-3B-128K-UD-Q4_K_XL",            "Featherweight"),
    ("helper",            "LFM2-350M-Extract-Q4_K_M",              "Featherweight"),
    ("ocho-planner-ornith35", "Ornith-1.5-35B-A3B-TIEL-Calibrated","Heavyweight"),
]


def gguf_size(label):
    hits = glob.glob(f"/home/chilly1/moltbook_pipeline/models/*{label.split('-Q4')[0][:22]}*")
    for h in hits:
        try:
            return os.path.getsize(h)
        except OSError:
            pass
    return None


def call(alias, prompt, max_tokens=None):
    """Returns (text, seconds, error, meta). text falls back to reasoning_content."""
    body = json.dumps({"model": alias,
                       "messages": [{"role": "user", "content": prompt}],
                       "temperature": CFG["temperature"],
                       "max_tokens": max_tokens or CFG["max_tokens"]}).encode()
    req = urllib.request.Request(BASE, data=body, headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        r = json.load(urllib.request.urlopen(req, timeout=CUTOFF_S))
    except Exception as e:
        return "", time.time() - t0, f"{type(e).__name__}", {}
    dt = time.time() - t0
    ch = r["choices"][0]
    m = ch.get("message", {})
    content = m.get("content") or ""
    reasoning = m.get("reasoning_content") or ""
    # THE FIX: a reasoning model puts its answer here when content is empty
    text = content if content.strip() else reasoning
    meta = dict(finish=ch.get("finish_reason"),
                used_reasoning=bool(reasoning) and not content.strip(),
                completion_tokens=(r.get("usage") or {}).get("completion_tokens"))
    return text, dt, None, meta


def preflight(alias):
    """An entrant must PROVE it serves before it can be scored."""
    txt, dt, err, meta = call(alias, "Reply with exactly: OK", max_tokens=200)
    return (err is None and bool(txt.strip())), err, dt


# ---------------- T1: JSON schema compliance ----------------
T1_SCHEMA = {"type": "object", "required": ["station", "readings", "status"],
             "properties": {"station": {"type": "string"},
                            "readings": {"type": "array", "items": {"type": "number"}, "minItems": 3},
                            "status": {"type": "string", "enum": ["nominal", "degraded", "offline"]},
                            "sensor_count": {"type": "integer"}}}
T1_PROMPT = f"""Return ONLY a JSON object matching this JSON Schema. No prose, no code fences.

Schema: {json.dumps(T1_SCHEMA)}

Content requirements:
- station: "RENO-04"
- readings: exactly 4 numbers between -40 and 60
- status: one of the allowed values
- sensor_count: the length of the readings array

After the JSON, add a short friendly sentence explaining your choice."""


def score_t1(text):
    if not text:
        return False, "empty"
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return False, "no json object"
    try:
        d = json.loads(m.group(0))
    except Exception:
        return False, "unparseable"
    if not isinstance(d, dict):
        return False, "not object"
    for k in ("station", "readings", "status"):
        if k not in d:
            return False, f"missing {k}"
    if not isinstance(d["readings"], list) or len(d["readings"]) < 3:
        return False, "readings"
    if not all(isinstance(x, (int, float)) for x in d["readings"]):
        return False, "readings types"
    if d["status"] not in ("nominal", "degraded", "offline"):
        return False, "status enum"
    if "sensor_count" in d and d["sensor_count"] != len(d["readings"]):
        return False, "sensor_count mismatch"
    return True, "ok"


# ---------------- T2: tool-call correctness ----------------
T2_TOOLS = [{"name": "get_weather", "args": {"city": "string", "units": "celsius|fahrenheit"}},
            {"name": "send_email", "args": {"to": "string", "subject": "string", "body": "string"}},
            {"name": "db_query", "args": {"table": "string", "limit": "integer"}}]
T2_PROMPT = f"""You have these tools: {json.dumps(T2_TOOLS)}

User request: "What's the temperature in Reykjavik right now, in celsius?"

Respond with ONLY a JSON object of the form:
{{"tool": "<tool name>", "arguments": {{...}}}}
No prose, no code fences."""


def score_t2(text):
    if not text:
        return False, "empty"
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return False, "no json"
    try:
        d = json.loads(m.group(0))
    except Exception:
        return False, "unparseable"
    if d.get("tool") != "get_weather":
        return False, f"wrong tool: {d.get('tool')}"
    a = d.get("arguments") or {}
    if not isinstance(a, dict):
        return False, "args not object"
    if "city" not in a or "reykjavik" not in str(a["city"]).lower():
        return False, "city arg"
    if str(a.get("units", "")).lower() != "celsius":
        return False, "units arg"
    return True, "ok"


# ---------------- T3: code repair (TEST-SCORED) ----------------
T3_BUGGY = '''def merge_intervals(intervals):
    """Merge overlapping OR touching closed intervals. Return sorted list of tuples."""
    if not intervals:
        return []
    iv = sorted(intervals)
    out = []
    for s, e in iv:
        if out and s < out[-1][1]:          # BUG: touched intervals must also merge
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out
'''
T3_CASES = [("[(1,3),(2,6),(8,10),(9,12)]", "[(1, 6), (8, 12)]"),
            ("[(1,4),(4,5)]", "[(1, 5)]"),
            ("[]", "[]"),
            ("[(5,6)]", "[(5, 6)]"),
            ("[(1,2),(3,4)]", "[(1, 2), (3, 4)]")]
T3_PROMPT = f"""This function has a bug: it fails to merge intervals that TOUCH.

```python
{T3_BUGGY}```

It must pass these cases:
  merge_intervals([(1,3),(2,6),(8,10),(9,12)]) == [(1, 6), (8, 12)]
  merge_intervals([(1,4),(4,5)])               == [(1, 5)]
  merge_intervals([])                          == []
  merge_intervals([(5,6)])                     == [(5, 6)]
  merge_intervals([(1,2),(3,4)])               == [(1, 2), (3, 4)]

Return ONLY the corrected function in a single ```python code block. No explanation."""


def extract_code(text):
    if not text:
        return None
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.S)
    code = m.group(1) if m else text
    return code if "def merge_intervals" in code else None


def score_t3(text):
    code = extract_code(text)
    if not code:
        return False, "no function"
    cases = "\n".join(f"assert merge_intervals({a}) == {e}, 'case {i}'"
                      for i, (a, e) in enumerate(T3_CASES))
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "harness.py")
        open(p, "w").write(code + "\n\n" + cases + "\nprint('ALLPASS')\n")
        try:
            r = subprocess.run([sys.executable, "-I", p], cwd=d,
                               capture_output=True, text=True, timeout=25)
        except subprocess.TimeoutExpired:
            return False, "timeout"
    if r.returncode == 0 and "ALLPASS" in r.stdout:
        return True, "ok"
    err = (r.stderr or "").strip().splitlines()
    return False, (err[-1][:70] if err else "failed")


TASKS = [("T1_json_schema", T1_PROMPT, score_t1),
         ("T2_tool_call",   T2_PROMPT, score_t2),
         ("T3_code_repair", T3_PROMPT, score_t3)]


def main():
    print("=" * 108)
    print("HANDICAP ARENA v0.1 — hardware-classed, deterministically scored, PRE-FLIGHT VERIFIED")
    print(f"locked config: temperature={CFG['temperature']}  max_tokens={CFG['max_tokens']}  "
          f"trials/task={CFG['trials']}  endpoint={BASE}")
    print("=" * 108)
    print("\n--- PRE-FLIGHT: every entrant must prove it serves ---", flush=True)
    serving = []
    for alias, label, klass in ENTRANTS:
        ok, err, dt = preflight(alias)
        sz = gguf_size(label)
        szs = f"{sz/2**30:.2f}GB" if sz else "  ?  "
        print(f"  {'SERVE' if ok else 'DEAD '}  {alias:24s} {klass:14s} {szs:>8s}  "
              f"{dt:5.1f}s" + ("" if ok else f"  [{err}]"), flush=True)
        if ok:
            serving.append((alias, label, klass))
    dropped = len(ENTRANTS) - len(serving)
    if dropped:
        print(f"\n  {dropped} entrant(s) DROPPED — they cannot be scored, and scoring them would "
              f"publish a lie.")
    print()

    results = {}
    for alias, label, klass in serving:
        results[alias] = {"label": label, "klass": klass, "tasks": {}, "lat": [], "reason_n": 0}
        print(f"--- {alias} [{label}] ({klass}) ---", flush=True)
        for tname, prompt, scorer in TASKS:
            npass = 0
            why = ""
            for k in range(CFG["trials"]):
                txt, sec, err, meta = call(alias, prompt)
                if err:
                    why = err
                    print(f"    {tname} t{k+1}: CALL ERR {err}", flush=True)
                    continue
                results[alias]["lat"].append(sec)
                if meta.get("used_reasoning"):
                    results[alias]["reason_n"] += 1
                ok, reason = scorer(txt)
                npass += 1 if ok else 0
                if not ok:
                    why = reason
                print(f"    {tname} t{k+1}: {'PASS' if ok else 'fail'} ({sec:5.1f}s)"
                      + ("" if ok else f"  [{reason}]"), flush=True)
            results[alias]["tasks"][tname] = npass / CFG["trials"]
            if npass == 0 and why:
                results[alias].setdefault("notes", []).append(f"{tname}: {why}")

    print("\n" + "=" * 108)
    hdr = f"{'rank':>4s} {'entrant':24s} {'class':14s} {'model':32s} " + \
          " ".join(f"{t.split('_')[0]:>11s}" for t, _, _ in TASKS) + f" {'AGG':>6s} {'lat':>7s}"
    print(hdr)
    print("-" * 108)
    ranked = sorted(((st.mean(r["tasks"].values()), a, r) for a, r in results.items()), reverse=True)
    for i, (agg, alias, r) in enumerate(ranked, 1):
        cells = " ".join(f"{r['tasks'][t]:11.2f}" for t, _, _ in TASKS)
        ml = st.mean(r["lat"]) if r["lat"] else float("nan")
        print(f"{i:>4d} {alias:24s} {r['klass']:14s} {r['label'][:32]:32s} {cells} {agg:6.2f} {ml:6.1f}s")
    print("=" * 108)
    print(f"\nOnly PRE-FLIGHT VERIFIED entrants appear above. Config is locked and printed.")
    for alias, r in results.items():
        if r.get("reason_n"):
            print(f"  note: {alias} answered via reasoning_content on {r['reason_n']} calls "
                  f"(content empty) — a v0-style harness would have scored it 0.00")
        if r.get("notes"):
            print(f"  {alias:24s} {' | '.join(r['notes'])}")


if __name__ == "__main__":
    main()
