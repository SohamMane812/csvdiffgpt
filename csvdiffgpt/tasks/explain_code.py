"""Task to explain code for data manipulation and analysis."""
import os
import inspect
from typing import Dict, Any, Optional, Union, Callable

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


def detect_language(code: str, file_path: Optional[str] = None) -> str:
    """
    Detect the programming language of the code.
    
    Args:
        code: Code string
        file_path: Path to the code file, if available
        
    Returns:
        Detected language ("python", "sql", or "unknown")
    """
    # Try to detect from file extension if available
    if file_path:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.py', '.ipynb']:
            return "python"
        elif ext in ['.sql']:
            return "sql"
    
    # Try to detect from code content
    code_lower = code.lower()
    
    # Check for SQL keywords
    sql_keywords = ['select', 'from', 'where', 'group by', 'order by', 
                   'join', 'inner join', 'left join', 'create table',
                   'insert into', 'update', 'delete from']
    
    # Check for Python keywords and common libraries
    python_indicators = ['import ', 'def ', 'class ', 'if __name__', 
                        'with open', 'for ', 'while ', 'return ',
                        'pandas', 'numpy', 'matplotlib', 'sklearn']
    
    # Count matches for each language
    sql_count = sum(1 for kw in sql_keywords if kw in code_lower)
    python_count = sum(1 for ind in python_indicators if ind in code_lower)
    
    # Determine language based on keyword counts
    if sql_count > python_count and sql_count > 1:
        return "sql"
    elif python_count > 0:
        return "python"
    
    # Default to unknown if can't determine
    return "unknown"


def get_code_from_object(obj: Callable) -> str:
    """
    Get the source code from a Python object (function, class, method).
    
    Args:
        obj: Python object
        
    Returns:
        Source code as string
    """
    try:
        return inspect.getsource(obj)
    except (TypeError, OSError):
        return f"# Could not retrieve source code for {obj.__name__}"


def get_code_from_file(file_path: str) -> str:
    """
    Read code from a file.
    
    Args:
        file_path: Path to the code file
        
    Returns:
        Code as string
    """
    # Check if file exists
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")
    
    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def preprocess_code(code: str, language: str) -> str:
    """
    Preprocess code to prepare for explanation.
    
    Args:
        code: Code string
        language: Programming language
        
    Returns:
        Preprocessed code
    """
    # Remove excess whitespace
    lines = code.split('\n')
    lines = [line.rstrip() for line in lines]
    
    # Remove multiple empty lines
    result_lines = []
    prev_empty = False
    for line in lines:
        if not line.strip():
            if not prev_empty:
                result_lines.append(line)
                prev_empty = True
        else:
            result_lines.append(line)
            prev_empty = False
    
    return '\n'.join(result_lines)


def explain_code(
    code: Optional[str] = None,
    file_path: Optional[str] = None,
    code_object: Optional[Callable] = None,
    language: Optional[str] = None,
    detail_level: str = "medium",
    focus: Optional[str] = None,
    audience: str = "data_analyst",
    api_key: Optional[str] = None,
    provider: str = "gemini",
    model: Optional[str] = None,
    **kwargs: Any
) -> str:
    """
    Explain code using an LLM.
    
    Args:
        code: Code string to explain
        file_path: Path to a code file (alternative to code parameter)
        code_object: Python object (function, class) to explain (alternative to code parameter)
        language: Programming language ("python", "sql", or "unknown", auto-detected if None)
        detail_level: Level of explanation detail ("high", "medium", "low")
        focus: Specific part or aspect to focus on
        audience: Target audience for the explanation
        api_key: API key for the LLM provider
        provider: LLM provider to use ("openai", "gemini", etc.)
        model: Specific model to use (provider-dependent)
        **kwargs: Additional parameters for the LLM provider
        
    Returns:
        Explanation of the code
    """
    # Get the code string from the provided source
    if code is not None:
        code_str = code
    elif file_path is not None:
        code_str = get_code_from_file(file_path)
    elif code_object is not None:
        code_str = get_code_from_object(code_object)
    else:
        raise ValueError("No code provided. Specify one of: code, file_path, or code_object.")
    
    # Auto-detect language if not specified
    if language is None:
        language = detect_language(code_str, file_path)
    
    # Preprocess code
    processed_code = preprocess_code(code_str, language)
    
    # Ensure valid detail level
    detail_level = detail_level.lower()
    if detail_level not in ["high", "medium", "low"]:
        detail_level = "medium"
    
    # Set default focus if not provided
    focus_text = focus if focus else "entire code"
    
    # Set default audience if not valid
    valid_audiences = ["beginner", "data_analyst", "data_scientist", "developer", "technical", "non_technical"]
    if audience.lower() not in valid_audiences:
        audience = "data_analyst"
    
    # Get the LLM provider
    llm = get_provider(provider, api_key)
    
    # Format the prompt
    prompt_data = {
        "code": processed_code,
        "language": language,
        "detail_level": detail_level,
        "focus": focus_text,
        "audience": audience
    }
    prompt = llm.format_prompt("explain_code", prompt_data)
    
    # Create a clean copy of kwargs
    clean_kwargs = {k: v for k, v in kwargs.items()}
    
    # Query the LLM
    model_kwargs = {}
    if model:
        model_kwargs["model"] = model
    
    response = llm.query(prompt, **model_kwargs, **clean_kwargs)
    
    return response