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
import urllib.request, shlex, atexit, signal

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


def bout_grade(rounds, trials, aggregate=None, belt_rule=1):
    """Derive the earnable belt, stripes and round-wins from a completed bout.

    BELT RULE v2 — MONOTONIC IN THE AGGREGATE. The Chair found what I missed: under the v1 rule
    the belt is NOT monotonic. Cross-tabbing the v2 field gives pairs where a LOWER aggregate
    earns a HIGHER belt:

        0.5000 -> Orange   outranks   0.5555 -> Yellow
        0.7222 -> Green    outranks   0.8333 -> Orange

    `rounds_won` causes it: it counts rounds with a strict majority of items and DISCARDS how
    well each was won, so 6/6+6/6+4/6 and 5/6+5/6+4/6 are the same belt. A belt-sorted UI would
    therefore rank a weaker model above a stronger one — not lossy, WRONG. That is why the front
    end must not be belt-sorted, and why this rule is fixed before one ships.

    A round is still won on a strict majority of trials, and stripes are still the record. The
    belt is now banded on the aggregate, which makes it monotonic by construction. The bands are
    a DESIGN CHOICE, stated rather than derived, and the pass/fail criteria in CARD_v2.md were
    evaluated against the OLD rule — they are not re-scored under this one.
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

    if belt_rule >= 2 and aggregate is not None:
        if n == 0:
            belt = "White"
        elif aggregate >= 0.90:
            belt = "Green"
        elif aggregate >= 0.65:
            belt = "Orange"
        elif aggregate >= 0.30:
            belt = "Yellow"
        else:
            belt = "White"
    elif n == 0:
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
                stripes=stripes, trials=total_trials, note=note,
                belt_rule=belt_rule)



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
    """explicit -> env -> PATH -> known locations -> REFUSE. Never a bare name.

    A resolver that cannot resolve must return None and let the caller refuse. The alternative --
    falling back to a string literal -- is what produced 26 empty bundles: the literal is truthy, so
    arena.py's call site `binary or find_llama_server()` skipped this function entirely, and the
    absolute path three lines below was never reached. The guard that says "llama-server not found"
    could not fire, because the failure path was pre-empted by a name.

    Same trap as hermes-webui.service resolving a Python interpreter by PATH and silently taking
    whatever it found; it now refuses unless exactly one match exists. Same day, different service.
    """
    if explicit:
        # An explicit path that does not exist is an ERROR, not a hint. Silently continuing to the
        # next candidate is how a typo becomes a mystery -- and this line previously returned it
        # unchecked, so `--llama-server /typo` would have been handed to exec.
        if not os.path.exists(explicit):
            raise SystemExit(f"llama-server {explicit!r} does not exist")
        return explicit
    for p in (os.environ.get("LLAMA_SERVER", ""),
              shutil.which("llama-server") or "",
              "/home/chilly1/llama.cpp/build/bin/llama-server",
              "./llama.cpp/build/bin/llama-server",
              "/usr/local/bin/llama-server",
              os.path.expanduser("~/llama.cpp/build/bin/llama-server")):
        if p and os.path.exists(p):
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


def gpu_free_mb():
    """Free GPU memory in MB, or None. The complement of gpu_used_mb(), and the number that
    decides how much of a model llama.cpp is willing to place."""
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
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

    LIVE = []          # class-level registry so a killed run cannot leak VRAM

    @classmethod
    def kill_all(cls):
        for s in list(cls.LIVE):
            try:
                s.stop()
            except Exception:
                pass

    @classmethod
    def install_guards(cls):
        """A crashed or killed run must not leave a model resident holding VRAM.

        atexit covers normal exits; SIGTERM/SIGINT cover Ctrl-C and a killed shell. SIGKILL cannot
        be caught, so a hard kill can still leak one server — check with:
            pgrep -af 'llama-server.*arena'
        """
        atexit.register(cls.kill_all)
        for sig in (signal.SIGTERM, signal.SIGINT):
            prev = signal.getsignal(sig)

            def handler(signum, frame, _prev=prev):
                cls.kill_all()
                if callable(_prev):
                    _prev(signum, frame)
                else:
                    sys.exit(128 + signum)
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError):
                pass            # not on the main thread; atexit still applies

    def __init__(self, gguf, ctx, ngl, port=None, binary=None, extra=None):
        self.gguf, self.ctx, self.ngl = gguf, ctx, ngl
        self.binary = binary or find_llama_server()
        self.port = port or free_port()
        self.flags = ["--model", gguf, "--ctx-size", str(ctx)]
        # DO NOT pass --n-gpu-layers unless explicitly asked. llama.cpp probes free device memory
        # and auto-fits the layer count when the user has not set it -- but if the flag IS set and
        # the placement does not fit, it ABORTS instead ("failed to fit params to free device
        # memory: n_gpu_layers already set by user to 99, abort"). An always-on --ngl 99 therefore
        # converts a graceful partial offload into an out-of-memory failure on any contended GPU,
        # which is the COMMON case on a machine that also serves other models.
        # Omission = auto-fit = the model loads, partially offloaded, and the weigh-in reports the
        # smaller footprint honestly. That is the Open/Offload division working as designed.
        if ngl is not None:
            self.flags += ["--n-gpu-layers", str(ngl)]
        self.flags += ["--host", "127.0.0.1", "--port", str(self.port)]
        if extra:
            self.flags += extra
        self.proc = None
        self.vram_base = None
        self.vram_peak = None
        self.vram_free_mb = None
        # THE RUN'S OWN DIAGNOSTIC EVIDENCE MUST OUTLIVE THE RUN.
        #
        # This was tempfile.gettempdir(): a shared namespace with a half-life nobody controls. The
        # server logs from a run still in flight were already gone when Chilly went looking, so the
        # one artifact that could explain a failed load had deleted itself by design. **Discarding
        # by where you put it is the quietest way to lose it.**
        #
        # Same rule as FINDING 007 -- no verdict may depend on data that was discarded at scoring
        # time -- applied to diagnostics: where the data lives decides whether it is discarded.
        # logs/ and not results/, because results/ holds result bundles and nothing else; a log
        # sitting among them is the kind of file a reader counts as an entrant.
        _logs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(_logs, exist_ok=True)
        self.logpath = os.path.join(_logs, f"arena-server-{os.getpid()}-{self.port}.log")

    def server_log_tail(self, lines=14):
        """A weigh-in that cannot explain itself is a bad weigh-in. Capture the server's own words."""
        try:
            with open(self.logpath, errors="replace") as f:
                tail = f.read().strip().splitlines()[-lines:]
            return [l for l in tail if l.strip()]
        except OSError:
            return []

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}"

    def start(self, timeout=600):
        if not self.binary:
            raise RuntimeError("llama-server not found. Pass --llama-server /path/to/bin.")
        self.vram_base = gpu_used_mb()
        # FINDING 002: capture ambient free VRAM at load. Auto-fit places layers according to THIS
        # number, so without it a footprint cannot be interpreted after the fact.
        self.vram_free_mb = gpu_free_mb()
        self._logfh = open(self.logpath, "w")
        self.proc = subprocess.Popen([self.binary] + self.flags,
                                     stdout=self._logfh, stderr=subprocess.STDOUT)
        LlamaServer.LIVE.append(self)
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.proc.poll() is not None:
                raise RuntimeError(f"llama-server exited early rc={self.proc.returncode} "
                                   f"(log: {self.logpath})")
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
        if self in LlamaServer.LIVE:
            LlamaServer.LIVE.remove(self)
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        try:
            self._logfh.close()
        except Exception:
            pass

    def footprint_gb(self):
        if self.vram_base is None or self.vram_peak is None:
            return None
        return max(0.0, (self.vram_peak - self.vram_base) / 1024.0)

    def weights_gb(self):
        """The model's weights on disk. This is what the model IS, before any machine gets a say."""
        try:
            return os.path.getsize(self.gguf) / 1e9
        except Exception:
            return None

    def weigh_in(self):
        """A weigh-in that can tell the difference between a model and a machine.

        FINDING 002: a footprint taken under auto-fit reports whatever ambient VRAM allowed. The
        same checkpoint measured 1.55-1.64 GB fully offloaded and 0.20 GB when the GPU was
        contended by another service -- an 8x spread that moves a model down a whole weight class.

        The test needs no calibration:

            resident < weights on disk  ==>  partial offload  ==>  we measured the MACHINE

        A model cannot occupy less VRAM than its own weights occupy on disk. When it appears to,
        the surplus is on CPU, and `division_from_resident` becomes a statement about what else was
        running -- not about the entrant. `division_for_competition` therefore takes the division
        from WEIGHTS in that case, and from the real resident footprint otherwise.
        """
        fp, wd = self.footprint_gb(), self.weights_gb()
        partial = bool(fp is not None and wd is not None and fp < wd * 0.95)
        d_res = None if fp is None else division_for(fp)
        d_wts = None if wd is None else division_for(wd)
        return dict(
            ngl_requested=self.ngl,                     # null = auto-fit
            placement="forced" if self.ngl is not None else "auto-fit",
            footprint_gb=None if fp is None else round(fp, 2),
            weights_gb=None if wd is None else round(wd, 2),
            gpu_free_gb_at_weigh_in=(None if self.vram_free_mb is None
                                     else round(self.vram_free_mb / 1024.0, 2)),
            partial_offload=partial,
            division_from_resident=d_res,
            division_from_weights=d_wts,
            # The one that counts. Partial offload means the resident number is the machine's.
            division_for_competition=(d_wts if partial else (d_res or d_wts)),
        )

    def print_weigh_in(self):
        w = self.weigh_in()
        line = f"  footprint {w['footprint_gb']} GB measured ({w['placement']}"
        if w["ngl_requested"] is not None:
            line += f" ngl={w['ngl_requested']}"
        line += f", gpu free {w['gpu_free_gb_at_weigh_in']} GB)"
        print(line, flush=True)
        if w["partial_offload"]:
            print(f"  ** PARTIAL OFFLOAD — resident {w['footprint_gb']} GB is LESS than the "
                  f"{w['weights_gb']} GB of weights on disk, so the surplus is on CPU.")
            print(f"     That footprint is a measurement of THE MACHINE, not the model. "
                  f"Division from resident would read {w['division_from_resident']}; from weights "
                  f"it is {w['division_from_weights']}.")
            print(f"     FINDING 002: weigh in with a declared placement, or do not weigh in. "
                  f"Competition division is taken from WEIGHTS, and the CPU placement is a cost "
                  f"the biathlon will charge for.")
        return w

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
        usage = r.get("usage") or {}
        return dict(text=content if content.strip() else reasoning,
                    from_reasoning=bool(reasoning) and not content.strip(),
                    finish=ch.get("finish_reason"),
                    ctok=usage.get("completion_tokens"),
                    ptok=usage.get("prompt_tokens"),
                    secs=dt)


