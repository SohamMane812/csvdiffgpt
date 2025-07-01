"""Helper functions for test framework lookup."""
from typing import Optional

def normalize_framework_name(framework_name: str) -> str:
    """
    Normalize a framework name for consistent lookup.
    
    Args:
        framework_name: Framework name (e.g., 'pytest', 'great_expectations')
        
    Returns:
        Normalized framework name
    """
    # Remove underscores and convert to lowercase
    normalized = framework_name.replace('_', '').lower()
    
    # Handle special cases
    if normalized == 'greatexpectations' or normalized == 'ge':
        return 'greatexpectations'
    
    return normalized

def get_adapter_class_name(framework_name: str) -> str:
    """
    Get the adapter class name for a framework.
    
    Args:
        framework_name: Framework name (e.g., 'pytest', 'great_expectations')
        
    Returns:
        Adapter class name
    """
    normalized = normalize_framework_name(framework_name)
    
    # Map normalized names to adapter class names
    name_mapping = {
        'pytest': 'PytestAdapter',
        'greatexpectations': 'GreatExpectationsAdapter',
        'ge': 'GreatExpectationsAdapter',
        'dbt': 'DbtAdapter'
    }
    
    # Return mapped name or capitalize the first letter and add 'Adapter'
    return name_mapping.get(normalized, framework_name.capitalize() + 'Adapter')