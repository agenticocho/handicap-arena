#!/usr/bin/env python3
"""mastermind_run_onefile.py — the Mastermind 4x6 runner as ONE importable file.

Why this file exists: mastermind_run.py imports mastermind_sim, mastermind_prompt and
mastermind_probe as siblings. Over the chair link a file's bytes arrive but its module
name does not (arrivals are stored as <sha12>-<name>), so that runner cannot start on a
box that only received the four files. Chilly named this precisely; this is the answer.

What is inlined here, and from where (verbatim semantics, no drift):
  all_codes / feedback / PEGS / COLOURS / SPACE   <- mastermind_sim.py
  build_prompt / render_history / parse_history / parse_guess  <- mastermind_prompt.py
  http_model                                      <- mastermind_probe.py

Two deliberate changes from mastermind_run.py, both required by the peer review:

1. NO ABSOLUTE PATH. mastermind_prompt.py did sys.path.insert(0, "<an absolute arcade dir>"),
   inserted at position 0, which OUTRANKS the runner's own directory: on any box where that
   path exists a stale simulator could shadow the shipped one while the prompt bytes still
   matched. There is no sys.path manipulation in this file at all. (No literal absolute path
   appears in this file anywhere, including in comments, so a grep for one returns nothing.)

2. THE CONTROL'S CHOOSER IS FROZEN. mastermind_run.py drew a random member of the
   consistent set (random.Random(seed+1)), which made its row-set digest a portability test
   of one file rather than an agreement test between two instruments. SELECTOR below is
   fixed at the first feedback-consistent code in lexicographic order (`pick = cands[0]`)
   and is printed in every run header. Two independent implementations must now produce ONE
   row-set digest, and a mismatch is a fault rather than a choice of rule.

CONTROL FIRST. --control swaps the model for a scripted consistent player on the identical
prompt path. If it does not score 100% on the fixture the harness is broken and no model
number from this file is valid. The process exit status carries that verdict (see emit_exit).

Row schema (per game) — unchanged from mastermind_run.py, plus `state`:
  secret, guesses, feedback, consistent, consistent_all, solved, guesses_used,
  distinct_guesses, turns, no_answer, strict, normalized, raw, tokens, secs, finish,
  content_empty, remaining_candidates, ended, won_at
  state   {"ended", "remaining_candidates", "candidates_at_each_turn",
           "consistent_at_each_turn"}   <-- the column the review asked for

Run header (per run): instrument name + sha256, fixture name + sha256, selector, rules,
prompt-renderer sha256, exit-status policy, and the row-set digest.
"""
import argparse
import hashlib
import itertools
import json
import os
import re
import sys
import time
import urllib.request
from collections import Counter

# ── Engine (from mastermind_sim.py) ───────────────────────────────────────────
PEGS = 4
COLOURS = 6
SPACE = COLOURS ** PEGS  # 1296
MAX_GUESSES = 10

# ── Frozen selector: the whole point of the second change ─────────────────────
SELECTOR = "first-consistent-lex  (pick = cands[0]; candidates enumerated in itertools.product order)"

# ── Broken arm: a deliberately constant guess. Must score 0 on solvable boards ──
CONSTANT_GUESS = (0, 0, 0, 0)

UNIVERSE = list(itertools.product(range(COLOURS), repeat=PEGS))
GIVE_UP = ("resign", "give up", "giveup", "quit", "surrender", "abandon")

EXIT_OK = 0
EXIT_CONTROL_FAILED = 2
EXIT_FIXTURE = 3
EXIT_PROMPT = 4
EXIT_INCONSISTENT = 5


def all_codes():
    return list(itertools.product(range(COLOURS), repeat=PEGS))


def feedback(code, guess):
    """(exact, partial). Exact = right colour, right place; partial = right colour, wrong
    place, multiplicity-correct. Identical to mastermind_sim.feedback."""
    exact = sum(1 for c, g in zip(code, guess) if c == g)
    common = sum(min(a, b) for a, b in zip(
        tuple(Counter(code)[i] for i in range(COLOURS)),
        tuple(Counter(guess)[i] for i in range(COLOURS)),
    ))
    return exact, common - exact


