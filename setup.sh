#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "=================================================================="
echo " Setting up HealthPulse Environment (Python .venv + Node Modules)"
echo "=================================================================="

# 1. Setup Python Virtual Environment
echo "-> Checking Python 3..."
PYTHON_BIN="python3"
if ! command -v python3 &> /dev/null; then
  PYTHON_BIN="python"
fi

if [ ! -d "$PROJECT_DIR/.venv" ]; then
  echo "-> Creating virtual environment in .venv..."
  $PYTHON_BIN -m venv "$PROJECT_DIR/.venv"
fi

echo "-> Installing backend Python packages from requirements.txt..."
"$PROJECT_DIR/.venv/bin/pip" install --upgrade pip
"$PROJECT_DIR/.venv/bin/pip" install -r "$PROJECT_DIR/backend/requirements.txt"
touch "$PROJECT_DIR/.venv/.deps_installed"
echo "✅ Python backend setup complete."

# 2. Setup Node / Frontend Packages
echo "-> Checking Node & npm..."
if ! command -v npm &> /dev/null; then
  if [ -d "$PROJECT_DIR/../tools/nodejs/bin" ]; then
    export PATH="$PROJECT_DIR/../tools/nodejs/bin:$PATH"
  fi
fi

echo "-> Installing frontend packages (React, Vite, Lucide icons)..."
cd "$PROJECT_DIR/frontend"
npm install
cd "$PROJECT_DIR"
echo "✅ Frontend React setup complete."

echo ""
echo "=================================================================="
echo " Setup successfully finished!"
echo " Start the application anytime by running: ./run.sh"
echo "=================================================================="
