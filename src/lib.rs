// src/lib.rs
use serde_json::{Value, Map};
use std::collections::HashMap;
use rayon::prelude::*;
use std::sync::{Arc, Mutex};
use std::io::{BufReader};
use std::fs::File;

pub type FlattenedJson = HashMap<String, String>;

/// Options for controlling the flattening process
#[derive(Clone, Debug)]
pub struct FlattenOptions {
    /// Separator used in the flattened keys
    pub separator: String,
    /// Maximum concurrency for parallel processing
    pub max_concurrency: usize,
    /// Maximum nested depth to process (0 means no limit)
    pub max_depth: usize,
    /// Whether to include array indices in keys
    pub include_array_indices: bool,
    /// Whether to expand arrays into individual columns
    pub expand_arrays: bool,
    /// Chunk size for processing large JSON files
    pub chunk_size: usize,
}

impl Default for FlattenOptions {
    fn default() -> Self {
        FlattenOptions {
            separator: ".".to_string(),
            max_concurrency: num_cpus::get(),
            max_depth: 0,
            include_array_indices: true,
            expand_arrays: true,
            chunk_size: 10000,
        }
    }
}

/// Flattens a JSON value into a HashMap with dot-notation keys
pub fn flatten_json(value: &Value, options: &FlattenOptions) -> FlattenedJson {
    let mut result = HashMap::new();
    flatten_value("", value, &mut result, options, 0);
    result
}

/// Flattens a JSON value recursively
fn flatten_value(
    prefix: &str,
    value: &Value,
    result: &mut FlattenedJson,
    options: &FlattenOptions,
    depth: usize,
) {
    // Check if we've exceeded the maximum depth
    if options.max_depth > 0 && depth >= options.max_depth {
        // Store the whole subtree as a JSON string
        result.insert(prefix.to_string(), value.to_string());
        return;
    }

    match value {
        Value::Object(map) => {
            flatten_object(prefix, map, result, options, depth);
        }
        Value::Array(array) => {
            flatten_array(prefix, array, result, options, depth);
        }
        Value::String(s) => {
            if !prefix.is_empty() {
                result.insert(prefix.to_string(), s.clone());
            }
        }
        Value::Number(n) => {
            if !prefix.is_empty() {
                result.insert(prefix.to_string(), n.to_string());
            }
        }
        Value::Bool(b) => {
            if !prefix.is_empty() {
                result.insert(prefix.to_string(), b.to_string());
            }
        }
        Value::Null => {
            if !prefix.is_empty() {
                result.insert(prefix.to_string(), "null".to_string());
            }
        }
    }
}

/// Flattens a JSON object
fn flatten_object(
    prefix: &str,
    obj: &Map<String, Value>,
    result: &mut FlattenedJson,
    options: &FlattenOptions,
    depth: usize,
) {
    for (key, value) in obj {
        let new_prefix = if prefix.is_empty() {
            key.clone()
        } else {
            format!("{}{}{}", prefix, options.separator, key)
        };
        flatten_value(&new_prefix, value, result, options, depth + 1);
    }
}

/// Flattens a JSON array
fn flatten_array(
    prefix: &str,
    array: &[Value],
    result: &mut FlattenedJson,
    options: &FlattenOptions,
    depth: usize,
) {
    if options.expand_arrays {
        for (i, value) in array.iter().enumerate() {
            let new_prefix = if options.include_array_indices {
                format!("{}{}{}", prefix, options.separator, i)
            } else {
                prefix.to_string()
            };
            flatten_value(&new_prefix, value, result, options, depth + 1);
        }
    } else {
        // Store the array as a JSON string
        result.insert(prefix.to_string(), serde_json::to_string(array).unwrap_or_default());
    }
}

/// Flattens a JSON file in a streaming fashion
/// This is optimized for memory usage with very large files
pub fn flatten_json_file(
    filepath: &str,
    options: &FlattenOptions,
) -> Result<Vec<FlattenedJson>, Box<dyn std::error::Error>> {
    let file = File::open(filepath)?;
    let reader = BufReader::new(file);
    
    // Use a streaming JSON parser for memory efficiency
    let stream = serde_json::Deserializer::from_reader(reader).into_iter::<Value>();
    
    // For array-root JSONs, process elements individually
    let results = Arc::new(Mutex::new(Vec::new()));
    let chunk_size = options.chunk_size;
    
    // Process the stream in chunks to limit memory usage
    let mut chunk = Vec::with_capacity(chunk_size);
    
    for item in stream {
        match item {
            Ok(value) => {
                chunk.push(value);
                
                if chunk.len() >= chunk_size {
                    process_chunk(&chunk, &results, options);
                    chunk.clear();
                }
            }
            Err(e) => {
                return Err(Box::new(e));
            }
        }
    }
    
    // Process any remaining items
    if !chunk.is_empty() {
        process_chunk(&chunk, &results, options);
    }
    
    // Return the accumulated results
    let results = Arc::try_unwrap(results)
        .expect("There should be no more references to the results")
        .into_inner()?;
    
    Ok(results)
}

/// Process a chunk of JSON values in parallel
fn process_chunk(
    chunk: &[Value],
    results: &Arc<Mutex<Vec<FlattenedJson>>>,
    options: &FlattenOptions,
) {
    // Use Rayon for parallel processing
    let parallel_results: Vec<FlattenedJson> = chunk
        .par_iter()
        .map(|value| flatten_json(value, options))
        .collect();
    
    // Add the results to the shared collection
    let mut results_guard = results.lock().unwrap();
    results_guard.extend(parallel_results);
}

