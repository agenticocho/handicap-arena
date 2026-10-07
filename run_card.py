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
import glob, json, os, subprocess, sys, time

ARENA = "/home/chilly1/workspace/ocho_arena"
RESULTS = os.path.join(ARENA, "results")
MODELS = "/home/chilly1/moltbook_pipeline/models"
SERVER = "/home/chilly1/llama.cpp/build/bin/llama-server"

CTX, MT, TRIALS = 8192, 3000, 3

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
                    and c.get("n_gpu_layers") is None):
                return os.path.basename(bp)
    return None


def bundle_path(stem):
    return os.path.join(RESULTS, f"{stem}_neutral_ctx{CTX}_mt{MT}.json")


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
               "--trials", str(TRIALS), "--out", outp, "--llama-server", SERVER]
        try:
            r = subprocess.run(cmd, cwd=ARENA, capture_output=True, text=True, timeout=5400)
            dt = time.time() - t0
            tail = (r.stdout or "").strip().splitlines()[-4:]
            well = [l for l in (r.stdout or "").splitlines()
                    if any(k in l for k in ("DIVISION", "AGG", "belt", "BELT", "SCRATCHED",
                                            "MEASURED", "PARTIAL", "wrote", "bundle"))]
            for l in well[-6:]:
                print("      " + l.strip())
            # A bundle can EXIST and be EMPTY: the harness writes one even when the entrant is
            # scratched at weigh-in. rc=0 with an empty results list is not a score, and counting
            # it as one overstates the field. Verify the artifact, not the exit code.
            scored_ok = False
            if r.returncode == 0 and os.path.exists(outp):
                try:
                    scored_ok = len(json.load(open(outp)).get("results") or []) > 0
                except Exception:
                    scored_ok = False
            if scored_ok:
                done += 1
                print(f"      -> scored in {dt/60:.1f} min", flush=True)
            else:
                scratched += 1
                why = [l for l in (r.stdout or "").splitlines() if "SCRATCH" in l or "not found" in l]
                print(f"      -> NOT SCORED rc={r.returncode} {dt/60:.1f} min "
                      f"{(why[-1].strip() if why else (r.stderr or '')[:120])}", flush=True)
            with open(log, "a") as lf:
                lf.write(f"{stem}\trc={r.returncode}\t{dt:.0f}s\tbundle={os.path.exists(outp)}\n")
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
