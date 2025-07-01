"""Task to recommend schema restructuring for a CSV file."""
from typing import Dict, Any, Optional, List, Union
import os
import re
import pandas as pd

from ..core.utils import validate_file
from ..core.preprocessor import CSVPreprocessor
from ..tasks.validate import validate_raw
from ..llm.openai import OpenAIProvider
from ..llm.gemini import GeminiProvider
from ..llm.base import LLMProvider
from ..restructure_analyzers import get_all_analyzers
from ..data_models import get_model_adapter, get_available_adapters

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


def restructure_raw(
    file: str,
    format: str = "sql",
    sep: Optional[str] = None,
    max_rows_analyzed: int = 150000,
    max_cols_analyzed: Optional[int] = None,
    null_threshold: float = 5.0,
    cardinality_threshold: float = 95.0,
    outlier_threshold: float = 3.0,
    table_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a CSV file and recommend schema restructuring without using LLM.
    
    Args:
        file: Path to the CSV file
        format: Output format for recommendations ('sql', 'mermaid', 'python')
        sep: CSV separator (auto-detected if None)
        max_rows_analyzed: Maximum number of rows to analyze
        max_cols_analyzed: Maximum number of columns to analyze
        null_threshold: Percentage threshold for flagging columns with missing values
        cardinality_threshold: Percentage threshold for high cardinality warning
        outlier_threshold: Z-score threshold for identifying outliers
        table_name: Optional name for the database table
        
    Returns:
        A dictionary containing restructuring recommendations and formatted output
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
    
    # Derive table name if not provided
    if table_name is None:
        table_name = os.path.splitext(os.path.basename(file))[0]
        # Clean up the table name to be valid SQL
        table_name = re.sub(r'[^\w]', '_', table_name).lower()
    
    # Initialize restructuring results
    restructure_results = {
        "file_info": validation_results["file_info"],
        "format": format,
        "table_name": table_name,
        "recommendation_count": 0,
        "recommendations_by_type": {},
        "recommendations_by_severity": {},
        "recommendations": [],
        "output_code": "",
    }
    
    # Get all registered analyzers and apply them
    analyzers = get_all_analyzers()
    all_recommendations = []
    
    # Process each analyzer
    for analyzer in analyzers:
        try:
            # Generate recommendations
            recommendations = analyzer.analyze(
                df, 
                metadata, 
                validation_results,
                null_threshold=null_threshold,
                cardinality_threshold=cardinality_threshold,
                outlier_threshold=outlier_threshold
            )
            
            all_recommendations.extend(recommendations)
        except Exception as e:
            print(f"Error in {analyzer.get_name()}: {str(e)}")
    
    # Count recommendations by type and severity
    recommendation_types = {}
    recommendation_severities = {}
    
    for rec in all_recommendations:
        # Count by type
        rec_type = rec.get("type", "other")
        if rec_type not in recommendation_types:
            recommendation_types[rec_type] = 0
        recommendation_types[rec_type] += 1
        
        # Count by severity
        severity = rec.get("severity", "medium")
        if severity not in recommendation_severities:
            recommendation_severities[severity] = 0
        recommendation_severities[severity] += 1
    
    # Update restructure results
    restructure_results["recommendation_count"] = len(all_recommendations)
    restructure_results["recommendations_by_type"] = recommendation_types
    restructure_results["recommendations_by_severity"] = recommendation_severities
    restructure_results["recommendations"] = all_recommendations
    
    # Get the appropriate model adapter
    model_adapter = get_model_adapter(format)
    if model_adapter is None:
        available_adapters = get_available_adapters()
        raise ValueError(f"Format '{format}' not supported. Available formats: {available_adapters}")
    
    # Format the recommendations
    output_code = model_adapter.format_recommendations(
        all_recommendations, 
        metadata, 
        file_path=file,
        table_name=table_name
    )
    
    # Update output code
    restructure_results["output_code"] = output_code
    
    return restructure_results


def restructure(
    file: str,
    question: str = "Recommend schema improvements for this dataset",
    api_key: Optional[str] = None,
    provider: str = "gemini",
    format: str = "sql",
    sep: Optional[str] = None,
    max_rows_analyzed: int = 150000,
    max_cols_analyzed: Optional[int] = None,
    null_threshold: float = 5.0,
    cardinality_threshold: float = 95.0,
    outlier_threshold: float = 3.0,
    table_name: Optional[str] = None,
    model: Optional[str] = None,
    use_llm: bool = True,
    **kwargs: Any
) -> Union[str, Dict[str, Any]]:
    """
    Analyze a CSV file and recommend schema restructuring.
    
    Args:
        file: Path to the CSV file
        question: The specific question about schema restructuring
        api_key: API key for the LLM provider
        provider: LLM provider to use ('openai', 'gemini', etc.)
        format: Output format for recommendations ('sql', 'mermaid', 'python')
        sep: CSV separator (auto-detected if None)
        max_rows_analyzed: Maximum number of rows to analyze
        max_cols_analyzed: Maximum number of columns to analyze
        null_threshold: Percentage threshold for flagging columns with missing values
        cardinality_threshold: Percentage threshold for high cardinality warning
        outlier_threshold: Z-score threshold for identifying outliers
        table_name: Optional name for the database table
        model: Specific model to use (provider-dependent)
        use_llm: Whether to use LLM for generating summary (if False, returns raw data)
        **kwargs: Additional parameters for the LLM provider
        
    Returns:
        If use_llm is True, returns a string with restructuring insights.
        If use_llm is False, returns a dictionary with structured restructuring recommendations.
    """
    # If LLM is not used, call restructure_raw instead
    if not use_llm:
        return restructure_raw(
            file=file,
            format=format,
            sep=sep,
            max_rows_analyzed=max_rows_analyzed,
            max_cols_analyzed=max_cols_analyzed,
            null_threshold=null_threshold,
            cardinality_threshold=cardinality_threshold,
            outlier_threshold=outlier_threshold,
            table_name=table_name
        )
    
    # Validate the file
    is_valid, error = validate_file(file)
    if not is_valid:
        return f"Error: {error}"
    
    # Get the structured restructuring recommendations
    restructure_results = restructure_raw(
        file=file,
        format=format,
        sep=sep,
        max_rows_analyzed=max_rows_analyzed,
        max_cols_analyzed=max_cols_analyzed,
        null_threshold=null_threshold,
        cardinality_threshold=cardinality_threshold,
        outlier_threshold=outlier_threshold,
        table_name=table_name
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
        "recommendations": restructure_results["recommendations"],
        "question": question,
        "format": format
    }
    prompt = llm.format_prompt("restructure", prompt_data)
    
    # Create a clean copy of kwargs without 'use_llm'
    clean_kwargs = {k: v for k, v in kwargs.items() if k != "use_llm"}
    
    # Query the LLM
    model_kwargs = {}
    if model:
        model_kwargs["model"] = model
    
    response = llm.query(prompt, **model_kwargs, **clean_kwargs)
    
    return response