# digdug_reader.py -- THE ONE READER OF RECORD for the DIG DUG cabinet.
#
# There is exactly one reader in this cabinet.  Every side script -- the
# simulator, the solver, the runner, the scorer, the freeze tool, the side
# test -- IMPORTS this module.  None of them reimplements it.  Two readers
# for one record is a defect, and it fails toward the better-looking number.
#
# WHY THIS FILE EXISTS AT ALL: the DIG DUG prose (CONTRACT_DIGDUG.md section
# 1) describes a GAME.  It says nothing at all about what an ANSWER looks
# like.  Standing rule R3 says only the read grammar states the ANSWER SHAPE,
# and standing rule R1 says the abstention token list is FROZEN and that the
# grammar's list must EQUAL the code's scored list.  So this file is the read
# grammar, it is the only place the token list exists in code, and
# `contract_agrees_with_code()` below proves the document and the code agree
# by reading the document.  A list that lives in two places is two lists.
#
# Stdlib only.  No imports from the rest of the cabinet: this file is the
# root of the dependency graph, not a leaf of it.

"""DIG DUG READ-GRAMMAR -- one reader, imported, never reimplemented.

    read_answer(raw) -> Reading(outcome, action, line, rule_fired, ...)

    outcome in {"action", "give_up", "not_an_action"}
    action  in {"U","D","L","R",None}   -- upper-cased, only when outcome=="action"

The reader NEVER truncates.  `RESIGN` is not `R`.  `RR` is not `R`.
"""

import hashlib
import os
import re

# ---------------------------------------------------------------------------
# 1. THE ANSWER SHAPE -- [A12] declared here, because the prose does not
#    contain it.  One answer per turn (standing rule R3).
# ---------------------------------------------------------------------------

ACTIONS = ("U", "D", "L", "R")

#: WASD are NOT synonyms.  They are letters, they are counted, and they are
#: `not_an_action`.  Named here so the fact is in the code, not in a comment
#: somewhere else.  A model that plays WASD is not abstaining; it is playing
#: a different alphabet, and the record must say so rather than read `W` as
#: `U` because that looked helpful.
_WASD = frozenset(("W", "A", "S", "D"))

#: [U5] THERE IS NO "WAIT".  The prose never says whether the player may
#: stop, and the brief names that gap.  DECIDED: the player may not pass.
#: A turn is a move or an
#: abstention, and an abstention ENDS the attempt.  Rejected alternative:
#: a WAIT token that costs a turn -- under a lockstep hazard clock a WAIT
#: changes nothing except the budget, and it turns every level into a
#: stalling game where the only termination is the cap.  Recorded, and
#: `WAIT` in the answer stream is therefore `not_an_action`, with a rule
#: name that says exactly that, so the divergence is visible in the record.
WAIT_WORDS = frozenset(w.casefold() for w in
                       ("WAIT", "WAIT.", "STAY", "STAY.", "HOLD", "HOLD.",
                        "PASS", "PASS.", "SKIP", "NO MOVE TURN", "."))

_WS = re.compile(r"\s+")

