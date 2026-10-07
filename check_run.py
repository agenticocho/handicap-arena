#!/usr/bin/env python3
"""Is the run alive, finished, or DEAD? Three-valued, because that ambiguity cost me a run.

WHY THIS EXISTS. A card run was killed at 17 of 46 entrants by lifecycle cleanup. There was no error
in the log. The last line named a model and said `rc=0` -- which is what a healthy run's last line
looks like too. **A run that dies silently and a run that finishes are indistinguishable from the
tail of its own log**, so the tail cannot be the check.

Chilly found the general form while building its run-state protocol: *"My run state covers the
machine. Nothing covers the run's liveness... the same defect as the service that crash-loops and
reads as busy, one level up."*

THE ASSERTION THAT MATTERS, and it is the only line here that changes a decision:

    NOT ALIVE and COMPLETED < EXPECTED  ->  DIED.  Report a FAILURE. Never a finish.

Everything else is diagnostics. That one clause stops "died" rendering as "done".

EXPECTED IS FILTERED, NOT COUNTED FROM THE DIRECTORY. 53 GGUFs sit on disk; 46 are text entrants;
7 are excluded by the runner's own EXCLUDE_PAT (audio, vision projectors, diffusion). A directory
count would report 53 and a curated count would report whatever someone remembered -- so this reads
the SAME filter the runner uses. 53 is a directory fact; 46 is a filtered fact.
"""
import ast
import glob
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.environ.get("ARENA_MODELS") or os.path.expanduser("~/moltbook_pipeline/models")
STALE_SECONDS = int(os.environ.get("ARENA_STALE_SECONDS", "2700"))   # 45 min: slowest entrant seen


def parse_exclude_pat(src):
    """The parser, on SOURCE TEXT, so it can be probed without touching the real runner."""
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if getattr(t, "id", None) == "EXCLUDE_PAT":
                    try:
                        return tuple(ast.literal_eval(node.value))
                    except ValueError as e:
                        raise SystemExit(
                            f"EXCLUDE_PAT is not a literal ({e}); this check cannot read it, and a "
                            f"stale copy would report a field nobody is running.")
    raise SystemExit("EXCLUDE_PAT not found in the source -- the runner's filter moved, so this "
                     "check's expected-count is unsupported. Fix the reader, do not hardcode it.")


def runner_exclude_pat():
    """Read EXCLUDE_PAT OUT OF run_card.py. Do not copy it.

    A copied constant drifts from the thing it copied: the runner's filter changes, this file's
    doesn't, and the expected-count silently describes a field nobody is running. That is the
    hand-maintained-count defect one level down -- and it is why Chilly's run-state check now reads
    the filter out of the runner instead of restating it.

    Parsed with ast, NOT imported: run_card.py parses argv and calls sys.exit at module level, so
    importing it would run it. If the name moves or the value stops being a literal, this FAILS
    LOUDLY rather than quietly falling back to a stale list.
    """
    with open(os.path.join(HERE, "run_card.py"), encoding="utf-8") as f:
        return parse_exclude_pat(f.read())


def expected_entrants():
    """Same filter the RUNNER applies, read from the runner itself."""
    pat = runner_exclude_pat()
    return [os.path.basename(p) for p in glob.glob(os.path.join(MODELS, "*.gguf"))
            if not any(k in os.path.basename(p).lower() for k in pat)]


def main(card="v3", pid=None):
    exp = expected_entrants()
    pattern = os.path.join(HERE, "results", f"*card{card}*.json")
    done = sorted(glob.glob(pattern))
    log = os.path.join(HERE, "results", "card_run.log")
    age = (time.time() - os.path.getmtime(log)) if os.path.exists(log) else -1
    alive = None
    if pid:
        alive = subprocess.run(["ps", "-p", str(pid)],
                               capture_output=True).returncode == 0

    print(f"  card              : {card}")
    print(f"  expected entrants : {len(exp)}   (same EXCLUDE_PAT the runner uses)")
    print(f"  completed bundles : {len(done)}")
    print(f"  process alive     : {alive if pid else 'unknown (no pid given)'}")
    print(f"  last progress     : {age:.0f}s ago" if age >= 0 else "  last progress     : no log")
    print()

    if len(done) >= len(exp):
        print("  STATE: FINISHED")
        return 0
    if alive is False:
        print(f"  STATE: *** DIED ***  — completed {len(done)} of {len(exp)}, "
              f"{len(exp) - len(done)} entrants never measured.")
        print("  Report this as a FAILURE. Do not report it as a finish.")
        return 2
    if alive is None:
        print("  STATE: UNKNOWN — pass a pid to get the three-valued answer.")
        return 1
    if age > STALE_SECONDS:
        print(f"  STATE: RUNNING BUT STALE — no log progress for {age:.0f}s "
              f"(threshold {STALE_SECONDS}s). Slowest entrant seen is ~30 min; suspect a hang.")
        return 1
    print(f"  STATE: RUNNING — {len(done)} of {len(exp)}, last progress {age:.0f}s ago.")
    return 0


if __name__ == "__main__":
    card = sys.argv[1] if len(sys.argv) > 1 else "v3"
    pid = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(main(card, pid))