# ── Prompt renderer + parsers (from mastermind_prompt.py) ─────────────────────
def render_history(history):
    if not history:
        return "(no guesses yet)"
    lines = []
    for i, (guess, exact, partial) in enumerate(history, 1):
        g = " ".join(str(x) for x in guess)
        lines.append(f"  Turn {i:2d}:  {g}  ->  exact: {exact}, partial: {partial}")
    return "\n".join(lines)


def build_prompt(history, turn, limit=10):
    remaining = limit - turn + 1
    return (
        f"You are playing Mastermind. {PEGS} pegs, {COLOURS} colours (0-{COLOURS-1}).\n"
        f"Goal: guess the secret code in {limit} tries or fewer.\n"
        f"\n"
        f"After each guess you receive feedback:\n"
        f"  exact = pegs correct colour AND position\n"
        f"  partial = pegs correct colour but wrong position\n"
        f"  (Colours may repeat — the secret code can have duplicate colours.)\n"
        f"\n"
        f"Guess history ({len(history)} of {limit} turns used, {remaining} remaining):\n"
        f"{render_history(history)}\n"
        f"\n"
        f"What is your next guess? Reply with ONLY {PEGS} numbers (0-{COLOURS-1}) "
        f"separated by spaces. Nothing else."
    )


_HIST_RE = re.compile(
    r"Turn\s+\d+:\s+([\d\s]+?)\s*->\s*exact:\s*(\d+),\s*partial:\s*(\d+)"
)


def parse_history(prompt):
    history = []
    for m in _HIST_RE.finditer(prompt):
        guess = tuple(int(x) for x in m.group(1).strip().split())
        if len(guess) != PEGS:
            return None
        history.append((guess, int(m.group(2)), int(m.group(3))))
    return history


def parse_guess_strict(response):
    for line in response.strip().splitlines():
        parts = line.strip().split()
        if len(parts) == PEGS:
            try:
                guess = tuple(int(p) for p in parts)
                if all(0 <= g < COLOURS for g in guess):
                    return guess
            except ValueError:
                continue
    parts = response.strip().split()
    if len(parts) == PEGS:
        try:
            guess = tuple(int(p) for p in parts)
            if all(0 <= g < COLOURS for g in guess):
                return guess
        except ValueError:
            pass
    return None


def parse_guess_normalized(response):
    text = response.replace("**", "").replace("*", "").replace("`", "").replace(",", " ")
    return parse_guess_strict(text)


def parse_guess(response):
    strict = parse_guess_strict(response)
    normalized = parse_guess_normalized(response) if strict is None else strict
    return {"strict": strict, "normalized": normalized,
            "no_answer": strict is None and normalized is None}


# ── HTTP arm (from mastermind_probe.py) ──────────────────────────────────────
def http_model(base, model, api_key=None, max_tokens=512, thinking_off=True):
    def call(prompt):
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": max_tokens,
        }
        if thinking_off:
            body["chat_template_kwargs"] = {"enable_thinking": False}
        req = urllib.request.Request(
            base.rstrip("/") + "/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json",
                     **({"Authorization": f"Bearer {api_key}"} if api_key else {})},
        )
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                d = json.loads(r.read())
        except Exception as e:
            return {"content": "", "reasoning": "", "finish": f"error:{type(e).__name__}",
                    "secs": round(time.time() - t0, 2), "tokens": None}
        ch = d["choices"][0]
        return {
            "content": ch["message"].get("content") or "",
            "reasoning": ch["message"].get("reasoning_content") or "",
            "finish": ch.get("finish_reason"),
            "secs": round(time.time() - t0, 2),
            "tokens": d.get("usage", {}).get("completion_tokens"),
        }
    return call


# ── Fixture ─────────────────────────────────────────────────────────────────
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(s):
    return hashlib.sha256(s.encode()).hexdigest()


