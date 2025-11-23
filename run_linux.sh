#!/bin/bash
if [ ! -d "venv" ]; then
  echo "Creating venv..."
  python3 -m venv venv
fi
source venv/bin/activate
python install_dependencies.py  # Auto-install deps if missing
python app.py
=======
# MkweliAML Linux/Mac Runner

# Activate venv if exists
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

python3 app.py

