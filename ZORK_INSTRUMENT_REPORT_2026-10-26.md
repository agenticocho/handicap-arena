# ZORK — ACCEPTED / REJECTED / UNATTRIBUTABLE, AND PROGRESS FROM THE ROOM GRAPH

**Dated 2026-10-26.** Cabinet `zork`. Card `t_8cc536de`. Authorised by Mike, 2026-10-26.
Branch `cabinet/zork-instrument` off `main` @ `32593ce`.
**CPU only. Zero model runs. Zero GPU minutes.** Nothing in this work touched the card, the lease, or
`:58595`.

---

## 0. THE SHORT VERSION

| ask | state |
|---|---|
| three-way `accepted` / `rejected` / `UNATTRIBUTABLE`, counted per row | **done**, additive to the frozen counters, checked row-by-row against them |
| rows without the counts are not scoreable | **done** — `scoreable: false` is what an old row now says by carrying nothing |
| progress against the room graph, from world state | **done** — rooms, objects moved, score, BFS bearing; **nothing in it is prose** |
| say which fields remain prose-only | **three**, named and enumerated; the `progress` block has **none** |
| a scripted walker that must reach the objective | **done** — derives its route by BFS, escapes both levels, and is shown failing three ways |
| a scripted non-parser that must produce zero accepted | **done** — 200 commands, `accepted == 0`, world unmoved, and shown moving when one real command is injected |
| the digest claim correctly stated | **the match proves a shared FILE, not a shared live instrument**, and this box's records cannot settle it — §4 |
| frozen world files untouched | **untouched**; digests re-measured and matched against the records — §6 |

**And four defects found while doing it, three of them in the instrument rather than in any entrant:**

1. **`unparsed` carried two opposite claims**, and the archive proves it: the one command the frozen
   counters called "unreadable" on Bonsai's retention row was **a real command naming a thing the
   world's own prose names** (`take metal`), while all three of Ministral's were **sentences with no
   verb in them**. Same number, opposite findings. §2.
2. **`config.n_gpu_layers: 0` contradicted `config.server_argv -ngl 99` on all eight recorded rows** —
   the summary field naming the constant it was written against, the argv naming the launch that ran.
   This is on the one field the suite card requires: the compute path. §5.
3. **`replay()` read the wrong take**, which made the cabinet's own sufficiency control file
   `reproduces: false` — "THIS IS NOT A RESULT" — against **two rows that were fine**. A control that
   cried instrument-failure where there was none, which is the mirror of the chess failure. §3.
4. **Inside the 34 rejections in the archive, 29 are `already_carrying`** — entrants re-taking what they
   already hold. The frozen counter calls all of them `recognised-but-impossible`, which is true and
   tells a reader nothing about the fact that it is the same item, over and over, for half a budget. §2.

---

## 1. WHAT CHANGED, AND WHAT DELIBERATELY DID NOT

`zork.py` · `ff35ec83b340fbf0…` (40,254 B) → `b9701007d6e186d5…` (75,338 B)
`zork_run.py` · `0c5d137931c667b0…` (67,435 B) → `19bb29c03ed70729…` (81,121 B)
`zork_controls.py` · new · `92ba23bab1f84dc5…` (26,545 B)

```python
def frozen_counter_of(category, reason):   # the additive axis maps back onto the prereg's counters
```

**THE FROZEN COUNTERS ARE NOT MOVED.** `PREREG_zork.md` pre-registers `parsed` / `unparsed` /
`recognised-but-impossible` and freezes the boundary rule for them. This cabinet's card does not license
rewriting that, and moving a pre-registered counter under a criteria set frozen against it would make
every historical row incomparable. So the three-way separation arrives **beside** the counters, and the
mapping between the two axes is a **function with a control on it**, not a paragraph of prose:

| row | frozen counter |
|---|---|
| `accepted` | `parsed` |
| `rejected` / `unknown_object`, `missing_object`, `unknown_direction`, `missing_direction` | `unparsed` |
| `rejected` / `no_exit`, `not_here`, `already_carrying`, `not_carrying`, `nothing_to_open`, `gate_locked` | `recognised-but-impossible` |
| `UNATTRIBUTABLE` / `no_verb`, `empty` | `unparsed` |

Every trace row now carries `attribution`, `reason`, `reason_text` and **`counted_under`** — so a reader
can rebuild the prereg's three numbers from the rows and check them, instead of trusting either total.

```
PASS  the per-row attribution reproduces the frozen counters EXACTLY
PASS  ...and that is a check that can fail: a mutated `counted_under` breaks it
```

**AND THE ARCHIVE ASSERTS THE SAME THING ON REAL DATA.** All eight recorded rows are replayed through
the fixed parser and their frozen counters compared to what those files recorded:

```
PASS  MiMo-V2.6-Distill-Qwen-9B-Q4_K_M / zork_02_long_crawl: the FROZEN counters are reproduced exactly
PASS  Ministral-3-3B-... / zork_02_long_crawl: the FROZEN counters are reproduced exactly
... 24 checks, 8 rows × (counters, per-row sum, score), all PASS
```

The additive axis is **additive**: it did not move one number the prereg owns.

---

## 2. THE THREE-WAY SEPARATION, MEASURED ON THE EIGHT ROWS THIS CABINET ALREADY HAD

Re-attributed read-only through `zork_controls.py`. **No record was rewritten, repaired or re-scored.**

| entrant | level | acc | rej | UNATT | old `unreadable` | rejected by reason |
|---|---|---|---|---|---|---|
| MiMo-V2.6-Distill-Qwen-9B-Q4_K_M | floor | 6 | 10 | 0 | 0 | `already_carrying=10` |
| MiMo-V2.6-Distill-Qwen-9B-Q4_K_M | crawl | 9 | 11 | 0 | 0 | `already_carrying=10`, `no_exit=1` |
| Ministral-3-3B-Instruct-2512-UD-Q4_K_XL | floor | 3 | 2 | 0 | 0 | `already_carrying=2` |
| Ministral-3-3B-Instruct-2512-UD-Q4_K_XL | crawl | 12 | 5 | **3** | **3** | `already_carrying=3`, `nothing_to_open=2` |
| Ornith-1.5-9B-Q4_K_M | floor | 2 | 2 | 0 | 0 | `already_carrying=2` |
| Ornith-1.5-9B-Q4_K_M | crawl | 7 | 0 | 0 | 0 | — |
| Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0 | floor | 3 | 0 | 0 | 0 | — |
| Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0 | crawl | 14 | 4 | **0** | **1** | `already_carrying=2`, `gate_locked=1`, **`unknown_object=1`** |

**TOTALS: 93 commands consumed — 56 accepted, 34 rejected, 3 outside the language.**

### 2.1 The pair that proves the split was needed

These two rows have the **same frozen counter for the command in question** and are **not the same kind
of event**:

```
Bonsai      zork_02   ply 4    `take metal`                                   unparsed, "unreadable": 1
Ministral   zork_02   ply 6-7  `Try moving in a direction to explore further.` unparsed, "unreadable": 3
```