def read_fixture(path):
    """TSV: game, index, four colours. Refuses rather than repairs a malformed line."""
    out = []
    with open(path) as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#") or line.lower().startswith("game\t"):
                continue
            parts = line.split("\t")
            if len(parts) != 3:
                raise SystemExit(f"fixture line {ln}: expected 3 columns, got {len(parts)}")
            game, idx, secret = parts
            code = tuple(int(x) for x in secret.split())
            if len(code) != PEGS or any(c < 0 or c >= COLOURS for c in code):
                raise SystemExit(f"fixture line {ln}: bad secret {secret!r}")
            if UNIVERSE.index(code) != int(idx):
                raise SystemExit(f"fixture line {ln}: index {idx} != {UNIVERSE.index(code)}")
            out.append((int(game), code))
    if not out:
        raise SystemExit("fixture is empty")
    return out


# ── Control player: reads only the rendered prompt, chooses cands[0] ─────────
def consistent_choice(prompt):
    hist = parse_history(prompt)
    if hist is None:
        return None, "parse-fail", None
    cands = [c for c in UNIVERSE]
    for g, ex, pa in hist:
        cands = [c for c in cands if feedback(c, g) == (ex, pa)]
    if not cands:
        return None, "inconsistent-history", 0
    return cands[0], "", len(cands)


def constant_guess_choice(prompt):
    """Deliberately broken arm: ignores the prompt entirely."""
    return CONSTANT_GUESS, "constant-guess", None


def recompute_consistent_list(game):
    """Recompute the per-turn consistent flags from guesses + feedback, never trusting stored."""
    hist = []
    out = []
    guesses = [tuple(g) for g in game.get("guesses", [])]
    feedbacks = game.get("feedback", [])
    for guess, fb in zip(guesses, feedbacks):
        ex, pa = int(fb[0]), int(fb[1])
        cons = all(feedback(guess, hg) == (he, hp) for (hg, he, hp) in hist)
        out.append(bool(cons))
        hist.append((guess, ex, pa))
    return out


def stored_vs_recomputed_disagreements(rows):
    n = 0
    for r in rows:
        stored = list(r.get("consistent", []))
        recomputed = recompute_consistent_list(r)
        for a, b in zip(stored, recomputed):
            if bool(a) != bool(b):
                n += 1
    return n


def per_turn_prompt_digests(limit=MAX_GUESSES):
    return [sha256_text(build_prompt([], t, limit)) for t in range(1, limit + 1)]


def per_state_nulls(game):
    cands_before = game.get("state", {}).get("candidates_before_each_turn", [])
    if not cands_before:
        cands_before = game.get("candidates_before_each_turn", [])
    return [cb / SPACE for cb in cands_before]


def control_arm_rows(fixture, limit, reply_fn):
    return [play_game(secret, reply_fn, limit, True) for _, secret in fixture]


def run_control_block(fixture, limit, verbose=True):
    def _control_reply(p):
        g, note, _n = consistent_choice(p)
        return g, {"route": "strict" if g else "none", "note": note, "raw": None}
    def _broken_reply(p):
        g, note, _n = constant_guess_choice(p)
        return g, {"route": "constant-guess", "note": note, "raw": None}
    control_rows = control_arm_rows(fixture, limit, _control_reply)
    broken_rows = control_arm_rows(fixture, limit, _broken_reply)
    control_wins = sum(1 for r in control_rows if r.get("solved"))
    broken_wins = sum(1 for r in broken_rows if r.get("solved"))
    disc = stored_vs_recomputed_disagreements(control_rows) + stored_vs_recomputed_disagreements(broken_rows)
    digests = per_turn_prompt_digests(limit)
    # per-state null sample from control arm
    nulls = [per_state_nulls(r) for r in control_rows]
    if verbose:
        print("\n=== MASTERMIND CONTROL BLOCK (in-process) ===")
        print(f"  scripted control arm: {control_wins}/{len(fixture)} wins (must be 100%)")
        print(f"  broken (constant guess) arm: {broken_wins}/{len(fixture)} wins (must be 0)")
        print(f"  stored-vs-recomputed consistent disagreements: {disc}")
        print(f"  per-turn prompt digests: " + " ".join(d[:8] for d in digests))
        print("  per-state nulls (control arm, game 0): " + ", ".join(f"{x:.4f}" for x in (nulls[0] if nulls else [])))
        if control_wins != len(fixture):
            print("  CONTROL FAILED — scripted arm did not score 100%")
        if broken_wins != 0:
            print("  CONTROL FAILED — broken arm did not score 0")
        if disc != 0:
            print("  NOTE: nonzero disagreements printed above (must be investigated)")
        if control_wins == len(fixture) and broken_wins == 0:
            print("  CONTROL BLOCK PASSED")
    return {"control_wins": control_wins, "broken_wins": broken_wins,
            "disagreements": disc, "digests": digests, "nulls": nulls,
            "passed": control_wins == len(fixture) and broken_wins == 0}


