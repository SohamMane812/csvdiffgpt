"""Adapter for formatting tests as dbt tests."""
from typing import Dict, Any, List, Optional, Union, cast
import os
import yaml

from .base import BaseTestFramework, register_framework

@register_framework
class DbtAdapter(BaseTestFramework):
    """Adapter for formatting tests as dbt tests."""
    
    def format_tests(self, tests: List[Dict[str, Any]], metadata: Dict[str, Any], **kwargs) -> str:
        """
        Format test specifications into dbt test YAML.
        
        Args:
            tests: List of test specifications
            metadata: Metadata dictionary
            **kwargs: Additional parameters
            
        Returns:
            Formatted test YAML as a string
        """
        # Create the schema YAML for dbt
        model_name = kwargs.get("model_name", os.path.splitext(os.path.basename(kwargs.get("file_path", "data.csv")))[0])
        
        # Structure for dbt schema.yml
        schema: Dict[str, Any] = {
            "version": 2,
            "models": [
                {
                    "name": model_name,
                    "description": f"Tests for {model_name} table/view",
                    "columns": []
                }
            ]
        }
        
        # Track columns that already have entries
        column_entries: Dict[str, Dict[str, Any]] = {}
        
        # Process each test
        for test in tests:
            column_name = test.get("column")
            
            # Skip tests that don't map well to dbt
            if test.get("type") == "relationship" and test.get("subtype") == "correlation":
                continue
                
            if column_name and "," in str(column_name):  # Skip multi-column tests
                continue
                
            # Handle tests for specific columns
            if column_name and column_name not in ["None", "null", None]:
                col_name_str = str(column_name)  # Ensure it's a string
                
                # Create or get column entry
                if col_name_str not in column_entries:
                    column_entries[col_name_str] = {
                        "name": col_name_str,
                        "description": f"Column '{col_name_str}'",
                        "tests": []
                    }
                
                # Add the test based on type
                dbt_test = self._convert_test_to_dbt(test)
                if dbt_test:
                    # Get the tests list from the column entry
                    column_tests = column_entries[col_name_str].get("tests", [])
                    if not isinstance(column_tests, list):
                        column_tests = []
                    
                    # Add the test
                    column_tests.append(dbt_test)
                    
                    # Update the column entry
                    column_entries[col_name_str]["tests"] = column_tests
            
            # Handle table-level tests
            elif test.get("type") == "schema" and test.get("subtype") in ["column_count", "column_names"]:
                # Ensure the tests key exists in the model
                if "tests" not in schema["models"][0]:
                    schema["models"][0]["tests"] = []
                
                # Get model tests as a list
                model_tests = schema["models"][0]["tests"]
                if not isinstance(model_tests, list):
                    model_tests = []
                
                # Add the test
                dbt_test = self._convert_test_to_dbt(test)
                if dbt_test:
                    if isinstance(dbt_test, dict):
                        model_tests.append(dbt_test)
                    else:
                        # For simple string tests
                        model_tests.append(dbt_test)
                
                # Update model tests
                schema["models"][0]["tests"] = model_tests
        
        # Add column entries to schema
        schema["models"][0]["columns"] = list(column_entries.values())
        
        # Convert to YAML
        yaml_str = yaml.dump(schema, sort_keys=False, default_flow_style=False)
        
        # Add comments and instructions
        result = [
            "# dbt Schema Tests",
            "# Save this file as schema.yml in your dbt models directory",
            "# For more information on dbt tests, see: https://docs.getdbt.com/docs/building-a-dbt-project/tests",
            "",
            yaml_str
        ]
        
        return "\n".join(result)
    
    def generate_imports(self, **kwargs) -> str:
        """
        Generate import statements needed for dbt.
        
        Args:
            **kwargs: Additional parameters
            
        Returns:
            Import statements as a string
        """
        return "# No imports needed for dbt YAML files"
    
    def generate_setup(self, file_path: str, metadata: Dict[str, Any], **kwargs) -> str:
        """
        Generate setup code needed for dbt.
        
        Args:
            file_path: Path to the CSV file
            metadata: Metadata dictionary
            **kwargs: Additional parameters
            
        Returns:
            Setup code as a string
        """
        return "# No setup code needed for dbt YAML files"
    
    def _convert_test_to_dbt(self, test: Dict[str, Any]) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Convert a test specification to a dbt test.
        
        Args:
            test: Test specification
            
        Returns:
            dbt test specification or None if not convertible
        """
        test_type = test.get("type")
        subtype = test.get("subtype")
        column = test.get("column")
        
        # Schema tests
        if test_type == "schema":
            if subtype == "column_names":
                # For expected columns, we use dbt_utils.equal_rowcount
                return None  # Not directly translatable
            
            elif subtype == "column_count":
                # Not directly translatable to dbt
                return None
            
            elif subtype == "column_type" and column:
                # Not directly translatable to standard dbt
                return None
        
        # Value tests
        elif test_type == "value" and column:
            if subtype == "minimum":
                min_val = cast(Dict[str, Any], test.get("parameters", {})).get("min_expected")
                if min_val is not None:
                    return {"accepted_values": {"values": f">= {min_val}"}}
            
            elif subtype == "maximum":
                max_val = cast(Dict[str, Any], test.get("parameters", {})).get("max_expected")
                if max_val is not None:
                    return {"accepted_values": {"values": f"<= {max_val}"}}
            
            elif subtype == "categorical":
                values = cast(Dict[str, Any], test.get("parameters", {})).get("valid_values")
                if values:
                    return {"accepted_values": {"values": values}}
            
            elif subtype == "string_length":
                max_length = cast(Dict[str, Any], test.get("parameters", {})).get("max_length")
                if max_length is not None:
                    return {"string_length": {"max_length": max_length}}
        
        # Quality tests
        elif test_type == "quality":
            if subtype == "no_nulls" and column:
                return "not_null"
            
            elif subtype == "limited_nulls" and column:
                # Not directly translatable to standard dbt
                return None
            
            elif subtype == "duplicates":
                return "unique"
        
        # Relationship tests
        elif test_type == "relationship" and column:
            if subtype == "unique_values":
                return "unique"
        
        # Return None if we couldn't convert this test
        return None