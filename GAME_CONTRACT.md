# GAME CONTRACT — when a game is a measurement and when it is a costume

**Date:** 2026-10-07 · **Author:** Ocho (CFO), design owner · **Status:** normative, with an
enforcing test

## The directive

> *"They all must have a visual game... board games to combat sports to summer/winter olympics to UFC
> to any extreme sport. That's the spirit of The Arena."* — Mike

The game is **not decorative**. It is the product. Which means the game has to be **the measurement**,
not a picture drawn over one.

## The standard

**Can a stranger reconstruct the game from the recorded bundle?**

- **Yes** → the game *is* the measurement, and the visual is honest.
- **No** → **the visual is a skin over someone else's result.**

That second case is not a cosmetic defect. It is **the same failure as a count carried as a literal**:
a claim with no carrier, displayed as though it had one. A front end rendering a chessboard over a
tool-selection score is asserting something the record does not contain.

**Strengthened into something checkable:** the recorded state must be a **sufficient statistic for
the score** — *the scored outcome can be recomputed from the recorded state alone.* Not "the state
is related to the outcome"; the state **reproduces** it. A move list reproduces a chess result. A
latency column does not reproduce a boxing result.

## The two event classes

This split is **forced by the standard above**: an INSTRUMENT event given a `game` name would fail
the reconstruction test, so the class must exist.

| class | game? | bundle carries | may be watched? | ranked? |
|---|---|---|---|---|
| **CONTEST** | **must** declare one | **the game's state** | yes — the audience watches the game | yes, with belt and division |
| **INSTRUMENT** | **must NOT** declare one | **what it is staged as** | **yes, and often by more people** | **never** |

### The correction that shaped this — being an instrument is not being boring

**An earlier version of this document said INSTRUMENT events are "deliberately unwatchable". That was
wrong, and Mike caught it with a counterexample that costs nothing to understand:**

> **A weigh-in for a UFC title fight is an instrument.** It validates the measurement, settles
> nothing about the result — and it is one of the most-watched things on the card.

**Two independent axes were bundled into one.** *What an event does* (validate a measurement) and
*what the audience gets* (a show) are unrelated. **Not being staged makes something boring; being an
instrument does not.**

**And the precise form of the defect, because it changes the rule:**

> ## The defect is not *instrument as spectacle*. It is *instrument as a FAKE CONTEST*.

**A weigh-in is honest — it shows a weighing. It never pretends to be a fight.** That is the line.
So an INSTRUMENT event **may be** the most compelling thing on the card; it simply **may not wear a
game's clothes.** Dressing one as a game is still the referee in a costume — *the costume is the
offence, not the audience.*

### The recipe is already in the catalogue: five ingredients of a real weigh-in

1. **a number everyone understands**
2. **a hard threshold with a consequence**
3. **a scheduled, public moment**
4. **a legible way to fail — the miss IS the drama**
5. **side-by-side comparison**

**The Arena's weigh-in already has all five.** `gpu_free_gb_at_weigh_in`. Divisions assigned by
**measured** footprint. A real threshold — exceed your VRAM and the model does not run. Side-by-side,
because every entrant is weighed the same way.

**And the miss is already documented**, which is the part worth sitting with:

> **A 2B model swung 0.00 → 0.33 → 0.67 → 0.33 → 0.67 with its weights never changing once.** Every
> movement came from a config flag.

**That is a fighter missing weight because someone left a grammar file switched on.** It is
FINDING 001, and this document has been filing it as an instrument result when it is **the best
spectacle the project has produced.**

### And the audience argument, which reverses the priority

> **The fight answers "which model is better." The weigh-in answers "can this thing run on my desk
> at all" — and that is the question everyone with a GPU actually has.**

It is the project's own thesis, televised: **VRAM is the absolute bottleneck for the
democratisation of AI.** So **the instrument league must not be written off as the boring half.** On
the audience evidence it may be the half that speaks to the most people, and **League I may be a
better lead product than League B.**

**INSTRUMENT events are still never ranked** — a weigh-in does not decide the fight. That exclusion
is a **hard partition in the render path**, the same way `card_version` is. A front end that merely
*labels* the difference will eventually rank a scale-calibration against a boxing match.


## The rule

**An event may declare a `game` only if it also declares the bundle fields that carry that game's
state. `game` set + empty `game_state_in_bundle` = FAIL.**

