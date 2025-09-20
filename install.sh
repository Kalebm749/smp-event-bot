#!/bin/bash

# Exit on error
set -e

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install mcrcon discord.py pytz python-dotenv

# Freeze requirements
echo "Freezing requirements..."
pip freeze > requirements.txt

echo "Setup complete! Use 'source venv/bin/activate' to activate your environment."