# ---------------------------------------------------------------------------- tasks
def load_tasks(card="v1"):
    """card='v2' returns one pseudo-task PER ITEM (see load_card_v2). v1 is untouched."""
    if card == "v5":
        return load_card_v5()
    if card == "v4":
        return load_card_v4()
    if card == "v3":
        return load_card_v3()
    if card == "v2":
        return load_card_v2()
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


# ------------------------------------------------------------------ CARD v2 scorers
# v2 runs a BATTERY of distinct items per round instead of repeated trials of one prompt.
# Three trials at temperature 0 are three copies of one measurement, which is why the v1 field
# was bimodal (0/3 or 3/3, nothing between). Items, not repetitions, are what create a gradient.
#
# Two v2 items are won by DOING NOTHING -- "no tool is correct" and "the code is already
# correct". They exist to be failed by any model that must always produce output.

def _first_json(text):
    if not text:
        return None, "empty"
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None, "no json object"
    try:
        return json.loads(m.group(0)), "ok"
    except Exception:
        return None, "unparseable"


def _deep_eq(a, b):
    """Numeric-tolerant deep equality: 4250 == 4250.0, and 'Oslo' == 'oslo' for strings."""
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_deep_eq(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_deep_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().lower() == b.strip().lower()
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 1e-9
    return a == b


def score_json_schema_multi(spec, text):
    """PARTIAL CREDIT: fraction of required fields correct. A near-miss beats a blank, and a
    blank beats nothing at all -- so the score carries how close the model got, not just
    whether it got there."""
    d, why = _first_json(text)
    if d is None:
        return 0.0, why
    if not isinstance(d, dict):
        return 0.0, "not an object"
    exp = spec if isinstance(spec, dict) else {}
    if not exp:
        return 0.0, "no expectation"
    got = sum(1 for k, v in exp.items() if k in d and _deep_eq(d[k], v))
    return got / len(exp), f"{got}/{len(exp)} fields"


def score_json_schema_strict_multi(spec, text):
    """CARD v3's R1 scorer. v2's counted REQUIRED FIELDS ONLY, so adding keys was free -- and
    adding keys is the failure the v3 items are built to elicit. This one also scores the two
    things a schema states and a field-count cannot see:

      * a FORBIDDEN key present  -> 0.0. The schema said "exactly these keys"; an extra one is not
        a deduction, it is the item. R1.1 gives the model a doctor to transcribe and forbids the
        key. Omission is the task.
      * an exact KEY SET violated (spec['forbid_all_other_keys']) -> 0.0.
      * and the null case: a key the model filled with null where the schema said OMIT. That is
        named separately in the reason because "absent" and "null" are different claims -- but it
        costs the field, because the field was not emitted.

    spec is a WRAPPER: {"expect": {...}, "forbid": [...], "forbid_all_other_keys": bool}. Passing
    the expectation bare and adding these to it would make them look like required fields, which
    is the same class of bug as v2's loader passing the whole item as the spec.
    """
    d, why = _first_json(text)
    if d is None:
        return 0.0, why
    if not isinstance(d, dict):
        return 0.0, "not an object"
    exp = spec.get("expect") or {}
    if not exp:
        return 0.0, "no expectation"
    forbid = set(spec.get("forbid") or [])
    hit = sorted(k for k in forbid if k in d)
    if hit:
        return 0.0, f"emitted forbidden key(s): {hit}"
    if spec.get("forbid_all_other_keys"):
        extra = sorted(set(d) - set(exp))
        if extra:
            return 0.0, f"extra key(s) outside the schema: {extra}"

    def _ok(k):
        if k not in d:
            return False
        if d[k] is None:
            return False          # null is not the value; absent was required
        return _deep_eq(d[k], exp[k])

    got = sum(1 for k in exp if _ok(k))
    nulled = sorted(k for k in exp if k in d and d[k] is None)
    note = f"{got}/{len(exp)} fields"
    if nulled:
        note += f" (null where OMIT was required: {nulled})"
    return got / len(exp), note


def score_tool_call_multi(spec, text):
    """Handles the null case: an item whose correct answer is 'no available tool' is won by
    emitting null, and lost by emitting any plausible tool."""
    d, why = _first_json(text)
    if d is None:
        return 0.0, why
    exp = spec.get("expect", spec)
    want_tool = exp.get("tool")
    got_tool = d.get("tool")
    if want_tool is None:
        if got_tool in (None, "", "null"):
            return 1.0, "ok (correctly declined)"
        return 0.0, f"guessed {got_tool!r} where no tool fits"
    if got_tool != want_tool:
        return 0.0, f"wrong tool: {got_tool!r}"
    want_args = exp.get("arguments") or {}
    if not want_args:
        return 1.0, "ok"
    args = d.get("arguments")
    if not isinstance(args, dict):
        return 0.0, "arguments not an object"
    got = sum(1 for k, v in want_args.items() if k in args and _deep_eq(args[k], v))
    return (0.5 + 0.5 * got / len(want_args)), f"tool ok, {got}/{len(want_args)} args"


def score_code_repair_multi(spec, text):
    """Executed against cases in a subprocess. Two things v1 could not express:
      * expect_unchanged -- the item is won by changing nothing;
      * 'call' entries that are assertions rather than calls (e.g. checking the input list was
        not mutated), which is how a silent-mutation bug becomes detectable."""
    if not text:
        return 0.0, "empty"
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.S)
    code = m.group(1) if m else text
    if spec.get("expect_unchanged"):
        # the model must return the function as given. Any invented "fix" is a failure.
        if "def clamp" not in code:
            return 0.0, "did not return the function"
        body = code.split("def clamp", 1)[1]
        invented = ("min(" in body or "max(" in body) and "if x < lo" not in body
        if invented:
            return 0.0, "changed correct code"
        return 1.0, "ok (unchanged, correctly)"
    if spec.get("expect_contains") and spec["expect_contains"] not in code:
        return 0.0, f"missing {spec['expect_contains']!r}"
    # Some items must be graded in a context: a correct function the model is NOT allowed to
    # change (R3.5's whole point is that the bug is in the caller), or a list the mutation check
    # has to inspect afterwards.
    cases, prelude = [], spec.get("harness_prelude", "")
    for i, c in enumerate(spec.get("cases") or []):
        if "mutates" in c:
            # A mutation check must run the function ON a known list and then inspect that SAME
            # list. Asserting on a fresh literal proves nothing: the mutation lands on an object
            # the assertion never saw, which is why the first version of this passed a function
            # that mutated its input.
            prelude += f"_orig = {c['want_input']}\n"
            cases.append(f"assert {c['mutates']} == {c['want_result']}, 'wrong result'")
            cases.append(f"assert _orig == {c['want_input']}, 'mutated its input'")
            continue
        call, want = c.get("call"), c.get("want")
        cases.append(f"assert {call} == {want}, 'case {i}'")
    harness = prelude + code + "\n\n" + "\n".join(cases) + "\nprint('ALLPASS')\n"
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "harness.py")
        with open(p, "w") as f:
            f.write(harness)
        try:
            r = subprocess.run([sys.executable, "-I", p], cwd=d, capture_output=True,
                               text=True, timeout=30)
        except subprocess.TimeoutExpired:
            return 0.0, "timeout"
    if r.returncode == 0 and "ALLPASS" in r.stdout:
        return 1.0, "ok"
    err = (r.stderr or "").strip().splitlines()
    return 0.0, (err[-1][:80] if err else "failed")