**And the name is a LABEL on the state, not a parallel declaration.** The state schema is the primary
artifact; `game` is derived from it. This is the day's own rule — *derive, don't carry* — because a
name kept alongside a schema drifts from it exactly the way a hand-maintained count drifts from what
it counts.

### The presentation boundary, made explicit because it WILL be tested

**An INSTRUMENT may be FRAMED by the Arcade; it may not be NAMED as a game.** Two cases, one field apart:

```
{"class": "INSTRUMENT", "staged_as": "arcade cabinet -- PUNCH-OUT: which weigh-in gets up"}
    -> PASSES. The framing is presentation, and presentation lives in `staged_as`.

{"class": "INSTRUMENT", "staged_as": "arcade cabinet -- PUNCH-OUT: ...", "metaphor": "PUNCH-OUT"}
    -> FAILS. THE NAME IS THE OFFENCE, not the presentation.
```

**Why this is written down rather than left to the rule.** The Arcade fronts every event, so an instrument
**will** be shown as a cabinet. Without this passage, a presentation decision reads as a contract violation
and the next reader *"fixes" the test* — which is the failure mode a rule about presentation invites.

**Both cases are executed in `test_game_states.py`** — the framing case as a **negative control** (it must
pass) and the same framing with the name as its **positive counterpart** (it must fire). So the boundary
**fails loudly** if anyone moves it, rather than being a sentence nobody re-reads. That is the caption rule
applied to the contract: a distinction stated once, in prose, is a distinction that drifts.

**Scope, stated so the rule does not overreach:** the catalogue may name a game **as a
specification** — that is a target, not a claim. **The check binds BUNDLES.** A bundle that claims a
game and carries no state is a lie in the record; a catalogue entry that names one is a plan.

## The sport category determines the math, so pick the game from the math

| class | examples | math | status |
|---|---|---|---|
| **OLYMPIC** — absolute | 100m, long jump, weightlifting | every entrant measured independently against a **frozen instrument** | **the Arena's native shape.** The card already is this |
| **COMBAT** — head-to-head | boxing, MMA, UFC | contested, but **pairing-dependent**: the score depends on who you drew | **a different event class. Needs Elo or round-robin.** Expensive to measure honestly |
| **TEAM / RELAY** | H league | the unit is the team; the footprint is the **sum** of members | already stated in the catalogue, and correct |

**COMBAT is a trap and must be treated as one.** A score that depends on who you played is
**FINDING 002's twin** — *two entrants measured against different machines*, one level up. **No
COMBAT event ships without a stated n and a confidence interval.** Model-versus-model play is
brilliant to watch and expensive to measure honestly; free play comes later, as its own event, with
its own acceptance criteria.

## What the Arena already gets right

Worth noticing, because it is a stronger foundation than it looks: **the Arena already speaks combat
sport.** Weight classes (Featherweight → Heavyweight) and belts (white → red) are martial-arts
vocabulary, and **divisions are assigned by measured footprint** — a real measurement, not a label.
The metaphor system is half-built and internally consistent. It needs the games to be **real rather
than named**, which is the whole of this document.

## Enforced by

`test_game_states.py` — reads every card task file and every bundle, and fails on a game name with no
state behind it. **Positive control included**: the test is verified to fire on a reintroduced
`metaphor`-without-state, so it cannot become a check that passes by being unable to fail.
**It exits 1 while violations stand** — verified, not assumed, because an enforcing check that exits
0 while reporting violations is a check that cannot fail.

## STATUS: ENFORCEABLE, AND BINDING AT ADMISSION — with the residual gap named

**What is true today, all of it verified by mutation rather than asserted:**

```
the 5 task files declare class=INSTRUMENT + staged_as   · the game name is gone
the 301 historical rounds carry SUPERSESSION records    · annotated, NOT excused, still counted
the check counts NEW and HISTORICAL separately          · NEW: 0 / HISTORICAL: 301
the check exits 1 on a NEW violation                    · proven by planting one
the rule (bundle filename -> record filename) exists once and is asserted  · proven by mutation
THE ARENA CONSUMES THE EXIT CODE AT ADMISSION           · run_card.py:268, before any model is spawned
```

**THIS SECTION PREVIOUSLY SAID *"no arena workflow consumes that exit code."* THAT IS FALSE**, and the
evidence is the v5 run's own journal at admission, the moment before any model was spawned:

```
game contract: OK (  NO NEW violation. The 301 historical rounds stand AS RECORDED -- superseded, not)
```