* `take metal` — the verb `take` is in this world's vocabulary. The object `metal` is not, **and the
  world's own room description put it there**: `desc cellar A root cellar. Damp brick, and something
  metal on a shelf.` The entrant read the room, addressed a thing the room named, and the noun list
  refused it. Attributed **REJECTED / `unknown_object`**.
* `Try moving in a direction to explore further.` — no verb this world knows. **UNATTRIBUTABLE.**

Under the old rows, Bonsai's row read **identically** to a row full of prose. It is not that row. The
`unreadable` field on Bonsai's crawl says **1**, and a reader would reasonably conclude Bonsai produced
one unparseable string. What Bonsai actually produced was **a correct command whose noun the world's own
prose had invited and its own noun list did not have.** That is a finding about the world, not the model.

The verdict names it:

```
PASS  THE TWO ARE INDISTINGUISHABLE IN THE FROZEN COUNTERS -- that is the defect, asserted
PASS  ...but `take metal` is REJECTED: the verb is one this world knows
PASS  ...and prose with no verb in it is UNATTRIBUTABLE
PASS  `take metal` is STILL counted under `unparsed`, per the prereg -- the axis is additive, not a rewrite
```

### 2.2 The dominant rejection in the archive is one behaviour

**29 of the 34 rejections are `already_carrying`** — the entrant re-took what it already held.

```
MiMo      floor   10 of its 16 consumed commands: `take key` x 10, after the first one worked
MiMo      crawl   10 of its 20 consumed commands: `take torch` x 10
Ministral crawl    3 of its 20: `Take torch.` / `Take the torch.` x 2
Ornith    floor    2 of its 4:  `take key` x 2
Bonsai    crawl    2 of its 18: `take torch` x 2
```

MiMo is the sharpest: it took the key on ply 0 and then typed `take key` **ten more times**, spending
more than half its budget re-issuing a command that had already succeeded. The frozen counters record
that as ten `recognised-but-impossible`, which is correct and which a reader cannot distinguish from ten
different refusals of ten different things. `rejected_by_reason` distinguishes them, and it is the single
largest consumption of budget in this cabinet's entire archive.

### 2.3 The boundary cases, all controls, all passing

```
'e2e4'           -> UNATTRIBUTABLE/no_verb            'take unicorn'  -> rejected/unknown_object
'RESIGN'         -> UNATTRIBUTABLE/no_verb            'take br'       -> rejected/unknown_object
''               -> UNATTRIBUTABLE/empty             'go sideways'   -> rejected/unknown_direction
'look'           -> accepted/acted                    'go'            -> rejected/missing_direction
'north'          -> accepted/acted                    'take'          -> rejected/missing_object
'west' (no exit) -> rejected/no_exit                  'take brasskey' -> rejected/not_here
```

`take unicorn` is **REJECTED**, not `UNATTRIBUTABLE`, and that is the one boundary a reader will argue
with. The prereg's rule is about the frozen counter and it stands: `take unicorn` remains `unparsed`,
because the object does not resolve. The attribution axis asks a **different question** — *whose
vocabulary failed* — and `take` is in the world's verb vocabulary while `unicorn` is not in its nouns.
An entrant that says `take unicorn` is speaking the language and naming a thing that is not there; one
that says `xyzzy` is not. Both are failures. They are not the same failure.

---

## 3. PROGRESS AGAINST THE ROOM GRAPH — FROM WORLD STATE

`zork.progress_from_world(w, st, distance_trail)` reads **only** the parsed world and the world's state.
It never sees a command, a note or a sentence.

```
score    finished, ending, carried_required_item, took_item_at_step
rooms    total_in_world, reachable_from_start, exits_in_world, visited,
         visited_fraction_of_reachable, route, revisited
objects  total_in_world, moved_from_start_placement, in_hand, placement{...},
         required_item_start_room, required_item_placement_now, required_item_moved
bearing  gate_room, distance_start_to_gate, distance_final_room_to_gate,
         closest_gate_distance_reached, fraction_of_the_way_along_the_graph,
         distance_trail, monotone_toward_gate
