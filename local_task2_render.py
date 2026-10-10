#!/usr/bin/env python3
"""TASK 2 -- A SECOND, DIFFERENTLY-SHAPED TASK. The capacity claim waits on one.

The Chair: *"he won't move three profiles on one task -- so it waits for a second, differently-shaped task."*

TASK 1 WAS: write code that CALLS a provided API. Its shape is logic --- take a position, apply tokens, count
                    outcomes.
TASK 2 IS:  write code that PRODUCES AN EXACT TEXT FORMAT from a data structure. Its shape is SERIALIZATION ---
                    no control flow to speak of, no API to consult for the answer, and it fails on a single
                    wrong character rather than on a wrong count.

DIFFERENT ENOUGH THAT PASSING BOTH IS NOT THE SAME AS PASSING ONE TWICE.

THREE THINGS IT INHERITS FROM THE RETRACTIONS, RATHER THAN RE-LEARNING THEM:
  1  THE READER OF RECORD IS IMPORTED (RULING 79). It scores `content` only; a trace is never an answer.
  2  THE SPEC IS DERIVED FROM THE MODULE'S OWN CONSTANTS, NOT TYPED. A format stated from memory of the code is
     the same defect as a field name stated from memory of the code -- the spec cannot drift from the thing it
     is checked against, because it is built by reading that thing.
  3  THE SETTING IS DECLARED AND IT IS OFF -- the Chair's re-taken ruling, sent as the chat-template switch
     because that travels with the request, and the request is the task.

    python3 local_task2_render.py [alias]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban as S                                                     # noqa: E402
import local_task_compare as L                                          # noqa: E402

ALIAS = sys.argv[1] if len(sys.argv) > 1 else "brain"


def build_prompt():
    """THE SPEC IS BUILT BY READING THE MODULE. If a glyph ever changes, this prompt changes with it."""
    return f"""You are writing one small Python function for a Sokoban measurement harness. Reply with the code only, in one fenced block, no explanation.

A position is already parsed for you and arrives as a dictionary with these keys, and you may read them directly.

There is a key named walls holding a set of coordinate pairs, one for each solid wall cell.
There is a key named boxes holding a set of coordinate pairs, one for each crate.
There is a key named targets holding a set of coordinate pairs, one for each target square.
There is a key named player holding a single coordinate pair, the player's cell.
There is a key named rows holding the number of rows as an integer.
There is a key named cols holding the number of columns as an integer.

Coordinates are pairs written row first, then column, and rows and columns both count from zero.

Write a function named render_position that takes a position and returns a single string: the board drawn as text. Rows are separated by a single newline character, and there is no newline after the last row. Each row is exactly cols characters long.

