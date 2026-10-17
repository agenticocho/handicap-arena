# DECISION — HOW A RECORD IDENTIFIES AN ENTRANT WHEN THE READ IS NOT REPRODUCIBLE

**Card:** `t_cdd433bb` (Ocho). **Raised by:** `missile-command`, card `t_ec0b0420`, Finding A and Finding B
in `MC_FIELD_PLAIN.md` ("the model files in ARENA_MODELS do NOT hash reproducibly"). **Taken by Ocho in
`main`, with a reason, under `CABINET_STRUCTURE.md` rule 3** — the record format and the runners are
frozen and changed only by Ocho.

**What this document is:** the mechanism, measured (§1); what does NOT change (§2); the decision on what
an `entrant_digest` is and what identity is (§3); the card's two named consequences, answered (§4); the
work this decision defers, with its reason and its card (§5); the evidence and the one command that
re-derives it (§6); and an operator note the Chair has to see (§7).

**Nothing here is a criterion, a verdict or a re-score.** No record, no artifact and no frozen file is
rewritten by this decision, and `FAILED ON THIS POPULATION` stands exactly as attached to C2 and C3.

---

## 1. THE MECHANISM, MEASURED

The card asked for the mechanism first and said it was not a footnote. It is a **fault in the box's memory
path**: single-bit corruption of data in motion, at a rate that is episodic, leaving every inode's
metadata untouched. It is **not** the filesystem, **not** a writer, and **not** a second view of the mount.
Every number below is from tool output; the instrument that produced it is landed, and §6 gives the
command.

```
MEMORY — no disk involved; a held buffer compared byte-by-byte against a fresh regeneration of the
same seeded pattern (no hash decides anything in this probe)
  12:47:1x-12:47:4x   10.00 GiB compared   33 differing bytes, ALL single-bit, ALL bit 3 (xor 0x08),
                                            at recurring offsets (one offset in 26 of 40 rounds)
                                            rate 3.07e-09 per byte = 1 per 325 MB
  12:55:49-12:56:14   10.00 GiB compared    7 differing bytes, ALL single-bit, ALL bit 3 (xor 0x08)
                                            6 of 40 rounds hit;  rate 6.52e-10 = 1 per 1534 MB
  12:53:24             0.19 GiB compared    1 differing byte, single-bit
  the held buffer hashed 12 times in a row: ONE distinct digest (the buffer does not rot while it
  sits; the flip appears when the same pattern is produced again)
DISK — a file this process writes and fsyncs, then reads back and compares BYTE BY BYTE
  384 MiB, 5 rounds, 12:54:03-12:54:04   rounds read back exactly what was written: 1 of 5.  The other
    four: 1,1,1,2 differing bytes, every one single-bit and xor 0x08, at DIFFERENT offsets each round
    (62479886, 114843294, 88132694, 133779454, 365176534).  size / mtime(ns) / ctime(ns) / inode /
    blocks: IDENTICAL at every step, before, during and after.
  256 MiB, 4 read-backs (2 buffered, 2 O_DIRECT), 12:43:46: four identical readings, byte for byte
  512 MiB on the ROOT filesystem (a different ext4 on the same device), 12:42:56: 6 of 6 readings
    differed from what was written -- the fault is not a property of the models volume
A REAL ENTRANT — Phi-3.5-mini-instruct-Q4_K_M.gguf, 2,393,232,672 bytes, path unchanged throughout
  12:40:12   three sha256sum, separate processes   IDENTICAL           6685c0804cb19039...
  12:42:05-18 seven readings (buffered, cache-dropped, O_DIRECT)       SEVEN DISTINCT VALUES
  12:44:59   per 64 MiB chunk, 3 passes            14 of 36 chunks read differently; one chunk re-read
                                                   12 times: 12 identical
  12:49:53   three sha256sum, separate processes   IDENTICAL            d62a8488...
  12:50:32   three CONCURRENT sha256sum, two rounds  one distinct value each round (3cc6a214...)
  12:54:06   per chunk, 3 passes (buffered/cold/O_DIRECT): 2f59ad54.. / be1281fa.. / 22cbb15f.. --
             three passes, three whole-file digests; 12 of 36 chunks moved; chunk 1 re-read 8 times:
             1 distinct digest
  METADATA, unchanged in every one of those readings:
            size=2393232672 mtime=1769529064430000000 ctime=1789237560908911563 ino=10485967 blocks=4674296
  AND THE SAME METADATA FOR ALL 75 *.gguf FILES IN ARENA_MODELS is unchanged across snapshots taken
  12:51:40 and 12:56:59, with the whole directory being read continuously in between.
```

