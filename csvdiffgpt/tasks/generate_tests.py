"""Task to generate tests for a CSV file."""
from typing import Dict, Any, Optional, List, Union
import os
import pandas as pd

from ..core.utils import validate_file
from ..core.preprocessor import CSVPreprocessor
from ..tasks.validate import validate_raw
from ..llm.openai import OpenAIProvider
from ..llm.gemini import GeminiProvider
from ..llm.base import LLMProvider
from ..test_generators import get_all_generators
from ..test_frameworks import get_framework, get_available_frameworks

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


def generate_tests_raw(
    file: str,
    framework: str = "pytest",
    sep: Optional[str] = None,
    max_rows_analyzed: int = 150000,
    max_cols_analyzed: Optional[int] = None,
    null_threshold: float = 5.0,
    cardinality_threshold: float = 95.0,
    outlier_threshold: float = 3.0,
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate tests for a CSV file without using LLM.
    
    Args:
        file: Path to the CSV file
        framework: Test framework to use ('pytest', 'great_expectations', 'dbt')
        sep: CSV separator (auto-detected if None)
        max_rows_analyzed: Maximum number of rows to analyze
        max_cols_analyzed: Maximum number of columns to analyze
        null_threshold: Percentage threshold for flagging columns with missing values
        cardinality_threshold: Percentage threshold for high cardinality warning
        outlier_threshold: Z-score threshold for identifying outliers
        model_name: Optional name for the model/table (for DBT)
        
    Returns:
        A dictionary containing generated tests and test code
    """
    # Validate the file
    is_valid, error = validate_file(file)
    if not is_valid:
        raise ValueError(f"Error: {error}")
    
    # Get validation results to identify issues
    validation_results = validate_raw(
        file=file,
        sep=sep,
        max_rows_analyzed=max_rows_analyzed,
        max_cols_analyzed=max_cols_analyzed,
        null_threshold=null_threshold,
        cardinality_threshold=cardinality_threshold,
        outlier_threshold=outlier_threshold
    )
    
    # Preprocess the CSV file to get metadata
    preprocessor = CSVPreprocessor(
        file_path=file,
        sep=sep,
        max_rows_analyzed=max_rows_analyzed,
        max_cols_analyzed=max_cols_analyzed
    )
    metadata = preprocessor.to_dict()
    df = preprocessor.df
    
    if df is None:
        raise ValueError("Failed to load DataFrame")
    
    # Initialize test results
    test_results = {
        "file_info": validation_results["file_info"],
        "framework": framework,
        "test_count": 0,
        "tests_by_type": {},
        "tests_by_severity": {},
        "test_code": "",
    }
    
    # Get all registered test generators and apply them
    generators = get_all_generators()
    all_tests = []
    
    # Process each generator
    for generator in generators:
        # Generate tests
        tests = generator.generate_tests(
            df, 
            metadata, 
            validation_results,
            null_threshold=null_threshold,
            cardinality_threshold=cardinality_threshold,
            outlier_threshold=outlier_threshold
        )
        
        all_tests.extend(tests)
    
    # Count tests by type and severity
    test_types = {}
    test_severities = {}
    
    for test in all_tests:
        # Count by type
        test_type = test.get("type", "other")
        if test_type not in test_types:
            test_types[test_type] = 0
        test_types[test_type] += 1
        
        # Count by severity
        severity = test.get("severity", "medium")
        if severity not in test_severities:
            test_severities[severity] = 0
        test_severities[severity] += 1
    
    # Update test results
    test_results["test_count"] = len(all_tests)
    test_results["tests_by_type"] = test_types
    test_results["tests_by_severity"] = test_severities
    
    # Get the appropriate test framework adapter
    framework_adapter = get_framework(f"{framework.capitalize()}Adapter")
    if framework_adapter is None:
        available_frameworks = get_available_frameworks()
        raise ValueError(f"Framework '{framework}' not supported. Available frameworks: {[f.replace('Adapter', '').lower() for f in available_frameworks]}")
    
    # Format the tests
    test_code = framework_adapter.format_tests(
        all_tests, 
        metadata, 
        file_path=file,
        model_name=model_name or os.path.splitext(os.path.basename(file))[0]
    )
    
    # Update test results with the generated code
    test_results["test_code"] = test_code
    test_results["tests"] = all_tests
    
    return test_results


def generate_tests(
    file: str,
    question: str = "Generate tests for this dataset to ensure data quality",
    api_key: Optional[str] = None,
    provider: str = "gemini",
    framework: str = "pytest",
    sep: Optional[str] = None,
    max_rows_analyzed: int = 150000,
    max_cols_analyzed: Optional[int] = None,
    null_threshold: float = 5.0,
    cardinality_threshold: float = 95.0,
    outlier_threshold: float = 3.0,
    model_name: Optional[str] = None,
    model: Optional[str] = None,
    use_llm: bool = True,
    **kwargs: Any
) -> Union[str, Dict[str, Any]]:
    """
    Generate tests for a CSV file.
    
    Args:
        file: Path to the CSV file
        question: The specific question about test generation
        api_key: API key for the LLM provider
        provider: LLM provider to use ('openai', 'gemini', etc.)
        framework: Test framework to use ('pytest', 'great_expectations', 'dbt')
        sep: CSV separator (auto-detected if None)
        max_rows_analyzed: Maximum number of rows to analyze
        max_cols_analyzed: Maximum number of columns to analyze
        null_threshold: Percentage threshold for flagging columns with missing values
        cardinality_threshold: Percentage threshold for high cardinality warning
        outlier_threshold: Z-score threshold for identifying outliers
        model_name: Optional name for the model/table (for DBT)
        model: Specific model to use (provider-dependent)
        use_llm: Whether to use LLM for generating summary (if False, returns raw data)
        **kwargs: Additional parameters for the LLM provider
        
    Returns:
        If use_llm is True, returns a string with test generation insights.
        If use_llm is False, returns a dictionary with structured test specifications.
    """
    # If LLM is not used, call generate_tests_raw instead
    if not use_llm:
        return generate_tests_raw(
            file=file,
            framework=framework,
            sep=sep,
            max_rows_analyzed=max_rows_analyzed,
            max_cols_analyzed=max_cols_analyzed,
            null_threshold=null_threshold,
            cardinality_threshold=cardinality_threshold,
            outlier_threshold=outlier_threshold,
            model_name=model_name
        )
    
    # Validate the file
    is_valid, error = validate_file(file)
    if not is_valid:
        return f"Error: {error}"
    
    # Get the structured test results
    test_results = generate_tests_raw(
        file=file,
        framework=framework,
        sep=sep,
        max_rows_analyzed=max_rows_analyzed,
        max_cols_analyzed=max_cols_analyzed,
        null_threshold=null_threshold,
        cardinality_threshold=cardinality_threshold,
        outlier_threshold=outlier_threshold,
        model_name=model_name
    )
    
    # Get validation results
    validation_results = validate_raw(
        file=file,
        sep=sep,
        max_rows_analyzed=max_rows_analyzed,
        max_cols_analyzed=max_cols_analyzed,
        null_threshold=null_threshold,
        cardinality_threshold=cardinality_threshold,
        outlier_threshold=outlier_threshold
    )
    
    # Preprocess the CSV file to get metadata
    preprocessor = CSVPreprocessor(
        file_path=file,
        sep=sep,
        max_rows_analyzed=max_rows_analyzed,
        max_cols_analyzed=max_cols_analyzed
    )
    metadata = preprocessor.to_dict()
    
    # Get the LLM provider
    llm = get_provider(provider, api_key)
    
    # Format the prompt
    prompt_data = {
        "metadata": metadata,
        "validation_results": validation_results,
        "question": question,
        "framework": framework
    }
    prompt = llm.format_prompt("generate_tests", prompt_data)
    
    # Create a clean copy of kwargs without 'use_llm'
    clean_kwargs = {k: v for k, v in kwargs.items() if k != "use_llm"}
    
    # Query the LLM
    model_kwargs = {}
    if model:
        model_kwargs["model"] = model
    
    response = llm.query(prompt, **model_kwargs, **clean_kwargs)
    
    return response