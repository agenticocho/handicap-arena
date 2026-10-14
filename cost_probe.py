#!/usr/bin/env python3
"""THE COST OF AN ENTRANT THAT CAN COMPLETE A GAME HERE -- measured, not estimated.

Chilly's ask: the head-to-head needs an entrant that can finish, so the scale decision has to be made
before the contest rather than discovered during it. This measures the one number that decides it --
PER MOVE, for each candidate, against the SAME position with the SAME frozen prompt.

THE POSITION IS THE ONE THE ORNITH RUN DIED AT: 28 legal moves, no move list supplied. It is the hard case
on the axis that matters (many candidates to derive), so a model that clears it clears easier ones.

    python3 cost_probe.py
"""
import glob
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess_game as g                                                # noqa: E402
import cabinet_root as _root                                          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FEN = "rnbqkbnr/ppp2ppp/8/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3"
LLAMA = "/home/chilly1/llama.cpp/build/bin/llama-server"
MODELS = os.environ.get("ARENA_MODELS") or os.path.expanduser("~/moltbook_pipeline/models")
# THE SAME RESOLUTION AS run_card.py, DELIBERATELY. The first version hardcoded ~/.hermes/models, which
# holds EIGHT models rather than the arena's fifty-three -- so a widened probe reported five entrants as
# ABSENT and would have reported a finding about a population it never looked at. A population named twice
# is a population that can disagree with itself; this reads ARENA_MODELS exactly as the runner does.
PORT = 8741

# smallest first, so the table fills in cheaply and a slow entrant is the only long wait
CANDIDATES = [
    ("Ministral-3-3B-Instruct-2512-UD-Q4_K_XL.gguf", "Ministral-3B"),
    ("Tiel-Inspired-Coder-9B-UD-Q4_K_M.gguf", "Tiel-Inspired-9B"),
    ("Ornith-1.5-9B-Q4_K_M.gguf", "Ornith-9B"),
]

# THE WIDENED POPULATION, DERIVED FROM THE DIRECTORY RATHER THAN TYPED. Chilly's call: DO NOT RESCOPE THE
# EVENT, WIDEN THE POPULATION -- and if no entrant can play unaided, that IS the finding ("no model on this
# box can play chess without being handed its moves"), reported with the population named and the rates
# attached.
#
# THE FIRST WIDENED LIST WAS TYPED AND FIVE OF ITS NINE ENTRIES WERE ABSENT -- invented filenames, against
# a directory that was itself the wrong one. A population has to be DERIVED from the field it claims to
# describe, at a spread across the size range, or the result is about the list instead of about the box.
def wide_population(n=9):
    # mmproj* ARE VISION PROJECTORS, NOT MODELS -- they load as weights for a separate .gguf and cannot be
    # an entrant. DERIVING A POPULATION ALSO INHERITS THE DIRECTORY'S NON-MEMBERS, so the exclusion is
    # explicit here rather than discovered as an unexplained load failure.
    files = sorted((p for p in glob.glob(os.path.join(MODELS, "*.gguf"))
                    if not os.path.basename(p).startswith("mmproj")), key=os.path.getsize)
    if not files:
        return []
    step = max(1, len(files) // n)
    return [(os.path.basename(p), os.path.basename(p).replace(".gguf", "")[:24])
            for p in files[::step][:n]]


WIDE = wide_population()


def probe(path, label):
    # SCRATCH, AND ITS COORDINATE IS DECLARED (cabinet_root.log_dir), not derived from this file's
    # location -- see DECISION_logs_are_scratch.md. A reader in another worktree could not resolve
    # a path built from HERE, which is the defect the declaration removes.
    os.makedirs(_root.log_dir(HERE), exist_ok=True)
    log = os.path.join(_root.log_dir(HERE), f"COST_PROBE_{label}.log")
    srv = subprocess.Popen([LLAMA, "-m", path, "-c", "8192", "-ngl", "0", "--port", str(PORT),
                            "--no-webui"], stdout=open(log, "w"), stderr=subprocess.STDOUT)
    row: dict = dict(entrant=label, loaded_s=None, committed=None, tokens=None, secs=None, move=None,
                     reason=None, viable=None)
    try:
        t0 = time.time()
        up = False
        while time.time() - t0 < 600:
            if srv.poll() is not None:
                row["reason"] = f"server exited rc={srv.returncode}"
                return row
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=3).read()
                up = True
                break
            except Exception:                                         # noqa: BLE001
                time.sleep(3)
        if not up:
            row["reason"] = "never answered /health in 600 s"
            return row
        row["loaded_s"] = round(time.time() - t0, 1)

        legal = g.legal_moves(FEN)
        body = json.dumps({"messages": [{"role": "user", "content": g.PROMPT_TEMPLATE.format(fen=FEN)}],
                           "max_tokens": g.MAX_TOKENS, "temperature": 0.0})
        req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions",
                                     data=body.encode(), headers={"Content-Type": "application/json"})
        t0 = time.time()
        j = json.loads(urllib.request.urlopen(req, timeout=900).read().decode())
        row["secs"] = round(time.time() - t0, 1)
        msg = (j.get("choices") or [{}])[0].get("message") or {}
        row["tokens"] = (j.get("usage") or {}).get("completion_tokens")
        content = (msg.get("content") or "").strip()
        uci, san, why = g.resolve(FEN, content, legal)
        row["committed"] = uci is not None
        row["move"] = uci or san
        row["reason"] = why.split(":")[0]
        row["reasoning_chars"] = len(msg.get("reasoning_content") or "")
        # VIABLE = commits to a legal move, so a 60-ply event costs secs*60 and can be budgeted
        row["viable"] = bool(uci)
        row["a_60ply_event_min"] = round(row["secs"] * 60 / 60, 1) if row["secs"] else None
        return row
    except Exception as e:                                            # noqa: BLE001
        row["reason"] = f"probe error: {e}"
        return row
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=30)
        except Exception:                                             # noqa: BLE001
            srv.kill()