# ── Play one game ───────────────────────────────────────────────────────────
def play_game(secret, reply_fn, limit, check_prompt_roundtrip=True):
    history, rows = [], []
    won_at = None
    ended = "budget_exhausted"
    cands_after = []
    cands_before = list(UNIVERSE)
    candidates_before_each_turn = []
    for turn in range(1, limit + 1):
        candidates_before_each_turn.append(len(cands_before))
        prompt = build_prompt(history, turn, limit)
        if check_prompt_roundtrip and parse_history(prompt) != history:
            raise RuntimeError(f"prompt round-trip failed at turn {turn}: "
                               f"{parse_history(prompt)!r} != {history!r}")
        guess, meta = reply_fn(prompt)

        if guess is None and str(meta.get("note", "")).lower() in GIVE_UP:
            ended = "gave_up"
            break

        cons = None
        if guess is not None:
            cons = all(feedback(guess, h) == (ex, pa) for h, ex, pa in history)

        rows.append({"turn": turn, "guess": guess, "consistent": cons, **meta})
        if guess is None:
            ended = "no_answer"
            break

        ex, pa = feedback(secret, guess)
        history.append((guess, ex, pa))
        cands_after.append(len([c for c in UNIVERSE
                                if all(feedback(c, g) == (e, p) for g, e, p in history)]))
        cands_before = [c for c in cands_before if feedback(c, guess) == (ex, pa)]
        if guess == secret:
            won_at = turn
            ended = "solved"
            break

    cands = list(UNIVERSE)
    for g, ex, pa in history:
        cands = [c for c in cands if feedback(c, g) == (ex, pa)]

    answered = [r for r in rows if r["guess"] is not None]
    return {
        "secret": list(secret),
        "guesses": [list(r["guess"]) for r in answered],
        "feedback": [[ex, pa] for _, ex, pa in history],
        "consistent": [r["consistent"] for r in answered],
        "consistent_all": all(r["consistent"] for r in answered) if answered else None,
        "solved": won_at is not None,
        "guesses_used": len(history),
        "distinct_guesses": len({tuple(r["guess"]) for r in answered}),
        "turns": len(rows),
        "no_answer": sum(1 for r in rows if r["guess"] is None),
        "strict": sum(1 for r in answered if r.get("route") == "strict"),
        "normalized": sum(1 for r in answered if r.get("route") == "normalized"),
        "raw": [r.get("raw") for r in answered],
        "tokens": [r.get("tokens") for r in answered],
        "secs": [r.get("secs") for r in answered],
        "finish": [r.get("finish") for r in answered],
        "content_empty": [r.get("content_empty") for r in answered],
        "remaining_candidates": len(cands),
        "ended": ended,
        "won_at": won_at,
        "state": {
            "ended": ended,
            "remaining_candidates": len(cands),
            "candidates_at_each_turn": cands_after,
            "candidates_before_each_turn": candidates_before_each_turn,
            "consistent_at_each_turn": [r["consistent"] for r in answered],
        },
    }


def rowset_digest(rows):
    """Canon shared with the peer's independent instrument:
    json.dumps([[secret, guesses, feedback, won_at], ...], sort_keys=True) -> sha256."""
    canon = json.dumps([[r["secret"], r["guesses"], r["feedback"], r["won_at"]]
                        for r in rows], sort_keys=True).encode()
    return hashlib.sha256(canon).hexdigest()


