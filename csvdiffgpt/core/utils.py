"""Utility functions for CSV file handling."""
import os
import csv
import pandas as pd
from typing import Optional, Tuple, List, Dict, Any, Callable

def detect_separator(file_path: str, sample_size: int = 1024) -> str:
    """
    Detect the separator used in a CSV file.
    
    Args:
        file_path: Path to the CSV file
        sample_size: Number of bytes to sample for detection
        
    Returns:
        The detected separator (default: ',')
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        sample = f.read(sample_size)
    
    # Count potential separators
    separators: Dict[str, int] = {',': 0, ';': 0, '\t': 0, '|': 0}
    for sep in separators:
        separators[sep] = sample.count(sep)
    
    # Return the most common separator
    # Fix the type issue with max() by using a lambda
    max_sep = max(separators, key=lambda k: separators[k])
    
    # If no common separator found, default to comma
    if separators[max_sep] == 0:
        return ','
    
    return max_sep

def validate_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if a file exists and is a valid CSV.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if file exists
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    
    # Check if file is readable
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sample = f.read(1024)
    except Exception as e:
        return False, f"Error reading file: {str(e)}"
    
    # Try to detect separator and validate CSV structure
    try:
        sep = detect_separator(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f, delimiter=sep)
            # Read a few rows to check structure
            for _ in range(5):
                next(csv_reader, None)
        return True, None
    except Exception as e:
        return False, f"Invalid CSV format: {str(e)}"

def get_file_size_mb(file_path: str) -> float:
    """
    Get the size of a file in megabytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in MB
    """
    return os.path.getsize(file_path) / (1024 * 1024)