# ---------------------------------------------------------------------------
# 2. THE ABSTENTION TOKEN LIST -- FROZEN.  [A11] / standing rule R1
# ---------------------------------------------------------------------------
#
#: The prose never mentions abstaining at all.  The cabinet needs it anyway:
#: level 04 has NO safe line (proven by exhaustive search), so the only
#: correct answer on that level is to stop, and an instrument that cannot
#: read "stop" records a correct answer as a malformed one.  That is the
#: exact shape of failure standing rule R3 calls a disproof of the spec.
#:
#: This list is the UNION of the two lists the two Sokoban implementations
#: froze for themselves.  Those two lists agreed on 3 tokens out of 22
#: probes: {RESIGN, RESIGNS, GIVEUP}.  Everything else a model might say to
#: mean "I cannot finish this" was an abstention in exactly one of them.  A
#: union is a decision, not a discovery, and it is recorded here and in every
#: bundle so two cabinets can be told apart.
#:
#: Matching is EXACT against the normalised line (casefold, internal
#: whitespace collapsed, outer whitespace stripped).  Punctuation is NOT
#: stripped except where the punctuated form is itself listed: "GIVE UP." is
#: in the list, "GIVE UP!" is not, and that is `not_an_action`.  Failing
#: closed on the abstention counter is a direction; it is recorded, and the
#: loose diagnostic below measures what the strict rule costs.
GIVE_UP_TOKENS = (
    # -- carried over from the frozen Sokoban reader --
    "RESIGN", "RESIGNS", "RESIGNED", "GIVEUP", "SURRENDER",
    "IQUIT", "QUIT", "FORFEIT",
    # -- carried over from the second Sokoban implementation --
    "GIVE UP", "GIVE UP.", "GIVE-UP", "GIVE_UP", "GIVING UP",
    "I GIVE UP", "I GIVE UP.", "ABSTAIN", "ABSTAIN.",
    "NO MOVE", "NO_MOVE", "NO-MOVE",
    "UNSOLVABLE", "DEAD END", "STUCK",
    # -- added here, with the reason for each --
    "IMPOSSIBLE",       # the word a model uses for a level with no safe line
    "NO SAFE LINE",     # the cabinet's own phrase; level 04 is exactly this
    "CANNOT SOLVE", "CANNOT SOLVE.", "CAN NOT SOLVE",
    "I STOP", "STOP", "STOP.",
)
_GIVE_UP_SET = frozenset(_WS.sub(" ", t).strip().casefold()
                         for t in GIVE_UP_TOKENS)

#: A DIAGNOSTIC ONLY -- never scored, never in a denominator, never in a
#: verdict.  Substring test, so the record can show how much abstention the
#: strict rule loses.  A number that exists only in a diagnostic is a finding
#: about the INSTRUMENT, not about the entrant, and that is the point of
#: carrying it separately.
_LOOSE_GIVE_UP = re.compile(
    r"\b(give\s*up|giving\s*up|gave\s*up|resign\w*|surrender\w*|forfeit\w*|"
    r"quit\w*|abstain\w*|no\s+move|unsolvable|impossible|dead\s*end|stuck|"
    r"cannot\s+(?:be\s+)?solve?d?|can\s?not\s+solve|no\s+safe\s+line|"
    r"i\s+stop)\b", re.I)

OUTCOME_ACTION = "action"
OUTCOME_GIVE_UP = "give_up"
OUTCOME_NOT_AN_ACTION = "not_an_action"

OUTCOMES = (OUTCOME_ACTION, OUTCOME_GIVE_UP, OUTCOME_NOT_AN_ACTION)

#: The words step() can say.  `give_up` and `not_an_action` never reach the
#: transition function: they are resolved here, before an action exists.
STEP_WORDS = ("dug", "moved", "blocked", "collected")
TURN_WORDS = STEP_WORDS + ("killed",)


class Reading(object):
    """What one raw answer resolved to.  Immutable by convention."""

    __slots__ = ("outcome", "action", "line", "rule_fired", "raw",
                 "n_nonempty_lines", "loose_give_up")

    def __init__(self, outcome, action, line, rule_fired, raw,
                 n_nonempty_lines, loose_give_up=False):
        self.outcome = outcome
        self.action = action
        self.line = line
        self.rule_fired = rule_fired
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
            # standing rule R1: RECORD WHICH RULE FIRED.  Not "why" -- the
            # name of the rule, so two readers can be diffed by rule name.
            "rule_fired": self.rule_fired,
            "raw": self.raw,
            "n_nonempty_lines": self.n_nonempty_lines,
            "loose_give_up_diagnostic": self.loose_give_up,
        }

    def __repr__(self):
        return "Reading(%s, %r, rule=%s)" % (self.outcome, self.action,
                                             self.rule_fired)


def normalise(line):
    """casefold + collapse internal whitespace + strip.  Punctuation KEPT."""
    return _WS.sub(" ", line).strip().casefold()


