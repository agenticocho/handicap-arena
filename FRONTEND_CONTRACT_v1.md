# THE HANDICAP ARENA — FRONT-END CONTRACT

## v1

**Status:** **IN FORCE** — both signatures present. Mike: the contract as a whole, 2026-10-14.
Ocho: §8's four clauses only, 2026-10-14, with the gates now executable. See SIGN-OFF below.
**Author:** Jarvis's `arena` bot · **Date:** 2026-10-07
**Supersedes:** nothing. This is the first contract for the front end.
**Normative parents:** `FORMAT.md` (rules and version numbering), `BELTS.md` (grading),
`FRONTEND_CONTRACT_ACCEPTANCE.md` (the four gated clauses).

---

## SIGN-OFF

Two signers, two scopes. **This contract is in force only when both are present** — one of two is
not a signed contract, and a draft that reads as in force is worse than a draft.

| signer | scope | date |
|--------|-------|------|
| **Mike** | the contract as a whole — the instrument, its four items, its frozen ground truth. Commission: build the Arcade against it. | 2026-10-14 |
| **Ocho** | **§8's four clauses only** (`FRONTEND_CONTRACT_ACCEPTANCE.md`). Layout, aesthetics, interaction and every product decision are Chair's and are not his to gate. | 2026-10-14 |

**Ocho's verification, flags and holds:** `FRONTEND_CONTRACT_SIGN_OFF_OCHO.md` — the signer's own
record, which carries what this table cannot: the artifacts behind the gates at their revisions, the
five flags, and the two holds.

**Consequence of Mike's signature alone:** the front end is **commissioned** and may be built against
this contract, with the four clauses binding as they already stand in
`FRONTEND_CONTRACT_ACCEPTANCE.md` — **but the contract is not yet the settled instrument**, and any
choice still marked *Overturn* in §0–§6 may change when Ocho answers §11.

**What Ocho's signature adds:** the four clauses become gated rather than merely written, and §11's
ten questions get answered by the only party whose answers bind — *"each is cheap to reverse now and
expensive to reverse after anything is built on it."*

---

## 0. How to read this draft

This contract covers exactly the four items `FORMAT.md §8` leaves open, plus the rendering rules
that make them safe to ship. **Every choice below carries two lines:**

- **Why** — the measurement or the reading that produced it.
- **Overturn** — the sentence Ocho writes to reverse it, and what changes if he does.

Ocho gates **four clauses only** (`FRONTEND_CONTRACT_ACCEPTANCE.md`). Layout, aesthetics, interaction
and product decisions are Chair's and are not up for review. **The clause-satisfaction map is §8.**

**This is a `v1` contract.** `v1` is a **release** number, from the project line in `FORMAT.md §9`
(FORMAT is normative; README points at it). `card_version` is a **separate axis** naming the task
suite. Today's state is **card v2 on project v0.1**. Two numbers, two axes. **The front end is v1.**

---

## 1. Ground truth — what this contract binds to

Nothing below is asserted from memory. Every value carries the command that derives it; §10 holds
the full derivations. If a value here disagrees with re-running its command, **the command wins and
this document is wrong.**

### 1.1 The harness CLI (frozen — v0.1, as built)

    python3 arena.py --self-test
    python3 arena.py --model <path.gguf> --card <v1|v2> --ctx <N> --max-tokens <N> --out <bundle.json>
    python3 arena.py --grade <bundle.json>
    python3 arena.py --biathlon <bundle.json>... --penalty-k <k>
    python3 arena.py --relay <A,B[,C]>

`arena.py` takes `--card` with `choices=["v1","v2"]`. **The suite is selected by `--card`.** That is
the only supported way to name a task suite, and it is what makes clause 3 enforceable in software.

**Why:** read from `arena.py`'s own `argparse` block, not from a document about it.
**Overturn:** adding a card version means adding a `choices` entry and a suite hash — not changing
this contract.

### 1.2 The locked task suites (frozen — with hashes)

A suite is a directory of task JSON. `tasks/` is card v1; `tasks/v2/` is card v2. The suite hash is
over `sha256( relpath ‖ 0x00 ‖ filebytes ‖ 0x00 )` for each task file in sorted `relpath` order.

| card_version | suite dir | task files | `suite_sha256` |
|---|---|---|---|
| `1` (or **absent** — see §5.1) | `tasks/` | 3 | `c9ca5d5d6c4a35d4917b55cfc854de95361627abe11a25c5bfbb339e20738489` |
| `2` | `tasks/v2/` | 3 | `b3bc04b1b03878e673ca7783b1e262d8c0ad79622d48dfba10063f2423d34366` |

**Why:** "locked task suite" (`FORMAT.md §8`) has to mean a byte-exact artefact or it means nothing.
Derived in §10.2.
**Overturn:** if the hash function changes, every signature made under the old rule must be marked
with the hash rule it used. Changing the hash silently invalidates every existing signature.

### 1.3 The field as it stands (derived, not carried)

| quantity | command | value |
|---|---|---|
| result bundles | `ls results/*.json \| wc -l` | **91** |
| graded bundles (`results != []`) | §10.1 | **75** |
| scratched bundles (`results == []`) | §10.1 | **16** |
| graded on card v1 (absent `card_version`) | §10.1 | **42** |
| graded on card v2 (`card_version == 2`) | §10.1 | **33** |
| bundles carrying an absolute `/home/` path | §10.6 | **75** |
| bundles with `certification == "OPEN (self-reported)…"` | §10.1 | **75 of 75** |

**Every one of these is produced by a command in §10.** None is typed in from memory. That is the
rule this project runs on: *a hand-maintained count is a claim with no check behind it.*

---

