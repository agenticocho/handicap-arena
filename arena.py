#!/usr/bin/env python3
"""
HANDICAP ARENA — a self-contained, distributable evaluation harness for local models.

  Usage:   python3 arena.py --model /path/to/model.gguf
           python3 arena.py --model-dir ~/models --pattern '*.gguf'
           python3 arena.py --self-test

WHAT MAKES THIS DIFFERENT FROM A LEADERBOARD
  The scarce thing is not the ranking, it is PROVABLE EXECUTION. So this harness:
    * LAUNCHES ITS OWN llama-server with a neutral command line it controls.
      It never talks to an application-configured endpoint. An alias is an application;
      benchmarking an application tells you nothing about the model.
    * WEIGHS THE MODEL ON A SCALE. Division is assigned by MEASURED peak VRAM at the
      benchmark's context size, not by file size or a number in a filename.
    * SCORES WITH PARSERS AND BY EXECUTING TESTS. There is no LLM judge anywhere.
    * PRINTS ITS PROVENANCE. Config, GGUF sha256, server flags. A result without its
      config is not a result.

FOUR CONFOUNDS THIS DESIGN EXISTS TO PREVENT (each one produced a confidently wrong
leaderboard when we hit it ourselves):
    1. a stale server config pointing at model files that no longer exist
       -> this harness refuses to score a model that did not serve
    2. reasoning models returning the answer in `reasoning_content` with `content` empty
       -> this harness reads both, and reports which one had to be used
    3. a GBNF grammar file applied by the serving layer, making the model physically
       incapable of the requested output
       -> this harness controls its own server flags, and records them
    4. alias names that lie (an alias called `granite-8b` serving Qwen3.5-9B)
       -> this harness takes a file path and reports its sha256
"""
import argparse, json, os, re, shutil, socket, subprocess, sys, tempfile, time, hashlib, glob
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(HERE, "tasks")

DIVISIONS = [("Featherweight", 4.0), ("Lightweight", 8.0), ("Middleweight", 16.0),
             ("Heavyweight", float("inf"))]

# Cords are the division's colour, so a card is readable at a glance.
CORDS = {"Featherweight": "teal", "Lightweight": "amber", "Middleweight": "violet",
         "Heavyweight": "crimson", "OPEN": "slate"}

# Belts earnable from a SINGLE bout, by demonstrated behaviour. Nothing is awarded by a judge.
# White..Green need one bout; Blue/Purple need consecutive results and are confirmed by the arena.
BOUT_BELTS = ["White", "Yellow", "Orange", "Green"]
BELT_ORDER = ["White", "Yellow", "Orange", "Green", "Blue", "Purple", "Brown", "Black"]


def bout_grade(rounds, trials):
    """Derive the earnable belt, stripes and round-wins from a completed bout.

    A round is won on a STRICT MAJORITY of trials, so 1-1 of 2 is a draw, not a win.
    A stripe is a single trial won. Stripes are the record; the belt is the rank.
    """
    rounds_won = 0
    stripes = 0
    total_trials = 0
    for r in rounds.values():
        w, t = r.get("wins", 0), r.get("trials", trials)
        stripes += w
        total_trials += t
        if w * 2 > t:                      # strict majority
            rounds_won += 1
    n = len(rounds)
    if n == 0:
        belt = "White"
    elif rounds_won == n:
        belt = "Green"
    elif rounds_won >= 2:
        belt = "Orange"
    elif rounds_won >= 1:
        belt = "Yellow"
    else:
        belt = "White"
    note = None
    if belt == "Green":
        note = "swept the bout — 2 more consecutive sweeps earn Blue, then Purple (a challenger slot above)"
    return dict(belt=belt, rounds_won=rounds_won, rounds=n,
                stripes=stripes, trials=total_trials, note=note)



# ---------------------------------------------------------------------------- utilities
def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def find_llama_server(explicit=None):
    if explicit:
        return explicit
    c = shutil.which("llama-server")
    if c:
        return c
    for p in ("/home/chilly1/llama.cpp/build/bin/llama-server",
              "./llama.cpp/build/bin/llama-server",
              "/usr/local/bin/llama-server",
              os.path.expanduser("~/llama.cpp/build/bin/llama-server")):
        if os.path.exists(p):
            return p
    return None


def gpu_used_mb():
    """Total GPU memory in use, in MB, or None if no NVIDIA GPU / nvidia-smi."""
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return int(out.splitlines()[0].strip())
    except Exception:
        return None


