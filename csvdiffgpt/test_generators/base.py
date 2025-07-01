"""Base class for test generators."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseTestGenerator(ABC):
    """Base class for all test generators."""
    
    @abstractmethod
    def generate_tests(self, df, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Generate tests based on the provided data.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of test specifications
        """
        pass
    
    def get_name(self) -> str:
        """Get the name of this test generator."""
        return self.__class__.__name__

# Registry of all test generators
TEST_GENERATOR_REGISTRY = {}

def register_generator(generator_class):
    """Register a test generator class."""
    TEST_GENERATOR_REGISTRY[generator_class.__name__] = generator_class
    return generator_class

def get_all_generators():
    """Get all registered test generators."""
    return [generator_class() for generator_class in TEST_GENERATOR_REGISTRY.values()]