def summarize(rows, label, meta):
    n = len(rows)
    wins = [r["won_at"] for r in rows if r["won_at"]]
    answered = [c for r in rows for c in r["consistent"] if c is not None]
    cons = sum(1 for c in answered if c)
    trunc = sum(1 for r in rows for e in r["content_empty"] if e)
    finished = sum(r["finish"].count("length") for r in rows if r["finish"])
    distinct_all = len({tuple(g) for r in rows for g in r["guesses"]})
    print(f"\n=== {label} — {n} games, {SPACE} codes, limit {meta['limit']} ===")
    print(f"  instrument {meta['instrument']}  sha256 {meta['instrument_sha256'][:12]}")
    print(f"  fixture    {meta['fixture']}  sha256 {meta['fixture_sha256'][:12]}")
    print(f"  selector   {meta['selector']}")
    print(f"  prompt     inlined renderer  sha256 {meta['prompt_sha256'][:12]}"
          f"   round-trip checked every turn: {meta['prompt_roundtrip']}")
    print(f"  prompt     per-turn digests: " + " ".join(d[:8] for d in meta.get("prompt_digests_per_turn", [])))
    print(f"  digest     rowset sha256 {meta['rowset_sha256']}")
    print(f"  header     distinct answers {distinct_all} of {len(answered)} turns"
          f"   truncated/empty {trunc}   finish=length {finished}")
    print(f"  wins       {len(wins)}/{n}" + (f" = {100*len(wins)/n:.1f}%" if n else ""))
    if wins:
        print(f"             mean {sum(wins)/len(wins):.2f}   spread {sorted(wins)}")
    print(f"  answered   {len(answered)} turns   no_answer {sum(r['no_answer'] for r in rows)}"
          f"   strict {sum(r['strict'] for r in rows)}"
          f"   normalized {sum(r['normalized'] for r in rows)}")
    if answered:
        print(f"  CONSISTENCY {100*cons/len(answered):.1f}% of {len(answered)} answers"
              f"   (random 2.09% · consistent 100%)")
    print(f"  consistent stored-vs-recomputed disagreements: {stored_vs_recomputed_disagreements(rows)}")
    turn_nulls = [[] for _ in range(meta["limit"])]
    for r in rows:
        ns = per_state_nulls(r)
        for i, val in enumerate(ns):
            if i < len(turn_nulls):
                turn_nulls[i].append(val)
    if any(any(v) for v in turn_nulls):
        print("  null       per-state (mean over games, by turn): " +
              ", ".join(f"t{i+1}={ (sum(v)/len(v)) if v else 0:.4f}" for i, v in enumerate(turn_nulls)))
    return {"games": n, "wins": len(wins), "consistency": (cons / len(answered) if answered else None),
            "answered_turns": len(answered), "distinct_all": distinct_all,
            "truncated_or_empty": trunc, "finish_length": finished,
            "mean_guesses_when_won": (sum(wins) / len(wins) if wins else None),
            "stored_vs_recomputed_disagreements": stored_vs_recomputed_disagreements(rows)}


