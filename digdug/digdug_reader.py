# digdug_reader.py -- THE ONE READER OF RECORD for the DIG DUG cabinet.
#
# There is exactly one reader in this cabinet.  Every side script -- the
# simulator, the runner, the scorer, the solver, the shadow readings, the tests
# -- IMPORTS this module.  None of them reimplements it.
#
# WHAT IT IMPLEMENTS.  DIG DUG ships with no read grammar from The Order: the
# brief hands over one prose paragraph and says the step() contract is the
# cabinet author's to write.  So the answer shape here is defined by
# `CONTRACT_digdug_v1.md` section A (THE ANSWER), which THIS cabinet wrote and
# froze before any entrant ran.  Standing rule R1 applies to that document:
#
#     R1  the abstention token list is FROZEN and the grammar's list must equal
#         the code's scored list.  Record which rule fired.  Loose-match is a
#         DIAGNOSTIC, never scored.
#
# Every one of those three clauses is enforced below or by a control that reads
# this file against the frozen document:
#   * FROZEN      -> CONTRACT_frozen.json carries the digest of the doc, and
#                    the runner REFUSES to run an entrant without a matching
#                    manifest.  "frozen before the run" is a gate, not a claim.
#   * LIST EQUALS -> self-test group [R1] parses the fenced token block out of
#                    CONTRACT_digdug_v1.md and asserts set equality with
#                    GIVE_UP_TOKENS below, and asserts equality with the
#                    sokoban2 cabinet's list (cross-cabinet parity, [R1-X]).
#   * WHICH RULE -> every Reading carries `rule`, the name of the clause that
#                    decided it, and it goes into every ply of every bundle.
#   * LOOSE      -> `_LOOSE_GIVE_UP` is a substring test carried in the record
#                    as `loose_give_up_diagnostic`.  It is NEVER scored and is
#                    NEVER folded into give_up.
#
# [D-STOP] THE WAIT TOKEN.  The prose never says whether the player may stop.
# It does not say it may not either.  `.` is therefore IN THE ALPHABET here,
# and stopping IS a turn (the hazards move).  Standing rule R3 is the reason
# this is a grammar question and not a game question: "only the read grammar
# states the ANSWER SHAPE", so if the game allows waiting and the alphabet does
# not contain `.`, the correct answer is a malformed answer -- a reading under
# which the correct answer is a FAILURE is a disproof of the spec.  An
# implementer that omitted WAIT would score a legal, optimal `.` as
# `not_an_action` and the run would report ERROR: ZERO MEASURED on a field of
# players who were answering correctly.
#
# Stdlib only.  No imports from the rest of the cabinet: this file is the root
# of the dependency graph, not a leaf of it.

"""DIG DUG READ GRAMMAR -- one reader, imported, never reimplemented.

    read_answer(raw) -> Reading(outcome, action, line, rule, raw,
                                n_nonempty_lines)

    outcome in {"action", "give_up", "not_an_action"}
    action   in {"U","D","L","R",".",None}  -- upper-cased, only when
                                             outcome == "action"

The reader NEVER truncates.  `GIVE UP` is not `G`.  `RRULL` is not `R`.
"""

import os
import re

# ---------------------------------------------------------------------------
# 1. THE ALPHABET -- frozen by CONTRACT_digdug_v1.md section A
# ---------------------------------------------------------------------------

#: The five legal answers.  WAIT is one of them.  [D-STOP]
ACTIONS = ("U", "D", "L", "R", ".")

#: The move letters, i.e. the alphabet minus WAIT.  The simulator needs the
#: distinction (WAIT moves nobody and digs nothing); the reader does not care.
MOVE_LETTERS = ("U", "D", "L", "R")

#: The wait letter, named so the fact is in the code and not in a comment.
WAIT = "."

