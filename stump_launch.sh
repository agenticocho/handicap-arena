#!/usr/bin/env bash
# STUMP Launcher — starts model servers, waits for readiness, opens cabinet
# Usage: ./stump_launch.sh [--model-a ornith9b] [--model-b lfm3-1.7b]
set -e

MODEL_A="${1:-ornith9b}"
MODEL_B="${2:-lfm3-1.7b}"
PORT_A=8360
PORT_B=8376

# Model paths
declare -A MODEL_PATHS
MODEL_PATHS["ornith9b"]="/Users/mikebird/models/llm/inference/Ornith-1.5-9B-Q4_K_M.gguf"
MODEL_PATHS["lfm3-1.7b"]="/Users/mikebird/models/llm/inference/LFM3-1.7B-Q4_K_M.gguf"

# Kill any existing servers
pkill -f "llama-server.*$PORT_A" 2>/dev/null || true
pkill -f "llama-server.*$PORT_B" 2>/dev/null || true
sleep 2

# Start model A
echo "Starting $MODEL_A on port $PORT_A..."
/opt/homebrew/bin/llama-server \
  --model "${MODEL_PATHS[$MODEL_A]}" \
  --host 127.0.0.1 --port $PORT_A \
  --ctx-size 4096 --parallel 1 \
  --n-gpu-layers 999 --jinja --alias "$MODEL_A" \
  --cache-type-k q4_0 --cache-type-v q4_0 --no-mmproj \
  --reasoning on --cache-ram 512 &
PID_A=$!

# Start model B
echo "Starting $MODEL_B on port $PORT_B..."
/opt/homebrew/bin/llama-server \
  --model "${MODEL_PATHS[$MODEL_B]}" \
  --host 127.0.0.1 --port $PORT_B \
  --ctx-size 8192 --parallel 1 \
  --n-gpu-layers 999 --jinja --alias "$MODEL_B" &
PID_B=$!

# Wait for both servers to be ready
echo "Waiting for servers to load..."
for port in $PORT_A $PORT_B; do
  for i in $(seq 1 60); do
    if curl -s http://127.0.0.1:$port/v1/models >/dev/null 2>&1; then
      echo "  Port $port: READY"
      break
    fi
    sleep 2
  done
done

# Pre-warm both models (page in weights)
echo "Warming up models..."
curl -s -X POST http://127.0.0.1:$PORT_A/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"'$MODEL_A'","messages":[{"role":"user","content":"Hi"}],"max_tokens":5,"temperature":0.0}' >/dev/null 2>&1
curl -s -X POST http://127.0.0.1:$PORT_B/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"'$MODEL_B'","messages":[{"role":"user","content":"Hi"}],"max_tokens":5,"temperature":0.0}' >/dev/null 2>&1
echo "Models warm."

# Open cabinet
CABINET="/Users/mikebird/arena/handicap-arena/stump_cabinet.html"
echo "Opening cabinet at http://localhost:8765/stump_cabinet.html"
open "http://localhost:8765/stump_cabinet.html"

echo ""
echo "STUMP is running. Press Ctrl+C to stop servers."
echo "Model A: $MODEL_A on :$PORT_A (PID $PID_A)"
echo "Model B: $MODEL_B on :$PORT_B (PID $PID_B)"

# Wait for user to stop
wait $PID_A $PID_B 2>/dev/null || true
