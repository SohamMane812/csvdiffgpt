"""Base class for all cleaning strategies."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseCleaner(ABC):
    """Base class for all cleaning strategies."""
    
    @abstractmethod
    def detect_issues(self, df, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Detect issues of a specific type in the data.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from the validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of issues detected
        """
        pass
    
    @abstractmethod
    def generate_recommendations(self, df, metadata: Dict[str, Any], issues: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        Generate cleaning recommendations for detected issues.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            issues: List of issues detected
            **kwargs: Additional parameters
            
        Returns:
            List of cleaning recommendations
        """
        pass
    
    def get_name(self) -> str:
        """Get the name of this cleaner."""
        return self.__class__.__name__

# Registry of all cleaners
CLEANER_REGISTRY = {}

def register_cleaner(cleaner_class):
    """Register a cleaner class."""
    CLEANER_REGISTRY[cleaner_class.__name__] = cleaner_class
    return cleaner_class

def get_all_cleaners():
    """Get all registered cleaners."""
    return [cleaner_class() for cleaner_class in CLEANER_REGISTRY.values()]