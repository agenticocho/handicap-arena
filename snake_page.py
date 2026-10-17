#!/usr/bin/env python3
"""SNAKE -- the STEPPED wrapper. Holds the game's tick, takes exactly one move per turn.

WHY A STEPPED WRAPPER EXISTS AT ALL (card t_401ee1d7): `snake.html` runs a `requestAnimationFrame`
loop throttled to 15 fps. A reasoning model cannot feed a live 15 fps game -- the answer arrives after a
`Thinking Process:` preamble, measured at 2,314 tokens in a sibling cabinet. So the tick is HELD and the
episode is scored one move at a time.

WHAT THIS FILE IS: the seam between the entrant and THE GAME ITSELF.
  * the game is not re-implemented here. `snake/snake.html` is loaded into a real browser and PLAYED.
  * the tick is held by replacing `requestAnimationFrame` with a recorder, so the game's own `loop()`
    only runs when we call it. THE GAME'S OWN CODE DECIDES WHAT A TICK IS -- `step()` calls `loop()`
    until the game's own throttle counter (`window.count`, which the game's own `loop()` resets) comes
    back to 0. The tick length is read from the game, never assumed to be 4.
  * the apple spawn is made deterministic by replacing `Math.random` with a seeded PRNG before the page's
    script runs. The game's own `getRandomInt` is the only consumer, and the call site is untouched.
  * a move is DISPATCHED AS A `keydown` EVENT, so it enters the game through the game's real input
    handler -- including the handler's own no-backtrack rule (`snake.dx === 0`). The wrapper does not
    write `snake.dx` directly; it reads back whether the game accepted or refused the move.
  * state is READ, not scraped from pixels. `snake`, `apple`, `grid`, `canvas` and `count` are top-level
    `var`s in the page, so the live game state is directly readable. The vision projector is the
    documented FALLBACK if JS injection were blocked; it is not the path taken here.

THE INSTRUMENT IS RECORDED WITH THE NUMBER: chrome binary path + digest + version, the subject html's
digest, the injected harness source digest, and -- because a claim with no carrier is unverified -- the
digest of the page's OWN inline game script read back from the live DOM. If the harness had patched the
game's code, that digest would differ from the file's; `instrument()` is what makes "we did not modify
the game" checkable rather than asserted.

NO THIRD-PARTY DEPENDENCY: the CDP client below is a minimal websocket + JSON-RPC implementation on the
stdlib. MEASURED REASON: `/usr/bin/python3` on this box has no `websockets` and no `playwright`, and the
only python that has them is a Hermes-internal venv -- a driver that only runs under another project's
interpreter is a driver that stops running when that project moves.

    p = SnakePage(); p.start(); p.new_episode(seed=1); s = p.step("D"); ...; p.stop()
"""
import base64
import hashlib
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

# THE BROWSER IS PART OF THE INSTRUMENT. Default: the Chrome for Testing build already on this box
# (playwright's downloaded chromium-1234). A different browser is a different instrument, so it is
# selectable and its identity travels in the record -- the same discipline as the llama-server binary.
CHROME_CANDIDATES = (
    "~/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome",
    "~/.cache/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
)


def find_chrome():
    for c in CHROME_CANDIDATES:
        p = os.path.expanduser(c)
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
    return None


