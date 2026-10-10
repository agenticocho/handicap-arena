# SECTION_4F.md — the two facets, and what each one was actually measured as

Tier 3 asks for two things that are usually collapsed into one score:

> **F1 — search under destruction.** The player edits the map it is planning on.
> Does the plan consume the ground it needed?
> **F2 — hazard-aware planning.** The same edit is a road for the thing that
> kills you. Does the entrant see that before it digs it?

Both are answered here from **one trace per item** — the record of the plies the
score was computed from — because a second event would be a second measurement
and the cabinet would then be reporting which of the two it liked. `digdug_run.py
facet_rows()` is a *projection* of `item["trace"]`; it re-runs nothing, and there
is no second round, second seed or second solver anywhere in this file's numbers.

The six findings below are ordered by how much they cost to hold.

---

## 4F1 — the player's mobility NEVER shrinks, so "the ground it needed" was never a cell

The obvious F1 metric is a shrinking traversable set: dig, and the map you are
planning on gets smaller. It is not what these rules do. Soil and dug ground are
both enterable, nothing ever reverts (`"ground the player digs becomes permanent
terrain"`), and the dug set is monotone — so `len(reachable_cells())` is
**non-increasing in nothing: it is constant**. Control `[M1]` in
`digdug_solve.py` asserts it over every reachable state of every level to depth
12, and `digdug_run.py instrument-check` `[F]` re-asserts it on the played runs:

```
F1: static-planner never removes a traversable cell -- the player's mobility is
    monotone under these rules ... mobility_shrink_events = 0
```

Measured on the item set, mobility is *identical from ply 0 to the last ply* on
every level (01: 3, 02: 14, 03: 17, 05: 9 cells). The destruction in this game is
not the removal of ground. It is the removal of **time and of margin**, and the
record has to measure that instead, which is what the arithmetic below is.

**What would falsify this:** one level where a dig makes a cell unenterable. The
contract has no such clause; `[D-TARGET]`'s `persists_as_marker` is the closest
and the solver refuses to reason about it at all.

## 4F2 — attribution is 1.000 *by construction*, so it cannot be the finding

"The hazard arrived through a tunnel the player dug" is entangled by the rules:
under `[D-T0]` a hazard's only terrain is dug ground, so every route a hazard
ever used was authored by the entrant, at every ply, on every level. A facet that
reports `deaths_armed_by_own_dig / deaths = 1.000` is therefore reporting the
contract, not the entrant.

The number is still in the record — a reader has to be able to see that the
trivial answer is trivial — and `facet_rows` prints the reason beside it rather
than letting the 1.000 stand as an achievement:

> every route a hazard used was dug by the player, by [D-T0]; so attribution is
> 1.000 by CONSTRUCTION and is NOT a finding about the entrant. The finding is
> whether the arming ply had an alternative.

