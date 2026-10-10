# RULINGS REQUESTED — from the three cabinets (Q*BERT, TETRIS, DIG DUG)

**For Ocho. Three items, each measured, each with the artifact that produced it. Two are rulings; one is a
defect in the trunk.**

Source: three independent sessions, each built from a dossier alone, none of them reading the others or the
Sokoban implementation. Combined: **1,393 + 40 + 649 controls**, every bundle replayed from its raw answers,
and **no model ran in any of them** (no weights, no endpoint, no verified GPU where they ran) — **so none of
these numbers is a model-performance result, and not one of the three claimed otherwise.**

---

## 1. RULING — THE GATE CAN CHANGE AFTER GAMEPLAY IS COMPLETE

**TETRIS, measured.** Two entrants produced **identical gameplay** — 3 of 4 solved, in seven moves each.
**Their gate rates differ:**

```
reference       3 /  8  =  0.375
post-terminal   3 / 12  =  0.250
```

**Because the gate is `solved / attempted_emitted`, output after the game is over still divides the score.**
An entrant that keeps talking after solving is **penalised for talking**, not for playing worse — and R2
chose `attempted_emitted` specifically so that *a shorter run cannot flatter itself.* **In this direction it
can flatter itself by saying less.**

**This is a defect in the ruling I wrote, not in the cabinet.** The rate was chosen against the failure mode
where a chatty entrant hides a low score behind a long transcript; **it did not account for the same lever
working the other way.**

**Options:** (a) the gate is `solved / items_attempted` — items, not tokens, which is what the phrase
"solved / attempted_emitted" was reaching for; (b) keep emitted but freeze the transcript at the terminal
event before scoring; (c) both rates recorded, one gated.

**Chair's read, offered not applied:** the gate should be **`solved / items_attempted`**, and emitted and
consumed stay in the record as **diagnostics**. *A gate must be a function of the game, and this one is
currently a function of the transcript.*

## 2. RULING — THE FLOOR OF THE SCALE IS A CLAUSE

**DIG DUG, measured, all five items proved exhaustively before the field ran.** The specification handed to
that cabinet was **deliberately under-specified** — a paragraph, not a spec — and it had to choose and record
its own readings. **What the choices do:**

```
under a REJECTED reading of "whose turn resolves first"
     level 01 -- one pearl, one letter -- becomes PROVEN UNWINNABLE (opt None; its own solution
     ends KILLED_BY_HAZARD)
under hazard_terrain = soil_too
     levels 03 and 05 become PROVEN LOSSES
under resolve_order = simultaneous
     level 02's optimum changes from 7 to 5
```

**So two implementers can build compatible-looking simulators, run the same entrants, and publish numbers
that are not comparable — without either of them being wrong.** The difference is a clause neither the prose
nor the record settles.

**Ruled (proposed):** every under-specified clause is **recorded with the reading chosen and the alternative
rejected**, the reading travels **inside the bundle**, and **a field is only comparable to another field that
declares the same readings.** *A defaulted setting is still a setting — the same rule we already have for the
launch config and the reasoning setting.*

**And the general form, which is the tier's real result:** *the floor of the scale is not the weakest model
in the population; it is a clause.* **A cabinet whose contract is one clause away from a provably unwinnable
level is measuring the clause as much as the entrant.**

## 3. DEFECT, NOT A RULING — THE TRUNK'S OWN GRAMMAR CONTRADICTS R1 AND R2

**Q*BERT found this from outside, in the frozen artifact the other cabinets were told to read as the
reference shape:**

```
SOKOBAN_READ_GRAMMAR.md   calls moves "THE SCORE"          -- contrary to R2 (solved is the score,
                                                              moves is a cost)
                          leaves the abstention tokens
                          UNSPECIFIED                        -- contrary to R1 (the list is frozen
                                                              explicitly, and equals the code's)
```

**R1 and R2 were ruled after that grammar was written, and the grammar was never amended.** Every cabinet
brief now cites the rulings as binding — **and the trunk still carries the artifact that contradicts them.**

**Fix, not decide.** The grammar should take an amendment that points at the rulings, **and the abstention
list should be stated in it verbatim from the code** — a grammar that names one token while the code scores
eight is two conforming artifacts that disagree, which is R1's own justification.

---

## AND ONE THING THAT IS NEITHER, WHICH I WOULD KEEP

**DIG DUG left nine of its own defects visible in the files** rather than cleaning them: a chase measured from
the wrong end; a copied boundary rule that OOM'd any wrap reading; a shadow reading leaking into the blocked
counter; **a freeze gate that iterated a key nothing ever wrote and so passed vacuously**; a search wired to
a field that does not exist; facet aggregates silently summing a subset; and two counters that are
structurally equal under its runner — **reported as a limit of the runner, with the divergence proven in
`--self-test` instead.**

**A gate that passed vacuously is the exact defect we have spent two days on, found in its own code by the
thing that wrote it.** That is what the standing rules were for, and it is the first time a cabinet has
produced that finding about itself.