## 2. Identity model

Three things, kept separate. Conflating any two of them is the class of error this project exists to
avoid.

**The entry** — the thing that fights. Identified by the **`sha256` of the GGUF**, never by name,
never by path, never by alias. An alias called `granite-8b` served Qwen3.5-9B; the hash cannot be
argued with (`README.md`; `FORMAT.md §7`).

**The operator** — the human or machine that ran it. Identified by an **Ed25519 public key** (§4).
An operator may hold many entries. An entry has exactly one operator key at a time, because the key
is what makes a submission attributable.

**The division** — the weight class. Assigned by **measured footprint**, and the measurement that
decides is stated in §7.4d. A division is a property of *an entry as served on a machine*, not of a
model in the abstract.

**Why:** `FORMAT.md §2` "measured, not declared"; `FORMAT.md §7` confound 4.
**Overturn:** none recommended. Every alternative reintroduces a confound already measured.

---

## 3. ITEM 1 — How a challenge is issued and accepted

### 3.1 Shape

A challenge is a **document**, not an event. It has two halves: the terms, and two signatures. It is
issued by writing it, accepted by counter-signing the *same bytes*, and it is **live only when both
signatures are present over identical terms.**

    challenge.json
    {
      "challenge_id":   "<sha256 of the canonical terms block>",
      "terms": {
        "issued_utc":   "2026-10-07T18:00:00Z",
        "challenger":   "<entry sha256>",
        "defender":     "<entry sha256>",
        "division":     "Lightweight",
        "card_version": 2,
        "suite_sha256": "b3bc04b1…",
        "deadline_utc": "2026-11-06T18:00:00Z",
        "title_staked": false
      },
      "signatures": [
        { "key": "<challenger op key>", "role": "challenger", "sig": "<base64>" },
        { "key": "<defender   op key>", "role": "defender",   "sig": "<base64>" }
      ]
    }

### 3.2 Issue

1. The challenger writes `terms`. `challenge_id` is `sha256(canonical_json(terms))` — **the id is the
   terms**, so two different challenges cannot share an id and a mutated term cannot keep one.
2. The challenger signs `terms` and appends its signature.
3. The document is **posted anywhere**. v1 needs no inbox: the challenger sends the JSON to the
   defender by any channel, and optionally registers it with the arena index.

### 3.3 Accept

1. The defender verifies: `challenge_id` recomputes; challenger's signature verifies; the two entries
   are in the stated `division`; `card_version` and `suite_sha256` are a known locked pair; the
   deadline has not passed.
2. The defender signs **the identical `canonical_json(terms)`** and appends its signature.
3. A challenge with **two** signatures over the same terms is **ACCEPTED** and enters the bout queue.
   A challenge with one is **ISSUED**. With none or a broken one, **VOID**.

**No scheduling. No simultaneous presence.** Both sides run the locked suite whenever they like,
inside the deadline, and submit (§6). That is `FORMAT.md §8`'s "bouts are asynchronous" made literal.

### 3.4 Terms a challenge may NOT change

`card_version` and `suite_sha256` are part of the terms, and they are a **matched pair**. A challenge
that names a `suite_sha256` not belonging to its `card_version` is **VOID** — not adjudicated, not
scored, not ranked. This is clause 3 enforced at the earliest possible point.

**Why:** clause 3 is a *hard partition*. The cheapest place to enforce a partition is before the bout
exists, because a bout that cannot be valid can then never produce an invalid table.
**Overturn:** if Ocho wants cross-version bouts, the contract must ship a **stated conversion**, and
there is none — the two cards grade different numbers of items with different semantics.

### 3.5 Expiry, refusal, silence

- **Silence is not a forfeit.** An unaccepted challenge expires and is void. A challenger cannot win
  a belt from an unanswered letter.
- **Refusal is permitted and public.** Refusing a sanctioned-title challenge is recorded and voids
  any standing "active champion" claim for the refusal window (`BELTS.md §4`, 180-day decay reused).
- **Expiry does not consume a title shot.**

**Why:** `BELTS.md §4` already makes titles decay on inactivity; reusing that number keeps one clock.
**Overturn:** Ocho may set a different default deadline. It is one constant.

---

## 4. ITEM 2 — What a "signed bundle" is

### 4.1 Key type

**Ed25519.** 32-byte public key, 64-byte signature, base64 in JSON.

- The **public key** is the operator's identity. It is published with every submission, so any third
  party can verify without the arena, and **the arena holds no secret that can forge a submission.**
- **One key, one purpose** (`BELTS.md` spirit; the Chair/Chilly rule). An operator key signs
  submissions and challenges and nothing else.

**Why:** asymmetric, so verification needs no shared secret; tiny keys and signatures; no ambient
authority. Delivery detail: Python's stdlib has no Ed25519, and the harness is **stdlib-only**
(`README.md` quickstart). So the primitive is **vendored as one pure-Python module**, matching the
existing zero-dependency constraint.

**Overturn — this is the choice most worth reversing, and it is cheap:**
Say *"use HMAC-SHA256"* and §4 becomes: a symmetric secret per operator, `hashlib`/`hmac` only, zero
new code. What is lost, stated plainly: (a) verification requires the secret, so the arena can forge
and a third party cannot verify; (b) a leaked secret is a forged identity with no public-key remedy;
(c) it proves nothing to a stranger, which is most of the point of a public board.
**If Ocho prefers "no new code" over "publicly verifiable", say so and this section is rewritten.**

### 4.2 Canonical form — what the signature is actually over

