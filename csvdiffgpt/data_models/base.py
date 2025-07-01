"""Base class for data model adapters."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseDataModelAdapter(ABC):
    """Base class for all data model adapters."""
    
    @abstractmethod
    def format_recommendations(self, recommendations: List[Dict[str, Any]], metadata: Dict[str, Any], **kwargs) -> str:
        """
        Format restructuring recommendations into a specific output format.
        
        Args:
            recommendations: List of restructuring recommendations
            metadata: Metadata dictionary
            **kwargs: Additional parameters
            
        Returns:
            Formatted recommendations as a string
        """
        pass
    
    def get_name(self) -> str:
        """Get the name of this adapter."""
        return self.__class__.__name__

# Registry of all data model adapters
DATA_MODEL_REGISTRY = {}

def register_model_adapter(adapter_class):
    """Register a data model adapter class."""
    DATA_MODEL_REGISTRY[adapter_class.__name__] = adapter_class
    return adapter_class

def get_model_adapter(name: str) -> Optional['BaseDataModelAdapter']:
    """
    Get a data model adapter by name.
    
    Args:
        name: Name of the data model adapter
        
    Returns:
        Data model adapter instance or None if not found
    """
    adapter_class = DATA_MODEL_REGISTRY.get(f"{name.capitalize()}Adapter")
    if adapter_class:
        return adapter_class()
    return None

def get_available_adapters() -> List[str]:
    """Get names of all available data model adapters."""
    return [name.replace("Adapter", "").lower() for name in DATA_MODEL_REGISTRY.keys()]