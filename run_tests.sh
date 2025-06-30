#!/bin/bash
# Simple script to run tests for csvdiffgpt

# Set up virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install package in development mode with all dependencies
echo "Installing package and dependencies..."
pip install -e ".[dev,all]"

# Run tests
echo "Running tests..."
pytest -v tests/

# Run with coverage
echo "Running tests with coverage..."
pytest --cov=csvdiffgpt --cov-report=term-missing tests/

# Deactivate virtual environment
deactivate

echo "Tests completed!"