A signature over JSON is a signature over *bytes*, so the bytes are defined here, once.

    canonical_json(x):
      1. object keys sorted lexicographically by Unicode code point
      2. no insignificant whitespace: separators (",", ":")
      3. UTF-8, ensure_ascii=False
      4. every float rendered with format(x, '.6f')   # no repr(), no shortest-round-trip
      5. 'aggregate' is NOT a float — see 4.3
      6. no null-vs-missing ambiguity: emit missing keys as absent, never null

**Why 4:** the field stores the same score at different precisions — four values appear in two or
more forms and `0.8889` appears **three** ways (derived, §10.3):
`0.8888666666666666`, `0.8888888888888888`, `0.8889`. Two of those are the *same* submitted bytes
under `repr` and different bytes under the original producer's formatting. Fixing six decimals makes
the signed bytes independent of the producer's float hygiene.
**Why 6:** `card_version` is **absent** on 42 of 75 rows rather than `1` (§5.1). A canonical form
that materialises `null` would produce two byte-strings for one contract.

### 4.3 `aggregate` is signed as an exact rational, never a float

The signed payload carries `"aggregate": {"wins": <int>, "trials": <int>}` — the **integer counts** —
and the display value is derived from them (§5.2). No float is signed.

**Why — and this is the sharpest measurement in this document.** Two entries on card v2 have the
**same true score, 10 items of 18**, and different stored floats:

    R1,R2,R3 = (5,4,1)/6  -> stored aggregate 0.5555666666666667
    R1,R2,R3 = (5,3,2)/6  -> stored aggregate 0.5555333333333333

They differ because each round score was rounded to four decimals *before* being averaged. Under
`round(x, 4)` they do **not** collapse — they land on **0.5555** and **0.5556** (derived, §10.4).
**Rounding the aggregate is not a fix. It is a smaller version of the bug.** Integer counts are the
only normalisation that is exact by construction.

### 4.4 Exactly what is signed

**The whole bundle, minus the signature block, after path normalisation.**

    signature_block = {
      "scheme": "ed25519",
      "key": "<base64 public key>",
      "bundle_sha256": "<sha256 of the canonical bytes that were signed>",
      "sig": "<base64 signature over those bytes>",
      "signed_utc": "<ISO-8601>"
    }

The signed payload is the bundle entry with `signature` removed, `aggregate` replaced by its
`{wins, trials}` pair (§4.3), all floats formatted `%.6f`, and **all filesystem paths reduced to
basenames** (`gguf`, and every path appearing in `config.server_flags`).

**Why sign everything rather than a chosen subset:** a subset invites an argument about which fields
matter, and the fields that matter are exactly the ones someone will later want to change. Sign the
artefact.
**Why normalise paths *before* signing:** **75 of 91** bundles carry an absolute `/home/` path
(§10.6). A signature over unpublished bytes is unverifiable, and a bundle published to prove a claim
must not leak a filesystem layout. **Paths are not identity — the `sha256` is.**
**Overturn:** if Ocho wants the raw `server_flags` preserved verbatim in the published bundle, the
signature must then cover the redacted form and the document must say so; the alternative is
unverifiable signatures over published bundles, which is worse.

### 4.5 What a signature does and does not prove

**Proves:** *this operator key submitted these exact bytes.* Attribution and tamper-evidence.
**Does not prove:** that the run is honest, that the model is what the hash claims, or that the
latency is a local cadence. A signature is a **fingerprint, and fingerprints can be forged**
(`FORMAT.md §6`).

**Therefore every signed bundle in v1 is `OPEN (self-reported)` and `UNCERTIFIED`, in the same size
type as the score.** A signature is not a certification, and the UI must never let one read as one.

**Why:** `FORMAT.md §6` Tier 1. Confirming measured: `certification == "OPEN (self-reported) — re-run
by the arena to become CERTIFIED"` on **75 of 75** graded rows (§10.1).

---

## 5. ITEM 3 — How adjudication decides

### 5.1 The comparability gate — three checks, all must pass

Before any comparison, adjudication refuses unless:

1. **Same `card_version`.** Clause 3. Never compared across suites.
2. **Same `suite_sha256`**, and it is the locked hash for that `card_version` (§1.2).
3. **Neither side scratched.** `results == []` on either side means **that side has no measurement**
   — so the bout is **NO CONTEST**, not a win, not a loss, not a zero. Clause 2.

**`card_version` ABSENT means card v1.** Not `null`, not `"unknown"`. Mapped in **one named place**,
`card_of(entry)`, and nowhere else.

    def card_of(entry):                       # THE only mapping in the system
        cv = entry.get("card_version", None)
        return 1 if cv is None else cv        # absent -> card v1, explicitly

**Why:** raw values across all 75 graded rows are `2 → 33` and `absent → 42` (§10.1). A language
default must not decide this invisibly: treating absent as "unknown" drops all 42 v1 entries or
lumps them into a cohort that is exactly the failure clause 3 prevents.
**Overturn:** none. This is clause 3's mechanism.

### 5.2 Normalisation — the rule clause 1 depends on

    wins(e)   = sum(rounds[*].wins)          # integers
    trials(e) = sum(rounds[*].trials)        # integers
    exact(e)  = Fraction(wins, trials)       # exact, no float anywhere

**Sort, compare, rank and band on `exact(e)`.** The stored float `aggregate` is **never** the
comparison key; it is a display artefact of the producer's arithmetic and is discarded at the door.

    display(e) = f"{exact(e):.4f}"           # four decimals, display only

**Why four decimals for display:** the field's observed true scores are spaced at least `1/18` apart,
and `.4f` is injective on the *observed* values in both cards (§10.5) — so four decimals show every
distinction that exists without inventing one. It is a **display** choice; the comparison is exact.
**Why not `round(aggregate, 4)`:** it leaves 0.5555 and 0.5556 as different values for one true score
(§4.3, §10.4). Measured: `round(x,4)` yields **12** distinct v2 values where there are **11**.
**Overturn:** Ocho may choose a different display precision. He may **not** choose a float comparison
key — that reintroduces the bug in §10.4.

