"""Generator for data relationship tests."""
from typing import Dict, Any, List, Optional, Set, Tuple, cast
import pandas as pd
import numpy as np

from .base import BaseTestGenerator, register_generator

@register_generator
class RelationshipTestGenerator(BaseTestGenerator):
    """Generator for data relationship tests."""
    
    def generate_tests(self, df: pd.DataFrame, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Generate tests for data relationships.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of test specifications
        """
        tests: List[Dict[str, Any]] = []
        
        # Only proceed if we have enough data
        if len(df) < 10:
            return tests
            
        # Identify numeric columns for correlation tests
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Find strongly correlated pairs of numeric columns
        if len(numeric_cols) >= 2:
            correlated_pairs = self._find_correlated_pairs(df[numeric_cols])
            
            # Generate tests for strongly correlated columns
            for col1, col2, corr in correlated_pairs:
                # Use absolute correlation for test threshold (allow it to weaken by 0.2)
                corr_abs = abs(corr)
                min_corr_abs = max(0.5, corr_abs - 0.2)  # Don't go below 0.5
                
                # Adjust sign based on original correlation
                sign = ">" if corr > 0 else "<"
                
                tests.append({
                    "type": "relationship",
                    "subtype": "correlation",
                    "name": f"test_{col1}_{col2}_correlation",
                    "description": f"Test that columns '{col1}' and '{col2}' maintain their {corr:.2f} correlation",
                    "test_code": f"# Calculate correlation between {col1} and {col2}\ncorr = df['{col1}'].corr(df['{col2}'])\n# Check if correlation is still {sign} 0 and strong enough\nassert {'corr ' + sign + ' 0 and abs(corr)' if corr_abs > 0.5 else 'abs(corr)'} >= {min_corr_abs}, f\"Correlation between '{col1}' and '{col2}' has changed significantly. Expected: {corr:.2f}, Got: {{corr:.2f}}\"",
                    "severity": "medium",
                    "column": f"{col1}, {col2}",
                    "parameters": {
                        "columns": [col1, col2],
                        "expected_correlation": float(corr),
                        "min_correlation_abs": float(min_corr_abs)
                    }
                })
        
        # Find potential primary key columns (high cardinality, few duplicates)
        potential_id_columns = self._find_potential_id_columns(df, metadata)
        
        # Generate tests for potential ID columns
        for col in potential_id_columns:
            tests.append({
                "type": "relationship",
                "subtype": "unique_values",
                "name": f"test_{col}_uniqueness",
                "description": f"Test that column '{col}' contains unique values (potential ID column)",
                "test_code": f"# Check if {col} contains unique values\nassert df['{col}'].is_unique, f\"Column '{col}' contains duplicate values\"",
                "severity": "high",
                "column": col,
                "parameters": {
                    "column": col
                }
            })
        
        return tests
    
    def _find_correlated_pairs(self, df_numeric: pd.DataFrame, threshold: float = 0.7) -> List[Tuple[str, str, float]]:
        """
        Find pairs of columns with strong correlations.
        
        Args:
            df_numeric: DataFrame with only numeric columns
            threshold: Correlation threshold (absolute value)
            
        Returns:
            List of tuples (column1, column2, correlation)
        """
        # Calculate correlation matrix
        corr_matrix = df_numeric.corr()
        
        # Find pairs with strong correlations
        pairs: List[Tuple[str, str, float]] = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):  # Upper triangle only
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_val = corr_matrix.iloc[i, j]
                
                if abs(corr_val) >= threshold:
                    pairs.append((str(col1), str(col2), float(corr_val)))
        
        # Return pairs sorted by absolute correlation (strongest first)
        return sorted(pairs, key=lambda x: abs(x[2]), reverse=True)
    
    def _find_potential_id_columns(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> List[str]:
        """
        Find columns that might be IDs or primary keys.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            
        Returns:
            List of potential ID column names
        """
        potential_ids: List[str] = []
        
        for column, details in metadata["columns"].items():
            # Criteria for potential ID columns:
            # 1. High cardinality (unique count close to row count)
            # 2. Few or no nulls
            # 3. Name suggests ID ('id', 'key', 'code' in name)
            
            unique_count = details.get("unique_count", 0)
            null_count = details.get("nulls", 0)
            total_rows = metadata.get("total_rows", len(df))
            
            # Check unique ratio (at least 90% unique)
            unique_ratio = unique_count / (total_rows - null_count) if (total_rows - null_count) > 0 else 0
            
            # Check if name suggests ID
            name_suggests_id = any(id_term in column.lower() for id_term in ['id', 'key', 'code', 'uuid', 'guid'])
            
            # Add to potential IDs if criteria met
            if (unique_ratio >= 0.9 and null_count == 0) or (name_suggests_id and unique_ratio >= 0.8):
                potential_ids.append(column)
        
        return potential_ids