```

### 3.1 The provenance table is enforced, in both directions

`PROGRESS_FIELDS` declares a source for every leaf; `provenance_gaps()` walks the block actually emitted
and fails on a leaf nobody declared, **and** on a declaration for a field that is not emitted.

```
PASS  every leaf of the progress block has a declared source
PASS  ...and every declared field is actually emitted
PASS  A FIELD WITH NO STATED SOURCE IS CAUGHT: an invented leaf is undeclared
PASS  ...and a declaration for a field that is not emitted is caught too
PASS  NO progress field is prose-derived
```

**WHAT REMAINS PROSE-ONLY — THREE FIELDS, AND NO OTHERS:**

| field | what it is |
|---|---|
| `turns[].command` | the first non-empty line of the reply, **verbatim** — the driver's reading rule. This is the **input** to the parser, not a measurement; it is the one field in a run that comes out of the entrant's own words. |
| `turns[].raw` | the reply, truncated to 400 characters for size. **Read by no scorer.** |
| `turns[].answer_field` | which JSON field the answer arrived in, off the wire. |

Nothing in `score`, `rooms`, `objects` or `bearing` is prose-derived, and the record states this as
`progress_prose_only` beside `progress_field_source` so a reader does not have to take it on faith.

### 3.2 What the graph says that the score does not

**Bonsai, `zork_02`** — `finished: false`, `ending: gate_locked`, `carried_required_item: false`.

```
rooms    visited 5 / 5 reachable (1.0)   route  hall → corridor → cellar → study → vault
objects  moved_from_start_placement 1    required_item_moved FALSE   brasskey still in cellar
bearing  distance_final_room_to_gate 0   fraction_of_the_way_along_the_graph 1.0
```

Bonsai **walked the entire room graph, reached the gate, and moved exactly one object — the torch.**
`objects moved: 1` and `score: locked` are both true and they are not the same claim. That is precisely
why the card asked for the room graph: a count of objects moved would have flattered this row, and a
score alone would have hidden that the traversal was complete.

**Ministral, `zork_02`** — `finished: false`, `carried_required_item: true`, `took_item_at_step: 10`.

```
rooms    visited 3 / 5 (0.6)     revisited 18  (18 of 20 room entries were re-entries)
objects  moved 2   required_item_moved TRUE   in_hand [torch, brasskey]
bearing  distance_start_to_gate 3   distance_final_room_to_gate 4
         closest_gate_distance_reached 2   fraction 0.3333
```

`carried_required_item: true` reads like "it had the key". **It ended FURTHER from the gate than it
started, having never got closer than two moves.** It had the faculty and could not navigate. The two
facts are in different fields and both are now measured.

### 3.3 A finding about the progress *measure*, kept rather than smoothed

```
PASS  the distance trail records the step taken AWAY from the gate to fetch the key
      [3, 4, 4, 3, 2, 1, 0]
PASS  ...so progress toward the gate is NOT monotone on the level that measures retention
```

The retention level puts the key **north** and the gate **east**. The correct solution walks **one step
away** from the objective first. A "progress never decreases" check would have scored the canonical
solution as regressing, so the field is a **trail** and the flag reports the truth instead of a
convenient one. A row that does not move the entrant repeats the previous distance, because the trail is
per command consumed and `take` changes the inventory, not the room.

---

## 4. THE DIGEST CLAIM, CORRECTLY STATED

### 4.1 What the match proves

`zork.py` was `ff35ec83b340fbf0…`, 40,254 B, and **the same bytes on both boxes.** That proves **one file
existed in two places.** It proves nothing about an instrument: an instrument is the file *plus* the
process that ran it *plus* the sitting it ran in, and a digest speaks only to the first.

**AND THIS BOX'S RECORDS CANNOT SETTLE THE QUESTION, FOR A REASON IN THE RECORD ITSELF:**

```python
def host_block():
    return {"platform": ..., "release": ..., "machine": ..., "cpus": ..., "python": ...}
