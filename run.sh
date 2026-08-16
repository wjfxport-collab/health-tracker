#!/bin/bash
set -e

# Project paths
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="/home/wjf42/.gemini/antigravity/scratch/tools/nodejs/bin:$PATH"
export LD_LIBRARY_PATH="/home/wjf42/.gemini/antigravity/scratch/tools/tesseract/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export TESSDATA_PREFIX="/home/wjf42/.gemini/antigravity/scratch/tools/tesseract/usr/share/tesseract-ocr/5/tessdata"

echo "=================================================================="
echo " Starting HealthPulse (Flask API + OCR Engine + React Frontend)  "
echo "=================================================================="

# Function to stop background processes when interrupted
cleanup() {
  echo ""
  echo "Shutting down servers..."
  kill $(jobs -p) 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 1. Start Flask API Backend
echo "-> Starting Flask backend on http://127.0.0.1:5000..."
"$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/backend/app.py" &
FLASK_PID=$!

# Wait for Flask to boot
sleep 1.5

# 2. Start Vite React Frontend
echo "-> Starting Vite React frontend on http://localhost:5173..."
cd "$PROJECT_DIR/frontend"
npm run dev -- --host

# Wait for background jobs
wait $FLASK_PID
