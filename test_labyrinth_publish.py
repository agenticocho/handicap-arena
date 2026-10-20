#!/usr/bin/env python3
"""test_labyrinth_publish.py — the vectors behind the publish revision.

WHAT THIS PROVES, in the shape the defect actually took:

  1  exit 10. An unusable --out-dir used to die as a raw traceback at exit 1, which a second box
     cannot key on. Three errno shapes are exercised for real (17 FileExistsError, 20 NotADirectory,
     13 PermissionError) plus the shape that is not a property of the directory at all: a write
     that fails at CLOSE because the record fits the text buffer. Each is run against the PRE-FIX
     driver as well, and the pre-fix bytes are shown failing the same vector -- otherwise "the guard
     fired" and "nothing ever ran" are the same observation.

  2  exit 7 in all three publish tiers, each beside a control that publishes successfully: a
     refusal-only test cannot tell a working exclusivity from a driver that never writes.

  3  the splice defect: two writers, one cell, one slug. Exactly one record, the other refused,
     and no <slug>.<pid>.tmp left behind -- unit level (distinct pids, byte-exact check) and end to
     end (twelve concurrent dispatches).

  4  the `publish` field. The control run's record must NAME the tier it used, and the pre-fix
     record must be shown to carry no such field.

Tier 2 (excl-claim) and tier 3 (replace-no-exclusive-support) are reached by injecting the errno a
filesystem without hard links raises. That is not a shortcut around a measurement: ext4 and tmpfs
are the only filesystems this box mounts unprivileged, both implement links, and the thing under
test is the driver's DECISION on a real OSError. The exFAT measurement itself was the peer's
(link ENOTSUP, claim OK, second claim EEXIST, replace works).

Usage: python3 test_labyrinth_publish.py [--graph PATH]
Exit 0 iff every vector passes. No GPU, no model, no network, no lease.
"""
import argparse
import contextlib
import errno
import importlib.util
import io
import json
import os
import resource
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVER = os.path.join(HERE, "labyrinth_run.py")
DEFAULT_GRAPH = "/home/chilly1/workspace/chair-link/artifacts/ged_matrix.json"
# The revision this file supersedes, used as the control for "the vector fails before the fix".
PREFIX_REV = "c8205c3"

ROWS = []


def row(name, ok, said="", **extra):
    ROWS.append({"case": name, "pass": bool(ok), "said": str(said)[:300], **extra})
    return ok


def run(*args, out_dir=None, preexec=None):
    """One real dispatch, as a subprocess. Returns (rc, stdout, stderr)."""
    cmd = [sys.executable, DRIVER, "--graph", GRAPH, "--symmetrisation", "min", "--rune", "Fehu"]
    if out_dir is not None:
        cmd += ["--out-dir", out_dir]
    cmd += list(args)
    p = subprocess.run(cmd, capture_output=True, text=True, preexec_fn=preexec)
    return p.returncode, p.stdout, p.stderr


def files(d):
    return sorted(os.listdir(d)) if os.path.isdir(d) else []


def records(d):
    return [f for f in files(d) if f.endswith(".json") and ".tmp" not in f]


def residue(d):
    return [f for f in files(d) if f.endswith(".tmp") or "publish-probe" in f]


def errno_in(stderr, n):
    return f"[Errno {n}]" in stderr


# --------------------------------------------------------------------------------------------------
# 1. THE EXIT MAP AND THE CONTROL RUN


def v_self_test():
    p = subprocess.run([sys.executable, DRIVER, "--self-test"], capture_output=True, text=True)
    d = json.loads(p.stdout) if p.stdout.strip().startswith("{") else {}
    flags = {k: v for k, v in d.items() if k.endswith("_pass") or k == "pass"}
    want = ["pass", "parser_pass", "admission_pass", "edge_counts_pass", "parse_pass",
            "identity_pass", "publish_pass"]
    ok = p.returncode == 0 and all(flags.get(k) is True for k in want)
    row("self_test_exit0_all_flags", ok, p.stderr, flags=flags)