### 5.3 The decision rule

    if exact(A) >  exact(B):  A wins
    if exact(A) <  exact(B):  B wins
    if exact(A) == exact(B):  DRAW — no belt changes hands

Then, and only then:

- The winner's result is **flagged for Tier-2 re-run** (`FORMAT.md §6`, `§8`). v1 does not run it.
- A win **never** transfers a belt in v1. Belts require Tier-2 certification on arena hardware
  (`BELTS.md §1`, `FORMAT.md §6` Tier 3). v1 records **stripes** and a **record (W/L/D)** only.
- A `title_staked: true` bout's winner is recorded as **champion pending certification**.

**Why a DRAW rather than a tie-break:** after exact normalisation, an equal score *is* an equal
measurement. Any further tie-break (latency, footprint, stripes) is a **different measurement
wearing a comparator's clothes** — and `FORMAT.md §8` says latency is not comparable across
`placement` anyway (§7.4b). A draw is the only verdict that adds no information.
**Overturn:** Ocho may declare a deterministic tie-break. If he does, it must be named in the terms
*before* the bout, and it must be a measurement of the same thing — not a second axis.

### 5.4 Clause 3's table, drafted for N card versions

**ILLUSTRATIVE — not exhaustive.** Rows beyond v1 and v2 are placeholders showing where a future
card's row goes; they carry no values and must not be rendered as if they do.

| `card_version` | task suite | suite dir | one bout | round score | aggregate | graded entries on record | status |
|---|---|---|---|---|---|---|---|
| `1` (= **absent**) | retired 3-round card | `tasks/` | 3 rounds × 3 trials of one prompt | `wins / 3` | `mean of 3` = `k/9` | 42 | retired |
| `2` | 18-item battery | `tasks/v2/` | 3 rounds × 6 distinct items, one trial each | `items passed / 6` (partial credit inside R1) | `k/18` where no partial credit | 33 | current |
| `N` | *(future card)* | *(its dir)* | *(its shape)* | *(its rule)* | *(its rule)* | *(none)* | not designed |

**Every row is its own partition. No row is ever compared with another row.** The "graded entries on
record" column is derived (§10.1), never carried.

**The trap this table exists to show:** v1 rows carry **no `items{}` block** (`rounds[*].items` is
present on all 33 v2 rows and absent on all 42 v1 rows — §10.3). So a v1 round score of `wins/3`
takes **three discrete values** and a v2 round score takes **seven**. **Item-level saturation cannot
be computed for card v1 at all.** Therefore:

> **Any v1-vs-v2 contrast must label the metric per column.** The v1 column is a *model-level*
> measure; the v2 column can be an *item-level* one. They are not the same measurement, and placing
> them side by side without saying so implies a comparison the reader cannot make.

**Overturn:** Ocho may name further columns for future cards. He may not merge rows.

### 5.5 The decision record

Adjudication emits a small document, not a paragraph:

    decision.json
    {
      "challenge_id":     "<from §3.1>",
      "card_version":     2,
      "suite_sha256":     "b3bc04b1…",
      "verdict":          "A_WINS" | "B_WINS" | "DRAW" | "NO_CONTEST" | "VOID",
      "void_reason":      null | "different card_version" | "suite hash mismatch" | "scratched side",
      "a": { "entry": "<sha256>", "wins": 15, "trials": 18, "display": "0.8333" },
      "b": { "entry": "<sha256>", "wins": 14, "trials": 18, "display": "0.7778" },
      "reproduce": "python3 arena.py --grade <bundle.json>"
    }

**Every claim links to a reproducible command** (`FORMAT.md §8`). The `reproduce` field is that link,
and it is emitted by the adjudicator rather than written by hand.

---

## 6. ITEM 4 — How a Tier-1 submission is made

### 6.1 Produce

    python3 arena.py --self-test                                   # 1. validate the scorers first
    python3 arena.py --model /path/to/model.gguf \
                     --card v2 --ctx 8192 --trials 1 --max-tokens 3000 \
                     --out bundle.json                             # 2. run the locked suite

**`--self-test` is required, not suggested.** A scorer that only ever passes is not a scorer
(`README.md`). A submission that does not declare a passing self-test is **rejected at intake**.

### 6.2 Normalise, then sign

    bundle_norm = normalise_paths(bundle)        # basenames only (§4.4)
    payload     = canonical_json(strip_signature(bundle_norm))   # §4.2, aggregate as {wins,trials}
    signature   = { "scheme":"ed25519", "key":pub, "sig":sign(sk, payload),
                    "bundle_sha256": sha256(payload), "signed_utc": now }

**Order matters: normalise, then sign.** Signing first and redacting later produces a bundle nobody
can verify (§4.4).

### 6.3 Submit

    submission.json
    {
      "submitter_key":  "<base64 ed25519 public key>",
      "card_version":   2,                       # explicit; absence means 1 (§5.1)
      "suite_sha256":   "b3bc04b1…",
      "self_test":      { "passed": true, "harness_version": "1.0" },
      "bundle":         { … },
      "signature":      { … },
      "reproduce":      "python3 arena.py --grade <bundle.json>"
    }

### 6.4 Intake validation

All eight must pass. Any failure is a **rejection with the failing check named**, never a silent
score of zero.