**`run_card.py:268` calls `game_contract_gate()` before the entrant loop; a non-zero exit REFUSES and no
model is spawned — proven in both directions by `test_bind_control.py`, which reads the DECISION rather
than running the permitted work. So the arena stopped on it last night.** *A stale status line is the
stand-in-outliving-its-thing defect, and this is that defect sitting on the document whose subject is
exactly that.*

**AND THE RECORD OF THE FLIP, because it happened and the file should say so:** the gate was a policy
decision and deliberately not an agent's — *an agent may not certify the gate that admits its own work* —
and the operator made it. The historical 301 do not block, because they are superseded and annotated;
`NEW: 0` is the condition that is computed and enforced at exit.

### THE RESIDUAL GAP, NAMED RATHER THAN LEFT AS A BLANKET "NOT YET BINDING"

- **BINDING at ADMISSION.** ✓ `run_card.py` refuses before spawning anything.
- **NOT bound to a COMMIT.** **There is no git hook** — `.git/hooks/` holds only the shipped samples and
  there is no global hooks directory. A violation can be committed.
- **NOT bound to a SUITE RUN.** The check runs when `run_card.py` runs, not when the suite does.

**So the contract blocks the thing it was built to block — an unmeasured run — and does not block the thing
it was never asked to block — a commit.** Named here so a reader learns *which*, instead of being told "not
binding" about a gate that refused a run twelve hours ago. **If a commit-time hook is wanted, it is a
separate decision and a separate line, and it is not implied by this one.**

**A LOOSE END, FLAGGED AND DELIBERATELY NOT CHANGED.** The task ids still name games — `R1_fencing`,
`R2_chess`, `R3_pitstop`. The check inspects the `metaphor`/`game` **fields**, so the ids are legal, and
by the same argument that made the caption and the filename defects a slot name that names a game is a
label whose referent has moved. **Renaming them touches the 301 round keys**, which is a migration rather
than an edit — **so it is recorded here as a known label debt and deferred, not slipped in.**

## THE SLOT NAMESPACE — DECLARED, NOT MIGRATED (operator-authorised 2026-10-08)

**The round keys keep their names. The names are SLOTS, and this table is what makes them opaque IDs rather
than residual claims.**

| slot | what it MEASURES | historical name | status |
|---|---|---|---|
| `R1_fencing` | structured-output conformance — schema strictness, scalar types, sequences | `FENCING` | **costume, kept for key stability** |
| `R2_chess`   | tool selection — the right call, and the reflex to abstain | `CHESS` | **costume, kept for key stability** |
| `R3_pitstop` | code repair — a fix that breaks the other cases scores zero | `PIT STOP` | **costume, kept for key stability** |
| `R1_conformance` | structured-output conformance — the representation of absence, six items (v6) | — | **NEUTRAL KEY. The label debt retires FORWARD here: new rounds do not name a game.** |

### THE DECLARED NAMESPACE, MACHINE-READABLE

**The table above is the PROSE. What follows is the SINGLE SOURCE `test_game_states.py` parses, and the
reason is a filed defect: the namespace used to be declared in two places, and THE COPY THE ERROR MESSAGE
NAMED WAS NOT THE COPY THE CHECK READ** — so a reader who complied with the instruction changed nothing.
*An error message is part of the instrument.*

**IT IS A FLAT LINE FORMAT BETWEEN EXACT MARKERS, NOT A PARSED ENGLISH TABLE.** A regex over a markdown
table is the greedy `{.*}` class this project has already paid for once. Each line is `<key><whitespace>
<description>`; nothing else is read, and nothing is inferred.

```
=== DECLARED_SLOTS BEGIN ===
R1_fencing       structured-output conformance (schema strictness, scalar types, sequences)
R2_chess         tool selection (the right call, and the reflex to abstain)
R3_pitstop       code repair (a fix that breaks the other cases scores zero)
R1_conformance   structured-output conformance -- the representation of absence (v6, neutral key)
=== DECLARED_SLOTS END ===
```

**AND ZERO SLOTS PARSED IS AN ERROR, NOT AN EMPTY DECLARATION.** Zero slots means every round key is
undeclared, so a run is refused for a reason nobody stated — **the empty-list rule pointed at the parser
instead of at the model.** The parser asserts a non-zero count and names the file and markers it read.

**AND EVERY RUN RECORDS THE GATE REVISION THAT ADMITTED IT**, the same discipline as a card carrying its
own commit hash: the gate digest travels in the record, so a run and the gate that admitted it are linked
by more than a timestamp. **v5 taught us that lesson once and it was paid for.**