The character for a cell is decided in this order, and the first rule that matches wins. A cell that is a wall is written as the character {S.WALL!r}. Otherwise, a cell holding the player is written as {S.PLAYER_ON!r} if that cell is also a target, and as {S.PLAYER!r} if it is not. Otherwise, a cell holding a crate is written as {S.BOX_ON!r} if that cell is also a target, and as {S.BOX!r} if it is not. Otherwise, a cell that is a target is written as {S.TARGET!r}. Otherwise the cell is written as {S.FLOOR!r}.
"""


def cases():
    """-> [(name, state, expected)]. EXPECTED COMES FROM THE FROZEN IMPLEMENTATION, never from a hand-written
    literal -- a hand-written expectation is a second definition of the format, which is the defect this whole
    exercise is about."""
    out = []
    for lv in ("levels/01_one_push.txt", "levels/02_two_boxes.txt", "levels/03_the_corner_waiting.txt"):
        text = open(os.path.join(HERE, lv)).read()
        st = S.parse(text)
        out.append((f"{os.path.basename(lv)}:initial", st, S.render(st)))
        # AND EVERY INTERMEDIATE STATE of that level's verified solution, so the check is not five samples of
        # the same shape -- the interesting cells are the ones where a crate sits ON a target, or the player
        # does, and those only appear mid-solution.
        sol = VERIFIED.get(os.path.basename(lv), "")
        cur = st
        for i, a in enumerate(sol):
            nxt, outcome = S.step(cur, a)
            if outcome in ("moved", "pushed"):
                cur = nxt
            out.append((f"{os.path.basename(lv)}:after {sol[:i + 1]}", cur, S.render(cur)))
    return out


# THE VERIFIED SOLUTIONS, read from the verifier's own table rather than recalled.
VERIFIED = {"01_one_push.txt": "R", "02_two_boxes.txt": "RRRRDLLLDRRR",
            "03_the_corner_waiting.txt": "RULDLU"}


def main():
    prompt = build_prompt()
    print("=" * 100)
    print("TASK 2 -- a differently-shaped task: produce an EXACT TEXT FORMAT from a data structure")
    print("=" * 100)
    print(f"  alias    {ALIAS}")
    print(f"  setting  enable_thinking=false (the re-taken ruling: OFF, sent as the chat-template switch)")
    print(f"  spec     DERIVED from sokoban.py's own constants: "
          f"wall={S.WALL!r} player={S.PLAYER!r} player_on={S.PLAYER_ON!r} "
          f"box={S.BOX!r} box_on={S.BOX_ON!r} target={S.TARGET!r} floor={S.FLOOR!r}")
    cs = cases()
    print(f"  cases    {len(cs)} -- every intermediate state of the three verified solutions, "
          f"so the on-target glyphs are exercised")
    print()

    ans = L.ask(ALIAS, prompt, think_off=True, max_tokens=1200)
    print(f"  {ans['secs']}s  {ans['completion_tokens']} completion tokens  finish_reason={ans['finish_reason']}"
          f"  field={ans['field']}")
    if not ans["is_answer"]:
        print(f"  NO ANSWER TO SCORE -- {ans.get('why', ans['field'])}")
        if ans.get("cap_cut"):
            print(f"  cap_cut: {ans['cap_cut']}")
        print()
        print("  A NO-ANSWER IS NOT A FAILED TASK. It is a turn the harness could not read as an answer, and it")
        print("  is reported as exactly that.")
        return 3

    code = L.code_of(ans["text"])
    ns = dict(vars(S))
    try:
        exec(compile(code, "<model>", "exec"), ns)                      # noqa: S102
    except Exception as e:                                              # noqa: BLE001
        print(f"  DOES NOT COMPILE: {type(e).__name__}: {e}")
        print(f"   {code[:220]}")
        return 1
    fn = ns.get("render_position")
    if not callable(fn):
        print("  NO render_position FUNCTION DEFINED")
        return 1

    good, firstbad = 0, None
    for name, st, want in cs:
        try:
            got = fn(st)
        except Exception as e:                                          # noqa: BLE001
            got = f"RAISED {type(e).__name__}"
        if got == want:
            good += 1
        elif firstbad is None:
            firstbad = (name, got, want)
    print(f"  -> {good}/{len(cs)} cases match the FROZEN renderer exactly")
    if firstbad:
        name, got, want = firstbad
        print(f"  first disagreement on {name}:")
        print(f"    got : {got!r}")
        print(f"    want: {want!r}")
    print()
    print("  AND THE HONEST READING: one alias, one task, temperature 0 so it is DETERMINISTIC and reproducible")
    print("  rather than sampled. Two tasks of different shape passing is stronger than one task twice -- and")
    print("  it is still not a field.")

    json.dump({"alias": ALIAS, "setting": "enable_thinking=false", "cases": len(cs), "matched": good,
               "field": ans["field"], "completion_tokens": ans["completion_tokens"],
               "spec_derived_from_module": True,
               "prompt_digest": __import__("hashlib").sha256(prompt.encode()).hexdigest()[:16]},
              open(os.path.join(HERE, "probes", "TASK2_RENDER.json"), "w"), indent=1)
    return 0 if good == len(cs) else 1


if __name__ == "__main__":
    sys.exit(main())
