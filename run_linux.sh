#!/bin/bash
# ==============================================================================
# MkweliAML - Run Script for Linux/macOS
# ==============================================================================
# This script handles first-time setup and auto-startup of MkweliAML.
# Simply run: bash run_linux.sh (or ./run_linux.sh after chmod +x)
# ==============================================================================

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "  MkweliAML - Sanctions Screening System     "
echo "=============================================="

# 1. Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "   Please install Python 3.8+ from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python $PYTHON_VERSION detected"

# 2. Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "→ Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# 3. Activate virtual environment
echo "→ Activating virtual environment..."
source venv/bin/activate

# 4. Install/upgrade dependencies
echo "→ Checking dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# 5. Create data folder if it doesn't exist
if [ ! -d "data" ]; then
    echo "→ Creating data folder..."
    mkdir -p data
fi

# 6. Check for sanctions XML files
XML_COUNT=$(find data -name "*.xml" 2>/dev/null | wc -l)
if [ "$XML_COUNT" -eq "0" ]; then
    echo ""
    echo "⚠️  No sanctions XML files found in data/ folder!"
    echo "   Download the following files and place them in data/:"
    echo ""
    echo "   1. UN Consolidated List → Rename to: un_consolidated.xml"
    echo "      https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list"
    echo ""
    echo "   2. UK Sanctions List → Rename to: uk_consolidated.xml"
    echo "      https://www.gov.uk/government/publications/the-uk-sanctions-list"
    echo ""
    echo "   3. OFAC SDN List → Rename to: ofac_consolidated.xml"
    echo "      https://sanctionslist.ofac.treas.gov/Home/SdnList"
    echo ""
    echo "   4. EU Consolidated List → Rename to: eu_consolidated.xml"
    echo "      https://www.sanctionsmap.eu"
    echo ""
    echo "   The app will start but screening requires these files."
    echo ""
else
    echo "✓ Found $XML_COUNT sanctions XML file(s) in data/"
fi

# 7. Initialize database if needed
if [ ! -f "instance/mkweli.db" ]; then
    echo "→ Database will be initialized on first run"
fi

# 8. Start the application
echo ""
echo "=============================================="
echo "  Starting MkweliAML..."
echo "=============================================="
echo "  📍 URL: http://localhost:5000"
echo "  🔑 Password: admin123 (change after login)"
echo "  ⏹  Press Ctrl+C to stop"
echo "=============================================="
echo ""

python3 app.py
