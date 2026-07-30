#!/bin/bash
# =============================================================================
# Customer Pain Research Agent — Mac double-click launcher
# Double-click this file in Finder to open the web UI in your browser.
# =============================================================================

set -e
cd "$(dirname "$0")"

echo ""
echo "=============================================="
echo "  Customer Pain Research Agent"
echo "  Starting the web UI…"
echo "=============================================="
echo ""

# Prefer python3
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found."
  echo "Install Python 3.12+ from https://www.python.org/downloads/"
  echo "Then double-click this file again."
  read -r -p "Press Enter to close…"
  exit 1
fi

# Create venv if missing
if [ ! -d ".venv" ]; then
  echo "First run: creating virtual environment (.venv)…"
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing / updating dependencies (may take a minute the first time)…"
python -m pip install --upgrade pip -q
pip install -q -r requirements.txt

# Create .env from example if missing (user can fill keys in the UI)
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "Created .env — you can paste API keys in the web UI sidebar."
fi

echo ""
echo "Opening browser at http://localhost:8501"
echo "Leave this window open while you use the app."
echo "Press Ctrl+C here to stop the server."
echo ""

# Open browser shortly after Streamlit starts
(sleep 2 && open "http://localhost:8501") &

exec streamlit run app.py \
  --server.headless true \
  --browser.gatherUsageStats false \
  --server.port 8501
