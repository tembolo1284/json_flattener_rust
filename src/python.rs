// src/python.rs
use crate::{flatten_json, flatten_json_file, process_large_json_object, FlattenOptions, FlattenedJson};
use pyo3::exceptions::{PyIOError, PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use serde_json::Value;
use std::collections::HashMap;

/// A high-performance JSON flattener
#[pymodule]
fn json_flattener_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyFlattenOptions>()?;
    m.add_function(wrap_pyfunction!(flatten_json_str, m)?)?;
    m.add_function(wrap_pyfunction!(flatten_json_file_py, m)?)?;
    m.add_function(wrap_pyfunction!(process_large_json_file, m)?)?;
    m.add_function(wrap_pyfunction!(flatten_pandas_ready, m)?)?;
    m.add_function(wrap_pyfunction!(flatten_polaris_ready, m)?)?;
    Ok(())
}

/// Options for controlling the JSON flattening process
#[pyclass]
#[derive(Clone)]
struct PyFlattenOptions {
    #[pyo3(get, set)]
    separator: String,
    #[pyo3(get, set)]
    max_concurrency: usize,
    #[pyo3(get, set)]
    max_depth: usize,
    #[pyo3(get, set)]
    include_array_indices: bool,
    #[pyo3(get, set)]
    expand_arrays: bool,
    #[pyo3(get, set)]
    chunk_size: usize,
}

#[pymethods]
impl PyFlattenOptions {
    #[new]
    fn new(
        separator: Option<String>,
        max_concurrency: Option<usize>,
        max_depth: Option<usize>,
        include_array_indices: Option<bool>,
        expand_arrays: Option<bool>,
        chunk_size: Option<usize>,
    ) -> Self {
        let default_options = FlattenOptions::default();
        PyFlattenOptions {
            separator: separator.unwrap_or(default_options.separator),
            max_concurrency: max_concurrency.unwrap_or(default_options.max_concurrency),
            max_depth: max_depth.unwrap_or(default_options.max_depth),
            include_array_indices: include_array_indices.unwrap_or(default_options.include_array_indices),
            expand_arrays: expand_arrays.unwrap_or(default_options.expand_arrays),
            chunk_size: chunk_size.unwrap_or(default_options.chunk_size),
        }
    }
}

impl From<PyFlattenOptions> for FlattenOptions {
    fn from(options: PyFlattenOptions) -> Self {
        FlattenOptions {
            separator: options.separator,
            max_concurrency: options.max_concurrency,
            max_depth: options.max_depth,
            include_array_indices: options.include_array_indices,
            expand_arrays: options.expand_arrays,
            chunk_size: options.chunk_size,
        }
    }
}

/// Flatten a JSON string to a dictionary with dot-notation keys
#[pyfunction]
fn flatten_json_str(py: Python, json_str: &str, options: Option<PyFlattenOptions>) -> PyResult<PyObject> {
    let options = options.unwrap_or_else(|| PyFlattenOptions::new(None, None, None, None, None, None));
    let rust_options: FlattenOptions = options.into();

    // Parse the JSON string
    let json_value: Value = serde_json::from_str(json_str)
        .map_err(|e| PyValueError::new_err(format!("Invalid JSON: {}", e)))?;

    // Flatten the JSON
    let flattened = flatten_json(&json_value, &rust_options);

    // Convert the HashMap to a Python dict
    let py_dict = PyDict::new(py);
    for (key, value) in flattened {
        py_dict.set_item(key, value)?;
    }

    Ok(py_dict.into())
}

/// Flatten a JSON file to a list of dictionaries
#[pyfunction]
fn flatten_json_file_py(py: Python, filepath: &str, options: Option<PyFlattenOptions>) -> PyResult<PyObject> {
    let options = options.unwrap_or_else(|| PyFlattenOptions::new(None, None, None, None, None, None));
    let rust_options: FlattenOptions = options.into();

    // Flatten the JSON file
    let result = flatten_json_file(filepath, &rust_options)
        .map_err(|e| PyIOError::new_err(format!("Error reading file: {}", e)))?;

    // Convert the result to a Python list of dicts
    let py_list = PyList::empty(py);
    for item in result {
        let py_dict = PyDict::new(py);
        for (key, value) in item {
            py_dict.set_item(key, value)?;
        }
        py_list.append(py_dict)?;
    }

    Ok(py_list.into())
}