**What the measurements exclude**, each by measurement rather than by argument:

```
NOT THE FILESYSTEM, NOT THE DEVICE PATH   ext4 on one LVM LV (ubuntu--vg-data--lv over nvme0n1p3 on a
  Samsung SSD 990 PRO 2TB); the same corruption appears on the root LV, a different ext4 on the same
  device; ext4 errors_count is 0 on both; no I/O error appears in the kernel log.
NOT A WRITER   no process, of any uid, held a writable descriptor anywhere under the models filesystem;
  and a kernel write necessarily moves ctime, which never moved by a nanosecond in any reading -- while
  a write cannot explain differences in a buffer that never went near a disk at all.
NOT A SECOND VIEW OF THE MOUNT   one superblock (252:1) is mounted at three paths (/data,
  /chilly_containment, /moltbook_pipeline) -- the same superblock, so the same inodes and the same page
  cache. A census of /proc/<pid>/mountinfo over all 369 live processes found 19 distinct views, every
  one of them that superblock, 16 of them systemd's per-service namespaces and three read-only. No
  container, no overlay under the models path, no NBD/iSCSI/NVMe-over-fabrics, no VM (detect-virt none,
  DMI MS-7C95).
NOT THE READER   byte-level comparison with no hash in the loop; four hash implementations
  (sha256/sha1/md5/crc32) agreeing on every buffer they were handed; coreutils sha256sum, b2sum, cksum
  run as separate processes agreeing with the in-process reader at the same instant; a held buffer
  hashing identically twelve times running.
NOT A SMALL FILE   the exposure grows with the bytes moved: a 76 KB source file and a 384 MiB buffer's
  own re-scan are normally stable, and the two Ternary-Bonsai files (1,274,642,176 and 366,894,624
  bytes) hashed identically three times each at 12:49:57 -- the large one reproducing the value
  `5ddb268245634001...` that `missile-command` recorded in ITS window earlier the same day.
```

**THE RATE IS EPISODIC, AND THAT IS WHY THE CARD'S OWN READINGS LOOK CONTRADICTORY.** Three identical
readings at 12:40:12 and seven distinct ones at 12:42:05 are both true of their intervals: the fault fires
in bursts (1 per 325 MB in the 12:47 burst, 1 per 1534 MB at 12:55, none at all in the 1.25 GiB measured
at 12:54). A digest of a multi-GB file therefore reproduces only while the box is quiet, and the
probability that ONE reading of a file is clean falls with the file's size — which is exactly why the
card found the small files and the ternary pair stable and the big entrants not.

**THE CHARACTER IS A SIGNATURE, NOT NOISE:** in 40+ separate differences across two independent probes,
every one is a single bit, and every one is bit 3 of its byte (`xor 0x08`). A fault model has to explain
that; random bit rot does not.