```

There is **no hostname, no machine-id, no boot id**. Two different machines with the same kernel string
and the same CPU count produce **byte-identical host blocks**. Here, every recorded row carries

```
"release": "7.0.0-38-generic", "machine": "x86_64", "cpus": 12, "python": "3.14.4"
```

which is this box (`uname -r` → `7.0.0-38-generic`, `nproc` → `12`) **and would equally be any other box
configured the same way**. So: *the record cannot demonstrate cross-box provenance at all.* Adding a
distinguishing field is a change to the record format and belongs to whoever owns `FORMAT.md`, not to
this card — **reported, not done.**

### 4.2 What I can say from this box

**YES — one box, one revision, two sittings, and both copies survive.** This is the only cross-sitting
claim the artifacts support, and it is checkable:

| | sitting 1 | sitting 2 |
|---|---|---|
| record | `suite2/runs/published_cpu/ZORK_Ministral-…_zork_01_the_floor.json` | `suite3/preserved/20261026-140512/ZORK_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_zork_01_the_floor.json` |
| mtime / preserved | `2026-10-17 10:55`, preserved `2026-10-25T13:46:04-0700` | `2026-10-25 13:46` |
| `simulator_digest` | `ff35ec83b340fbf0` | `ff35ec83b340fbf0` |
| launch in argv | `-c 4096 -ngl 0 --port 8752` | `-c 4096 -ngl 99 --port 58701 --parallel 1` |
| outcome | `escaped`, counts `{parsed 3, unparsed 0, impossible 2}` | `escaped`, counts `{parsed 3, unparsed 0, impossible 2}` |

Eight days apart, same simulator digest, same box, **and the two rows agree on every counter.** The
sitting-2 record carries the replacement note verbatim ("*the GPU row is a new row, this copy is the
record of the row that was already there*"), so the preservation is on the record rather than asserted
here.

> **CITATION REPAIRED 2026-10-26 (card `t_a828c554`).** The sitting-2 cell named
> `probes/ZORK_Ministral-…_zork_01_the_floor.json`, which now holds the `13b161a` re-measurement and not
> the record this table describes. It is repointed to the preserved path above —
> `suite3/preserved/20261026-140512/…`, 17,803 B, its own mtime `2026-10-25 13:46`, `simulator_digest`
> `ff35ec83b340fbf0`, `-ngl 99` — which is the row every cell of this row is about. Nothing else in the
> table moved, and the preserved rows are cited by their preserved paths, never as `probes/`.

**NO — two boxes in one sitting.** I cannot show it, and I am not going to state it as though a matching
digest implied it. What a matching digest would license is exactly one sentence: *the file was the same
file.* Whether either box **ran** it in the same sitting is not in any artifact on this disk.

**AND THE REVISION HAS NOW MOVED, WHICH IS THE MOST IMPORTANT THING IN THIS SECTION.**

```
zork.py   ff35ec83b340fbf0…   the instrument that produced all eight rows
zork.py   b9701007d6e186d5…   the instrument from this commit forward
```

**Every one of the eight recorded rows was produced by an instrument that no longer exists.** They are
rows of a superseded instrument: their **frozen counters and scores remain valid** — §1 replays all
eight and reproduces them exactly — but they carry **no attribution and no `progress`**, so on the new
axis they are **`scoreable: false`**, and that absence is a true statement about them rather than a gap
to be filled in later. **They must be carried beside any new rows, never merged, never re-scored.**

---

## 5. THE COMPUTE-PATH FIELD THAT CONTRADICTED ITSELF ON EVERY ROW

Found while establishing §4, and reported because the suite card requires each row to carry its compute
path.

```
probes/ZORK_*.json     config.n_gpu_layers = 0        config.server_argv = [... -c 4096 -ngl 99 --parallel 1]
```

**All eight rows.** `n_gpu_layers` was written as the literal `0` (`zork_run.py:799`), while the argv
beside it was built from the `NGL` the run actually used. A reader taking the summary files **eight CPU
rows**; a reader taking the argv files **eight GPU rows**; neither would know the other existed. Same
defect class as the counters this card is about — one record, two claims, no way to tell which is the
measurement — and it landed on the one field the suite card names as required.

`argv_value()` and `compute_path()` now **read the summary out of the argv**, so the two cannot drift,
and the control fires on the archive:

```
PASS  with --ngl 99 the argv says -ngl 99
PASS  ...and the summary field agrees with it
PASS  a flag that is absent reads as None, not as a plausible zero
PASS  EVERY recorded GPU row contradicts itself: config.n_gpu_layers vs config.server_argv -ngl
PASS  ...and the contradiction is 0 against 99, on all eight
      8 rows: the summary said CPU, the argv said GPU. Neither reader would know the other existed.
