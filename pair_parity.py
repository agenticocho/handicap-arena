#!/usr/bin/env python3
"""A CROSS-MACHINE COMPARISON IS CHECKED, NOT AGREED -- join on sha256, never on a path.

WHY THIS EXISTS. A result bundle carries the GGUF's **path** and its **sha256**, and the two
machines do not share a filesystem: the same weights are `/home/chilly1/moltbook_pipeline/models/
LFM2-350M-Math-Q4_K_M.gguf` on one box and `/Users/mikebird/Mac/iphone/Max/Max/...` on the other.
Join two records on the path and ONE MODEL READS AS TWO; join them on sha256 and the path is what
it is -- a location, recorded, never used to decide identity. This is a rule that gets violated by
the first person in a hurry, so it is asserted here rather than agreed in prose.

THE RULE, OPERATIONALLY. Two records may be compared only when all of the following hold, and each
is checked rather than assumed:

  1. IDENTITY      both carry a well-formed sha256, and the two are equal.
  2. CONFIG        ctx, max_tokens, temperature, trials, n_gpu_layers are equal field by field.
  3. SERVING       `config.server_flags` are equal AS A PORTABLE PROJECTION -- see portable_flags():
                   the model path is replaced by its sha256 and `--port`/`--host` by <ephemeral>,
                   because a path is a location and a bound port is a runtime fact, while the rest
                   of the flags are configuration. Compared verbatim, flags refuse every genuine
                   cross-machine pair (different paths, different ports) while accepting two runs
                   of one machine -- exactly backwards.
  4. PLACEMENT     `ngl_requested: null` means AUTO-FIT, and "auto-fit" is a stand-in for a number
                   that differs between boxes and between runs. So for an auto-fit entry the
                   REALIZED placement (`ngl_realized`, read from llama-server's own log) is
                   REQUIRED on both sides. A forced placement (`ngl_requested` set) is declared by
                   construction, and any realized count that disagrees with the request is
                   reported -- a forced placement that did not take is worth knowing.

VERDICTS
  CERTIFIED                       exit 0  identity, config, serving and a known placement on both
  CERTIFIED WITH A DECLARED       exit 0  the two realized placements differ and BOTH SAY SO --
    PLACEMENT DIFFERENCE                  the comparison is between two placements, stated, not lost
  REFUSED                         exit 1  a named reason: unknown identity, a differing field, or a
                                          placement that could not be read

A REFUSAL IS THE USEFUL OUTPUT. It names the field and both values, so the pair is fixed by
changing one thing rather than by re-running both sides and hoping.

USAGE
    python3 pair_parity.py A.json B.json      # each: a bundle, or one entrant entry
    python3 pair_parity.py --self-test        # the controls: two directions, four cases
"""
import json
import os
import re
import sys

JOIN_FIELDS = ["ctx", "max_tokens", "temperature", "trials", "n_gpu_layers"]
MODEL_FLAGS = ("--model", "-m")
EPHEMERAL_FLAGS = ("--port", "--host")           # bound at launch; not configuration
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def load_entry(path):
    """A bundle (one entrant) or a bare entrant entry -> (entry, error)."""
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:                                        # noqa: BLE001
        return None, f"{path}: unreadable ({type(e).__name__})"
    if isinstance(d, dict) and d.get("harness") == "handicap-arena":
        res = d.get("results") or []
        if len(res) != 1:
            return None, (f"{os.path.basename(path)} carries {len(res)} entrants; "
                          f"a pair check compares ONE entrant from each side")
        return res[0], None
    if isinstance(d, dict) and ("sha256" in d or "gguf" in d):
        return d, None
    return None, f"{os.path.basename(path)} is neither a bundle nor an entrant entry"


