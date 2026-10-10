# sokoban_reader.py -- THE ONE READER OF RECORD.
#
# There is exactly one reader in this cabinet.  Every side script -- the
# simulator, the runner, the scorer, the solver, the tests -- IMPORTS this
# module.  None of them reimplements it.  Two readers for one record is a
# defect, and it fails toward the better-looking number.
#
# It implements SOKOBAN_READ_GRAMMAR.md, frozen.  Where the grammar does not
# speak, this module DECIDES, and every decision is (a) marked [G<n>] here,
# (b) restated in SOKOBAN2_AMBIGUITIES.md, and (c) written into the record by
# `grammar_as_record()` so a reader of a bundle can see which rule decided it.
#
# Stdlib only.  No imports from the rest of the cabinet: this file is the root
# of the dependency graph, not a leaf of it.

"""SOKOBAN READ-GRAMMAR -- one reader, imported, never reimplemented.

    read_answer(raw) -> Reading(outcome, action, line, why, raw, n_nonempty_lines)

    outcome in {"action", "give_up", "not_an_action"}
    action   in {"U","D","L","R",None}   -- upper-cased, only when outcome=="action"

The reader NEVER truncates.  `RESIGN` is not `R`.  See control `README` below.
"""

import re

# ---------------------------------------------------------------------------
# 1. THE ALPHABET -- frozen by SOKOBAN_READ_GRAMMAR.md section 1
# ---------------------------------------------------------------------------

ACTIONS = ("U", "D", "L", "R")

#: WASD are NOT synonyms.  They are letters, they are counted, and they are
#: `not_an_action`.  Named here so the fact is in the code, not in a comment
#: somewhere else.  (Grammar section 1.)
_WASD = frozenset(("W", "A", "S", "D"))

#: whitespace collapsing, used by `normalise` and by the token set below.
_WS = re.compile(r"\s+")

#: [G1] THE ABSTENTION TOKEN SET IS NOT DEFINED BY THE GRAMMAR.
#:
#: Grammar section 2 says `give_up` is "an explicit ABSTENTION" and calls it
#: SCOREABLE -- and section 3 uses `RESIGN` as its worked example of a word
#: that must NOT be truncated to `R`.  It never says what the token IS.
#:
#: This set is a DECLARATION, not a discovery.  It is written into every bundle
#: by `grammar_as_record()` so two implementations can be told apart.
#:
#: Matching is EXACT against the normalised line (casefold, internal
#: whitespace collapsed, outer whitespace stripped).  Punctuation is NOT
#: stripped: grammar section 1 lists "punctuation ... -> not_an_action", so
#: "GIVE UP." with a period is not_an_action here.  That fails CLOSED, and
#: failing closed on the abstention counter is a defensible direction but it
#: is a direction -- see [G1] in SOKOBAN2_AMBIGUITIES.md, and the diagnostic
#: `loose_give_up` below, which is recorded and NEVER scored.
GIVE_UP_TOKENS = (
    "GIVE UP", "GIVEUP", "GIVE UP.", "GIVE-UP", "GIVE_UP", "GIVING UP",
    "I GIVE UP", "I GIVE UP.", "RESIGN", "RESIGN.", "RESIGNS",
    "ABSTAIN", "ABSTAIN.", "NO MOVE", "NO_MOVE", "NO-MOVE",
    "UNSOLVABLE", "DEAD END", "STUCK",
)
# compared against the NORMALISED line, so the set must be normalised too.
_GIVE_UP_SET = frozenset(_WS.sub(" ", t).strip().casefold()
                         for t in GIVE_UP_TOKENS)

#: A DIAGNOSTIC ONLY -- never scored.  Substring test, so the record can show
#: how much abstention the strict rule loses.  A number that exists only in a
#: diagnostic is not a finding about the entrant; it is a finding about the
#: instrument, which is the point of carrying it.
_LOOSE_GIVE_UP = re.compile(
    r"\b(give\s*up|giving\s*up|resign|abstain|no\s+move|unsolvable|"
    r"dead\s*end|stuck|impossible)\b", re.I)


OUTCOME_ACTION = "action"
OUTCOME_GIVE_UP = "give_up"
OUTCOME_NOT_AN_ACTION = "not_an_action"

#: The four outcomes of grammar section 2, minus the two that `step()` owns.
#: An answer resolves to one of these three; `moved`/`pushed`/`blocked` are
#: produced by the simulator, downstream of this module.  The grammar's own
#: wording merges them ("moved / pushed" is one row) -- see [G4].
OUTCOMES = (OUTCOME_ACTION, OUTCOME_GIVE_UP, OUTCOME_NOT_AN_ACTION)


class Reading(object):
    """What one raw answer resolved to.  Immutable by convention."""

    __slots__ = ("outcome", "action", "line", "why", "raw", "n_nonempty_lines",
                 "loose_give_up")

    def __init__(self, outcome, action, line, why, raw, n_nonempty_lines,
                 loose_give_up=False):
        self.outcome = outcome
        self.action = action
        self.line = line
        self.why = why
        self.raw = raw
        self.n_nonempty_lines = n_nonempty_lines
        self.loose_give_up = loose_give_up

    @property
    def is_action(self):
        return self.outcome == OUTCOME_ACTION

    def as_record(self):
        return {
            "outcome": self.outcome,
            "action": self.action,
            "line_read": self.line,
            "why": self.why,
            "raw": self.raw,
            "n_nonempty_lines": self.n_nonempty_lines,
            "loose_give_up_diagnostic": self.loose_give_up,
        }

    def __repr__(self):
        return "Reading(%s, %r, why=%s)" % (self.outcome, self.action, self.why)


