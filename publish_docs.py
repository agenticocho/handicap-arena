#!/usr/bin/env python3
"""publish_docs.py — copy generated artifacts into docs/ and PROVE the copy is the same object.

WHY THIS EXISTS
    GitHub Pages serves docs/. The wall is generated at the repo ROOT by build_arcade_wall.py, so
    docs/ necessarily carries a COPY -- and a copy that can drift silently while looking
    authoritative is exactly the defect this project has ruled on repeatedly (a cabinet's GAMES.md
    printing the arena's masthead; a line copied between siblings).

    So this script does not merely copy. It copies, then re-reads both files and compares digests,
    and refuses to report success if they differ. A copy that is not verified is a claim.

AND THE GATE THAT HAS TO COME FIRST
    2026-10-16: a cabinet demo was held back because one misplaced parenthesis made the browser
    discard its whole script at parse time -- the page did not run, and every check we had passed.
    A digest gate cannot see that: a parse error moves no digest, no size and no reference count.
    THE COPY PROOF ESTABLISHES THAT THE COPY IS THE OBJECT; IT NEVER ESTABLISHES THAT THE OBJECT
    WORKS. So this script now runs verify_docs.py (a syntax gate on every inline script) UPSTREAM
    of the copy, and publishes nothing if that gate fails.

WHAT IT DOES NOT DO
    It never edits docs/index.html -- that is authored, not generated. It refuses if an artifact it
    publishes is missing at the source rather than writing an empty or stale file over a good one.
    And it does not DRIVE the page -- see verify_docs.py's own stated limit.

USAGE
    python3 publish_docs.py            # syntax-check, publish, verify copies
    python3 publish_docs.py --check    # verify only, change nothing (for CI or a pre-commit run)

EXIT
    0 all published copies are byte-identical to their sources
    1 a copy differs after writing
    2 a source artifact is missing, docs/ is unreadable, or a source FAILED THE FUNCTION GATE --
      REFUSES rather than publishing something that cannot run
"""
import hashlib
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
DOCS = HERE / "docs"

# artifacts at the repo root that are served. Add here, never hand-copy.
#   generated here   : arcade_wall.html -- produced by build_arcade_wall.py from this repo's results
#   received, certified: missile_command_in_action_DRIVEN_AND_WORKING.html -- built by the visuals
#     agent on the peer box and DRIVEN there, where the only working driver lives. It arrives with a
#     sha256 certificate (47c461ec59...) and this side's job is the complementary half: prove the
#     published object IS that object. The certificate travels as a digest because the driver cannot
#     read our pages' schema, and a durable certificate needs no shared instrument.
PUBLISH = [
    "arcade_wall.html",
    "missile_command_in_action_DRIVEN_AND_WORKING.html",
]


def digest(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    check_only = "--check" in sys.argv
    if not DOCS.is_dir():
        print(f"publish_docs: no docs/ at {DOCS} -- REFUSING", file=sys.stderr)
        return 2

    bad = 0

    # FUNCTION GATE, upstream of the copy gate -- a parse error moves no digest.
    sys.path.insert(0, str(HERE))
    import verify_docs

    node = shutil.which("node") or shutil.which("nodejs")
    if not node:
        print("publish_docs: no node/nodejs -- the function gate cannot run -- REFUSING",
              file=sys.stderr)
        return 2
    gate = []
    for name in PUBLISH:
        src = HERE / name
        if not src.is_file():
            print(f"publish_docs: source missing: {name} -- REFUSING", file=sys.stderr)
            return 2
        try:
            problems, _n = verify_docs.check_file(src, node)
        except OSError as e:
            print(f"publish_docs: {name}: {e} -- REFUSING", file=sys.stderr)
            return 2
        gate += problems
    if gate:
        for pr in gate:
            print(f"  PARSE ERROR  {pr}", file=sys.stderr)
        print("publish_docs: a source FAILED the function gate -- REFUSING to publish",
              file=sys.stderr)
        return 2
    print("  function gate: every published source parses (syntax only -- see verify_docs.py)")

    for name in PUBLISH:
        src = HERE / name
        dst = DOCS / name
        if not src.is_file():
            print(f"  MISSING SOURCE  {name} -- not published, and no empty file written",
                  file=sys.stderr)
            return 2

        if not check_only:
            stale = dst.is_file() and digest(dst) != digest(src)
            shutil.copyfile(src, dst)
            if stale:
                print(f"  replaced stale  {name}")

        if not dst.is_file():
            print(f"  NOT PUBLISHED   {name}", file=sys.stderr)
            bad += 1
            continue

        a, b = digest(src), digest(dst)
        if a == b:
            print(f"  OK  {name}  {src.stat().st_size} bytes  {a[:16]}")
        else:
            print(f"  DIFFER  {name}  src={a[:16]} dst={b[:16]}", file=sys.stderr)
            bad += 1

    authored = DOCS / "index.html"
    print(f"  authored (not generated): index.html {authored.stat().st_size if authored.is_file() else 'MISSING'} bytes")
    if bad:
        print(f"  FAIL -- {bad} artifact(s) not identical", file=sys.stderr)
        return 1
    print("  OK -- every published copy is byte-identical to its source")
    return 0


if __name__ == "__main__":
    sys.exit(main())