SCORERS = {"json_schema": score_json_schema,
           "tool_call": score_tool_call,
           "code_repair": score_code_repair}

SCORERS["json_schema_multi"] = score_json_schema_multi
SCORERS["json_schema_strict_multi"] = score_json_schema_strict_multi
SCORERS["tool_call_multi"] = score_tool_call_multi
SCORERS["code_repair_multi"] = score_code_repair_multi


def load_card_v2():
    """Expand each v2 round into one pseudo-task PER ITEM. The round loop then needs no new
    concept: an item is a task with one trial. Rounds are regrouped afterwards."""
    out = []
    for p in sorted(glob.glob(os.path.join(TASKS_DIR, "v2", "*.json"))):
        d = json.load(open(p))
        for it in (d.get("items") or []):
            # THE SCORER GETS THE EXPECTATION, NOT THE ITEM. My first version passed the whole
            # item as the spec, so json_schema_multi compared the model's output against keys
            # named 'id', 'difficulty' and 'expect' -- impossible for any model -- and R1 scored
            # 0/6 for everyone, including a model that swept the v1 card. The pilot caught it;
            # nothing downstream of it would have.
            scorer = d["scorer"]
            if scorer == "json_schema_multi":
                spec = it.get("expect") or {}
            elif scorer == "tool_call_multi":
                spec = {"expect": it.get("expect") or {}}
            else:                       # code_repair_multi reads case fields directly
                spec = {k: v for k, v in it.items()
                        if k in ("cases", "expect_contains", "expect_unchanged",
                                 "harness_prelude")}
            out.append({
                "id": f"{d['id']}::{it['id']}",
                "round_id": d["id"],
                "prompt": it["prompt"],
                "scorer": scorer,
                "kind": d.get("kind", ""),
                # THE NAME GOES, NOT THE STATE ARRIVES. A task that is an INSTRUMENT is measured by a
                # scorer -- no game supplies an oracle -- so the round carries the STAGING and not a
                # game name. `metaphor` is written ONLY for a task that declares a game AND the bundle
                # fields carrying that game's state; otherwise the record would claim a game with
                # nothing behind it, which is the defect GAME_CONTRACT.md exists to catch.
                "class": d.get("class", ""),
                "staged_as": d.get("staged_as", ""),
                "metaphor": d.get("metaphor", "") if d.get("class") == "CONTEST" else "",
                "spec": spec,
                "difficulty": it.get("difficulty", ""),
                "trap": it.get("trap", ""),
                "card_version": 2,
            })
    return out


