#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

SSL_MODE=false
SSL_FLAG=""

if [ "$1" == "--ssl" ] || [ "$1" == "--https" ]; then
  SSL_MODE=true
  SSL_FLAG="--ssl"
fi

echo "=================================================================="
if [ "$SSL_MODE" = true ]; then
  echo " 🔒 Starting HealthPulse with SSL / HTTPS (Port 5000)            "
else
  echo " 🚀 Starting HealthPulse (HTTP Mode - Port 5000)                  "
fi
echo "=================================================================="

# Ensure previous stale processes on ports 5000 and 5173 are stopped cleanly
pkill -f "$PROJECT_DIR/backend/app.py" 2>/dev/null || true
fuser -k 5000/tcp 2>/dev/null || true
fuser -k 5173/tcp 2>/dev/null || true
sleep 0.5

# Check for Node.js / npm
if ! command -v node &> /dev/null; then
  if [ -d "$PROJECT_DIR/../tools/nodejs/bin" ]; then
    export PATH="$PROJECT_DIR/../tools/nodejs/bin:$PATH"
  elif [ -d "$HOME/.nvm/versions/node" ]; then
    NODE_LATEST=$(find "$HOME/.nvm/versions/node" -maxdepth 2 -name "bin" 2>/dev/null | tail -n 1)
    [ -n "$NODE_LATEST" ] && export PATH="$NODE_LATEST:$PATH"
  fi
fi

if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
  echo "❌ Error: Node.js and npm are required to run the frontend."
  echo "Please install Node.js (https://nodejs.org)."
  exit 1
fi

# Check for Python 3
PYTHON_BIN="python3"
if ! command -v python3 &> /dev/null; then
  PYTHON_BIN="python"
fi

# 1. Automatic Python .venv setup
if [ ! -d "$PROJECT_DIR/.venv" ]; then
  echo "📦 Setting up Python virtual environment (.venv)..."
  $PYTHON_BIN -m venv "$PROJECT_DIR/.venv" || {
    $PYTHON_BIN -m venv --without-pip "$PROJECT_DIR/.venv"
  }
fi

VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
VENV_PIP="$PROJECT_DIR/.venv/bin/pip"

# Ensure pip is installed and requirements are up to date
if [ -f "$VENV_PIP" ]; then
  if [ ! -f "$PROJECT_DIR/.venv/.deps_installed_v2" ]; then
    echo "📥 Installing Python dependencies (Flask, pyjwt, cryptography, google-genai)..."
    "$VENV_PIP" install -q --upgrade pip
    "$VENV_PIP" install -q -r "$PROJECT_DIR/backend/requirements.txt"
    touch "$PROJECT_DIR/.venv/.deps_installed_v2"
    echo "✅ Python dependencies installed."
  fi
else
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

# Check SSL certs (Auto-generate self-signed cert if missing)
if [ ! -f "$PROJECT_DIR/certs/cert.pem" ]; then
  echo "🔒 Generating local development SSL certificates for WebAuthn / Passkeys..."
  "$VENV_PYTHON" "$PROJECT_DIR/backend/ssl_manager.py"
fi

# Function to stop background processes cleanly on Ctrl+C
cleanup() {
  echo ""
  echo "Shutting down servers..."
  kill $(jobs -p) 2>/dev/null || true
  pkill -f "$PROJECT_DIR/backend/app.py" 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 3. Start Flask API Backend
if [ "$SSL_MODE" = true ]; then
  echo "🔒 Starting Flask API backend on https://127.0.0.1:5000..."
  "$VENV_PYTHON" "$PROJECT_DIR/backend/app.py" --ssl &
  FLASK_PID=$!
else
  echo "🚀 Starting Flask API backend on http://127.0.0.1:5000..."
  "$VENV_PYTHON" "$PROJECT_DIR/backend/app.py" &
  FLASK_PID=$!
fi

# Wait briefly for Flask to bind port 5000
sleep 1.5

# 4. Start Vite React Frontend
echo "🚀 Starting Vite React frontend on http://localhost:5173..."
cd "$PROJECT_DIR/frontend"
npm run dev -- --host &
VITE_PID=$!

echo ""
echo "=================================================================="
echo " 🎉 HealthPulse is LIVE!"
echo " 👉 Web App:     http://localhost:5173"
if [ "$SSL_MODE" = true ]; then
  echo " 👉 Backend API: https://localhost:5000 (SSL Active)"
else
  echo " 👉 Backend API: http://localhost:5000"
  echo " 💡 Tip: Run './run.sh --ssl' to start with HTTPS / SSL"
fi
echo " Press Ctrl+C to stop all servers."
echo "=================================================================="
echo ""

# Wait for both processes
wait $FLASK_PID $VITE_PID
