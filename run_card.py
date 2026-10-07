#!/usr/bin/env python3
"""
Run the standing card across every available text entrant.

DESIGN CONSTRAINTS, all from this project's own findings:

  * DECLARED CONFIG, IDENTICAL FOR EVERY ENTRANT. --ctx 8192 --max-tokens 3000 --trials 3.
    FINDING 001: a smaller --ctx silently caps how much a reasoning model may think, and a
    smaller --max-tokens truncates the trace. A card run at different configs per entrant
    measures the configs, not the models. The config is printed once and never varied.

  * NO --ngl. Omission = llama.cpp auto-fits to free VRAM. FINDINGS/002: passing an
    explicit --n-gpu-layers makes an over-large placement ABORT rather than fall back, and
    a forced footprint that exceeds free VRAM turns a graceful partial offload into a
    crash. On this box the GPU has ~1.6 GB free, so most entrants will run partially
    offloaded and the weigh-in will say so.

  * PATHS, NEVER ALIASES. Two aliases in the local llama-swap config point at GGUFs that
    were deleted; the first version of this arena scored 40% of a field that did not exist.

  * RESUMABLE. A bundle that already exists is skipped, so a long run can be restarted
    without redoing work or overwriting evidence.

  * SMALLEST FIRST. In the order of file size, so results land progressively rather than
    after the slowest model finishes.

  * SCRATCH, NEVER ABORT. A model that cannot serve is recorded as scratched and the run
    continues. One bad entrant must not cost the field.
"""
import glob, json, os, shutil, subprocess, sys, time

# PORTABLE. Derived from this file, overridable by environment. The README says "download it,
# point it at your GGUFs" -- with absolute paths baked in, it could only be downloaded by one
# machine, which is the opposite of the point.
ARENA = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(ARENA, "results")
MODELS = os.environ.get("ARENA_MODELS") or os.path.expanduser("~/moltbook_pipeline/models")
SERVER = (os.environ.get("LLAMA_SERVER") or shutil.which("llama-server") or "llama-server")

CTX, MT, TRIALS = 8192, 3000, 3

# WHICH CARD. v1 = the retired 3-round card. v2 = the 6-item battery. A v2 bundle carries
# card_version 2 and a _cardv2_ filename marker, because a v1 score and a v2 score are different
# measurements and must never be ranked together.
CARD = "v2" if ("--card" in sys.argv and "v2" in sys.argv) else "v1"
CARD_TAG = "_cardv2_" if CARD == "v2" else "_"

# Excluded because the standing card is TEXT: diffusion, audio, and bare projectors.
EXCLUDE_PAT = ("qwen-image", "audio", "mmproj", "clip", "vae", "embed", "whisper")

os.makedirs(RESULTS, exist_ok=True)


def entrants():
    out = []
    for p in glob.glob(os.path.join(MODELS, "*.gguf")):
        b = os.path.basename(p)
        if any(k in b.lower() for k in EXCLUDE_PAT):
            continue
        out.append((os.path.getsize(p), p, b))
    out.sort()                      # smallest first
    return out


def already_measured(path):
    """Has this exact GGUF already been measured at this config, in ANY bundle?

    Keyed on CONTENT, not filename. The first version keyed on the derived output name, which
    only recognised bundles this script had itself created -- so it missed the hand-named
    bundles (Qwen3.5-2B_neutral_ctx8192_mt3000.json) and re-ran a model whose measurement
    already existed. A skip that only recognises your own filenames is not a skip.
    """
    base = os.path.basename(path)
    for bp in glob.glob(os.path.join(RESULTS, "*.json")):
        try:
            d = json.load(open(bp))
        except Exception:                                        # noqa: BLE001
            continue
        for r in (d.get("results") or []):
            if os.path.basename(r.get("gguf") or "") != base:
                continue
            c = r.get("config") or {}
            if (c.get("ctx") == CTX and c.get("max_tokens") == MT
                    and c.get("n_gpu_layers") is None
                    and r.get("card_version", 1) == (2 if CARD == "v2" else 1)):
                return os.path.basename(bp)
    return None


def bundle_path(stem):
    # Placement is IN THE NAME because it changes the latency conclusion (FINDINGS/004), and
    # this repo's rule is: if it changes what the reader concludes, it belongs in the name.
    # The card version is in the name for the same reason -- a v1 score and a v2 score are
    # different measurements.
    tag = "_cardv2" if CARD == "v2" else ""
    return os.path.join(RESULTS, f"{stem}{tag}_autofit_neutral_ctx{CTX}_mt{MT}.json")


