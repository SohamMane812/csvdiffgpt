"""Cleaner for handling outliers in CSV data."""
from typing import Dict, Any, List, Optional

from .base import BaseCleaner, register_cleaner

@register_cleaner
class OutlierCleaner(BaseCleaner):
    """Cleaner for handling outliers."""
    
    def detect_issues(self, df, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Extract outlier issues from validation results.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from the validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of outlier issues
        """
        return validation_results["issues"]["outliers"]
    
    def generate_recommendations(self, df, metadata: Dict[str, Any], issues: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        Generate recommendations for outlier issues.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            issues: List of outlier issues
            **kwargs: Additional parameters
            
        Returns:
            List of cleaning recommendations
        """
        recommendations = []
        outlier_threshold = kwargs.get("outlier_threshold", 3.0)
        
        for issue in issues:
            column = issue["column"]
            
            # Recommend different strategies based on outlier percentage
            if issue["outlier_percentage"] > 10:
                # Many outliers, might be bimodal or meaningful - suggest winsorizing or transforming
                recommendations.append(self._create_winsorize_recommendation(column, issue))
            elif issue["outlier_percentage"] < 5:
                # Few outliers, could be errors - suggest removing or capping
                recommendations.append(self._create_cap_outliers_recommendation(column, issue, outlier_threshold))
        
        return recommendations
    
    def _create_winsorize_recommendation(self, column: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Create a recommendation to winsorize outliers."""
        return {
            "issue_type": "outliers",
            "column": column,
            "action": "winsorize",
            "reason": f"Column has {issue['outlier_percentage']}% outliers",
            "code": f"# Winsorize outliers (cap at 5th and 95th percentiles)\nlower_bound = df['{column}'].quantile(0.05)\nupper_bound = df['{column}'].quantile(0.95)\ndf['{column}'] = df['{column}'].clip(lower=lower_bound, upper=upper_bound)",
            "severity": "medium",
            "impact": {
                "values_modified": int(issue["outlier_count"]),
                "method": "winsorizing"
            }
        }
    
    def _create_cap_outliers_recommendation(self, column: str, issue: Dict[str, Any], outlier_threshold: float) -> Dict[str, Any]:
        """Create a recommendation to cap outliers based on z-score."""
        return {
            "issue_type": "outliers",
            "column": column,
            "action": "cap_outliers",
            "reason": f"Column has {issue['outlier_percentage']}% outliers",
            "code": f"# Cap outliers based on z-score\nz_scores = np.abs((df['{column}'] - df['{column}'].mean()) / df['{column}'].std())\noutlier_mask = z_scores > {outlier_threshold}\ndf.loc[outlier_mask, '{column}'] = np.sign(df.loc[outlier_mask, '{column}'] - df['{column}'].mean()) * {outlier_threshold} * df['{column}'].std() + df['{column}'].mean()",
            "severity": "medium",
            "impact": {
                "values_modified": int(issue["outlier_count"]),
                "method": "z-score capping"
            }
        }