def portable_flags(entry):
    """server_flags with the two values that are NOT configuration neutralised.

    The model path becomes the sha256 it points at (identity travels, location does not), and the
    bound port/host become <ephemeral>. Everything else is compared verbatim -- including -lv,
    because whether the placement evidence exists is itself part of how the entrant was served.
    """
    flags = list(((entry.get("config") or {}).get("server_flags")) or [])
    dig = (entry.get("sha256") or "?")[:12]
    out, i = [], 0
    while i < len(flags):
        f = flags[i]
        nxt = flags[i + 1] if i + 1 < len(flags) else None
        if f in MODEL_FLAGS and nxt is not None:
            out += [f, "sha256:" + dig]
            i += 2
            continue
        if f in EPHEMERAL_FLAGS and nxt is not None:
            out += [f, "<ephemeral>"]
            i += 2
            continue
        if f == entry.get("gguf"):
            out.append("sha256:" + dig)
            i += 1
            continue
        out.append(f)
        i += 1
    return out


def placement_state(entry):
    """(known?, realized_or_None, source, why) for one side."""
    w = entry.get("weigh_in") or {}
    requested = w.get("ngl_requested")
    realized = w.get("ngl_realized")
    source = w.get("placement_source") or "ABSENT (record predates the field)"
    if realized is not None:
        return True, realized, source, None
    if requested is not None:
        # A forced placement is declared by construction: the request IS the placement, and the
        # absence of the log line is a weaker statement than the request itself.
        return True, requested, f"declared-request ({source})", None
    return False, None, source, (
        "placement is AUTO-FIT and the realized layer count was not read, so two entrants at "
        "'auto-fit' are not two entrants at the same config")


def compare(path_a, path_b):
    a, err = load_entry(path_a)
    if err:
        return 2, [err]
    b, err = load_entry(path_b)
    if err:
        return 2, [err]
    out = []
    sa, sb = a.get("sha256"), b.get("sha256")
    out.append(f"A  identity sha256 {sa}")
    out.append(f"   location (NOT identity) {a.get('gguf')}")
    out.append(f"B  identity sha256 {sb}")
    out.append(f"   location (NOT identity) {b.get('gguf')}")

    refusals = []
    if not (isinstance(sa, str) and SHA_RE.match(sa)):
        refusals.append(f"A carries no well-formed sha256 ({sa!r}) -- identity unknown, nothing "
                        f"may be joined to it")
    if not (isinstance(sb, str) and SHA_RE.match(sb)):
        refusals.append(f"B carries no well-formed sha256 ({sb!r}) -- identity unknown, nothing "
                        f"may be joined to it")
    if not refusals and sa != sb:
        refusals.append(f"DIFFERENT WEIGHTS: {sa[:12]} vs {sb[:12]} -- these are two models, and "
                        f"no config parity can make them comparable")

    if not refusals:
        vca, vcb = a.get("card_version"), b.get("card_version")
        if vca != vcb:
            refusals.append(f"CARD DIFFERS: {vca!r} vs {vcb!r} -- cards are different instruments, "
                            f"and scores from different cards are different measurements")
        for f in JOIN_FIELDS:
            va, vb = (a.get("config") or {}).get(f), (b.get("config") or {}).get(f)
            if va != vb:
                refusals.append(f"CONFIG DIFFERS on {f}: {va!r} vs {vb!r}")
        fa, fb = portable_flags(a), portable_flags(b)
        if fa != fb:
            refusals.append("SERVING DIFFERS: server_flags (model path -> sha256, port/host -> "
                            f"<ephemeral>) are\n      A {fa}\n      B {fb}")

    ka, ra, srca, whya = placement_state(a)
    kb, rb, srcb, whyb = placement_state(b)
    out.append(f"A  placement realized {ra}  [{srca}]")
    out.append(f"B  placement realized {rb}  [{srcb}]")
    if not refusals:
        for known, why, side in ((ka, whya, "A"), (kb, whyb, "B")):
            if not known:
                refusals.append(f"PLACEMENT UNREAD on {side}: {why}")

    out.append(f"   config A {json.dumps({f: (a.get('config') or {}).get(f) for f in JOIN_FIELDS})}")
    out.append(f"   config B {json.dumps({f: (b.get('config') or {}).get(f) for f in JOIN_FIELDS})}")
    if refusals:
        return 1, out + [""] + [f"REFUSED  {r}" for r in refusals]
    if ra != rb:
        return 0, out + ["", f"CERTIFIED WITH A DECLARED PLACEMENT DIFFERENCE: A realized "
                             f"ngl={ra}, B realized ngl={rb}. Comparable, and now it is stated "
                             f"rather than assumed."]
    return 0, out + ["", f"CERTIFIED: same sha256, parity on {len(JOIN_FIELDS)} config fields and "
                          f"on the serving projection; both realizations ngl={ra}."]


