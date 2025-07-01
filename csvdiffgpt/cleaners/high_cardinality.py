"""Cleaner for handling high cardinality columns in CSV data."""
from typing import Dict, Any, List, Optional

from .base import BaseCleaner, register_cleaner

@register_cleaner
class HighCardinalityCleaner(BaseCleaner):
    """Cleaner for handling high cardinality columns."""
    
    def detect_issues(self, df, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Extract high cardinality issues from validation results.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from the validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of high cardinality issues
        """
        return validation_results["issues"]["high_cardinality"]
    
    def generate_recommendations(self, df, metadata: Dict[str, Any], issues: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        Generate recommendations for high cardinality issues.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            issues: List of high cardinality issues
            **kwargs: Additional parameters
            
        Returns:
            List of cleaning recommendations
        """
        recommendations = []
        
        for issue in issues:
            column = issue["column"]
            
            # Suggest grouping less frequent categories
            recommendations.append(self._create_group_rare_categories_recommendation(column, issue))
        
        return recommendations
    
    def _create_group_rare_categories_recommendation(self, column: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Create a recommendation to group rare categories."""
        return {
            "issue_type": "high_cardinality",
            "column": column,
            "action": "group_rare_categories",
            "reason": f"Column has high cardinality ({issue['unique_count']} unique values, {issue['unique_percentage']}%)",
            "code": f"# Group rare categories\nvalue_counts = df['{column}'].value_counts()\ntop_n = value_counts.nlargest(10).index.tolist()\ndf['{column}_grouped'] = df['{column}'].apply(lambda x: x if x in top_n else 'Other')",
            "severity": "low",
            "impact": {
                "new_columns": 1,
                "cardinality_reduced": True
            }
        }