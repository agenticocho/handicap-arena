#!/usr/bin/env python3
"""
arena_v0.py -- Handicap Arena v0: hardware-tiered, deterministically-scored evaluation.

DESIGN RULES (these are the whole point):
  * NO LLM judge anywhere. Every task is scored by a parser or by EXECUTING TESTS.
  * Every run records its locked configuration (temperature, max_tokens, trials) and the model id,
    because an unrecorded config makes a result worthless.
  * Models are grouped so llama-swap does not thrash between loads.
  * Throughput is reported ALONGSIDE accuracy: a model that is right but unusably slow has not
    solved the user's problem.

CLASS: Lightweight (=>8 GB). Entrants are all deployable on the reference rig (8 GB consumer GPU).

TASKS
  T1 json_schema    -- emit JSON conforming to a nested schema, under instruction pressure. Parse-scored.
  T2 tool_call      -- select the right tool and arguments from a spec. Parse-scored.
  T3 code_repair    -- fix a buggy function so a supplied test suite passes. TEST-SCORED (executed).
"""
import json, urllib.request, time, statistics as st, subprocess, sys, os, textwrap, tempfile, re

BASE = "http://127.0.0.1:8080/v1/chat/completions"
CFG = dict(temperature=0.0, max_tokens=900, trials=3)
CUTOFF_S = 240

ENTRANTS = [
    ("ocho-planner",     "Qwen3.5-9B-UD-Q4_K_XL"),
    ("critic2",          "Qwen2.5.1-Coder-7B-Instruct-Q5_K_M"),
    ("critic3",          "Meta-Llama-3.1-8B-Instruct-Q4_K_M"),
    ("rival",            "Falcon-H1R-7B-Q4_K_M"),
    ("ocho-planner-smol","SmolLM3-3B-128K-UD-Q4_K_XL"),
]


def call(alias, prompt, system=None):
    """Returns (text, seconds, error)."""
    msgs = ([{"role": "system", "content": system}] if system else []) + \
           [{"role": "user", "content": prompt}]
    body = json.dumps({"model": alias, "messages": msgs, **CFG}).encode()
    req = urllib.request.Request(BASE, data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        r = json.load(urllib.request.urlopen(req, timeout=CUTOFF_S))
        return r["choices"][0]["message"]["content"], time.time() - t0, None
    except Exception as e:
        return "", time.time() - t0, f"{type(e).__name__}"


# ---------------- T1: JSON schema compliance ----------------
T1_SCHEMA = {
    "type": "object",
    "required": ["station", "readings", "status"],
    "properties": {
        "station": {"type": "string"},
        "readings": {"type": "array", "items": {"type": "number"}, "minItems": 3},
        "status": {"type": "string", "enum": ["nominal", "degraded", "offline"]},
        "sensor_count": {"type": "integer"},
    },
}
T1_PROMPT = f"""Return ONLY a JSON object matching this JSON Schema. No prose, no code fences.

Schema: {json.dumps(T1_SCHEMA)}

Content requirements:
- station: "RENO-04"
- readings: exactly 4 numbers between -40 and 60
- status: one of the allowed values
- sensor_count: the length of the readings array

After the JSON, add a short friendly sentence explaining your choice."""


def score_t1(text):
    """Parse-scored. The trailing-prose instruction is deliberate instruction pressure."""
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
    if not isinstance(d["station"], str):
        return False, "station type"
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
T2_TOOLS = [
    {"name": "get_weather", "args": {"city": "string", "units": "celsius|fahrenheit"}},
    {"name": "send_email", "args": {"to": "string", "subject": "string", "body": "string"}},
    {"name": "db_query", "args": {"table": "string", "limit": "integer"}},
]
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
T3_TESTS = [
    ("[(1,3),(2,6),(8,10),(9,12)]", "[(1, 6), (8, 12)]"),
    ("[(1,4),(4,5)]", "[(1, 5)]"),
    ("[]", "[]"),
    ("[(5,6)]", "[(5, 6)]"),
    ("[(1,2),(3,4)]", "[(1, 2), (3, 4)]"),
]
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
    """EXECUTED. The model's code is run against a generated test harness in a subprocess."""
    code = extract_code(text)
    if not code:
        return False, "no function"
    cases = "\n".join(
        f"assert merge_intervals({args}) == {exp}, 'case {i}'"
        for i, (args, exp) in enumerate(T3_TESTS)
    )
    harness = code + "\n\n" + cases + "\nprint('ALLPASS')\n"
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "harness.py")
        open(p, "w").write(harness)
        try:
            r = subprocess.run([sys.executable, "-I", "-S", p], cwd=d,
                               capture_output=True, text=True, timeout=20)
        except subprocess.TimeoutExpired:
            return False, "timeout"
    if r.returncode == 0 and "ALLPASS" in r.stdout:
        return True, "ok"
    err = (r.stderr or "").strip().splitlines()
    return False, (err[-1][:70] if err else "failed")


