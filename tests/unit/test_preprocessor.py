"""Tests for CSV preprocessor."""
import os
import pytest
import pandas as pd

from csvdiffgpt.core.preprocessor import CSVPreprocessor


def test_preprocessor_init(simple_csv_path):
    """Test preprocessor initialization."""
    preprocessor = CSVPreprocessor(simple_csv_path)
    assert preprocessor.file_path == simple_csv_path
    assert preprocessor.sep == ','  # Auto-detected
    assert preprocessor.max_rows_analyzed == 150000
    assert preprocessor.max_cols_analyzed is None


def test_preprocessor_load_data(simple_csv_path):
    """Test data loading."""
    preprocessor = CSVPreprocessor(simple_csv_path)
    preprocessor.load_data()
    
    # Check that the DataFrame was loaded
    assert preprocessor.df is not None
    assert isinstance(preprocessor.df, pd.DataFrame)
    assert len(preprocessor.df) == 5  # 5 rows in simple.csv
    assert list(preprocessor.df.columns) == ['id', 'name', 'age', 'score']


def test_preprocessor_analyze(simple_csv_path):
    """Test metadata analysis."""
    preprocessor = CSVPreprocessor(simple_csv_path)
    metadata = preprocessor.analyze()
    
    # Check basic metadata
    assert metadata['file_path'] == simple_csv_path
    assert metadata['total_rows'] == 5
    assert metadata['total_columns'] == 4
    assert list(metadata['columns'].keys()) == ['id', 'name', 'age', 'score']
    
    # Check column metadata
    assert metadata['columns']['id']['type'] == 'int64'
    assert metadata['columns']['name']['type'] == 'object'
    assert metadata['columns']['age']['type'] == 'int64'
    assert metadata['columns']['score']['type'] == 'int64'
    
    # Check stats
    assert metadata['columns']['age']['min'] == 22
    assert metadata['columns']['age']['max'] == 45
    
    # Check for nulls (none in our test file)
    assert metadata['columns']['name']['nulls'] == 0


def test_preprocessor_column_limit(simple_csv_path):
    """Test column limit functionality."""
    # Limit to first 2 columns
    preprocessor = CSVPreprocessor(simple_csv_path, max_cols_analyzed=2)
    preprocessor.load_data()
    
    # Only first 2 columns should be loaded
    assert list(preprocessor.df.columns) == ['id', 'name']
    assert len(preprocessor.df.columns) == 2


def test_preprocessor_row_limit(simple_csv_path):
    """Test row limit functionality."""
    # Limit to first 3 rows
    preprocessor = CSVPreprocessor(simple_csv_path, max_rows_analyzed=3)
    preprocessor.load_data()
    
    # Only first 3 rows should be loaded
    assert len(preprocessor.df) == 3


def test_preprocessor_to_json(simple_csv_path):
    """Test JSON serialization."""
    preprocessor = CSVPreprocessor(simple_csv_path)
    json_str = preprocessor.to_json()
    
    # Check that the result is a string
    assert isinstance(json_str, str)
    assert 'file_path' in json_str
    assert 'columns' in json_str
    # The path will be escaped in JSON, so we can't do a direct match
    # Instead, check if the filename is present
    assert 'simple.csv' in json_str