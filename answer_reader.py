#!/usr/bin/env python3
"""THE ONE READER OF RECORD -- how an answer is read out of a chat-completion response.

RULING 79: *"the reader of record lives in the instrument of record, and every side-script imports it -- never
reimplements it. Two readers for one record is the one-definition defect applied to interpretation, and it
fails silently in the direction of a better-looking number."*

THIS FILE EXISTS BECAUSE OF A MEASURED FAILURE. The cabinet read answers correctly for days. A side-script I
wrote reimplemented the read as `content or reasoning_content` and then scored whatever its extraction found in
the result -- SO ON ONE ARM IT FOUND THE CODE INSIDE THE MODEL'S THINKING TRACE AND REPORTED 5/5, when the
model's actual answer was 1/5. Two readers, one record, and the wrong one flattered.

WHAT THE READER KNOWS THAT A CALLER MUST NOT RE-DERIVE:

  1  `content` IS THE ANSWER. Almost every entrant here puts its answer there.
  2  `reasoning_content` IS DELIBERATION. It is the only place a thinking model's text ever appears, so it is
     returned -- for DIAGNOSIS -- but it is NOT AN ANSWER, and code found inside it is code the model wrote
     while thinking, not code it committed to.
  3  A TURN CUT AT THE CEILING is a MISSING VALUE: the harness stopped it, the model did not fail.
  4  `finish_reason` DESCRIBES THE HARNESS, NOT THE MODEL. So it is reported, never interpreted by the caller.

    from answer_reader import read_answer        # NEVER reimplement this
"""
import json

# the ONLY legal values of `answer_field`. A caller switching on this should find no other.
FIELD_CONTENT = "content"
FIELD_REASONING = "reasoning_content"
FIELD_CAPPED_MISSING = "capped-deliberation-missing-value"
FIELD_ERROR = "error"
ALL_FIELDS = (FIELD_CONTENT, FIELD_REASONING, FIELD_CAPPED_MISSING, FIELD_ERROR)


def read_answer(response, *, exception=None):
    """-> dict(text, field, is_answer, is_deliberation_only, missing, finish_reason, completion_tokens)

    `is_answer` IS THE FIELD A SCORER MUST GATE ON. If it is False, THERE IS NO ANSWER TO SCORE, and a scorer
    that scores anyway is the defect this module exists to remove.
    """
    if exception is not None:
        return {"text": "", "field": FIELD_ERROR, "is_answer": False,
                "is_deliberation_only": False, "missing": True,
                "finish_reason": None, "completion_tokens": 0,
                "why": f"{type(exception).__name__}: {exception}"}

    ch = (response.get("choices") or [{}])[0]
    msg = ch.get("message") or {}
    content = (msg.get("content") or "").strip()
    reasoning = (msg.get("reasoning_content") or "").strip()
    finish_reason = ch.get("finish_reason")
    capped = finish_reason == "length"
    ctok = (response.get("usage") or {}).get("completion_tokens", 0)

    if content:
        return {"text": content, "field": FIELD_CONTENT, "is_answer": True,
                "is_deliberation_only": False, "missing": False,
                "finish_reason": finish_reason, "completion_tokens": ctok,
                "cap_cut": ("nothing -- the model stopped on its own" if not capped else
                            "SURPLUS AFTER AN ANSWER -- the answer is present and readable; the cap cut "
                            "what followed it. NOT a failed turn.")}

    if reasoning:
        # THE TRACE IS RETURNED AND LABELLED. It is NOT an answer, and NOTHING is scored from it.
        if capped:
            return {"text": "", "field": FIELD_CAPPED_MISSING, "is_answer": False,
                    "is_deliberation_only": True, "missing": True,
                    "finish_reason": finish_reason, "completion_tokens": ctok,
                    "trace_head": reasoning[:200],
                    "cap_cut": ("THE ANSWER -- deliberation consumed the ceiling before any answer was "
                                "reached. THIS IS THE ONE CASE WHERE `length` MEANS THE MODEL DID NOT ANSWER."),
                    "why": "the harness cut the turn before an answer existed"}
        return {"text": "", "field": FIELD_REASONING, "is_answer": False,
                "is_deliberation_only": True, "missing": True,
                "finish_reason": finish_reason, "completion_tokens": ctok,
                "trace_head": reasoning[:200],
                "cap_cut": "nothing -- the model stopped on its own",
                "why": "the model produced deliberation and NO ANSWER FIELD. THE TRACE IS NOT AN ANSWER: "
                       "code found inside it is code written while thinking, not code committed to."}

    return {"text": "", "field": FIELD_CONTENT, "is_answer": False,
            "is_deliberation_only": False, "missing": True,
            "finish_reason": finish_reason, "completion_tokens": ctok,
            "why": "the response carried neither an answer nor a trace"}


def self_test():
    """THE CONTROLS. A reader that has never been shown the failure it exists to prevent has not been tested."""
    cases = [
        # (name, response, expected field, expected is_answer)
        ("a plain answer",
         {"choices": [{"message": {"content": "R"}, "finish_reason": "stop"}]}, FIELD_CONTENT, True),
        ("an answer that was capped afterwards",
         {"choices": [{"message": {"content": "```python\nx=1"}, "finish_reason": "length"}]},
         FIELD_CONTENT, True),
        ("A CAP THAT CUT THE ANSWER",
         {"choices": [{"message": {"content": "", "reasoning_content": "Let me think about"},
                       "finish_reason": "length"}]}, FIELD_CAPPED_MISSING, False),
        ("A TRACE WITH NO CAP -- THE CASE THAT WAS SCORED AS 5/5",
         {"choices": [{"message": {"content": "", "reasoning_content":
                                   "Let me parse the requirements.\n```python\ndef counters(): ...```"},
                       "finish_reason": "stop"}]}, FIELD_REASONING, False),
        ("neither field",
         {"choices": [{"message": {}, "finish_reason": "stop"}]}, FIELD_CONTENT, False),
    ]
    bad, fails = 0, []
    for name, resp, want_field, want_answer in cases:
        got = read_answer(resp)
        ok = got["field"] == want_field and got["is_answer"] == want_answer
        if not ok:
            bad += 1
            fails.append(f"{name}: field={got['field']} is_answer={got['is_answer']}")
    # AND THE ONE THAT MATTERS MOST, STATED AS ITS OWN CONTROL: a trace must NEVER be scorable.
    t = read_answer({"choices": [{"message": {"content": "", "reasoning_content": "code ```def f()```"},
                                  "finish_reason": "stop"}]})
    if t["is_answer"]:
        bad += 1
        fails.append("A DELIBERATION TRACE WAS REPORTED AS AN ANSWER -- the exact failure this file removes")
    total = len(cases) + 1
    print(f"  answer_reader self-test: {total - bad}/{total}")
    for f in fails:
        print(f"    FAIL {f}")
    return bad == 0


if __name__ == "__main__":
    import sys
    print("=" * 100)
    print("THE READER OF RECORD -- self-test")
    print("=" * 100)
    print(json.dumps(read_answer({"choices": [{"message": {"content": "U"}, "finish_reason": "stop"}]}),
                     indent=1))
    sys.exit(0 if self_test() else 1)
