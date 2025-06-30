"""CSV file preprocessing and analysis."""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union
import json
from ..core.utils import detect_separator, get_file_size_mb

class CSVPreprocessor:
    """
    Preprocesses CSV files to extract metadata and sample information.
    """
    
    def __init__(
        self, 
        file_path: str, 
        sep: Optional[str] = None,
        max_rows_analyzed: int = 150000,
        max_cols_analyzed: Optional[int] = None
    ):
        """
        Initialize the preprocessor with file path and analysis parameters.
        
        Args:
            file_path: Path to the CSV file
            sep: Separator character (auto-detected if None)
            max_rows_analyzed: Maximum number of rows to analyze
            max_cols_analyzed: Maximum number of columns to analyze
        """
        self.file_path = file_path
        self.sep = sep if sep else detect_separator(file_path)
        self.max_rows_analyzed = max_rows_analyzed
        self.max_cols_analyzed = max_cols_analyzed
        self.file_size_mb = get_file_size_mb(file_path)
        self.df: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, Any] = {}
    
    def load_data(self) -> None:
        """
        Load the CSV file into a pandas DataFrame with appropriate sampling.
        """
        # For large files, use sampling
        if self.file_size_mb > 100:  # If file is larger than 100MB
            # First load just the header to get column names
            df_header = pd.read_csv(self.file_path, sep=self.sep, nrows=0)
            total_cols = len(df_header.columns)
            
            # Now load with sampling
            if self.max_cols_analyzed and self.max_cols_analyzed < total_cols:
                # Select a subset of columns if needed
                cols_to_use = list(df_header.columns[:self.max_cols_analyzed])
                self.df = pd.read_csv(
                    self.file_path, 
                    sep=self.sep, 
                    usecols=cols_to_use,
                    nrows=self.max_rows_analyzed
                )
            else:
                self.df = pd.read_csv(
                    self.file_path, 
                    sep=self.sep, 
                    nrows=self.max_rows_analyzed
                )
        else:
            # For smaller files, load normally
            self.df = pd.read_csv(self.file_path, sep=self.sep)
            
            # Apply column limit if specified
            if self.max_cols_analyzed and len(self.df.columns) > self.max_cols_analyzed:
                self.df = self.df.iloc[:, :self.max_cols_analyzed]
            
            # Apply row limit if specified
            if len(self.df) > self.max_rows_analyzed:
                self.df = self.df.iloc[:self.max_rows_analyzed]
    
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze the CSV file and return a metadata dictionary.
        
        Returns:
            A dictionary containing metadata about the CSV file
        """
        if self.df is None:
            self.load_data()
        
        # Ensure df is not None
        if self.df is None:
            raise ValueError("Failed to load DataFrame")
        
        # Basic metadata
        shape = self.df.shape
        
        # Get row count of the actual file (not just the sample)
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                row_count = sum(1 for _ in f) - 1  # Subtract header row
        except:
            # Fall back to sample size if we can't count all rows
            row_count = shape[0]
        
        # Initialize metadata
        self.metadata = {
            "file_path": self.file_path,
            "file_size_mb": round(self.file_size_mb, 2),
            "separator": self.sep,
            "total_rows": row_count,
            "total_columns": shape[1],
            "analyzed_rows": min(shape[0], self.max_rows_analyzed),
            "analyzed_columns": shape[1],
            "columns": {},
            "sample_provided": shape[0] < row_count
        }
        
        # Column analysis
        for col in self.df.columns:
            col_data = self.df[col]
            col_type = str(col_data.dtype)
            
            # Prepare column metadata
            col_meta: Dict[str, Any] = {
                "type": col_type,
                "nulls": int(col_data.isna().sum()),
                "null_percentage": round(col_data.isna().mean() * 100, 2),
                "unique_count": int(col_data.nunique())
            }
            
            # Add stats based on data type
            if np.issubdtype(col_data.dtype, np.number):
                # Numeric columns
                col_meta.update({
                    "min": col_data.min() if not pd.isna(col_data.min()) else None,
                    "max": col_data.max() if not pd.isna(col_data.max()) else None,
                    "mean": round(float(col_data.mean()), 2) if not pd.isna(col_data.mean()) else None,
                    "median": round(float(col_data.median()), 2) if not pd.isna(col_data.median()) else None,
                    "std": round(float(col_data.std()), 2) if not pd.isna(col_data.std()) else None
                })
            elif col_data.dtype == 'object' or col_data.dtype == 'string':
                # String columns
                non_null_values = col_data.dropna()
                if len(non_null_values) > 0:
                    col_meta.update({
                        "min_length": min(non_null_values.str.len()),
                        "max_length": max(non_null_values.str.len()),
                        "avg_length": round(float(non_null_values.str.len().mean()), 2)
                    })
            
            # Add sample values (max 5)
            try:
                non_null_sample = col_data.dropna().sample(min(5, col_data.nunique())).tolist()
                col_meta["examples"] = non_null_sample
            except:
                # If sampling fails, get first few non-null values
                non_null_sample = col_data.dropna().iloc[:5].tolist()
                col_meta["examples"] = non_null_sample
            
            # Add top values for categorical-like columns
            if col_meta["unique_count"] < 20 and col_meta["unique_count"] > 0:
                value_counts = col_data.value_counts(normalize=True).head(10).to_dict()
                col_meta["value_distribution"] = {str(k): round(float(v) * 100, 2) for k, v in value_counts.items()}
            
            # Store column metadata
            self.metadata["columns"][col] = col_meta
        
        return self.metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get the metadata as a dictionary.
        
        Returns:
            A dictionary of metadata
        """
        if not self.metadata:
            self.analyze()
        return self.metadata
    
    def to_json(self) -> str:
        """
        Get the metadata as a JSON string.
        
        Returns:
            A JSON string of metadata
        """
        return json.dumps(self.to_dict(), indent=2, default=str)