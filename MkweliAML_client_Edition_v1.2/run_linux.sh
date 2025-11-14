#!/bin/bash
# MkweliAML Linux/Mac Runner

# Activate venv if exists
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

python3 app.py
