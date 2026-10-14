#!/usr/bin/env python3
"""Rename every bundle so its FILENAME cannot disagree with its CONTENT.

RESIDUAL A (the Chair's find): the display name still violated the repo's own convention.
  11 distinct filename stems, 9 distinct sha256.
    LFM2-350M_neutral_ctx2048   -> GGUF is LFM2-350M-Extract-Q4_K_M.gguf
    Qwen3.5-2B_neutral_ctx2048  -> GGUF is Qwen3.5-2B-UD-Q4_K_XL.gguf
My content-keyed dedupe grouped them correctly because it reads the GGUF name INSIDE the bundle.
Any reader or future script that groups by filename stem sees 11 models where there are 9.
The identity key got fixed; the display name did not. Same rule, one level out.

RESIDUAL B (the one that matters): a bundle with `results: []` -- zero rounds, no config, no
sha256 -- was recorded by the run log as `rc=0 ... bundle=True`. `bundle=True` tests that a FILE
EXISTS, not that it CONTAINS a measurement, so the success signal cannot detect the failure it
most needs to catch. A 2-second "success" is the most dangerous row on a board: it looks like a
result and it is the absence of one.

CANONICAL FORM, derived from the bundle itself so the name cannot drift from the content:

    <gguf-stem>_<placement>_<serving>_ctx<N>_mt<N>.json     e.g. LFM2-350M-Extract-Q4_K_M_autofit_neutral_ctx8192_mt3000.json
    <gguf-stem>_EMPTY_<serving>_ctx<N>_mt<N>.json           for a bundle with no measurement

Placement is IN THE NAME because it changes the latency conclusion (FINDINGS/004), and the
repo's rule is: if it changes what the reader concludes, it belongs in the name.
"""
import glob, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)                      # root scripts: already sys.path[0]; scripts/*: required
import cabinet_root as _root

# The manifest lives OUTSIDE results/, because results/ holds result bundles and nothing else.
# A manifest sitting among them is exactly the kind of file a reader counts as an entrant --
# the same objection the Chair raised about the empty bundle.
MANIFEST = os.path.join(HERE, "RENAME_MANIFEST.json")


def scope(pattern="*.json"):
    """[(kind, base, [paths])] over the DECLARED domain, entry by entry. No pattern is widened,
    no directory joins by existing."""
    rows = []
    for kind, base in _root.domain():
        rows.append((kind, base, sorted(glob.glob(os.path.join(base, pattern)))))
    return rows


def print_scope(rows, pattern):
    # THE SCOPE IS PRINTED WITH THE COUNT IT CONTRIBUTED: a count without its scope is not a count.
    for kind, base, hits in rows:
        print(f"  scope  {kind:16} {len(hits):4} {pattern}  {base}")


def canonical(path):
    d = json.load(open(path))
    res = d.get("results") or []
    if not res:
        # No measurement. Say so in the name -- do not let it pass as an entrant.
        return None, os.path.basename(path)
    r = res[0]
    cfg = r.get("config") or {}
    flags = cfg.get("server_flags") or []
    serving = "GRAMMAR" if "--grammar-file" in flags else "neutral"
    ngl = cfg.get("n_gpu_layers")
    placement = "autofit" if ngl is None else f"ngl{ngl}"
    model = os.path.basename(r.get("gguf") or "UNKNOWN").replace(".gguf", "")
    want = f"{model}_{placement}_{serving}_ctx{cfg.get('ctx')}_mt{cfg.get('max_tokens')}.json"
    return want, os.path.basename(path)


HANDICAP = "handicap-arena"


