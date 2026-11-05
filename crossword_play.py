#!/usr/bin/env python3
"""CROSSWORD PLAYER / SCORER -- answer-per-slot, scored against the crate's own answers.

Two things must be true before a model is worth spending a token on:

  1. the SCORER is right -- `--stub answers` returns 20/20 on any crate, or the scorer is broken;
  2. the CEILING is achievable -- `--stub ceiling` answers only where the clue alone determines the word,
     and must return exactly the crate's declared `clue_resolved` total. If it does not, the crate's
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
    loaded = CG.set_definitions()
    if not loaded:
        sys.exit("definitions.json not found: the candidate index would be empty and every ceiling "
                 "measurement would read zero BY CONSTRUCTION rather than by measurement")
    return d


def slots(d):
    for pi, p in enumerate(d["puzzles"]):
        for s in p["slots"]:
            yield pi, p, s


def prompt_for(s):
    return (f"Cryptic crossword clue: {s['clue']}\n"
            f"The answer is a single {s['length']}-letter English word. Reply with the word only.")


def ask(endpoint, prompt, timeout=180):
    """CHAT completions, with thinking disabled. A raw /completion on a reasoning model returns
    '<think>...' and any stop sequence on a newline truncates it to the empty string -- which is how the
    first two rows recorded 0/20 while the model was in fact answering."""
    body = json.dumps({"messages": [{"role": "user", "content": prompt}],
                       "n_predict": 48, "temperature": 0.0,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(endpoint.rstrip("/") + "/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out = json.loads(r.read())
    return (out["choices"][0]["message"]["content"] or "").strip()


def parse_answer(text, length):
    """ONE word of the right length, or nothing. A model that offers two candidates has not committed to an
    answer, and scoring the first one is a generosity applied after the fact -- so it scores as no answer."""
    m = sorted(set(re.findall(rf"\b[A-Za-z]{{{length}}}\b", text.upper())))
    return m[0] if len(m) == 1 else None


def self_test():
    """The PARSER is where a model run gets blamed for the harness. Check it against outputs a model
    actually produces before spending a token on one."""
    ok = fail = 0

    def check(name, cond):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"  FAIL {name}")

    check("bare word", parse_answer("TOUCHES", 7) == "TOUCHES")
    check("sentence", parse_answer("The answer is TOUCHES.", 7) == "TOUCHES")
    check("lower case", parse_answer("waltzes", 7) == "WALTZES")
    check("punctuated", parse_answer("TOUCHES!", 7) == "TOUCHES")
    check("leading newline", parse_answer("\nTOUCHES", 7) == "TOUCHES")
    check("word of the wrong length is not accepted", parse_answer("TOUCH", 7) is None)
    check("prose with no answer-length word is None", parse_answer("I am not sure", 7) is None)
    check("two candidate words is not an answer", parse_answer("maybe TOUCHES or WALTZES", 7) is None)
    check("the same word twice is still one answer", parse_answer("TOUCHES ... TOUCHES", 7) == "TOUCHES")
    check("a 7-letter word inside a longer token is not matched", parse_answer("TOUCHESX", 7) is None)
    check("an apostrophe word of the right length does not match", parse_answer("DON'T", 5) is None)
    print(f"{ok} passed, {fail} failed")
    return fail == 0


def play_iterate(endpoint, crate_path, rounds=4):
    """THE ITERATIVE PLAYER. Nothing is locked: each round, every slot sees the letters that the OTHER slots
    currently agree on at its cells, and may change its answer because of them. Only at the end are the
    proposals scored. This is the protocol in which a model's second answer can differ from its first --
    the greedy placer commits in one pass and therefore cannot recover a non-prototypical answer."""
    import re
    d = load(crate_path)
    rows, history = [], []
    for pi, p in enumerate(d["puzzles"]):
        slots = p["slots"]
        cells = {s["id"]: CG.slot_cells(s) for s in slots}
        cover = {}
        for s in slots:
            for c in cells[s["id"]]:
                cover.setdefault(c, []).append(s["id"])
        prop = {}
        for rd in range(1, rounds + 1):
            new = {}
            for s in slots:
                # a cell is fixed only where every OTHER slot that covers it agrees on one letter
                pat = []
                for idx, c in enumerate(cells[s["id"]]):
                    letters = set()
                    for o in cover[c]:
                        if o == s["id"]:
                            continue
                        w = prop.get(o)
                        if not w:
                            continue
                        j = cells[o].index(c)
                        letters.add(w[j])
                    pat.append(letters.pop() if len(letters) == 1 else "_")
                pattern = "".join(pat)
                prompt = (f"Crossword clue: {s['clue']} ({s['length']} letters). "
                          f"The crossing letters from the rest of the grid are {pattern} "
                          f"(underscores are unknown). Answer with exactly one {s['length']}-letter "
                          f"English word and nothing else.")
                raw = ask(endpoint, prompt)
                m = re.findall(rf"\b[A-Za-z]{{{s['length']}}}\b", (raw or "").upper())
                cand = m[0] if len(set(m)) == 1 else None
                if cand and cand in CG.WORDS:
                    new[s["id"]] = cand
            changed = sum(1 for k in new if new.get(k) != prop.get(k))
            history.append(dict(round=rd, proposed=len(new), changed=changed))
            prop = new
            if changed == 0:
                break
        conflicts = 0
        for c, ids in cover.items():
            letters = {prop[i][cells[i].index(c)] for i in ids if prop.get(i)}
            if len(letters) > 1:
                conflicts += 1
        for s in slots:
            rows.append(dict(puzzle=pi, id=s["id"], clue=s["clue"], answer=s["answer"],
                             placed=prop.get(s["id"]), correct=prop.get(s["id"]) == s["answer"]))
    filled = sum(1 for r in rows if r["placed"])
    right = sum(1 for r in rows if r["correct"])
    rec = dict(mode="iterate", endpoint=endpoint, crate=crate_path, n=len(rows), filled=filled,
               correct=right, rounds=history, conflicts=conflicts, rows=rows)
    print(f"iterative: slots {len(rows)}  filled {filled}  correct {right}  crossing-conflicts {conflicts}")
    print("  rounds:", history)
    for r in rows[:10]:
        print(f"   {r['id']:3s} {r['clue'][:18]:20s} key={r['answer']:9s} placed={str(r['placed']):10s} {'OK' if r['correct'] else ''}")
    return rec


def play_grid(endpoint, crate_path, passes=3):
    """THE ACTUAL GAME: answer slots against a live grid, using the crossing letters the grid already fixes.
    A slot is accepted only if it fits the pattern; passes repeat until nothing new lands. This is the
    protocol that can turn a synonym into an answer, and the one that tests whether crossings do work."""
    import re
    d = load(crate_path)
    rows, grid = [], {}
    for pi, p in enumerate(d["puzzles"]):
        placed = {}
        for pno in range(passes):
            before = len(placed)
            for s in p["slots"]:
                if s["id"] in placed:
                    continue
                cells = CG.slot_cells(s)
                pattern = "".join(grid.get(c, "_") for c in cells)
                prompt = (f"Crossword clue: {s['clue']} ({s['length']} letters). "
                          f"The pattern so far is {pattern} (underscores are unknown). "
                          f"Answer with exactly one {s['length']}-letter English word and nothing else.")
                raw = ask(endpoint, prompt)
                m = re.findall(rf"\b[A-Za-z]{{{s['length']}}}\b", (raw or "").upper())
                cand = m[0] if len(set(m)) == 1 else None
                # a word that is not in the declared lexicon never enters the grid: DARBOUR fit the pattern
                # and is not a word, and accepting it would have been the instrument's hole, not the model's win
                declared = bool(cand) and cand in CG.WORDS
                fits = declared and all(grid.get(c, ch) == ch for c, ch in zip(cells, cand))
                if fits:  # only declared words, only pattern-consistent placements
                    for c, ch in zip(cells, cand):
                        grid[c] = ch
                    placed[s["id"]] = cand
            if len(placed) == before:
                break
        for s in p["slots"]:
            rows.append(dict(puzzle=pi, id=s["id"], clue=s["clue"], answer=s["answer"],
                             placed=placed.get(s["id"]),
                             declared=(placed.get(s["id"]) in CG.WORDS) if placed.get(s["id"]) else False,
                             correct=placed.get(s["id"]) == s["answer"]))
    filled = sum(1 for r in rows if r["placed"])
    declared_n = sum(1 for r in rows if r["declared"])
    right = sum(1 for r in rows if r["correct"])
    rec = dict(mode="grid", endpoint=endpoint, crate=crate_path, n=len(rows), filled=filled,
               declared=declared_n, correct=right, rows=rows)
    print(f"grid protocol: slots {len(rows)}  filled {filled}  declared-word {declared_n}  correct {right}")
    for r in rows[:10]:
        print(f"   {r['id']:3s} {r['clue'][:20]:22s} key={r['answer']:9s} placed={str(r['placed']):10s} {'OK' if r['correct'] else ''}")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crate", default=str(HERE / "probes/CROSSWORD_CRATE_2026-11-05.json"))
    ap.add_argument("--stub", default=None, choices=("answers", "ceiling"))
    ap.add_argument("--endpoint", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--protocol", default="clues", choices=("clues", "grid", "iterate"))
    ap.add_argument("--rounds", type=int, default=4)
    a = ap.parse_args()

    if a.self_test:
        return 0 if self_test() else 1
    if a.protocol == "iterate":
        rec = play_iterate(a.endpoint, a.crate, rounds=a.rounds)
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_text(json.dumps(rec, indent=1) + "\n")
            print(f"wrote {a.out}")
        return 0
    if a.protocol == "grid":
        rec = play_grid(a.endpoint, a.crate)
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_text(json.dumps(rec, indent=1) + "\n")
            print(f"wrote {a.out}")
        return 0
    d = load(a.crate)
    rows, t0 = [], time.time()
    for pi, p, s in slots(d):
        cands = CG.candidates_of(s["clue_data"])
        if a.stub == "answers":
            got = s["answer"]
        elif a.stub == "ceiling":
            got = cands[0] if cands == [s["answer"]] else None
        elif a.endpoint:
            raw = ask(a.endpoint, prompt_for(s))
            got = parse_answer(raw, s["length"])
        else:
            sys.exit("need --stub or --endpoint")
        rows.append(dict(puzzle=pi, id=s["id"], kind=s["clue_kind"], length=s["length"],
                         raw=locals().get("raw") if a.endpoint else None,
                         clue=s["clue"], answer=s["answer"], got=got,
                         correct=bool(got) and got == s["answer"],
                         candidates=len(cands),
                         ceiling_reachable=(cands == [s["answer"]])))

    n = len(rows)
    right = sum(r["correct"] for r in rows)
    ceil = sum(1 for r in rows if r["ceiling_reachable"])
    declared_ceiling = sum(p["ceiling"]["clue_resolved"] for p in d["puzzles"])
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
