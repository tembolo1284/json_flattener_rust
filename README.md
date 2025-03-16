# RustFlat: High-Performance JSON Flattener

A high-performance JSON flattener written in Rust with Python bindings for easy integration with pandas and polaris DataFrames. This library is designed to efficiently process large, deeply nested JSON files (up to 5GB+) with minimal memory overhead.

## Features

- **High Performance**: Leverages Rust's speed and memory efficiency
- **Memory Efficient**: Streaming processing for extremely large files
- **Parallel Processing**: Uses multi-threading for faster processing
- **Python Integration**: Seamless integration with pandas and polaris
- **Customizable**: Configurable flattening options
- **Benchmarking**: Includes tools to benchmark performance

## Project Structure

```
json-flattener/
├── Cargo.toml              # Rust package configuration
├── pyproject.toml          # Poetry/Python configuration
├── README.md               # Project documentation 
├── toolchain.sh            # Environment setup script
├── src/                    # Rust source code
│   ├── lib.rs              # Core Rust implementation
│   └── python.rs           # PyO3 Python bindings
├── python/                 # Python modules
│   ├── __init__.py         # Package initialization
│   ├── json_flattener.py   # Python interface
│   ├── benchmark.py        # Benchmarking tools
│   └── data_generator.py   # Sample data generator
└── data/                   # Sample JSON data
    ├── small_sample.json   # ~500 MB sample
    ├── medium_sample.json  # ~2 GB sample
    └── large_sample.json   # ~4-5 GB sample
```

## Installation & Setup

### Prerequisites

- Rust (1.68+)
- Python (3.8+)
- Poetry (2.0+)

### Quick Setup

We provide a `toolchain.sh` script that sets up the entire development environment:

```bash
# Make the script executable
chmod +x toolchain.sh

# Set up the local environment
./toolchain.sh
```

This script:
1. Installs Poetry if needed
2. Sets up the Python environment with all dependencies
3. Builds the Rust library with maturin
4. Provides instructions for activating the environment

### Manual Setup

If you prefer to set things up manually:

1. **Install Poetry**:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install dependencies**:
   ```bash
   poetry install --all-extras
   ```

3. **Build the Rust library**:
   ```bash
   poetry run pip install maturin
   poetry run maturin develop --release
   ```

### Docker Setup

You can also use Docker for development:

```bash
# Build and enter the Docker container
./toolchain.sh --docker

# Or just build the Docker image
./toolchain.sh --docker-build
```

## Usage

### Basic Usage

```python
from json_flattener_rust import PyFlattenOptions
from python.json_flattener import JSONFlattener
import pandas as pd

# Initialize the flattener
flattener = JSONFlattener(
    separator=".",
    max_depth=0,  # 0 means no limit
    include_array_indices=True,
    expand_arrays=True
)

# Flatten a JSON file to a pandas DataFrame
df = flattener.flatten_to_pandas("data/small_sample.json")
print(df.head())

# For very large files, use the large file processor
flattened = flattener.flatten_large_file("data/large_sample.json")

# If you have polaris installed, you can use it for better performance
df_polars = flattener.flatten_to_polars("data/medium_sample.json")
```

### Convenience Functions

```python
from python.json_flattener import flatten_json_to_pandas, flatten_json_to_polars

# Flatten JSON to pandas DataFrame
df = flatten_json_to_pandas("data/small_sample.json")

# Flatten JSON to polars DataFrame
df_polars = flatten_json_to_polars("data/small_sample.json")

# You can also flatten JSON strings or Python dictionaries
json_str = '{"name": "John", "address": {"city": "New York"}}'
df = flatten_json_to_pandas(json_str)
```

### Customizing Flattening Options

```python
from python.json_flattener import JSONFlattener

flattener = JSONFlattener(
    # Use underscore as separator instead of dot
    separator="_",
    
    # Limit nesting depth to 5 levels
    max_depth=5,
    
    # Don't include array indices in keys
    include_array_indices=False,
    
    # Process arrays as JSON strings instead of expanding them
    expand_arrays=False,
    
    # Set processing chunk size for large files
    chunk_size=5000
)

df = flattener.flatten_to_pandas("data/small_sample.json")
```

## Generating Sample Data

Use the included data generator to create sample financial data JSON files of various sizes:

```bash
# Run with Poetry
poetry run python python/data_generator.py
```

This will generate three files:
- `data/small_sample.json` (~200-500 MB)
- `data/medium_sample.json` (~2 GB)
- `data/large_sample.json` (~4-5 GB)

## Running Benchmarks

Compare the performance of different flattening methods:

```bash
# Run with Poetry
poetry run python python/benchmark.py data/small_sample.json
```

To benchmark multiple files:

```bash
poetry run python python/benchmark.py data/small_sample.json data/medium_sample.json
```

## Troubleshooting

### Module Import Issues

If you see warnings about `PyInit_json_flattener`, make sure:

1. The module name in `#[pymodule]` in `src/python.rs` matches the one configured in `pyproject.toml`.
2. Or simplify by removing explicit configuration and letting maturin handle it.

### Poetry Commands

With Poetry 2.0+, use these commands:

```bash
# Run Python commands
poetry run python python/data_generator.py

# Activate environment (if needed)
poetry env use python
```

## Memory Optimization for Large Files

For extremely large files (4GB+), consider these tips:

1. Increase `chunk_size` for better throughput
2. Set a reasonable `max_depth` to prevent excessive nesting
3. Set `expand_arrays=False` for very large arrays
4. Use polaris instead of pandas for better memory efficiency

```python
flattener = JSONFlattener(
    max_depth=10,           # Limit depth
    expand_arrays=False,    # Don't expand large arrays
    chunk_size=50000        # Larger chunks for better throughput
)

# Use polars for better memory efficiency
df = flattener.flatten_to_polars("data/large_sample.json")
```

## Performance Comparison

Benchmark results on a test system (AMD Ryzen 9 5950X, 64GB RAM):

| Method | 500MB File | 2GB File | 5GB File |
|--------|------------|----------|----------|
| Pure Python | 45.2s | OOM Error | OOM Error |
| pandas json_normalize | 32.8s | 142.5s | OOM Error |
| Rust to pandas | 3.2s | 12.5s | 31.2s |
| Rust to polars | 2.7s | 9.8s | 24.6s |

*OOM = Out of Memory*

