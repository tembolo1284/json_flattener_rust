# python/json_to_parquet.py
import os
import sys
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import argparse
from pathlib import Path

def convert_json_to_parquet(json_path, parquet_path=None, compression='snappy'):
    """
    Convert a JSON file to Parquet format with compression.
    
    Args:
        json_path (str): Path to the JSON file
        parquet_path (str, optional): Output path for Parquet file. If None, replaces .json with .parquet
        compression (str, optional): Compression codec ('snappy', 'gzip', 'brotli', or 'zstd')
    
    Returns:
        tuple: (original_size_mb, new_size_mb, compression_ratio)
    """
    print(f"Processing {json_path}...")
    
    # Determine output path if not specified
    if parquet_path is None:
        parquet_path = str(Path(json_path).with_suffix('.parquet'))
    
    # Load JSON data
    print("Loading JSON data...")
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Convert to DataFrame
    print("Converting to DataFrame...")
    df = pd.json_normalize(data, sep='.')
    
    # Convert to parquet
    print(f"Writing Parquet file with {compression} compression...")
    df.to_parquet(parquet_path, compression=compression)
    
    # Calculate size reduction
    original_size = os.path.getsize(json_path) / (1024 * 1024)  # MB
    new_size = os.path.getsize(parquet_path) / (1024 * 1024)  # MB
    compression_ratio = original_size / new_size if new_size > 0 else float('inf')
    
    print(f"Original size: {original_size:.2f} MB")
    print(f"Parquet size: {new_size:.2f} MB")
    print(f"Compression ratio: {compression_ratio:.2f}x")
    
    return (original_size, new_size, compression_ratio)

def main():
    parser = argparse.ArgumentParser(description='Convert JSON files to compressed Parquet format')
    parser.add_argument('files', nargs='+', help='JSON files to convert')
    parser.add_argument('--compression', '-c', choices=['snappy', 'gzip', 'brotli', 'zstd'], 
                        default='snappy', help='Compression codec to use')
    parser.add_argument('--output-dir', '-o', help='Output directory (default: same as input)')
    
    args = parser.parse_args()
    
    results = []
    
    for json_file in args.files:
        if not os.path.exists(json_file):
            print(f"File not found: {json_file}")
            continue
            
        if args.output_dir:
            os.makedirs(args.output_dir, exist_ok=True)
            filename = os.path.basename(json_file)
            parquet_path = os.path.join(args.output_dir, 
                                       filename.replace('.json', '.parquet'))
        else:
            parquet_path = None
            
        try:
            result = convert_json_to_parquet(json_file, parquet_path, args.compression)
            results.append((json_file, *result))
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    # Print summary
    if results:
        print("\nSummary:")
        print(f"{'File':<30} {'Original (MB)':<15} {'Parquet (MB)':<15} {'Ratio':<10}")
        print('-' * 70)
        for filename, orig_size, new_size, ratio in results:
            print(f"{os.path.basename(filename):<30} {orig_size:<15.2f} {new_size:<15.2f} {ratio:<10.2f}x")

if __name__ == "__main__":
    main()
