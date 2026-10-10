# WHAT I WOULD HAVE GOT WRONG IF I HAD TRUSTED THE PROSE

**Cabinet:** DIG DUG (`digdug/`) · **Required section 4F** · **Written 2026-10-10**
**Method:** build the cabinet from the paragraph → freeze it → run the field → **build a second
implementation of the same paragraph that chose the opposite reading on every open clause** → run
both on identical answer streams → attribute every divergence to the clause that caused it.

Nothing here is an opinion about what the prose *might* mean. Every line below is a number that
came out of `prose_check.py`, or a defect that a control or a run caught in my own build.

```
python3 prose_check.py            -> PROSE CHECK PASSED, exit 0
  cross-check : the second implementation, configured with MY decisions,
                reproduces my counters on 44/44 (entrant, level) pairs
  dividend    : under the LITERAL reading, 23 of those 44 pairs differ
  attribution : one clause flipped at a time -> 8 settled by the field,
                4 settled only by a synthetic probe, 2 no run can settle
```

The cross-check matters more than the dividend. If a second implementation disagrees with the first
*under identical decisions*, the disagreement is coding drift and proves nothing about the prose. It
agrees on all 44. So every divergence below is the clause's, not the coder's.

---

## F1 — THE PARAGRAPH DOES NOT DESCRIBE A DESTRUCTIVE SEARCH AT ALL

**This is the one that would have sunk the cabinet, and it is a fact about the prose, not about me.**

The brief for this tier says the faculty is *search with destructive steps — the tunnel you dug is
ground you cannot re-use*. The paragraph says:

> The player moves … into soil **or into an already-dug tunnel**. Moving into soil digs it. …
> Digging is permanent — dug ground never returns to soil.

Read those two sentences together and the tunnel is **the most reusable ground on the board**: it is
enterable forever, it costs one move to enter, exactly what soil costs, and digging never blocks
anything. **The traversable graph only grows.** A route cannot be consumed, because nothing is ever
removed from it.

Measured, not argued. `min_moves_to_complete` is a distance over the non-rock cells, and the set of
non-rock cells does not depend on what has been dug — so the distance cannot depend on the dug set:

```
01_first_blood.txt             route-proof HOLDS (990 evals)
02_the_long_way_round.txt      route-proof HOLDS (1320 evals)
03_the_open_door.txt           route-proof HOLDS (1452 evals)
04_no_safe_line.txt            route-proof HOLDS (594 evals)
```

4,356 distance evaluations, every player cell on every level against the empty dug set, the full
dug set, and 64 random subsets. The distance never moves. **Digging never lengthens a route.**

So the only thing digging destroys in this game is **the soil's job as a barrier**: a dug cell
conducts the hazard forever. That is a real, permanent, monotone destruction — and it is the *only*
one. Two consequences I would have got wrong by trusting the prose:

1. **"The tunnel you dug is ground you cannot re-use" is false under this paragraph.** What you
   cannot re-use is the soil's function as a wall. An implementer who believed the brief's gloss
   would have built a game where digging *removes* a cell, contradicting "moves into … an
   already-dug tunnel", and would have reported a faculty the paragraph never described.
2. **The two facets this tier demands cannot be two independent mechanics.** If the only destroyed
   thing is the barrier, then a death (facet 2) *requires* the components to have merged (facet 1).
   Facet 2 is a **strict subset** of facet 1. This is not a limitation of my measurement, it is a
   property of the game the paragraph describes, and it is checked on every death in the field:

```
test_digdug.py: "facet 2 fired, so facet 1 must have (the nesting claim)"  -- passes on all 11 deaths
```

To make them independent you must add a mechanic the paragraph does not contain — falling rocks,
collapsing tunnels, a dig budget. **I did not invent one.** I measured the consequence instead, and
split facet 1 into a barrier half (1a) and a budget half (1b), because 1b needs no hazard at all
and so survives the collapse of the independence claim.

**Who settled it:** the running, on every level, plus a structural proof.

---

## F2 — THE FOURTEEN CLAUSES, AND WHO ARBITRATED EACH

Every row is one flip of one clause, on the answer streams the frozen cabinet actually produced.