def main():
    ap = argparse.ArgumentParser(description="Mastermind 4x6 runner, single file, frozen chooser")
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--constant-guess", "--broken", action="store_true", dest="constant_guess")
    ap.add_argument("--control-block", action="store_true", help="run the in-process control block and exit")
    ap.add_argument("--no-control-block", action="store_true", help="skip the in-process control block")
    ap.add_argument("--base", default="http://127.0.0.1:8360")
    ap.add_argument("--model", default="ornith9b")
    ap.add_argument("--key", default=None)
    ap.add_argument("--limit", type=int, default=MAX_GUESSES)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--thinking-on", action="store_true")
    ap.add_argument("--raw-cap", type=int, default=400)
    ap.add_argument("--no-roundtrip-check", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    try:
        fixture = read_fixture(a.fixture)
    except SystemExit as e:
        print(f"FIXTURE REFUSED: {e}")
        return EXIT_FIXTURE
    fsha = sha256_file(a.fixture)
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    cb_result = None
    if not a.no_control_block:
        cb_result = run_control_block(fixture, a.limit, verbose=True)
        if a.control_block:
            return 0 if cb_result["passed"] else EXIT_CONTROL_FAILED
        if not cb_result["passed"]:
            print("\\n  CONTROL BLOCK FAILED — aborting row production")
            return EXIT_CONTROL_FAILED

    if a.control:
        def reply_fn(prompt):
            g, note, _n = consistent_choice(prompt)
            return g, {"route": "strict" if g else "none", "note": note, "raw": None}

        label = "CONTROL — scripted consistent player, frozen chooser (must be 100%)"
        selector = SELECTOR
    elif a.constant_guess:
        def reply_fn(prompt):
            g, note, _n = constant_guess_choice(prompt)
            return g, {"route": "constant-guess", "note": note, "raw": None}

        label = "BROKEN — constant guess (must score 0 on solvable boards)"
        selector = "constant guess (0,0,0,0) regardless of prompt"
    else:
        call = http_model(a.base, a.model, a.key, a.max_tokens, not a.thinking_on)

        def reply_fn(prompt):
            d = call(prompt)
            parsed = parse_guess(d["content"])
            g = parsed["strict"] or parsed["normalized"]
            return g, {"route": ("strict" if parsed["strict"] else
                                 "normalized" if parsed["normalized"] else "no_answer"),
                       "raw": (d["content"] or "")[:a.raw_cap],
                       "reasoning_chars": len(d["reasoning"]),
                       "finish": d["finish"], "secs": d["secs"],
                       "tokens": d["tokens"],
                       "content_empty": not d["content"].strip(),
                       "note": ""}

        label = f"MODEL {a.model} @ {a.base}  (max_tokens {a.max_tokens})"
        selector = "model reply (no scripted chooser); " + SELECTOR + " used only for --control"

    try:
        rows = [play_game(secret, reply_fn, a.limit, not a.no_roundtrip_check)
                for _, secret in fixture]
    except RuntimeError as e:
        print(f"PROMPT PATH BROKEN: {e}")
        return EXIT_PROMPT

    meta = {"instrument": "mastermind_run_onefile.py",
            "instrument_sha256": sha256_file(os.path.abspath(__file__)),
            "source_modules": {
                "engine": "mastermind_sim.py feedback/all_codes inlined verbatim",
                "prompt": "mastermind_prompt.py build_prompt/parse_* inlined verbatim",
                "http": "mastermind_probe.py http_model inlined verbatim"},
            "sys_path_manipulation": "none",
            "selector": selector,
            "fixture": os.path.basename(a.fixture), "fixture_sha256": fsha,
            "fixture_games": len(fixture),
            "model": None if a.control else a.model,
            "base": None if a.control else a.base,
            "max_tokens": a.max_tokens, "thinking": bool(a.thinking_on),
            "limit": a.limit, "control": bool(a.control),
            "prompt": "inlined build_prompt (no import)",
            "prompt_sha256": sha256_text(build_prompt([], 1, a.limit)),
            "prompt_digests_per_turn": per_turn_prompt_digests(a.limit),
            "prompt_roundtrip": "on" if not a.no_roundtrip_check else "off",
            "exit_status_policy": {"0": "self-checks passed", "2": "control < 100%",
                                   "3": "fixture refused", "4": "prompt round-trip failed",
                                   "5": "answered turn inconsistent with feedback already shown"},
            "started": started}
    meta["rowset_sha256"] = rowset_digest(rows)
    summary = summarize(rows, label, meta)
    meta["ended"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if a.out:
        with open(a.out, "w") as f:
            json.dump({"run": meta, "summary": summary, "rows": rows}, f, default=str, indent=1)
        print(f"  written {a.out}  sha256 {sha256_file(a.out)[:12]}")

    if a.control and summary["wins"] != len(fixture):
        print("\n  CONTROL FAILED — the harness is broken; no model number is valid")
        return EXIT_CONTROL_FAILED
    if a.constant_guess and summary["wins"] != 0:
        print("\n  BROKEN ARM FAILED — constant guess scored nonzero")
        return EXIT_CONTROL_FAILED
    inconsistent = [r for r in rows if r["consistent_all"] is False]
    if inconsistent:
        print(f"\n  {len(inconsistent)} game(s) contain an answered turn inconsistent with "
              f"feedback already shown — flagged, not hidden")
        return EXIT_INCONSISTENT
    if a.control:
        print("\n  CONTROL PASSED — fixture path is sound; a model number is now meaningful")
    if a.constant_guess:
        print("\n  BROKEN ARM PASSED — constant guess scored 0 on solvable boards")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
