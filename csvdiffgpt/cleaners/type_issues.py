"""Cleaner for handling type issues in CSV data."""
from typing import Dict, Any, List, Optional

from .base import BaseCleaner, register_cleaner

@register_cleaner
class TypeIssueCleaner(BaseCleaner):
    """Cleaner for handling type issues."""
    
    def detect_issues(self, df, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Extract type issues from validation results.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from the validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of type issues
        """
        return validation_results["issues"]["type_issues"]
    
    def generate_recommendations(self, df, metadata: Dict[str, Any], issues: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        Generate recommendations for type issues.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            issues: List of type issues
            **kwargs: Additional parameters
            
        Returns:
            List of cleaning recommendations
        """
        recommendations = []
        
        for issue in issues:
            column = issue["column"]
            issue_type = issue["issue"]
            
            if issue_type == "possible_numeric":
                # Convert string to numeric
                recommendations.append(self._create_convert_to_numeric_recommendation(column, issue))
            elif issue_type == "possible_date":
                # Convert string to datetime
                recommendations.append(self._create_convert_to_date_recommendation(column, issue))
        
        return recommendations
    
    def _create_convert_to_numeric_recommendation(self, column: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Create a recommendation to convert string to numeric."""
        return {
            "issue_type": "type_issues",
            "column": column,
            "action": "convert_to_numeric",
            "reason": "Column contains numeric values stored as strings",
            "code": f"# Convert string to numeric\ndf['{column}'] = pd.to_numeric(df['{column}'].str.replace(',', ''), errors='coerce')",
            "severity": "high",
            "impact": {
                "data_type_changed": True,
                "from_type": "object",
                "to_type": "numeric"
            }
        }
    
    def _create_convert_to_date_recommendation(self, column: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Create a recommendation to convert string to datetime."""
        return {
            "issue_type": "type_issues",
            "column": column,
            "action": "convert_to_date",
            "reason": "Column contains date values stored as strings",
            "code": f"# Convert string to datetime\ndf['{column}'] = pd.to_datetime(df['{column}'], errors='coerce')",
            "severity": "high",
            "impact": {
                "data_type_changed": True,
                "from_type": "object",
                "to_type": "datetime"
            }
        }