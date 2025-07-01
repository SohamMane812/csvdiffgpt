"""Analyzer for identifying redundant columns in CSV data."""
from typing import Dict, Any, List, Optional, Tuple, Set
import pandas as pd
import numpy as np

from .base import BaseRestructureAnalyzer, register_analyzer

@register_analyzer
class RedundancyAnalyzer(BaseRestructureAnalyzer):
    """Analyzer for identifying redundant columns in CSV data."""
    
    def analyze(self, df: pd.DataFrame, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Analyze the data for redundant columns.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of restructuring recommendations
        """
        recommendations: List[Dict[str, Any]] = []
        min_similarity = kwargs.get("min_similarity", 0.9)  # Threshold for similarity
        
        # 1. Identify duplicate columns (identical content)
        duplicate_cols = self._find_duplicate_columns(df)
        
        for col_group in duplicate_cols:
            if len(col_group) > 1:
                keep_col = col_group[0]  # Keep the first column by default
                drop_cols = col_group[1:]
                
                recommendations.append({
                    "type": "redundancy",
                    "subtype": "duplicate_columns",
                    "name": f"remove_duplicate_columns_{keep_col}",
                    "description": f"Columns {drop_cols} are duplicates of '{keep_col}' and can be removed",
                    "severity": "high",
                    "columns": col_group,
                    "action": "drop_columns",
                    "details": {
                        "keep_column": keep_col,
                        "drop_columns": drop_cols
                    },
                    "sql_code": f"-- Remove duplicate columns\n-- Original data is kept in '{keep_col}'\nALTER TABLE your_table DROP COLUMN {', DROP COLUMN '.join(drop_cols)};",
                    "python_code": f"# Remove duplicate columns\n# Original data is kept in '{keep_col}'\ndf = df.drop(columns={drop_cols})"
                })
        
        # 2. Identify highly correlated numeric columns
        if len(df.select_dtypes(include=[np.number]).columns) >= 2:
            correlated_pairs = self._find_highly_correlated_columns(df, min_similarity)
            
            for col1, col2, corr in correlated_pairs:
                # Only suggest dropping one if correlation is very high (> 0.95)
                if abs(corr) > 0.95:
                    recommendations.append({
                        "type": "redundancy",
                        "subtype": "correlated_columns",
                        "name": f"consider_removing_{col2}",
                        "description": f"Columns '{col1}' and '{col2}' are highly correlated ({corr:.2f}), consider removing one",
                        "severity": "medium",
                        "columns": [col1, col2],
                        "action": "evaluate_correlation",
                        "details": {
                            "correlation": corr,
                            "suggested_action": f"Consider whether both columns provide unique information or if '{col2}' can be derived from '{col1}'"
                        },
                        "sql_code": f"-- Columns '{col1}' and '{col2}' are highly correlated ({corr:.2f})\n-- Evaluate whether to keep both\n-- ALTER TABLE your_table DROP COLUMN {col2};  -- Only if redundant",
                        "python_code": f"# Columns '{col1}' and '{col2}' are highly correlated ({corr:.2f})\n# Evaluate whether to keep both\n# df = df.drop(columns=['{col2}'])  # Only if redundant"
                    })
                else:
                    # Just inform about the correlation
                    recommendations.append({
                        "type": "redundancy",
                        "subtype": "correlated_columns",
                        "name": f"note_correlation_{col1}_{col2}",
                        "description": f"Columns '{col1}' and '{col2}' are correlated ({corr:.2f}), but may contain unique information",
                        "severity": "low",
                        "columns": [col1, col2],
                        "action": "note_correlation",
                        "details": {
                            "correlation": corr
                        },
                        "sql_code": f"-- Note: Columns '{col1}' and '{col2}' are correlated ({corr:.2f})",
                        "python_code": f"# Note: Columns '{col1}' and '{col2}' are correlated ({corr:.2f})"
                    })
        
        # 3. Identify columns with low information content
        constant_cols = self._find_near_constant_columns(df, metadata)
        
        for col, unique_pct in constant_cols:
            recommendations.append({
                "type": "redundancy",
                "subtype": "constant_column",
                "name": f"consider_removing_{col}",
                "description": f"Column '{col}' has very low variability (only {unique_pct:.1f}% unique values), consider removing",
                "severity": "low",
                "columns": [col],
                "action": "evaluate_usefulness",
                "details": {
                    "unique_percentage": unique_pct,
                    "suggested_action": f"Evaluate whether column '{col}' provides useful information"
                },
                "sql_code": f"-- Column '{col}' has low information content\n-- ALTER TABLE your_table DROP COLUMN {col};  -- Only if not needed",
                "python_code": f"# Column '{col}' has low information content\n# df = df.drop(columns=['{col}'])  # Only if not needed"
            })
        
        return recommendations
    
    def _find_duplicate_columns(self, df: pd.DataFrame) -> List[List[str]]:
        """
        Find columns with identical content.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            List of column groups where columns within each group are duplicates
        """
        # Hash each column to find duplicates efficiently
        duplicates: Dict[int, List[str]] = {}
        
        # Process each column
        for col in df.columns:
            # Convert to string hash to handle different types
            col_hash = hash(tuple(df[col].astype(str).fillna('NA').values))
            
            if col_hash in duplicates:
                duplicates[col_hash].append(col)
            else:
                duplicates[col_hash] = [col]
        
        # Return only the groups with more than one column (actual duplicates)
        return [cols for cols in duplicates.values() if len(cols) > 1]
    
    def _find_highly_correlated_columns(self, df: pd.DataFrame, threshold: float = 0.9) -> List[Tuple[str, str, float]]:
        """
        Find pairs of numeric columns with high correlation.
        
        Args:
            df: Pandas DataFrame
            threshold: Correlation threshold (absolute value)
            
        Returns:
            List of tuples (column1, column2, correlation)
        """
        # Get numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        
        # If not enough numeric columns, return empty list
        if len(numeric_df.columns) < 2:
            return []
        
        # Calculate correlation matrix
        corr_matrix = numeric_df.corr()
        
        # Find pairs with high correlation
        pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):  # Upper triangle only
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr = corr_matrix.iloc[i, j]
                
                if not pd.isna(corr) and abs(corr) >= threshold:
                    pairs.append((col1, col2, corr))
        
        # Return pairs sorted by absolute correlation (strongest first)
        return sorted(pairs, key=lambda x: abs(x[2]), reverse=True)
    
    def _find_near_constant_columns(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> List[Tuple[str, float]]:
        """
        Find columns with very low variability (almost constant).
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary with column information
            
        Returns:
            List of tuples (column_name, unique_percentage)
        """
        constant_cols = []
        
        # Use metadata to find columns with low cardinality relative to row count
        for col, details in metadata.get("columns", {}).items():
            # Skip columns with high null percentage
            if details.get("null_percentage", 0) > 50:
                continue
                
            unique_count = details.get("unique_count", 0)
            total_rows = metadata.get("total_rows", len(df))
            
            if total_rows > 0 and unique_count > 0:
                unique_pct = (unique_count / total_rows) * 100
                
                # Consider a column "near-constant" if it has very few unique values
                # relative to the row count (less than 0.5%)
                if 0 < unique_pct < 0.5:
                    constant_cols.append((col, unique_pct))
        
        return constant_cols