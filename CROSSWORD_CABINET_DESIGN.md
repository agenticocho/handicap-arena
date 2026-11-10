# Crossword Cabinet — Visual Design Plan

## Overview
The cabinet renders a criss-cross crossword puzzle being solved by a resident model in real-time. It replays (or polls) a trace file and animates each turn: slot selection, word landing, crossing check, contradiction/fit, and termination.

## Grid
- 12×14 cells (variable per crate), each cell at least 24px.
- Black cells: dark (#0a0a0a) with subtle border.
- Empty white cells: dark blue (#1a1a2e) with 1px border.
- Filled cells: lighter (#1a2a18) with letter in gold (#ffcc33).
- Contradicted cells: dark red (#3a1a1a) with red letter (#ff5a5a) and diagonal strikethrough.
- Active slot cells: gold border (3px) with subtle glow.
- Crossing cells (where active slot intersects a filled slot): pulsing highlight (alternating gold/dark over 300ms).

## Slot highlight
- The active slot's cells get a 3px gold border and a subtle background tint (#3a3a0a).
- The slot's clue is shown in the clue panel below the grid.
- The slot's direction (across/down) shown as an arrow.

## Word landing animation
- Letters appear one cell at a time, 50ms apart, left-to-right (across) or top-to-bottom (down).
- Each letter scales in (0.5→1.0) over 100ms with ease-out.
- After the last letter: 300ms pause for crossing check.

## Crossing check
- Each crossing cell (where the new word intersects an already-filled word) pulses: green if consistent, red if conflict.
- The crossing word's letters are briefly highlighted (200ms).
- If all crossings consistent: green flash on the slot's cells (200ms), then settle.
- If any crossing conflicts: red flash on conflicting cells (300ms), cells turn dark red (dead), "CONTRADICTION" indicator appears.

## Contradiction visualization
- Conflicting cell(s) flash red (3 frames at 100ms each), then turn dark red.
- Already-placed word's letters stay visible (spectator sees both).
- New word is NOT placed — grid stays as-is.
- Slot marked failed in the log.
- Dead cells accumulate (dark red with strikethrough). By the end, the grid shows which regions died.

## Clue panel (below grid)
- Current clue text (large, readable).
- Candidates list (smaller, the slot's candidates).
- Crossing pattern (???? with filled letters).
- "Letters already fixed at crossings: position N = X" (if any).
- Candidates that match crossings (highlighted).
- Key badge: if clue_candidates === 1, show a pink "1" in the top-right corner of the slot's first cell (anagram-recoverable slot).

## Model badge
- Top-left of cabinet: model name in large text (blue for ornith9b, amber for lfm3-1.7b).
- Below: parameter count badge (9B / 1.7B).
- Top-right: arm indicator (ARM A / ARM B).

## Readout line
- TURN · FILLED · CORRECT · CONTRADICTIONS · CLOCK · CCR
- Example: "TURN: 12 · FILLED: 34/51 · CORRECT: 27 · CONTRADICTIONS: 6 · CLOCK: 2:30 · CCR: 0.4 (4/10)"

## Narrative log (bottom, scrollable)
- Each turn as a row: "tick 0 A1 CIGARS ✓" or "tick 8 D1 DROPOUT ✗ CONTRADICTION"
- Color: green for accepted, red for contradiction, amber for malformed, grey for timeout.
- Auto-scrolls to latest.
- Max height 80px, scrollable.

## Termination banner
- When all slots filled or abandoned: animation stops. Banner appears:
  - "SOLVED" (green, large) — all slots correct
  - "CONTRADICTED" (red, large) — at least one contradiction
  - "ABANDONED" (amber, large) — no progress
- Final grid stays visible. Readout shows final stats.
- Banner fades in over 500ms.

## Side-by-side (two models)
- Two cabinets, same crate, same animation timing.
- Shared clock at the top.
- Spectator watches both play simultaneously.
- Each cabinet shows its model's name, results, and play-by-play.

## Live play mode
- The harness writes the trace incrementally (flush after each turn).
- The cabinet polls the trace file every 500ms via fetch().
- When a new turn appears, advance the animation.
- The cabinet shows "LIVE" indicator when polling.

## Data needed from the trace (all present)
- grid_state per turn
- fill: slot, word, contradiction, clue_candidates
- accepted, conflicts_with_crossings
- eval_before/after (satisfiable slot count)
- slot, answer_submitted, answer_field
- secs, gen_tokens, budget_hit
- model, arm, crate_digest
- slots_attempted, malformed_count, wrong_count, timeout_count
- crossing_consistency_rate, ccr_all_fills, ccr_with_crossing_denominator
- slot_clue_candidates, slot_candidates
- termination, solved, correct_slots, filled_slots

## Implementation notes
- The existing cabinet already has the animation loop (playLoop, advanceTurn, drawGrid).
- Changes are visual: larger cells, slot highlight, crossing pulse, contradiction flash, model badge, termination banner.
- Cell-to-slot map can be built from fill data (each fill has slot + word; apply to cells).
- slot_clue_candidates already in trace (marker on cells where clue_candidates === 1).
- The trace is embedded as a JSON constant (TRACE) for replay mode. For live mode, poll via fetch().