1. `self_test.passed` is true.
2. `bundle.signature` verifies over the canonical payload (§4.2–§4.4).
3. `bundle.entry.sha256` is present and well-formed.
4. `card_version` is a **known** card, and `suite_sha256` is its locked hash (§1.2).
5. `config` is complete — `temperature`, `max_tokens`, `trials`, `ctx`, `n_gpu_layers`,
   `server_flags`. *A result without its config is not a result* (`FORMAT.md §4`).
6. No absolute path in the published form.
7. `results != []`. If `results == []`, the submission is **accepted as scratched** and renders as
   **no measurement** (clause 2) — it is not rejected and never scored 0.
8. `aggregate` is derivable from integer counts (§5.2).

### 6.5 What a Tier-1 submission earns

**Stripes and a record. Never a belt.** Belts require Tier-2 certification on arena hardware
(`BELTS.md §1`, `FORMAT.md §6` Tier 3). Every accepted submission is rendered
**`OPEN (self-reported)` / `UNCERTIFIED` — in the same size type as the score.**

**Why the same size type:** a caveat set smaller than the claim is not a caveat, it is a disclaimer
(`FORMAT.md §6`, Tier 1).

---

## 7. Rendering rules — Ocho's four clauses as product requirements

### 7.1 Clause 1 — sort on the aggregate; the belt is a label

- **Default sort is `exact(entry)` descending** (§5.2). Wherever a belt is shown, the aggregate is
  shown with it.
- **No belt-sorted default may exist anywhere.** Stated plainly, because it happened: under belt
  rule 1 the belt was **not monotonic** in the aggregate — `0.7222`, `0.7778` and `0.8333` each mapped
  to **both Green and Orange** (`FRONTEND_CONTRACT_ACCEPTANCE.md` §1). A belt-sorted view **ranks a
  weaker model above a stronger one.** Belt rule 2 bands the belt on the aggregate and is monotonic
  by construction (0 inversions, verified).
- **Check:** for any two entries where A's score exceeds B's, B is never placed above A; and no
  belt-sorted default exists. Failure is disqualifying.

### 7.2 Clause 2 — a scratch is no measurement, never zero

- **Key `scratched` off `results == []`, and nothing else. Never off the filename.**
- A scratched entrant renders as **"did not serve"**, visually distinct from a scored zero, and is
  **excluded from every average, ranking and comparison.**
- **Measured:** 16 bundles have `results == []` (§10.1). The `EMPTY` filename marker currently covers
  **16 of 16**, but the marker is a **convenience, not the data** — for a period it covered only 9 of
  16, and the 7 unmarked were exactly the v1 counterparts, which a filename-keyed UI would have
  rendered as **zeros**.
- **Check:** delete the filename convention in your head and re-derive. The view must still treat all
  16 correctly.

### 7.3 Clause 3 — `card_version` is a hard partition, and is not the release version

- Entries with different `card_version` **never** share a table, ranking, average or chart.
- Absent means **card v1**, mapped once (§5.1).
- **The front end is `v1`** in the sense of `FORMAT.md §9`. **"card v2" is a task suite, never a
  release.**
- **Check:** every occurrence of "v2" in UI copy is either the card version or provably not a release
  number; and no combined v1+v2 table exists.

### 7.4 Clause 4 — truncation is not a wrong answer; placement is not comparable

- **4a.** A trial that stopped on the token cap renders as **out of room**, visually distinct from a
  wrong answer. Signal: `rounds[*].finish_reasons` carrying `{length: n}`. **Measured** (§10.3): card
  v1 carries **36** truncated trials (22 of them in `R1_fencing`) and card v2 carries **25**. Read as
  wrong answers, all 61 lie.
- **4b.** **No latency figure appears without its `placement` beside it**, in the same visual unit.
  `auto-fit` and `ngl99` are different measurements and must not share a column, chart or average.
  **Measured** (§10.3): 71 of 75 graded rows carry `weigh_in.placement == "auto-fit"`; **4 carry no
  `weigh_in` block at all** and therefore **have no placement — so they may display no latency.**
- **4c.** `ngl` counts **layers, not bytes**. A fixed `ngl` is **not** a valid normaliser, because the
  same `ngl` is a different VRAM footprint per architecture. No copy may imply otherwise.
- **4d.** When `weigh_in.partial_offload` is true, **the division comes from weights**, and the
  resident footprint is shown as a reading of **the machine**, not of the model. Measured in-field:
  an entry at `footprint_gb: 5.37` with `weights_gb: 17.2` and `partial_offload: true` competes as
  **Heavyweight** (`division_for_competition`), having been `division_from_resident: Lightweight`.
  **Check:** the UI calls it Heavyweight *and* explains why a 5.37 GB reading is in that class.

---

## 8. Clause-satisfaction map

Ocho gates four clauses. This is where each is satisfied, stated so it can be checked mechanically.

| clause | satisfied in | mechanism |
|---|---|---|
| **1** — sort on the aggregate, belt is a label | **§5.2** (rule) · **§7.1** (requirement) · §5.3 (decisions) | `exact(e) = Fraction(sum(wins), sum(trials))`; belt never a key |
| **2** — scratch is no measurement, never zero | **§5.1.3** (gate) · **§6.4.7** (intake) · **§7.2** (render) | keyed on `results == []`, never the filename |
| **3** — `card_version` is a hard partition, not the release | **§3.4** (bout gate) · **§5.1.1–2** (adjudication gate) · **§5.1** (one mapping) · **§5.4** (N-version table) · **§7.3** | `card_of()` in one named place; suite hash matched to card |
| **4** — truncation ≠ wrong; placement ≠ comparable | **§7.4a–d** · §5.3 (why no latency tie-break) | `finish_reasons`, `placement`, `partial_offload`, `ngl`-is-layers |

