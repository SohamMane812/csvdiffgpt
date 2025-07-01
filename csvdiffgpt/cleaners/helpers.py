"""Helper functions for generating cleaning code and calculating impact."""
import os
from typing import Dict, Any, List

def generate_sample_code(file: str, metadata: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> str:
    """
    Generate sample code for cleaning recommendations.
    
    Args:
        file: CSV file path
        metadata: Metadata dictionary
        recommendations: List of cleaning recommendations
        
    Returns:
        A string with Python code for cleaning
    """
    if not recommendations:
        return ""
    
    code_lines = [
        "# Data cleaning script",
        "import pandas as pd",
        "import numpy as np",
        "",
        f"# Load the CSV file",
        f"df = pd.read_csv('{os.path.basename(file)}', sep='{metadata['separator']}')",
        "",
        "# Apply cleaning steps",
    ]
    
    # Add cleaning steps code
    for step in recommendations:
        code_lines.append("")
        code_lines.append(f"# Step {step['priority']}: {step['action']} for {step['column']}")
        code_lines.append(step["code"])
    
    code_lines.append("")
    code_lines.append("# Save cleaned data")
    code_lines.append(f"df.to_csv('{os.path.splitext(os.path.basename(file))[0]}_cleaned.csv', index=False)")
    
    return "\n".join(code_lines)

def calculate_potential_impact(validation_results: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate potential impact of cleaning steps.
    
    Args:
        validation_results: Results from the validate_raw function
        recommendations: List of cleaning recommendations
        
    Returns:
        Dictionary with impact metrics
    """
    if not recommendations:
        return {
            "rows_affected": 0,
            "percentage_data_preserved": 100.0
        }
    
    # Count rows that would be dropped
    rows_dropped = 0
    for step in recommendations:
        if step["action"] == "drop_rows" and "rows_removed" in step.get("impact", {}):
            rows_dropped += step["impact"]["rows_removed"]
    
    # Calculate percentage of data preserved
    total_rows = validation_results["file_info"]["total_rows"]
    percentage_preserved = 100.0 if total_rows == 0 else (1.0 - rows_dropped / total_rows) * 100
    
    return {
        "rows_affected": rows_dropped,
        "percentage_data_preserved": round(percentage_preserved, 2)
    }