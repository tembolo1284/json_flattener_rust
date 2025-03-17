// tests/test_flattener.rs
use json_flattener::{FlattenOptions, flatten_json, flatten_json_file};
use serde_json::{Value};
use std::fs::File;
use std::io::BufReader;

#[test]
fn test_flatten_small_sample() {
    // Path to the small sample JSON file
    let file_path = "data/small_sample.json";
    
    // Read the JSON file
    let file = File::open(file_path).expect("Failed to open JSON file");
    let reader = BufReader::new(file);
    let json: Value = serde_json::from_reader(reader).expect("Failed to parse JSON");
    
    // Create default flattening options
    let options = FlattenOptions::default();
    
    // Flatten the JSON
    let flattened = flatten_json(&json, &options);
    
    // Basic validation checks
    assert!(!flattened.is_empty(), "Flattened JSON should not be empty");
    
    // Check if some expected keys exist (adjust these to match your actual data)
    println!("Flattened JSON contains {} key-value pairs", flattened.len());
    
    // Print a few sample keys and values for inspection
    let sample_count = 5.min(flattened.len());
    println!("Sample of flattened key-value pairs:");
    for (i, (key, value)) in flattened.iter().take(sample_count).enumerate() {
        println!("  {}: {} = {}", i + 1, key, value);
    }
    
    // You can add more specific assertions based on your sample data
    // For example:
    // assert!(flattened.contains_key("metadata.version"), "Should contain metadata.version key");
}

#[test]
fn test_flatten_file() {
    // Path to the small sample JSON file
    let file_path = "data/small_sample.json";
    
    // Create default flattening options
    let options = FlattenOptions::default();
    
    // Test the file processing function
    let result = flatten_json_file(file_path, &options);
    assert!(result.is_ok(), "File flattening should succeed");
    
    // Get the flattened results
    let flattened = result.unwrap();
    assert!(!flattened.is_empty(), "Flattened results should not be empty");
    
    println!("File flattening produced {} result objects", flattened.len());
    println!("First result contains {} key-value pairs", flattened[0].len());
}
