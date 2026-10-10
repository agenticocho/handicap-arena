#!/usr/bin/env python3
"""DUMP THE RAW ANSWER, so a failure is attributed to whatever actually caused it.

I AM DOING THIS BECAUSE I ALREADY MADE THIS EXACT MISTAKE ONCE TODAY. Task 2's output did not compile, and the
honest first question is NOT "can the model not do it" -- it is "DID MY EXTRACTION CUT THE ANSWER". The last
time I skipped that question I published a 5/5 that came from a thinking trace.

So this prints the RAW text, its length, the finish_reason, and the extracted code side by side, and it does not
score anything.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import local_task_compare as L                                          # noqa: E402
import local_task2_render as T                                          # noqa: E402

alias = sys.argv[1] if len(sys.argv) > 1 else "brain"
prompt = T.build_prompt()
ans = L.ask(alias, prompt, think_off=True, max_tokens=1200)

print("=" * 100)
print("THE RAW ANSWER -- no scoring, no interpretation")
print("=" * 100)
print(f"  finish_reason       {ans['finish_reason']}")
print(f"  field               {ans['field']}")
print(f"  completion_tokens   {ans['completion_tokens']}")
print(f"  is_answer           {ans['is_answer']}")
print(f"  RAW TEXT LENGTH     {len(ans['text'])} chars")
print()
print("  ---- RAW TEXT, BEGINNING ----")
for line in ans["text"][:600].splitlines():
    print(f"    {line}")
print("  ---- RAW TEXT, END ----")
print(f"    ...{ans['text'][-200:]!r}" if len(ans["text"]) > 600 else "")
print()
code = L.code_of(ans["text"])
print(f"  ---- EXTRACTED CODE ({len(code)} chars, {len(code.splitlines())} lines) ----")
print(f"  fenced blocks in the raw text: {ans['text'].count('```')}")
print()
for line in code.splitlines()[-6:]:
    print(f"    {line}")
print()
# THE QUESTION THAT MATTERS: DID THE EXTRACTION LOSE ANYTHING THE MODEL SENT?
print(f"  DOES THE RAW TEXT END ITS FENCE?   {ans['text'].rstrip().endswith('```')}")
print(f"  IS THE EXTRACTED CODE A PREFIX OF THE RAW TEXT?  {code.strip() in ans['text']}")
print()
print("  AND THE READING: if the raw text is itself unterminated, THE MODEL STOPPED MID-ANSWER and that is a")
print("  real failure. If the raw text is complete and the extraction cut it, THE FAILURE IS MINE.")
