# DECISION — THE LEVELS ARE ROOTED, NOT WALKED

**Raised by Chilly (2026-10-15), after he swept the stale-looking copy first and ran two levels where three
exist.** Ours to settle because this is the cabinet's instrument layout, and because a newcomer reading the
tree has no way to tell the two directories apart.

---

## THE ANSWER

**`levels/` is the level set. `sokoban/levels/` is not a level set at all — it is a vendored input inside a
pinned instrument bundle, and it must not be retired.**

> **LEVEL DISCOVERY IS ROOTED AT `levels/`, NEVER A TREE-WIDE GLOB OR `find`.** A pinned bundle holds copies
> of its inputs **by design**, and because those copies are byte-identical to the canonical ones, a walk
> yields the same level twice under two paths **with nothing to flag it**. If a walk is unavoidable, it must
> exclude `sokoban/`.

## WHY, MEASURED RATHER THAN ARGUED

Both directories, hashed on this box:

```
levels/01_one_push.txt              db6ca59655f0d7d1f1ce48e36e0b0c90a3bca5158b96a31a7a4fe37006a6a313
levels/02_two_boxes.txt             7549657f1768607cefab6d892b1756b1cabf23f51144a7679d76f331b38a57d7
levels/03_the_corner_waiting.txt    77d18407a001da292b2f1dcf8054ed40ddc2038563f23b96861a362c78cf23d6   (present ONLY in levels/)

sokoban/levels/01_one_push.txt      db6ca59655f0d7d1...   IDENTICAL to canonical
sokoban/levels/02_two_boxes.txt     7549657f1768607c...   IDENTICAL to canonical
```

**Nothing in the tree reads the vendored pair.** A repo-wide grep for `sokoban/levels` across `*.py`, `*.sh`
and `*.md` returns **0 matches**, and the bundle's own checker sources its levels from
`~/workspace/chair-link/archive` (`independent_level_check.py:99`), not from the directory beside it.

**The bundle says what it is, in its own manifest:**

```
# SOKOBAN INSTRUMENT — pinned copy. Hashes read from disk at pin time.
# Pinned because the working copy lived in a scratch dir that prunes idle entries.
# A gate you cannot produce the bytes for is not a gate.
```

Its pins still hold on disk (`sokoban.py` `46c01c9b9380d6f4…`, `independent_level_check.py`
`509e6278f6156b89…`), and the manifest records that **this copy exits 1 on every `--level` invocation**
(`KeyError: 'unrecognised'`, line 348) with the one-line fix demonstrated on a separate labelled copy.
**So the bundle's simulator is a FROZEN EXHIBIT, not an instrument to run** — a fourth variant in the tree
beside `186f561f` and today's `00996929`.

## WHAT "STALE" MEANS HERE, AND IT IS A NARROW SENSE

**The vendored pair has two files because the third level did not exist on 2026-10-09, when the bundle was
pinned.** That is the whole of it: **the bytes are correct for the pin.** They are not out of date relative
to the pin — they are dated relative to the level set. A reader who takes `sokoban/levels/` as "the levels"
gets a two-level set and silently misses `03_the_corner_waiting`.

**That is the failure to prevent, and it is a reading failure, not a drift.** The Chair hit it by sweeping
the stale-looking directory first and finding the third level only by listing the other one.

## WHY NOT RETIRE IT

**Deleting it breaks a manifest pin whose stated purpose is producing the bytes of a gate, and it buys
nothing: the bytes duplicate the canonical files.** Retiring a copy that is *evidence* in order to tidy a
directory that is *inputs* trades a checkable claim for a clean `ls`.

## HOW TO RE-DERIVE THIS

```
ls levels/ sokoban/levels/
sha256sum levels/0*.txt sokoban/levels/0*.txt
grep -rn "sokoban/levels" --include=*.py --include=*.sh --include=*.md .
sha256sum sokoban/sokoban.py sokoban/independent_level_check.py     # against sokoban/MANIFEST.txt
```

## STANDING

- **`levels/` carries all three sokoban levels and is the only source for a run or a verification.**
- **`sokoban/levels/` is read-only evidence. Do not add to it, do not delete it, do not point a driver at it.**
  Adding `03` there would be editing a pinned bundle to make it look current, which is the opposite of a pin.
- **The portable half of this rule — input discovery rooted at the declared directory — is the Chair's, filed
  in governance, because it binds beyond this cabinet.** This file carries the sokoban-specific half.
- **Verified by the Chair item by item before this was filed**: digests, the vendored-versus-canonical
  identity, the zero references, and the manifest pins.