#: [D-WASD] WASD ARE NOT SYNONYMS -- AND `D` IS A COLLISION, NOT A SYNONYM.
#:
#: The prose says nothing about WASD.  But look at what a synonym table would
#: have to do with `D`:  under UDLR, `D` is DOWN.  Under WASD, `D` is RIGHT.
#  Two implementers who both "accept WASD" therefore play DIFFERENT GAMES from
#: identical bytes, and -- unlike every other gap in this contract -- no
#: counter disagrees: `attempted`, `blocked`, `not_an_action` all match.  Only
#: the board moves somewhere else, silently, for the whole run.
#:
#: `A` and `S` are left and down under WASD and are not in this alphabet, so
#: they are counted and refused.  `D` is read as DOWN because DOWN is what the
#: frozen alphabet says, and the WASD reading of `D` is the rejected
#: alternative.  This is recorded in DIGDUG_DECISIONS.md [D-WASD] and measured
#: in digdug_readings.py (reading `wasd_synonyms`), because it is the single
#: most dangerous default in the whole paragraph: it is the one that cannot be
#: spotted from the record's counters.
_WASD = frozenset(("W", "A", "S"))

#: [D-XY] `X` and `Y` are not anything at all.  Named because a reader that
#: accepts them is accepting an un-frozen alphabet.
_OTHER_DIRECTION_KEYS = frozenset(("W", "A", "S", "X", "Y", "N", "E"))

_WS = re.compile(r"\s+")

#: [D-TOKENS] THE ABSTENTION TOKEN SET, FROZEN WITH THE CONTRACT.
#:
#: The prose does not mention abstention at all -- it is the standing rules
#: (R1) and the Sokoban precedent that force it, and this cabinet NEEDS it:
#: level 04 is provably unwinnable, so on that level the ONLY correct answer is
#: an abstention.  Which makes the token set the scoring surface for a whole
#: item, not a parsing convenience.
#:
#: The list is the CIRCUIT's list, carried over unchanged from
#: `sokoban2/sokoban_reader.py`, deliberately: one vocabulary for one circuit.
#: Two cabinets of the same circuit with two different abstention vocabularies
#: is a defect a reader cannot see from a table.  Control [R1-X] asserts it.
#:
#: Matching is EXACT against the normalised line (casefold, internal whitespace
#: collapsed, outer whitespace stripped).  Punctuation is NOT stripped, so
#: "GIVE UP." with a period is `not_an_action`.  That fails CLOSED, which is a
#: direction and not a neutral default -- see [D-TOKENS].
GIVE_UP_TOKENS = (
    "GIVE UP", "GIVEUP", "GIVE UP.", "GIVE-UP", "GIVE_UP", "GIVING UP",
    "I GIVE UP", "I GIVE UP.", "RESIGN", "RESIGN.", "RESIGNS",
    "ABSTAIN", "ABSTAIN.", "NO MOVE", "NO_MOVE", "NO-MOVE",
    "UNSOLVABLE", "DEAD END", "STUCK",
)
_GIVE_UP_SET = frozenset(_WS.sub(" ", t).strip().casefold()
                         for t in GIVE_UP_TOKENS)

#: A DIAGNOSTIC ONLY -- never scored, never folded into give_up.  It exists so
#: the amount of abstention the strict rule loses is VISIBLE in the record
#: rather than silent in two different files.
_LOOSE_GIVE_UP = re.compile(
    r"\b(give\s*up|giving\s*up|resign|abstain|no\s+move|unsolvable|"
    r"dead\s*end|stuck|impossible|cannot|can't)\b", re.I)

OUTCOME_ACTION = "action"
OUTCOME_GIVE_UP = "give_up"
OUTCOME_NOT_AN_ACTION = "not_an_action"

#: The three outcomes this reader can return.  `moved`/`dug`/`collected`/
#: `waited`/`blocked` are produced by the transition function, downstream
#: [D-STEP-SCOPE]; `killed` is produced by hazard resolution, which is not
#: step()'s business at all.  The prose lists six game facts and no vocabulary,
#: so the split between "what the reader says" and "what step() says" is a
#: decision, recorded as [D-WORDS].
OUTCOMES = (OUTCOME_ACTION, OUTCOME_GIVE_UP, OUTCOME_NOT_AN_ACTION)