```

**For Ocho, before scoring anything:** the eight existing rows are `-ngl 99 --parallel 1 -c 4096` per
their argv, and their summary field says CPU. **The argv is the measurement.** The old rows are not
rewritten; the finding is here.

---

## 6. THE FROZEN WORLD FILES — NOT EDITED, AND HERE IS THE PROOF

The card says do not edit them, and append a dated NOTE.

```
NOTE (2026-10-26) — THE FROZEN WORLD FILES WERE NOT EDITED.

    levels/zork_01_the_floor.txt   699ef17bfe26521b…   661 B
    levels/zork_02_long_crawl.txt  c1d33b940fd842ed…  1,890 B

  These are not digests taken before and after my own work — they are the digests the EIGHT RECORDED
  ROWS CARRY as `level_digest`. They were produced on 2026-10-17 and 2026-10-25, before this card
  existed. The files today hash to the same values, so the claim is checked against the archive rather
  than against my word. `zork_controls.py` replays all eight rows from the `level_text` those records
  carry and reproduces their frozen counters exactly, which could not happen if the worlds had moved.
```

**One thing about those files that I could not fix and am not going to quietly live with:**
`desc cellar` reads *"Damp brick, and something metal on a shelf."* — and there is no item `metal`. The
world's prose names a thing its own parser refuses. Bonsai's `take metal` is the direct consequence, and
it is attributed `REJECTED / unknown_object` rather than blamed on the entrant. Whether to add the item,
add an alias, or change the description is a change to a **frozen** file and is the Chair's call, not
this cabinet's.

---

## 7. THE CONTROLS THAT CAN FIRE

`python3 zork_controls.py` — **93/93 PASS**, CPU only, zero model runs. Artifact:
`ZORK_CONTROLS_2026-10-26.json`. Full stdout: `ZORK_CONTROLS_2026-10-26.txt`.

### 7.1 The walker — derived, not hardcoded, and asserted to finish

`walker_plan()` is given a **world and no answer**. It BFS-searches the world's own exits for
`start → required item → gate`.

```
zork_01_the_floor   plan: take key ; north
                    legs: [] -> take key -> ['north']
zork_02_long_crawl  plan: north ; take brasskey ; south ; east ; north ; east
                    legs: ['north'] -> take brasskey -> ['south', 'east', 'north', 'east']

