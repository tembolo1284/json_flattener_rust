import json
import os
import time
from typing import Dict, List, Any, Optional, Union
import pandas as pd

try:
    import polars as pl
    HAS_POLARS = True
except ImportError:
    HAS_POLARS = False

# Import our Rust library
from json_flattener_rust import (
    flatten_json_str,
    flatten_json_file_py,
    process_large_json_file,
    flatten_pandas_ready,
    flatten_polaris_ready,
    PyFlattenOptions
)

class JSONFlattener:
    """A high-performance JSON flattener using Rust"""
    
    def __init__(
        self,
        separator: str = ".",
        max_concurrency: Optional[int] = None,
        max_depth: int = 0,
        include_array_indices: bool = True,
        expand_arrays: bool = True,
        chunk_size: int = 10000,
        prefer_polars: bool = True
    ):
        """Initialize the JSON flattener with the given options"""
        self.options = PyFlattenOptions(
            separator=separator,
            max_concurrency=max_concurrency,
            max_depth=max_depth,
            include_array_indices=include_array_indices,
            expand_arrays=expand_arrays,
            chunk_size=chunk_size
        )
        self.prefer_polars = prefer_polars and HAS_POLARS
    
    def flatten_json(self, json_data: Union[str, Dict, List]) -> Dict[str, str]:
        """Flatten a JSON object into a dictionary with dot-notation keys"""
        if isinstance(json_data, (dict, list)):
            json_str = json.dumps(json_data)
        elif isinstance(json_data, str):
            json_str = json_data
        else:
            raise ValueError("Input must be a JSON string, dict, or list")
        
        return flatten_json_str(json_str, self.options)
    
    def flatten_file(self, filepath: str) -> List[Dict[str, str]]:
        """Flatten a JSON file into a list of dictionaries"""
        if filepath.endswith('.parquet'):
            # For parquet files, we read them and convert to dict
            if self.prefer_polars and HAS_POLARS:
                df = pl.read_parquet(filepath)
                return df.to_dicts()
            else:
                df = pd.read_parquet(filepath)
                return df.to_dict(orient='records')
        else:
            return flatten_json_file_py(filepath, self.options)
    
    def flatten_large_file(self, filepath: str) -> Dict[str, str]:
        """Process a large JSON file optimized for memory efficiency"""
        if filepath.endswith('.parquet'):
            # For parquet files, we read them and convert to dict
            if self.prefer_polars and HAS_POLARS:
                df = pl.read_parquet(filepath)
                # For large files we just return the first row as a dict
                # as this is what process_large_json_file does for JSON
                return df.to_dicts()[0] if len(df) > 0 else {}
            else:
                df = pd.read_parquet(filepath)
                return df.iloc[0].to_dict() if len(df) > 0 else {}
        else:
            return process_large_json_file(filepath, self.options)
    
    def flatten_to_pandas(self, filepath: str) -> pd.DataFrame:
        """Flatten a file and convert it to a pandas DataFrame"""
        if filepath.endswith('.parquet'):
            return pd.read_parquet(filepath)
        else:
            data = flatten_pandas_ready(filepath, self.options)
            return pd.DataFrame(data)
    
    def flatten_to_polars(self, filepath: str) -> Union[pl.DataFrame, None]:
        """Flatten a file and convert it to a polars DataFrame"""
        if not HAS_POLARS:
            raise ImportError("Polars is not installed. Please install it with 'pip install polars'.")
        
        if filepath.endswith('.parquet'):
            return pl.read_parquet(filepath)
        else:
            data = flatten_polaris_ready(filepath, self.options)
            return pl.DataFrame(data)
    
    def flatten_to_dataframe(self, filepath: str) -> Union[pl.DataFrame, pd.DataFrame]:
        """Flatten a file and convert it to the preferred DataFrame type"""
        if self.prefer_polars and HAS_POLARS:
            return self.flatten_to_polars(filepath)
        else:
            return self.flatten_to_pandas(filepath)
    
    def benchmark(self, filepath: str) -> Dict[str, float]:
        """Benchmark flattening performance on a file"""
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        is_parquet = filepath.endswith('.parquet')
        
        # Benchmark pandas conversion
        start_time = time.time()
        df_pandas = self.flatten_to_pandas(filepath)
        pandas_time = time.time() - start_time
        pandas_rows = len(df_pandas)
        pandas_cols = len(df_pandas.columns)
        
        # Benchmark polars conversion if available
        if HAS_POLARS:
            start_time = time.time()
            df_polars = self.flatten_to_polars(filepath)
            polars_time = time.time() - start_time
            polars_rows = len(df_polars)
            polars_cols = len(df_polars.columns)
        else:
            polars_time = None
            polars_rows = None
            polars_cols = None
        
        return {
            "file_size_mb": file_size_mb,
            "file_type": "parquet" if is_parquet else "json",
            "pandas_time_seconds": pandas_time,
            "pandas_rows": pandas_rows,
            "pandas_cols": pandas_cols,
            "polars_time_seconds": polars_time,
            "polars_rows": polars_rows,
            "polars_cols": polars_cols,
            "pandas_mb_per_second": file_size_mb / pandas_time if pandas_time > 0 else float('inf'),
            "polars_mb_per_second": file_size_mb / polars_time if polars_time and polars_time > 0 else None
        }


def flatten_json_to_pandas(
    json_data: Union[str, Dict, List, str],
    separator: str = ".",
    max_depth: int = 0,
    expand_arrays: bool = True
) -> pd.DataFrame:
    """Convenience function to flatten JSON and convert to pandas DataFrame"""
    flattener = JSONFlattener(
        separator=separator,
        max_depth=max_depth,
        expand_arrays=expand_arrays,
        prefer_polars=False
    )
    
    if isinstance(json_data, str) and os.path.isfile(json_data):
        # If input is a file path
        return flattener.flatten_to_pandas(json_data)
    else:
        # If input is a JSON object or string
        flat_json = flattener.flatten_json(json_data)
        return pd.DataFrame([flat_json])


def flatten_json_to_polars(
    json_data: Union[str, Dict, List, str],
    separator: str = ".",
    max_depth: int = 0,
    expand_arrays: bool = True
) -> Union[pl.DataFrame, None]:
    """Convenience function to flatten JSON and convert to polars DataFrame"""
    if not HAS_POLARS:
        raise ImportError("Polars is not installed. Please install it with 'pip install polars'.")
    
    flattener = JSONFlattener(
        separator=separator,
        max_depth=max_depth,
        expand_arrays=expand_arrays,
        prefer_polars=True
    )
    
    if isinstance(json_data, str) and os.path.isfile(json_data):
        # If input is a file path
        return flattener.flatten_to_polars(json_data)
    else:
        # If input is a JSON object or string
        flat_json = flattener.flatten_json(json_data)
        return pl.DataFrame([flat_json])


def flatten_json_to_dataframe(
    json_data: Union[str, Dict, List, str],
    separator: str = ".",
    max_depth: int = 0,
    expand_arrays: bool = True,
    prefer_polars: bool = True
) -> Union[pl.DataFrame, pd.DataFrame]:
    """Convenience function to flatten JSON to preferred DataFrame type"""
    if prefer_polars and HAS_POLARS:
        return flatten_json_to_polars(json_data, separator, max_depth, expand_arrays)
    else:
        return flatten_json_to_pandas(json_data, separator, max_depth, expand_arrays)
