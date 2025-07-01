"""Generator for value validation tests."""
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from .base import BaseTestGenerator, register_generator

@register_generator
class ValueTestGenerator(BaseTestGenerator):
    """Generator for value validation tests."""
    
    def generate_tests(self, df: pd.DataFrame, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Generate value validation tests.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of test specifications
        """
        tests = []
        
        # Generate tests for each numeric column
        for column, details in metadata["columns"].items():
            col_type = details.get("type", "")
            
            # Value range tests for numeric columns
            if np.issubdtype(np.dtype(col_type), np.number):
                # Only generate if min and max are available
                if "min" in details and "max" in details:
                    min_val = details["min"]
                    max_val = details["max"]
                    
                    # Allow for a small buffer (5% on each side)
                    buffer = (max_val - min_val) * 0.05 if max_val > min_val else 1.0
                    min_test = min_val - buffer
                    max_test = max_val + buffer
                    
                    # Test for minimum value
                    tests.append({
                        "type": "value",
                        "subtype": "minimum",
                        "name": f"test_{column}_minimum",
                        "description": f"Test that values in column '{column}' are not below the expected minimum ({min_val})",
                        "test_code": f"min_val = df['{column}'].min()\nassert min_val >= {min_test}, f\"Minimum value {{min_val}} is below the expected minimum {min_test}\"",
                        "severity": "high",
                        "column": column,
                        "parameters": {
                            "min_expected": float(min_test)
                        }
                    })
                    
                    # Test for maximum value
                    tests.append({
                        "type": "value",
                        "subtype": "maximum",
                        "name": f"test_{column}_maximum",
                        "description": f"Test that values in column '{column}' are not above the expected maximum ({max_val})",
                        "test_code": f"max_val = df['{column}'].max()\nassert max_val <= {max_test}, f\"Maximum value {{max_val}} is above the expected maximum {max_test}\"",
                        "severity": "high",
                        "column": column,
                        "parameters": {
                            "max_expected": float(max_test)
                        }
                    })
            
            # String length tests for string columns
            elif col_type == "object" and "min_length" in details and "max_length" in details:
                min_length = details["min_length"]
                max_length = details["max_length"]
                
                # Allow for a small buffer
                max_length_test = max_length + int(max_length * 0.1) + 1
                
                tests.append({
                    "type": "value",
                    "subtype": "string_length",
                    "name": f"test_{column}_string_length",
                    "description": f"Test that strings in column '{column}' are not too long (max: {max_length})",
                    "test_code": f"# Check string length for non-null values\nnon_null = df['{column}'].dropna()\nif len(non_null) > 0:\n    max_len = non_null.astype(str).str.len().max()\n    assert max_len <= {max_length_test}, f\"Maximum string length {{max_len}} is above the expected maximum {max_length_test}\"",
                    "severity": "medium",
                    "column": column,
                    "parameters": {
                        "max_length": max_length_test
                    }
                })
            
            # Category value tests for columns with few unique values
            if "value_distribution" in details:
                # Get the allowed values
                valid_values = list(details["value_distribution"].keys())
                
                # If there are a reasonable number of values (not too many)
                if len(valid_values) <= 20:
                    valid_values_str = ", ".join([f"'{v}'" for v in valid_values])
                    tests.append({
                        "type": "value",
                        "subtype": "categorical",
                        "name": f"test_{column}_valid_values",
                        "description": f"Test that values in column '{column}' are within the expected set of values",
                        "test_code": f"# Get unique non-null values\nvalues = df['{column}'].dropna().unique()\n# Convert to strings for comparison\nvalues_str = [str(v) for v in values]\n# Expected values\nvalid_values = [{valid_values_str}]\n# Check if there are any unexpected values\nunexpected = [v for v in values_str if v not in valid_values]\nassert len(unexpected) == 0, f\"Found {{len(unexpected)}} unexpected values in '{column}'\"",
                        "severity": "high",
                        "column": column,
                        "parameters": {
                            "valid_values": valid_values
                        }
                    })
        
        return tests