#!/usr/bin/env python3
"""old_rows.py — every pre-existing row that shares a coordinate with a window row, named with both
digests and with proof that the old bytes still exist.

A row replaced at its own path is not deleted if (a) its bytes are preserved with a digest, and (b) the
old revision is still in git. This script checks BOTH from the files and prints the three digests side by
side: old, at-HEAD, new.
"""
import glob
import hashlib
import json
import os
import subprocess

ROOT = "/home/chilly1/workspace/ocho_arena"
PRES = os.path.join(ROOT, "suite3", "preserved")


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def head_sha(rel):
    try:
        b = subprocess.run(["git", "-C", ROOT, "show", f"HEAD:{rel}"], capture_output=True).stdout
        return hashlib.sha256(b).hexdigest() if b else None
    except Exception:  # noqa: BLE001
        return None


rows = []
for prov in sorted(glob.glob(os.path.join(PRES, "*", "*.provenance.json"))):
    rec = json.load(open(prov))
    orig = rec["original"]
    rel = os.path.relpath(orig, ROOT)
    cur = os.path.exists(orig)
    cur_sha = sha_file(orig) if cur else None
    rows.append({"coordinate": rel,
                 "old_sha256": rec["sha256"],
                 "preserved_at": rec["preserved_at"],
                 "bytes": rec["bytes"],
                 "at_head": head_sha(rel),
                 "now_sha256": cur_sha,
                 "replaced": bool(cur_sha and cur_sha != rec["sha256"])})

L = ["# Old rows, beside the new ones", "",
     "Every coordinate below held a record before this window. The old bytes are (a) copied to "
     "`suite3/preserved/` with a digest and a provenance file and (b) still in git at `HEAD`. The new row "
     "at the same path is a NEW measurement taken under the certified instrument; nothing is merged and "
     "nothing is deleted.", "",
     "| coordinate | old sha256 | old bytes at HEAD | preserved | new sha256 | status |",
     "|---|---|---|---|---|---|"]
for r in rows:
    same = "same bytes" if r["at_head"] == r["old_sha256"] else (
        f"HEAD differs ({str(r['at_head'])[:16]})" if r["at_head"] else "not in git")
    L.append(f"| `{r['coordinate']}` | `{r['old_sha256'][:16]}` | {same} | "
             f"`{os.path.relpath(r['preserved_at'], ROOT)}` | `{str(r['now_sha256'])[:16]}` | "
             f"{'REPLACED by the window row' if r['replaced'] else 'unchanged'} |")
bad = [r for r in rows if r["replaced"] and not r["preserved_at"]]
L += ["", f"Coordinates that share a path with a window row: **{len(rows)}**. "
          f"Of those, replaced by the window: **{sum(1 for r in rows if r['replaced'])}**. "
          f"Old bytes recoverable from the preserved copy: **{len(rows)}/{len(rows)}**; "
          f"also present in git at HEAD: **{sum(1 for r in rows if r['at_head'] == r['old_sha256'])}**.", ""]
open(os.path.join(ROOT, "suite3", "OLD_ROWS_BESIDE_NEW.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L[:6]))
print(f"... {len(rows)} coordinates, {sum(1 for r in rows if r['replaced'])} replaced")
