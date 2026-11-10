# STUMP — Two-Model Wits Challenge

## What is STUMP?

STUMP is a two-model wits challenge. Model A fires 3 verifiable questions it can accurately answer. Model B answers them. An oracle validates. Best 2 of 3 wins the round.

The game tests whether a model knows what it doesn't know. Questions are constrained by a frozen grammar (illposed-v1) that generates both well-posed (answerable) and ill-posed (unanswerable) questions.

## Model Pairings (from spec)

| Pairing | Model A | Model B | Notes |
|---------|---------|---------|-------|
| 2B vs 2B | (need two 2B models) | (need two 2B models) | Closest match |
| 4B vs 4B | (need two 4B models) | (need two 4B models) | Balanced |
| 4B vs 9B | ornith9b (9B) | jang (4B) | Ornith advantage |
| 9B vs 1.7B | ornith9b (9B) | lfm3-1.7b (1.7B) | Current (lopsided) |

## Current Setup

- **Model A:** ornith9b (9B params) on :8360
- **Model B:** lfm3-1.7b (1.7B params) on :8376
- **Grammar:** illposed-v1, digest `e0a456b3...`
- **Result:** ornith9b 26/30, lfm3-1.7b 15/30 (calibrated, 3 passes)

## Running STUMP

### Prerequisites
- llama-server installed at /opt/homebrew/bin/llama-server
- Model files in /Users/mikebird/models/llm/inference/
- Python 3 with json module
- Brave/Chrome browser
- http.server running on port 8765 (or any static file server)

### Start servers
```bash
# Terminal 1: Start ornith9b
/opt/homebrew/bin/llama-server \
  --model /Users/mikebird/models/llm/inference/Ornith-1.5-9B-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8360 --ctx-size 4096 --parallel 1 \
  --n-gpu-layers 999 --jinja --alias ornith9b \
  --cache-type-k q4_0 --cache-type-v q4_0 --no-mmproj \
  --reasoning on --cache-ram 512

# Terminal 2: Start lfm3-1.7b
/opt/homebrew/bin/llama-server \
  --model /Users/mikebird/models/llm/inference/LFM3-1.7B-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8376 --ctx-size 8192 --parallel 1 \
  --n-gpu-layers 999 --jinja --alias lfm3-1.7b
```

Or use the launcher: `./stump_launch.sh`

### Wait for servers to load
Both servers print "listening on http://127.0.0.1:PORT" when ready. This takes ~1-2 minutes.

### Start the cabinet
```bash
# If not already running:
cd /Users/mikebird/arena/handicap-arena && python3 -m http.server 8765
```

### Play
1. Open `http://localhost:8765/stump_cabinet.html` in browser (NOT file://)
2. Hard-refresh (Cmd+Shift+R)
3. Click CLEAR SAVED PROGRESS
4. Click INSERT COIN
5. Watch the game play live (~3.5 min for 30 questions)

### Important
- No other process can use ports 8360 or 8376
- The sokoban harness (t_545d9eb9) competes for port 8360 — must be stopped
- Browser harness daemons consume CPU — close unused browser tabs
- The game takes ~3.5 minutes for 30 questions (Model A ~2.5 min, Model B ~1.25 min, Replay ~1 min)

## Files
- `stump_cabinet.html` — The cabinet (self-contained, 35KB)
- `stump.py` — The harness (question gen, oracle, scorer, trace writer)
- `STUMP_CABINET_DESIGN.md` — Design doc (visual spec, audio, CRT, bindings)
- `FROZEN_STUMP_GRAMMAR.json` — Frozen grammar (digest: e0a456b3...)
- `stump_launch.sh` — Server launcher script
- `traces/stump_calibrated_ornith9b_lfm1.7b_p{1,2,3}.json` — Calibrated results

## Architecture
- Cabinet: client-side HTML/JS, calls model APIs via fetch()
- Servers: llama-server (local GGUF models)
- No backend required — but servers must be running
- localStorage persists progress across browser drops
- Resume from partial progress supported

## Known Issues
- Model servers must be started manually (not baked into the game)
- 30 questions takes ~3.5 minutes (reduce to 10 for faster play)
- Browser must load via HTTP (not file://) for fetch() to work
- Model server can deadlock under memory pressure (0.1 GB free)
- The answer key uses "INSUFFICIENT" but the neutral prompt doesn't tell models to output this — they produce natural language refusals that are classified by keyword matching
- 9B vs 1.7B is lopsided (26/30 vs 15/30) — need closer model pairings for competitive play