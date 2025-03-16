#!/bin/bash
set -e

# Activate virtual environment
source /app/venv/bin/activate

# Print welcome message
echo -e "\033[1;32m==>\033[0m \033[1mJSON Flattener Development Environment\033[0m"
echo -e "\033[1;32m==>\033[0m \033[1mRust is built and Python environment is ready!\033[0m"
echo ""
echo "Available commands:"
echo "  python python/data_generator.py           # Generate sample JSON files"
echo "  python python/benchmark.py data/*.json    # Run benchmarks"
echo ""

# Execute the command passed to docker run
exec "$@"
