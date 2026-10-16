#!/usr/bin/env python3
"""publish_docs.py — copy generated artifacts into docs/ and PROVE the copy is the same object.

WHY THIS EXISTS
    GitHub Pages serves docs/. The wall is generated at the repo ROOT by build_arcade_wall.py, so
    docs/ necessarily carries a COPY -- and a copy that can drift silently while looking
    authoritative is exactly the defect this project has ruled on repeatedly (a cabinet's GAMES.md
    printing the arena's masthead; a line copied between siblings).

    So this script does not merely copy. It copies, then re-reads both files and compares digests,
    and refuses to report success if they differ. A copy that is not verified is a claim.

WHAT IT DOES NOT DO
    It never edits docs/index.html -- that is authored, not generated. It refuses if an artifact it
    publishes is missing at the source rather than writing an empty or stale file over a good one.

USAGE
    python3 publish_docs.py            # publish + verify
    python3 publish_docs.py --check    # verify only, change nothing (for CI or a pre-commit run)

EXIT
    0 all published copies are byte-identical to their sources
    1 a copy differs after writing
    2 a source artifact is missing, or docs/ is unreadable -- REFUSES rather than guessing
"""
import hashlib
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
DOCS = HERE / "docs"

# generated artifacts at the repo root that are served. Add here, never hand-copy.
PUBLISH = ["arcade_wall.html"]


def digest(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    check_only = "--check" in sys.argv
    if not DOCS.is_dir():
        print(f"publish_docs: no docs/ at {DOCS} -- REFUSING", file=sys.stderr)
        return 2

    bad = 0
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