class Reading(object):
    """What one raw answer resolved to.  Immutable by convention."""

    __slots__ = ("outcome", "action", "line", "rule", "why", "raw",
                 "n_nonempty_lines", "loose_give_up")

    def __init__(self, outcome, action, line, rule, why, raw,
                 n_nonempty_lines, loose_give_up=False):
        self.outcome = outcome
        self.action = action
        self.line = line
        #: `rule` names the CLAUSE of the frozen grammar that decided this
        #: reading, e.g. "A2.exact_single_letter".  R1: "record which rule
        #: fired".  It is not a free-text comment -- it is one of RULES below,
        #: and a control asserts every emitted rule name is declared.
        self.rule = rule
        self.why = why
        self.raw = raw
        self.n_nonempty_lines = n_nonempty_lines
        self.loose_give_up = loose_give_up

    @property
    def is_action(self):
        return self.outcome == OUTCOME_ACTION

    #: the rule names this reader can emit.  A control asserts
    #: set(emitted) <= set(declared), so a typo cannot invent a rule silently.
    RULES = (
        "A1.none_answer",
        "A1.empty_answer",
        "A1.multi_line",
        "A2.give_up_token",
        "A3.action_letter",
        "A3.wait_letter",
        "A4.wasd_not_a_synonym",
        "A4.single_char_not_in_alphabet",
        "A5.multi_char_never_truncated",
    )

    def as_record(self):
        return {
            "outcome": self.outcome,
            "action": self.action,
            "line_read": self.line,
            "rule": self.rule,
            "why": self.why,
            "raw": self.raw,
            "n_nonempty_lines": self.n_nonempty_lines,
            "loose_give_up_diagnostic": self.loose_give_up,
        }

    def __repr__(self):
        return "Reading(%s, %r, rule=%s)" % (self.outcome, self.action,
                                             self.rule)


def normalise(line):
    """casefold + collapse internal whitespace + strip.  Punctuation KEPT."""
    return _WS.sub(" ", line).strip().casefold()


def read_answer(raw):
    """THE READER.  Take a raw answer and resolve it.  Never raises.

    Rules, in the frozen order.  Every branch returns a `rule` naming itself,
    which is what R1's "record which rule fired" means in this cabinet.

      A1  split on newlines, drop blank lines.  Two or more non-empty lines is
          `not_an_action` (multi_line) -- never one of them, never a join.
      A2  exact match against the frozen give_up set -> give_up.
      A3  exactly one character in the alphabet -> action.  `.` is the WAIT
          letter and is an action, not a refusal.  [D-STOP]
      A4  one character NOT in the alphabet -> not_an_action, and W/A/S say so
          explicitly because they are the near-miss a model will produce.
      A5  more than one character -> not_an_action.  NEVER TRUNCATED.

    The order is itself a decision [D-ORDER]: give_up is tested BEFORE the
    single-letter test, so a future one-letter abstention token could never be
    shadowed by A3.  There is no such token today, and that is the point --
    the order is what keeps it that way.
    """
    if raw is None:
        return Reading(OUTCOME_NOT_AN_ACTION, None, None, "A1.none_answer",
                       "no answer at all", None, 0)
    text = raw if isinstance(raw, str) else str(raw)

    lines = [ln for ln in text.splitlines() if ln.strip()]
    n = len(lines)
    loose = bool(_LOOSE_GIVE_UP.search(text))

    if n == 0:
        return Reading(OUTCOME_NOT_AN_ACTION, None, "", "A1.empty_answer",
                       "empty answer", text, 0, loose)
    if n > 1:
        return Reading(OUTCOME_NOT_AN_ACTION, None, lines[0], "A1.multi_line",
                       "%d non-empty lines; the grammar states ONE answer per "
                       "turn and forbids picking" % n, text, n, loose)

    line = lines[0].strip()          # outer whitespace is not part of an answer
    norm = normalise(line)

    if norm in _GIVE_UP_SET:
        return Reading(OUTCOME_GIVE_UP, None, line, "A2.give_up_token",
                       "exact match on the frozen abstention list", text, n,
                       loose)

    if len(line) == 1:
        up = line.upper()
        if up == WAIT:
            return Reading(OUTCOME_ACTION, WAIT, line, "A3.wait_letter",
                           "the wait letter; stopping is a turn [D-STOP]",
                           text, n, loose)
        if up in MOVE_LETTERS:
            return Reading(OUTCOME_ACTION, up, line, "A3.action_letter",
                           "one letter from the frozen alphabet", text, n,
                           loose)
        if up in _WASD:
            return Reading(OUTCOME_NOT_AN_ACTION, None, line,
                           "A4.wasd_not_a_synonym",
                           "WASD are not in the alphabet; and D is DOWN here, "
                           "never RIGHT [D-WASD]", text, n, loose)
        return Reading(OUTCOME_NOT_AN_ACTION, None, line,
                       "A4.single_char_not_in_alphabet",
                       "one character, not in U D L R .", text, n, loose)

    # More than one character.  NEVER truncate.  `RRULL` is not `R`, and
    # `GIVE UP` was already caught by A2 above -- which is why A2 precedes A3
    # [D-ORDER]: if the letter test came first, a one-letter abstention token
    # could never exist, and the whole give_up counter would be hostage to the
    # order of two unrelated tests.
    return Reading(OUTCOME_NOT_AN_ACTION, None, line,
                    "A5.multi_char_never_truncated",
                    "%d characters; the first is never taken" % len(line),
                    text, n, loose)


