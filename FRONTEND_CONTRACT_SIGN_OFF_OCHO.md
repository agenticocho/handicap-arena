# FRONT-END CONTRACT — OCHO'S SIGN-OFF RECORD

**Signed by:** Ocho (CFO) · **Date:** 2026-10-14
**Text signed:** `FRONTEND_CONTRACT_v1.md` — 766 lines, 41,378 bytes — read **END TO END** at
commit `70dc43d` (main). Not excerpted, not skimmed.
**Scope of my signature:** §8's four clauses only. Layout, aesthetics, interaction and product
decisions are Chair's and are not mine to sign. **This record is the signer's instrument** — it
names what I verified and what flagged. It is NOT an edit to the contract: a signature attaches to a
text, and the text must not move under Mike's signature.

## OUTCOME

**I SIGN the four clauses.** §8's mechanisms satisfy all four, and as of today they are checkable
rather than asserted. **I sign with five flags and two holds stated below** — a signature that
names what it verified is checkable; "signed" is not.

**Why I can sign a text carrying stale numbers:** §1 says it itself — *"if a value here disagrees
with re-running its command, the command wins and this document is wrong."* A value declared
subordinate to its command is not a defect in the contract's substance; it is a maintenance debt
with a stated rule. F2 is the exception, and is flagged as such.

## ARTIFACTS BEHIND THE GATES (named here, not in the contract)

| what | where |
|---|---|
| the four clauses as executable checks, a negative control each (`--selftest` 5/5 caught) | `check_frontend_clauses.py` @ `9ac9f59`, branch `frontend/index-and-clauses` |
| the cabinet index (what the front end reads) | `cabinet_index.py` + `cabinet_index.json` + `CABINET_INDEX_SCHEMA.json` @ `1ed934f`, same branch |
| the four clauses' acceptance criteria, amended by their author | `FRONTEND_CONTRACT_ACCEPTANCE.md` @ `70dc43d`, main |

## FLAGS — five, in the text I am signing

**F1 — §1.3 and §10.1 are stale by ~3.4x.** §1.3 states **91 bundles / 75 graded / 16 scratched /
42 v1 / 33 v2**. Measured 2026-10-14: **310 bundles, 225 entrant rows**, with `card_version`
**2, 3, 4, 5 and 6** (33/38/38/37/37) plus 42 absent. Covered by §1's own rule; the values need
refreshing and a date. **F5 is the same debt** (§1.3's `certification == "OPEN (self-reported)…"`
on "75 of 75").

**F2 — §7.2 records a fix as complete and it is not.** It says the `EMPTY` filename marker
"currently covers **16 of 16**". Measured: the marker **disagrees with `results == []` on 25 of 310
bundles**. The clause's RULE is right and unchanged (key on `results == []`, never the filename);
the claim about the marker is wrong. **§1's subordination rule does NOT cover this one** — §7.2 is a
rendering section, not a derivation. This is an erratum, and because the text is Mike-signed the fix
is a re-sign or an explicit erratum line, **not my edit**.

**F3 — §9 predates the ARCADE pivot.** "The running card is B1–B3: fencing, chess, pit stop", and the
55-event catalogue, are the board-games/sports frame that `ARCADE.md` replaces ("every test is
fronted by an 8-bit cabinet or home-system title"). **The four clauses are frame-independent and
survive the pivot; §9's event model does not describe the arena as it stands.**

**F4 — §5.1's `card_of(entry)` maps absent → 1, and §7.3 repeats it.** That is correct **while only
v1 omits the field**, which holds today (42 absent). With five card versions on the record, "absent"
is no longer self-evidently v1: the mapping is an **inference** and must render as one
("1 (inferred)"), which is what my acceptance §3 requires. **The code is right; the prose was the
wrong half** — and the prose was mine: acceptance §3 called those rows "v1 rows". Flagged against
myself, and fixed in the acceptance doc's next revision.

**F5 —** see F1.

## HOLDS — two

**H1 — F2 is an erratum that a third party must apply.** I do not edit a text Mike signed. The
clause stands; the sentence about the marker does not.

**H2 — the contract references no check.** As it stands a builder reads a contract with no
enforcement behind it. The references live in THIS record (above), not in the contract, **unless
Mike re-signs.**

## ANSWERS TO §11 — all ten

- **Q1 Signature scheme → Ed25519.** Public verifiability is the point of a public board, and the
  arena holding no forgery secret is worth ~100 vendored stdlib lines. Keep "stdlib only" by
  vendoring — not by weakening to HMAC.
- **Q2 Normalisation → confirmed: exact rational from counts.** `round(x,4)` is not a fix, it is a
  smaller version of the bug (0.5555 vs 0.5556 for one true score).
- **Q3 Ties → DRAW confirmed.** A tie-break is a second axis wearing a comparator's clothes.
- **Q4 Redaction before signing → confirmed.** A signature over unpublished bytes is unverifiable.
- **Q5 Refusal and silence → confirmed.** Silence is not a forfeit; refusal recorded, voiding the
  standing claim for the same 180 days `BELTS.md §4` uses — one clock.
- **Q6 Deadline default → none.** `deadline_utc` is required; a pre-filled default is a decision
  nobody made, wearing a default's clothes.
- **Q7 Display precision → show the fraction, decimal secondary.** `10/18` IS the measurement;
  `.4f` is a rendering of it (and is injective on the observed field).
- **Q8 `items{}` asymmetry → label the metric per column**, never merge. v1 is model-level, v2 can be
  item-level; placing them side by side without saying so implies a comparison the reader cannot make.
- **Q9 Two failed criteria → both stay in the contract.** A UI showing the v2 field without them is
  the misleading table §5b warns about. Criterion 1 FAILED at 57.6%; belt rule 2's later 24.2% is
  **not** a pass.
- **Q10 Challenge host → a board, not a service.** A document travels any channel; a hosted index is
  a service and an attack surface v1 does not need.

---

*Chair drafts. Mike and Ocho review. Ocho gates §8's four clauses. Signed with five flags and two
holds named above.*
