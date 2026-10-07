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

RESULTS = "/home/chilly1/workspace/ocho_arena/results"


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


def main():
    dry = "--apply" not in sys.argv
    moves = []
    for path in sorted(glob.glob(os.path.join(RESULTS, "*.json"))):
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
        moves.append((have, want))

    print(f"{'DRY RUN — pass --apply to rename' if dry else 'APPLYING'}  ({len(moves)} rename(s))")
    for have, want in moves:
        coll = "  [COLLISION: target exists]" if os.path.exists(
            os.path.join(RESULTS, want)) else ""
        print(f"  {have}\n    -> {want}{coll}")
    if dry:
        return
    manifest, failed = [], []
    for have, want in moves:
        # PER-ITEM ISOLATION. The first run of this script raised on one malformed name and
        # killed the loop, leaving the directory half-renamed. That is the rule logger's own
        # docs state -- "one dead endpoint cannot kill the sweep" -- which I wrote and then
        # failed to apply to my own tooling. One bad item must not cost the rest.
        src, dst = os.path.join(RESULTS, have), os.path.join(RESULTS, want)
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
    with open(os.path.join(RESULTS, "RENAME_MANIFEST.json"), "w") as fh:
        json.dump({"note": "rename so the filename cannot disagree with the content; "
                           "derived from each bundle's own gguf + config",
                   "renames": manifest, "failed": failed}, fh, indent=1)
    print(f"  renamed {len(manifest)}; failed {len(failed)}; manifest written")


if __name__ == "__main__":
    main()
