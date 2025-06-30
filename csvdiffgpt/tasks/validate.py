"""Task to validate a CSV file for data quality issues."""
from typing import Dict, Any, Optional, List, Union
import os
import pandas as pd
import numpy as np

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


def validate_raw(
    file: str,
    sep: Optional[str] = None,
    max_rows_analyzed: int = 150000,
    max_cols_analyzed: Optional[int] = None,
    null_threshold: float = 5.0,
    cardinality_threshold: float = 95.0,
    outlier_threshold: float = 3.0
) -> Dict[str, Any]:
    """
    Validate a CSV file and identify data quality issues without using LLM.
    
    Args:
        file: Path to the CSV file
        sep: CSV separator (auto-detected if None)
        max_rows_analyzed: Maximum number of rows to analyze
        max_cols_analyzed: Maximum number of columns to analyze
        null_threshold: Percentage threshold for flagging columns with missing values
        cardinality_threshold: Percentage threshold for high cardinality warning
        outlier_threshold: Z-score threshold for identifying outliers
        
    Returns:
        A dictionary containing validation results
    """
    # Validate the file
    is_valid, error = validate_file(file)
    if not is_valid:
        raise ValueError(f"Error: {error}")
    
    # Preprocess the CSV file
    preprocessor = CSVPreprocessor(
        file_path=file,
        sep=sep,
        max_rows_analyzed=max_rows_analyzed,
        max_cols_analyzed=max_cols_analyzed
    )
    
    metadata = preprocessor.analyze()
    df = preprocessor.df
    
    if df is None:
        raise ValueError("Failed to load DataFrame")
    
    # Initialize validation results
    validation_results = {
        "file_info": {
            "file_path": metadata["file_path"],
            "file_size_mb": metadata["file_size_mb"],
            "total_rows": metadata["total_rows"],
            "total_columns": metadata["total_columns"],
            "analyzed_rows": metadata["analyzed_rows"]
        },
        "issues": {
            "missing_values": [],
            "high_cardinality": [],
            "outliers": [],
            "inconsistent_values": [],
            "type_issues": []
        },
        "summary": {
            "missing_values_columns": 0,
            "high_cardinality_columns": 0,
            "outlier_columns": 0,
            "inconsistent_columns": 0,
            "type_issue_columns": 0,
            "total_issues": 0
        }
    }
    
    # Check for missing values
    for col, col_meta in metadata["columns"].items():
        # Missing values check
        if col_meta["null_percentage"] > null_threshold:
            validation_results["issues"]["missing_values"].append({
                "column": col,
                "null_count": col_meta["nulls"],
                "null_percentage": col_meta["null_percentage"],
                "severity": "high" if col_meta["null_percentage"] > 20 else "medium" if col_meta["null_percentage"] > 10 else "low"
            })
    
        # High cardinality check for string/categorical columns
        if col_meta["type"] == "object" and col_meta["unique_count"] > 0:
            unique_percentage = (col_meta["unique_count"] / (metadata["analyzed_rows"] - col_meta["nulls"])) * 100 if (metadata["analyzed_rows"] - col_meta["nulls"]) > 0 else 0
            if unique_percentage > cardinality_threshold:
                validation_results["issues"]["high_cardinality"].append({
                    "column": col,
                    "unique_count": col_meta["unique_count"],
                    "unique_percentage": round(unique_percentage, 2),
                    "severity": "high" if unique_percentage > 99 else "medium" if unique_percentage > 97 else "low"
                })
    
        # Type issues check (mixed data types)
        if col_meta["type"] == "object" and "examples" in col_meta:
            # Check if examples look like they could be numeric but are stored as strings
            examples = col_meta["examples"]
            numeric_count = 0
            date_count = 0
            
            for ex in examples:
                # Skip None values
                if ex is None:
                    continue
                
                # Check if looks like a number
                try:
                    float(str(ex).replace(',', ''))
                    numeric_count += 1
                    continue
                except ValueError:
                    pass
                
                # Check if looks like a date
                try:
                    # Very simple date check
                    if '/' in str(ex) or '-' in str(ex):
                        parts = str(ex).replace('/', '-').split('-')
                        if len(parts) == 3 and all(part.isdigit() for part in parts):
                            date_count += 1
                except:
                    pass
            
            # If more than half of examples look like numbers or dates
            if len(examples) > 0:
                if numeric_count / len(examples) > 0.5:
                    validation_results["issues"]["type_issues"].append({
                        "column": col,
                        "issue": "possible_numeric",
                        "examples": examples,
                        "severity": "medium"
                    })
                elif date_count / len(examples) > 0.5:
                    validation_results["issues"]["type_issues"].append({
                        "column": col,
                        "issue": "possible_date",
                        "examples": examples,
                        "severity": "medium"
                    })
    
    # Check for outliers in numeric columns
    for col in df.select_dtypes(include=[np.number]).columns:
        # Skip columns with too many nulls
        if df[col].isna().mean() > 0.5:
            continue
            
        # Calculate z-scores for outlier detection
        mean = df[col].mean()
        std = df[col].std()
        
        # Skip if std is 0 or close to 0
        if std < 1e-10:
            continue
            
        # Calculate z-scores
        z_scores = np.abs((df[col] - mean) / std)
        
        # Find values that exceed the threshold
        outlier_mask = z_scores > outlier_threshold
        outliers = df[col][outlier_mask]
        
        # Only report if we found outliers
        if len(outliers) > 0:
            outlier_percentage = (len(outliers) / len(df[col])) * 100
            
            # Always report outliers, regardless of percentage
            validation_results["issues"]["outliers"].append({
                "column": col,
                "outlier_count": int(len(outliers)),
                "outlier_percentage": round(outlier_percentage, 2),
                "min_value": float(df[col].min()),
                "max_value": float(df[col].max()),
                "mean": float(mean),
                "std": float(std),
                "severity": "high" if outlier_percentage > 5 else "medium" if outlier_percentage > 1 else "low"
            })
    
    # Check for inconsistent formats in string columns
    for col in df.select_dtypes(include=['object']).columns:
        # Skip columns with too many nulls
        if df[col].isna().mean() > 0.5:
            continue
            
        # Check string length consistency
        non_null_strings = df[col].dropna().astype(str)
        if len(non_null_strings) > 0:
            lengths = non_null_strings.str.len()
            length_mean = lengths.mean()
            length_std = lengths.std()
            
            # If standard deviation of string length is high relative to mean
            if length_std > 0 and length_mean > 0 and (length_std / length_mean) > 0.5:
                # Check if there are very different lengths
                min_length = lengths.min()
                max_length = lengths.max()
                
                if max_length > min_length * 2:  # If max is more than double min
                    validation_results["issues"]["inconsistent_values"].append({
                        "column": col,
                        "issue": "inconsistent_length",
                        "min_length": int(min_length),
                        "max_length": int(max_length),
                        "avg_length": round(float(length_mean), 2),
                        "std_length": round(float(length_std), 2),
                        "severity": "medium"
                    })
    
    # Update summary counts
    validation_results["summary"]["missing_values_columns"] = len(validation_results["issues"]["missing_values"])
    validation_results["summary"]["high_cardinality_columns"] = len(validation_results["issues"]["high_cardinality"])
    validation_results["summary"]["outlier_columns"] = len(validation_results["issues"]["outliers"])
    validation_results["summary"]["inconsistent_columns"] = len(validation_results["issues"]["inconsistent_values"])
    validation_results["summary"]["type_issue_columns"] = len(validation_results["issues"]["type_issues"])
    
    # Calculate total issues
    validation_results["summary"]["total_issues"] = (
        validation_results["summary"]["missing_values_columns"] +
        validation_results["summary"]["high_cardinality_columns"] +
        validation_results["summary"]["outlier_columns"] +
        validation_results["summary"]["inconsistent_columns"] +
        validation_results["summary"]["type_issue_columns"]
    )
    
    return validation_results


