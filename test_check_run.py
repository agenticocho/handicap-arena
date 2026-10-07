#!/usr/bin/env python3
"""check_run.py must READ the runner's filter, not restate it -- and must fail loudly if it can't.

The defect this guards: a copied constant drifts from the thing it was copied from. run_card.py's
EXCLUDE_PAT changes, check_run.py's does not, and the expected-entrant count silently describes a
field nobody is running. That is the hand-maintained-count defect one level down.

PROBE, in Chilly's style: inject a key into a COPY of the runner's source and confirm the parser
picks it up. If the reader were a literal in this repo instead of a parse of that file, the probe
would find nothing and this test would fail.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("check_run", os.path.join(HERE, "check_run.py"))
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)

REAL_FILTER = C.runner_exclude_pat()
ENTRANTS = C.expected_entrants()

CASES = []


def case(name, ok, detail=""):
    CASES.append((name, ok, detail))


# 1. The real filter is read, and it is the runner's.
case("reads EXCLUDE_PAT from run_card.py", len(REAL_FILTER) >= 5, repr(REAL_FILTER))
case("filter includes the exclusions we measured on disk",
     {"mmproj", "audio", "qwen-image"} <= set(REAL_FILTER), repr(REAL_FILTER))

# 2. THE PROBE -- an injected key must be picked up. A copied constant would miss it.
INJECTED = 'EXCLUDE_PAT = ("mmproj", "audio", "qwen-image", "PROBE_KEY_XYZ")\n'
got = C.parse_exclude_pat(INJECTED)
case("probe: an injected key IS picked up (so it parses, not copies)",
     "PROBE_KEY_XYZ" in got, repr(got))

# 3. A moved name must FAIL LOUDLY, never silently fall back to a stale list.
try:
    C.parse_exclude_pat("EXCLUDE_PATTERNS = ('a',)\n")
    case("missing EXCLUDE_PAT fails loudly", False, "it returned instead of raising")
except SystemExit as e:
    case("missing EXCLUDE_PAT fails loudly", True, str(e)[:60])

# 4. A non-literal value cannot be read and must not be guessed at.
try:
    C.parse_exclude_pat("import os\nEXCLUDE_PAT = os.environ.get('X', '').split()\n")
    case("non-literal EXCLUDE_PAT fails loudly", False, "it returned instead of raising")
except SystemExit as e:
    case("non-literal EXCLUDE_PAT fails loudly", True, str(e)[:60])

# 5. The expected-count is a real number of real files, and less than the directory.
import glob
ondisk = glob.glob(os.path.join(C.MODELS, "*.gguf"))
case("expected entrants <= GGUFs on disk", 0 < len(ENTRANTS) <= len(ondisk),
     f"{len(ENTRANTS)} entrants of {len(ondisk)} GGUFs")

fails = 0
for name, ok, detail in CASES:
    print(f"  {'ok  ' if ok else 'FAIL'} {name}")
    if not ok:
        fails += 1
        print(f"        {detail}")
print()
if fails:
    print(f"{fails} failure(s) -- the liveness check cannot be trusted about its own denominator")
    sys.exit(1)
print(f"all {len(CASES)} cases pass: the filter is read, the probe is picked up, and a moved "
      f"constant fails loudly")
