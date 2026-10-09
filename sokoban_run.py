#!/usr/bin/env python3
"""SOKOBAN -- the entrant driver. One model, one level, one letter at a time.

BUILT TO PREREG_sokoban.md. The simulator decided everything; this only asks and records.

THE MENU LESSON, APPLIED BY DISTINCTION RATHER THAN BY HABIT. Chess failed because the prompt listed the
LEGAL MOVES -- the answer set -- so the entrant chose from a menu instead of deriving candidates. Here the
prompt names the four CONTROLS: U D L R. That is the INTERFACE, the way a controller has four buttons:

    NAMING THE FOUR CONTROLS IS THE INTERFACE.        LISTING THE TWENTY LEGAL MOVES WAS THE ANSWER.
    A control scheme is part of the machine.          A move list is the work.

No move is named, no direction is suggested, and the illegal push is rejected by the simulator rather than
warned about in the prompt -- so the entrant learns about walls the way a player does.

AND `RESIGN` IS OFFERED, because the give-up is a SIGNAL and not noise: a model that says it is beaten when
it IS beaten, and one that says it when it is not, are the faculty this cabinet measures. Premature
collapse is provable without a solver wherever the level's solution is verified.

    python3 sokoban_run.py --entrant <gguf> --level levels/01_one_push.txt --cap 40
    python3 sokoban_run.py --self-test
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban as S                                                     # noqa: E402

LLAMA = "/home/chilly1/llama.cpp/build/bin/llama-server"
MODELS = os.environ.get("ARENA_MODELS") or os.path.expanduser("~/moltbook_pipeline/models")
MAX_TOKENS = 64                     # ONE LETTER NEEDS A FEW TOKENS, and a cap that cannot be deliberated
                                    # into is the constraint this game was chosen for


def prompt_for(board, history):
    """THE SCREEN, not the answers. Board, the four controls, and the offer to resign."""
    recent = "".join(history[-12:]) if history else "(none yet)"
    return (
        "You are playing Sokoban. One crate per target; a crate can be PUSHED but never pulled, so a "
        "wrong push can end the level permanently.\n\n"
        "Board:\n"
        "# wall   . target   $ crate   @ you   * crate on target   + you on target\n\n"
        f"{board}\n\n"
        f"Moves so far: {recent}\n\n"
        "FIRST LINE: your next move as ONE letter and nothing else.\n"
        "  U = up    D = down    L = left    R = right\n"
        "If you judge the level unwinnable from here, the first line is exactly: RESIGN\n"
        "AFTER the first line you may explain your reasoning if you wish."
    )


def ask(base, board, history, timeout_s=300):
    body = json.dumps({"messages": [{"role": "user", "content": prompt_for(board, history)}],
                       "max_tokens": MAX_TOKENS, "temperature": 0.0})
    req = urllib.request.Request(base + "/v1/chat/completions", data=body.encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            j = json.loads(r.read().decode())
        dt = time.time() - t0
        msg = ((j.get("choices") or [{}])[0].get("message") or {})
        txt = (msg.get("content") or "").strip()
        if not txt and (msg.get("reasoning_content") or "").strip():
            # THE SECOND FIELD, AGAIN. A reasoning model puts its output in `reasoning_content` and leaves
            # `content` empty -- measured on this box, 2048 tokens of deliberation and no answer. Reading
            # one field and reporting "the model said nothing" is the empty-room defect in the API response.
            txt = (msg.get("reasoning_content") or "").strip()
        nt = (j.get("usage") or {}).get("completion_tokens", 0)
        hit = (j.get("choices") or [{}])[0].get("finish_reason") == "length"
        return txt, dt, nt, hit
    except Exception as e:                                              # noqa: BLE001
        return "", time.time() - t0, 0, False


def first_token(text):
    """THE ANSWER IS AT THE HEAD -- the first line, and one token from it. Nothing is mined from prose."""
    for line in (text or "").splitlines():
        line = line.strip()
        if line:
            return line.split()[0] if line.split() else ""
    return ""


def run(entrant, level_path, cap, port):
    level = open(level_path).read()
    label = os.path.basename(entrant).replace(".gguf", "")
    lname = os.path.basename(level_path).replace(".txt", "")
    st = S.parse(level)

    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    log = os.path.join(HERE, "logs", f"SOKOBAN_{label}_{lname}.log")
    srv = subprocess.Popen([LLAMA, "-m", entrant, "-c", "4096", "-ngl", "0", "--port", str(port),
                            "--no-webui"], stdout=open(log, "w"), stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    try:
        t0 = time.time()
        up = False
        while time.time() - t0 < 600:
            if srv.poll() is not None:
                return {"entrant": label, "level": lname, "loaded": False,
                        "why": f"server exited rc={srv.returncode}"}
            try:
                urllib.request.urlopen(base + "/health", timeout=3).read()
                up = True
                break
            except Exception:                                           # noqa: BLE001
                time.sleep(3)
        if not up:
            return {"entrant": label, "level": lname, "loaded": False,
                    "why": "never answered /health in 600 s"}
        load_s = time.time() - t0

        tokens, turns = [], []
        cur, history = S.render(st), []
        for i in range(cap):
            text, secs, nt, hit = ask(base, cur, history)
            tok = first_token(text)
            tokens.append(tok)
            turns.append({"ply": i, "raw": text[:400], "token": tok, "secs": round(secs, 1),
                          "gen_tokens": nt, "budget_hit": hit, "board": cur})
            history.append(tok)
            if not tok:
                break
            # STEP THE SIMULATOR, so the next screen is the truth rather than the model's belief about it
            nxt, _outcome = S.step(st, tok.strip().upper()) if (
                len(tok.strip()) == 1 and tok.strip().upper() in S.ACTIONS) else (st, "noop")
            st = nxt
            cur = S.render(st)
            if S.solved(st):
                break

        r = S.play(level, tokens)
        r.update({"entrant": label, "level": lname, "loaded": True, "load_s": round(load_s, 1),
                  "turns": turns, "cap": cap, "final_screen": cur})
        return r
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=30)
        except Exception:                                               # noqa: BLE001
            srv.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrant")
    ap.add_argument("--level")
    ap.add_argument("--cap", type=int, default=40)
    ap.add_argument("--port", type=int, default=8751)
    a = ap.parse_args()
    if not a.entrant or not a.level:
        ap.error("--entrant and --level are required")
    p = a.entrant if os.path.exists(a.entrant) else os.path.join(MODELS, a.entrant)
    if not os.path.exists(p):
        print(f"  ENTRANT ABSENT: {a.entrant}"); return 2
    r = run(p, a.level, a.cap, a.port)
    print(f"  entrant   {r['entrant']}")
    print(f"  level     {r['level']}")
    if not r.get("loaded"):
        print(f"  DID NOT LOAD -- {r['why']}"); return 3
    print(f"  ended     {r['ended']}    solved={r['solved']}    moves={r['moves']}")
    print(f"  counts    blocked={r['blocked']}  not_an_action={r['not_an_action']}  "
          f"give_up={r['give_up']}  gave_up_at={r['gave_up_at']}")
    print(f"  tokens    {[t['token'] for t in r['turns']]}")
    out = os.path.join(HERE, "probes", f"SOKOBAN_{r['entrant']}_{r['level']}.json")
    os.makedirs(os.path.join(HERE, "probes"), exist_ok=True)
    json.dump(r, open(out, "w"), indent=1)
    print(f"  artifact  {os.path.relpath(out, HERE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