PASS  zork_01_the_floor: it FINISHES                                    (True, 'escaped')
PASS  zork_02_long_crawl: it FINISHES                                   (True, 'escaped')
PASS  zork_02_long_crawl: every command it typed was ACCEPTED           (6 == 6)
PASS  zork_02_long_crawl: it ends on the gate, so the graph distance is zero   0
PASS  zork_02_long_crawl: it moved exactly one object -- the required one      1
PASS  zork_02_long_crawl: the derived route == the documented solution      ['north','take brasskey',...]
```

The last check is the one that ties the walker to the level: the route it **derived from the graph** is
the route the level file's comment block **documents** (up to the alias — the walker has only the item
id). Neither was given the other.

### 7.2 And the walker can fail — three ways that must not finish

```
PASS  the walker WITHOUT the take reaches the gate and is LOCKED          gate_locked
PASS  ...and moved NO object                                              0
PASS  the walker with its LAST move cut off does not finish               out_of_commands
PASS  ...and is one room short of the gate                                1
PASS  the walker walking its route BACKWARDS does not finish              False
PASS  a world whose gate is unreachable is REFUSED, not silently played    ValueError
```

Without these, `escaped` is a number nobody has watched move.

### 7.3 The non-parser — zero accepted, and the world does not move

200 commands from a fixed list, cycling. Each is asserted **by the generator itself** to have a first word
that is neither a verb nor a direction this world knows.

```
PASS  EVERY one of them is outside this world's vocabulary -- the generator's own control   200/200
PASS  zork_01_the_floor: ZERO accepted commands                        0
PASS  zork_01_the_floor: every command is UNATTRIBUTABLE              200
PASS  zork_01_the_floor: the frozen counter says `unparsed == 200` too  200
PASS  zork_01_the_floor: THE WORLD DID NOT MOVE -- same room            'hall'
PASS  zork_01_the_floor: ...same inventory                             []
PASS  zork_01_the_floor: ...zero objects moved                          0
PASS  zork_01_the_floor: ...and the distance to the gate never changed  0.0
... same six checks on zork_02_long_crawl
```

### 7.4 And that assertion can move

```
PASS  EXACTLY ONE command is accepted                              1
PASS  ...and it is the one that was injected                       trace[100] == 'north'
PASS  ...which is the only row whose attribution is not UNATTRIBUTABLE   [100]
PASS  ...and the world moved by that one command                   'cellar'
PASS  ...so `accepted == 0` above was not a counter stuck at zero  True
PASS  five looks are five accepted commands that move nothing      (5, 'hall')
```

### 7.5 The non-parser's own near-miss, which I had to fix rather than exclude

**THE FIRST VERSION OF THE NON-PARSER FAILED ITS OWN CONTROL — 195 unattributable, 5 accepted.** The
offending string was `I am not sure what to do next.`, and `i` is a **declared abbreviation for
inventory**. The parser read the sentence as a command, correctly, by its own frozen vocabulary.

The entry was **moved out of the gibberish list and is now asserted in the other direction**:

```
PASS  the excluded `I ...` sentence IS read as a command by this world, which is why it is excluded
      ('accepted', 'inventory')
