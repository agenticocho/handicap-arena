#!/usr/bin/env python3
"""assemble.py — put the generated tables into the results document.

The prose is written once (`SUITE_RESULTS_sitting2_TEMPLATE.md`); every number in a table comes from
`suite2/TABLES2.md`, which `suite2/report2.py` generates from the block records and the cabinet
artifacts. This script substitutes `{{TABLE:<name>}}` markers, so no figure in the results document is
re-typed by hand and a regenerated table cannot drift from the row files.
"""
import os
import re
import sys

ROOT = "/home/chilly1/workspace/ocho_arena"
TEMPLATE = os.path.join(ROOT, "SUITE_RESULTS_sitting2_TEMPLATE.md")
TABLES = os.path.join(ROOT, "suite2", "TABLES2.md")
OUT = os.path.join(ROOT, "SUITE_RESULTS_multi_model_sitting2_2026-10-25.md")


def parse_tables():
    tables, cur = {}, None
    for line in open(TABLES).read().splitlines():
        m = re.match(r"<!-- TABLE:(\w+) -->", line)
        if m:
            cur = m.group(1)
            tables[cur] = []
            continue
        if cur:
            tables[cur].append(line)
    return {k: "\n".join(v).strip() + "\n" for k, v in tables.items()}


def main():
    tables = parse_tables()
    text = open(TEMPLATE).read()
    missing = []

    def sub(m):
        name = m.group(1)
        if name not in tables:
            missing.append(name)
            return f"<!-- TABLE {name} MISSING -->"
        return tables[name]

    out = re.sub(r"<!-- TABLE:(\w+) -->", sub, text)
    if missing:
        print(f"REFUSED: no generated table for {missing}; the document would carry a hole")
        return 2
    with open(OUT, "w") as f:
        f.write(out)
    print(f"wrote {os.path.relpath(OUT, ROOT)}  ({len(out)} bytes, {len(tables)} tables)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