# ------------------------------------------------------------------ controls
def _entry(sha, path, ctx=8192, mt=3000, ngl=None, realized=None, source="server-log",
           card="v4"):
    cfg = dict(temperature=0.0, max_tokens=mt, trials=1, ctx=ctx, n_gpu_layers=ngl,
               server_flags=["--model", path, "--ctx-size", str(ctx), "-lv", "4",
                             "--host", "127.0.0.1", "--port", "50267"])
    w = dict(ngl_requested=ngl, placement="forced" if ngl is not None else "auto-fit",
             footprint_gb=None, weights_gb=None, gpu_free_gb_at_weigh_in=None,
             partial_offload=False, division_from_resident=None, division_from_weights=None,
             division_for_competition=None, ngl_realized=realized, placement_source=source,
             layers_total=realized, memory_probe="server-log", footprint_measured=False)
    return dict(gguf=path, sha256=sha, weigh_in=w, config=cfg, card_version=card)


SHA = "3af1a1e75d43a8c9bfc3455de23be356d08e6948e841c96e4f07715f16c4120e"


def self_test():
    """FOUR CONTROLS. Two must certify and two must refuse -- a check that only ever passes is a
    caption, and a check that only ever refuses is a wall. All fixtures are synthetic and say so."""
    linux = "/home/chilly1/moltbook_pipeline/models/m.gguf"
    macos = "/Users/mikebird/Mac/iphone/Max/Max/m.gguf"
    cases = [
        ("path differs, identity same        -> CERTIFY",
         _entry(SHA, linux, realized=17), _entry(SHA, macos, realized=17), 0),
        ("same path, identity differs        -> REFUSE",
         _entry(SHA, linux, realized=17), _entry("00" * 32, linux, realized=17), 1),
        ("identity same, ctx differs         -> REFUSE",
         _entry(SHA, linux, realized=17), _entry(SHA, macos, ctx=4096, realized=17), 1),
        ("identity same, placement unread    -> REFUSE",
         _entry(SHA, linux, realized=None, source="ABSENT (record predates the field)"),
         _entry(SHA, macos, realized=17), 1),
        ("identity same, placements differ   -> CERTIFY WITH A DECLARED DIFFERENCE",
         _entry(SHA, linux, realized=17), _entry(SHA, macos, realized=33), 0),
        ("identity same, card differs        -> REFUSE",
         _entry(SHA, linux, realized=17, card="v1"), _entry(SHA, macos, realized=17, card="v4"), 1),
    ]
    bad = 0
    for name, a, b, want in cases:
        rc, lines = compare_files(a, b)
        ok = "ok " if rc == want else "FAIL"
        if rc != want:
            bad += 1
        print(f"  [{ok}] {name}  (exit {rc}, wanted {want})")
        if rc != want:
            for ln in lines:
                print(f"         {ln}")
    print(f"\n  {len(cases) - bad}/{len(cases)} controls behaved as declared")
    return 0 if bad == 0 else 1


def compare_files(a_entry, b_entry, tmpdir=None):
    """compare() over two in-memory entries: write them as one-entry bundles and run the real path."""
    import tempfile
    d = tmpdir or tempfile.mkdtemp(prefix="pair-parity-control-")
    pa, pb = os.path.join(d, "a.json"), os.path.join(d, "b.json")
    for p, e in ((pa, a_entry), (pb, b_entry)):
        with open(p, "w", encoding="utf-8") as f:
            json.dump(dict(harness="handicap-arena", version="1.0", results=[e]), f)
    return compare(pa, pb)


def main(argv):
    if len(argv) == 2 and argv[1] == "--self-test":
        print("pair_parity.py --self-test: synthetic control fixtures, both directions\n")
        return self_test()
    if len(argv) != 3:
        print(__doc__)
        return 2
    rc, lines = compare(argv[1], argv[2])
    print("\n".join(lines))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
