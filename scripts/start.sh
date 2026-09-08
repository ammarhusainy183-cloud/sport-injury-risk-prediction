#!/usr/bin/env bash
# Start Flask app using venv Python (POSIX)
if [ -x "venv/bin/python" ]; then
  venv/bin/python app.py
else
  python3 app.py
fi
