"""Tests for validate functionality."""
import os
import pytest
from unittest.mock import patch, MagicMock

from csvdiffgpt import validate, validate_raw


def test_validate_raw(simple_csv_path):
    """Test validate_raw function."""
    validation_results = validate_raw(simple_csv_path)
    
    # Check basic structure
    assert "file_info" in validation_results
    assert "issues" in validation_results
    assert "summary" in validation_results
    
    # Check file info
    assert validation_results["file_info"]["file_path"] == simple_csv_path
    assert validation_results["file_info"]["total_rows"] == 5
    assert validation_results["file_info"]["total_columns"] == 4
    
    # Check issue categories
    assert "missing_values" in validation_results["issues"]
    assert "high_cardinality" in validation_results["issues"]
    assert "outliers" in validation_results["issues"]
    assert "inconsistent_values" in validation_results["issues"]
    assert "type_issues" in validation_results["issues"]
    
    # Check summary counts
    assert "total_issues" in validation_results["summary"]
    assert isinstance(validation_results["summary"]["total_issues"], int)


def test_validate_raw_with_custom_thresholds(simple_csv_path):
    """Test validate_raw function with custom thresholds."""
    # Set very low thresholds to trigger more issues
    validation_results = validate_raw(
        simple_csv_path, 
        null_threshold=0.1,  # Very low threshold for nulls
        cardinality_threshold=50.0,  # Lower threshold for high cardinality
        outlier_threshold=1.0  # Lower threshold for outliers
    )
    
    # The counts might be different with custom thresholds
    assert isinstance(validation_results["summary"]["total_issues"], int)


def test_validate_with_llm(simple_csv_path, monkeypatch):
    """Test validate function with LLM."""
    from csvdiffgpt.tasks.validate import validate
    from unittest.mock import MagicMock
    
    # Create a mock LLM provider
    mock_provider = MagicMock()
    mock_provider.query.return_value = "Mocked LLM response"
    
    # Create a mock get_provider function that returns our mock
    def mock_get_provider(provider_name, api_key=None):
        return mock_provider
    
    # Patch the get_provider function to return our mock
    monkeypatch.setattr("csvdiffgpt.tasks.validate.get_provider", mock_get_provider)
    
    # Call validate
    result = validate(
        file=simple_csv_path,
        question="Check this dataset for issues",
        provider='gemini',
        api_key='fake-key'
    )
    
    # Check that we got the mock response
    assert result == "Mocked LLM response"
    
    # Check that the mock was called
    assert mock_provider.query.called


def test_validate_without_llm(simple_csv_path):
    """Test validate function without LLM."""
    result = validate(
        file=simple_csv_path,
        use_llm=False
    )
    
    # Result should be the raw validation data
    assert "file_info" in result
    assert "issues" in result
    assert "summary" in result


def test_validate_nonexistent_file():
    """Test validate with a nonexistent file."""
    with pytest.raises(ValueError, match="Error: File not found"):
        validate_raw("nonexistent_file.csv")

    result = validate("nonexistent_file.csv")
    assert "Error: File not found" in result


def test_validate_outlier_detection():
    """Test the outlier detection logic."""
    from csvdiffgpt.tasks.validate import validate_raw
    import os
    
    # Create a temporary CSV with known outliers
    with open('temp_outliers.csv', 'w') as f:
        f.write("id,value\n")
        f.write("1,10\n")
        f.write("2,12\n")
        f.write("3,9\n")
        f.write("4,11\n")
        f.write("5,100\n")  # This is a very extreme outlier
    
    try:
        # Validate with a very low outlier threshold to ensure we catch the outlier
        result = validate_raw('temp_outliers.csv', outlier_threshold=1.0)
        
        # Check if outliers were detected
        assert len(result["issues"]["outliers"]) > 0
        
        # Find the 'value' column outlier
        value_outlier = None
        for outlier in result["issues"]["outliers"]:
            if outlier["column"] == "value":
                value_outlier = outlier
                break
        
        # Check that the value column outlier was detected
        assert value_outlier is not None, "No outlier detected for 'value' column"
        assert value_outlier["outlier_count"] > 0
        assert value_outlier["max_value"] == 100.0
    finally:
        # Clean up
        if os.path.exists('temp_outliers.csv'):
            os.remove('temp_outliers.csv')


def test_validate_missing_values():
    """Test the missing values detection."""
    # Create a temporary CSV with missing values
    with open('temp_missing.csv', 'w') as f:
        f.write("id,name,value\n")
        f.write("1,Alice,10\n")
        f.write("2,Bob,\n")  # Missing value
        f.write("3,Charlie,30\n")
        f.write("4,,40\n")  # Missing value
        f.write("5,Eve,50\n")
    
    try:
        # Validate with a low missing values threshold
        result = validate_raw('temp_missing.csv', null_threshold=1.0)
        
        # Check if missing values were detected
        missing_values = result["issues"]["missing_values"]
        assert len(missing_values) > 0
        
        # Check that 'name' column has missing values
        name_missing = next((item for item in missing_values if item["column"] == "name"), None)
        assert name_missing is not None
        assert name_missing["null_count"] == 1
        assert name_missing["null_percentage"] == 20.0
        
        # Check that 'value' column has missing values
        value_missing = next((item for item in missing_values if item["column"] == "value"), None)
        assert value_missing is not None
        assert value_missing["null_count"] == 1
        assert value_missing["null_percentage"] == 20.0
    finally:
        # Clean up
        if os.path.exists('temp_missing.csv'):
            os.remove('temp_missing.csv')