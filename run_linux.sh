#!/bin/bash
if [ ! -d "venv" ]; then
  echo "Creating venv..."
  python3 -m venv venv
fi
source venv/bin/activate
python install_dependencies.py  # Auto-install deps if missing
python app.py