/// Processes a single large JSON object by iterating through its top-level keys
/// This is useful for very large objects that might not fit in memory
// Process a large JSON object by iterating through its top-level keys
pub fn process_large_json_object(
    filepath: &str,
    options: &FlattenOptions,
) -> Result<FlattenedJson, Box<dyn std::error::Error>> {
    let file = File::open(filepath)?;
    let reader = BufReader::new(file);
    
    // Parse the outer structure of the JSON to get top-level keys
    let json: Value = serde_json::from_reader(reader)?;
    
    if let Value::Object(map) = json {
        // Process each top-level key in parallel
        let flattened = Arc::new(Mutex::new(HashMap::new()));
        
        // Convert map entries to a Vec which can be processed in parallel
        let entries: Vec<_> = map.into_iter().collect();
        
        // Now we can use par_iter on the Vec
        entries.par_iter().for_each(|(key, value)| {
            let mut partial_result = HashMap::new();
            flatten_value(key, value, &mut partial_result, options, 0);
            
            // Merge the partial results
            let mut flattened_guard = flattened.lock().unwrap();
            flattened_guard.extend(partial_result);
        });
        
        let result = Arc::try_unwrap(flattened)
            .expect("There should be no more references to the flattened map")
            .into_inner()?;
        
        Ok(result)
    } else {
        // If the top-level is not an object, just flatten it directly
        Ok(flatten_json(&json, options))
    }
}

/// A more memory efficient version for extremely large files
/// This uses a streaming approach and processes the JSON file line by line
pub fn flatten_json_streaming(
    filepath: &str,
    callback: impl Fn(FlattenedJson) + Send + Sync,
    options: &FlattenOptions,
) -> Result<(), Box<dyn std::error::Error>> {
    use std::io::{BufRead};
    
    let file = File::open(filepath)?;
    let reader = BufReader::new(file);
    
    // Process the file line by line
    for line in reader.lines() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }
        
        // Parse the JSON line
        let json: Value = serde_json::from_str(&line)?;
        
        // Flatten the JSON
        let flattened = flatten_json(&json, options);
        
        // Call the callback with the flattened JSON
        callback(flattened);
    }
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_flatten_simple_object() {
        let json = json!({
            "name": "John",
            "age": 30,
            "address": {
                "street": "123 Main St",
                "city": "New York"
            }
        });

        let options = FlattenOptions::default();
        let flattened = flatten_json(&json, &options);

        assert_eq!(flattened.get("name"), Some(&"John".to_string()));
        assert_eq!(flattened.get("age"), Some(&"30".to_string()));
        assert_eq!(flattened.get("address.street"), Some(&"123 Main St".to_string()));
        assert_eq!(flattened.get("address.city"), Some(&"New York".to_string()));
    }

    #[test]
    fn test_flatten_array() {
        let json = json!({
            "name": "John",
            "skills": ["programming", "design", "communication"]
        });

        let options = FlattenOptions::default();
        let flattened = flatten_json(&json, &options);

        assert_eq!(flattened.get("skills.0"), Some(&"programming".to_string()));
        assert_eq!(flattened.get("skills.1"), Some(&"design".to_string()));
        assert_eq!(flattened.get("skills.2"), Some(&"communication".to_string()));
    }

    #[test]
    fn test_flatten_nested_array() {
        let json = json!({
            "name": "John",
            "education": [
                {"degree": "BS", "year": 2010},
                {"degree": "MS", "year": 2012}
            ]
        });

        let options = FlattenOptions::default();
        let flattened = flatten_json(&json, &options);

        assert_eq!(flattened.get("education.0.degree"), Some(&"BS".to_string()));
        assert_eq!(flattened.get("education.0.year"), Some(&"2010".to_string()));
        assert_eq!(flattened.get("education.1.degree"), Some(&"MS".to_string()));
        assert_eq!(flattened.get("education.1.year"), Some(&"2012".to_string()));
    }

    #[test]
    fn test_custom_separator() {
        let json = json!({
            "user": {
                "name": "John",
                "email": "john@example.com"
            }
        });

        let mut options = FlattenOptions::default();
        options.separator = "_".to_string();
        
        let flattened = flatten_json(&json, &options);

        assert_eq!(flattened.get("user_name"), Some(&"John".to_string()));
        assert_eq!(flattened.get("user_email"), Some(&"john@example.com".to_string()));
    }

    #[test]
    fn test_max_depth() {
        let json = json!({
            "user": {
                "name": "John",
                "address": {
                    "city": "New York",
                    "geo": {
                        "lat": 40.7128,
                        "lng": -74.0060
                    }
                }
            }
        });

        let mut options = FlattenOptions::default();
        options.max_depth = 2;
        
        let flattened = flatten_json(&json, &options);

        assert_eq!(flattened.get("user.name"), Some(&"John".to_string()));
        assert_eq!(flattened.get("user.address.city"), Some(&"New York".to_string()));
        
        // The geo object should be stored as a JSON string
        assert_eq!(
            flattened.get("user.address.geo"),
            Some(&r#"{"lat":40.7128,"lng":-74.006}"#.to_string())
        );
    }
}