**FAILS THIS REVIEW OUTRIGHT:** any belt-sorted default; any zero where a scratch belongs; any table
mixing `card_version` 1 and 2; any latency figure without placement; any copy treating "card v2" as a
release number; any division taken from a resident footprint when `partial_offload` is true.

---

## 9. What v1 does NOT do

**Catalogued is not implemented, and this contract does not blur it.** `GAMES.md` is a **design
catalogue**. Its own headings count **55 events across 10 leagues (A–J)** — derived by counting the
file's own headings, not by reading its prose (§10.7). Its build-order table (`PART 5`) is the **only
statement of what exists**, and it marks **I1/I2 as already existing** and **B1–B3, G3, G4 as already
built**.

**The running card is B1–B3: fencing, chess, pit stop. Three events.** Those are the only events this
contract offers an entrant. **Everything else in `GAMES.md` is specified, not built**, and the v1 UI
must present it that way — a catalogue entry with no implementation behind it, labelled as such.

**This is why no total in this document is typed in.** The drift is measured, not hypothetical:
`WHITEPAPER.md:186` says *"the full catalogue — 42 events across nine leagues"*, `GAMES.md`'s own
prose says *"Forty-plus events across nine leagues"*, and `GAMES.md`'s own headings count **55 events
across 10 leagues** while the file contains the literal `42` **zero** times (§10.7). Two prose
summaries, two different wrong numbers, over a catalogue that was right in front of them.
**A count living in a document that summarises a catalogue drifts from the catalogue.**

**This contract does not:**
- run Tier-2 certification — that is `v2` (`FORMAT.md §9`). v1 **flags** a winner for re-run and stops.
- award belts or dan grades — belts need Tier-2 on arena hardware (`BELTS.md §1`).
- offer any of the 55 catalogued events beyond B1–B3.
- publish anything. **75 of 91 bundles carry absolute `/home/` paths** (§10.6). Publication is Mike's
  call, not this contract's.
- claim any certification. Every result in v1 is **`OPEN (self-reported)` / `UNCERTIFIED`.**

### 9.1 The card v2 criteria — stated as they stand

`CARD_v2.md §5` froze four success criteria before the run. **Two failed.** Stated here so no later
reader, and no UI copy, can drift them:

| criterion (`CARD_v2.md §5`) | requirement | verdict |
|---|---|---|
| **1** — saturation falls | Green drops from 52% to **under 25%** | **FAILED** — 19/33 = **57.6%** under belt rule 1 |
| **2** — the gradient exists | ≥6 distinct aggregates, no value >40% | passes — 11 distinct, top 21.2% |
| **3** — the zero-side survives | **≥4** entries below 0.34 | **FAILED** — **2** entries below 0.34 |
| **4** — the trap items bite | ≥3 fail each trap | passes — 26 fail *no-tool-correct*, 5 fail *already-correct* |

> **Criterion 1 STANDS AS FAILED.** Belt rule 2 later moved Green to 8/33 = **24.2%**. **That is not
> a pass.** The instrument was changed *after* the run; **a re-derivation is not a re-scoring**, and a
> bar frozen before the run does not move because its author later moved the measurement. Any table
> showing Green under 25% without this paragraph is misleading.

**Why both verdicts are reproduced here:** measured directly from the bundles (§10.8) so the failure
is checkable rather than asserted. **Criterion 3 failed on the data — 2 entries below 0.34 against a
required 4 — and it is not reversible by any later rule change, because it counts aggregates.**
**Overturn:** none. This is a record, not a decision.

---

## 10. Derivation appendix

Every number in this document comes from one of these. `D` = the repo root.

**10.1 — bundle counts, card partition, certification.** Scratched is keyed on `results == []` only;
absence of `card_version` maps to 1.

    python3 - <<'EOF'
    import json, glob
    from collections import Counter
    d = [(p, json.load(open(p))) for p in sorted(glob.glob("results/*.json"))]
    scr = [p for p, x in d if x.get("results") == []]
    rows = [e for p, x in d if x.get("results") for e in x["results"]]
    card = lambda e: 1 if e.get("card_version") is None else e["card_version"]
    print("bundles", len(d), "| scratched", len(scr), "| graded", len(rows))
    print("card_version mapped:", dict(Counter(card(e) for e in rows)))
    print("raw card_version :", dict(Counter(repr(e.get('card_version')) for e in rows)))
    print("certification    :", dict(Counter(e.get("certification") for e in rows)))
    EOF

    bundles 91 | scratched 16 | graded 75
    card_version mapped: {2: 33, 1: 42}
    raw card_version : {'2': 33, 'None': 42}
    certification    : {'OPEN (self-reported) — re-run by the arena to become CERTIFIED': 75}

**10.2 — suite hashes.**

    python3 - <<'EOF'
    import glob, hashlib, os
    for d in ("tasks", "tasks/v2"):
        h = hashlib.sha256()
        for f in sorted(glob.glob(os.path.join(d, "*.json"))):
            h.update(os.path.relpath(f).encode()); h.update(b"\0")
            h.update(open(f, "rb").read());     h.update(b"\0")
        print(d, h.hexdigest())
    EOF

    tasks     c9ca5d5d6c4a35d4917b55cfc854de95361627abe11a25c5bfbb339e20738489
    tasks/v2  b3bc04b1b03878e673ca7783b1e262d8c0ad79622d48dfba10063f2423d34366

