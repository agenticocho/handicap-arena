#!/usr/bin/env python3
"""
Remove the terminology collision I introduced in GAMES.md.

THE COLLISION: "cabinet" in this repo already means an ARCADE CABINET -- a self-contained game
with frozen criteria, owned by one cabinet agent, living in its own git worktree
(cabinet/sokoban, cabinet/missile-command, cabinet/zork). There are ~2100 uses. GAMES.md:166
already used it correctly ("which cabinet's oracle can decide it").

In League K I used "cabinet" to mean something completely different: a frozen perceptual layer
that describes an image to a text-only entrant. That put two conflicting meanings in ONE file.

THE STANDARD TERM: SENSOR. A declared, frozen perceptual channel attached to an entrant. It
describes and does not conclude, and it must FAIL the task alone -- otherwise the event measures
the sensor rather than the entrant. "Assisted play" remains the mode; the sensor is the component.

SCOPE IS ENFORCED. This only edits the League K span. Line 166's correct usage of "cabinet" must
survive, and the script asserts it does.
"""
import re, sys

PATH = "/home/chilly1/workspace/ocho_arena/GAMES.md"
start_marker = "# LEAGUE K —"
end_marker = "# PART 3 — THE NULL-BASELINE CATALOGUE"

text = open(PATH, encoding="utf-8").read()
lines = text.split("\n")

start = next((i for i, l in enumerate(lines) if l.startswith(start_marker)), None)
end = next((i for i, l in enumerate(lines) if l.startswith(end_marker)), None)
if start is None or end is None or end <= start:
    sys.exit(f"could not bound the League K span (start={start} end={end})")

span = lines[start:end]
before = sum(l.count("cabinet") + l.count("Cabinet") for l in span)
print(f"League K span: lines {start+1}..{end}  ({len(span)} lines)")
print(f"  'cabinet' occurrences inside the span: {before}")

# prove the CORRECT usage is outside the span
outside = [(i + 1, l) for i, l in enumerate(lines) if i < start or i >= end
           if "cabinet" in l.lower()]
print(f"  correct uses OUTSIDE the span (must survive): {len(outside)}")
for n, l in outside[:4]:
    print(f"    :{n}  {l.strip()[:88]}")

new_span = [l.replace("Cabinet", "Sensor").replace("cabinet", "sensor") for l in span]
after = sum(l.count("sensor") + l.count("Sensor") for l in new_span)
print(f"  after replacement, 'sensor' occurrences inside the span: {after}")

out = "\n".join(lines[:start] + new_span + lines[end:])

# the standard, recorded where the term is used
note = """
> **TERMINOLOGY (standardised 2026-10-07).** In this repository **"cabinet" means an ARCADE
> CABINET** — a self-contained game with frozen criteria, owned by one cabinet agent, in its own
> git worktree (`cabinet/sokoban`, `cabinet/missile-command`, `cabinet/zork`). It is NOT used here
> for anything else.
>
> The assistive layer in this league is a **SENSOR**: a declared, frozen perceptual channel
> attached to an entrant. It describes and does not conclude, and it **must fail the task alone** —
> otherwise the event measures the sensor rather than the entrant. *"Assisted play"* is the mode;
> the sensor is the component. The seeing-eye-dog metaphor is the informal gloss.
>
> A sensor is **not** part of a cabinet's machinery, and a cabinet is **not** a sensor. Two
> different things, two different words, deliberately.
"""
anchor = "\n## The one failure mode that would ruin this league"
assert anchor in out, "anchor paragraph missing — refusing to write"
out = out.replace(anchor, note + anchor, 1)

open(PATH, "w", encoding="utf-8").write(out)

# verify
check = open(PATH, encoding="utf-8").read().split("\n")
s2 = next(i for i, l in enumerate(check) if l.startswith(start_marker))
e2 = next(i for i, l in enumerate(check) if l.startswith(end_marker))
inside = sum(l.lower().count("cabinet") for l in check[s2:e2])
outside2 = sum(1 for i, l in enumerate(check) if (i < s2 or i >= e2) and "cabinet" in l.lower())
print()
print(f"VERIFY  'cabinet' inside League K : {inside}   (must be 0)")
print(f"VERIFY  'cabinet' outside League K: {outside2}  (must be unchanged)")
print(f"VERIFY  terminology note present  : {'TERMINOLOGY (standardised' in open(PATH).read()}")
if inside or outside2 != len(outside):
    sys.exit("*** VERIFICATION FAILED ***")
print("OK — collision removed, correct usage intact")
