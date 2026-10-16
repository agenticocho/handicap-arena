#!/usr/bin/env python3
"""verify_docs.py — a FUNCTION gate for the published shelf, upstream of the copy gate.

WHY THIS EXISTS
    2026-10-16: a cabinet demo was held back because one parenthesis in the wrong place made an
    outer group `(X : Y)` — a JavaScript PARSE ERROR, so the browser discarded the entire script
    before a line of it ran. Nothing was wired, nothing rendered, and every check we had passed:

      self-containment      a parse error moves no reference count
      publish_docs.py       a parse error moves no digest -- the copy proof held perfectly
      served == origin/main a parse error moves no size

    Three green checks on a page that does not run. A COPY PROOF ESTABLISHES THAT THE COPY IS THE
    OBJECT; IT NEVER ESTABLISHES THAT THE OBJECT WORKS.

WHAT IT DOES
    Extracts every inline <script> block from a published HTML file and syntax-checks each with
    `node --check`. That is precisely the failure that bit us: a page whose script never runs.

WHAT IT DOES NOT DO, AND SAYS SO IN ITS OWN OUTPUT
    It does NOT drive the page. No jsdom and no headless browser are installed on this box, so a
    page that parses cleanly but does nothing at all still passes THIS gate. Syntax is necessary
    and not sufficient, and the output states that limit rather than implying coverage it lacks.
    When a driver is available, the driven PLAY/STEP check belongs here, ahead of the copy gate.

USAGE
    python3 verify_docs.py docs/index.html docs/arcade_wall.html
    python3 verify_docs.py --all          # every .html under docs/

EXIT
    0 every inline script parsed
    1 a script failed to parse (the defect this exists for)
    2 node is absent, a file is unreadable, or no script was found where one was expected --
      REFUSING rather than reporting green on an instrument that cannot read
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script\s*>", re.S | re.I)


def scripts_in(html: str):
    """Yield (attrs, body) for each inline script. src= scripts carry no body and cannot be
    syntax-checked here -- they are a self-containment concern, not a parse concern."""
    for m in SCRIPT_RE.finditer(html):
        attrs, body = m.group(1) or "", m.group(2) or ""
        if re.search(r"\bsrc\s*=", attrs, re.I):
            continue
        if body.strip():
            yield attrs, body


def check_file(path: pathlib.Path, node: str):
    """Return (problems, checked_count). Raises OSError if the file cannot be read."""
    html = path.read_text(errors="replace")
    if not scripts_in(html):
        return [], 0
    problems = []
    n = 0
    for i, (_attrs, body) in enumerate(scripts_in(html), 1):
        n += 1
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
            fh.write(body)
            tmp = fh.name
        try:
            r = subprocess.run([node, "--check", tmp], capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                first = (r.stderr or r.stdout).strip().splitlines()
                detail = next((l for l in first if l.strip()), "parse error")
                problems.append(f"{path.name} script #{i}: {detail}")
        finally:
            pathlib.Path(tmp).unlink(missing_ok=True)
    return problems, n


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--all"]
    node = shutil.which("node") or shutil.which("nodejs")
    if not node:
        print("verify_docs: no node/nodejs on PATH — cannot syntax-check — REFUSING", file=sys.stderr)
        return 2

    if "--all" in sys.argv:
        files = sorted(pathlib.Path("docs").glob("*.html"))
    else:
        files = [pathlib.Path(a) for a in args]
    if not files:
        print("verify_docs: no files given — REFUSING", file=sys.stderr)
        return 2

    total_scripts = 0
    all_problems = []
    for p in files:
        if not p.is_file():
            print(f"verify_docs: cannot read {p} — REFUSING", file=sys.stderr)
            return 2
        try:
            problems, n = check_file(p, node)
        except OSError as e:
            print(f"verify_docs: {p}: {e} — REFUSING", file=sys.stderr)
            return 2
        total_scripts += n
        all_problems += problems
        tag = "no inline scripts" if n == 0 else f"{n} script(s) parsed"
        print(f"  {'FAIL' if problems else 'OK  '}  {p}  {p.stat().st_size} bytes  {tag}")

    for pr in all_problems:
        print(f"  PARSE ERROR  {pr}", file=sys.stderr)

    print(f"  checked {total_scripts} inline script(s) with {pathlib.Path(node).name} --check")
    print("  LIMIT: syntax only. Behaviour is NOT driven (no jsdom, no headless browser on this")
    print("         box), so a page that parses but does nothing still passes this gate.")
    if all_problems:
        print(f"  FAIL — {len(all_problems)} script(s) would be discarded by the browser")
        return 1
    print("  OK — every inline script parses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
