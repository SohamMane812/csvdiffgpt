"""Tests for compare functionality."""
import os
import pytest
from unittest.mock import patch, MagicMock

from csvdiffgpt import compare, compare_raw


def test_compare_raw(simple_csv_path, modified_csv_path):
    """Test compare_raw function."""
    comparison = compare_raw(simple_csv_path, modified_csv_path)
    
    # Check basic structure
    assert 'file1' in comparison
    assert 'file2' in comparison
    assert 'comparison' in comparison
    
    # Check file metadata
    assert comparison['file1']['path'] == simple_csv_path
    assert comparison['file2']['path'] == modified_csv_path
    assert comparison['file1']['row_count'] == 5
    assert comparison['file2']['row_count'] == 5
    
    # Check structural differences
    structural = comparison['comparison']['structural_changes']
    assert 'active' in structural['only_in_file2']
    assert len(structural['common_columns']) == 4  # id, name, age, score
    assert structural['row_count_change']['difference'] == 0  # Same number of rows
    
    # Check value changes (age changed for Alice)
    assert 'age' in comparison['comparison']['value_changes']
    assert comparison['comparison']['value_changes']['age']['diff_count'] > 0


def test_compare_with_llm(simple_csv_path, modified_csv_path, mock_llm_provider, patch_llm_provider):
    """Test compare function with LLM."""
    # Patch the provider to use our mock
    patch_llm_provider('gemini', mock_llm_provider)
    
    # Call compare
    result = compare(
        file1=simple_csv_path,
        file2=modified_csv_path,
        question="What changed?",
        provider='gemini',
        api_key='fake-key'  # This won't be used because we're mocking
    )
    
    # Check that we got the mock response
    assert result == mock_llm_provider.response
    
    # Check that the prompt was formatted
    assert mock_llm_provider.last_prompt is not None


def test_compare_without_llm(simple_csv_path, modified_csv_path):
    """Test compare function without LLM."""
    result = compare(
        file1=simple_csv_path,
        file2=modified_csv_path,
        use_llm=False
    )
    
    # Result should be the raw comparison data
    assert result['file1']['path'] == simple_csv_path
    assert result['file2']['path'] == modified_csv_path
    assert 'comparison' in result


def test_compare_nonexistent_file(simple_csv_path):
    """Test compare with a nonexistent file."""
    result = compare(simple_csv_path, "nonexistent_file.csv")
    assert "Error in File 2: File not found" in result


def test_find_diff_stats():
    """Test the diff stats calculation function."""
    from csvdiffgpt.tasks.compare import find_diff_stats
    import pandas as pd
    import numpy as np
    
    # Create two simple dataframes with known differences
    df1 = pd.DataFrame({
        'A': [1, 2, 3, 4],
        'B': ['a', 'b', 'c', 'd'],
        'C': [1.1, 2.2, 3.3, 4.4],
        'D': [True, False, True, False]
    })
    
    df2 = pd.DataFrame({
        'A': [1, 2, 3, 5],  # Changed last value
        'B': ['a', 'b', 'c', 'e'],  # Changed last value
        'C': [1.1, 2.2, 3.3, 5.5],  # Changed last value
        'E': [10, 20, 30, 40]  # New column
    })
    
    # Calculate diff stats
    diff_stats = find_diff_stats(df1, df2)
    
    # Check column differences
    assert set(diff_stats['common_columns']) == {'A', 'B', 'C'}
    assert set(diff_stats['only_in_file1']) == {'D'}
    assert set(diff_stats['only_in_file2']) == {'E'}
    
    # Check value changes
    assert 'A' in diff_stats['value_changes']
    assert 'B' in diff_stats['value_changes']
    assert 'C' in diff_stats['value_changes']
    
    # Check for specific change count
    assert diff_stats['value_changes']['A']['diff_count'] == 1  # One value changed
    assert diff_stats['value_changes']['A']['diff_percentage'] == 25.0  # 1 out of 4 values