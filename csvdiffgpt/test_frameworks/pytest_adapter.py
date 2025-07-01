"""Adapter for formatting tests as pytest code."""
from typing import Dict, Any, List, Optional, Callable
import os

from .base import BaseTestFramework, register_framework

@register_framework
class PytestAdapter(BaseTestFramework):
    """Adapter for formatting tests as pytest code."""
    
    def format_tests(self, tests: List[Dict[str, Any]], metadata: Dict[str, Any], **kwargs) -> str:
        """
        Format test specifications into pytest code.
        
        Args:
            tests: List of test specifications
            metadata: Metadata dictionary
            **kwargs: Additional parameters
            
        Returns:
            Formatted test code as a string
        """
        # Sort tests by type and severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        
        # Fix: Handle None values in sorting key by providing default empty string
        def sort_key(test: Dict[str, Any]) -> tuple:
            test_type = test.get("type", "")
            severity = severity_order.get(test.get("severity", "medium"), 4)
            # Convert column to string or empty string if None
            column = test.get("column", "")
            column = str(column) if column is not None else ""
            return (test_type, severity, column)
        
        sorted_tests = sorted(tests, key=sort_key)
        
        # Group tests by type
        grouped_tests: Dict[str, List[Dict[str, Any]]] = {}
        for test in sorted_tests:
            test_type = test.get("type", "other")
            if test_type not in grouped_tests:
                grouped_tests[test_type] = []
            grouped_tests[test_type].append(test)
        
        # Build the test file
        file_content = []
        
        # Add imports
        file_content.append(self.generate_imports())
        file_content.append("")
        
        # Add setup code
        file_path = kwargs.get("file_path", "data.csv")
        file_content.append(self.generate_setup(file_path, metadata))
        file_content.append("")
        
        # Add test classes for each type
        for test_type, type_tests in grouped_tests.items():
            # Convert test_type to CamelCase for class name
            class_name = "".join(word.capitalize() for word in test_type.split("_")) + "Tests"
            
            file_content.append(f"class Test{class_name}:")
            file_content.append(f"    \"\"\"Tests for {test_type} validation.\"\"\"")
            file_content.append("")
            
            # Add individual test methods
            for test in type_tests:
                test_name = test.get("name", "").replace("test_", "")
                
                # Fix: Ensure test name is valid
                if not test_name:
                    continue
                
                # Add method docstring
                file_content.append(f"    def {test.get('name', 'test_unnamed')}(self, df):")
                file_content.append(f"        \"\"\"{test.get('description', 'No description provided')}\"\"\"")
                
                # Add test code (properly indented)
                test_code = test.get("test_code", "pass  # No test code provided")
                test_code_lines = test_code.split("\n")
                for line in test_code_lines:
                    file_content.append(f"        {line}")
                
                # Add empty line between tests
                file_content.append("")
        
        return "\n".join(file_content)
    
    def generate_imports(self, **kwargs) -> str:
        """
        Generate import statements needed for pytest.
        
        Args:
            **kwargs: Additional parameters
            
        Returns:
            Import statements as a string
        """
        return "import pytest\nimport pandas as pd\nimport numpy as np"
    
    def generate_setup(self, file_path: str, metadata: Dict[str, Any], **kwargs) -> str:
        """
        Generate setup code needed for pytest.
        
        Args:
            file_path: Path to the CSV file
            metadata: Metadata dictionary
            **kwargs: Additional parameters
            
        Returns:
            Setup code as a string
        """
        separator = metadata.get("separator", ",")
        
        setup_code = [
            "@pytest.fixture",
            "def df():",
            f"    \"\"\"Load the CSV file into a pandas DataFrame.\"\"\"",
            f"    # Load the CSV file",
            f"    return pd.read_csv('{os.path.basename(file_path)}', sep='{separator}')"
        ]
        
        return "\n".join(setup_code)