def main():
    dry = "--apply" not in sys.argv
    # THE WRITE SCOPE, RESOLVED ONCE AND NEVER FALLEN BACK TO (AC5). results_dir() refuses (a
    # SystemExit, exit 1, nothing written) when there is no declaration -- that refusal is NOT
    # caught here, because a caught refusal is a fallback with better manners.
    write = _root.results_dir()
    rows = scope("*.json")
    print_scope(rows, "*.json")
    print(f"  write scope: {write}")
    proposals, refused = [], []
    for path in [p for _k, _b, hits in rows for p in hits]:
        try:
            d = json.load(open(path))
        except Exception as e:                                    # noqa: BLE001
            print(f"  SKIP (unreadable): {os.path.basename(path)} — {e}")
            continue
        # IS THIS A BUNDLE AT ALL? The first version treated ANY json without a `results` key
        # as an empty measurement -- so it tried to rename its own RENAME_MANIFEST.json to
        # RENAME_MANIFEST.EMPTY.json. That is the day's signature move once more: a test that
        # answers 'is this empty?' without first asking 'is this a bundle?'.
        if d.get("harness") != HANDICAP or "results" not in d:
            print(f"  SKIP (not a result bundle): {os.path.basename(path)}")
            continue
        try:
            want, have = canonical(path)
        except Exception as e:                                    # noqa: BLE001
            print(f"  SKIP (unreadable): {os.path.basename(path)} — {e}")
            continue
        if want is None:
            # an empty bundle: mark it EMPTY using whatever stem it has
            base = have.replace(".json", "")
            want = base.replace("_neutral_", "_EMPTY_").replace("_GRAMMAR_", "_EMPTY_") + ".json"
            if "EMPTY" not in want:
                want = base + ".EMPTY.json"
        if want == have:
            continue
        # A RENAME OUTSIDE THE WRITE SCOPE IS A REWRITE OF THE RECORD, so it is REFUSED -- and the
        # refusal prints the rename it declined, so the intent stays visible instead of vanishing.
        in_scope = os.path.dirname(os.path.abspath(path)) == os.path.abspath(write)
        proposals.append((have, want, in_scope))
        if not in_scope:
            refused.append((have, want))

    print(f"{'DRY RUN — pass --apply to rename' if dry else 'APPLYING'}  ({len(proposals)} rename(s))")
    for have, want, in_scope in proposals:
        if not in_scope:
            print(f"  REFUSED (not the write scope): {have} -> {want}")
            continue
        # THE COLLISION PROBE READS THE DIRECTORY THE RENAME WOULD HAPPEN IN, and nothing else: a
        # probe against the legacy record would answer a question about a place this run may not
        # write. It is a read, so it is inside the domain -- it is the ANSWER that was out of scope.
        coll = "  [COLLISION: target exists]" if os.path.exists(
            os.path.join(write, want)) else ""
        print(f"  {have}\n    -> {want}{coll}")
    print(f"  {len(refused)} outside the write scope, 0 applied")
    if dry:
        return
    # --apply WITH NO IN-SCOPE CANDIDATE WRITES NOTHING AT ALL: no empty RENAME_MANIFEST.json, and
    # no dirty tree. A manifest of nothing is a file a reader counts.
    if not refused and not [p for p in proposals if p[2]]:
        print(f"  NOTHING WAS WRITTEN: no candidate anywhere, write scope {write}")
        return
    if not [p for p in proposals if p[2]]:
        print(f"  NOTHING WAS WRITTEN: every candidate is outside the write scope {write}")
        return
    manifest, failed = [], []
    for have, want, in_scope in proposals:
        if not in_scope:
            continue
        # PER-ITEM ISOLATION. The first run of this script raised on one malformed name and
        # killed the loop, leaving the directory half-renamed. That is the rule logger's own
        # docs state -- "one dead endpoint cannot kill the sweep" -- which I wrote and then
        # failed to apply to my own tooling. One bad item must not cost the rest.
        src, dst = os.path.join(write, have), os.path.join(write, want)
        try:
            if os.path.exists(dst):
                print(f"  SKIP (collision) {have}")
                continue
            if not os.path.exists(src):
                raise FileNotFoundError(src)
            os.rename(src, dst)
            manifest.append({"was": have, "now": want})
        except Exception as e:                                    # noqa: BLE001
            failed.append({"was": have, "want": want, "error": f"{type(e).__name__}: {e}"})
            print(f"  FAILED {have}: {type(e).__name__}: {e}")
    with open(MANIFEST, "w") as fh:
        json.dump({"note": "rename so the filename cannot disagree with the content; "
                           "derived from each bundle's own gguf + config",
                   "renames": manifest, "failed": failed}, fh, indent=1)
    print(f"  renamed {len(manifest)}; failed {len(failed)}; manifest at {MANIFEST}")


if __name__ == "__main__":
    main()