| clause | my reading | the literal reading | how it was arbitrated |
|---|---|---|---|
| **U1** hazard clock | one cell per player turn | its own clock, every second turn | **SETTLED BY THE FIELD** — 2 pairs: `liar`/03 and `wanderer`/01 go from KILLED to UNSOLVED |
| **U2** what exists at t=0 | the player's and every hazard's cell is a tunnel | "a grid of soil": the hazard stands in soil, has no tunnel, **can never move** | **SETTLED BY THE FIELD** — the short route on level 02 stops being a death |
| **U4** adjacency | only the same cell kills | adjacent kills | **SETTLED BY THE FIELD** — 2 pairs, and the **SCORE** moves: `ring-runner` goes from solved 1/3 to 0/3 |
| **A1** hazards dig | never | they dig, so the barrier does not exist | **SETTLED BY THE FIELD** — 11 pairs, score moves for `ring-runner` |
| **A8** a blocked move | costs the turn and ticks the clock | free | **SETTLED BY THE FIELD** — `liar`/03 goes from KILLED to UNSOLVED |
| **A11** abstention list | 31 frozen tokens | 2 tokens (`RESIGN`, `GIVEUP`) | **SETTLED BY THE FIELD** — the reference solver's correct abstention on level 04 becomes a malformed answer |
| **A13** answer shape | one token per turn, never truncated | the first line, and the first letter in it | **SETTLED BY THE FIELD** — 8 pairs, and the **SCORE** moves: `garbage` SOLVES level 01 |
| **A17** counters | from the state change | from the word | **SETTLED BY THE FIELD** — 11 pairs; `dug` differs by one on every level with buried treasure |
| **U5** may the player stop | no pass action | `WAIT` is a turn | **settled by a synthetic probe only** — the field never emitted a WAIT |
| **U7** the collecting turn | the objective is awarded **before** the clock | the turn resolves in full first | **settled by a synthetic probe only** — probe board `#P%TH #`: frozen SOLVED, literal KILLED on the winning move |
| **U9** the boundary | bounded, no wrap | the grid wraps | **settled by a synthetic probe only** — the field's levels are all enclosed, so out-of-bounds is unreachable |
| **A6** an unresolved letter | `step()` raises | `step()` is total: a block and a counter | **settled by a direct call**, not by any entrant — no reader can produce one, so this clause is about a caller that bypasses the reader |
| **U3** a collected target | removed | persists | **NO RUN CAN SETTLE IT** — the two readings differ only in what the board *draws*; `targets_left` shrinks either way |
| **U8** several hazards | simultaneous, one snapshot | sequential in index order | **NO RUN CAN SETTLE IT** — moot under `[A10]`: hazards do not block each other and the policy reads only the tunnel graph and the player's cell, so index order cannot change a move |

```
SETTLED BY THE FIELD      :  8
SETTLED BY A PROBE ONLY   :  4   (U5, U7, U9, A6)
NOT SETTLEABLE BY ANY RUN :  2   (U3, U8)
STILL OPEN, NO CARRIER    :  0
```

The last line is the honest one. **Two of my twenty-six decisions cannot be wrong in any way a
measurement could ever detect**, and one of them (U8) is moot only because of a *third* decision
(A10). A contract that recorded U8 as a live decision would be recording a decision that does not
exist.

### The three that change the SCORE, not just the trace

Most divergences move a counter. Three move the number that goes on the board, which is what makes
them dangerous — two cabinets would publish different rankings from identical answers:

```
U4_adjacent_kills    ring-runner   solved 1/3 -> 0/3
A1_hazards_dig       ring-runner   solved 1/3 -> 0/3
A13_first_line       garbage       solved 0/3 -> 1/3   (level 01 SOLVED by an entrant emitting junk)
```

The last one is worth dwelling on. Under the permissive reader, `"move right please"` is read as
`R` — the first letter in the line — and a garbage entrant **solves a level**. My reader scores the
same bytes as `not_an_action` and the run exits 2, `ERROR: ZERO MEASURED`. Neither file would tell a
reader which convention it used, unless the convention is in the file. It is:
`grammar.give_up_tokens`, `grammar.truncation`, `grammar.answer_shape` are in every bundle.

---

## F3 — WHAT THE RUNNING CAUGHT IN MY OWN BUILD

Three defects in the frozen cabinet, all found by *executing* something, none by reading it. Each
one would have produced a confident, clean, wrong number.

### 1. A counter that disagreed with the board inside the same record — `[A17]`

The first build counted the **word**. A move that killed the player reported `killed`, so the cell
it dug on the way in never reached `dug`, and the wall it bumped on the way never reached `blocked`
— while the board printed in the same record showed both. Off by one on every fatal move:

```
hazard-blind  02_the_long_way_round.txt   dug: mine 1   second implementation 2
liar          03_the_open_door.txt        blocked: mine 0   second implementation 1
```