def file_digest(path, n=16):
    """sha256 of a FILE, first n hex. UNREADABLE -> None and a reason, never a fabricated digest:
    a made-up hash is worse than a missing one because it verifies."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()[:n]


def sha16(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


# ==================================================================================================
# THE INJECTED HARNESS -- the whole of what the wrapper does to the page, in one readable string.
#
# IT IS PART OF THE INSTRUMENT, so its digest travels in every record. Two things are installed and
# neither one touches a rule of the game:
#   (1) `requestAnimationFrame` records its callback instead of scheduling it  -> the tick is HELD;
#   (2) `Math.random` becomes a seeded PRNG                                    -> the run is REPLAYABLE.
# Everything else is a read (state) or a dispatch into the game's own keydown handler (move).
# ==================================================================================================
INIT_JS = r"""
(function () {
  var SEED = __SEED__;
  // ---- (2) the seeded PRNG. mulberry32: 2^32 period, one uint32 of state, named in the record.
  var rng_state = SEED >>> 0;
  function rnd() {
    rng_state = (rng_state + 0x6D2B79F5) | 0;
    var t = Math.imul(rng_state ^ (rng_state >>> 15), 1 | rng_state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  var rng_calls = 0;
  Math.random = function () { rng_calls += 1; return rnd(); };
  // ---- (1) HOLD THE TICK. The game's own loop re-registers itself each call; the stub just keeps it.
  var pending = null;
  window.requestAnimationFrame = function (cb) { pending = cb; return 1; };
  window.cancelAnimationFrame = function () { pending = null; };

  var T = 0;                    // ticks TAKEN, counted by us
  var tick_calls = 0;           // loop() calls spent, counted by us, reported per step

  function cells() {
    var out = [];
    for (var i = 0; i < snake.cells.length; i++) out.push([snake.cells[i].x, snake.cells[i].y]);
    return out;
  }

  function state() {
    return {tick: T, grid: grid, canvas: [canvas.width, canvas.height],
            head: [snake.x, snake.y], dir: [snake.dx, snake.dy],
            cells: cells(), length: snake.cells.length, maxCells: snake.maxCells,
            apple: [apple.x, apple.y], count: window.count, rng_calls: rng_calls};
  }

  var KEYS = {U: 38, D: 40, L: 37, R: 39};

  window.__SNAKE__ = {
    seed: SEED, held: true,
    version: 1,
    state: state,
    // ONE TICK. Bound by the GAME'S OWN counter: `loop()` is called until `window.count` returns to 0.
    // With the throttle the file ships, that is 4 calls; if the file's throttle changed, this still
    // stops on the game's tick boundary rather than on a number written here.
    step: function (dir) {
      if (dir) {
        var k = KEYS[dir];
        if (!k) throw new Error('not a control: ' + dir);
        var ev = new KeyboardEvent('keydown', {keyCode: k, which: k, bubbles: true});
        document.dispatchEvent(ev);
      }
      if (!pending) throw new Error('no frame callback registered by the game');
      var calls = 0;
      do {
        pending();
        calls += 1;
        if (calls > 64) throw new Error('tick never advanced: window.count=' + window.count);
      } while (window.count !== 0);
      T += 1;
      tick_calls += calls;
      return {tick_calls: calls, state: state()};
    },
    tick_calls: function () { return tick_calls; },
    // THE GAME'S OWN CODE, read back from the live page. The instrument claims the game was not
    // modified; this is the value that makes the claim checkable.
    game_source: function () {
      var s = document.querySelectorAll('script');
      return s.length ? s[0].textContent : null;
    }
  };
})();
"""


class WSError(RuntimeError):
    pass


class WebSocketText:
    """A minimal RFC6455 text client. GET/Upgrade handshake, masked client frames, ping->pong,
    fragmentation reassembled. Deliberately small: the only peer is a local DevTools endpoint."""

    def __init__(self, url, timeout=30.0):
        if not url.startswith("ws://"):
            raise WSError("only ws:// is supported, got %r" % url)
        rest = url[5:]
        hostport, _, path = rest.partition("/")
        host, _, port = hostport.partition(":")
        self.sock = socket.create_connection((host, int(port or 80)), timeout=timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        req = ("GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
               "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % (path, hostport, key))
        self.sock.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise WSError("handshake closed by peer")
            buf += chunk
        head, _, rest = buf.partition(b"\r\n\r\n")
        if b"101" not in head.split(b"\r\n")[0]:
            raise WSError("handshake refused: %r" % head[:200])
        self.buf = rest

    def _exact(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise WSError("connection closed by peer")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def send(self, text):
        payload = text.encode()
        mask = os.urandom(4)
        n = len(payload)
        if n < 126:
            header = struct.pack("!BB", 0x81, 0x80 | n)
        elif n < 65536:
            header = struct.pack("!BBH", 0x81, 0x80 | 126, n)
        else:
            header = struct.pack("!BBQ", 0x81, 0x80 | 127, n)
        self.sock.sendall(header + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def recv(self):
        parts = []
        while True:
            b0, b1 = self._exact(2)
            fin, op = b0 & 0x80, b0 & 0x0F
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack("!H", self._exact(2))[0]
            elif n == 127:
                n = struct.unpack("!Q", self._exact(8))[0]
            payload = self._exact(n)
            if op == 0x9:                                   # ping -> pong, same payload
                mask = os.urandom(4)
                body = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
                self.sock.sendall(struct.pack("!BB", 0x8A, 0x80 | len(payload)) + mask + body)
                continue
            if op == 0xA:                                   # pong
                continue
            if op == 0x8:
                raise WSError("peer closed the websocket (opcode 8)")
            parts.append(payload)
            if fin:
                return b"".join(parts).decode("utf-8", "replace")

    def close(self):
        try:
            self.sock.close()
        except Exception:                                   # noqa: BLE001
            pass


class CDP:
    """JSON-RPC over one websocket. Events are counted and dropped -- this driver reads state by
    REQUEST, so an event stream it never waits on cannot make a step look like it happened."""

    def __init__(self, ws):
        self.ws = ws
        self._id = 0
        self.session = None
        self.events = 0

    def call(self, method, **params):
        self._id += 1
        msg = {"id": self._id, "method": method, "params": params}
        if self.session:
            msg["sessionId"] = self.session
        self.ws.send(json.dumps(msg))
        while True:
            data = json.loads(self.ws.recv())
            if data.get("id") == self._id:
                if "error" in data:
                    raise WSError("%s -> %s" % (method, json.dumps(data["error"])[:400]))
                return data.get("result", {})
            self.events += 1

    def evaluate(self, expression, await_promise=False):
        r = self.call("Runtime.evaluate", expression=expression, returnByValue=True,
                      awaitPromise=await_promise)
        if r.get("exceptionDetails"):
            d = r["exceptionDetails"]
            raise WSError("evaluate: %s" % json.dumps(d.get("exception") or d)[:500])
        return r["result"].get("value")


class SnakePage:
    """A LIVE `snake.html`, held at the tick, stepped by us."""

    def __init__(self, html=None, chrome=None, headless=True, verbose=False):
        self.html = os.path.abspath(html or os.path.join(HERE, "snake", "snake.html"))
        self.chrome = chrome or find_chrome()
        self.headless = headless
        self.verbose = verbose
        self.proc = None
        self.udir = None
        self.cdp = None
        self.seed = None
        self.harness_source = None
        self.launch = []
        self.version_string = None

    # ---- process -------------------------------------------------------------------------------

    def start(self, timeout=45.0):
        if not self.chrome or not os.path.exists(self.chrome):
            raise RuntimeError("no chrome binary found (looked at %s)" % (CHROME_CANDIDATES,))
        if not os.path.exists(self.html):
            raise RuntimeError("subject html absent: %s" % self.html)
        self.udir = tempfile.mkdtemp(prefix="snake-chrome-")
        flags = ["--no-sandbox", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                 "--disable-background-networking", "--disable-sync", "--disable-gpu",
                 "--allow-file-access-from-files", "--mute-audio",
                 "--remote-debugging-port=0", "--user-data-dir=" + self.udir]
        if self.headless:
            flags = ["--headless=new"] + flags
        self.launch = [self.chrome] + flags + ["about:blank"]
        self.proc = subprocess.Popen(self.launch, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        port_file = os.path.join(self.udir, "DevToolsActivePort")
        t0 = time.time()
        port = None
        while time.time() - t0 < timeout:
            if os.path.exists(port_file):
                with open(port_file) as f:
                    lines = f.read().splitlines()
                if lines and lines[0].strip().isdigit():
                    port = int(lines[0].strip())
                    break
            if self.proc.poll() is not None:
                err = (self.proc.stderr.read() or b"").decode("utf-8", "replace")
                raise RuntimeError("chrome exited rc=%s: %s" % (self.proc.returncode, err[-800:]))
            time.sleep(0.2)
        if port is None:
            raise RuntimeError("chrome never published DevToolsActivePort in %.0fs" % timeout)
        self.port = port
        try:
            self.version_string = subprocess.run([self.chrome, "--version"], capture_output=True,
                                                 text=True, timeout=30).stdout.strip() or None
        except Exception:                                   # noqa: BLE001
            self.version_string = None
        info = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port,
                                                 timeout=10).read())
        ws = WebSocketText(info["webSocketDebuggerUrl"])
        self.cdp = CDP(ws)
        t = self.cdp.call("Target.createTarget", url="about:blank")["targetId"]
        att = self.cdp.call("Target.attachToTarget", targetId=t, flatten=True)
        self.cdp.session = att["sessionId"]
        self.cdp.call("Page.enable")
        self.cdp.call("Runtime.enable")
        return self

    def stop(self):
        try:
            if self.cdp:
                try:
                    self.cdp.call("Browser.close")
                except Exception:                           # noqa: BLE001
                    pass
                self.cdp.ws.close()
        finally:
            self.cdp = None
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=15)
                except Exception:                           # noqa: BLE001
                    self.proc.kill()
            if self.udir:
                shutil.rmtree(self.udir, ignore_errors=True)

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()

    # ---- episodes ------------------------------------------------------------------------------

    def new_episode(self, seed):
        """A FRESH LOAD with the seed installed BEFORE the game's own script runs, so the apple
        sequence is a function of (seed, moves) alone. Returns the state at tick 0."""
        self.seed = int(seed)
        src = INIT_JS.replace("__SEED__", str(self.seed))
        self.harness_source = src
        # THE INIT SCRIPT IS SCOPED TO THE NEXT DOCUMENT, so an episode cannot inherit the last one's
        # held tick or consumed RNG calls -- that would be a silent cross-episode leak.
        self.script_id = self.cdp.call("Page.addScriptToEvaluateOnNewDocument", source=src)["identifier"]
        self.cdp.call("Page.navigate", url="file://" + self.html)
        t0 = time.time()
        while time.time() - t0 < 30:
            try:
                if self.cdp.evaluate("!!(window.__SNAKE__ && window.snake && window.apple)"):
                    break
            except WSError:
                pass
            time.sleep(0.05)
        else:
            raise RuntimeError("the game never came up in %s" % self.html)
        self.cdp.evaluate("1")                              # settle
        # the game must be HELD before the first move: if a tick already ran, the run is not ours
        st = self.state()
        if st["tick"] != 0 or st["cells"]:
            raise RuntimeError("the game advanced before the harness held it: %r" % (st,))
        r = self.cdp.call("Page.removeScriptToEvaluateOnNewDocument", identifier=self.script_id)
        return st

    def state(self):
        return self.cdp.evaluate("window.__SNAKE__.state()")

    def step(self, direction=None):
        """ONE MOVE, ONE TICK. `direction` is U/D/L/R or None (hold still: the game keeps its own
        velocity). Returns {"tick_calls", "state"}."""
        arg = "null" if direction is None else json.dumps(direction)
        return self.cdp.evaluate("window.__SNAKE__.step(%s)" % arg)

    def game_source(self):
        return self.cdp.evaluate("window.__SNAKE__.game_source()")

    # ---- the instrument ------------------------------------------------------------------------

    def instrument(self):
        """THE WRAPPER, DESCRIBED WITH THE NUMBER. Every value here is read at run time; none is typed
        from a card. `game_source_digest` is the live page's own script read back out of the DOM, and
        `subject_source_digest` is the same script on disk: the two are equal exactly when the harness
        did not modify the game, which is what makes the claim checkable instead of asserted."""
        disk = None
        try:
            with open(self.html, encoding="utf-8") as f:
                text = f.read()
            body = text.split("<script>", 1)[1].rsplit("</script>", 1)[0]
            disk = sha16(body)
        except Exception:                                   # noqa: BLE001
            disk = None
        live = self.game_source()
        return {
            "kind": "stepped-browser-wrapper",
            "wrapper": {"file": os.path.relpath(os.path.abspath(__file__), HERE),
                        "harness_source_digest": sha16(self.harness_source or ""),
                        "harness_installs": ["requestAnimationFrame -> recorder (THE TICK IS HELD)",
                                             "Math.random -> mulberry32(seed) (THE RUN REPLAYS)",
                                             "window.__SNAKE__ = {state, step, game_source}"],
                        "tick_definition": ("step() calls the game's own loop() until the game's own "
                                            "throttle counter `window.count` returns to 0 -- the tick "
                                            "length is READ FROM THE GAME, not assumed"),
                        "input_path": ("a move is a dispatched `keydown` (keyCode/which 37..40), so it "
                                       "passes through the game's own handler and its no-backtrack rule"),
                        "state_path": ("read from the live page's top-level vars (snake, apple, grid, "
                                       "canvas, count); NOT scraped from pixels"),
                        "rng": {"algorithm": "mulberry32", "period": 2 ** 32, "seed": self.seed,
                                "call_site": "Math.random, whose only consumer in the page is getRandomInt"}},
            "browser": {"binary": self.chrome, "binary_digest": file_digest(self.chrome),
                        "version": self.version_string, "headless": self.headless,
                        "launch_flags": [f for f in self.launch[1:] if not f.startswith("--user-data-dir")],
                        "digest_scope": "sha256 of the browser BINARY FILE, first 16 hex"},
            "subject": {"path": os.path.relpath(self.html, HERE),
                        "source_digest_on_disk": disk,
                        "source_digest_from_live_dom": sha16(live) if live else None,
                        "source_modified_by_harness": (disk != sha16(live)) if (disk and live) else None,
                        "live_constants": {"grid": self.state()["grid"],
                                           "canvas": self.state()["canvas"]}},
            "episode_clock": "one step == one tick; no wall-clock time enters the game",
        }


def selftest(seed=7, n=40):
    """Drive the page with a fixed move loop and print what the wrapper saw. No model, no scoring --
    this only proves the seam: the tick is held, the state is readable, a keypress reaches the game."""
    p = SnakePage()
    p.start()
    try:
        st = p.new_episode(seed=seed)
        print("tick0  head=%s len=%d maxCells=%d apple=%s count=%s rng=%d"
              % (st["head"], st["length"], st["maxCells"], st["apple"], st["count"], st["rng_calls"]))
        inst = p.instrument()
        print("subject digest disk=%s live=%s modified=%s"
              % (inst["subject"]["source_digest_on_disk"],
                 inst["subject"]["source_digest_from_live_dom"],
                 inst["subject"]["source_modified_by_harness"]))
        print("browser %s %s digest=%s" % (inst["browser"]["version"], inst["browser"]["binary"],
                                           inst["browser"]["binary_digest"]))
        moving = st["dir"][0] != 0
        for i in range(n):
            # straight line, wrapping the torus: no reversal, so every move should be ACCEPTED
            st2 = p.step("R" if not moving else "R")
            st = st2["state"]
            if i < 6 or i % 10 == 0:
                print("step %2d calls=%d head=%s dir=%s len=%d maxCells=%d apple=%s rng=%d"
                      % (i, st2["tick_calls"], st["head"], st["dir"], st["length"], st["maxCells"],
                         st["apple"], st["rng_calls"]))
            moving = st["dir"][0] != 0
        print("score-by-maxCells: %d apples (maxCells %d - 4)" % (st["maxCells"] - 4, st["maxCells"]))
        return 0
    finally:
        p.stop()


if __name__ == "__main__":
    sys.exit(selftest(seed=int(sys.argv[1]) if len(sys.argv) > 1 else 7,
                      n=int(sys.argv[2]) if len(sys.argv) > 2 else 40))
