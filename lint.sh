#!/bin/bash

# Print commands being executed
set -x

# Exit on first error
set -e

# Run Ruff checks
echo "Running Ruff checks..."
ruff check .

# Run Ruff formatting
echo "Running Ruff formatting..."
ruff format .

echo "Linting completed successfully!" 