def validate(
    file: str,
    question: str = "Validate this dataset and identify data quality issues",
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
    Validate a CSV file and identify data quality issues.
    
    Args:
        file: Path to the CSV file
        question: The specific question about data quality
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
        If use_llm is True, returns a string with data quality assessment.
        If use_llm is False, returns a dictionary with structured validation results.
    """
    # If LLM is not used, call validate_raw instead
    if not use_llm:
        return validate_raw(
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
    
    # Get the structured validation results
    validation_results = validate_raw(
        file=file,
        sep=sep,
        max_rows_analyzed=max_rows_analyzed,
        max_cols_analyzed=max_cols_analyzed,
        null_threshold=null_threshold,
        cardinality_threshold=cardinality_threshold,
        outlier_threshold=outlier_threshold
    )
    
    # Get the LLM provider
    llm = get_provider(provider, api_key)
    
    # Format the prompt
    prompt_data = {
        "metadata": validation_results,
        "question": question
    }
    prompt = llm.format_prompt("validate", prompt_data)
    
    # Create a clean copy of kwargs without 'use_llm'
    clean_kwargs = {k: v for k, v in kwargs.items() if k != "use_llm"}
    
    # Query the LLM
    model_kwargs = {}
    if model:
        model_kwargs["model"] = model
    
    response = llm.query(prompt, **model_kwargs, **clean_kwargs)
    
    return response