def division_for(gb):
    for name, cap in DIVISIONS:
        if gb <= cap:
            return name
    return DIVISIONS[-1][0]


# ---------------------------------------------------------------------------- the server
class LlamaServer:
    """Launches a NEUTRAL llama-server. No grammar, no template, no alias. Just the weights."""

    def __init__(self, gguf, ctx, ngl, port=None, binary=None, extra=None):
        self.gguf, self.ctx, self.ngl = gguf, ctx, ngl
        self.binary = binary or find_llama_server()
        self.port = port or free_port()
        self.flags = ["--model", gguf, "--ctx-size", str(ctx), "--n-gpu-layers", str(ngl),
                      "--host", "127.0.0.1", "--port", str(self.port)]
        if extra:
            self.flags += extra
        self.proc = None
        self.vram_base = None
        self.vram_peak = None

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}"

    def start(self, timeout=600):
        if not self.binary:
            raise RuntimeError("llama-server not found. Pass --llama-server /path/to/bin.")
        self.vram_base = gpu_used_mb()
        self.proc = subprocess.Popen([self.binary] + self.flags,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.proc.poll() is not None:
                raise RuntimeError(f"llama-server exited early rc={self.proc.returncode}")
            try:
                urllib.request.urlopen(self.url + "/health", timeout=3).read()
                time.sleep(1.0)
                self.vram_peak = gpu_used_mb()
                return True
            except Exception:
                time.sleep(1.5)
        raise RuntimeError(f"llama-server not ready within {timeout}s")

    def sample_vram(self):
        v = gpu_used_mb()
        if v is not None:
            self.vram_peak = v if self.vram_peak is None else max(self.vram_peak, v)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def footprint_gb(self):
        if self.vram_base is None or self.vram_peak is None:
            return None
        return max(0.0, (self.vram_peak - self.vram_base) / 1024.0)

    def chat(self, prompt, max_tokens, temperature=0.0):
        body = json.dumps({"messages": [{"role": "user", "content": prompt}],
                           "temperature": temperature, "max_tokens": max_tokens}).encode()
        req = urllib.request.Request(self.url + "/v1/chat/completions", data=body,
                                     headers={"Content-Type": "application/json"})
        t0 = time.time()
        r = json.load(urllib.request.urlopen(req, timeout=900))
        dt = time.time() - t0
        ch = r["choices"][0]
        m = ch.get("message", {})
        content = m.get("content") or ""
        reasoning = m.get("reasoning_content") or ""
        return dict(text=content if content.strip() else reasoning,
                    from_reasoning=bool(reasoning) and not content.strip(),
                    finish=ch.get("finish_reason"),
                    ctok=(r.get("usage") or {}).get("completion_tokens"),
                    secs=dt)


# ---------------------------------------------------------------------------- tasks
def load_tasks():
    """Task definitions live in tasks/*.json so the suite can be extended without touching code."""
    out = []
    for p in sorted(glob.glob(os.path.join(TASKS_DIR, "*.json"))):
        with open(p) as f:
            d = json.load(f)
        d["_file"] = os.path.basename(p)
        out.append(d)
    return out


def score_json_schema(spec, text):
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
        return False, "not an object"
    for k in spec.get("required", []):
        if k not in d:
            return False, f"missing {k}"
    for k, allowed in (spec.get("enums") or {}).items():
        if k in d and d[k] not in allowed:
            return False, f"{k} outside enum"
    for k, t in (spec.get("types") or {}).items():
        if k in d and not isinstance(d[k], {"string": str, "number": (int, float),
                                            "array": list, "integer": int}.get(t, object)):
            return False, f"{k} wrong type"
    for k, n in (spec.get("min_len") or {}).items():
        if isinstance(d.get(k), list) and len(d[k]) < n:
            return False, f"{k} too short"
    return True, "ok"


def score_tool_call(spec, text):
    if not text:
        return False, "empty"
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return False, "no json"
    try:
        d = json.loads(m.group(0))
    except Exception:
        return False, "unparseable"
    if d.get("tool") != spec["expect_tool"]:
        return False, f"wrong tool: {d.get('tool')}"
    args = d.get("arguments")
    if not isinstance(args, dict):
        return False, "arguments not an object"
    for k, want in spec["expect_args"].items():
        got = str(args.get(k, "")).lower()
        if want.lower() not in got:
            return False, f"arg {k}={args.get(k)!r}"
    return True, "ok"


def score_code_repair(spec, text):
    """EXECUTED. The model's code is run against a generated test suite in a subprocess."""
    if not text:
        return False, "empty"
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.S)
    code = m.group(1) if m else text
    if spec["entry_point"] not in code:
        return False, f"no {spec['entry_point']}"
    cases = "\n".join(f"assert {c['call']} == {c['expect']}, 'case {i}'"
                      for i, c in enumerate(spec["cases"]))
    harness = code + "\n\n" + cases + "\nprint('ALLPASS')\n"
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "harness.py")
        with open(p, "w") as f:
            f.write(harness)
        try:
            r = subprocess.run([sys.executable, "-I", p], cwd=d, capture_output=True,
                               text=True, timeout=30)
        except subprocess.TimeoutExpired:
            return False, "timeout"
    if r.returncode == 0 and "ALLPASS" in r.stdout:
        return True, "ok"
    err = (r.stderr or "").strip().splitlines()
    return False, (err[-1][:80] if err else "failed")