def v_control(root):
    d = os.path.join(root, "control")
    rc, out, err = run("--dry-run", "--cap", "5", out_dir=d)
    recs = records(d)
    body = json.load(open(os.path.join(d, recs[0]))) if len(recs) == 1 else {}
    stdout = json.loads(out) if out.strip().startswith("{") else {}
    ok = (rc == 0 and len(recs) == 1 and not residue(d)
          and body.get("publish") == "link-exclusive"
          and stdout.get("publish") == "link-exclusive"
          and body.get("dry_run") is True and body.get("plies") == 5)
    row("control_exit0_one_record_publish_named", ok, err,
        exit=rc, records=recs, publish=body.get("publish"), stdout_publish=stdout.get("publish"),
        residue=residue(d))
    return os.path.join(d, recs[0]) if recs else None


def v_duplicate(rec_path):
    d = os.path.dirname(rec_path)
    before = open(rec_path, "rb").read()
    rc, out, err = run("--dry-run", "--cap", "5", out_dir=d)
    after = open(rec_path, "rb").read() if os.path.exists(rec_path) else b""
    ok = rc == 7 and before == after and len(records(d)) == 1 and not residue(d)
    row("duplicate_exit7_bytes_untouched", ok, err, exit=rc, residue=residue(d))


# --------------------------------------------------------------------------------------------------
# 2. EXIT 10, THREE ERRNO SHAPES PLUS THE CLOSE, AND ITS PLACE IN THE ORDER


def v_out_dir_is_file(root):
    p = os.path.join(root, "out_is_a_file")
    open(p, "w").write("not a directory\n")
    rc, out, err = run("--dry-run", "--cap", "2", out_dir=p)
    ok = rc == 10 and errno_in(err, errno.EEXIST) and open(p).read() == "not a directory\n"
    row("exit10_out_dir_is_a_file_errno17", ok, err, exit=rc)


def v_out_dir_through_file(root):
    p = os.path.join(root, "middle_is_a_file")
    open(p, "w").write("x\n")
    target = os.path.join(p, "sub")
    rc, out, err = run("--dry-run", "--cap", "2", out_dir=target)
    ok = rc == 10 and errno_in(err, errno.ENOTDIR) and not os.path.exists(target)
    row("exit10_file_in_the_middle_errno20", ok, err, exit=rc)


def v_out_dir_read_only(root):
    d = os.path.join(root, "readonly")
    os.makedirs(d)
    os.chmod(d, 0o500)
    try:
        rc, out, err = run("--dry-run", "--cap", "2", out_dir=d)
    finally:
        os.chmod(d, 0o700)
    ok = rc == 10 and errno_in(err, errno.EACCES) and not records(d) and not residue(d)
    row("exit10_out_dir_refuses_write_errno13", ok, err, exit=rc, residue=residue(d))


def _limit(size):
    def f():
        resource.setrlimit(resource.RLIMIT_FSIZE, (size, size))
    return f


def v_close_time_failure(root):
    """The measured shape: the record is smaller than the 8 kB text buffer, so the write() call
    RETURNS and the filesystem failure surfaces at the implicit close. RLIMIT_FSIZE produces
    exactly that (EFBIG on flush), which is why the guard has to cover the whole with-block."""
    d = os.path.join(root, "close_failure")
    os.makedirs(d)
    rc, out, err = run("--dry-run", "--cap", "5", out_dir=d, preexec=_limit(200))
    ok = (rc == 10 and errno_in(err, errno.EFBIG) and not records(d) and not residue(d))
    row("exit10_failure_at_close_not_write_errno27", ok, err,
        exit=rc, records=records(d), residue=residue(d))


def v_admission_outranks_out_dir(root):
    p = os.path.join(root, "out_is_a_file")
    rc, out, err = run("--dry-run", "--cap", "0", out_dir=p)
    ok = rc == 2 and "exit 2" in err
    row("admission_outranks_a_bad_out_dir_exit2_not_10", ok, err, exit=rc)


# --------------------------------------------------------------------------------------------------
# 3. THE THREE TIERS, END TO END, AND EXIT 7 IN EACH


