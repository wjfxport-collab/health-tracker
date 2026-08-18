#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

export PATH="$PROJECT_DIR/../tools/nodejs/bin:$PROJECT_DIR/frontend/node_modules/.bin:$PATH"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"

# Terminal formatting
GREEN="\033[92m"
RED="\033[91m"
CYAN="\033[96m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "\n${CYAN}${BOLD}==================================================================${RESET}"
echo -e "${CYAN}${BOLD}           HealthPulse Unified Regression Test Suite              ${RESET}"
echo -e "${CYAN}${BOLD}==================================================================${RESET}\n"

RUN_BACKEND=false
RUN_FRONTEND=false
RUN_API=false

if [ "$1" == "--backend" ]; then
  RUN_BACKEND=true
elif [ "$1" == "--frontend" ]; then
  RUN_FRONTEND=true
elif [ "$1" == "--api" ]; then
  RUN_API=true
else
  # Default to running all test suites
  RUN_BACKEND=true
  RUN_FRONTEND=true
  RUN_API=true
fi

FAILED=0

# --- 1. Python Backend Pytest Suite ---
if [ "$RUN_BACKEND" = true ]; then
  echo -e "${CYAN}${BOLD}▶ [1/3] Running Python Backend Pytest Regression Suite...${RESET}"
  if "$VENV_PYTHON" -m pytest "$PROJECT_DIR/backend/tests" -v; then
    echo -e "${GREEN}✔ Backend Pytest tests passed successfully!${RESET}\n"
  else
    echo -e "${RED}✘ Backend Pytest tests failed!${RESET}\n"
    FAILED=$((FAILED + 1))
  fi
fi

# --- 2. React Frontend Vitest Suite ---
if [ "$RUN_FRONTEND" = true ]; then
  echo -e "${CYAN}${BOLD}▶ [2/3] Running React Frontend Vitest Regression Suite...${RESET}"
  cd "$PROJECT_DIR/frontend"
  if npx vitest run; then
    echo -e "${GREEN}✔ Frontend Vitest tests passed successfully!${RESET}\n"
  else
    echo -e "${RED}✘ Frontend Vitest tests failed!${RESET}\n"
    FAILED=$((FAILED + 1))
  fi
  cd "$PROJECT_DIR"
fi

# --- 3. JSON REST API Regression Runner ---
if [ "$RUN_API" = true ]; then
  echo -e "${CYAN}${BOLD}▶ [3/3] Running Live JSON REST API Regression Suite...${RESET}"
  
  TEST_PORT=5099
  fuser -k ${TEST_PORT}/tcp 2>/dev/null || true
  sleep 0.5

  # Start temporary test server on dedicated isolated port
  PORT=${TEST_PORT} "$VENV_PYTHON" "$PROJECT_DIR/backend/app.py" &
  SERVER_PID=$!

  cleanup_server() {
    kill $SERVER_PID 2>/dev/null || true
    fuser -k ${TEST_PORT}/tcp 2>/dev/null || true
  }
  trap cleanup_server EXIT

  if "$VENV_PYTHON" "$PROJECT_DIR/backend/tests/api_regression_runner.py" --base-url "http://127.0.0.1:${TEST_PORT}"; then
    echo -e "${GREEN}✔ JSON REST API regression tests passed successfully!${RESET}\n"
  else
    echo -e "${RED}✘ JSON REST API regression tests failed!${RESET}\n"
    FAILED=$((FAILED + 1))
  fi

  cleanup_server
fi

# --- Final Summary ---
echo -e "${CYAN}${BOLD}==================================================================${RESET}"
if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}${BOLD} 🎉 ALL REGRESSION TEST SUITES PASSED WITH 100% SUCCESS!${RESET}"
else
  echo -e "${RED}${BOLD} ❌ $FAILED TEST SUITE(S) FAILED. CHECK OUTPUT ABOVE.${RESET}"
fi
echo -e "${CYAN}${BOLD}==================================================================${RESET}\n"

exit $FAILED