SCORERS = {"json_schema": score_json_schema,
           "tool_call": score_tool_call,
           "code_repair": score_code_repair}


# ---------------------------------------------------------------------------- self-test
def self_test():
    """Proves the SCORERS work before anyone trusts a score they produce."""
    checks = []

    def ck(name, cond):
        checks.append((name, bool(cond)))

    good_schema = '{"station":"RENO-04","readings":[1,2,3,4],"status":"nominal","sensor_count":4}'
    ck("json_schema accepts valid", score_json_schema(
        {"required": ["station", "readings", "status"],
         "enums": {"status": ["nominal", "degraded", "offline"]},
         "types": {"readings": "array"}, "min_len": {"readings": 3}}, good_schema)[0])
    ck("json_schema rejects missing key", not score_json_schema(
        {"required": ["station", "readings", "status"]}, '{"station":"x"}}')[0])
    ck("json_schema rejects bad enum", not score_json_schema(
        {"required": ["status"], "enums": {"status": ["nominal"]}}, '{"status":"broken"}')[0])
    ck("json_schema rejects empty", not score_json_schema({"required": []}, "")[0])

    tspec = {"expect_tool": "get_weather", "expect_args": {"city": "reykjavik", "units": "celsius"}}
    ck("tool_call accepts correct", score_tool_call(
        tspec, '{"tool":"get_weather","arguments":{"city":"Reykjavik","units":"celsius"}}')[0])
    ck("tool_call rejects wrong tool", not score_tool_call(
        tspec, '{"tool":"send_email","arguments":{}}')[0])
    ck("tool_call rejects missing arg", not score_tool_call(
        tspec, '{"tool":"get_weather","arguments":{"city":"Reykjavik"}}')[0])

    # the adjudicated fixed function must pass; the buggy original must fail
    fixed = ("```python\ndef merge_intervals(intervals):\n"
             "    if not intervals: return []\n"
             "    iv = sorted(intervals); out = []\n"
             "    for s, e in iv:\n"
             "        if out and s <= out[-1][1]: out[-1] = (out[-1][0], max(out[-1][1], e))\n"
             "        else: out.append((s, e))\n"
             "    return out\n```")
    buggy = fixed.replace("s <= out[-1][1]", "s < out[-1][1]")
    cspec = {"entry_point": "merge_intervals",
             "cases": [{"call": "merge_intervals([(1,4),(4,5)])", "expect": "[(1, 5)]"},
                       {"call": "merge_intervals([])", "expect": "[]"}]}
    ck("code_repair PASSES the fixed function", score_code_repair(cspec, fixed)[0])
    ck("code_repair FAILS the buggy function", not score_code_repair(cspec, buggy)[0])
    ck("code_repair rejects non-code", not score_code_repair(cspec, "I cannot help with that")[0])

    ck("division assignment", division_for(3.0) == "Featherweight"
       and division_for(6.0) == "Lightweight" and division_for(20.0) == "Heavyweight")

    npass = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print(f"\n  {npass}/{len(checks)} self-tests passed")
    return npass == len(checks)


