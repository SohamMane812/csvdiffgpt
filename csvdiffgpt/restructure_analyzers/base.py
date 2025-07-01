"""Base class for all restructure analyzers."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseRestructureAnalyzer(ABC):
    """Base class for all restructure analyzers."""
    
    @abstractmethod
    def analyze(self, df, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Analyze the data and provide restructuring recommendations.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of restructuring recommendations
        """
        pass
    
    def get_name(self) -> str:
        """Get the name of this analyzer."""
        return self.__class__.__name__

# Registry of all analyzers
ANALYZER_REGISTRY = {}

def register_analyzer(analyzer_class):
    """Register an analyzer class."""
    ANALYZER_REGISTRY[analyzer_class.__name__] = analyzer_class
    return analyzer_class

def get_all_analyzers():
    """Get all registered analyzers."""
    return [analyzer_class() for analyzer_class in ANALYZER_REGISTRY.values()]