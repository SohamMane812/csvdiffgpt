"""Tests for restructure functionality."""
import os
import pytest
from unittest.mock import patch, MagicMock

from csvdiffgpt import restructure, restructure_raw


def test_restructure_raw(simple_csv_path):
    """Test restructure_raw function with SQL format."""
    restructure_results = restructure_raw(simple_csv_path, format="sql")
    
    # Check basic structure
    assert "file_info" in restructure_results
    assert "format" in restructure_results
    assert "table_name" in restructure_results
    assert "recommendations" in restructure_results
    assert "output_code" in restructure_results
    
    # Check format
    assert restructure_results["format"] == "sql"
    
    # Check that output code was generated
    assert isinstance(restructure_results["output_code"], str)
    assert len(restructure_results["output_code"]) > 0
    assert "CREATE TABLE" in restructure_results["output_code"]


def test_restructure_raw_different_formats(simple_csv_path):
    """Test restructure_raw function with different formats."""
    # Test with Mermaid
    mermaid_results = restructure_raw(simple_csv_path, format="mermaid")
    assert "erDiagram" in mermaid_results["output_code"]
    
    # Test with Python
    python_results = restructure_raw(simple_csv_path, format="python")
    assert "import pandas as pd" in python_results["output_code"]
    
    # Different formats should produce different output code
    assert mermaid_results["output_code"] != python_results["output_code"]


def test_restructure_with_custom_parameters(simple_csv_path):
    """Test restructure_raw with custom parameters."""
    restructure_results = restructure_raw(
        simple_csv_path, 
        format="sql",
        table_name="custom_table"
    )
    
    # Check that custom table name was used
    assert restructure_results["table_name"] == "custom_table"
    assert "CREATE TABLE custom_table" in restructure_results["output_code"]


def test_restructure_with_llm(simple_csv_path, monkeypatch):
    """Test restructure function with LLM."""
    from csvdiffgpt.tasks.restructure import restructure
    from unittest.mock import MagicMock
    
    # Create a mock LLM provider
    mock_provider = MagicMock()
    mock_provider.query.return_value = "Mocked LLM response with restructuring recommendations"
    
    # Create a mock get_provider function that returns our mock
    def mock_get_provider(provider_name, api_key=None):
        return mock_provider
    
    # Patch the get_provider function to return our mock
    monkeypatch.setattr("csvdiffgpt.tasks.restructure.get_provider", mock_get_provider)
    
    # Call restructure
    result = restructure(
        file=simple_csv_path,
        question="How should I restructure this database schema?",
        provider='gemini',
        api_key='fake-key'
    )
    
    # Check that we got the mock response
    assert result == "Mocked LLM response with restructuring recommendations"
    
    # Check that the mock was called
    assert mock_provider.query.called


def test_restructure_without_llm(simple_csv_path):
    """Test restructure function without LLM."""
    result = restructure(
        file=simple_csv_path,
        format="sql",
        use_llm=False
    )
    
    # Result should be the raw restructuring recommendations
    assert "file_info" in result
    assert "format" in result
    assert "table_name" in result
    assert "recommendations" in result
    assert "output_code" in result
    assert isinstance(result["output_code"], str)
    assert len(result["output_code"]) > 0


def test_restructure_nonexistent_file():
    """Test restructure with a nonexistent file."""
    with pytest.raises(ValueError, match="Error: File not found"):
        restructure_raw("nonexistent_file.csv")

    result = restructure("nonexistent_file.csv")
    assert "Error: File not found" in result


def test_restructure_invalid_format(simple_csv_path):
    """Test restructure with an invalid format."""
    with pytest.raises(ValueError, match="Format 'invalid' not supported"):
        restructure_raw(simple_csv_path, format="invalid")