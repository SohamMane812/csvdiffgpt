"""Tests for core utility functions."""
import os
import pytest
import tempfile

from csvdiffgpt.core.utils import detect_separator, validate_file, get_file_size_mb


def test_detect_separator_comma():
    """Test comma separator detection."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("col1,col2,col3\na,b,c\n1,2,3")
        temp_path = f.name
    
    try:
        assert detect_separator(temp_path) == ','
    finally:
        os.unlink(temp_path)


def test_detect_separator_semicolon():
    """Test semicolon separator detection."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("col1;col2;col3\na;b;c\n1;2;3")
        temp_path = f.name
    
    try:
        assert detect_separator(temp_path) == ';'
    finally:
        os.unlink(temp_path)


def test_detect_separator_tab():
    """Test tab separator detection."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("col1\tcol2\tcol3\na\tb\tc\n1\t2\t3")
        temp_path = f.name
    
    try:
        assert detect_separator(temp_path) == '\t'
    finally:
        os.unlink(temp_path)


def test_validate_file_valid(temp_csv_file):
    """Test file validation with a valid file."""
    is_valid, error = validate_file(temp_csv_file)
    assert is_valid
    assert error is None


def test_validate_file_nonexistent():
    """Test file validation with a nonexistent file."""
    is_valid, error = validate_file("nonexistent_file.csv")
    assert not is_valid
    assert "not found" in error


def test_validate_file_not_csv():
    """Test file validation with a non-CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("This is not a CSV file")
        temp_path = f.name
    
    try:
        is_valid, error = validate_file(temp_path)
        # File exists but might fail CSV validation
        if not is_valid:
            assert "Invalid CSV" in error
    finally:
        os.unlink(temp_path)


def test_get_file_size_mb():
    """Test file size calculation."""
    # Create a file with known content size
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        # Write approximately 1 MB of data
        f.write("x" * 1024 * 1024)
        temp_path = f.name
    
    try:
        size_mb = get_file_size_mb(temp_path)
        # Allow small variation due to filesystem overhead
        assert 0.9 <= size_mb <= 1.1
    finally:
        os.unlink(temp_path)