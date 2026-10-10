#!/usr/bin/env python3
"""vram_holder -- WHO HOLDS THE CARD. Ruling 82: the failure must name the holder.

    "model failed to load"  ->  "the card is held by llama-swap-brain (pid 409710, 5532 MiB) under a mode=run
                                 lease; not reclaimable while its pid is alive"

BECAUSE THE CURRENT MESSAGE IS INDISTINGUISHABLE FROM A BROKEN MODEL, A BAD PRESET OR A CORRUPT FILE -- and an
agent will retry forever while the operator reads a load error. Measured on this box: the runtime failed to load
a model five times, and the log said only `failed to load`, while the actual cause was a live seat lease holding
5.5 of 8 GB under a policy that never reclaims it.

THIS IS THE FOURTH INSTANCE OF ONE RULE. Every one of these reports a condition of the INSTRUMENT in the
grammar of a failure of the SUBJECT:

    finish_reason=length               we stopped it        -- looked like "no answer"
    capped-deliberation-missing-value  we cut it            -- looked like an illegal move
    budget_confounded                  we capped the turns  -- looked like a failed model
    model failed to load               the card was HELD    -- looked like a broken model

READ ONLY. This reports tenancy; it never touches a lease, never kills a process, and never changes a policy.
Releasing a lease touches infrastructure other agents depend on, and that is not a decision a diagnostic makes.
"""
import json
import os
import re
import subprocess

LEASE_DIR = os.path.expanduser("~/.local/state/gpu-lease")


def _run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout if r.returncode == 0 else ""
    except Exception:                                                   # noqa: BLE001
        return ""


def tenants():
    """-> [(pid, mib)] from nvidia-smi. Empty means no tool or no holders -- both are reported as unknown."""
    out = _run(["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader"])
    found = []
    for line in out.splitlines():
        m = re.match(r"\s*(\d+)\s*,\s*(\d+)\s*MiB", line)
        if m:
            found.append((int(m.group(1)), int(m.group(2))))
    return found


def leases():
    """-> [(owner, need, mode, pid)] from the lease RECORDS. The OWNER is what the message needs.

    THE RECORD IS JSON. My first version looked for `owner=` as a key=value line, found nothing, and reported
    "NO LEASE RECORD" for every tenant -- WHICH WAS A FALSE STATEMENT ABOUT THE HOLDER, produced by a reader that
    did not match the file it was reading. It is the same defect class as a field name taken from memory: the
    reader has to be checked against the thing it reads, not against what it expects.
    """
    found = []
    lease_d = os.path.join(LEASE_DIR, "lease.d")
    if not os.path.isdir(lease_d):
        return found
    for fn in sorted(os.listdir(lease_d)):
        try:
            with open(os.path.join(lease_d, fn)) as f:
                rec = json.load(f)
        except (OSError, ValueError):
            continue
        if isinstance(rec, dict) and rec.get("owner"):
            found.append((rec.get("owner"), rec.get("need_mib"), rec.get("mode"), rec.get("pid")))
    return found


def holder_sentence():
    """THE SENTENCE. Names the holder, the memory, and the policy -- or says honestly that it could not tell."""
    t = tenants()
    ls = leases()
    if not t and not ls:
        return ("  AND THE HOLDER IS UNKNOWN -- no tenants reported and no lease records found. THIS IS NOT THE "
                "SAME AS NOBODY HOLDING IT: an unreadable cause is reported as unreadable, never as absent.")
    parts = []
    for owner, need, mode, pid in ls:
        live = pid and os.path.exists(f"/proc/{pid}")
        mem = ""
        for tpid, tmib in t:
            if pid and tpid == pid:
                mem = f", {tmib} MiB"
                break
        parts.append(f"{owner} (pid {pid or '?'}{mem}) under a {mode or '?'} lease"
                     f"{' -- LIVE, so NOT reclaimable at any age' if live else ' -- not alive, reclaimable'}"
                     f"{f', need {need} MiB' if need else ''}")
    for tpid, tmib in t:
        if not any(pid == tpid for _o, _n, _m, pid in ls):
            parts.append(f"pid {tpid} ({tmib} MiB) holding the card with NO LEASE RECORD")
    total = sum(m for _p, m in t)
    return f"  AND THE CARD IS HELD BY: {'; '.join(parts)}.  Tenants total {total} MiB."


def self_test():
    s = holder_sentence()
    print("  holder_sentence() ->")
    print(s)
    ok = isinstance(s, str) and len(s) > 20
    print(f"  returns a sentence: {'YES' if ok else 'NO'}")
    return ok


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        sys.exit(0 if self_test() else 1)
    print(holder_sentence())