TASKS = [("T1_json_schema", T1_PROMPT, score_t1, None),
         ("T2_tool_call",   T2_PROMPT, score_t2, None),
         ("T3_code_repair", T3_PROMPT, score_t3, None)]


def main():
    print("=" * 100)
    print("HANDICAP ARENA v0 — Lightweight class (<=8GB) — deterministically scored, no LLM judge")
    print(f"locked config: temperature={CFG['temperature']}  max_tokens={CFG['max_tokens']}  "
          f"trials/task={CFG['trials']}  endpoint={BASE}")
    print("=" * 100)
    results = {}
    for alias, model in ENTRANTS:
        results[alias] = {"model": model, "tasks": {}, "lat": []}
        print(f"\n--- {alias}  [{model}] ---", flush=True)
        for tname, prompt, scorer, _ in TASKS:
            npass = 0
            why = ""
            for k in range(CFG["trials"]):
                txt, sec, err = call(alias, prompt)
                if err:
                    why = err
                    print(f"    {tname} trial{k+1}: CALL ERR {err}", flush=True)
                    continue
                results[alias]["lat"].append(sec)
                ok, reason = scorer(txt)
                npass += 1 if ok else 0
                if not ok:
                    why = reason
                print(f"    {tname} trial{k+1}: {'PASS' if ok else 'fail'}  ({sec:5.1f}s)"
                      + ("" if ok else f"  [{reason}]"), flush=True)
            results[alias]["tasks"][tname] = npass / CFG["trials"]
            if npass == 0 and why:
                results[alias].setdefault("notes", []).append(f"{tname}: {why}")

    print("\n" + "=" * 100)
    print(f"{'rank':>4s} {'entrant':22s} {'model':34s} " +
          " ".join(f"{t[0][:9]:>10s}" for t in TASKS) + f" {'AGG':>6s} {'mean lat':>9s}")
    print("-" * 100)
    ranked = []
    for alias, r in results.items():
        agg = st.mean(r["tasks"].values())
        ml = st.mean(r["lat"]) if r["lat"] else float("nan")
        ranked.append((agg, alias, r, ml))
    for i, (agg, alias, r, ml) in enumerate(sorted(ranked, reverse=True), 1):
        cells = " ".join(f"{r['tasks'][t[0]]:10.2f}" for t in TASKS)
        print(f"{i:>4d} {alias:22s} {r['model'][:34]:34s} {cells} {agg:6.2f} {ml:8.1f}s")
    print("=" * 100)
    print()
    print("AGG = mean task pass-rate across 3 trials each. Scored by parsers and by EXECUTING tests.")
    print("Config is locked and recorded above; a result without its config is not a result.")
    print("\nnotes (first failure reason per entrant):")
    for alias, r in results.items():
        if r.get("notes"):
            print(f"  {alias:22s} {' | '.join(r['notes'])}")


if __name__ == "__main__":
    main()