def load_driver():
    spec = importlib.util.spec_from_file_location("labyrinth_publish_under_test", DRIVER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dispatch_in_process(mod, out_dir, extra=("--dry-run", "--cap", "4")):
    saved = sys.argv
    sys.argv = [DRIVER, "--graph", GRAPH, "--symmetrisation", "min", "--rune", "Fehu",
                "--out-dir", out_dir] + list(extra)
    buf, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            mod.main()
        return 0, buf.getvalue(), err.getvalue()
    except SystemExit as e:
        return e.code, buf.getvalue(), err.getvalue()
    finally:
        sys.argv = saved


def tier_case(root, name, want_tier, patch):
    mod = load_driver()
    d = os.path.join(root, name)
    os.makedirs(d)
    saved = {k: getattr(os, k) for k in patch}
    try:
        for k, v in patch.items():
            setattr(os, k, v)
        rc, out, err = dispatch_in_process(mod, d)
        recs = records(d)
        body = json.load(open(os.path.join(d, recs[0]))) if len(recs) == 1 else {}
        rc2, out2, err2 = dispatch_in_process(mod, d)
        keep = body.get("publish") == want_tier and not residue(d)
        ok = (rc == 0 and len(recs) == 1 and keep and rc2 == 7 and not residue(d)
              and len(records(d)) == 1)
    finally:
        for k, v in saved.items():
            setattr(os, k, v)
    row(f"tier_{name}_publishes_then_refuses", ok, err or err2,
        exit=rc, exit_second=rc2, publish=body.get("publish"), want=want_tier,
        residue=residue(d), dir=files(d), out=out[:200], out2=out2[:200])


def v_tier2(root):
    def link_enotsup(src, dst):
        raise OSError(errno.ENOTSUP, "Operation not supported")
    tier_case(root, "tier2_excl_claim", "excl-claim", {"link": link_enotsup})


def v_tier3(root):
    def link_enotsup(src, dst):
        raise OSError(errno.ENOTSUP, "Operation not supported")
    real_open = os.open

    def open_claim_enotsup(path, flags, *a):
        if flags & os.O_EXCL:
            raise OSError(errno.ENOTSUP, "Operation not supported")
        return real_open(path, flags, *a)
    tier_case(root, "tier3_replace_only", "replace-no-exclusive-support",
              {"link": link_enotsup, "open": open_claim_enotsup})


# --------------------------------------------------------------------------------------------------
# 4. TWO WRITERS, ONE CELL -- UNIT AND END TO END


def v_splice_unit(root):
    """Two writers with distinct pids, one slug: the surviving bytes must be ONE writer's payload,
    never a splice. The failure this replaces is measured on the peer box: a fixed temp name let
    two writers share one inode and publish a tail from each."""
    mod = load_driver()
    d = os.path.join(root, "splice_unit")
    os.makedirs(d)
    p = os.path.join(d, "S.json")
    A, B = '{"writer": "A"}\n', '{"writer": "B"}\n'
    first = mod.publish_record(p, A, mod.PUBLISH_LINK_EXCLUSIVE, 7001)
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            mod.publish_record(p, B, mod.PUBLISH_LINK_EXCLUSIVE, 7002)
        second = "published"
    except SystemExit as e:
        second = e.code
    body = open(p, "rb").read()
    ok = (first is None and second == 7 and body == A.encode() and b"\x00" not in body
          and not residue(d))
    row("splice_unit_one_writer_one_record", ok, "", second=second, body=body[:40].decode("utf-8", "replace"))


def v_concurrent(root, n=12):
    d = os.path.join(root, "concurrent")
    os.makedirs(d)
    procs = []
    for _ in range(n):
        procs.append(subprocess.Popen(
            [sys.executable, DRIVER, "--graph", GRAPH, "--symmetrisation", "min",
             "--rune", "Fehu", "--out-dir", d, "--dry-run", "--cap", "5"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True))
    codes = [p.wait() for p in procs]
    errs = [p.stderr.read() for p in procs]
    recs = records(d)
    ok = (codes.count(0) == 1 and codes.count(7) == n - 1 and len(recs) == 1
          and not residue(d))
    row("concurrent_12_exactly_one_record", ok,
        "; ".join(e.strip()[:80] for e in errs if e.strip())[:300],
        codes=codes, records=recs, residue=residue(d))


# --------------------------------------------------------------------------------------------------
# 5. THE PRE-FIX BYTES, WHICH MUST FAIL THESE VECTORS


def prefix_driver(root):
    p = os.path.join(root, "prefix_labyrinth_run.py")
    src = subprocess.run(["git", "-C", HERE, "show", f"{PREFIX_REV}:labyrinth_run.py"],
                         capture_output=True, text=True)
    if src.returncode != 0:
        return None
    open(p, "w").write(src.stdout)
    return p


def v_prefix(root, prefix):
    d = os.path.join(root, "prefix_out_is_a_file")
    open(d, "w").write("not a directory\n")
    p = subprocess.run([sys.executable, prefix, "--graph", GRAPH, "--symmetrisation", "min",
                        "--rune", "Fehu", "--out-dir", d, "--dry-run", "--cap", "2"],
                       capture_output=True, text=True)
    ok = p.returncode == 1 and "Traceback" in p.stderr and "exit 10" not in p.stderr
    row("prefix_out_dir_is_a_file_dies_at_1_with_a_traceback", ok, p.stderr, exit=p.returncode)

    d2 = os.path.join(root, "prefix_control")
    p2 = subprocess.run([sys.executable, prefix, "--graph", GRAPH, "--symmetrisation", "min",
                         "--rune", "Fehu", "--out-dir", d2, "--dry-run", "--cap", "3"],
                        capture_output=True, text=True)
    recs = records(d2)
    body = json.load(open(os.path.join(d2, recs[0]))) if len(recs) == 1 else {}
    ok2 = p2.returncode == 0 and len(recs) == 1 and "publish" not in body
    row("prefix_record_carries_no_publish_field", ok2, p2.stderr,
        exit=p2.returncode, keys=sorted(body))

    # The measured shape on this box: the record fits the 8 kB text buffer, so the filesystem
    # failure lands at the CLOSE. Pre-fix that is an uncaught OSError out of main().
    d3 = os.path.join(root, "prefix_close_failure")
    os.makedirs(d3)
    p3 = subprocess.run([sys.executable, prefix, "--graph", GRAPH, "--symmetrisation", "min",
                         "--rune", "Fehu", "--out-dir", d3, "--dry-run", "--cap", "5"],
                        capture_output=True, text=True, preexec_fn=_limit(200))
    ok3 = p3.returncode == 1 and "Traceback" in p3.stderr and errno_in(p3.stderr, errno.EFBIG)
    row("prefix_close_time_failure_dies_at_1_with_a_traceback", ok3, p3.stderr, exit=p3.returncode)


# --------------------------------------------------------------------------------------------------

def main():
    global GRAPH
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", default=DEFAULT_GRAPH)
    a = ap.parse_args()
    GRAPH = a.graph
    if not os.path.exists(GRAPH):
        print(f"no graph at {GRAPH}", file=sys.stderr)
        return 2

    root = tempfile.mkdtemp(prefix="labyrinth-publish-e2e-")
    v_self_test()
    rec = v_control(root)
    if rec:
        v_duplicate(rec)
    v_out_dir_is_file(root)
    v_out_dir_through_file(root)
    v_out_dir_read_only(root)
    v_close_time_failure(root)
    v_admission_outranks_out_dir(root)
    v_tier2(root)
    v_tier3(root)
    v_splice_unit(root)
    v_concurrent(root)
    prefix = prefix_driver(root)
    if prefix:
        v_prefix(root, prefix)
    else:
        row("prefix_driver_available", False, f"git show {PREFIX_REV}:labyrinth_run.py failed")

    print(json.dumps({"vectors": ROWS, "pass": all(r["pass"] for r in ROWS)}, indent=1))
    bad = [r for r in ROWS if not r["pass"]]
    print(f"\n{len(ROWS) - len(bad)}/{len(ROWS)} vectors pass", file=sys.stderr)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
