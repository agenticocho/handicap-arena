#!/usr/bin/env python3
"""diag_mimo_noanswer.py — DIAGNOSTIC, NOT A ROW.

The Mastermind run files `no_answer` counts but the harness only stores `raw` for ANSWERED turns
(mastermind_run_onefile.play_game builds `raw` from `answered`), so the text that failed to parse is
dropped at the source. This probe replays one game with the harness's OWN build_prompt/feedback/
http_model and prints every turn's full response, so the failure can be named instead of guessed.

It files no rows and changes no instrument: it calls the same functions on a private server, then
releases the card.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S  # noqa: E402
sys.path.insert(0, os.path.join(S.ROOT, "probes/mastermind"))
import mastermind_run_onefile as mm  # noqa: E402

SECRET = (2, 3, 0, 1)   # game 2 of the fixture: ended 'no_answer' at turn 2 in the filed run
LIMIT = 10


def main():
    baseline = S.gpu_used_mib()
    lease = S.start_entrant("mimo-9b", 99)
    if not lease["ok"]:
        print("admission failed", lease.get("tail"))
        return 1
    rec = {"diagnostic": "mimo-9b mastermind no_answer replay", "secret": list(SECRET),
           "compute_path": S.compute_path(lease, "mimo-9b", 99, 8192), "turns": []}
    try:
        call = mm.http_model(S.BASE, "mimo-9b", None, 512, True)
        history = []
        for turn in range(1, LIMIT + 1):
            prompt = mm.build_prompt(history, turn, LIMIT)
            d = call(prompt)
            parsed = mm.parse_guess(d["content"])
            guess = parsed["strict"] or parsed["normalized"]
            rec["turns"].append({"turn": turn, "content": d["content"], "reasoning_chars": len(d["reasoning"]),
                                 "finish": d["finish"], "tokens": d["tokens"], "secs": d["secs"],
                                 "parsed": list(guess) if guess else None,
                                 "raw_is_empty": not (d["content"] or "").strip()})
            print(f"turn {turn}: guess={guess} finish={d['finish']} tokens={d['tokens']} "
                  f"reasoning_chars={len(d['reasoning'])} content={d['content']!r}"[:400], flush=True)
            if guess is None:
                rec["stopped_at"] = turn
                break
            ex, pa = mm.feedback(SECRET, guess)
            history.append((guess, ex, pa))
    finally:
        rec["release"] = S.stop_entrant(lease, baseline)
    out = os.path.join(S.ROOT, "suite", "runs", "DIAGNOSTIC_mimo-9b_noanswer.json")
    with open(out, "w") as f:
        json.dump(rec, f, indent=1)
    print("release:", json.dumps(rec["release"]))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
