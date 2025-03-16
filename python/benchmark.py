import os
import time
import json
import argparse
import pandas as pd
from memory_profiler import memory_usage
from json_flattener import JSONFlattener

try:
    import polars as pl
    HAS_POLARS = True
except ImportError:
    HAS_POLARS = False

def format_size(size_bytes):
    """Format file size in a human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0 or unit == 'TB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

def profile_memory(func, *args, **kwargs):
    """Profile memory usage of a function"""
    mem_usage, result = memory_usage(
        (func, args, kwargs),
        retval=True,
        interval=0.1,
        timeout=None
    )
    return max(mem_usage) - min(mem_usage), result

def benchmark_pure_python(filepath):
    """Benchmark flattening JSON using pure Python"""
    
    def flatten_json_python(d, parent_key='', sep='.'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_json_python(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(flatten_json_python(item, f"{new_key}{sep}{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}{sep}{i}", str(item)))
            else:
                items.append((new_key, str(v)))
        return dict(items)
    
    def process_with_python():
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return [flatten_json_python(item) for item in data]
        else:
            return flatten_json_python(data)
    
    start_time = time.time()
    mem_usage, result = profile_memory(process_with_python)
    elapsed_time = time.time() - start_time
    
    return {
        "method": "Pure Python",
        "time_seconds": elapsed_time,
        "memory_mb": mem_usage,
        "result_type": type(result).__name__,
        "result_size": len(result) if isinstance(result, list) else 1
    }

def benchmark_pandas_json_normalize(filepath):
    """Benchmark flattening JSON using pandas json_normalize"""
    
    def process_with_pandas():
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return pd.json_normalize(data)
        else:
            return pd.json_normalize([data])
    
    start_time = time.time()
    mem_usage, df = profile_memory(process_with_pandas)
    elapsed_time = time.time() - start_time
    
    return {
        "method": "pandas json_normalize",
        "time_seconds": elapsed_time,
        "memory_mb": mem_usage,
        "result_type": "DataFrame",
        "rows": len(df),
        "columns": len(df.columns)
    }

def benchmark_rust_flattener(filepath):
    """Benchmark flattening JSON using our Rust implementation"""
    flattener = JSONFlattener()
    
    # Benchmark to pandas
    start_time = time.time()
    mem_usage, df_pandas = profile_memory(flattener.flatten_to_pandas, filepath)
    pandas_time = time.time() - start_time
    
    results = [{
        "method": "Rust to pandas",
        "time_seconds": pandas_time,
        "memory_mb": mem_usage,
        "result_type": "DataFrame",
        "rows": len(df_pandas),
        "columns": len(df_pandas.columns)
    }]
    
    # Benchmark to polars if available
    if HAS_POLARS:
        start_time = time.time()
        mem_usage, df_polars = profile_memory(flattener.flatten_to_polars, filepath)
        polars_time = time.time() - start_time
        
        results.append({
            "method": "Rust to polars",
            "time_seconds": polars_time,
            "memory_mb": mem_usage,
            "result_type": "DataFrame",
            "rows": len(df_polars),
            "columns": len(df_polars.columns)
        })
    
    return results

def run_benchmark(filepath):
    """Run all benchmarks on a file"""
    file_size = os.path.getsize(filepath)
    print(f"Benchmarking file: {filepath} ({format_size(file_size)})")
    
    results = []
    
    # Only run pure Python benchmark on small files
    if file_size < 100 * 1024 * 1024:  # 100 MB
        try:
            result = benchmark_pure_python(filepath)
            results.append(result)
            print(f"Pure Python: {result['time_seconds']:.2f} seconds, {result['memory_mb']:.2f} MB")
        except Exception as e:
            print(f"Pure Python benchmark failed: {e}")
    
    # Only run pandas json_normalize on small files
    if file_size < 500 * 1024 * 1024:  # 500 MB
        try:
            result = benchmark_pandas_json_normalize(filepath)
            results.append(result)
            print(f"pandas json_normalize: {result['time_seconds']:.2f} seconds, {result['memory_mb']:.2f} MB")
        except Exception as e:
            print(f"pandas json_normalize benchmark failed: {e}")
    
    # Run Rust implementation benchmarks
    try:
        rust_results = benchmark_rust_flattener(filepath)
        results.extend(rust_results)
        for result in rust_results:
            print(f"{result['method']}: {result['time_seconds']:.2f} seconds, {result['memory_mb']:.2f} MB")
    except Exception as e:
        print(f"Rust flattener benchmark failed: {e}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Benchmark JSON flattening')
    parser.add_argument('files', metavar='FILE', type=str, nargs='+',
                        help='JSON files to benchmark')
    parser.add_argument('--output', type=str, default='benchmark_results.csv',
                        help='Output CSV file for results')
    
    args = parser.parse_args()
    
    all_results = []
    
    for filepath in args.files:
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
        
        results = run_benchmark(filepath)
        
        for result in results:
            result['file'] = os.path.basename(filepath)
            result['file_size_mb'] = os.path.getsize(filepath) / (1024 * 1024)
            all_results.append(result)
        
        print()
    
    # Save results to CSV
    df_results = pd.DataFrame(all_results)
    df_results.to_csv(args.output, index=False)
    print(f"Results saved to {args.output}")
    
    # Print summary
    print("\nSummary:")
    for file_group in df_results.groupby('file'):
        file_name = file_group[0]
        file_df = file_group[1]
        print(f"\n{file_name}:")
        
        for _, row in file_df.iterrows():
            throughput = row['file_size_mb'] / row['time_seconds']
            print(f"  {row['method']}: {row['time_seconds']:.2f} seconds ({throughput:.2f} MB/s)")

if __name__ == "__main__":
    main()
