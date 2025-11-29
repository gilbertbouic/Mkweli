#!/bin/bash
# =============================================================================
# Mkweli AML - Linux/Ubuntu Production Deployment Script
# Run without Docker using Gunicorn WSGI server
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration (can be overridden by environment variables)
PORT=${PORT:-8000}
WORKERS=${WORKERS:-4}
VENV_DIR="venv"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Mkweli AML - Production Server${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}[1/6] Checking Python version...${NC}"
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3.9 or higher"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"

# Create virtual environment if not exists
echo -e "${YELLOW}[2/6] Setting up virtual environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv $VENV_DIR
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
source $VENV_DIR/bin/activate

# Install dependencies
echo -e "${YELLOW}[3/6] Installing production dependencies...${NC}"
pip install --quiet --upgrade pip
if [ -f "requirements-prod.txt" ]; then
    pip install --quiet -r requirements-prod.txt
else
    pip install --quiet -r requirements.txt
    pip install --quiet gunicorn
fi
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Check for .env file
echo -e "${YELLOW}[4/6] Checking configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example${NC}"
        cp .env.example .env
        # Generate a random SECRET_KEY
        NEW_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        sed -i "s/your-secure-secret-key-here-change-me/$NEW_SECRET/g" .env
        echo -e "${GREEN}✓ Generated new SECRET_KEY${NC}"
    else
        echo -e "${YELLOW}Warning: No .env file found. Using defaults.${NC}"
    fi
else
    echo -e "${GREEN}✓ Configuration file found${NC}"
fi

# Load environment variables if .env exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs -d '\n' 2>/dev/null || true)
fi

# Create necessary directories
echo -e "${YELLOW}[5/6] Creating directories...${NC}"
mkdir -p instance uploads data
echo -e "${GREEN}✓ Directories ready${NC}"

# Check for sanctions data
echo -e "${YELLOW}[6/6] Checking sanctions data...${NC}"
DATA_FILES=("un_consolidated.xml" "uk_consolidated.xml" "ofac_consolidated.xml" "eu_consolidated.xml")
MISSING_FILES=0
for file in "${DATA_FILES[@]}"; do
    if [ ! -f "data/$file" ]; then
        echo -e "${YELLOW}  Warning: data/$file not found${NC}"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done
if [ $MISSING_FILES -eq 0 ]; then
    echo -e "${GREEN}✓ All sanctions data files present${NC}"
else
    echo -e "${YELLOW}Note: Some sanctions data files are missing.${NC}"
    echo -e "${YELLOW}      The application will start but screening may be limited.${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Starting Production Server${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Port:    ${GREEN}$PORT${NC}"
echo -e "Workers: ${GREEN}$WORKERS${NC}"
echo -e "URL:     ${GREEN}http://localhost:$PORT${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start Gunicorn
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers $WORKERS \
    --threads 2 \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --log-level info \
    app:app
