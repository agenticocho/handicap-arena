#!/usr/bin/env python3
"""CROSSWORD PLAYER / SCORER -- answer-per-slot, scored against the crate's own answers.

Two things must be true before a model is worth spending a token on:

  1. the SCORER is right -- `--stub answers` returns 20/20 on any crate, or the scorer is broken;
  2. the CEILING is achievable -- `--stub ceiling` answers only where the clue alone determines the word,
     and must return exactly the crate's declared `anagram_resolved` total. If it does not, the crate's
     headline number and the scorer disagree about what a slot is.

Only then `--endpoint`, which asks a model one slot at a time and scores what comes back.

    python3 crossword_play.py --stub answers
    python3 crossword_play.py --stub ceiling
    python3 crossword_play.py --endpoint http://127.0.0.1:5806 --out probes/CROSSWORD_PLAY_<model>.json
"""
import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import crossword_gen as CG  # noqa: E402


def load(crate_path):
    d = json.loads(Path(crate_path).read_text())
    CG.set_lexicon()
    return d


def slots(d):
    for pi, p in enumerate(d["puzzles"]):
        for s in p["slots"]:
            yield pi, p, s


def prompt_for(s):
    return (f"Cryptic crossword clue: {s['clue']}\n"
            f"The answer is a single {s['length']}-letter English word. Reply with the word only.")


def ask(endpoint, prompt, timeout=90):
    body = json.dumps({"prompt": prompt, "n_predict": 24, "temperature": 0.0,
                       "stop": ["\n", "."]}).encode()
    req = urllib.request.Request(endpoint.rstrip("/") + "/completion", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out = json.loads(r.read())
    return (out.get("content") or "").strip()


def parse_answer(text, length):
    m = re.findall(rf"\b[A-Za-z]{{{length}}}\b", text.upper())
    return m[0] if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crate", default=str(HERE / "probes/CROSSWORD_CRATE_2026-11-05.json"))
    ap.add_argument("--stub", default=None, choices=("answers", "ceiling"))
    ap.add_argument("--endpoint", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    d = load(a.crate)
    rows, t0 = [], time.time()
    for pi, p, s in slots(d):
        cands = CG.candidates_of(s["clue_data"])
        if a.stub == "answers":
            got = s["answer"]
        elif a.stub == "ceiling":
            got = cands[0] if cands == [s["answer"]] else None
        elif a.endpoint:
            got = parse_answer(ask(a.endpoint, prompt_for(s)), s["length"])
        else:
            sys.exit("need --stub or --endpoint")
        rows.append(dict(puzzle=pi, id=s["id"], kind=s["clue_kind"], length=s["length"],
                         clue=s["clue"], answer=s["answer"], got=got,
                         correct=bool(got) and got == s["answer"],
                         candidates=len(cands),
                         ceiling_reachable=(cands == [s["answer"]])))

    n = len(rows)
    right = sum(r["correct"] for r in rows)
    ceil = sum(1 for r in rows if r["ceiling_reachable"])
    declared_ceiling = sum(p["ceiling"]["anagram_resolved"] for p in d["puzzles"])
    total_slots = sum(len(p["slots"]) for p in d["puzzles"])
    by_kind = {}
    for r in rows:
        k = by_kind.setdefault(r["kind"], [0, 0])
        k[0] += r["correct"]
        k[1] += 1
    rec = dict(mode=a.stub or a.endpoint, crate=a.crate, n=n, correct=right,
               ceiling_reachable=ceil, declared_ceiling=declared_ceiling, total_slots=total_slots,
               by_kind={k: f"{v[0]}/{v[1]}" for k, v in by_kind.items()},
               wall_s=round(time.time() - t0, 1), rows=rows)
    print(f"mode {rec['mode']}  slots {n}  correct {right}/{n}  "
          f"ceiling-reachable {ceil}/{n}  declared ceiling total {declared_ceiling}/{total_slots}  "
          f"by kind {rec['by_kind']}")
    if a.stub == "answers" and right != n:
        print("  *** SCORER BROKEN: a perfect answer set must score every slot")
    if a.stub == "ceiling" and right != declared_ceiling:
        print(f"  *** CEILING DISAGREES: stub scores {right}, crate declares {declared_ceiling}")
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(rec, indent=1) + "\n")
        print(f"wrote {a.out}")
    return 0 if (a.stub != "answers" or right == n) and (a.stub != "ceiling" or right == declared_ceiling) else 1


if __name__ == "__main__":
    sys.exit(main())
