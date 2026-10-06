# Harness history — how the four confounds were found

These are the earlier iterations, kept because they document the failures that shaped the design.
Each one produced a clean, confident, completely wrong leaderboard.

- `arena_v0.py` — first attempt. Pointed at application-configured endpoints.
  **Bug 1:** two entrants referenced deleted GGUFs and were scored 0.00 as if they were models.
  **Bug 2:** reasoning models return the answer in `reasoning_content`; the scorer read `content`.
- `arena_v01.py` — added a pre-flight and a content/reasoning fallback.
  **Bug 3 (found here):** all four `ocho-planner*` aliases were launched with a GBNF grammar file,
  making the model physically incapable of the requested output. The table measured the grammar.
  **Bug 4:** an alias named `granite-8b` served Qwen3.5-9B, and `qwen-7b` served Qwen3.5-9B.
- `diag_reasoning.py` — the probe that found bugs 3 and 4 by dumping the raw response fields.
- `arena_v02_controlled.log` — the controlled experiment: same weights, grammar vs no-grammar.

The current `arena.py` exists specifically to make all four impossible: it spawns its own server,
takes file paths instead of aliases, prints its flags, records the sha256, and scratches any
entrant that fails to serve.
