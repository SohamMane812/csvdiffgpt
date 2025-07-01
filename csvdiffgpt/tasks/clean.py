"""Task to recommend data cleaning steps for a CSV file."""
from typing import Dict, Any, Optional, List, Union
import os
import pandas as pd
import numpy as np

from ..core.utils import validate_file
from ..core.preprocessor import CSVPreprocessor
from ..tasks.validate import validate_raw
from ..llm.openai import OpenAIProvider
from ..llm.gemini import GeminiProvider
from ..llm.base import LLMProvider
from ..cleaners import get_all_cleaners
from ..cleaners.helpers import generate_sample_code, calculate_potential_impact

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


def clean_raw(
    file: str,
    sep: Optional[str] = None,
    max_rows_analyzed: int = 150000,
    max_cols_analyzed: Optional[int] = None,
    null_threshold: float = 5.0,
    cardinality_threshold: float = 95.0,
    outlier_threshold: float = 3.0,
    generate_code: bool = True
) -> Dict[str, Any]:
    """
    Analyze a CSV file and recommend cleaning steps without using LLM.
    
    Args:
        file: Path to the CSV file
        sep: CSV separator (auto-detected if None)
        max_rows_analyzed: Maximum number of rows to analyze
        max_cols_analyzed: Maximum number of columns to analyze
        null_threshold: Percentage threshold for flagging columns with missing values
        cardinality_threshold: Percentage threshold for high cardinality warning
        outlier_threshold: Z-score threshold for identifying outliers
        generate_code: Whether to generate example code for cleaning steps
        
    Returns:
        A dictionary containing cleaning recommendations and sample code
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
    
    # Initialize cleaning recommendations
    cleaning_results = {
        "file_info": validation_results["file_info"],
        "issues_summary": validation_results["summary"],
        "cleaning_recommendations": [],
        "sample_code": "",
        "potential_impact": {
            "rows_affected": 0,
            "percentage_data_preserved": 100.0
        }
    }
    
    # Get all registered cleaners and apply them
    cleaners = get_all_cleaners()
    all_recommendations = []
    
    # Process each cleaner
    for cleaner in cleaners:
        # Detect issues specific to this cleaner
        issues = cleaner.detect_issues(
            df, 
            metadata, 
            validation_results,
            null_threshold=null_threshold,
            cardinality_threshold=cardinality_threshold,
            outlier_threshold=outlier_threshold
        )
        
        # Skip if no issues found
        if not issues:
            continue
            
        # Generate recommendations for these issues
        recommendations = cleaner.generate_recommendations(
            df, 
            metadata, 
            issues,
            null_threshold=null_threshold,
            cardinality_threshold=cardinality_threshold,
            outlier_threshold=outlier_threshold
        )
        
        all_recommendations.extend(recommendations)
    
    # Sort recommendations by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    all_recommendations.sort(key=lambda x: (severity_order.get(x.get("severity", "low"), 3)))
    
    # Assign priorities based on sorted order
    for i, rec in enumerate(all_recommendations):
        rec["priority"] = i + 1
    
    cleaning_results["cleaning_recommendations"] = all_recommendations
    
    # Generate sample code if requested
    if generate_code and all_recommendations:
        cleaning_results["sample_code"] = generate_sample_code(file, metadata, all_recommendations)
    
    # Calculate potential impact
    cleaning_results["potential_impact"] = calculate_potential_impact(validation_results, all_recommendations)
    
    return cleaning_results


def clean(
    file: str,
    question: str = "Recommend cleaning steps for this dataset",
    api_key: Optional[str] = None,
    provider: str = "gemini",
    sep: Optional[str] = None,
    max_rows_analyzed: int = 150000,
    max_cols_analyzed: Optional[int] = None,
    null_threshold: float = 5.0,
    cardinality_threshold: float = 95.0,
    outlier_threshold: float = 3.0,
    model: Optional[str] = None,
    use_llm: bool = True,
    **kwargs: Any
) -> Union[str, Dict[str, Any]]:
    """
    Analyze a CSV file and recommend cleaning steps.
    
    Args:
        file: Path to the CSV file
        question: The specific question about cleaning recommendations
        api_key: API key for the LLM provider
        provider: LLM provider to use ('openai', 'gemini', etc.)
        sep: CSV separator (auto-detected if None)
        max_rows_analyzed: Maximum number of rows to analyze
        max_cols_analyzed: Maximum number of columns to analyze
        null_threshold: Percentage threshold for flagging columns with missing values
        cardinality_threshold: Percentage threshold for high cardinality warning
        outlier_threshold: Z-score threshold for identifying outliers
        model: Specific model to use (provider-dependent)
        use_llm: Whether to use LLM for generating summary (if False, returns raw data)
        **kwargs: Additional parameters for the LLM provider
        
    Returns:
        If use_llm is True, returns a string with cleaning recommendations.
        If use_llm is False, returns a dictionary with structured cleaning recommendations.
    """
    # If LLM is not used, call clean_raw instead
    if not use_llm:
        return clean_raw(
            file=file,
            sep=sep,
            max_rows_analyzed=max_rows_analyzed,
            max_cols_analyzed=max_cols_analyzed,
            null_threshold=null_threshold,
            cardinality_threshold=cardinality_threshold,
            outlier_threshold=outlier_threshold
        )
    
    # Validate the file
    is_valid, error = validate_file(file)
    if not is_valid:
        return f"Error: {error}"
    
    # Get the structured cleaning recommendations
    cleaning_results = clean_raw(
        file=file,
        sep=sep,
        max_rows_analyzed=max_rows_analyzed,
        max_cols_analyzed=max_cols_analyzed,
        null_threshold=null_threshold,
        cardinality_threshold=cardinality_threshold,
        outlier_threshold=outlier_threshold
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
        "question": question
    }
    prompt = llm.format_prompt("clean", prompt_data)
    
    # Create a clean copy of kwargs without 'use_llm'
    clean_kwargs = {k: v for k, v in kwargs.items() if k != "use_llm"}
    
    # Query the LLM
    model_kwargs = {}
    if model:
        model_kwargs["model"] = model
    
    response = llm.query(prompt, **model_kwargs, **clean_kwargs)
    
    return response