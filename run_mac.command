#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "========================================"
echo " India Momentum & EMA Crossover Scanner"
echo "========================================"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed. Install Python 3.10+ from https://www.python.org/downloads/macos/"
  read -p "Press Enter to close..."
  exit 1
fi
python3 - <<'PY'
import sys
if sys.version_info < (3,10):
    print("Python 3.10 or later is required.")
    raise SystemExit(1)
PY
if [ ! -d ".venv" ]; then
  echo "Creating the app's private Python environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate
echo "Installing / updating required packages..."
python -m pip install --upgrade pip
python -m pip install -r requirements-local.txt
echo "Opening the scanner in your browser..."
python -m streamlit run streamlit_app.py