**10.3 — float forms, truncation, items, placement.**

    python3 - <<'EOF'
    import json, glob
    from collections import Counter, defaultdict
    d = [(p, json.load(open(p))) for p in sorted(glob.glob("results/*.json"))]
    rows = [e for p, x in d if x.get("results") for e in x["results"]]
    card = lambda e: 1 if e.get("card_version") is None else e["card_version"]
    g = defaultdict(set)
    for e in rows: g[round(e["aggregate"], 4)].add(repr(e["aggregate"]))
    print("float forms:", {k: sorted(v) for k, v in g.items() if len(v) > 1})
    t = Counter()
    for e in rows:
        for rn, r in (e.get("rounds") or {}).items():
            n = (r.get("finish_reasons") or {}).get("length")
            if n: t[(card(e), rn)] += n
    print("truncation:", dict(sorted(t.items())))
    print("rows with rounds[*].items:", dict(Counter(card(e) for e in rows if any("items" in v for v in (e.get("rounds") or {}).values()))))
    print("placement:", dict(Counter((e.get("weigh_in") or {}).get("placement") or "ABSENT" for e in rows)))
    EOF

    float forms: {0.3889: ['0.38889999999999997','0.3889'],
                  0.5556: ['0.5555555555555555','0.5555666666666667'],
                  0.7778: ['0.7777666666666666','0.7778'],
                  0.8889: ['0.8888666666666666','0.8888888888888888','0.8889']}
    truncation: {(1,'R1_fencing'):22, (1,'R2_chess'):3, (1,'R3_pitstop'):11,
                 (2,'R1_fencing'):2,  (2,'R2_chess'):9, (2,'R3_pitstop'):14}
    rows with rounds[*].items: {2: 33}
    placement: {'auto-fit': 71, 'ABSENT': 4}

**10.4 — why rounding does not fix the aggregate.**

    python3 - <<'EOF'
    import json, glob
    from fractions import Fraction
    from collections import Counter
    d = [(p, json.load(open(p))) for p in sorted(glob.glob("results/*.json"))]
    rows = [e for p, x in d if x.get("results") for e in x["results"]]
    card = lambda e: 1 if e.get("card_version") is None else e["card_version"]
    ex = lambda e: Fraction(sum(r.get("wins",0) for r in e["rounds"].values()),
                            sum(r.get("trials",0) for r in e["rounds"].values()))
    for cv in (1, 2):
        s = [e for e in rows if card(e) == cv]
        print(cv, "raw", len({repr(e['aggregate']) for e in s}),
                    "round4", len({round(e['aggregate'],4) for e in s}),
                    "exact", len({ex(e) for e in s}))
    s = [e for e in rows if card(e) == 2]
    for f, n in sorted(Counter(ex(e) for e in s).items()):
        fl = sorted({e["aggregate"] for e in s if ex(e) == f})
        if len(fl) > 1:
            print(f, "->", fl, "-> round4", sorted({round(x,4) for x in fl}))
    EOF

    1 raw 6 round4 6 exact 6
    2 raw 15 round4 12 exact 11
    5/9      -> [0.5555333333333333, 0.5555666666666667] -> round4 [0.5555, 0.5556]

**10.5 — four decimals are injective on the observed field.**

    round(x,4) keys mapping to more than one true score: card v1 none, card v2 none (§10.4).

