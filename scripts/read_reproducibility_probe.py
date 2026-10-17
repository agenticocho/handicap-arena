#!/usr/bin/env python3
"""READ REPRODUCIBILITY PROBE -- is a digest of this file reproducible on this box?

Written 2026-10-17 by Ocho for card t_cdd433bb, after `missile-command` measured (card t_ec0b0420,
MC_FIELD_PLAIN.md Finding A) that repeated sha256 of the same unchanged path in ARENA_MODELS returns
different values minutes apart.  The finding was right and the mechanism was unmeasured; this is the
instrument that measured it, kept so the numbers in DECISION_entrant_identity.md can be re-derived by
ONE COMMAND rather than taken on trust.

THREE PROBES, because a digest can only say "different", and three different things can make it so:

  --memory      a held in-memory buffer, re-scanned against a fresh regeneration of the same seeded
                pattern.  Nothing here touches a disk: a difference is the box corrupting data that
                was never stored.  Reports the rate, and whether the differences are single-bit.
  --controlled  a file this process WRITES and FSYNCs, then reads back and compares BYTE BY BYTE
                against the pattern, round after round, printing the file's own size/mtime/ctime/
                inode at every step.  This separates "the stored bytes are not what was written"
                (the same offsets differ every round) from "the reads are not what was stored"
                (different offsets, or none, each round).
  --file PATH   the whole file, hashed per chunk in more than one pass (buffered, cache-dropped,
                O_DIRECT), so a difference has an OFFSET; then one moved chunk re-read repeatedly,
                to see whether the same region moves every time.

NO HASH DECIDES ANYTHING IN --memory OR --controlled: those compare bytes.  The digests printed by
--file locate a difference; every one of them is accompanied by its offset.  The probe also prints,
for the same buffer, sha256/sha1/md5/crc32 -- four implementations, one buffer -- because a digest
that does not reproduce is not a bug in the reader until the reader has been excluded.

USAGE (memory-light; the sizes are the caller's)
  python3 scripts/read_reproducibility_probe.py --memory 256 --memory-rounds 40
  python3 scripts/read_reproducibility_probe.py --controlled /home/chilly1/chilly_containment/ocho_probe --mib 384 --controlled-rounds 5
  python3 scripts/read_reproducibility_probe.py --file ~/moltbook_pipeline/models/<an-entrant>.gguf

Inside the arena, run it under the guard like anything else:
  scripts/run_guarded.sh read-probe /home/chilly1/workspace/ocho_arena \
      python3 scripts/read_reproducibility_probe.py --memory 256 --memory-rounds 40

AND IT REPORTS ONLY WHAT IT RAN: the rounds, the sizes and the instant of every reading are printed,
because a rate without its interval is the "which interval" defect -- the fault measured here is
EPISODIC, so a quiet interval and a busy one give different numbers and both are true.
"""
import argparse, hashlib, mmap, os, random, sys, time, zlib

SEED = 20261017
MB = 1 << 20


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())


def meta(p):
    s = os.stat(p)
    return (f"size={s.st_size} mtime={s.st_mtime_ns} ctime={s.st_ctime_ns} ino={s.st_ino} "
            f"blocks={s.st_blocks}")


def digests(bufs):
    hs = [hashlib.sha256(), hashlib.sha1(), hashlib.md5()]
    crc = 0
    for b in bufs:
        for h in hs:
            h.update(b)
        crc = zlib.crc32(b, crc)
    return (f"sha256={hs[0].hexdigest()[:16]} sha1={hs[1].hexdigest()[:16]} "
            f"md5={hs[2].hexdigest()[:16]} crc32={crc & 0xffffffff:08x}")


def gen(nblk, seed=SEED):
    rng = random.Random(seed)
    return [rng.randbytes(MB) for _ in range(nblk)]


def compare(a, b, maxreport=6):
    """-> (nbytes, [(offset, a_byte, b_byte, xor, bits), ...])   byte-level, no hash"""
    nblk = min(len(a), len(b))
    n = 0
    out = []
    for i in range(nblk):
        x, y = a[i], b[i]
        if x == y:
            continue
        for j in range(min(len(x), len(y))):
            if x[j] != y[j]:
                n += 1
                if len(out) < maxreport:
                    z = x[j] ^ y[j]
                    out.append((i * MB + j, x[j], y[j], z, bin(z).count("1")))
    return n, out


def read_buffered(path, chunk=8 * MB):
    out = []
    with open(path, "rb", buffering=0) as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            out.append(b)
    return out


def read_odirect(path, chunk=8 * MB):
    out = []
    fd = os.open(path, os.O_RDONLY | os.O_DIRECT)
    buf = mmap.mmap(-1, chunk)
    mv = memoryview(buf)
    try:
        off = 0
        while True:
            k = os.preadv(fd, [mv], off)
            if k == 0:
                break
            out.append(bytes(mv[:k]))
            off += k
    finally:
        mv.release()
        buf.close()
        os.close(fd)
    return out


def drop_cache(p):
    fd = os.open(p, os.O_RDONLY)
    try:
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
    finally:
        os.close(fd)