def load_card_v3():
    """CARD v3. Same item-per-task expansion as v2; R1's scorer is stricter. The difference between
    v2 and v3 R1 is exactly that the schema's FORBIDDEN cases are scored, so the item's conformance
    rules have to travel with its expectation -- in a wrapper, not merged into it."""
    out = []
    for p in sorted(glob.glob(os.path.join(TASKS_DIR, "v3", "*.json"))):
        d = json.load(open(p))
        for it in (d.get("items") or []):
            scorer = d["scorer"]
            if scorer == "json_schema_strict_multi":
                spec = {"expect": it.get("expect") or {},
                        "forbid": it.get("forbid") or [],
                        "forbid_all_other_keys": bool(it.get("forbid_all_other_keys"))}
            elif scorer == "json_schema_multi":
                spec = it.get("expect") or {}
            elif scorer == "tool_call_multi":
                spec = {"expect": it.get("expect") or {}}
            else:
                spec = {k: v for k, v in it.items()
                        if k in ("cases", "expect_contains", "expect_unchanged",
                                 "harness_prelude")}
            out.append({
                "id": f"{d['id']}::{it['id']}",
                "round_id": d["id"],
                "prompt": it["prompt"],
                "scorer": scorer,
                "kind": d.get("kind", ""),
                # THE NAME GOES, NOT THE STATE ARRIVES. A task that is an INSTRUMENT is measured by a
                # scorer -- no game supplies an oracle -- so the round carries the STAGING and not a
                # game name. `metaphor` is written ONLY for a task that declares a game AND the bundle
                # fields carrying that game's state; otherwise the record would claim a game with
                # nothing behind it, which is the defect GAME_CONTRACT.md exists to catch.
                "class": d.get("class", ""),
                "staged_as": d.get("staged_as", ""),
                "metaphor": d.get("metaphor", "") if d.get("class") == "CONTEST" else "",
                "spec": spec,
                "difficulty": it.get("difficulty", ""),
                "trap": it.get("trap", ""),
                "card_version": 3,
            })
    return out