# ---------------------------------------------------------------------------- main
def evaluate(gguf, args, tasks):
    print(f"\n{'='*88}\nWEIGH-IN: {os.path.basename(gguf)}")
    digest = sha256(gguf)
    print(f"  sha256 : {digest[:32]}...")
    print(f"  size   : {os.path.getsize(gguf)/2**30:.2f} GB (on disk)")

    srv = LlamaServer(gguf, ctx=args.ctx, ngl=args.ngl, binary=args.llama_server)
    print(f"  server : {srv.binary}")
    print(f"  flags  : {' '.join(srv.flags)}")
    print("  loading...", end="", flush=True)
    try:
        srv.start(timeout=args.load_timeout)
    except Exception as e:
        srv.stop()
        print(f"\n  *** SCRATCHED AT WEIGH-IN *** {e}")
        print("  A model that does not serve is not scored. Scoring it would publish a lie.")
        return None
    fp = srv.footprint_gb()
    div = division_for(fp) if fp is not None else "UNKNOWN (no GPU telemetry)"
    print(" ready")
    print(f"  MEASURED VRAM FOOTPRINT: {fp:.2f} GB" if fp is not None
          else "  VRAM telemetry unavailable -> division UNKNOWN")
    print(f"  DIVISION: {div}")
    print("  NOTE: footprint is baseline-subtracted. Unload other GPU workloads first, "
          "or a concurrent model's eviction will skew the scale.")

    results, lat, reasons = {}, [], 0
    for t in tasks:
        name = t["id"]
        npass = 0
        why = ""
        for i in range(args.trials):
            try:
                r = srv.chat(t["prompt"], args.max_tokens, args.temperature)
            except Exception as e:
                print(f"    {name} t{i+1}: ERR {type(e).__name__}")
                continue
            srv.sample_vram()
            lat.append(r["secs"])
            reasons += 1 if r["from_reasoning"] else 0
            ok, reason = SCORERS[t["scorer"]](t["spec"], r["text"])
            npass += 1 if ok else 0
            if not ok:
                why = reason
            print(f"    {name:16s} t{i+1}: {'PASS' if ok else 'fail'} ({r['secs']:5.1f}s)"
                  + ("" if ok else f"  [{reason}]"), flush=True)
        results[name] = dict(score=npass / args.trials, wins=npass, trials=args.trials,
                             kind=t.get("kind", ""), metaphor=t.get("metaphor", ""))
        if npass == 0 and why:
            results[name]["why"] = why
    srv.stop()

    agg = sum(v["score"] for v in results.values()) / max(len(results), 1)
    grade = bout_grade(results, args.trials)
    return dict(gguf=gguf, sha256=digest, footprint_gb=fp, division=div,
                cord=CORDS.get(div, "slate"),
                config=dict(temperature=args.temperature, max_tokens=args.max_tokens,
                            trials=args.trials, ctx=args.ctx, n_gpu_layers=args.ngl,
                            server_flags=srv.flags),
                rounds=results, aggregate=agg, grade=grade,
                certification="OPEN (self-reported) — re-run by the arena to become CERTIFIED",
                mean_latency=round(sum(lat) / len(lat), 2) if lat else None,
                answers_from_reasoning=reasons)


def print_card(res):
    g = res.get("grade") or {}
    belt = g.get("belt", "?")
    stripes = g.get("stripes", 0)
    tot = g.get("trials", 0)
    print(f"\n{'='*88}")
    print(f"  {os.path.basename(res['gguf'])}")
    print(f"  DIVISION {res['division']} (cord: {res.get('cord','-')})   "
          f"footprint {res['footprint_gb']:.2f} GB measured")
    print(f"  BELT: {belt.upper()}   stripes {stripes}/{tot}   "
          f"rounds won {g.get('rounds_won',0)}/{g.get('rounds',0)}   AGG {res['aggregate']:.2f}")
    print(f"{'-'*88}")
    for name, v in res["rounds"].items():
        w, t = v.get("wins", 0), v.get("trials", 0)
        bar = "#" * int(round(v["score"] * 40))
        print(f"  {name:16s} {v.get('metaphor',''):12s} {w}/{t}  |{bar:<40}|"
              + (f"  {v.get('why','')}" if v.get("why") else ""))
    print(f"{'-'*88}")
    print(f"  latency {res['mean_latency']}s   reasoning-field answers {res['answers_from_reasoning']}")
    print(f"  certification: {res.get('certification','')}")
    if g.get("note"):
        print(f"  next: {g['note']}")
    print(f"  config: {json.dumps(res['config'])}")