def memory_probe(mib, rounds):
    print(f"\n=== MEMORY (no disk; no hash decides anything) {mib} MiB held, {rounds} rounds, seed {SEED}")
    pat = gen(mib)
    total = diffs = hit_rounds = single = multi = 0
    t0 = time.time()
    for r in range(rounds):
        ref = gen(mib)
        n, sample = compare(pat, ref)
        total += mib * MB
        if n:
            hit_rounds += 1
            diffs += n
            for off, ab, bb, x, bits in sample:
                if bits == 1:
                    single += 1
                else:
                    multi += 1
                print(f"  round {r:3d} offset {off:>12} held=0x{ab:02x} regenerated=0x{bb:02x} "
                      f"xor=0x{x:02x} bits={bits}   at {now()}")
            if n > len(sample):
                print(f"  round {r:3d} ... {n - len(sample)} more difference(s) in this round")
        del ref
    print(f"  rounds with any difference {hit_rounds} of {rounds}; bytes compared {total} "
          f"({total / (1 << 30):.2f} GiB)")
    print(f"  differing bytes {diffs}; single-bit {single} multi-bit {multi}")
    if diffs:
        print(f"  rate {diffs / total:.3e} per byte = 1 per {total / diffs / 1e6:.1f} MB")
    print(f"  elapsed {time.time() - t0:.1f}s")
    return diffs


def controlled_probe(d, mib, rounds):
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "known.bin")
    print(f"\n=== CONTROLLED WRITE + FSYNC, THEN BYTE-COMPARE READ-BACK\n    {p}  ({mib} MiB, {rounds} rounds)")
    pat = gen(mib)
    if os.path.exists(p):
        os.unlink(p)
    with open(p, "wb", buffering=0) as f:
        for b in pat:
            f.write(b)
        f.flush()
        os.fsync(f.fileno())
    print(f"  written and fsynced   {meta(p)}   at {now()}")
    clean = 0
    for r in range(rounds):
        buf = read_buffered(p, MB)          # 1 MiB blocks: the pattern's own block size, so the
        n, sample = compare(pat, buf)       # comparison is position-by-position and not two grids
        clean += 1 if n == 0 else 0
        print(f"  round {r}: {n} differing byte(s)   {meta(p)}   at {now()}")
        for off, ab, bb, x, bits in sample:
            print(f"      offset {off:>12} pattern=0x{ab:02x} read=0x{bb:02x} xor=0x{x:02x} bits={bits}")
        del buf
    print(f"  rounds that read back exactly what was written: {clean} of {rounds}")
    print(f"  digests of the pattern        {digests(pat)}")
    print(f"  digests of one fresh read     {digests(read_buffered(p))}")


def file_probe(path, chunk_mib, repeats):
    print(f"\n=== FILE {path}\n    {meta(path)}   at {now()}")
    ch = chunk_mib * MB
    nch = (os.path.getsize(path) + ch - 1) // ch
    passes = {}
    for name in ("buffered", "cold", "O_DIRECT"):
        if name == "cold":
            drop_cache(path)
            bufs = read_buffered(path, ch)
        elif name == "buffered":
            bufs = read_buffered(path, ch)
        else:
            bufs = read_odirect(path, ch)
        h_all = hashlib.sha256()
        for b in bufs:
            h_all.update(b)
        passes[name] = [hashlib.sha256(b).hexdigest()[:16] for b in bufs]
        print(f"  pass {name:9s} whole-file sha256 {h_all.hexdigest()[:16]}   {len(bufs)} chunks   at {now()}")
        del bufs
    moved = [i for i in range(nch) if len({passes[n][i] for n in passes}) > 1]
    print(f"  chunks whose digest moved between passes: {len(moved)} of {nch}"
          f"   {moved[:12]}{' ...' if len(moved) > 12 else ''}")
    for i in moved[:6]:
        print(f"    chunk {i:3d} off {i * ch:>12}  " + "  ".join(f"{n}={passes[n][i]}" for n in passes))
    idx = moved[0] if moved else 0
    seen = []
    for _ in range(repeats):
        with open(path, "rb", buffering=0) as f:
            f.seek(idx * ch)
            seen.append(hashlib.sha256(f.read(ch)).hexdigest()[:16])
    print(f"  chunk {idx} re-read {repeats} times: {len(set(seen))} distinct digest(s) {sorted(set(seen))}")
    print(f"  {meta(path)}   at {now()}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--memory", type=int, metavar="MIB", help="held-buffer re-scan")
    ap.add_argument("--controlled", metavar="DIR", help="write+fsync then byte-compare read-back")
    ap.add_argument("--file", help="whole-file per-chunk passes, then one chunk re-read")
    ap.add_argument("--mib", type=int, default=384, help="size for --controlled")
    ap.add_argument("--memory-rounds", type=int, default=40, help="rounds for --memory")
    ap.add_argument("--controlled-rounds", type=int, default=5, help="rounds for --controlled")
    ap.add_argument("--chunk-mib", type=int, default=64, help="chunk size for --file")
    ap.add_argument("--chunk-repeats", type=int, default=8)
    a = ap.parse_args()
    if not (a.memory or a.controlled or a.file):
        ap.print_help()
        return 1
    print(f"read_reproducibility_probe   host={os.uname().nodename}   {now()}")
    if a.memory:
        memory_probe(a.memory, a.memory_rounds)
    if a.controlled:
        controlled_probe(a.controlled, a.mib, a.controlled_rounds)
    if a.file:
        file_probe(a.file, a.chunk_mib, a.chunk_repeats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
