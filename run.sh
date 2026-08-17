#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "=================================================================="
echo " Starting HealthPulse (Auto-Setup & Launch)                      "
echo "=================================================================="

# Check for Node.js / npm
if ! command -v node &> /dev/null; then
  # Check local tools fallback if present
  if [ -d "$PROJECT_DIR/../tools/nodejs/bin" ]; then
    export PATH="$PROJECT_DIR/../tools/nodejs/bin:$PATH"
  elif [ -d "$HOME/.nvm/versions/node" ]; then
    NODE_LATEST=$(find "$HOME/.nvm/versions/node" -maxdepth 2 -name "bin" 2>/dev/null | tail -n 1)
    [ -n "$NODE_LATEST" ] && export PATH="$NODE_LATEST:$PATH"
  fi
fi

if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
  echo "❌ Error: Node.js and npm are required to run the frontend."
  echo "Please install Node.js (https://nodejs.org) or install via your package manager."
  exit 1
fi

# Check for Python 3
PYTHON_BIN=""
if command -v python3 &> /dev/null; then
  PYTHON_BIN="python3"
elif command -v python &> /dev/null; then
  PYTHON_BIN="python"
else
  echo "❌ Error: Python 3 is required to run the backend."
  exit 1
fi

# 1. Automatic Python .venv setup
if [ ! -d "$PROJECT_DIR/.venv" ]; then
  echo "📦 Setting up Python virtual environment (.venv)..."
  $PYTHON_BIN -m venv "$PROJECT_DIR/.venv" || {
    echo "⚠️ standard venv creation failed; attempting with --without-pip..."
    $PYTHON_BIN -m venv --without-pip "$PROJECT_DIR/.venv"
  }
fi

VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
VENV_PIP="$PROJECT_DIR/.venv/bin/pip"

# Ensure pip is installed and requirements are up to date
if [ -f "$VENV_PIP" ]; then
  if [ ! -f "$PROJECT_DIR/.venv/.deps_installed" ]; then
    echo "📥 Installing Python backend dependencies (Flask, Pillow, google-genai, etc.)..."
    "$VENV_PIP" install -q --upgrade pip
    "$VENV_PIP" install -q -r "$PROJECT_DIR/backend/requirements.txt"
    touch "$PROJECT_DIR/.venv/.deps_installed"
    echo "✅ Python dependencies installed."
  fi
else
  echo "ℹ️ Using system python packages fallback..."
  VENV_PYTHON="$PYTHON_BIN"
fi

# 2. Automatic Node.js / Vite dependencies setup
if [ ! -d "$PROJECT_DIR/frontend/node_modules" ]; then
  echo "📦 Installing Frontend dependencies (React, Vite, Lucide icons)..."
  cd "$PROJECT_DIR/frontend"
  npm install
  cd "$PROJECT_DIR"
  echo "✅ Frontend dependencies installed."
fi

# Optional local Tesseract config
if [ -d "$PROJECT_DIR/../tools/tesseract/usr/lib/x86_64-linux-gnu" ]; then
  export LD_LIBRARY_PATH="$PROJECT_DIR/../tools/tesseract/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
  export TESSDATA_PREFIX="$PROJECT_DIR/../tools/tesseract/usr/share/tesseract-ocr/5/tessdata"
fi

# Function to stop background processes cleanly on Ctrl+C
cleanup() {
  echo ""
  echo "Shutting down servers..."
  kill $(jobs -p) 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 3. Start Flask API Backend
echo "🚀 Starting Flask API backend on http://127.0.0.1:5000..."
"$VENV_PYTHON" "$PROJECT_DIR/backend/app.py" &
FLASK_PID=$!

# Wait briefly for Flask
sleep 1.5

# 4. Start Vite React Frontend
echo "🚀 Starting Vite React frontend on http://localhost:5173..."
cd "$PROJECT_DIR/frontend"
npm run dev -- --host &
VITE_PID=$!

echo ""
echo "=================================================================="
echo " 🎉 HealthPulse is LIVE!"
echo " 👉 Web Interface: http://localhost:5173"
echo " 👉 Backend API:   http://localhost:5000"
echo " Press Ctrl+C to stop all servers."
echo "=================================================================="
echo ""

# Wait for both processes
wait $FLASK_PID $VITE_PID
