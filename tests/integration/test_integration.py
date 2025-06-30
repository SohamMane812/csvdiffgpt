"""Integration tests for csvdiffgpt package."""
import os
import sys
import subprocess
import pytest
import json
from unittest.mock import patch

# Skip all integration tests if environment variable is set
pytestmark = pytest.mark.skipif(
    os.environ.get("SKIP_INTEGRATION_TESTS") == "1",
    reason="Integration tests are disabled"
)


def test_end_to_end_summarize_raw(simple_csv_path):
    """Test end-to-end summarize without LLM."""
    # Run the CLI command
    result = subprocess.run(
        [sys.executable, "-m", "csvdiffgpt.cli", "summarize", simple_csv_path, "--no-llm"],
        capture_output=True,
        text=True
    )
    
    # Check that the command succeeded
    assert result.returncode == 0
    
    # Check that the output contains expected information (raw JSON)
    assert "file_path" in result.stdout
    assert "columns" in result.stdout
    assert "total_rows" in result.stdout


def test_end_to_end_compare_raw(simple_csv_path, modified_csv_path):
    """Test end-to-end compare without LLM."""
    # Run the CLI command
    result = subprocess.run(
        [
            sys.executable, "-m", "csvdiffgpt.cli", "compare", 
            simple_csv_path, modified_csv_path, "--no-llm"
        ],
        capture_output=True,
        text=True
    )
    
    # Check that the command succeeded
    assert result.returncode == 0
    
    # Check that the output contains expected information (raw JSON)
    assert "file1" in result.stdout
    assert "file2" in result.stdout
    assert "comparison" in result.stdout
    assert "structural_changes" in result.stdout


@pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), 
                   reason="GEMINI_API_KEY not set")
def test_end_to_end_summarize_with_llm(simple_csv_path):
    """Test end-to-end summarize with LLM (requires API key)."""
    # Run the CLI command
    result = subprocess.run(
        [
            sys.executable, "-m", "csvdiffgpt.cli", "summarize", 
            simple_csv_path, "--provider", "gemini"
        ],
        capture_output=True,
        text=True,
        env=dict(os.environ, GEMINI_API_KEY=os.environ.get("GEMINI_API_KEY"))
    )
    
    # Check that the command succeeded
    assert result.returncode == 0
    
    # Check that the output is not empty and doesn't contain error messages
    assert len(result.stdout) > 100
    assert "Error" not in result.stdout


@pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), 
                   reason="GEMINI_API_KEY not set")
def test_end_to_end_compare_with_llm(simple_csv_path, modified_csv_path):
    """Test end-to-end compare with LLM (requires API key)."""
    # Run the CLI command
    result = subprocess.run(
        [
            sys.executable, "-m", "csvdiffgpt.cli", "compare", 
            simple_csv_path, modified_csv_path, "--provider", "gemini"
        ],
        capture_output=True,
        text=True,
        env=dict(os.environ, GEMINI_API_KEY=os.environ.get("GEMINI_API_KEY"))
    )
    
    # Check that the command succeeded
    assert result.returncode == 0
    
    # Check that the output is not empty and doesn't contain error messages
    assert len(result.stdout) > 100
    assert "Error" not in result.stdout


def test_programmatic_api_summarize(simple_csv_path, mock_llm_provider, patch_llm_provider):
    """Test the programmatic API for summarize."""
    from csvdiffgpt import summarize
    
    # Patch the provider
    patch_llm_provider('gemini', mock_llm_provider)
    
    # Test with LLM
    result_with_llm = summarize(
        file=simple_csv_path,
        question="Describe this dataset",
        provider='gemini',
        api_key='fake-key'
    )
    assert result_with_llm == mock_llm_provider.response
    
    # Test without LLM
    result_without_llm = summarize(
        file=simple_csv_path,
        use_llm=False
    )
    assert result_without_llm['total_rows'] == 5
    assert result_without_llm['total_columns'] == 4


def test_programmatic_api_compare(simple_csv_path, modified_csv_path, mock_llm_provider, patch_llm_provider):
    """Test the programmatic API for compare."""
    from csvdiffgpt import compare
    
    # Patch the provider
    patch_llm_provider('gemini', mock_llm_provider)
    
    # Test with LLM
    result_with_llm = compare(
        file1=simple_csv_path,
        file2=modified_csv_path,
        question="What changed?",
        provider='gemini',
        api_key='fake-key'
    )
    assert result_with_llm == mock_llm_provider.response
    
    # Test without LLM
    result_without_llm = compare(
        file1=simple_csv_path,
        file2=modified_csv_path,
        use_llm=False
    )
    assert 'comparison' in result_without_llm
    assert 'structural_changes' in result_without_llm['comparison']
    assert 'value_changes' in result_without_llm['comparison']