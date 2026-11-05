#!/usr/bin/env python3
"""The pilot's first number: how much of the freeform crate is solvable from the clue alone.

Ceiling = a slot is RESOLVED when the clue's own letters admit exactly one declared word and that
word is the slot's answer -- no crossings used. Reported as `anagram_resolved / slots`, never as a
pass, because a high ceiling is not a failure of the instrument; it is a finding about the crate.

Then the crossing check: fix every resolved slot, enumerate every combination of the unresolved
ones and keep the assignments whose letters agree on every shared cell. A count of 1 means the
crossings decide the puzzle in a single step. A larger count means the crate has more than one
consistent fill, i.e. a player can hand back a fully correct-looking grid that is not the key.

The word list is not embedded in the crate, only its digest, so this reads the list out of the
generator that declares it and REFUSES to report if the digest does not match the crate's own
`words_sha256`: a measurement against a different list is not a measurement of this crate.

    python3 crossword_pilot_ceiling.py --git-ref f80e47a \
        --json-out probes/CROSSWORD_PILOT_CEILING_2026-11-05.json

LABEL this artifact carries: PILOT - NOT A BENCHMARK - NO HUMAN SOLVE
"""
import argparse
import hashlib
import importlib.util
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile

LABEL = "PILOT - NOT A BENCHMARK - NO HUMAN SOLVE"


def from_git(ref, path):
    return subprocess.run(["git", "show", f"{ref}:{path}"], check=True,
                          capture_output=True).stdout.decode()


def load_generator(path):
    spec = importlib.util.spec_from_file_location("crossword_generator_under_test", path)
    if spec is None or spec.loader is None:
        sys.exit(f"REFUSE: {path} is not importable as a Python module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def clue_candidates(gen, slot):
    """Every declared word the clue alone admits. Handles both clue encodings this crate has had."""
    if slot.get("clue_data"):
        return gen.candidates_of(slot["clue_data"])
    return gen.anagram_candidates(slot["scramble"])


def cells(slot, word):
    if slot["direction"] == "across":
        return [(slot["row"], slot["col"] + i, ch) for i, ch in enumerate(word)]
    return [(slot["row"] + i, slot["col"], ch) for i, ch in enumerate(word)]


def consistent(slots, assign):
    grid = {}
    for s in slots:
        for r, c, ch in cells(s, assign[s["id"]]):
            if grid.setdefault((r, c), ch) != ch:
                return False
    return True


def measure(crate, gen):
    words = tuple(gen.WORDS)
    digest = hashlib.sha256(" ".join(words).encode()).hexdigest()
    if digest != crate["words_sha256"]:
        sys.exit(f"REFUSE: generator word list hashes to {digest}, crate declares "
                 f"{crate['words_sha256']} -- not the same words, so not the same crate")

    rows, total_slots, total_res = [], 0, 0
    for i, p in enumerate(crate["puzzles"]):
        slots = p["slots"]
        fixed, freed = {}, []
        for s in slots:
            cands = clue_candidates(gen, s)
            if len(cands) == 1:
                fixed[s["id"]] = cands[0]
            else:
                freed.append((s["id"], cands, s["answer"]))
        truth = {s["id"]: s["answer"] for s in slots}
        survivors, alternatives = 0, []
        for combo in itertools.product(*[c for _, c, _ in freed]):
            assign = dict(fixed)
            assign.update({freed[k][0]: combo[k] for k in range(len(freed))})
            if not consistent(slots, assign):
                continue
            survivors += 1
            diff = {k: [truth[k], v] for k, v in assign.items() if truth[k] != v}
            if diff:
                alternatives.append(diff)
        resolved = len(slots) - len(freed)
        total_slots += len(slots)
        total_res += resolved
        rows.append(dict(
            puzzle=i, slots=len(slots), anagram_resolved=resolved,
            declared_by_crate=p.get("ceiling", {}).get("anagram_resolved"),
            agrees_with_crate=resolved == p.get("ceiling", {}).get("anagram_resolved"),
            unresolved=[dict(id=sid, answer=ans, candidates=cs) for sid, cs, ans in freed],
            combinations_enumerated=len(list(itertools.product(*[c for _, c, _ in freed]))),
            crossing_consistent_completions=survivors,
            answer_key_is_consistent=consistent(slots, truth),
            alternative_fills=alternatives,
        ))
    return words, digest, rows, total_slots, total_res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crate", default="probes/CROSSWORD_CRATE_2026-11-05.json")
    ap.add_argument("--generator", default="crossword_gen.py")
    ap.add_argument("--git-ref", default=None,
                    help="read both files from this commit instead of the working tree")
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()

    tmpdir = None
    if a.git_ref:
        crate = json.loads(from_git(a.git_ref, a.crate))
        tmpdir = tempfile.mkdtemp()
        gen_path = os.path.join(tmpdir, "generator_under_test.py")
        with open(gen_path, "w") as fh:
            fh.write(from_git(a.git_ref, a.generator))
    else:
        with open(a.crate) as fh:
            crate = json.load(fh)
        gen_path = a.generator
    try:
        gen = load_generator(gen_path)
        words, digest, rows, total_slots, total_res = measure(crate, gen)
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)

    out = dict(label=LABEL,
               source=dict(git_ref=a.git_ref, crate=a.crate, generator=a.generator),
               word_list=dict(size=len(words), sha256=digest),
               method="clue-only candidate enumeration over the declared word list, then crossing "
                      "consistency by exhaustive enumeration of the unresolved combinations",
               puzzles=rows,
               total=dict(anagram_resolved=total_res, slots=total_slots,
                          fraction=round(total_res / total_slots, 4)))
    print(LABEL)
    print(f"word list {len(words)} words  sha256 {digest[:16]}  matches crate: yes")
    for r in rows:
        print(f"puzzle {r['puzzle']}: ceiling {r['anagram_resolved']}/{r['slots']} "
              f"crate-declared {r['declared_by_crate']} agree {r['agrees_with_crate']}  "
              f"unresolved {[u['id'] for u in r['unresolved']]}  "
              f"crossing-consistent fills {r['crossing_consistent_completions']}  "
              f"alternatives {r['alternative_fills']}")
    print(f"TOTAL anagram_resolved/slots = {total_res}/{total_slots} = {total_res / total_slots:.4f}")
    if a.json_out:
        with open(a.json_out, "w") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
        print(f"wrote {a.json_out}")


if __name__ == "__main__":
    main()
