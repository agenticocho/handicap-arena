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
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cabinet_root as _root                                              # noqa: E402
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
    # FILES ARE NOT MEASUREMENTS, AND BUNDLES ARE NOT ENTRANTS.
    #
    # Chilly caught the first half in its own check -- "a count of FILES is not a count of
    # MEASUREMENTS" -- and this tool had both halves wrong. It reported "45 of 46" while 26 of those
    # bundles had measured nothing; then, when the resolver was fixed and the failures re-ran, the
    # re-run wrote NEW filenames (`_EMPTY_` stays as the record of the failed attempt) so the file
    # count crossed the expected count and it reported FINISHED while the run was alive and working.
    #
    # The unit is the ENTRANT and the only progress is a MEASUREMENT. A stem counts as measured if
    # ANY of its bundles carries a result; a stem whose every bundle is empty has measured nothing.
    by_stem = {}
    for p in done:
        stem = os.path.basename(p).split("_cardv")[0]
        try:
            has = bool(json.load(open(p, encoding="utf-8")).get("results") or [])
        except Exception:
            has = False
        by_stem[stem] = by_stem.get(stem, False) or has
    measured = [s for s, has in by_stem.items() if has]
    never_ran = [s for s, has in by_stem.items() if not has]
    # ACCOUNTED-FOR IS THE COMPLETENESS TEST, NOT MEASURED.
    #
    # Fourth iteration of one class: files -> measurements -> entrants -> ACCOUNTED-FOR. A complete
    # run reports `scored 18 · scratched 7 · skipped 21 = 46`: a SKIPPED entrant already has a bundle
    # from an earlier pass, so it is done, and counting only fresh measurements made a finished field
    # read as DIED. Every entrant this tool can see has a stem; completeness is whether every EXPECTED
    # entrant has one.
    accounted = len(by_stem)
    # THE RUN'S JOURNAL IS SCRATCH, AND ITS COORDINATE IS DECLARED RATHER THAN DERIVED.
    #
    # This read [<HERE>/logs/card_run.log, <HERE>/results/card_run.log]: the SECOND is a log
    # coordinate sitting inside the RESULTS path, which belongs to no era and to no declaration --
    # the coordinate question this card owns -- and the FIRST is derived from where THIS READER
    # sits, so a reader in a cabinet worktree could not resolve the journal main's runs wrote.
    # Both are now declared: cabinet_root.log_path() for this worktree, plus LEGACY_LOGS, the
    # journal every bundle in the legacy record was written against, declared in place. Read from
    # both, newest wins: the value is read from where it IS, not remembered from where it was.
    _cands = [_root.log_path(HERE), os.path.join(_root.LEGACY_LOGS, _root.LOG_NAME)]
    _have = [p for p in _cands if os.path.exists(p)]
    log = max(_have, key=os.path.getmtime) if _have else _cands[0]
    # AND THE SERVER LOG, BECAUSE THE RUNNER'S LOG IS COARSER THAN THE WORK.
    #
    # `card_run.log` is written when an ENTRANT FINISHES; the server log is written per TOKENS. Watching
    # only the runner means a long entrant is indistinguishable from a hang -- MEASURED: 2727s of runner
    # silence while the server was emitting ~22 tokens every 3 seconds, on an entrant at 6.6 t/s with a
    # 3000-token cap and six items. The check reported STALE and was wrong; the work was progressing the
    # whole time in a file it was not reading.
    #
    # A check with a ceiling on what it can see reports a number that looks like a measurement. The
    # newest evidence is the evidence, and the newest evidence includes the server.
    _srv = sorted(glob.glob(os.path.join(_root.log_dir(HERE), "arena-server-*.log")),
                  key=os.path.getmtime, reverse=True)
    _live = _have + ([_srv[0]] if _srv else [])
    age = (time.time() - max(os.path.getmtime(p) for p in _live)) if _live else -1
    alive = None
    if pid:
        alive = subprocess.run(["ps", "-p", str(pid)],
                               capture_output=True).returncode == 0

    print(f"  card              : {card}")
    print(f"  expected entrants : {len(exp)}   (same EXCLUDE_PAT the runner uses)")
    print(f"  bundle files       : {len(done)}")
    print(f"  ENTRANTS MEASURED  : {len(measured)}   <- the only count that is progress")
    if never_ran:
        print(f"  entrants that never ran : {len(never_ran)}   <- a serving failure, "
              f"not a capability result")
    print(f"  process alive     : {alive if pid else 'unknown (no pid given)'}")
    print(f"  last progress     : {age:.0f}s ago" if age >= 0 else "  last progress     : no log")
    print()

    # CARRY THE BASIS INSIDE THE VERDICT. A verdict plus a separately-attached warning is a warning
    # nobody reads -- and a warning appended to EVERY result is read as never, because its position
    # carries no signal. "exit 1" is not a result; "exit 1, captured directly" is. So each verdict
    # line below states what it counted and where the count came from.
    n_m, n_exp = len(measured), len(exp)
    if accounted >= n_exp:
        print(f"  STATE: FINISHED — {accounted} entrants ACCOUNTED FOR against {n_exp} expected, of "
              f"which {n_m} carry a measurement.")
        return 0
    if alive is False:
        if accounted == 0:
            print(f"  STATE: NOT STARTED — 0 entrants accounted for against {n_exp} expected, no "
                  f"process alive. Nothing has been measured yet.")
            return 1
        print(f"  STATE: *** DIED *** — {accounted} entrants ACCOUNTED FOR against {n_exp} expected, "
              f"and NO process alive. {n_exp - accounted} entrants have no bundle at all.")
        print("  Report this as a FAILURE. Do not report it as a finish.")
        return 2
    if alive is None:
        print(f"  STATE: UNKNOWN — {accounted} of {n_exp} accounted for ({n_m} measured), process "
              f"liveness not checked (no pid given).")
        return 1
    if age > STALE_SECONDS:
        print(f"  STATE: RUNNING BUT STALE — {accounted} of {n_exp} accounted for ({n_m} measured), "
              f"process alive, no log progress for {age:.0f}s (threshold {STALE_SECONDS}s). Suspect "
              f"a hang.")
        return 1
    print(f"  STATE: RUNNING — {accounted} of {n_exp} entrants accounted for ({n_m} MEASURED), "
          f"process {pid} alive, last log progress {age:.0f}s ago.")
    return 0


if __name__ == "__main__":
    card = sys.argv[1] if len(sys.argv) > 1 else "v3"
    pid = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(main(card, pid))
