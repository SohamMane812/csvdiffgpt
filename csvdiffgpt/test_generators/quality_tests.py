"""Generator for data quality tests."""
from typing import Dict, Any, List, Optional, cast
import pandas as pd

from .base import BaseTestGenerator, register_generator

@register_generator
class QualityTestGenerator(BaseTestGenerator):
    """Generator for data quality tests."""
    
    def generate_tests(self, df: pd.DataFrame, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Generate data quality tests.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of test specifications
        """
        tests: List[Dict[str, Any]] = []
        null_threshold = kwargs.get("null_threshold", 5.0)
        
        # Test for expected row count (with some tolerance)
        total_rows = metadata.get("total_rows", 0)
        if total_rows > 0:
            # Allow for a 10% change in row count
            min_rows = int(total_rows * 0.9)
            max_rows = int(total_rows * 1.1)
            
            tests.append({
                "type": "quality",
                "subtype": "row_count",
                "name": "test_row_count_in_expected_range",
                "description": f"Test that the DataFrame has a reasonable number of rows (expected around {total_rows})",
                "test_code": f"row_count = len(df)\nassert {min_rows} <= row_count <= {max_rows}, f\"Row count {{row_count}} is outside the expected range ({min_rows}-{max_rows})\"",
                "severity": "high",
                "column": None,
                "parameters": {
                    "min_rows": min_rows,
                    "max_rows": max_rows
                }
            })
        
        # Test for duplicate rows
        tests.append({
            "type": "quality",
            "subtype": "duplicates",
            "name": "test_no_duplicate_rows",
            "description": "Test that the DataFrame has no duplicate rows",
            "test_code": "assert df.duplicated().sum() == 0, f\"Found {df.duplicated().sum()} duplicate rows\"",
            "severity": "medium",
            "column": None,
            "parameters": {}
        })
        
        # Test for null values in key columns
        for column, details in metadata["columns"].items():
            # If this column had no nulls originally, we should ensure it stays that way
            if details.get("nulls", 0) == 0:
                tests.append({
                    "type": "quality",
                    "subtype": "no_nulls",
                    "name": f"test_{column}_no_nulls",
                    "description": f"Test that column '{column}' has no null values",
                    "test_code": f"assert df['{column}'].isna().sum() == 0, f\"Found {{df['{column}'].isna().sum()}} null values in '{column}'\"",
                    "severity": "high",
                    "column": column,
                    "parameters": {}
                })
            # If this column had some nulls but below threshold, ensure it doesn't get worse
            elif details.get("null_percentage", 0) < null_threshold:
                max_null_pct = details.get("null_percentage", 0) + 2.0  # Allow 2% more nulls
                tests.append({
                    "type": "quality",
                    "subtype": "limited_nulls",
                    "name": f"test_{column}_limited_nulls",
                    "description": f"Test that column '{column}' has limited null values (max {max_null_pct:.1f}%)",
                    "test_code": f"null_pct = df['{column}'].isna().mean() * 100\nassert null_pct <= {max_null_pct}, f\"Found {{null_pct:.1f}}% null values in '{column}', exceeding limit of {max_null_pct:.1f}%\"",
                    "severity": "medium",
                    "column": column,
                    "parameters": {
                        "max_null_percentage": float(max_null_pct)
                    }
                })
        
        # Test for outliers in numeric columns
        for issue in validation_results["issues"].get("outliers", []):
            column = issue["column"]
            # Use standard Python conditional expression
            outlier_threshold = 4.0 if issue.get("severity", "medium") == "high" else 3.0
            outlier_pct_plus_buffer = float(issue.get("outlier_percentage", 0)) + 1.0
            
            tests.append({
                "type": "quality",
                "subtype": "outliers",
                "name": f"test_{column}_limited_outliers",
                "description": f"Test that column '{column}' has limited outliers",
                "test_code": f"# Calculate z-scores\nmean = df['{column}'].mean()\nstd = df['{column}'].std()\nif std > 0:  # Avoid division by zero\n    z_scores = np.abs((df['{column}'] - mean) / std)\n    outlier_pct = (z_scores > {outlier_threshold}).mean() * 100\n    # Allow up to 1% more outliers than originally detected\n    max_pct = {outlier_pct_plus_buffer}\n    assert outlier_pct <= max_pct, f\"Found {{outlier_pct:.2f}}% outliers in '{column}', exceeding limit of {{max_pct:.2f}}%\"",
                "severity": "medium",
                "column": column,
                "parameters": {
                    "outlier_threshold": float(outlier_threshold),
                    "max_percentage": outlier_pct_plus_buffer
                }
            })
        
        return tests