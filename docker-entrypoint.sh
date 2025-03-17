#!/bin/bash
set -e

# Install Python dependencies directly
pip install --no-cache-dir pandas polars pytest memory-profiler matplotlib tqdm faker pyarrow

# Build Rust library
cd /app
cargo build --release
maturin develop --release

echo "==> Environment is ready!"
echo "Available commands:"
echo "  python python/data_generator.py"
echo "  python python/benchmark.py data/small_sample.json"

# Execute the command
exec "$@"