**AND `R1_conformance` WAS ADDED ONLY AFTER THE CHECK CAUGHT ITS ABSENCE.** The v6 run wrote 13 bundles
under that key and `test_game_states.py` failed 13 NEW violations —

```
round key 'R1_conformance' is NOT in the declared slot table
```

— **which is the namespace behaving as a CHECK rather than a caption, and it is the whole reason the table
exists.** Retiring a label forward is not the same act as declaring the slot that replaces it: **the debt
was retired, the slot was not declared, and the contract refused a run at admission until it was.**
*Declare, do not migrate* has a second half — **the declaration is the fix, and a rename without one is a
violation with good intentions.**

**WHY DECLARE RATHER THAN RENAME**, measured rather than asserted:

- `evaluate_v4.py:35` is `ROUND = "R1_fencing"` and the evaluator **joins on that literal**;
- `R1_fencing` appears **151 times across the 151 bundles** (`R2_chess` 75, `R3_pitstop` 75);
- renaming therefore means **rewriting keys inside recorded bundles** — the overwrite of history refused
  twice already today — and a forward-only rename would **split the join for nothing**, since every
  cross-version comparison needs a mapping regardless. **That mapping is this table.**

**THE JOIN PATH, stated so a reader does not have to invent it.** A round records its slot key; the
**description** lives in the task file, which now carries `class` and `staged_as`:

```
bundle.results[i].rounds["R1_fencing"]   -> slot key      (historical, stable, OPAQUE)
tasks/<card>/01_fencing.json             -> class=INSTRUMENT + staged_as   (the description)
```

**Forward, a round carries `class` and `staged_as` directly**, so new records need no join. **The existing
151 recover theirs by the join above** — which is what declaring the table buys, at zero cost to the record.

**AND IT IS ENFORCED, NOT JUST DECLARED.** `test_game_states.py` fails on any round key present in a bundle
that is missing from this table, with **controls in both directions** — a declared key passes, an undeclared
key FIRES. **Without that check, "declared namespace" is a caption.**

**Attribution note, because I got this wrong while correcting something else.** A teammate reported
that the test "exits 0 while reporting violations". It does not — the exit code is 1, checked. **The
claim was theirs, not mine, and my correction commit `b8063bf` attributed it to my own commit
`3bb163a`.** Nobody's record should carry someone else's error under their name — the same rule as a
verification row whose `issuer` is the verified rather than the verifier. **Two corrections in one
hour, and the second was an attribution slip inside the first.**

**First finding, from running it against today's repo:** the card's three rounds carry `metaphor`
names (`FENCING`, `CHESS`, `PIT STOP`) and **no game state whatsoever**. They must therefore either
**lose the metaphor** or **gain the state**. `R2_chess` is the live case: it is a tool-selection task
named after a game it does not play, and the real chess event (R4, tactics puzzles scored by a
reference engine) is the one that earns the name.

---

## Correction — the scope of the game-name claim, measured

**I claimed in the accompanying message and commit that `metaphor` "occurs exactly ONCE in the whole
project". That was false, and a teammate caught it.**

I had swept **five documentation files** (`GAMES.md`, `EVENTS.md`, `BELTS.md`, `FORMAT.md`,
`WHITEPAPER.md`) — where the answer is 0,0,0,1,0 — and then stated the result as a fact about the
**project**. Measured properly:

    files containing "metaphor" : 122
    total occurrences           : 288
    of which in the 5 doc files : 1   (FORMAT.md, defining it)
    outside those five          : arena.py, README.md, all task files, ~107 result bundles

**The conclusion survives on the evidence that actually supports it**, which is the narrower claim:
**`GAMES.md` contains zero occurrences and its six declared fields carry no game name and no state
field.** The catalogue is clean; the project is not.

**The failure is mine and it is the one I had written a rule against an hour earlier.** The skill's
third corollary says *a search supports only the claim it was scoped to — never let a bounded search
support an unbounded "nowhere."* I wrote that, then generalised a five-file grep to "the whole
project".

**And the rule this document itself states is the reason it happened:** *a principle will not hold
across 55 events; a check will.* I trusted care to hold a count across a 122-file sweep. Care is a
principle. **The count needed a check, and the check — `test_doc_counts.py` — covers documents, not
the project.** Two teammates' numbers also differ (280 vs 288) and **that is not a contradiction**:
both were right for their moment, because a count of a growing record is a **timestamp**, not a fact.

