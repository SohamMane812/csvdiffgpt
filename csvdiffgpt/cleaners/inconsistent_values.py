"""Cleaner for handling inconsistent values in CSV data."""
from typing import Dict, Any, List, Optional

from .base import BaseCleaner, register_cleaner

@register_cleaner
class InconsistentValueCleaner(BaseCleaner):
    """Cleaner for handling inconsistent values."""
    
    def detect_issues(self, df, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Extract inconsistent value issues from validation results.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from the validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of inconsistent value issues
        """
        return validation_results["issues"]["inconsistent_values"]
    
    def generate_recommendations(self, df, metadata: Dict[str, Any], issues: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        Generate recommendations for inconsistent value issues.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            issues: List of inconsistent value issues
            **kwargs: Additional parameters
            
        Returns:
            List of cleaning recommendations
        """
        recommendations = []
        
        for issue in issues:
            column = issue["column"]
            issue_type = issue["issue"]
            
            if issue_type == "inconsistent_length":
                # Suggest standardizing string length or checking for errors
                recommendations.append(self._create_standardize_format_recommendation(column, issue))
        
        return recommendations
    
    def _create_standardize_format_recommendation(self, column: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Create a recommendation to standardize string format."""
        return {
            "issue_type": "inconsistent_values",
            "column": column,
            "action": "standardize_format",
            "reason": f"Column has inconsistent string lengths (min: {issue['min_length']}, max: {issue['max_length']})",
            "code": f"# Standardize string format (example for phone numbers or codes)\n# Inspect values first\nprint(df['{column}'].value_counts().head(10))\n# Then apply appropriate formatting\n# df['{column}'] = df['{column}'].str.strip().str.lower()  # For text\n# df['{column}'] = df['{column}'].str.replace('[^0-9]', '')  # For numeric IDs",
            "severity": "medium",
            "impact": {
                "standardization": "string format"
            }
        }