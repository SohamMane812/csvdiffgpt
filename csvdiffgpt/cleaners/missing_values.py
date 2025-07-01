"""Cleaner for handling missing values in CSV data."""
import numpy as np
from typing import Dict, Any, List, Optional

from .base import BaseCleaner, register_cleaner

@register_cleaner
class MissingValueCleaner(BaseCleaner):
    """Cleaner for handling missing values."""
    
    def detect_issues(self, df, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Extract missing value issues from validation results.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from the validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of missing value issues
        """
        return validation_results["issues"]["missing_values"]
    
    def generate_recommendations(self, df, metadata: Dict[str, Any], issues: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        Generate recommendations for missing value issues.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            issues: List of missing value issues
            **kwargs: Additional parameters
            
        Returns:
            List of cleaning recommendations
        """
        recommendations = []
        
        for issue in issues:
            column = issue["column"]
            col_meta = metadata["columns"].get(column, {})
            col_type = col_meta.get("type", "")
            
            if issue["null_percentage"] > 50:
                # More than half missing, consider dropping
                recommendations.append(self._create_drop_column_recommendation(column, issue, metadata))
            elif np.issubdtype(np.dtype(col_type), np.number) and issue["null_percentage"] < 30:
                # For numeric columns with reasonable amount of missing values, fill with median
                recommendations.append(self._create_median_imputation_recommendation(column, issue))
            elif col_type == "object" and issue["null_percentage"] < 30:
                # For string columns with reasonable amount of missing values, fill with mode or 'Unknown'
                recommendations.append(self._create_mode_imputation_recommendation(column, issue))
            else:
                # For other cases, recommend dropping rows if missing percentage is low
                if issue["null_percentage"] < 10:
                    recommendations.append(self._create_drop_rows_recommendation(column, issue))
                else:
                    # Otherwise, recommend a flag column for missingness
                    recommendations.append(self._create_missing_flag_recommendation(column, issue))
        
        return recommendations
    
    def _create_drop_column_recommendation(self, column: str, issue: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create a recommendation to drop a column."""
        return {
            "issue_type": "missing_values",
            "column": column,
            "action": "drop_column",
            "reason": f"Column has {issue['null_percentage']}% missing values",
            "code": f"# Drop column with excessive missing values\ndf = df.drop(columns=['{column}'])",
            "severity": "high" if issue["null_percentage"] > 80 else "medium",
            "impact": {
                "rows_preserved": metadata["total_rows"],
                "columns_removed": 1
            }
        }
    
    def _create_median_imputation_recommendation(self, column: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Create a recommendation to fill missing values with median."""
        return {
            "issue_type": "missing_values",
            "column": column,
            "action": "fill_median",
            "reason": f"Numeric column with {issue['null_percentage']}% missing values",
            "code": f"# Fill missing values with median\ndf['{column}'] = df['{column}'].fillna(df['{column}'].median())",
            "severity": "medium",
            "impact": {
                "rows_filled": int(issue["null_count"]),
                "fill_method": "median"
            }
        }
    
    def _create_mode_imputation_recommendation(self, column: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Create a recommendation to fill missing values with mode or 'Unknown'."""
        return {
            "issue_type": "missing_values",
            "column": column,
            "action": "fill_mode_or_unknown",
            "reason": f"String column with {issue['null_percentage']}% missing values",
            "code": f"# Fill missing values with most common value or 'Unknown'\nmode_value = df['{column}'].mode()[0] if not df['{column}'].mode().empty else 'Unknown'\ndf['{column}'] = df['{column}'].fillna(mode_value)",
            "severity": "medium",
            "impact": {
                "rows_filled": int(issue["null_count"]),
                "fill_method": "mode or 'Unknown'"
            }
        }
    
    def _create_drop_rows_recommendation(self, column: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Create a recommendation to drop rows with missing values."""
        return {
            "issue_type": "missing_values",
            "column": column,
            "action": "drop_rows",
            "reason": f"Column has {issue['null_percentage']}% missing values",
            "code": f"# Drop rows with missing values in this column\ndf = df.dropna(subset=['{column}'])",
            "severity": "medium" if issue["null_percentage"] < 5 else "high",
            "impact": {
                "rows_removed": int(issue["null_count"]),
                "percentage_removed": issue["null_percentage"]
            }
        }
    
    def _create_missing_flag_recommendation(self, column: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Create a recommendation to create a flag for missing values."""
        return {
            "issue_type": "missing_values",
            "column": column,
            "action": "create_missing_flag",
            "reason": f"Column has {issue['null_percentage']}% missing values",
            "code": f"# Create flag for missing values\ndf['{column}_missing'] = df['{column}'].isna()",
            "severity": "medium",
            "impact": {
                "new_columns": 1
            }
        }