So F2 is measured as `F2_arming_ply` (which ply's dig gave a hazard a road), and
`safe_alternatives_at_arming_ply` — the actions at that ply that neither die, nor
arm, nor forfeit the win. A non-empty list is "it dug its own grave out of a free
choice"; an empty one is "the level forced it". Those two sentences have
different meanings and the record refuses to use one word for both.

## 4F3 — the arithmeric of spending ground: `progress`, `threat_gain`, `balance`, `slack`

Because mobility does not shrink, F1 needs a quantity that does. Each consumed
ply is scored from the exhaustive graph, twice over — once for what the player's
task cost, once for what the hazard's road cost:

| field | definition | reading |
|---|---|---|
| `progress` | `task_before − task_after`, plies-to-win from the BFS | what the dig bought |
| `threat_gain` | `threat_before − threat_after`, the hazard's distance to you | what the dig handed over |
| `balance` | `progress − threat_gain` | **negative = the ply spent more ground than it bought** |
| `slack` | `threat_after − task_after` | the turns this run can still afford to waste |

Three decisions are inside those four columns and all three are recorded:

* `None` on either side of `threat` means **no road**, not zero — except when
  *both* sides are `None`, which is `threat_gain = 0`: a hazard that could not
  reach you and still cannot has gained nothing. The first draft returned `None`
  there too, which silently deleted every negative-balance ply from every run
  before the first dig near a hazard — i.e. from most of the item set. Fixed, and
  the fix is what makes `[F]`'s exhibit fire.
* A road that **opens** on this ply has no magnitude in steps at all, so
  `threat_gain` is `None` and `hazard_route_changed` is `True`. An event with no
  units is reported as an event, not converted into a number.
* `F1_committed_to_dug_ground` ("still winnable, and every remaining plan must
  dig") is **degenerate on this item set** and is kept anyway, because the shape
  is right and a reader should be able to see a metric flatten: with the pearls
  in soil there is never a tunnel-only completion, so it is `True` from ply 1 to
  the end on 13 of the static-planner's 18 plies. Reporting only the metric that
  moved would have hidden that the interesting question was asked in the wrong
  units.

## 4F4 — `[D-END]` decides the FLOOR of the scale, and entombment is not what I expected

Two numbers from `digdug_readings.py`, because they are the two that would not
have survived an argument:

* Under the rejected reading of "whose turn resolves first"
  (`end_on_solve_first=False`), **01 stops being winnable**. `opt = None`,
  exhaustive, and the frozen one-letter solution ends `KILLED_BY_HAZARD`. The
  level that exists to catch "a model that cannot do this cannot play at all"
  becomes a level nobody can play — which means the floor of the score scale is a
  *consequence of an undecided clause*, and a report that compares two runs of
  this cabinet without naming the clause is comparing two different games.
* `ENTOMBED_BY_A_LIVING_WALL` — a run that is alive, short of the objective, and
  has **no legal action left** — was reachable only under `hazard_clock=never`
  (probe P2). A chasing hazard never lets you finish sealing yourself in next to
  it; entombment is what a hazard-as-*terrain* reading produces and not what
  hazard-as-pursuer does. An earlier draft of this section claimed the state was
  unreachable outright; that claim was produced by a version of the chase loop
  written the wrong way round (`hazard_distances` measured from the hazard
  instead of from the player, so a pursuer standing next to its quarry found no
  closer neighbour and called it boxed in) and it is recorded here because a void
  conclusion from a buggy kernel is still a conclusion someone might have quoted.

## 4F5 — one trace, two projections: what each facet got

The whole field, one declared instrument setting (`reasoning=off`), 13 bundles,
12 code entrants, replayed by `test_digdug.py` (649 checks, 0 failures):

| entrant | score | won | moves | F1 `mobility_shrink_events` | F1 `plies_negative_progress` | F1 plies lost-while-mobile | F1 min slack | F2 arming plies | F2 died after arming | F2 deaths with a safe letter |
|---|---|---|---|---|---|---|---|---|---|---|
| `reference` | 0.8 | 4 | 19 | 0 | 0 | 1 | 2 | 3 | 0 | 0 |
| `slack-maximiser` | 0.8 | 4 | 19 | 0 | 0 | 1 | 2 | 3 | 0 | 0 |
| `beeline` | 0.6 | 3 | 18 | 0 | 1 | 0 | 2 | 4 | **2** | **1** |
| `static-planner` | 0.6 | 3 | 18 | 0 | 1 | 0 | 2 | 4 | **2** | **1** |
| `plan-emitter` | 0.2 | 1 | 1 | 0 | 0 | 1 | 1 | 2 | 0 | 0 |
| `liar` | 0.0 | 0 | 30 | 0 | 10 | 19 | — | 1 | 1 | 0 |
| `waiter` | 0.0 | 0 | 42 | 0 | 0 | 20 | — | 1 | 1 | 0 |
| `wall-bumper` | 0.0 | 0 | 1 | 0 | 0 | 21 | — | 1 | 1 | 0 |
| `resigner` | 0.0 | 0 | 0 | 0 | 0 | 1 | — | 1 | 0 | 0 |
| `garbage` | 0.0 (ERROR, zero measured) | 0 | 0 | 0 | 0 | 29 | — | 1 | 0 | 0 |
| `soft-resigner` | 0.0 (ERROR, zero measured) | 0 | 0 | 0 | 0 | 29 | — | 1 | 0 | 0 |
| `never-starts` | — (exit 4) | 0 | 0 | 0 | 0 | 0 | — | 0 | 0 | 0 |

`mobility_shrink_events = 0` on every row including the oracle's — the monotonicity
is a property of the rules, not of one entrant's misfortune. `—` marks a field
that had no numeric value on any item (no hazard ever had a road), and every
aggregate in the bundle carries `<field>__items` beside it so a sum over two
items cannot be read as a sum over five.

**F2's crown number, and it is a measurement rather than a metaphor:**

```
beeline  02_the_shortcut.txt  KILLED_BY_HAZARD  armed_at=4  ply=4
         safe_alternatives_at_arming_ply = ['D']
```

At the ply where the beeline's own dig gave the hazard its road, exactly one
action was available that neither died, nor armed, nor forfeited the win: `D`.
It had a way out and dug the grave instead — and the same is true of
`static-planner` on the same level. `arms_with_no_safe_alternative = 0` across
the whole field: **no death in this cabinet was forced by the level.** That is
the finding F2 was built to be able to say, and the counter that would have said
"forced" is at zero rather than absent, which is what makes the claim mean
something.

The `None` beside it matters the other way too: on 04 the hazard is armed at ply
0 (authored `_` tunnels), so *no ply of any run is an arming ply*, and
`safe_alternatives_at_arming_ply` is absent — with
`safe_alternatives_note` saying so. An absent number and an empty list are two
different statements and the record keeps them apart.

The photo finish is the place the two projections are genuinely about different
things, and they disagree on purpose. On 05's optimal line the winning ply (4)
carries, in the same row of the same trace:

```
F1_dist_to_win                 0     (the task is finished)
F2_min_hazard_distance         1     (a hazard is one cell away)
F2_armed                       True   (measured from the geometry of the state)
state.armed_at                 None  (the engine never set its flag)
hazard_resolution       "not_resolved_won_first"
```

The last two lines are the point. The engine's own `armed` flag says *nothing
happened*, because `[D-END]` ends the run before the world gets a turn; the
diagnostic says *it had you*, because it reads the geometry rather than the flag.
The row does not edit one to agree with the other, and the fact that both are
true at once is the whole content of the clause. F1 says "the task reached zero
at ply 4". F2 says "the level was won on the ply a hazard would have stepped onto
the player". Same row, and `test_digdug.py` replays it.

## 4F6 — what F1 and F2 cannot say on this item set, said out loud

* **Caution is free here.** The `slack-maximiser` entrant exists to trade turns
  for margin and it found lines of the *same length* as the oracle (7 = 7 on 02
  and 03; it picks a different one of 03's four optima). So this item set cannot
  price caution, and no table built from it may claim the entrants trade score
  against cost. A gap in the LEVELS, reported as one.
* **`loose_give_up_unscored` and `after_end` are structurally 0 in a driven
  run**, because the runner stops asking a level the instant the attempt ends.
  Both counters are real and both are proven in `digdug.py --self-test` [4];
  neither is available to a model run on this harness, so the record says the
  limit instead of leaving the zeros to be read as findings.
* **`[D-BLOCK]`, `[D-TIEBREAK]`, `[D-HAZCOLL]` are not testable by any level in
  this set**, and P1/P4 say why rather than leaving the rows blank. One is a
  theorem about the chase, one needs a fork behind the player, one needs the
  player to survive beside two hazards.
* **No model ran on this box.** There is no accelerator, no server and no weights
  here (`declared.gpu.name = null` with the probe that established it), so every
  number above is from code entrants, which are labelled `instrument: "code"` and
  are never pooled with a model's.
