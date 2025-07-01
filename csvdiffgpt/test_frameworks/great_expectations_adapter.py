"""Adapter for formatting tests as Great Expectations expectations."""
from typing import Dict, Any, List, Optional
import os
import json

from .base import BaseTestFramework, register_framework

# Register with both naming conventions to ensure compatibility
@register_framework
class GreatExpectationsAdapter(BaseTestFramework):
    """Adapter for formatting tests as Great Expectations expectations."""
    
    def format_tests(self, tests: List[Dict[str, Any]], metadata: Dict[str, Any], **kwargs) -> str:
        """
        Format test specifications into Great Expectations expectations.
        
        Args:
            tests: List of test specifications
            metadata: Metadata dictionary
            **kwargs: Additional parameters
            
        Returns:
            Formatted expectations as a string
        """
        # Build the script to create expectations
        file_content = []
        
        # Add imports
        file_content.append(self.generate_imports())
        file_content.append("")
        
        # Add setup code
        file_path = kwargs.get("file_path", "data.csv")
        file_content.append(self.generate_setup(file_path, metadata))
        file_content.append("")
        
        # Add expectations
        file_content.append("# Add expectations")
        
        for test in tests:
            expectation = self._convert_test_to_expectation(test)
            if expectation:
                file_content.append(expectation)
        
        # Add code to save the expectation suite
        file_content.append("")
        file_content.append("# Save the expectation suite")
        file_content.append("context.save_expectation_suite(expectation_suite)")
        file_content.append("")
        file_content.append("print('Expectation suite created successfully!')")
        
        return "\n".join(file_content)
    
    def generate_imports(self, **kwargs) -> str:
        """
        Generate import statements needed for Great Expectations.
        
        Args:
            **kwargs: Additional parameters
            
        Returns:
            Import statements as a string
        """
        return "import great_expectations as ge\nfrom great_expectations.core import ExpectationSuite\nimport pandas as pd"
    
    def generate_setup(self, file_path: str, metadata: Dict[str, Any], **kwargs) -> str:
        """
        Generate setup code needed for Great Expectations.
        
        Args:
            file_path: Path to the CSV file
            metadata: Metadata dictionary
            **kwargs: Additional parameters
            
        Returns:
            Setup code as a string
        """
        suite_name = kwargs.get("suite_name", "data_quality_suite")
        separator = metadata.get("separator", ",")
        
        setup_code = [
            "# Initialize the data context",
            "context = ge.get_context()",
            "",
            "# Create a new expectation suite",
            f"expectation_suite = ExpectationSuite(expectation_suite_name='{suite_name}')",
            "",
            "# Load the data",
            f"df = pd.read_csv('{os.path.basename(file_path)}', sep='{separator}')",
            "",
            "# Create a Great Expectations DataFrame",
            "ge_df = ge.from_pandas(df)"
        ]
        
        return "\n".join(setup_code)
    
    def _convert_test_to_expectation(self, test: Dict[str, Any]) -> Optional[str]:
        """
        Convert a test specification to a Great Expectations expectation.
        
        Args:
            test: Test specification
            
        Returns:
            Formatted expectation code or None if not convertible
        """
        test_type = test.get("type")
        subtype = test.get("subtype")
        column = test.get("column")
        
        # Schema tests
        if test_type == "schema":
            if subtype == "column_names":
                columns = test["parameters"]["expected_columns"]
                columns_str = ", ".join([f"'{col}'" for col in columns])
                return f"expectation_suite.add_expectation(ge_df.expect_table_columns_to_match_ordered_list([{columns_str}]))"
            
            elif subtype == "column_count":
                count = test["parameters"]["expected_count"]
                return f"expectation_suite.add_expectation(ge_df.expect_table_column_count_to_equal({count}))"
            
            elif subtype == "column_type" and column:
                return f"# Type expectations not directly supported in basic Great Expectations"
        
        # Value tests
        elif test_type == "value" and column:
            if subtype == "minimum":
                min_val = test["parameters"]["min_expected"]
                return f"expectation_suite.add_expectation(ge_df.expect_column_values_to_be_between('{column}', min_value={min_val}, max_value=None))"
            
            elif subtype == "maximum":
                max_val = test["parameters"]["max_expected"]
                return f"expectation_suite.add_expectation(ge_df.expect_column_values_to_be_between('{column}', min_value=None, max_value={max_val}))"
            
            elif subtype == "categorical":
                values = test["parameters"]["valid_values"]
                values_str = ", ".join([f"'{v}'" for v in values])
                return f"expectation_suite.add_expectation(ge_df.expect_column_values_to_be_in_set('{column}', [{values_str}]))"
            
            elif subtype == "string_length":
                max_length = test["parameters"]["max_length"]
                return f"expectation_suite.add_expectation(ge_df.expect_column_value_lengths_to_be_between('{column}', min_value=0, max_value={max_length}))"
        
        # Quality tests
        elif test_type == "quality":
            if subtype == "no_nulls" and column:
                return f"expectation_suite.add_expectation(ge_df.expect_column_values_to_not_be_null('{column}'))"
            
            elif subtype == "limited_nulls" and column:
                max_pct = test["parameters"]["max_null_percentage"] / 100.0  # Convert to fraction
                return f"expectation_suite.add_expectation(ge_df.expect_column_values_to_not_be_null('{column}', mostly={1-max_pct:.4f}))"
            
            elif subtype == "duplicates":
                return f"expectation_suite.add_expectation(ge_df.expect_table_row_count_to_equal_table_row_count_of_unique_values())"
        
        # Relationship tests
        elif test_type == "relationship":
            if subtype == "unique_values" and column:
                return f"expectation_suite.add_expectation(ge_df.expect_column_values_to_be_unique('{column}'))"
            
            elif subtype == "correlation":
                # Correlation tests not directly supported in basic Great Expectations
                return f"# Correlation expectations not directly supported in basic Great Expectations"
        
        # Return None if we couldn't convert this test
        return None


# Register with an alternative name to support both naming conventions
@register_framework
class Great_ExpectationsAdapter(GreatExpectationsAdapter):
    """Alias for GreatExpectationsAdapter to support underscore in name."""
    pass