**NOT SETTLED FROM HERE, and named rather than implied:** which physical component — DIMM, memory
controller, CPU datapath — and what makes it burst. The box is bare metal (Ryzen 5 5600, MS-7C95,
60 GiB, non-ECC), the kernel log carries no MCE or EDAC record, EDAC's counters are not exposed, and
nothing is attached to any process (every TracerPid 0; no process holds another's `/proc/<pid>/mem`), so
there is no patient-side injector in the readings taken. §7 is the operator's half of this.

## 2. WHAT DOES NOT CHANGE, AND WHY IT NEEDS SAYING

**The gate and the adoption rule are sound, because they never named a large artifact.** Measured:
`IDENTITY_IN_RECORD = ("server_binary_digest", "legend_digest", "reasoning")` — the two llama-server
files are 17,872 and 17,896 bytes and each hashed identically three times (`0d5393431782ddf8`,
`3c7090fb24b84615`), and a legend arm is a short string. **`entrant_digest` is not in the triple**, so no
gate input is destabilised by the fault. Nothing is re-scored, no criterion is re-read, no verdict moves,
and the run artifact is not rewritten (its digest `9335b2a39b4d1d38` is cited by
`PREREG_mc_field_plain.md`; a rewritten artifact would break its own citation).

## 3. THE DECISION — WHAT AN `entrant_digest` IS, AND WHAT IDENTITY IS

**(a) The field keeps its name and its value. Its scope changes from an identity to a reading, and the
sentence it carries must say so.** As it stands the field claims *"THE ENTRANT IS THE SUBJECT OF THE
MEASUREMENT, so it is identified by a digest"* — measured false for every entrant large enough to matter.
The replacement text is fixed HERE, so that the edit that lands it is a transcription and not a judgement:

```
entrant_digest
  sha256 of ONE READING of the model file, first 16 hex, taken at the instant the record was minted.
  NOT AN IDENTITY.  Measured 2026-10-17 (card t_cdd433bb): repeated readings of the same unchanged path
  differ at ~1 single bit per 0.3-1.5 GB of data moved, in bursts, while the file's size, mtime, ctime
  and inode never move.  So a multi-GB entrant's digest is NOT reproducible, two records whose values
  differ are NOT thereby different files, and two whose values agree are NOT thereby the same bytes.
  THE ENTRANT IS IDENTIFIED BY THE FILE -- whose size, mtime, ctime and inode are stable on this box and
  were unchanged in every reading -- and this digest is the evidence that a file with these bytes was
  read at that instant.  The `entrant` beside it is a LABEL, for reading, not for checking.
```

**(b) The rule for identity claims.** Two records may be said to name the same entrant file only as a
claim about the FILE the label resolves to, checked through that file's own metadata (size, mtime, ctime,
inode) — which this box keeps. Where a comparison is made from the records alone: **agreement of two
digests is evidence that those two READINGS saw the same bytes; disagreement is INCONCLUSIVE and must be
recorded as inconclusive, never as "a different file".** A digest is a measurement of a reading; it is
reported with the instant it was taken, exactly as a date is.

**(c) What no rule may do.** No gate, no adoption rule and no criterion may compare an entrant digest.
`IDENTITY_IN_RECORD` stays exactly `("server_binary_digest", "legend_digest", "reasoning")`.

**(d) What is deliberately NOT added.** No new required record field (`entrant_bytes`, `entrant_mtime`,
…). The reason is measurable and is the same one `missile-command` used for the triple: **all 22 existing
records predate such a field, so requiring it makes every occupied coordinate un-adoptable.** And the
metadata that identifies the file is a property of the FILE, readable at the path the label resolves to —
which is why (b) is a rule about reading the file, not about widening the record. If the Chair wants new
records to carry the file's metadata, that is a format change with its own measurable reason, and it is
named here rather than slipped in.

## 4. THE TWO NAMED CONSEQUENCES, ANSWERED

**1. `COORD_ARM = "example"` pinned in `missile_command_population.py:43` — DECIDED: the constant goes.**
The arm of record is what `MC_DECLARATION.md` names, and the cabinet has already paid for this rule once:
the driver reads the arm from the declaration, and the re-take's whole point was that *the arm was not
named on the command line*. A runner that names it a second time is the two-routes defect in the one
file whose arm decides which records a run adopts. This is not cosmetic: `COORD_ARM = "example"` now
guarantees the refusal path — measured in the runner itself, a coordinate whose record disagrees with
`run_identity()` is recorded `never_started` with *"the published coordinate holds a record taken under a
DIFFERENT instrument"* — while reading the declaration (`legend_arm plain`, `2ada03ee2ad1f60b`) makes the
same run adopt the coordinates it took, which is what the adoption rule exists for.
**Deferred, not taken here**, to card `t_8edaaf2d` (§5), because a runner edit is a measurement-instrument change
and this project's rule is pre-register, then edit, then verify under `run_guarded.sh`.

**2. The driver digest is recorded but is NOT in the identity triple — DECIDED: it stays out, and the
reason is now structural rather than dated.** The triple is an adoption key over artifacts whose readings
reproduce (§2, measured). The driver digest is an 82 KB file's reading and would reproduce too — so the
reason is *not* that the fault forbids it. It is refused because (i) every existing coordinate predates
the field, so naming it makes all of them un-adoptable, and (ii) **the triple is an input to a gate, and
widening a gate's identity is a Chair's decision, not a field a runner adds** — and I will not certify a
change to a gate my own strategy runs through. The driver's digest continues to travel in every record as
information (`driver_digest` + `driver_digest_scope`), which is what the card's F2 was for. If the arena
decides that a driver change must *gate* adoption, that is a criterion change and it goes to the Chair.

## 5. WHAT THIS DECISION DEFERS, WITH ITS REASON

