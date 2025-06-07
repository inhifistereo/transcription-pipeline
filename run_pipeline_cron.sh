#!/bin/bash
# Usage: Set required environment variables in the .env file in this directory.

# Source the .env file (if it exists)
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Change to the project directory (defaults to the directory containing this script)
cd "$(dirname "$0")"

# Run the pipeline
python3 run_pipeline.py