def read_answer(raw):
    """THE READER.  Take a raw answer and resolve it.  Never raises.

    `raw` is the entrant's entire answer for ONE turn (R3).  Rules, in order,
    each one named in `rule_fired`:

      1. `none_answer`            -- raw is None.
      2. `empty_answer`           -- no non-empty line at all.
      3. `multi_line`             -- 2+ non-empty lines.  Refuse; never pick
                                      one.  A plan is not an answer, and
                                      taking the first line would score a
                                      five-move plan as one move.
      4. `give_up_token_exact`    -- exact match against the FROZEN list.
      5. `action_letter`          -- exactly one character in U/D/L/R (case
                                      insensitive; surrounding whitespace
                                      already stripped at step 3).
      6. `wasd_not_a_synonym`     -- one character in W/A/S/D.
      7. `wait_is_not_an_action`  -- a WAIT-shaped word [U5].
      8. `single_char_not_an_action` / `multi_char_no_truncation` -- else.

    There is no path that takes a prefix.  `RESIGN` -> give_up, never `R`.
    """
    if raw is None:
        return Reading(OUTCOME_NOT_AN_ACTION, None, None, "none_answer",
                       None, 0)
    text = raw if isinstance(raw, str) else str(raw)

    lines = [ln for ln in text.splitlines() if ln.strip()]
    n = len(lines)
    loose = bool(_LOOSE_GIVE_UP.search(text))

    if n == 0:
        return Reading(OUTCOME_NOT_AN_ACTION, None, "", "empty_answer",
                       text, 0, loose)
    if n > 1:
        return Reading(OUTCOME_NOT_AN_ACTION, None, lines[0], "multi_line",
                       text, n, loose)

    line = lines[0].strip()
    norm = normalise(line)

    if norm in _GIVE_UP_SET:
        return Reading(OUTCOME_GIVE_UP, None, line, "give_up_token_exact",
                       text, n, loose)

    if len(line) == 1:
        up = line.upper()
        if up in ACTIONS:
            return Reading(OUTCOME_ACTION, up, line, "action_letter",
                           text, n, loose)
        if up in _WASD:
            return Reading(OUTCOME_NOT_AN_ACTION, None, line,
                           "wasd_not_a_synonym", text, n, loose)
        return Reading(OUTCOME_NOT_AN_ACTION, None, line,
                       "single_char_not_an_action", text, n, loose)

    if norm in WAIT_WORDS:
        return Reading(OUTCOME_NOT_AN_ACTION, None, line,
                       "wait_is_not_an_action", text, n, loose)

    return Reading(OUTCOME_NOT_AN_ACTION, None, line,
                   "multi_char_no_truncation", text, n, loose)


def read_action(raw):
    """Convenience for scripts that want the letter or None.  Same reader."""
    return read_answer(raw).action


# ---------------------------------------------------------------------------
# 3. THE GRAMMAR AS A RECORD -- so a bundle says which rule decided it
# ---------------------------------------------------------------------------

def grammar_as_record():
    """The rules this reader applied, verbatim, for the bundle.

    Two bundles read under different grammars are not the same measurement,
    and until the grammar is IN the file nobody can tell.
    """
    return {
        "reader": "digdug/digdug_reader.py",
        "reader_sha256": reader_sha256(),
        "grammar_source": "digdug/CONTRACT_DIGDUG.md section 2 (READ GRAMMAR)",
        "answer_shape": "ONE token per turn (standing rule R3).  A plan, a "
                        "sentence, or two lines is not_an_action.",
        "actions": list(ACTIONS),
        "case_insensitive": True,
        "wasd": "not_an_action (NOT synonyms) -- rule wasd_not_a_synonym",
        "wait": "not_an_action -- there is NO pass action [U5]",
        "truncation": "NEVER. multi-char -> not_an_action. RESIGN is not R.",
        "give_up_tokens": list(GIVE_UP_TOKENS),
        "give_up_token_count": len(GIVE_UP_TOKENS),
        "give_up_match": "EXACT on casefold + whitespace-collapsed line; "
                         "punctuation NOT stripped except where the "
                         "punctuated form is itself listed [A11]",
        "give_up_diagnostic": "loose_give_up is a substring test, RECORDED "
                              "ONLY and never scored [A11/R1]",
        "line_rule": "the answer is the single non-empty line; 2+ non-empty "
                     "lines -> not_an_action (multi_line), never one of them",
        "whitespace_rule": "the chosen line is stripped; ' U ' reads as U",
        "outcomes_read_here": list(OUTCOMES),
        "outcomes_owned_by_step": list(STEP_WORDS),
        "outcomes_owned_by_turn": list(TURN_WORDS),
    }


