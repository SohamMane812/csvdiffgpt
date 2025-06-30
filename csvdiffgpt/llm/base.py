"""Base class for LLM providers."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
import os
import json

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM provider.
        
        Args:
            api_key: API key for the provider (can be None if using env var)
        """
        self.api_key = api_key or self._get_api_key_from_env()
    
    @abstractmethod
    def _get_api_key_from_env(self) -> Optional[str]:
        """
        Get API key from environment variables.
        
        Returns:
            API key if found, None otherwise
        """
        pass
    
    @abstractmethod
    def query(self, prompt: str, model: Optional[str] = None, **kwargs: Any) -> str:
        """
        Send a query to the LLM provider.
        
        Args:
            prompt: The prompt to send
            model: The model to use (provider-specific)
            **kwargs: Additional parameters for the provider
            
        Returns:
            The response from the LLM
        """
        pass
    
    def load_prompt_template(self, task_name: str) -> str:
        """
        Load a prompt template for a specific task.
        
        Args:
            task_name: Name of the task (e.g., 'summarize', 'compare')
            
        Returns:
            The prompt template as a string
        """
        # Calculate the path to the prompt file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_file = os.path.join(current_dir, 'prompts', f'{task_name}.txt')
        
        # Load the prompt template
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise ValueError(f"Prompt template for task '{task_name}' not found.")
    
    def format_prompt(self, task_name: str, data: Dict[str, Any]) -> str:
        """
        Format a prompt template with data.
        
        Args:
            task_name: Name of the task
            data: Dictionary of data to inject into the template
            
        Returns:
            The formatted prompt
        """
        # Load the prompt template
        template = self.load_prompt_template(task_name)
        
        # Format the template with the data
        # For CSV metadata, ensure it's properly formatted as a string
        if 'metadata' in data and not isinstance(data['metadata'], str):
            if isinstance(data['metadata'], dict):
                data['metadata'] = json.dumps(data['metadata'], indent=2, default=str)
        
        # Replace placeholders in the template
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if placeholder in template:
                template = template.replace(placeholder, str(value))
        
        return template