def main():
    ents = entrants()
    print(f"entrants: {len(ents)}   config: ctx={CTX} mt={MT} trials={TRIALS} ngl=auto-fit")
    print("=" * 96, flush=True)
    log = os.path.join(RESULTS, "card_run.log")
    with open(log, "a") as lf:
        lf.write(f"\n=== card run started {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} "
                 f"ctx={CTX} mt={MT} trials={TRIALS} ===\n")

    done = scratched = skipped = 0
    t_start = time.time()
    for i, (size, path, base) in enumerate(ents, 1):
        stem = base.replace(".gguf", "")
        outp = bundle_path(stem)
        prior = already_measured(path)
        if os.path.exists(outp) or prior:
            print(f"[{i:2d}/{len(ents)}] SKIP (already measured in {prior or os.path.basename(outp)})")
            skipped += 1
            continue

        print(f"[{i:2d}/{len(ents)}] {size/2**30:5.2f} GB  {stem}", flush=True)
        t0 = time.time()
        cmd = [sys.executable, "-u", os.path.join(ARENA, "arena.py"),
               "--model", path, "--ctx", str(CTX), "--max-tokens", str(MT),
               "--trials", str(TRIALS), "--card", CARD, "--out", outp,
               "--llama-server", SERVER]
        try:
            r = subprocess.run(cmd, cwd=ARENA, capture_output=True, text=True, timeout=5400)
            dt = time.time() - t0
            well = [l for l in (r.stdout or "").splitlines()
                    if any(k in l for k in ("DIVISION", "AGG", "belt", "BELT", "SCRATCHED",
                                            "MEASURED", "PARTIAL", "wrote", "bundle"))]
            for l in well[-6:]:
                print("      " + l.strip())

            # A bundle can EXIST and be EMPTY: the harness writes one even when the entrant is
            # scratched at weigh-in. rc=0 with an empty results list is not a score.
            #
            # bundle=True used to test that a FILE EXISTS, which cannot detect the failure it
            # most needs to catch -- a run that measured nothing reports success. The Chair
            # found one: laya_english_f16, results: [], logged as `rc=0 2s bundle=True`. A
            # 2-second "success" is the most dangerous row on a board: it looks like a result.
            #
            # So: a bundle only counts if it CONTAINS a measurement -- non-empty results, with a
            # config and a sha256. This is the repo's own README contract, enforced rather than
            # asserted.
            scored_ok, why_empty = False, ""
            if r.returncode == 0 and os.path.exists(outp):
                try:
                    d = json.load(open(outp))
                    res = d.get("results") or []
                    r0 = res[0] if res else {}
                    if not res:
                        why_empty = "results list is EMPTY (measured nothing)"
                    elif not (r0.get("config") and r0.get("sha256")):
                        why_empty = "entry lacks config and/or sha256 — violates results/README"
                    else:
                        scored_ok = True
                except Exception as e:                            # noqa: BLE001
                    why_empty = f"unreadable: {type(e).__name__}"
            if scored_ok:
                done += 1
                print(f"      -> scored in {dt/60:.1f} min", flush=True)
            else:
                scratched += 1
                # mark the artifact itself, so an `ls` cannot present it as an entrant
                try:
                    if os.path.exists(outp):
                        stem = os.path.basename(outp).replace(".json", "")
                        marked = os.path.join(RESULTS,
                                              stem.replace("_neutral_", "_EMPTY_")
                                              .replace("_GRAMMAR_", "_EMPTY_") + ".json")
                        if marked != outp and not os.path.exists(marked):
                            os.rename(outp, marked)
                            print(f"      -> marked {os.path.basename(marked)}")
                except Exception:                                 # noqa: BLE001
                    pass
                print(f"      -> NOT SCORED {why_empty or 'rc=' + str(r.returncode)} "
                      f"({dt/60:.1f} min)", flush=True)
            with open(log, "a") as lf:
                lf.write(f"{stem}\trc={r.returncode}\tscored={scored_ok}\t{dt:.0f}s\t"
                         f"{why_empty}\n")
        except subprocess.TimeoutExpired:
            scratched += 1
            print(f"      -> TIMEOUT after 90 min, moving on", flush=True)
            with open(log, "a") as lf:
                lf.write(f"{stem}\tTIMEOUT\n")

    print("=" * 96)
    print(f"scored {done}   scratched/not-scored {scratched}   skipped {skipped}   "
          f"total {(time.time()-t_start)/60:.1f} min")
    print(f"log: {log}")
    ls = sorted(glob.glob(os.path.join(RESULTS, "*_neutral_ctx*_mt*.json")))
    print(f"bundles now on disk: {len(ls)}")


if __name__ == "__main__":
    main()
