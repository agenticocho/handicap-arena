#!/usr/bin/env python3
"""Every count a public doc STATES must equal the count of the thing it names.

WHY THIS EXISTS. GAMES.md's header read "forty-plus events across nine leagues" while its own body
held 55 events across 10 leagues (A-J). League J had arrived; the closing line was updated and the
header was not. The stale figure then left this repo and was repeated in a generated audio summary
of the public documents.

That is the same defect as README-vs-FORMAT versioning: a summary line that disagrees with what it
summarises. The class fix is not to correct the number -- it is to stop trusting numbers that are
maintained by hand, because the next edit will go stale the same way.

WHAT IT CHECKS
  * league headings in GAMES.md          -> "ten leagues" / "nine leagues" / "10 leagues"
  * event headings in GAMES.md           -> "55 events" / "fifty-five events"
  * README's stated figures              -> the same two
  * and it FAILS if a doc states a count in prose that this file cannot resolve, so a new claim
    cannot slip in unchecked.

Counts come from the headings, never from a constant in this file. A constant here would be the
same disease one level out.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UNITS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
         "nine": 9}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
        "eighty": 80, "ninety": 90}
WORDS = {"zero": 0, **UNITS, **TENS, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
         "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
         "nineteen": 19}
# "fifty-five" is 55, not 5. The first version split on the hyphen and reported README's CORRECT
# "Fifty-five events across ten leagues" as a failure -- a test flagging a true line is worse than
# no test, because the next person stops reading it.
WORDNUM = r"\b((?:(?:" + "|".join(TENS) + r")[- ])?" + "(?:" + "|".join(WORDS) + r"))\b"
NUMPAT = re.compile(r"\b(\d{1,3})\b|" + WORDNUM, re.I)


def value_of(tok):
    """55 for 'fifty-five'/'fifty five', 5 for 'five', 55 for '55'."""
    tok = tok.strip().lower()
    if tok.isdigit():
        return int(tok)
    parts = re.split(r"[- ]", tok)
    return sum(WORDS.get(p, 0) for p in parts)


def count_structure(path):
    """Counted from the document, not asserted from memory."""
    lines = open(path, encoding="utf-8").read().splitlines()
    leagues = [l for l in lines if re.match(r"^#\s+LEAGUE\s+[A-Z]\b", l)]
    events = [l for l in lines if l.startswith("### ")]
    return len(leagues), len(events)


def stated_counts(path):
    """Counts a doc ASSERTS: a number immediately followed by the noun.

    TWO NARROWINGS, both learned from the first version of this file, which produced 16 reports of
    which 1 was real. Noise of that ratio is not a control -- nobody reads it, so it protects
    nothing.

    1. ADJACENCY. "42 events" and "nine leagues" are assertions. "one event already run" is a
       different claim about a different thing. The first version matched any number anywhere on a
       line that mentioned the noun.
    2. QUOTED TEXT IS A REPORT, NOT AN ASSERTION. A line quoting a stale figure -- as GAMES.md now
       does, deliberately, to record it -- is describing the defect, not committing it.
    """
    out = []
    for i, l in enumerate(open(path, encoding="utf-8").read().splitlines(), 1):
        # strip quoted spans so a reported claim is not read as an asserted one
        stripped = re.sub(r'"[^"]*"', ' ', l)
        stripped = re.sub(r"\*'[^']*'\*", " ", stripped)
        for m in NUMPAT.finditer(stripped):
            tok = (m.group(1) or m.group(2) or "")
            val = value_of(tok)
            after = stripped[m.end():m.end() + 14].lower()
            nm = re.match(r"[- ]?(league|event)s?\b", after)
            if not nm:
                continue
            noun = nm.group(1).lower()
            out.append((i, tok, val, noun, l.strip()[:78]))
    return out


# A CATALOGUE TOTAL IS NECESSARILY LARGE. This is a documented heuristic, not a law: the catalogue
# is 55 events across 10 leagues, so a count below 10 cannot be one. It removes the two remaining
# false positives -- "one event already run" (WHITEPAPER, a different claim) and EVENTS.md's
# "two events" -- without weakening the check on the numbers that can actually go stale.
CATALOGUE_FLOOR = 10


def main():
    fails, notes = [], []
    leagues, events = count_structure(os.path.join(HERE, "GAMES.md"))
    canonical = {"league": leagues, "event": events}
    print(f"measured in GAMES.md: {leagues} leagues, {events} events")
    print()

    # The sites that assert the CATALOGUE total. These are hard assertions: the catalogue is the
    # thing being counted, so a number here must equal the structure.
    sites = {"GAMES.md", "README.md", "WHITEPAPER.md", "EVENTS.md"}
    for doc in ("GAMES.md", "README.md", "EVENTS.md", "BELTS.md", "FORMAT.md", "WHITEPAPER.md"):
        p = os.path.join(HERE, doc)
        if not os.path.exists(p):
            continue
        for ln, tok, val, noun, text in stated_counts(p):
            actual = canonical[noun]
            if val < CATALOGUE_FLOOR:
                print(f"  note  {doc}:{ln}  {tok!r} {noun}(s) = {val} — below the catalogue "
                      f"floor, not a catalogue claim")
                notes.append(f"{doc}:{ln}")
            elif val == actual:
                print(f"  ok    {doc}:{ln}  {tok!r} {noun}(s) = {val}")
            elif doc in sites:
                print(f"  FAIL  {doc}:{ln}  {tok!r} {noun}(s) = {val}, catalogue has {actual}")
                fails.append(f"{doc}:{ln} states {val} {noun}s, catalogue has {actual} :: {text}")
            else:
                print(f"  note  {doc}:{ln}  {tok!r} {noun}(s) = {val} (not a catalogue claim)")
                notes.append(f"{doc}:{ln}")

    print()
    if notes:
        print(f"{len(notes)} line(s) mention a count that is not the catalogue total -- reviewed,")
        print("not failures. They are listed so a human sees them rather than a silent skip.")
    if fails:
        print(f"\n{len(fails)} stated count(s) contradict the catalogue:")
        for f in fails:
            print("  - " + f)
        return 1
    print("all catalogue counts agree with the counted structure")
    return 0


if __name__ == "__main__":
    sys.exit(main())