def _strict_first_json(text):
    """Find the FIRST BALANCED JSON object, not the first brace to the last.

    The greedy `\\{.*\\}` this replaces could not see an object inside a model's reasoning, so a model
    that thought first and answered second was scored `unparseable` when it was not. Measured on the v3
    field: 15 items scored unparseable, 14 of their raws contain an object, and on two entrants the
    parser accounted for the ENTIRE score (0.0000 recorded, 0.5833 actual). See FINDING 008.

    Code fences are stripped first -- a fence is presentation, not a parse failure. Then the scan walks
    candidate `{` positions and tracks depth with string and escape awareness, so a brace inside a
    string literal cannot close the object early. Returns (obj, reason); obj is None if nothing parsed.
    """
    if not text:
        return None, "empty response"
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1).strip()
    start = t.find("{")
    last_err = "no json object found"
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(t)):
            ch = t[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(t[start:i + 1]), "ok"
                    except Exception as e:
                        # BREAK, DO NOT RETURN. A reasoning trace can contain a BALANCED but invalid
                        # brace group -- e.g. it quotes the schema back as `{"sku": string}` with
                        # unquoted values. Returning here gave up on the whole response because the
                        # model's first brace was in its prose, which is the same class of failure as
                        # the greedy parser: the extractor decides the verdict instead of the answer.
                        # Try the next candidate opening brace.
                        last_err = f"unparseable: {type(e).__name__}: {e}"
                        break
        start = t.find("{", start + 1)
    return None, last_err


def strict_json_schema_multi(spec, text):
    """CARD v4's R1 scorer: v3's conformance rules with the STRICT extractor.

    v3 scored the same rules through the greedy extractor, which understated models whose answer
    followed their reasoning. The rules are unchanged -- forbidden key, exact key set, null-is-not-
    absent, partial credit on the expectation -- because the RULES were never the defect. Only the
    reading of the model's output changed.
    """
    d, why = _strict_first_json(text)
    if d is None:
        return 0.0, why
    if not isinstance(d, dict):
        return 0.0, "not an object"
    exp = spec.get("expect") or {}
    if not exp:
        return 0.0, "no expectation"
    forbid = set(spec.get("forbid") or [])
    hit = sorted(k for k in forbid if k in d)
    if hit:
        return 0.0, f"emitted forbidden key(s): {hit}"
    if spec.get("forbid_all_other_keys"):
        extra = sorted(set(d) - set(exp))
        if extra:
            return 0.0, f"extra key(s) outside the schema: {extra}"

    def _ok(k):
        if k not in d:
            return False
        if d[k] is None:
            return False          # null is not the value; absent was required
        return _deep_eq(d[k], exp[k])

    got = sum(1 for k in exp if _ok(k))
    nulled = sorted(k for k in exp if k in d and d[k] is None)
    note = f"{got}/{len(exp)} fields"
    if nulled:
        note += f" (null where OMIT was required: {nulled})"
    return got / len(exp), note


SCORERS["strict_json_schema_multi"] = strict_json_schema_multi


def load_card_v4(card_version=4):
    """CARD v4. Same item-per-task expansion as v3; R1 reads the model's output strictly.

    The difference between v3 and v4 R1 is NOT the conformance rules -- it is that a model which
    reasons first and answers second is now scored on its answer. v3's item set is otherwise identical
    in shape; v4's items are rebuilt around the two v3 items that actually discriminated (R1.6
    exact-and-ordered at 39.5%, R1.2 null-is-not-absent at 60.5%), because four of v3's six sat above
    85% and a round with no middle cannot populate the floor. See FINDING 008 and CARD_v4.md.

    `card_version` IS A PARAMETER because v5 measures THESE SAME ITEMS on a different population with
    the clock on. It must be stamped 5, not 4: `already_measured` keys on `card_version`, so a v5 bundle
    stamped 4 would be skipped by its own run -- and the whole purpose of v5 is to re-measure.
    """
    out = []
    for p in sorted(glob.glob(os.path.join(TASKS_DIR, "v4", "*.json"))):
        d = json.load(open(p))
        for it in (d.get("items") or []):
            scorer = d["scorer"]
            spec = {"expect": it.get("expect") or {},
                    "forbid": it.get("forbid") or [],
                    "forbid_all_other_keys": bool(it.get("forbid_all_other_keys"))}
            out.append({
                "id": f"{d['id']}::{it['id']}",
                "round_id": d["id"],
                "prompt": it["prompt"],
                "scorer": scorer,
                "kind": d.get("kind", ""),
                # THE NAME GOES, NOT THE STATE ARRIVES. A task that is an INSTRUMENT is measured by a
                # scorer -- no game supplies an oracle -- so the round carries the STAGING and not a
                # game name. `metaphor` is written ONLY for a task that declares a game AND the bundle
                # fields carrying that game's state; otherwise the record would claim a game with
                # nothing behind it, which is the defect GAME_CONTRACT.md exists to catch.
                "class": d.get("class", ""),
                "staged_as": d.get("staged_as", ""),
                "metaphor": d.get("metaphor", "") if d.get("class") == "CONTEST" else "",
                "spec": spec,
                "difficulty": it.get("difficulty", ""),
                "trap": it.get("trap", ""),
                "card_version": card_version,
            })
    return out


def load_card_v5():
    """CARD v5. THE SAME ITEMS AS v4, deliberately -- only the RUN differs.

    v5 measures v4's items on a population that can load, with the per-item clock on. The card version
    bumps because the run differs (population, gate as a fraction, and a timed item record), NOT because
    the measurement does. Stated here so no reader mistakes a carried item set for a re-chosen one.
    """
    return load_card_v4(card_version=5)


# A raw that is cut says so IN ITS OWN CONTENTS, so a reader can always tell "the model wrote this"
# from "the record stopped here". 20k chars is ~5x the largest legitimate answer seen at
# max_tokens=3000; anything beyond it is a rambler, and the marker preserves that distinction.
RAW_CAP = 20000


def regroup_v2(results, trials_per_item=1):
    """Fold item-level results back into rounds. Round score = mean of its item scores."""
    rounds = {}
    for tid, r in results.items():
        rid = tid.split("::")[0]
        slot = rounds.setdefault(rid, {"score": 0.0, "wins": 0.0, "trials": 0.0,
                                       "kind": r.get("kind", ""), "metaphor": r.get("metaphor", ""),
                                       "items": {}, "finish_reasons": {}, "truncated": False,
                                       "ctx_limited_trials": 0, "max_completion_tokens": 0})
        slot["items"][tid.split("::")[-1]] = dict(score=r.get("score", 0.0),
                                                  reason=r.get("why") or r.get("reason"),
                                                  truncated=r.get("truncated", False),
                                                  # THE CLOCK, PER ITEM -- see the note where these are
                                                  # measured. Without them a slow item and a truncated
                                                  # item land in the record looking the same.
                                                  secs=r.get("secs"),
                                                  gen_tokens=r.get("gen_tokens"),
                                                  serving_failures=r.get("serving_failures"),
                                                  # FINDING 007: the model's own output travels with
                                                  # the item score, so a verdict can be re-derived
                                                  # instead of taken on trust.
                                                  raw=r.get("raw"))
        slot["score"] += r.get("score", 0.0)
        slot["wins"] += r.get("score", 0.0)
        slot["trials"] += 1
        slot["truncated"] = slot["truncated"] or bool(r.get("truncated"))
        slot["ctx_limited_trials"] += r.get("ctx_limited_trials", 0)
        slot["max_completion_tokens"] = max(slot["max_completion_tokens"],
                                            r.get("max_completion_tokens", 0))
        for k, v in (r.get("finish_reasons") or {}).items():
            slot["finish_reasons"][k] = slot["finish_reasons"].get(k, 0) + v
    for rid, slot in rounds.items():
        n = max(slot["trials"], 1)
        slot["score"] = round(slot["score"] / n, 4)
        slot["perfect"] = slot["wins"] == n
    return rounds



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

    srv = LlamaServer(gguf, ctx=args.ctx, ngl=args.ngl, binary=args.llama_server,
                      extra=shlex.split(args.extra_flags) if args.extra_flags else None)
    print(f"  server : {srv.binary}")
    print(f"  flags  : {' '.join(srv.flags)}")
    print("  loading...", end="", flush=True)
    try:
        srv.start(timeout=args.load_timeout)
    except Exception as e:
        srv.stop()
        print(f"\n  *** SCRATCHED AT WEIGH-IN *** {e}")
        tail = srv.server_log_tail()
        if tail:
            print("  --- server's last words ---")
            for line in tail:
                print(f"    {line}")
        print("  A model that does not serve is not scored. Scoring it would publish a lie.")
        if any(("out of memory" in l.lower() or "oom" in l.lower() or "cuda" in l.lower())
               for l in tail):
            print("  Looks like a VRAM problem: free GPU memory (unload other models) and re-weigh.")
        return None
    fp = srv.footprint_gb()
    winfo = srv.weigh_in()
    div = winfo["division_for_competition"]
    print(" ready")
    srv.print_weigh_in()
    print(f"  DIVISION: {div}"
          + ("  (taken from WEIGHTS — this model is partially offloaded, so its resident "
             "footprint is a reading of the machine)" if winfo["partial_offload"] else ""))
    print("  NOTE: resident footprint is baseline-subtracted. Unload other GPU workloads first, "
          "or a concurrent model's eviction will skew the scale. See FINDINGS/002.")

    results, lat, reasons = {}, [], 0
    for t in tasks:
        name = t["id"]
        npass = 0
        why = ""
        finishes, ctoks, truncated = {}, 0, False
        ctx_hits = 0
        serve_failures = 0
        # FINDING 007: THE MODEL'S OWN OUTPUT, PER ITEM.
        #
        # It was discarded at scoring time. The scorer needed only `text`, so the record kept only
        # score/reason/truncated -- which made every verdict these bundles produce UNAUDITABLE: a
        # model failure and a scoring bug became indistinguishable, permanently, and the reason
        # string could never be checked against what the model actually emitted.
        #
        # The rule that fixes it: NO VERDICT MAY DEPEND ON DATA THAT WAS DISCARDED AT SCORING TIME.
        # This is the same rule as the chess replay needing its move list, and the same rule as
        # recording integer counts so a rational is recoverable. One rule, three sites.
        #
        # The cap is MARKED, not silent: a raw that was cut says so in its own contents, because a
        # reader must be able to tell "the model wrote this" from "the record stopped here".
        raws = []
        for i in range(args.trials):
            try:
                r = srv.chat(t["prompt"], args.max_tokens, args.temperature)
            except Exception as e:
                # A SERVING FAILURE IS NOT A CAPABILITY RESULT, AND IT USED TO BE INDISTINGUISHABLE
                # FROM ONE.
                #
                # This used to `continue` -- which discarded the raw slot AND left `why` at its
                # initial "". The item then recorded score 0.0 with no reason and no raw, and the
                # guard below (`if npass == 0 and why`) skipped, so no reason key was written at all.
                # `Cloudflare_clef :: R1.5` in the v3 field is exactly that triple, with nothing left
                # to examine -- the FINDING 007 hole, one level down.
                #
                # Same class as the 26 zero-byte bundles: a machine failure reported as a model's
                # result. The class now travels in the record.
                kind = type(e).__name__
                print(f"    {name} t{i+1}: ERR {kind}", flush=True)
                raws.append(f"[SERVING FAILURE: {kind} -- the request never completed]")
                if not why:
                    why = f"SERVING FAILURE: {kind} (request raised; not a capability result)"
                serve_failures += 1
                continue
            srv.sample_vram()
            lat.append(r["secs"])
            reasons += 1 if r["from_reasoning"] else 0
            finishes[r.get("finish") or "?"] = finishes.get(r.get("finish") or "?", 0) + 1
            ctoks = max(ctoks, r.get("ctok") or 0)
            total = (r.get("ptok") or 0) + (r.get("ctok") or 0)
            # WHICH limit bit? Confusing these two produces wrong advice.
            if r.get("finish") == "length" or total >= args.ctx:
                truncated = True
                if total >= args.ctx:
                    ctx_hits += 1
            _raw = r["text"] or ""
            raws.append(_raw if len(_raw) <= RAW_CAP
                        else _raw[:RAW_CAP] + f"\n[...TRUNCATED AT {RAW_CAP} CHARS]")
            ok, reason = SCORERS[t["scorer"]](t["spec"], r["text"])
            npass += 1 if ok else 0
            if not ok:
                why = reason
            print(f"    {name:16s} t{i+1}: {'PASS' if ok else 'fail'} ({r['secs']:5.1f}s)"
                  + ("" if ok else f"  [{reason}]"), flush=True)
        results[name] = dict(score=npass / args.trials, wins=npass, trials=args.trials,
                             kind=t.get("kind", ""), metaphor=t.get("metaphor", ""),
                             finish_reasons=finishes, max_completion_tokens=ctoks,
                             truncated=truncated, ctx_limited_trials=ctx_hits,
                             serving_failures=serve_failures,
                             # THE CLOCK, PER ITEM. Same finding as the chess event's: a reader must be
                             # able to tell "this item took 8 minutes because the model was reasoning"
                             # from "this item took 8 minutes because it ran to the cap." `truncated`
                             # answers whether it was CUT OFF; only the elapsed time and the token count
                             # answer HOW HARD IT WORKED. The runner measured both and wrote elapsed
                             # seconds to its LOG -- and a log is discarded relative to the artifact.
                             secs=round(sum(lat) / len(lat), 1) if lat else None,
                             gen_tokens=ctoks,
                             # one entry per trial; v2/v3 run one trial per item
                             raw=raws)
        # `if npass == 0:` and NOT `if npass == 0 and why:`. With `and why`, a falsy reason skipped
        # the block entirely and the item shipped with no reason at all -- a zero that cannot be
        # explained is worse than a wrong answer, because it cannot even be argued with.
        if npass == 0:
            # Distinguish four different things: a wrong answer, a cut-off answer, and WHICH cut-off.
            if truncated and ctx_hits:
                results[name]["why"] = (f"CONTEXT LIMIT hit ({args.ctx} tokens) before answering — "
                                        f"not a capability result; raise --ctx")
            elif truncated:
                results[name]["why"] = (f"TRUNCATED at max_tokens ({args.max_tokens}) before "
                                        f"answering — not a capability result; raise --max-tokens")
            else:
                results[name]["why"] = why or "(no reason reported by the scorer)"
    srv.stop()

    # CARD VERSION. A v2 score and a v1 score are different measurements and must never be
    # ranked together. Same rule as server_flags: if it changes the outcome, it belongs in the
    # record. v2 item results are folded back into rounds here.
    card_version = tasks[0].get("card_version", 1) if tasks else 1
    if card_version >= 2:
        # v2 and v3 both run ONE TRIAL PER ITEM: the items are the source of variation, not
        # sampling. At temperature 0, repeated trials of one prompt are copies of a measurement.
        results = regroup_v2(results)

    agg = sum(v["score"] for v in results.values()) / max(len(results), 1)
    # BELT RULE 2 FOR v2 ONLY. v1's belts are historical measurements; re-deriving them under a
    # new rule would silently rewrite what was measured. Rule 2 applies to the card it was
    # designed for.
    grade = bout_grade(results, args.trials, aggregate=agg,
                       belt_rule=2 if card_version >= 2 else 1)
    return dict(gguf=gguf, sha256=digest, footprint_gb=fp, division=div, weigh_in=winfo,
                cord=CORDS.get(div, "slate"),
                config=dict(temperature=args.temperature, max_tokens=args.max_tokens,
                            trials=args.trials, ctx=args.ctx, n_gpu_layers=args.ngl,
                            server_flags=srv.flags),
                rounds=results, aggregate=agg, grade=grade,
                card_version=card_version,
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


def biathlon(paths, k):
    """BIATHLON: accuracy x throughput, where every miss costs a penalty loop.

    The commercial event. Real biathlon ranks on total time INCLUDING penalties, which is exactly
    the local-inference trade: a fast model that is sometimes wrong against a slow model that is
    usually right. The penalty coefficient k is the declared cost of being wrong, for ONE trial
    (in units of that round's mean latency). Different applications have different k; the arena
    turns that argument into a number.

    total = (mean_latency x trials) + (misses x k x mean_latency)
    """
    rows = []
    for p in paths:
        with open(p) as f:
            b = json.load(f)
        for r in b.get("results", []):
            rounds = r.get("rounds", {})
            if any("wins" not in v for v in rounds.values()):
                print(f"  !! {os.path.basename(p)} predates per-round win counts — cannot score")
                continue
            trials = sum(v.get("trials", 0) for v in rounds.values())
            hits = sum(v.get("wins", 0) for v in rounds.values())
            misses = trials - hits
            lat = r.get("mean_latency") or 0.0
            ski = lat * trials
            pen = misses * k * lat
            # Disambiguate the serving configuration IN THE NAME. Two entrants with identical
            # names and different configs is exactly how a wrong leaderboard gets published.
            flags = (r.get("config") or {}).get("server_flags") or []
            tags = []
            if any("grammar" in str(f).lower() for f in flags):
                tags.append("GRAMMAR")
            if any(str(f).lower().startswith("--template") for f in flags):
                tags.append("TEMPLATE")
            if not tags:
                tags.append("neutral")
            mt = (r.get("config") or {}).get("max_tokens")
            if mt:
                tags.append(f"mt{mt}")
            rows.append(dict(name=os.path.basename(r["gguf"]), tag=" ".join(tags),
                             divisions=r["division"],
                             fp=r.get("footprint_gb"), hits=hits, trials=trials, misses=misses,
                             lat=lat, ski=ski, pen=pen, total=ski + pen,
                             belt=(r.get("grade") or {}).get("belt", "?")))
    if not rows:
        print("  no gradeable bundles")
        return
    print(f"\n{'='*96}")
    print(f"BIATHLON  (penalty k={k} — each miss costs {k}x the round's mean latency)")
    print(f"{'-'*96}")
    print(f"{'rank':>4s} {'entrant':30s} {'serving':16s} {'div':13s} {'footprint':>10s} "
          f"{'hits':>6s} {'miss':>5s} {'lat':>7s} {'ski':>9s} {'penalty':>9s} {'TOTAL':>10s}")
    for i, r in enumerate(sorted(rows, key=lambda x: x["total"]), 1):
        fps = f"{r['fp']:.2f}GB" if r["fp"] is not None else "?"
        print(f"{i:>4d} {r['name'][:30]:30s} {r['tag'][:16]:16s} {r['divisions']:13s} {fps:>10s} "
              f"{r['hits']:>3d}/{r['trials']:<2d} {r['misses']:>5d} {r['lat']:6.2f}s "
              f"{r['ski']:8.2f}s {r['pen']:8.2f}s {r['total']:9.2f}s")
    print(f"{'-'*96}")
    best = min(rows, key=lambda x: x["total"])
    acc = max(rows, key=lambda x: x["hits"])
    print(f"  biathlon winner (lowest total) : {best['name']}")
    if acc["name"] != best["name"]:
        print(f"  most accurate                  : {acc['name']}  "
              f"({acc['hits']}/{acc['trials']} vs {best['hits']}/{best['trials']})")
        print(f"  -> accuracy and value DISAGREE here. That is the entire reason this event exists.")
    print(f"  raise k to weight correctness, lower it to weight speed. The winner can flip.")


def run_relay(paths, args, tasks):
    """THE RELAY — does chaining models beat a single model?

    THREE CONDITIONS PER TASK, because a relay score on its own is meaningless:
      * ROUTER ALONE  -- is the planner any good? (usually not; that is expected)
      * WORKER ALONE  -- THE CONTROL. Without it, "the relay scored 0.67" says nothing.
      * RELAY         -- the router's plan handed to the worker VERBATIM, then scored.

    LEGS RUN IN SEQUENCE, NOT IN PARALLEL. The plan is text, so both models never need to be
    resident at once. This matters twice over:
      * PEAK VRAM = max(member), not sum(member). A 350M+2B relay fits an 8 GB card even when a
        cached model already occupies most of it. The first version of this function tried to hold
        both resident and died on VRAM.
      * COMPETITIVE DIVISION IS STILL THE SUM. Peak memory is what your machine must survive;
        division is what the team is worth. Those are different numbers and conflating them would
        let a relay smuggle size.

    A DROPPED BATON IS A DNF. An empty plan means the relay scores zero. Passing garbage downstream
    is a failure, not a recovery — and a plan that MISLEADS the worker is the most interesting thing
    this event can reveal.
    """
    router_p, worker_p = paths[0], paths[-1]

    def load(path, role):
        s = LlamaServer(path, ctx=args.ctx, ngl=args.ngl, binary=args.llama_server,
                        extra=shlex.split(args.extra_flags) if args.extra_flags else None)
        print(f"\nWEIGH-IN [{role}] {os.path.basename(path)}", flush=True)
        try:
            s.start(timeout=args.load_timeout)
        except Exception as e:
            # SCRATCH, never crash. Same rule as the single-bout path: a model that cannot serve is
            # not scored, and the reason is printed rather than thrown.
            print(f"  *** SCRATCHED AT WEIGH-IN *** {e}")
            for line in s.server_log_tail():
                print(f"    {line}")
            print("  A model that does not serve is not scored. Scoring it would publish a lie.")
            s.stop()
            return None
        s.print_weigh_in()
        return s

    print("=" * 108)
    print(f"RELAY — {len(paths)} legs, {len(tasks)} rounds, {args.trials} trials, ctx {args.ctx}")
    print("  legs run in SEQUENCE: peak VRAM is the largest member, division is the SUM")
    print("=" * 108)

    plans, router_scores, worker_scores, relay_scores, dnfs = {}, {}, {}, {}, {}
    trunc = {}
    router_fp = worker_fp = None

    # ---- PHASE 1 — the router, alone ----
    R = load(router_p, "router")
    if R:
        router_fp = R.footprint_gb()
        for t in tasks:
            passes, plist = [], []
            for _ in range(args.trials):
                try:
                    a = R.chat(t["prompt"], min(300, args.max_tokens), args.temperature)
                    passes.append(SCORERS[t["scorer"]](t["spec"], a["text"])[0])
                except Exception:
                    passes.append(False)
                try:
                    plist.append(R.chat(
                        "You are a planner. Read the task below and write a brief plan, at most 120 "
                        "words, for how to answer it correctly. Output ONLY the plan, no preamble, "
                        "and do not answer the task itself.\n\nTASK:\n" + t["prompt"],
                        300, args.temperature)["text"])
                except Exception:
                    plist.append("")
            router_scores[t["id"]] = sum(passes) / args.trials
            plans[t["id"]] = plist
            print(f"    [router] {t['id']:16s} {sum(passes)}/{args.trials}  "
                  f"(plans captured: {sum(1 for p in plist if p.strip())}/{args.trials})", flush=True)
        R.stop()

    # ---- PHASE 2 — the worker, alone and then with the plans ----
    W = load(worker_p, "worker")
    if W:
        worker_fp = W.footprint_gb()
        for t in tasks:
            w_ok = rel_ok = 0
            dnf = 0
            trunc_here = 0
            for i in range(args.trials):
                try:
                    b = W.chat(t["prompt"], args.max_tokens, args.temperature)
                    # A truncated answer is a MEASUREMENT FAILURE, not a capability result. The
                    # single-bout path reports this; the relay must too, or a 0.00 here is
                    # indistinguishable from a model that was cut off mid-thought.
                    if (b.get("finish") == "length"
                            or (int(b.get("ptok") or 0) + int(b.get("ctok") or 0)) >= args.ctx):
                        trunc_here += 1
                    w_ok += 1 if SCORERS[t["scorer"]](t["spec"], b["text"])[0] else 0
                except Exception:
                    pass
                plan = (plans.get(t["id"]) or [""] * args.trials)[i] if R else ""
                if not plan or not plan.strip():
                    dnf += 1                      # dropped baton
                    continue
                relay_prompt = (t["prompt"] + "\n\n---\nA planning model reviewed this task and "
                                "suggested the following approach. Use it if it helps. The output "
                                "format requirements above still apply.\nPLAN:\n" + plan.strip())
                try:
                    c = W.chat(relay_prompt, args.max_tokens, args.temperature)
                    if (c.get("finish") == "length"
                            or (int(c.get("ptok") or 0) + int(c.get("ctok") or 0)) >= args.ctx):
                        trunc_here += 1
                    rel_ok += 1 if SCORERS[t["scorer"]](t["spec"], c["text"])[0] else 0
                except Exception:
                    pass
            worker_scores[t["id"]] = w_ok / args.trials
            relay_scores[t["id"]] = rel_ok / args.trials
            dnfs[t["id"]] = dnf
            trunc[t["id"]] = trunc_here
            flag = ""
            if trunc_here:
                flag = f"   TRUNCATED {trunc_here} (not a capability result — raise --ctx/--max-tokens)"
            print(f"    [worker] {t['id']:16s} alone {w_ok}/{args.trials}   "
                  f"RELAY {rel_ok}/{args.trials}" + (f"   DNF {dnf}" if dnf else "") + flag,
                  flush=True)
        W.stop()

    if not worker_scores:
        print("\n  The worker could not be weighed in — no relay can be run. Nothing was scored.")
        return

    sum_fp = (router_fp or 0) + (worker_fp or 0)
    peak_fp = max(router_fp or 0, worker_fp or 0)
    print(f"\n{'='*108}")
    print(f"{'round':16s} {'router':>8s} {'WORKER(control)':>16s} {'RELAY':>8s} {'delta':>9s}  verdict")
    print("-" * 108)
    tw = tr = 0.0
    for t in tasks:
        n = t["id"]
        w = worker_scores.get(n, 0.0)
        r = relay_scores.get(n, 0.0)
        rs = router_scores.get(n, 0.0)
        tw += w
        tr += r
        d = r - w
        verdict = ("relay HELPS" if d > 0.01 else "relay HURTS" if d < -0.01 else "no effect")
        if dnfs.get(n):
            verdict += f" ({dnfs[n]} DNF)"
        print(f"{n:16s} {rs:8.2f} {w:16.2f} {r:8.2f} {d:+9.2f}  {verdict}")
    k = len(tasks) or 1
    print("-" * 108)
    print(f"{'MEAN':16s} {'':8s} {tw/k:16.2f} {tr/k:8.2f} {(tr-tw)/k:+9.2f}")
    print(f"\n  worker alone {tw/k:.2f}   relay {tr/k:.2f}")
    print(f"  DIVISION footprint (sum of members) {sum_fp:.2f} GB -> {division_for(sum_fp)}")
    print(f"  PEAK footprint (legs serialised)    {peak_fp:.2f} GB -> {division_for(peak_fp)}")
    print("  A relay that merely matches the worker has added a model and gained nothing.")
    print("  A relay that beats the worker has to justify a larger DIVISION footprint even though "
          "its PEAK fits in the worker's class.")


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
    ap.add_argument("--ngl", type=int, default=None,
                    help="layers to offload to GPU. OMIT IT (the default) to let llama.cpp auto-fit "
                         "the layer count to free VRAM -- which is what you want on a GPU that is "
                         "shared with other models. Setting it explicitly makes an over-large "
                         "placement ABORT rather than fall back.")
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=1200, dest="max_tokens")
    ap.add_argument("--load-timeout", type=int, default=600, dest="load_timeout")
    ap.add_argument("--llama-server", dest="llama_server")
    ap.add_argument("--extra-flags", dest="extra_flags", default=None,
                    help="extra llama-server flags, shell-split — e.g. "
                         "'--grammar-file x.gbnf --flash-attn'. Use this to reproduce the "
                         "serving-configuration experiment in FINDINGS/001.")
    ap.add_argument("--card", default="v1", choices=["v1", "v2", "v3", "v4", "v5"],
                    help="which card to run. v1 = 3 rounds x 3 trials of one prompt (retired). "
                         "v2 = 3 rounds x 6 distinct items, one trial each. Scores from "
                         "different cards are different measurements and are never mixed.")
    ap.add_argument("--out", help="write result bundle JSON here")
    ap.add_argument("--grade", metavar="BUNDLE.json",
                    help="re-derive belts from a stored result bundle (belts are computed, never assigned)")
    ap.add_argument("--biathlon", nargs="+", metavar="BUNDLE.json",
                    help="rank stored bundles as a biathlon: accuracy x throughput, misses cost time")
    ap.add_argument("--relay", metavar="MODEL_A,MODEL_B[,MODEL_C]",
                    help="THE RELAY: leg 1 plans, the last leg answers. Reports worker-alone as "
                         "the control, because a relay score without a control means nothing.")
    ap.add_argument("--penalty-k", type=float, default=1.0, dest="penalty_k",
                    help="cost of one miss in units of that round's mean latency (default 1.0)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    LlamaServer.install_guards()

    if args.relay:
        legs = [os.path.expanduser(p.strip()) for p in args.relay.split(",") if p.strip()]
        missing = [p for p in legs if not os.path.exists(p)]
        if missing:
            sys.exit("model file not found: " + ", ".join(missing))
        if len(legs) < 2:
            sys.exit("--relay needs at least two models: ROUTER,WORKER")
        run_relay(legs, args, load_tasks())
        return

    if args.biathlon:
        biathlon(args.biathlon, args.penalty_k)
        return

    if args.grade:
        grade_only(args.grade)
        return

    if args.self_test:
        print("HANDICAP ARENA self-test — validating the scorers before any score is trusted\n")
        sys.exit(0 if self_test() else 1)

    tasks = load_tasks(args.card)
    if not tasks:
        sys.exit(f"No task definitions found in {TASKS_DIR}")
    if args.card in ("v2", "v3"):
        # ONE TRIAL PER ITEM. In v2 the items are the source of variation, not sampling --
        # at temperature 0 repeated trials of the same prompt are copies of one measurement.
        args.trials = 1

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
        outdir = os.path.dirname(os.path.abspath(args.out))
        os.makedirs(outdir, exist_ok=True)
        # ATOMIC PROMOTION. The first version wrote straight to the final path, so a kill
        # mid-write -- hard freeze, reboot, OOM -- could leave truncated JSON sitting under a
        # name that says "this is a result". The 2026-10-07 hard reboot happened to hit BETWEEN
        # writes and nothing was lost: that was luck, not design. All 56 bundles parsed cleanly
        # afterwards, which tells you the write window was missed, not that it was small.
        # The logger has done tmp+fsync+rename since the beginning (see LOGGER.md). Now so does
        # the arena. A .part left behind is the signature of a killed write, and the survey
        # script looks for them.
        payload = dict(harness="handicap-arena", version="1.0",
                       generated=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       results=out)
        tmp = args.out + ".part"
        with open(tmp, "w") as f:
            json.dump(payload, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, args.out)     # atomic on POSIX: the old file or the new one, never half
        print(f"\nresult bundle -> {args.out}")
        print("Submit it. If it places, we re-run it on our rig from its sha256. "
              "Reproduce and it is CERTIFIED; fail and it is STRUCK.")


if __name__ == "__main__":
    main()
