"""Analyzer for identifying type consistency issues in CSV data."""
from typing import Dict, Any, List, Optional, Tuple, Set
import pandas as pd
import numpy as np
import re

from .base import BaseRestructureAnalyzer, register_analyzer

@register_analyzer
class TypeConsistencyAnalyzer(BaseRestructureAnalyzer):
    """Analyzer for identifying type consistency issues in CSV data."""
    
    def analyze(self, df: pd.DataFrame, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Analyze the data for type consistency issues.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of restructuring recommendations
        """
        recommendations: List[Dict[str, Any]] = []
        
        # 1. Identify columns with type issues from validation results
        type_issues = []
        for issue in validation_results.get("issues", {}).get("type_issues", []):
            type_issues.append(issue)
        
        # Process each type issue
        for issue in type_issues:
            column = issue["column"]
            issue_type = issue["issue"]
            
            if issue_type == "possible_numeric":
                recommendations.append(self._create_numeric_conversion_recommendation(column, issue))
            elif issue_type == "possible_date":
                recommendations.append(self._create_date_conversion_recommendation(column, issue))
        
        # 2. Identify columns with similar semantics but different types
        similar_columns = self._find_similar_name_different_type_columns(metadata)
        
        for group in similar_columns:
            col_group, types = group
            recommendations.append(self._create_type_standardization_recommendation(col_group, types))
        
        # 3. Identify ID columns stored as text that should be numeric
        id_columns = self._find_text_id_columns(df, metadata)
        
        for col in id_columns:
            recommendations.append({
                "type": "type_consistency",
                "subtype": "id_column_type",
                "name": f"convert_{col}_to_int",
                "description": f"Column '{col}' appears to be an ID stored as text but contains only numbers",
                "severity": "medium",
                "columns": [col],
                "action": "convert_type",
                "details": {
                    "from_type": "text",
                    "to_type": "integer",
                    "reason": "Numeric IDs should be stored as integers for better performance and consistency"
                },
                "sql_code": f"-- Convert ID column from text to integer\nALTER TABLE your_table\nALTER COLUMN {col} TYPE INTEGER USING ({col}::INTEGER);",
                "python_code": f"# Convert ID column from text to integer\ndf['{col}'] = pd.to_numeric(df['{col}'], errors='coerce')"
            })
        
        # 4. Look for boolean columns stored as text/int
        bool_columns = self._find_boolean_columns(df, metadata)
        
        for col, values in bool_columns:
            # Create string representations of the boolean values for SQL
            true_values_sql = ", ".join([f"'{v[0]}'" for v in values])
            false_values_sql = ", ".join([f"'{v[1]}'" for v in values])
            
            # Create string representations of the boolean values for Python
            true_values_py = ", ".join([f"'{v[0]}'" for v in values])
            false_values_py = ", ".join([f"'{v[1]}'" for v in values])
            
            # Create the SQL code without f-strings inside f-strings
            sql_code = f"-- Convert to proper boolean type\nALTER TABLE your_table\nALTER COLUMN {col} TYPE BOOLEAN USING (\n    CASE\n        WHEN {col} IN ({true_values_sql}) THEN TRUE\n        WHEN {col} IN ({false_values_sql}) THEN FALSE\n        ELSE NULL\n    END\n);"
            
            recommendations.append({
                "type": "type_consistency",
                "subtype": "boolean_column_type",
                "name": f"convert_{col}_to_boolean",
                "description": f"Column '{col}' appears to be a boolean stored as text",
                "severity": "medium",
                "columns": [col],
                "action": "convert_type",
                "details": {
                    "from_type": "text",
                    "to_type": "boolean",
                    "values": values,
                    "reason": "Boolean values should be stored in boolean type for clarity and efficiency"
                },
                "sql_code": sql_code,
                "python_code": f"# Convert to proper boolean type\ndf['{col}'] = df['{col}'].map({{\n    {true_values_py}: True,\n    {false_values_py}: False\n}})"
            })
        
        return recommendations
    
    def _create_numeric_conversion_recommendation(self, column: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Create a recommendation for converting a column to numeric type."""
        return {
            "type": "type_consistency",
            "subtype": "string_to_numeric",
            "name": f"convert_{column}_to_numeric",
            "description": f"Column '{column}' contains numeric values stored as strings",
            "severity": "high",
            "columns": [column],
            "action": "convert_type",
            "details": {
                "from_type": "string",
                "to_type": "numeric",
                "examples": issue.get("examples", []),
                "reason": "Numeric data should be stored in numeric type for calculations and efficiency"
            },
            "sql_code": f"-- Convert string to numeric\nALTER TABLE your_table\nALTER COLUMN {column} TYPE NUMERIC USING ({column}::NUMERIC);",
            "python_code": f"# Convert string to numeric\ndf['{column}'] = pd.to_numeric(df['{column}'].str.replace(',', ''), errors='coerce')"
        }
    
    def _create_date_conversion_recommendation(self, column: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Create a recommendation for converting a column to date type."""
        return {
            "type": "type_consistency",
            "subtype": "string_to_date",
            "name": f"convert_{column}_to_date",
            "description": f"Column '{column}' contains date values stored as strings",
            "severity": "high",
            "columns": [column],
            "action": "convert_type",
            "details": {
                "from_type": "string",
                "to_type": "date",
                "examples": issue.get("examples", []),
                "reason": "Date data should be stored in date type for better querying and manipulation"
            },
            "sql_code": f"-- Convert string to date\nALTER TABLE your_table\nALTER COLUMN {column} TYPE DATE USING ({column}::DATE);",
            "python_code": f"# Convert string to date\ndf['{column}'] = pd.to_datetime(df['{column}'], errors='coerce')"
        }
    
    def _create_type_standardization_recommendation(self, columns: List[str], types: List[str]) -> Dict[str, Any]:
        """Create a recommendation for standardizing types across similar columns."""
        # Determine the best type based on current types
        target_type = "VARCHAR"  # Default
        if all("int" in t for t in types):
            target_type = "INTEGER"
        elif any("float" in t for t in types) or any("numeric" in t for t in types):
            target_type = "NUMERIC"
        elif any("date" in t for t in types):
            target_type = "DATE"
        elif any("bool" in t for t in types):
            target_type = "BOOLEAN"
        
        # Generate SQL and Python code
        sql_lines = [f"-- Standardize column types for similar columns: {', '.join(columns)}"]
        python_lines = [f"# Standardize column types for similar columns: {', '.join(columns)}"]
        
        for i, col in enumerate(columns):
            if types[i] != target_type.lower():
                sql_lines.append(f"ALTER TABLE your_table ALTER COLUMN {col} TYPE {target_type} USING ({col}::{target_type});")
                
                if target_type == "INTEGER":
                    python_lines.append(f"df['{col}'] = pd.to_numeric(df['{col}'], errors='coerce').astype('Int64')")
                elif target_type == "NUMERIC":
                    python_lines.append(f"df['{col}'] = pd.to_numeric(df['{col}'], errors='coerce')")
                elif target_type == "DATE":
                    python_lines.append(f"df['{col}'] = pd.to_datetime(df['{col}'], errors='coerce')")
                elif target_type == "BOOLEAN":
                    python_lines.append(f"df['{col}'] = df['{col}'].astype(bool)")
                else:
                    python_lines.append(f"df['{col}'] = df['{col}'].astype(str)")
        
        return {
            "type": "type_consistency",
            "subtype": "standardize_similar_columns",
            "name": f"standardize_{columns[0]}_group",
            "description": f"Standardize types for similar columns: {', '.join(columns)}",
            "severity": "medium",
            "columns": columns,
            "action": "standardize_types",
            "details": {
                "columns": columns,
                "current_types": types,
                "target_type": target_type,
                "reason": "Similar columns should use consistent types"
            },
            "sql_code": "\n".join(sql_lines),
            "python_code": "\n".join(python_lines)
        }
    
    def _find_similar_name_different_type_columns(self, metadata: Dict[str, Any]) -> List[Tuple[List[str], List[str]]]:
        """
        Find columns with similar names but different data types.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            List of tuples ([column_names], [column_types])
        """
        # Group columns by name pattern
        name_patterns: Dict[str, List[Tuple[str, str]]] = {}
        
        for col, details in metadata.get("columns", {}).items():
            # Normalize column name for comparison (remove numbers, convert to lowercase)
            base_name = re.sub(r'\d+', '', col.lower())
            
            # Skip very short names
            if len(base_name) < 3:
                continue
                
            if base_name not in name_patterns:
                name_patterns[base_name] = []
            name_patterns[base_name].append((col, details.get("type", "")))
        
        # Find groups with different types
        result = []
        for pattern, columns in name_patterns.items():
            if len(columns) > 1:
                types = [c[1] for c in columns]
                
                # Check if there are different types in this group
                if len(set(types)) > 1:
                    result.append(([c[0] for c in columns], types))
        
        return result
    
    def _find_text_id_columns(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> List[str]:
        """
        Find ID columns stored as text that could be numeric.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            
        Returns:
            List of column names
        """
        result = []
        
        for col, details in metadata.get("columns", {}).items():
            # Look for columns that might be IDs (name contains 'id')
            if "id" in col.lower() and details.get("type", "") == "object":
                # Check if column contains only numeric strings
                if col in df.columns:
                    sample = df[col].dropna().astype(str).head(100)
                    if len(sample) > 0:
                        # Check if all values in sample are numeric
                        if all(v.isdigit() for v in sample):
                            result.append(col)
        
        return result
    
    def _find_boolean_columns(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> List[Tuple[str, List[Tuple[str, str]]]]:
        """
        Find columns that appear to contain boolean values stored as text.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            
        Returns:
            List of tuples (column_name, [(true_value, false_value), ...])
        """
        result = []
        bool_patterns = [
            ("yes", "no"),
            ("y", "n"),
            ("true", "false"),
            ("t", "f"),
            ("1", "0"),
            ("enabled", "disabled"),
            ("active", "inactive"),
            ("on", "off")
        ]
        
        for col, details in metadata.get("columns", {}).items():
            # Only check string columns with low cardinality
            if details.get("type", "") == "object" and details.get("unique_count", 100) <= 5:
                # Get unique values
                if col in df.columns:
                    unique_values = df[col].dropna().unique()
                    
                    # Skip if too many unique values
                    if len(unique_values) > 5:
                        continue
                    
                    # Convert to lowercase strings for comparison
                    unique_lower = [str(v).lower() for v in unique_values]
                    
                    # Check for known boolean patterns
                    matched_patterns = []
                    for true_val, false_val in bool_patterns:
                        if true_val in unique_lower and false_val in unique_lower:
                            # Find the original case versions
                            true_original = unique_values[unique_lower.index(true_val)]
                            false_original = unique_values[unique_lower.index(false_val)]
                            matched_patterns.append((true_original, false_original))
                    
                    if matched_patterns:
                        result.append((col, matched_patterns))
        
        return result