PASS  ...so a non-parser built on it would be measuring the synonym list, not the language   0
```

A test that quietly drops the cases it fails is the same defect as a counter that quietly folds two
claims into one, so the exclusion is stated in the source, justified by measurement, **and asserted**.

---

## 8. THE REPLAY DEFECT — A CONTROL THAT CRIED WOLF ON TWO ROWS

`replay()` recovered `took_item_at_step` as **the first row with `outcome == 'took'`, any item.** `play()`
sets that field to **the first take OF THE REQUIRED ITEM.** On `zork_01_the_floor` (one item) the two
readings agree and the error is invisible. On `zork_02_long_crawl`, which ships a **distractor** (the
torch), they disagree for any entrant that takes the torch first:

| record | `play()` said | `replay()` said | stored as |
|---|---|---|---|
| `ZORK_MiMo-…_zork_02_long_crawl.json` | 17 | **0** (the torch, ply 0) | `sufficiency_ok: false` |
| `ZORK_Ministral-…_zork_02_long_crawl.json` | 10 | **0** (the torch) | `sufficiency_ok: false` |

Both were filed **"THE RECORD DOES NOT REPRODUCE ITS OWN SCORE. THIS IS NOT A RESULT: it is an instrument
failure, and the number above it must not be filed."** **The records were fine. The replay was wrong.**

**THE TWO RECORDS ARE NOT REWRITTEN.** They are the record of what the instrument said at the time, and
what it said was false. `replay()` now takes the required item, says which basis it used, and reports
`takes_by_object` so the old reading is visible instead of silently corrected:

```
PASS  replay() WITHOUT the required item reads the TORCH and returns 0 -- THE DEFECT, asserted
PASS  replay() WITH the required item returns the required take                2
PASS  ...and the takes by object show BOTH items                               {'torch': 1, 'brasskey': 1}
PASS  on the FLOOR world, one item, the two readings agree -- which is why this was invisible   (0,0,0)
```

A control that reports an instrument failure where there is none is the same defect as one that reports
none where there is one. This cabinet has now had both, and both are controls.

---

## 9. CONTROL TOTALS

| suite | before | after |
|---|---|---|
| `python3 zork.py --self-test` | 114/114 | **175/175** |
| `python3 zork_run.py --self-test` | 43/43 | **64/64** |
| `python3 zork_controls.py` | — | **93/93** |

Baselines measured from `git show HEAD:zork.py` and `git show HEAD:zork_run.py` against the same levels,
not remembered.

---

## 10. WHAT THIS CABINET STILL CANNOT SEPARATE — STATED, NOT HIDDEN

1. **A correct direction that loses from a wrong command.** On `zork_01_the_floor`, `north` walks into
   the terminal gate and is **`REJECTED / gate_locked`** even though the direction was right. `accepted`
   therefore **understates competence on the terminal row**, and the record says so rather than counting
   the row as a failure of parsing.
2. **`open` ignores its argument.** `step()`'s `open` branch tests only the room and the inventory, so
   `open brasskey`, `open door` and `open vault` are the same command — and Ministral's `> Open
   brasskey.` / `> Use torch.` both land as **`nothing_to_open`**, which reads like a world fact and is
   really "*this verb cannot take an object here.*" Two of the archive's 34 rejections are this.
3. **Intent is not measured at all.** Whether the entrant understood *why* it carried the key is not a
   field, and cannot be: the only way to score it is to read the model's own explanation, which is
   exactly the prose-reading this cabinet exists to refuse. `carried_required_item` is a state flag, not
   an intention. The `takes then drops` reference line in `PREREG_zork.md` covers the **behaviour**; the
   **understanding** is out of scope and should be reported as out of scope.
4. **`take metal` cannot be attributed to the model.** The world's description invites the command; the
   world's noun list refuses it. Until the Chair rules on §6, that rejection is a **world** finding on a
   row that looks like an entrant finding.
5. **Old rows are not scoreable on the new axis and will never be.** Eight rows, `scoreable: false`,
   permanently. Nothing here repairs them.

---

## 11. WHAT WAS NOT DONE, DELIBERATELY

* **No model run.** The scorer was validated against **eight real command streams produced by four real
  models** — replayed through the fixed parser — which is stronger evidence than a fresh synthetic run
  and costs no GPU. If Ocho wants a fresh row on the new axis, that is a new row in Ocho's window, not
  something this card takes.
* **No GPU, no lease, no `:58595`.** Nothing in this card touched the card. `nvidia-smi` was never
  called.
* **`PREREG_zork.md` not edited.** The frozen counters and the boundary rule are untouched; the additive
  axis is documented in the source and in §1.
* **The eight records not edited.** Read-only, re-attributed, and their false `sufficiency_ok: false`
  left standing with this document as the correction.
* **`host_block()` not extended.** §4.1 says the record cannot demonstrate cross-box provenance; adding a
  distinguishing field is a `FORMAT.md` decision.

---

## 12. TO THE LOCAL CHAIR

**Commit:** `cabinet/zork-instrument`, off `main` @ `32593ce`.
**Files:** `zork.py`, `zork_run.py`, new `zork_controls.py`, `ZORK_CONTROLS_2026-10-26.json`,
`ZORK_CONTROLS_2026-10-26.txt`, this report.
**Controls' output:** §7 and §9 — 175/175, 64/64, 93/93, all CPU.
**Fields that remain prose-only:** `turns[].command`, `turns[].raw`, `turns[].answer_field`. Nothing in
`progress` is prose-derived, and that is enforced by a control rather than asserted.

**Three things for you to decide, all of them outside this card's authority:**

1. **`take metal` and the cellar's description** (§6). The world invites a command it refuses.
2. **The eight rows' compute path** (§5): their summary says CPU, their argv says `-ngl 99`. Ocho is
   about to verify certifications against these artifacts and will read one of the two.
3. **`host_block()`** cannot distinguish two boxes (§4.1). If cross-box provenance is a claim this
   project wants to make, the record format needs a field that can support it.
