"""Tests for generate_tests functionality."""
import os
import pytest
from unittest.mock import patch, MagicMock

from csvdiffgpt import generate_tests, generate_tests_raw


def test_generate_tests_raw(simple_csv_path):
    """Test generate_tests_raw function with pytest framework."""
    test_results = generate_tests_raw(simple_csv_path, framework="pytest")
    
    # Check basic structure
    assert "file_info" in test_results
    assert "framework" in test_results
    assert "test_count" in test_results
    assert "tests_by_type" in test_results
    assert "tests_by_severity" in test_results
    assert "test_code" in test_results
    assert "tests" in test_results
    
    # Check framework
    assert test_results["framework"] == "pytest"
    
    # Check that tests were generated
    assert test_results["test_count"] > 0
    assert len(test_results["tests"]) > 0
    
    # Check that test code was generated
    assert len(test_results["test_code"]) > 0
    assert "import pytest" in test_results["test_code"]
    assert "def df():" in test_results["test_code"]


def test_generate_tests_raw_different_frameworks(simple_csv_path):
    """Test generate_tests_raw function with different frameworks."""
    # Test with Great Expectations
    ge_results = generate_tests_raw(simple_csv_path, framework="great_expectations")
    assert "great_expectations" in ge_results["test_code"].lower()
    
    # Test with DBT
    dbt_results = generate_tests_raw(simple_csv_path, framework="dbt")
    assert "dbt" in dbt_results["test_code"].lower() or "yml" in dbt_results["test_code"].lower()
    
    # Different frameworks should produce different test code
    assert ge_results["test_code"] != dbt_results["test_code"]


def test_generate_tests_with_custom_parameters(simple_csv_path):
    """Test generate_tests_raw with custom parameters."""
    test_results = generate_tests_raw(
        simple_csv_path, 
        framework="pytest",
        null_threshold=10.0,
        outlier_threshold=2.0
    )
    
    # Should still generate tests
    assert test_results["test_count"] > 0
    assert len(test_results["test_code"]) > 0


def test_generate_tests_with_llm(simple_csv_path, monkeypatch):
    """Test generate_tests function with LLM."""
    from csvdiffgpt.tasks.generate_tests import generate_tests
    from unittest.mock import MagicMock
    
    # Create a mock LLM provider
    mock_provider = MagicMock()
    mock_provider.query.return_value = "Mocked LLM response with test recommendations"
    
    # Create a mock get_provider function that returns our mock
    def mock_get_provider(provider_name, api_key=None):
        return mock_provider
    
    # Patch the get_provider function to return our mock
    monkeypatch.setattr("csvdiffgpt.tasks.generate_tests.get_provider", mock_get_provider)
    
    # Call generate_tests
    result = generate_tests(
        file=simple_csv_path,
        question="How should I test this dataset?",
        provider='gemini',
        api_key='fake-key'
    )
    
    # Check that we got the mock response
    assert result == "Mocked LLM response with test recommendations"
    
    # Check that the mock was called
    assert mock_provider.query.called


def test_generate_tests_without_llm(simple_csv_path):
    """Test generate_tests function without LLM."""
    result = generate_tests(
        file=simple_csv_path,
        framework="pytest",
        use_llm=False
    )
    
    # Result should be the raw test specifications
    assert "file_info" in result
    assert "framework" in result
    assert "test_count" in result
    assert "test_code" in result
    assert isinstance(result["test_code"], str)
    assert len(result["test_code"]) > 0


def test_generate_tests_nonexistent_file():
    """Test generate_tests with a nonexistent file."""
    with pytest.raises(ValueError, match="Error: File not found"):
        generate_tests_raw("nonexistent_file.csv")

    result = generate_tests("nonexistent_file.csv")
    assert "Error: File not found" in result


def test_generate_tests_invalid_framework(simple_csv_path):
    """Test generate_tests with an invalid framework."""
    with pytest.raises(ValueError, match="Framework 'invalid' not supported"):
        generate_tests_raw(simple_csv_path, framework="invalid")