def read_action(raw):
    """Convenience for scripts that want the letter or None.  Same reader."""
    return read_answer(raw).action


# ---------------------------------------------------------------------------
# 2. THE GRAMMAR AS A RECORD -- so a bundle says which rule decided it
# ---------------------------------------------------------------------------

def grammar_as_record():
    """The rules this reader applied, verbatim, for the bundle.

    A9 lesson from the darts cabinet, applied: the grammar belongs IN THE
    RECORD, not in each side's head.  Two bundles read under different grammars
    are not the same measurement.
    """
    return {
        "reader": "digdug/digdug_reader.py",
        "reader_sha256": reader_sha256(),
        "grammar_source": "digdug/CONTRACT_digdug_v1.md section A",
        "actions": list(ACTIONS),
        "wait": {"letter": WAIT, "is_a_turn": True,
                 "note": "WAIT is in the ALPHABET because the prose does not "
                         "settle whether the player may stop, and R3 puts the "
                         "answer shape in the grammar [D-STOP]."},
        "case_insensitive": True,
        "wasd": "not_an_action (NOT synonyms).  D is DOWN, never RIGHT "
                "[D-WASD] -- a synonym table would change the GAME without "
                "changing any counter.",
        "truncation": "NEVER.  multi-char -> not_an_action.  GIVE UP is not G.",
        "give_up_tokens": list(GIVE_UP_TOKENS),
        "give_up_match": "EXACT on casefold + whitespace-collapsed line; "
                         "punctuation NOT stripped [D-TOKENS]",
        "give_up_diagnostic": "loose_give_up is a substring test, RECORDED "
                              "ONLY, never scored, never folded into give_up "
                              "[R1]",
        "rule_precedence": "A1 line count, A2 give_up, A3 alphabet, "
                           "A4 near-miss, A5 multi-char  [D-ORDER]",
        "line_rule": "answer is the single non-empty line; 2+ non-empty lines "
                     "-> not_an_action (multi_line), never one of them",
        "whitespace_rule": "the chosen line is stripped; ' U ' reads as U",
        "outcomes_read_here": list(OUTCOMES),
        "outcomes_owned_by_transition": ["moved", "dug", "collected",
                                          "waited", "blocked"],
        "outcomes_owned_by_hazard_resolution": ["armed", "killed",
                                                "unharmed"],
        "rules_declared": list(Reading.RULES),
    }


def reader_sha256():
    """Digest of THIS file.  The reader is part of the instrument."""
    import hashlib
    try:
        with open(os.path.abspath(__file__), "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


def parse_give_up_tokens_from_contract(path):
    """Read the FROZEN contract and return the token list it declares.

    This exists so that R1's "the grammar's list must equal the code's scored
    list" is a CHECK and not a promise.  The block is the fenced section that
    starts with a line `give_up_tokens:` and lists one token per indented line.
    """
    with open(path) as fh:
        text = fh.read()
    blocks = re.findall(r"```[a-zA-Z0-9]*\ngive_up_tokens:\n(.*?)\n```",
                        text, re.S)
    if len(blocks) != 1:
        raise ValueError("expected exactly one `give_up_tokens:` fenced block "
                         "in %s, found %d" % (path, len(blocks)))
    toks = []
    for ln in blocks[0].splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        toks.append(s)
    return tuple(toks)