**Found by the second implementation, on 11 of 44 pairs.** Not by reading my own code: the counter
looked right, and the self-test passed. Fixed by counting the state change; the clause is now in
the contract, and `dug + moved + blocked` partitions the action answers exactly.

### 2. A runner that never stops asking — a hang, not a wrong number

The cap was on **game turns**, and the game clock only advances on an answer that resolves to an
action. An entrant that emits nothing but malformed answers therefore never reaches the cap: the
runner asks it forever. `garbage` and `soft-resigner` both hung the field.

**Found by running the field** (900 s timeout, no output). Fixed: the cap is on **answers emitted**
`[A14]`, which makes an unreadable answer cost what a move would have cost. The clause now says in
the code why it is there.

### 3. My own contract contained a rule the contract makes impossible

The first draft of `CONTRACT_DIGDUG.md` said: *"a swap-through — both ending in each other's cell —
is a death, not a pass."* Under the frozen order the hazard always targets the player's
**post-move** cell, so if it steps into the player's old cell the player has already left it. **The
clause describes a state the game cannot reach.** A control that tried to construct one found
nothing to construct; the clause is now rewritten to say what is true — a player that moves *into*
a hazard's cell dies even though that hazard never moves — and to record that the impossible
version was in the draft.

A contract is a specification. An unreachable rule in it is a bug that no test will ever find,
because the test cannot build the input.

---

## F4 — WHAT A COMPETENT IMPLEMENTER WOULD HAVE BUILT, AND WHY IT IS INCOMPATIBLE

Suppose two competent implementers, both careful, both reading only the paragraph. Here is the
cabinet each builds, and where the two records stop being comparable.

| | implementer A (literal) | implementer B (this cabinet) | the record that differs |
|---|---|---|---|
| the hazard | stands in soil, never moves, decoration | a tunnel-dwelling chaser | every death, on every level |
| adjacency | lethal | irrelevant | `ring-runner` 1/3 vs 0/3 |
| the collecting turn | the turn finishes, then you win | you win before the clock | SOLVED vs KILLED on the same move |
| stopping | `WAIT` is a turn | no pass; abstention ends the attempt | `turns_used`, and whether stalling is legal |
| the boundary | a torus | bounded, out of bounds is a wall | SOLVED vs UNSOLVED on the probe board |
| the answer | the first line, first letter | one token, never truncated | `garbage` 0/3 vs 1/3 |
| abstention | `RESIGN`, `GIVEUP` | 31 tokens, exact | the reference solver's correct answer on level 04 |
| a dug cell that held treasure | a collection | a dig **and** a collection | `dug` on every buried-treasure level |

**Every row is a defensible reading of the same 91 words.** None of them is a bug. Two cabinets
built this way would both pass their own self-tests, both report all-green, and both publish
different scores for the same model — and nothing in either file would say why, unless the reading
is written into the file. That is what the decision register and `freeze.py` are for.

---

## F5 — WHAT THE RUNNING COULD NOT SETTLE, AND WHAT WOULD SETTLE IT

Being explicit, because a gap stated is a result and a gap hidden is a defect:

1. **U3 (does a collected target persist) is unfalsifiable by score.** It changes only the render.
   Settling it needs a decision, not an experiment.
2. **U8 (hazard order) is moot under A10.** It becomes observable the moment hazards block each
   other — a different contract, and a decision I did not take.
3. **Level 01 and level 03 do not punish a hazard-blind planner.** Measured: `hazard-blind` and
   `static-planner` both solve 01 and 03 and die only on 02. Under equal speeds and pre-hazard
   collection a hazard can only kill a player that *approaches* it, so only a level whose short
   route approaches the pocket discriminates. Level 02 is that level; 03 carries facet 1a instead.
   **A fourth scored level is needed and I did not add one** — adding a level to a frozen set means
   re-proving the set, and I would rather report the gap than widen the set on my own authority at
   the end of a run.
4. **No model played.** There is no GPU, no `llama-server` and no `.gguf` on this host. The field
   is twelve code entrants plus the `model` entrant exercised through its admission path. Every
   number in the report is an instrument number, not a model number.

---

## THE ONE-SENTENCE VERSION

The paragraph describes a game in which digging never destroys a route, so the faculty this tier
was built to measure does not exist in it; the only irreversible loss is the soil barrier, which
makes the two demanded facets nested rather than independent; and of the twenty-six decisions I had
to make to turn 91 words into a runnable contract, **eight were arbitrated by the field, four only
by a synthetic probe, two by nothing a run could ever do, and three of my own defects were caught
by executing the thing rather than reading it.**
