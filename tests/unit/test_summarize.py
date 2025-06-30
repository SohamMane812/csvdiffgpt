"""Tests for summarize functionality."""
import os
import pytest
from unittest.mock import patch, MagicMock

from csvdiffgpt import summarize, summarize_raw


def test_summarize_raw(simple_csv_path):
    """Test summarize_raw function."""
    metadata = summarize_raw(simple_csv_path)
    
    # Check basic metadata
    assert metadata['file_path'] == simple_csv_path
    assert metadata['total_rows'] == 5
    assert metadata['total_columns'] == 4
    
    # Check columns
    assert set(metadata['columns'].keys()) == {'id', 'name', 'age', 'score'}
    
    # Check specific values
    assert metadata['columns']['age']['min'] == 22
    assert metadata['columns']['age']['max'] == 45


def test_summarize_with_llm(simple_csv_path, mock_llm_provider, patch_llm_provider):
    """Test summarize function with LLM."""
    # Patch the provider to use our mock
    patch_llm_provider('gemini', mock_llm_provider)
    
    # Call summarize
    result = summarize(
        file=simple_csv_path,
        question="Describe this dataset",
        provider='gemini',
        api_key='fake-key'  # This won't be used because we're mocking
    )
    
    # Check that we got the mock response
    assert result == mock_llm_provider.response
    
    # Check that the prompt was formatted
    assert mock_llm_provider.last_prompt is not None


def test_summarize_without_llm(simple_csv_path):
    """Test summarize function without LLM."""
    result = summarize(
        file=simple_csv_path,
        use_llm=False
    )
    
    # Result should be the raw metadata
    assert result['file_path'] == simple_csv_path
    assert result['total_rows'] == 5
    assert result['total_columns'] == 4


def test_summarize_nonexistent_file():
    """Test summarize with a nonexistent file."""
    result = summarize("nonexistent_file.csv")
    assert "Error: File not found" in result


def test_summarize_custom_separator():
    """Test summarize with custom separator."""
    # Create a temporary file with semicolon separator
    with open('temp_semicolon.csv', 'w') as f:
        f.write("id;name;value\n")
        f.write("1;test;100\n")
    
    try:
        # Should auto-detect the semicolon
        result1 = summarize_raw('temp_semicolon.csv')
        assert result1['separator'] == ';'
        
        # Should use the provided separator
        result2 = summarize_raw('temp_semicolon.csv', sep=';')
        assert result2['separator'] == ';'
    finally:
        # Clean up
        if os.path.exists('temp_semicolon.csv'):
            os.remove('temp_semicolon.csv')