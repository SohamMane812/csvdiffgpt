"""Pytest configuration and fixtures."""
import os
import pytest
import tempfile
import shutil
from typing import Dict, Any, List, Tuple

# Path to fixtures directory
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def simple_csv_path():
    """Path to simple.csv test fixture."""
    return os.path.join(FIXTURES_DIR, "simple.csv")


@pytest.fixture
def modified_csv_path():
    """Path to modified.csv test fixture."""
    return os.path.join(FIXTURES_DIR, "modified.csv")


@pytest.fixture
def temp_csv_dir():
    """Create a temporary directory for CSV files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after tests
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_csv_file(temp_csv_dir):
    """Create a temporary CSV file."""
    file_path = os.path.join(temp_csv_dir, "test.csv")
    
    # Create a simple CSV file
    with open(file_path, "w") as f:
        f.write("col1,col2,col3\n")
        f.write("a,1,true\n")
        f.write("b,2,false\n")
        f.write("c,3,true\n")
    
    return file_path


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return """
## Dataset Summary

This dataset contains 5 records with 4 columns (id, name, age, score).

### Key Observations:
- Age ranges from 22 to 45 years
- Score ranges from 75 to 95 points
- Average age is 32 years
- Average score is 86.2 points
    """


class MockLLMProvider:
    """Mock LLM provider for testing."""
    
    def __init__(self, response=None):
        self.response = response or "Mock LLM response"
        self.last_prompt = None
    
    def query(self, prompt, **kwargs):
        """Mock query method."""
        self.last_prompt = prompt
        return self.response
    
    def format_prompt(self, task_name, data):
        """Mock format_prompt method."""
        return f"Mock prompt for {task_name}"
    

@pytest.fixture
def mock_llm_provider(mock_llm_response):
    """Create a mock LLM provider instance."""
    return MockLLMProvider(response=mock_llm_response)


@pytest.fixture
def patch_llm_provider(monkeypatch):
    """Patch the LLM provider to use a mock."""
    def _patch_provider(provider_name, mock_provider):
        from csvdiffgpt.tasks.summarize import LLM_PROVIDERS
        from csvdiffgpt.tasks.compare import LLM_PROVIDERS as COMPARE_LLM_PROVIDERS
        
        # Patch the provider in both modules
        LLM_PROVIDERS[provider_name] = lambda **kwargs: mock_provider
        COMPARE_LLM_PROVIDERS[provider_name] = lambda **kwargs: mock_provider
    
    return _patch_provider