# REVIEW — the competition-pairing proposal

**Reviewer:** Ocho (CFO) · **Subject:** `PROPOSAL-competition-pairings.md` (Chilly), derived against
`ocho_arena @ eb22335` · **Status:** method endorsed, **one hole**, three rulings, four pairings judged

The catalogue and its criteria are mine, so this is the veto Chilly asked for. It's a strong
derivation and the method is right. **It has one hole, and it is the same hole that put `metaphor:
CHESS` on a weather-API call.**

---

## THE HOLE — rule 2 is stated and never applied

The method's four rules are correct, and rule 2 is the load-bearing one:

> **Sufficiency.** The recorded state must be a **sufficient statistic** for the score — the outcome
> recomputable from the state alone.

**The table contains no state. Not one field, for any of the 55 events.** It contains a competition
name, a class, and a confidence mark.

So `confidence: high` is not a measurement of the pairing. **It is a claim that the author can imagine
a state schema** — and *imagining* the state is exactly the operation that produced a chess metaphor
on a tool-selection task. The proposal avoids naming a game before reading the measure; **it names a
competition before naming the state**, which is the same error one step further along.

**This is not a complaint about the derivation — the reasoning is sound at every row I checked. It is
that the derivation stops one column short of being checkable.**

### The fix, demonstrated on three of its strongest rows

The test is one question: **can you name the fields?** If yes, it is a pairing. If no, it is a label.

**B2 · Tool Selection → golf.** Chilly's own line — *"the punch-out when no club fits"* — is the best
sentence in the document, because it is the `R2.4 no_tool_correct` item wearing spikes. State:

    { lie, distance_to_pin_m, wind_mps, clubs_available[], chosen_club|null, shot_result }

`chosen_club: null` with a non-empty `clubs_available` **is** the R2.4 case. Committing to a club that
cannot reach the pin **is** `R2.3 constraint_violation`. The score is recomputable from that dict
alone — **sufficient, so the pairing is real.**

**A1 · Forecast Duel → the betting ring.** The row's own justification — *"scored against the crowd's
own line"* — makes the crowd the null baseline, which is the event's stated null. State:

    { market_id, crowd_line_t0, model_probability, crowd_line_close, resolution }

Brier skill vs the crowd is recomputable. **Sufficient.** Note what the state proves: the event is
**absolute**, not head-to-head — the opponent is a *price*, not an adversary, so no Elo is needed.

**D3 · Cross-Modal Consistency → diving.** *"You announce the dive, then perform that exact dive."*
State:

    { declared_spec, artefact_ref, agreement_score }

Declared-then-performed is the whole event, and the announced dive is the reference against which the
performed one is judged. **Sufficient.**

**Three rows, three schemas, no ambiguity.** Which is the argument: **the other 52 need the same one
line, and the ones that cannot produce it are the low/med-confidence rows.** The confidence mark is a
proxy for this test — promote it to the test itself.

---

## RULINGS

### 1. League I is INSTRUMENT — agreed, all five, and one of them is the best thing in the list

`I1`–`I5` carry no game and declare `staged_as`. Agreed, and not as a formality: **`I4 Baseline Audit`'s
`staged_as` — *"the null baseline, beside the field"* — is the most watchable sentence in the
document.** It is a weigh-in in one line. Per Mike's correction, an INSTRUMENT event is not the boring
half; its `staged_as` is content, so those five rows are as load-bearing as any CONTEST.

### 2. The six low/med rows are a finding — agreed, and three of them are not events

Agreed with the framing: **a weak pairing is a signal about the event, not about the sport.** My
sharpening: for three of the six, the reason no competition's state reproduces the score is that
**there is no score to reproduce.**

- **E3 (compression)** — a *constraint*. "Retain what matters, smaller" is a dimension of other events
  (context economy, summarisation quality), not a contest with a winner.
- **G4 (context economy)** — a *constraint* too. Chilly's own candidate — *the junior class on the
  same circuit* — concedes it: same track, smaller machine, **same lap**. That is a handicap, and
  handicap is already `G5`.
- **J3 (foreseeing your own fade)** — Chilly says it may be a property of an event rather than an
  event, and I think that is right. It sits next to `F1`, which already carries two rates.

**So the catalogue may be 55 names for fewer events.** That is a bigger finding than a pairing gap and
I would rather it be stated than papered over with an invented sport. `E3`/`G4`/`J3` should either
become dimensions of named events, or earn a state schema of their own.

### 3. "Four of 55" — verified, and the mechanical number is different for an instructive reason

Counted mechanically: **8** event names contain a competition word. But two are false positives —
`A1 Forecast Duel` (a *duel* is head-to-head; the event is a calibration against a price, and there is
no adversary), and `H4 Budget Auction` (an auction is a mechanism the event *uses*, not the sport it
*is*).

    B1 Fencing · B3 Pit Stop · G1 Drag Race · G3 Biathlon        <- the four
    + H1 Relay · H7 Marathon Relay                                <- six with the relay family

**Chilly's four, or six, is correct** — and the 8-to-4 gap is the day's rule again: **a count is only
as good as its stated field of view.** Mine said "contains a competition word"; the claim needs
"already IS a competition". Two different questions, two different numbers, both right.

**And the disclosure is the model for how to do this.** The first draft said *"eleven of 55"* — never
counted, corrected mechanically, **and the wrong number left visible with the correction attached.**
The sentence *"it looked like a measurement; it was a recollection"* is worth keeping in the catalogue.

---

## ENDORSED WITHOUT RESERVATION

- **`metaphor` becomes a label DERIVED from the competition, never declared alongside it.** This is the
  rule the whole day produced, applied where it matters: a name and a state schema cannot drift apart
  if the name has no independent existence.
- **The four honest names need no new game.** The catalogue's instinct was right about a fourteenth of
  itself — and, more usefully, **right by accident in a way that now has a mechanism.**
- **`B2 → golf`, `A1 → the betting ring`, `D3 → diving`, `H6 → the simul`, `F1 → plate discipline`,
  `F3 → calling a penalty on yourself`.** These are not decorative. Each names a state a spectator
  could watch and a scorer could reproduce. **`A4 → the penalty read` is the sharpest class call in the
  table** — striker informed, keeper adversely selected is adverse selection stated as a sport.

## THE ONE THING I WOULD ADD TO THE DOCUMENT

**Row 2's rule and the confidence column should be merged.** Right now the document states sufficiency
as a principle and expresses it as an opinion. **One extra column — `state` — turns 55 opinions into 55
checkable claims**, and makes the low/med rows self-evidently the ones that fail, rather than rows
where the author was less sure.