def grade_only(path):
    """Re-derive a belt from a stored result bundle — belts are computed, never assigned."""
    with open(path) as f:
        b = json.load(f)
    print(f"\n{'='*88}\nBELT REVIEW — {os.path.basename(path)}")
    print(f"  harness {b.get('harness','?')} v{b.get('version','?')}   generated {b.get('generated','?')}")
    for r in b.get("results", []):
        rounds = r.get("rounds", {})
        if rounds and any("wins" not in v for v in rounds.values()):
            print(f"\n  {os.path.basename(r['gguf'])}")
            print(f"    sha256  {r['sha256'][:24]}...")
            print("    !! CANNOT DERIVE A BELT: this bundle predates per-round win counts.")
            print("       Reporting 0 stripes here would be a confident lie. Re-run the model")
            print("       with the current harness to produce a gradeable bundle.")
            continue
        g = r.get("grade") or bout_grade(rounds, 3)
        print(f"\n  {os.path.basename(r['gguf'])}")
        print(f"    sha256  {r['sha256'][:24]}...")
        print(f"    division {r['division']}  footprint {r['footprint_gb']:.2f} GB  "
              f"cord {r.get('cord', CORDS.get(r['division'], '-'))}")
        print(f"    BELT {g['belt']}   stripes {g['stripes']}/{g['trials']}   "
              f"rounds won {g['rounds_won']}/{g['rounds']}")
        if g.get("note"):
            print(f"    next: {g['note']}")
    print(f"\n  Reminder: a belt is only valid on a CERTIFIED result. This bundle is "
          f"{b.get('results',[{}])[0].get('certification','OPEN') if b.get('results') else 'OPEN'}.")
    print(f"  To certify: send the bundle and the sha256; the arena re-runs the model on its own rig.")


def main():
    ap = argparse.ArgumentParser(description="HANDICAP ARENA — local model evaluation harness")
    ap.add_argument("--model", help="path to a .gguf")
    ap.add_argument("--model-dir", help="directory of models")
    ap.add_argument("--pattern", default="*.gguf")
    ap.add_argument("--ctx", type=int, default=4096)
    ap.add_argument("--ngl", type=int, default=99)
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=1200, dest="max_tokens")
    ap.add_argument("--load-timeout", type=int, default=600, dest="load_timeout")
    ap.add_argument("--llama-server", dest="llama_server")
    ap.add_argument("--out", help="write result bundle JSON here")
    ap.add_argument("--grade", metavar="BUNDLE.json",
                    help="re-derive belts from a stored result bundle (belts are computed, never assigned)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.grade:
        grade_only(args.grade)
        return

    if args.self_test:
        print("HANDICAP ARENA self-test — validating the scorers before any score is trusted\n")
        sys.exit(0 if self_test() else 1)

    tasks = load_tasks()
    if not tasks:
        sys.exit(f"No task definitions found in {TASKS_DIR}")

    models = []
    if args.model:
        models.append(args.model)
    if args.model_dir:
        models += sorted(glob.glob(os.path.join(os.path.expanduser(args.model_dir), args.pattern)))
    if not models:
        sys.exit("Give me --model or --model-dir. (--self-test validates the harness.)")

    print(f"HANDICAP ARENA — {len(models)} entrant(s), {len(tasks)} rounds, {args.trials} trials each")
    print("config: " + json.dumps(dict(ctx=args.ctx, ngl=args.ngl, trials=args.trials,
                                      temperature=args.temperature, max_tokens=args.max_tokens)))

    out = []
    for m in models:
        r = evaluate(m, args, tasks)
        if r:
            out.append(r)
            print_card(r)

    if out:
        print(f"\n{'='*88}\nFINAL CARD")
        for r in sorted(out, key=lambda x: -x["aggregate"]):
            g = r.get("grade") or {}
            print(f"  {r['aggregate']:.2f}  {g.get('belt','?'):>7s} belt  "
                  f"{g.get('stripes',0)}/{g.get('trials',0)} stripes  "
                  f"[{r['division']:>13s}]  {os.path.basename(r['gguf'])}")
        print(f"{'='*88}")
        print("  Belts shown are OPEN tier (self-reported). Certification re-runs the model from")
        print("  its sha256 on arena hardware; reproduce and it holds, fail and it is STRUCK.")
    if args.out:
        with open(args.out, "w") as f:
            json.dump(dict(harness="handicap-arena", version="1.0",
                           generated=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                           results=out), f, indent=2)
        print(f"\nresult bundle -> {args.out}")
        print("Submit it. If it places, we re-run it on our rig from its sha256. "
              "Reproduce and it is CERTIFIED; fail and it is STRUCK.")


if __name__ == "__main__":
    main()