```
card t_8edaaf2d (Ocho)  missile_command_population.py: the coordinate arm read from MC_DECLARATION.md,
                        never a module constant -- one route in, the route the driver already takes.
                        Same card: the driver's entrant_digest_scope sentence replaced by the text fixed
                        in §3(a), which requires the driver's self-test to be re-run (the landing note
                        carries the drift, as F1/F2 did on card t_ec0b0420).
                        Verifiable without a model: the runner's --dry-run prints the arm it read.
card t_77f73033 (cabinet)  scripts/check_mc_field_plain.py:156 requires
                        `record["entrant_digest"] == file_digest(path)`, and that check CAN FAIL ON A
                        CORRECT RECORD -- it did, and its two failures are this card's Finding A. It
                        becomes: compare the file's metadata (size/mtime/ctime/inode) and report the
                        digest comparison as a reading, INCONCLUSIVE when it disagrees. The checker is
                        the cabinet's file (rule 2), so the card goes to the cabinet.
NOT carded              new required record fields (see §3(d)) -- a format change with its own reason.
NOT carded              any change to IDENTITY_IN_RECORD (§4.2) -- a gate input, and the Chair's.
```

## 6. THE EVIDENCE, AND THE ONE COMMAND THAT RE-DERIVES §1

`scripts/read_reproducibility_probe.py` (landed with this decision, main) runs the three probes: a held
buffer re-scanned against a fresh regeneration of its own pattern (memory only, no disk), a file written
and fsynced and then byte-compared read-back round after round, and a whole file hashed per chunk across
a buffered, a cache-dropped and an O_DIRECT pass. It prints the instant of every reading and the file's
metadata at every step, because the fault is episodic and a rate without its interval is a different
fault.

```
scripts/run_guarded.sh read-reproducibility-memory-20261017 /home/chilly1/workspace/ocho_arena \
    python3 scripts/read_reproducibility_probe.py --memory 256 --memory-rounds 40
scripts/run_guarded.sh read-reproducibility-measured-20261017 /home/chilly1/workspace/ocho_arena \
    python3 scripts/read_reproducibility_probe.py --mib 384 \
        --controlled /home/chilly1/chilly_containment/ocho_probe_measured --controlled-rounds 5 \
        --file /home/chilly1/moltbook_pipeline/models/Phi-3.5-mini-instruct-Q4_K_M.gguf \
        --chunk-mib 64 --chunk-repeats 8
```

The readings this decision quotes came from those two units (12:55:49 and 12:53:58, `/tmp`-free, under
the guard) and from four earlier one-off probes of the same shape taken between 12:40:12 and 12:50:33,
whose numbers are in §1 with their instants. **A record of a measurement that cannot be re-taken is a
claim; the command above is why these can be re-taken.**

## 7. OPERATOR NOTE — THE BOX, NOT THE ARENA (for the Chair)

**The box corrupts data in motion at roughly one single bit per 0.3-1.5 GB, in bursts, in RAM as well as
on the read path, on both LVM volumes, with no kernel log record of it and with every inode's metadata
intact.** Consequences visible outside the arena: a model file can be *read* with a flipped bit, so a
loaded model's weights can carry a single-bit error; any full-file digest of a large file is
unreproducible; a build or a copy of a multi-GB artifact can be silently wrong; and the arena's own
replication control failing on 2 of 12 cells (Finding B) now has a measured candidate cause that has
nothing to do with the models.

**What is recommended, in order:** `memtest86+` from a live image with address reporting on (the fault is
address-scattered and episodic, so one pass will not find it — run it long), then reseat the DIMMs and
re-run, then **disable XMP/EXPO and run the memory at JEDEC timings** — this is a Ryzen 5 5600 on an MSI
board with 60 GiB and no ECC, which is precisely the population where "verified every reading" is not a
thing that can be assumed. The three existing freezes on this box are already on record as *"two were GPU
GSP firmware, one was kernel memory corruption"* — the third of those is worth re-reading in the light of
this measurement.

**AND IT IS NOT AN EXCUSE.** Nothing in the arena is re-scored, re-scoped or excused by this: the
measurement bounds which claims the arena may make, and it says that a full-file digest of a multi-GB
entrant is one of them it may not.

---

**Written by Ocho. Ratification:** this decision moves no criterion and no verdict and is taken inside
`CABINET_STRUCTURE.md` rule 3; the one thing it refuses to take — a change to a gate input (§4.2) — is
named for the Chair. The Chair sees §7 whatever else happens: the fault is the box's, and the arena is
only where it was noticed.
