"""Generator for schema validation tests."""
from typing import Dict, Any, List, Optional, cast
import pandas as pd

from .base import BaseTestGenerator, register_generator

@register_generator
class SchemaTestGenerator(BaseTestGenerator):
    """Generator for schema validation tests."""
    
    def generate_tests(self, df: pd.DataFrame, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Generate schema validation tests.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of test specifications
        """
        tests: List[Dict[str, Any]] = []
        
        # Test for expected column count
        tests.append({
            "type": "schema",
            "subtype": "column_count",
            "name": "test_column_count",
            "description": f"Test that the DataFrame has the expected number of columns ({len(df.columns)})",
            "test_code": f"assert len(df.columns) == {len(df.columns)}, f\"Expected {len(df.columns)} columns, got {{len(df.columns)}}\"",
            "severity": "critical",
            "column": None,
            "parameters": {
                "expected_count": len(df.columns)
            }
        })
        
        # Test for expected columns
        column_list_str = ", ".join([f"'{col}'" for col in df.columns])
        tests.append({
            "type": "schema",
            "subtype": "column_names",
            "name": "test_expected_columns",
            "description": "Test that all expected columns are present",
            "test_code": f"expected_columns = [{column_list_str}]\nfor col in expected_columns:\n    assert col in df.columns, f\"Expected column {{col}} missing from DataFrame\"",
            "severity": "critical",
            "column": None,
            "parameters": {
                "expected_columns": list(df.columns)
            }
        })
        
        # Test for column data types
        for column, details in metadata["columns"].items():
            col_type = details.get("type", "")
            
            # Convert pandas dtype to Python type
            python_type = "str"
            if "int" in col_type:
                python_type = "int"
            elif "float" in col_type:
                python_type = "float"
            elif "bool" in col_type:
                python_type = "bool"
            elif "datetime" in col_type:
                python_type = "pd.Timestamp"
            
            # Skip check for columns with high null percentage
            null_pct = details.get("null_percentage", 0)
            if null_pct > 50:
                continue
                
            tests.append({
                "type": "schema",
                "subtype": "column_type",
                "name": f"test_{column}_dtype",
                "description": f"Test that column '{column}' has the expected data type ({col_type})",
                "test_code": f"# Check type for non-null values\nnon_null_values = df['{column}'].dropna()\nassert len(non_null_values) > 0, \"No non-null values to check type for\"\n# Check if first non-null value has expected type\nfirst_value = non_null_values.iloc[0]\nassert isinstance(first_value, {python_type}) or pd.isna(first_value), f\"Expected {python_type} type for '{column}', got {{type(first_value).__name__}}\"",
                "severity": "high",
                "column": column,
                "parameters": {
                    "expected_type": col_type
                }
            })
        
        return tests