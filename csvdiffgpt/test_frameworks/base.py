"""Base class for test framework adapters."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from .framework_helpers import normalize_framework_name, get_adapter_class_name

class BaseTestFramework(ABC):
    """Base class for all test framework adapters."""
    
    @abstractmethod
    def format_tests(self, tests: List[Dict[str, Any]], metadata: Dict[str, Any], **kwargs) -> str:
        """
        Format test specifications into framework-specific code.
        
        Args:
            tests: List of test specifications
            metadata: Metadata dictionary
            **kwargs: Additional parameters
            
        Returns:
            Formatted test code as a string
        """
        pass
    
    @abstractmethod
    def generate_imports(self, **kwargs) -> str:
        """
        Generate import statements needed for this test framework.
        
        Args:
            **kwargs: Additional parameters
            
        Returns:
            Import statements as a string
        """
        pass
    
    @abstractmethod
    def generate_setup(self, file_path: str, metadata: Dict[str, Any], **kwargs) -> str:
        """
        Generate setup code needed for this test framework.
        
        Args:
            file_path: Path to the CSV file
            metadata: Metadata dictionary
            **kwargs: Additional parameters
            
        Returns:
            Setup code as a string
        """
        pass
    
    def get_name(self) -> str:
        """Get the name of this test framework adapter."""
        return self.__class__.__name__

# Registry of all test framework adapters
TEST_FRAMEWORK_REGISTRY = {}

def register_framework(framework_class):
    """Register a test framework adapter class."""
    TEST_FRAMEWORK_REGISTRY[framework_class.__name__] = framework_class
    return framework_class

def get_framework(name: str) -> Optional[BaseTestFramework]:
    """
    Get a test framework adapter by name.
    
    Args:
        name: Name of the test framework
        
    Returns:
        Test framework adapter instance or None if not found
    """
    # Try to get the adapter class using the provided name
    adapter_class_name = get_adapter_class_name(name)
    framework_class = TEST_FRAMEWORK_REGISTRY.get(adapter_class_name)
    
    # If not found, try normalized versions
    if not framework_class:
        for registered_name, registered_class in TEST_FRAMEWORK_REGISTRY.items():
            if normalize_framework_name(registered_name) == normalize_framework_name(name):
                framework_class = registered_class
                break
    
    if framework_class:
        return framework_class()
    
    return None

def get_available_frameworks() -> List[str]:
    """Get names of all available test frameworks."""
    return list(TEST_FRAMEWORK_REGISTRY.keys())