**10.6 — absolute paths.**

    grep -l '/home/' results/*.json | wc -l     ->  75

**10.7 — the catalogue counts, from its own headings.**

    grep -c '^### [A-J][0-9]' GAMES.md   ->  55
    grep -c '^# LEAGUE [A-J] ' GAMES.md  ->  10

**10.8 — the card v2 criteria.**

    python3 - <<'EOF'
    import json, glob
    from fractions import Fraction
    from collections import Counter
    d = [(p, json.load(open(p))) for p in sorted(glob.glob("results/*.json"))]
    v2 = [e for p, x in d if x.get("results") for e in x["results"] if e.get("card_version") == 2]
    ex = lambda e: Fraction(sum(r.get("wins",0) for r in e["rounds"].values()),
                            sum(r.get("trials",0) for r in e["rounds"].values()))
    belt1 = lambda e: (lambda rw=sum(1 for r in e["rounds"].values() if r.get("wins",0)*2 > r.get("trials",1)): "Green" if rw==3 else "Orange" if rw>=2 else "Yellow" if rw>=1 else "White")()
    c = Counter(belt1(e) for e in v2)
    print("criterion 1: Green", c["Green"], "/", len(v2), "=", round(100*c["Green"]/len(v2),1), "%")
    dist = Counter(ex(e) for e in v2)
    print("criterion 2:", len(dist), "distinct, top", round(100*dist.most_common(1)[0][1]/len(v2),1), "%")
    print("criterion 3:", sum(1 for e in v2 if float(ex(e)) < 0.34), "entries below 0.34")
    it = lambda e, r, i: ((e["rounds"][r].get("items") or {}).get(i) or {}).get("score")
    print("criterion 4: fail R2.4 =", sum(1 for e in v2 if it(e,"R2_chess","R2.4_no_tool_correct")==0.0),
          "| fail R3.6 =", sum(1 for e in v2 if it(e,"R3_pitstop","R3.6_already_correct")==0.0))
    EOF

    criterion 1: Green 19 / 33 = 57.6 %      <- pre-registered bar: under 25%  -> FAILED
    criterion 2: 11 distinct, top 21.2 %     -> passes
    criterion 3: 2 entries below 0.34        <- required >= 4                -> FAILED
    criterion 4: fail R2.4 = 26 | fail R3.6 = 5   -> passes

---

## 11. Open questions for Ocho

Everything below is a decision this draft had to make that belongs to you. Each is cheap to reverse
now and expensive to reverse after anything is built on it.

**Q1 — Signature scheme.** I chose **Ed25519**, vendored as one pure-Python module, because it makes
a submission verifiable by a stranger and leaves the arena holding no secret that can forge one. It
breaks the harness's "stdlib only, no pip" property, at the cost of ~100 vendored lines.
**Alternative: HMAC-SHA256** — zero new code, but symmetric: verification needs the secret, the arena
could forge, and a third party can verify nothing. *Which do you want: public verifiability, or no
new code?* (§4.1)

**Q2 — Do I have the normalisation right?** I discard the stored `aggregate` float entirely and
compare `Fraction(sum(wins), sum(trials))`. This is *stricter* than the acceptance clause, which asks
for a normalised comparison. I found the clause's premise is not enough on its own: `round(x, 4)`
still splits one true score (10/18) into 0.5555 and 0.5556. **Confirm that exact-rational-from-counts
is the intended reading**, or tell me the normalisation you want named. (§5.2, §10.4)

**Q3 — Ties.** I made an equal normalised score a **DRAW**, on the grounds that any tie-break is a
second axis wearing a comparator's clothes. If you want a winner for title bouts, name the tie-break
**and** confirm it is the same measurement. (§5.3)

**Q4 — Signing over redacted bytes.** To make a published bundle both verifiable and free of
`/home/` paths (75 of 91 carry one), I normalise paths to basenames **before** signing, so the
signature covers exactly the bytes a stranger sees. The alternative — sign verbatim, publish redacted
— produces signatures nobody can check. *Confirm redaction-before-signature.* (§4.4)

**Q5 — Refusal and silence.** I made silence a void (no forfeit) and refusal legal but recorded, with
a refused sanctioned-title challenge voiding the "active champion" claim for the same 180-day window
`BELTS.md §4` already uses. Is refusal-recorded-and-voiding the behaviour you want, and is 180 days
the right window? (§3.5)

**Q6 — Deadline default.** I set no default; `deadline_utc` is required in the terms. Is there a
default you want the UI to pre-fill, and if so, how long? (§3.1)

**Q7 — Display precision.** I show four decimals because `.4f` is injective on every observed score
in both cards and shows no distinction that does not exist. Is four right, or would you rather show
the fraction (`10/18`) since that is the actual measurement? (§5.2)

**Q8 — The `items{}` asymmetry.** Item-level saturation is computable for card v2 and **impossible**
for card v1 — 33 rows carry `rounds[*].items`, 42 do not. I have written the rule as *label the
metric per column, or do not show the contrast*. Is there a v1-side metric you would rather see
paired against a v2 item metric, given they are not the same measurement? (§5.4)

**Q9 — Two failed criteria, one document.** Card v2's **criterion 1 failed at 57.6%** (belt rule 2
later reads 24.2%, which is *not* a pass) and **criterion 3 failed at 2 entries below 0.34 against a
required 4**. Both are reproduced in §9.1 with their derivations. **Confirm you want both carried in
the front-end contract** rather than only in `CARD_v2.md` — I put them here because a UI that shows
the field without them is the misleading table §5b warns about. If you would rather the contract cite
`CARD_v2.md` and not restate, say so and §9.1 becomes a pointer.

**Q10 — Where the challenge lives.** v1 needs no inbox: a challenge is a document that can travel any
channel, and only a two-signature document is live. If you want an arena-hosted challenge index in
v1, that is a service to build and a new attack surface — *is a board enough, or does it need to be
a service?* (§3.2)

### ANSWERS — Ocho, 2026-10-14

**These are answers, not amendments.** Each confirms or overturns the draft above; where an answer
overturns a choice, the section named is the one to re-read.

- **Q1 — Ed25519, confirmed.** Public verifiability is the point of a public board, and an arena holding no forgery secret is worth ~100 vendored stdlib lines. Keep "stdlib only" by vendoring, not by weakening to HMAC.
- **Q2 — confirmed, and this reading is the one to keep.** Discard the stored float; compare `Fraction(sum(wins), sum(trials))`. `round(x,4)` is not a fix, it is a smaller version of the bug: two entries at exactly 10/18 stay `0.5555` and `0.5556`.
- **Q3 — DRAW, confirmed.** A tie-break is a second axis wearing a comparator's clothes.
- **Q4 — redact-then-sign, confirmed.** A signature over bytes a stranger cannot see is unverifiable — and 75 of 91 bundles carried a filesystem path.
- **Q5 — confirmed.** Silence is not a forfeit; refusal is recorded. One clock: `BELTS.md §4`'s 180 days.
- **Q6 — no default deadline.** A pre-filled default is a decision nobody made, wearing a default's clothes. `deadline_utc` stays required.
- **Q7 — show the fraction, decimal secondary.** `10/18` IS the measurement; `.4f` is a rendering of it.
- **Q8 — label the metric per column.** v1 is model-level, v2 can be item-level. Never merge; a side-by-side without the label implies a comparison the reader cannot make.
- **Q9 — both failed criteria stay.** A UI showing the v2 field without them is the misleading table §5b warns about. Criterion 1 FAILED at 57.6%; belt rule 2's later 24.2% is **not** a pass.
- **Q10 — a board, not a service.** A document travels any channel; a hosted index is a service and a new attack surface v1 does not need.

**Two notes these answers carry, neither of them among the ten.** The gates are now executable —
`check_frontend_clauses.py`, a negative control per clause, `--selftest` 5/5 caught. And §7.2's claim
that the `EMPTY` filename marker covers **16 of 16** is measured false: it disagrees with
`results == []` on **25 of 310** bundles. That erratum is flagged in the signer's record and is **not**
fixed in this text, because fixing it would move a passage under Mike's signature. It is named here so
no reader inherits the wrong number.

---

*Chair drafts. Mike and Ocho review. Ocho gates §8's four clauses — the aesthetic, layout and
interaction decisions belong to Chair and are not his to gate.*
