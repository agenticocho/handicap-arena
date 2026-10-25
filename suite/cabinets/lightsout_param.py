#!/usr/bin/env python3
"""lightsout_param.py — the registered 3x3 Lights Out instrument, parameterised at the URL/model
boundary only.

The instrument (prompt text, parser, scorer, fixture, label recomputation) is
probes/lightsout/arm2_3x3_same_conditions.py, imported by path and left unmodified. This wrapper
sets BASE / MODEL / OUT and calls its main(), so the prompt is byte-identical to the registered
arm and no fork of the instrument exists to drift from it.

Recorded per row by the instrument itself: verdict, claim, parse_path, presses, out_of_range,
completion_tokens, answer_block, raw.
"""
import argparse
import importlib.util
import sys

ARM2 = "/home/chilly1/workspace/ocho_arena/probes/lightsout/arm2_3x3_same_conditions.py"


def load(path, name="arm2"):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    arm2 = load(ARM2)
    # the only three things this wrapper touches; the prompt is untouched
    arm2.BASE = a.base.rstrip("/") + "/v1/chat/completions"
    arm2.MODEL = a.model
    arm2.OUT = a.out
    print(f"[lightsout_param] instrument {ARM2}")
    print(f"[lightsout_param] prompt sha256 "
          f"{__import__('hashlib').sha256(arm2.PROMPT.encode()).hexdigest()}")
    print(f"[lightsout_param] base {arm2.BASE} model {arm2.MODEL} max_tokens {arm2.MAX_TOKENS}")
    arm2.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
