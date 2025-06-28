"""Task to summarize a CSV file."""
from typing import Dict, Any, Optional
import os

from ..core.utils import validate_file
from ..core.preprocessor import CSVPreprocessor
from ..llm.openai import OpenAIProvider
from ..llm.gemini import GeminiProvider
from ..llm.base import LLMProvider

# Dictionary of available LLM providers
LLM_PROVIDERS = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    # Add more providers here as they are implemented
}

def get_provider(provider_name: str, api_key: Optional[str] = None) -> LLMProvider:
    """
    Get an LLM provider instance by name.
    
    Args:
        provider_name: Name of the provider ('openai', 'gemini', etc.)
        api_key: API key for the provider
        
    Returns:
        An instance of the LLM provider
    """
    if provider_name not in LLM_PROVIDERS:
        raise ValueError(f"Provider '{provider_name}' not supported. Available providers: {list(LLM_PROVIDERS.keys())}")
    
    # Initialize the provider
    return LLM_PROVIDERS[provider_name](api_key=api_key)

def summarize(
    file: str,
    question: str = "Summarize this dataset",
    api_key: Optional[str] = None,
    provider: str = "gemini",
    sep: Optional[str] = None,
    max_rows_analyzed: int = 150000,
    max_cols_analyzed: Optional[int] = None,
    model: Optional[str] = None,
    **kwargs
) -> str:
    """
    Summarize a CSV file using LLM.
    
    Args:
        file: Path to the CSV file
        question: The specific question about the dataset
        api_key: API key for the LLM provider
        provider: LLM provider to use ('openai', 'gemini', etc.)
        sep: CSV separator (auto-detected if None)
        max_rows_analyzed: Maximum number of rows to analyze
        max_cols_analyzed: Maximum number of columns to analyze
        model: Specific model to use (provider-dependent)
        **kwargs: Additional parameters for the LLM provider
        
    Returns:
        A summary of the CSV file
    """
    # Validate the file
    is_valid, error = validate_file(file)
    if not is_valid:
        return f"Error: {error}"
    
    # Preprocess the CSV file
    preprocessor = CSVPreprocessor(
        file_path=file,
        sep=sep,
        max_rows_analyzed=max_rows_analyzed,
        max_cols_analyzed=max_cols_analyzed
    )
    metadata = preprocessor.analyze()
    
    # Get the LLM provider
    llm = get_provider(provider, api_key)
    
    # Format the prompt
    prompt_data = {
        "metadata": metadata,
        "question": question
    }
    prompt = llm.format_prompt("summarize", prompt_data)
    
    # Query the LLM
    model_kwargs = {}
    if model:
        model_kwargs["model"] = model
    
    response = llm.query(prompt, **model_kwargs, **kwargs)
    
    return response