def reader_sha256():
    """Digest of THIS file.  The reader is part of the instrument."""
    try:
        with open(os.path.abspath(__file__), "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


# ---------------------------------------------------------------------------
# 4. R1 -- THE GRAMMAR'S LIST MUST EQUAL THE CODE'S SCORED LIST
# ---------------------------------------------------------------------------
#
# Standing rule R1 is not satisfied by writing the same list twice.  It is
# satisfied by a check that reads the DOCUMENT and compares it to the code,
# so that a token added to one and not the other fails loudly instead of
# silently changing what an abstention is.

_TOKEN_BLOCK_START = "<!-- ABSTENTION-TOKENS:START -->"
_TOKEN_BLOCK_END = "<!-- ABSTENTION-TOKENS:END -->"


def contract_token_list(contract_path):
    """Extract the frozen token list from the CONTRACT, or None.

    The contract carries the list inside a marked block, one token per line,
    in backticks.  This function is the only reader of that block, and the
    block is generated FROM this module by `freeze.py --write-tokens`, so the
    document cannot drift -- and if somebody edits it by hand anyway, the
    comparison below says so.
    """
    try:
        with open(contract_path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    if _TOKEN_BLOCK_START not in text or _TOKEN_BLOCK_END not in text:
        return None
    body = text.split(_TOKEN_BLOCK_START, 1)[1].split(_TOKEN_BLOCK_END, 1)[0]
    toks = []
    for ln in body.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        m = re.match(r"^`(.+)`\s*$", ln)
        if m:
            toks.append(m.group(1))
    return toks


def token_list_is_unique(tokens):
    """Standing rule B3: a validator validates UNIQUENESS, not only COUNT.

    A token list can be the right LENGTH and still be broken: a duplicate
    makes `count` lie, and a token that normalises onto another one makes
    two rules fire for one answer.  Both are checked here, and both are
    controls in the self-test.
    """
    problems = []
    seen_raw = {}
    seen_norm = {}
    for t in tokens:
        if t in seen_raw:
            problems.append("duplicate token %r" % t)
        seen_raw[t] = True
        n = normalise(t)
        if n in seen_norm:
            problems.append("token %r normalises onto %r" % (t, seen_norm[n]))
        seen_norm[n] = t
        if len(t) == 1 and t.upper() in ACTIONS:
            problems.append("token %r collides with an action letter" % t)
    return problems


def contract_agrees_with_code(contract_path):
    """R1, measured.  -> (agrees: bool, detail: dict)"""
    doc = contract_token_list(contract_path)
    detail = {
        "contract_path": contract_path,
        "code_tokens": list(GIVE_UP_TOKENS),
        "code_count": len(GIVE_UP_TOKENS),
        "uniqueness_problems": token_list_is_unique(GIVE_UP_TOKENS),
    }
    if doc is None:
        detail["agrees"] = False
        detail["why"] = "the contract has no marked abstention-token block"
        return False, detail
    detail["contract_count"] = len(doc)
    detail["in_code_not_contract"] = [t for t in GIVE_UP_TOKENS if t not in doc]
    detail["in_contract_not_code"] = [t for t in doc if t not in GIVE_UP_TOKENS]
    detail["uniqueness_problems_contract"] = token_list_is_unique(doc)
    agrees = (not detail["in_code_not_contract"]
              and not detail["in_contract_not_code"]
              and not detail["uniqueness_problems"]
              and not detail["uniqueness_problems_contract"])
    detail["agrees"] = agrees
    detail["why"] = ("lists equal and unique" if agrees else
                     "THE LISTS DIFFER -- a token exists in one place only")
    return agrees, detail