/// Process a large JSON file optimized for memory usage
#[pyfunction]
fn process_large_json_file(py: Python, filepath: &str, options: Option<PyFlattenOptions>) -> PyResult<PyObject> {
    let options = options.unwrap_or_else(|| PyFlattenOptions::new(None, None, None, None, None, None));
    let rust_options: FlattenOptions = options.into();

    // Process the large JSON file
    let result = process_large_json_object(filepath, &rust_options)
        .map_err(|e| PyIOError::new_err(format!("Error processing file: {}", e)))?;

    // Convert the result to a Python dict
    let py_dict = PyDict::new(py);
    for (key, value) in result {
        py_dict.set_item(key, value)?;
    }

    Ok(py_dict.into())
}

/// Flatten a JSON file and prepare it for pandas DataFrame conversion
/// Returns a dict with column names as keys and lists of values as values
#[pyfunction]
fn flatten_pandas_ready(py: Python, filepath: &str, options: Option<PyFlattenOptions>) -> PyResult<PyObject> {
    let options = options.unwrap_or_else(|| PyFlattenOptions::new(None, None, None, None, None, None));
    let rust_options: FlattenOptions = options.into();

    // Flatten the JSON file
    let flattened_data = flatten_json_file(filepath, &rust_options)
        .map_err(|e| PyIOError::new_err(format!("Error reading file: {}", e)))?;

    // If there's no data, return an empty dict
    if flattened_data.is_empty() {
        return Ok(PyDict::new(py).into());
    }

    // Collect all column names
    let mut all_columns = std::collections::HashSet::new();
    for item in &flattened_data {
        for key in item.keys() {
            all_columns.insert(key.clone());
        }
    }

    // Create dict with column names as keys and empty lists as values
    let py_dict = PyDict::new(py);
    for column in &all_columns {
        let py_list = PyList::empty(py);
        py_dict.set_item(column, py_list)?;
    }

    // Fill in the lists with values
    for item in flattened_data {
        for column in &all_columns {
            let value = item.get(column).cloned().unwrap_or_else(|| "".to_string());
            let py_list = py_dict.get_item(column).unwrap().downcast::<PyList>().unwrap();
            py_list.append(value)?;
        }
    }

    Ok(py_dict.into())
}

/// Flatten a JSON file and prepare it for polaris DataFrame conversion
/// Returns a dict with column names as keys and lists of values as values
/// This is optimized for the polaris DataFrame API
#[pyfunction]
fn flatten_polaris_ready(py: Python, filepath: &str, options: Option<PyFlattenOptions>) -> PyResult<PyObject> {
    let options = options.unwrap_or_else(|| PyFlattenOptions::new(None, None, None, None, None, None));
    let rust_options: FlattenOptions = options.into();

    // Flatten the JSON file
    let flattened_data = flatten_json_file(filepath, &rust_options)
        .map_err(|e| PyIOError::new_err(format!("Error reading file: {}", e)))?;

    // If there's no data, return an empty dict
    if flattened_data.is_empty() {
        return Ok(PyDict::new(py).into());
    }

    // Convert to column-oriented format for Polaris
    let mut columns: HashMap<String, Vec<String>> = HashMap::new();
    
    // First pass: collect all column names
    for item in &flattened_data {
        for key in item.keys() {
            if !columns.contains_key(key) {
                columns.insert(key.clone(), Vec::with_capacity(flattened_data.len()));
            }
        }
    }
    
    // Second pass: fill columns with values
    for item in flattened_data {
        for (key, column) in columns.iter_mut() {
            let value = item.get(key).cloned().unwrap_or_else(|| "null".to_string());
            column.push(value);
        }
    }
    
    // Convert to Python dict
    let py_dict = PyDict::new(py);
    for (key, values) in columns {
        let py_list = PyList::new(py, &values);
        py_dict.set_item(key, py_list)?;
    }

    Ok(py_dict.into())
}