def normalise(line):
    """casefold + collapse internal whitespace + strip.  Punctuation KEPT."""
    return _WS.sub(" ", line).strip().casefold()


def read_answer(raw):
    """THE READER.  Take a raw answer and resolve it.  Never raises.

    `raw` is the entrant's entire answer for one turn.  Rules, in order:

      1. [G2] Split on newlines.  Drop empty/whitespace-only lines.  The answer
         is the FIRST remaining line if there is exactly one; if there are two
         or more non-empty lines the answer is `not_an_action` (multi_line) --
         the grammar says "exactly one action letter ... Nothing else on the
         line" and forbids truncation, so a multi-line emission is not a single
         answer and neither line may be preferred over the other.
      2. [G3] The chosen line is stripped of surrounding whitespace, so " U "
         reads as U.  A model emitting a trailing space is not abstaining.
      3. Exact match against GIVE_UP_TOKENS (normalised) -> give_up.
      4. len == 1 and upper() in {U,D,L,R} -> action.
      5. Anything else -> not_an_action, with a `why` that says which.

    There is no path that takes a prefix.  `RESIGN` -> give_up, never `R`.
    """
    if raw is None:
        return Reading(OUTCOME_NOT_AN_ACTION, None, None, "none_answer", None, 0)
    text = raw if isinstance(raw, str) else str(raw)

    lines = [ln for ln in text.splitlines() if ln.strip()]
    n = len(lines)
    loose = bool(_LOOSE_GIVE_UP.search(text))

    if n == 0:
        return Reading(OUTCOME_NOT_AN_ACTION, None, "", "empty_answer",
                       text, 0, loose)
    if n > 1:
        # [G2] two or more non-empty lines: refuse, do not pick one.
        return Reading(OUTCOME_NOT_AN_ACTION, None, lines[0], "multi_line",
                       text, n, loose)

    line = lines[0].strip()                      # [G3]
    norm = normalise(line)

    if norm in _GIVE_UP_SET:                     # [G1]
        return Reading(OUTCOME_GIVE_UP, None, line, "give_up_token",
                       text, n, loose)

    if len(line) == 1:
        up = line.upper()
        if up in ACTIONS:
            return Reading(OUTCOME_ACTION, up, line, "action_letter",
                           text, n, loose)
        if up in _WASD:
            # Grammar section 1: WASD are NOT synonyms.  Counted, never read.
            return Reading(OUTCOME_NOT_AN_ACTION, None, line,
                           "wasd_not_a_synonym", text, n, loose)
        return Reading(OUTCOME_NOT_AN_ACTION, None, line,
                       "single_char_not_an_action", text, n, loose)

    if len(line) == 0:
        return Reading(OUTCOME_NOT_AN_ACTION, None, line, "empty_answer",
                       text, n, loose)

    # More than one character.  NEVER truncate -- grammar section 3.
    why = "multi_char"
    if re.fullmatch(r"[\s]*[udlr][\s]*", line, re.I) and len(line.strip()) == 1:
        why = "action_letter"        # unreachable -- stated to prove the test
    return Reading(OUTCOME_NOT_AN_ACTION, None, line, why, text, n, loose)


def read_action(raw):
    """Convenience for scripts that want the letter or None.  Same reader."""
    return read_answer(raw).action


# ---------------------------------------------------------------------------
# 2. THE GRAMMAR AS A RECORD -- so a bundle says which rule decided it [A9]
# ---------------------------------------------------------------------------

def grammar_as_record():
    """The rules this reader applied, verbatim, for the bundle.

    A5/A9 lesson from darts: the notation grammar belongs IN THE RECORD, not in
    each side's head.  Two bundles read under different grammars are not the
    same measurement, and until the grammar is in the file nobody can tell.
    """
    return {
        "reader": "sokoban2/sokoban_reader.py",
        "reader_sha256": reader_sha256(),
        "grammar_source": "SOKOBAN_READ_GRAMMAR.md",
        "actions": list(ACTIONS),
        "case_insensitive": True,
        "wasd": "not_an_action (NOT synonyms) -- grammar section 1",
        "truncation": "NEVER. multi-char -> not_an_action. RESIGN is not R.",
        "give_up_tokens": list(GIVE_UP_TOKENS),
        "give_up_match": "EXACT on casefold + whitespace-collapsed line; "
                         "punctuation NOT stripped [G1]",
        "give_up_diagnostic": "loose_give_up is a substring test, RECORDED "
                              "ONLY and never scored [G1]",
        "line_rule": "answer is the single non-empty line; 2+ non-empty lines "
                     "-> not_an_action (multi_line), never one of them [G2]",
        "whitespace_rule": "the chosen line is stripped; ' U ' reads as U [G3]",
        "outcomes_read_here": list(OUTCOMES),
        "outcomes_owned_by_step": ["moved", "pushed", "blocked"],
    }


def reader_sha256():
    """Digest of THIS file.  The reader is part of the instrument."""
    import hashlib
    import os
    try:
        with open(os.path.abspath(__file__), "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None