def main():
    wide = "--wide" in sys.argv
    selected = WIDE if wide else CANDIDATES
    print("=" * 96)
    print("COST OF AN ENTRANT THAT CAN COMPLETE A GAME HERE -- one move, the hard position, frozen prompt")
    print("=" * 96)
    print(f"  population: {'WIDENED (' + str(len(selected)) + ' entrants, untried)' if wide else 'the first three'}")
    print(f"  position: {FEN}")
    print(f"  {len(g.legal_moves(FEN))} legal moves, none of them supplied")
    print(f"  prompt digest {g.PROMPT_DIGEST}, max_tokens {g.MAX_TOKENS}, all-CPU (ngl=0)")
    print()
    rows = []
    for fn, label in selected:
        p = os.path.join(MODELS, fn)
        if not os.path.exists(p):
            print(f"  {label:18s} ABSENT")
            continue
        print(f"  {label:18s} probing ...", flush=True)
        r = probe(p, label)
        rows.append(r)
        print(f"  {label:18s} load {r['loaded_s']}s | {r['secs']}s | {r['tokens']} tok | "
              f"committed={r['committed']} | {r['move']} | {r['reason']}")
    print()
    print("  === THE TABLE ===")
    print(f"  {'entrant':18s} {'load':>7s} {'sec/move':>9s} {'tokens':>7s} {'commits':>8s} "
          f"{'60-ply event':>13s}")
    for r in rows:
        print(f"  {r['entrant']:18s} {str(r['loaded_s']):>7s} {str(r['secs']):>9s} {str(r['tokens']):>7s} "
              f"{str(r['committed']):>8s} {str(r.get('a_60ply_event_min')):>10s} min")
    print()
    viable = [r for r in rows if r.get("viable")]
    print(f"  VIABLE (commits to a legal move): {len(viable)} of {len(rows)}")
    for r in viable:
        print(f"    {r['entrant']:18s} a 60-ply event costs about {r['a_60ply_event_min']} min on this box")
    # probes/ NOT results/ -- THE SECOND TIME THIS EXACT MISTAKE HAS COST SOMETHING. `results/` holds
    # RESULT BUNDLES, and run_card.py's `already_measured` reads every JSON in it as a bundle
    # (`d.get("results")`). A LIST-shaped file there raises `'list' object has no attribute 'get'` and
    # KILLED a v6 run at entrant 14 of 46. The stray .log files were the first version of this; fixing the
    # writer is the only version that stops the third.
    os.makedirs(os.path.join(HERE, "probes"), exist_ok=True)
    out = os.path.join(HERE, "probes", "COST_PROBE_WIDE.json" if wide else "COST_PROBE.json")
    json.dump(rows, open(out, "w"), indent=1)
    print(f"\n  artifact: {os.path.relpath(out, HERE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
