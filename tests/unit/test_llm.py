"""Tests for LLM providers."""
import os
import pytest
from unittest.mock import patch, MagicMock

from csvdiffgpt.llm.base import LLMProvider


class TestProvider(LLMProvider):
    """Test implementation of LLMProvider for testing."""
    
    def _get_api_key_from_env(self):
        return os.environ.get("TEST_API_KEY")
    
    def query(self, prompt, model=None, **kwargs):
        return f"Test response for: {prompt[:20]}..."


def test_base_provider():
    """Test the base provider functionality."""
    provider = TestProvider(api_key="test-key")
    assert provider.api_key == "test-key"


def test_load_prompt_template(monkeypatch, tmp_path):
    """Test loading prompt templates."""
    # Create a mock prompt file
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    test_prompt_file = prompt_dir / "test_task.txt"
    test_prompt_file.write_text("SYSTEM: {system}\nUSER: {question}")
    
    # Patch the path to use our temporary directory
    provider = TestProvider(api_key="test-key")
    
    with monkeypatch.context() as m:
        m.setattr("os.path.dirname", lambda x: str(tmp_path))
        
        # Test loading the prompt
        prompt = provider.load_prompt_template("test_task")
        assert prompt == "SYSTEM: {system}\nUSER: {question}"
        
        # Test error when prompt doesn't exist
        with pytest.raises(ValueError):
            provider.load_prompt_template("nonexistent_task")


def test_format_prompt(monkeypatch, tmp_path):
    """Test prompt formatting."""
    # Create a mock prompt file
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    test_prompt_file = prompt_dir / "test_task.txt"
    test_prompt_file.write_text("SYSTEM: {system}\nUSER: {question}\nDATA: {metadata}")
    
    # Create test data
    data = {
        "system": "You are a helpful assistant",
        "question": "What is this data?",
        "metadata": {"key": "value"}
    }
    
    # Patch the path to use our temporary directory
    provider = TestProvider(api_key="test-key")
    
    with monkeypatch.context() as m:
        m.setattr("os.path.dirname", lambda x: str(tmp_path))
        
        # Test formatting the prompt
        formatted = provider.format_prompt("test_task", data)
        assert "You are a helpful assistant" in formatted
        assert "What is this data?" in formatted
        # Just check if metadata is in there in some form (might be formatted differently)
        assert "key" in formatted
        assert "value" in formatted


@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), 
                    reason="OpenAI API key not available")
def test_openai_provider():
    """Test the OpenAI provider with a real API key (optional)."""
    from csvdiffgpt.llm.openai import OpenAIProvider
    
    provider = OpenAIProvider()
    assert provider.api_key is not None
    
    # This is an expensive test that requires a real API key, so we'll skip it by default


@pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), 
                    reason="Gemini API key not available")
def test_gemini_provider():
    """Test the Gemini provider with a real API key (optional)."""
    from csvdiffgpt.llm.gemini import GeminiProvider
    
    provider = GeminiProvider()
    assert provider.api_key is not None
    
    # This is an expensive test that requires a real API key, so we'll skip it by default


def test_mock_openai():
    """Test mocking the OpenAI provider."""
    with patch("openai.OpenAI", autospec=True) as mock_openai_class:
        # Set up the mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Set up the completion response
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Mocked response"
        
        # Make chat.completions.create return our mock completion
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Import the provider class
        from csvdiffgpt.llm.openai import OpenAIProvider
        
        # Create provider with patch in place
        provider = OpenAIProvider(api_key="fake-key")
        
        # Manually inject the mock client
        provider.client = mock_client
        
        # Test the query
        result = provider.query("Test prompt")
        
        # Check the result
        assert result == "Mocked response"
        
        # Check that the API was called correctly
        mock_client.chat.completions.create.assert_called_once()