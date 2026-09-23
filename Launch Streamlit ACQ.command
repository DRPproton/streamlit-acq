#!/bin/zsh

set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "$APP_DIR/app.py" ]; then
  APP_DIR="/Users/dashelruizperez/PycharmProjects/Streamlit-ACQ"
fi

if [ ! -f "$APP_DIR/app.py" ]; then
  echo "Could not find app.py."
  echo "Keep this launcher in the Streamlit-ACQ folder, or update APP_DIR inside this file."
  echo
  read "reply?Press Enter to close this window."
  exit 1
fi

cd "$APP_DIR"

echo "Starting Baseline ACQ file extractor..."
echo "Project: $APP_DIR"
echo

if command -v uv >/dev/null 2>&1; then
  uv run streamlit run app.py
elif [ -x "$APP_DIR/.venv/bin/python" ]; then
  "$APP_DIR/.venv/bin/python" -m streamlit run app.py
elif command -v python3 >/dev/null 2>&1; then
  python3 -m streamlit run app.py
else
  echo "Python was not found."
  echo "Install Python or uv, then run this launcher again."
  echo
  read "reply?Press Enter to close this window."
fi
