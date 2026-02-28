#!/bin/bash

# IG-Detective Launch Script
# Created by @shredzwho

# Ensure we are in the project root
cd "$(dirname "$0")"

# Colors for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}[*] Initializing IG-Detective Environment...${NC}"

# Define potential venv locations
VENV_DIRS=("venv" ".venv")
PYTHON_EXEC=""

for dir in "${VENV_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
            PYTHON_EXEC="$dir/Scripts/python.exe"
        else
            PYTHON_EXEC="$dir/bin/python3"
        fi
        break
    fi
done

if [ -z "$PYTHON_EXEC" ]; then
    echo -e "${RED}[!] Virtual environment not found!${NC}"
    echo "Please set up the environment first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Run the detective tool
echo -e "${GREEN}[*] Launching Interactive Shell...${NC}"
$PYTHON_EXEC main.py "$@"
