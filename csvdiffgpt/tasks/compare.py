"""Task to compare two CSV files."""
from typing import Dict, Any, Optional, Tuple, List, Union
import os
import pandas as pd
import json
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

def find_diff_stats(df1: pd.DataFrame, df2: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate additional diff statistics between two dataframes.
    
    Args:
        df1: First dataframe
        df2: Second dataframe
        
    Returns:
        Dictionary with diff statistics
    """
    diff_stats: Dict[str, Any] = {}
    
    # Get column differences
    columns1 = set(df1.columns)
    columns2 = set(df2.columns)
    
    diff_stats["common_columns"] = list(columns1.intersection(columns2))
    diff_stats["only_in_file1"] = list(columns1 - columns2)
    diff_stats["only_in_file2"] = list(columns2 - columns1)
    
    # For common columns, check data type changes
    diff_stats["type_changes"] = {}
    for col in diff_stats["common_columns"]:
        type1 = str(df1[col].dtype)
        type2 = str(df2[col].dtype)
        if type1 != type2:
            diff_stats["type_changes"][col] = {"file1": type1, "file2": type2}
    
    # Check for row count changes
    diff_stats["row_count_change"] = {
        "file1": len(df1),
        "file2": len(df2),
        "difference": len(df2) - len(df1),
        "percent_change": round((len(df2) - len(df1)) / max(1, len(df1)) * 100, 2)
    }
    
    # Calculate value changes for common columns
    diff_stats["value_changes"] = {}
    for col in diff_stats["common_columns"]:
        # Only compare if both DataFrames have the column and they can be compared
        if col in df1.columns and col in df2.columns:
            # For numeric columns, calculate statistics on differences
            if np.issubdtype(df1[col].dtype, np.number) and np.issubdtype(df2[col].dtype, np.number):
                # Compare only rows that exist in both dataframes
                min_rows = min(len(df1), len(df2))
                if min_rows > 0:
                    # Calculate absolute and percentage differences
                    abs_diff = (df2[col].iloc[:min_rows] - df1[col].iloc[:min_rows]).abs()
                    
                    # Calculate statistics on non-NaN differences
                    non_nan_diffs = abs_diff.dropna()
                    if len(non_nan_diffs) > 0:
                        diff_stats["value_changes"][col] = {
                            "mean_abs_diff": float(non_nan_diffs.mean()),
                            "max_abs_diff": float(non_nan_diffs.max()),
                            "diff_count": int((abs_diff > 0).sum()),
                            "diff_percentage": round(float((abs_diff > 0).sum()) / min_rows * 100, 2)
                        }
            # For categorical-like columns, compare value distributions
            elif df1[col].nunique() < 20 and df2[col].nunique() < 20:
                counts1 = df1[col].value_counts(normalize=True)
                counts2 = df2[col].value_counts(normalize=True)
                
                # Find categories with significant changes
                all_categories = set(counts1.index).union(set(counts2.index))
                category_changes = {}
                
                for category in all_categories:
                    val1 = float(counts1.get(category, 0)) * 100  # Convert to percentage
                    val2 = float(counts2.get(category, 0)) * 100
                    
                    # If significant change (more than 1 percentage point)
                    if abs(val1 - val2) > 1:
                        category_changes[str(category)] = {
                            "file1_pct": round(val1, 2),
                            "file2_pct": round(val2, 2),
                            "diff_pct": round(val2 - val1, 2)
                        }
                
                if category_changes:
                    diff_stats["value_changes"][col] = {
                        "category_changes": category_changes
                    }
    
    return diff_stats

def compare_raw(
    file1: str,
    file2: str,
    sep1: Optional[str] = None,
    sep2: Optional[str] = None,
    max_rows_analyzed: int = 150000,
    max_cols_analyzed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Compare two CSV files and return structured comparison data without using LLM.
    
    Args:
        file1: Path to the first CSV file
        file2: Path to the second CSV file
        sep1: CSV separator for file1 (auto-detected if None)
        sep2: CSV separator for file2 (auto-detected if None)
        max_rows_analyzed: Maximum number of rows to analyze per file
        max_cols_analyzed: Maximum number of columns to analyze per file
        
    Returns:
        A dictionary containing structured comparison data
    """
    # Validate the files
    result = {}
    for file_path, file_name in [(file1, "file1"), (file2, "file2")]:
        is_valid, error = validate_file(file_path)
        if not is_valid:
            raise ValueError(f"Error in {file_name}: {error}")
    
    # Preprocess the first CSV file
    preprocessor1 = CSVPreprocessor(
        file_path=file1,
        sep=sep1,
        max_rows_analyzed=max_rows_analyzed,
        max_cols_analyzed=max_cols_analyzed
    )
    metadata1 = preprocessor1.analyze()
    
    # Preprocess the second CSV file
    preprocessor2 = CSVPreprocessor(
        file_path=file2,
        sep=sep2,
        max_rows_analyzed=max_rows_analyzed,
        max_cols_analyzed=max_cols_analyzed
    )
    metadata2 = preprocessor2.analyze()
    
    # Calculate diff statistics
    df1 = preprocessor1.df
    df2 = preprocessor2.df
    diff_stats = find_diff_stats(df1, df2)
    
    # Prepare result structure
    result = {
        "file1": {
            "path": file1,
            "row_count": metadata1["total_rows"],
            "column_count": metadata1["total_columns"],
            "metadata": metadata1
        },
        "file2": {
            "path": file2,
            "row_count": metadata2["total_rows"],
            "column_count": metadata2["total_columns"],
            "metadata": metadata2
        },
        "comparison": {
            "structural_changes": {
                "common_columns": diff_stats["common_columns"],
                "only_in_file1": diff_stats["only_in_file1"],
                "only_in_file2": diff_stats["only_in_file2"],
                "type_changes": diff_stats["type_changes"],
                "row_count_change": diff_stats["row_count_change"]
            },
            "value_changes": diff_stats.get("value_changes", {})
        }
    }
    
    return result

def compare(
    file1: str,
    file2: str,
    question: str = "What are the key differences between these datasets?",
    api_key: Optional[str] = None,
    provider: str = "gemini",
    sep1: Optional[str] = None,
    sep2: Optional[str] = None,
    max_rows_analyzed: int = 150000,
    max_cols_analyzed: Optional[int] = None,
    model: Optional[str] = None,
    use_llm: bool = True,
    **kwargs
) -> Union[str, Dict[str, Any]]:
    """
    Compare two CSV files and highlight differences.
    
    Args:
        file1: Path to the first CSV file
        file2: Path to the second CSV file
        question: The specific question about the differences
        api_key: API key for the LLM provider
        provider: LLM provider to use ('openai', 'gemini', etc.)
        sep1: CSV separator for file1 (auto-detected if None)
        sep2: CSV separator for file2 (auto-detected if None)
        max_rows_analyzed: Maximum number of rows to analyze per file
        max_cols_analyzed: Maximum number of columns to analyze per file
        model: Specific model to use (provider-dependent)
        use_llm: Whether to use LLM for generating summary (if False, returns raw data)
        **kwargs: Additional parameters for the LLM provider
        
    Returns:
        If use_llm is True, returns a string summary of the differences.
        If use_llm is False, returns a dictionary with structured comparison data.
    """
    # If LLM is not used, call compare_raw instead
    if not use_llm:
        return compare_raw(
            file1=file1,
            file2=file2,
            sep1=sep1,
            sep2=sep2,
            max_rows_analyzed=max_rows_analyzed,
            max_cols_analyzed=max_cols_analyzed
        )
    
    # Validate the files
    for file_path, file_name in [(file1, "File 1"), (file2, "File 2")]:
        is_valid, error = validate_file(file_path)
        if not is_valid:
            return f"Error in {file_name}: {error}"
    
    # Preprocess the first CSV file
    preprocessor1 = CSVPreprocessor(
        file_path=file1,
        sep=sep1,
        max_rows_analyzed=max_rows_analyzed,
        max_cols_analyzed=max_cols_analyzed
    )
    metadata1 = preprocessor1.analyze()
    
    # Preprocess the second CSV file
    preprocessor2 = CSVPreprocessor(
        file_path=file2,
        sep=sep2,
        max_rows_analyzed=max_rows_analyzed,
        max_cols_analyzed=max_cols_analyzed
    )
    metadata2 = preprocessor2.analyze()
    
    # Calculate additional diff statistics
    df1 = preprocessor1.df
    df2 = preprocessor2.df
    diff_stats = find_diff_stats(df1, df2)
    
    # Add diff stats to metadata
    metadata1["diff_stats"] = diff_stats
    
    # Get the LLM provider
    llm = get_provider(provider, api_key)
    
    # Format the prompt
    prompt_data = {
        "metadata1": metadata1,
        "metadata2": metadata2,
        "question": question
    }
    prompt = llm.format_prompt("compare", prompt_data)
    
    # Create a clean copy of kwargs without 'use_llm'
    clean_kwargs = {k: v for k, v in kwargs.items() if k != 'use_llm'}
    
    # Query the LLM
    model_kwargs = {}
    if model:
        model_kwargs["model"] = model
    
    response = llm.query(prompt, **model_kwargs, **clean_kwargs)
    
    return response