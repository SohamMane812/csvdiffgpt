"""Google Gemini API provider for LLM integration."""
import os
import time
from typing import Dict, Any, Optional, List, Union, cast

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .base import LLMProvider

class GeminiProvider(LLMProvider):
    """
    Google Gemini API provider for LLM integration.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini provider.
        
        Args:
            api_key: Gemini API key (defaults to env var)
        """
        super().__init__(api_key)
        
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "The 'google-generativeai' package is required to use the Gemini provider. "
                "Install it with: pip install google-generativeai"
            )
        
        # Initialize Gemini client
        genai.configure(api_key=self.api_key)
    
    def _get_api_key_from_env(self) -> Optional[str]:
        """
        Get API key from environment variables.
        
        Returns:
            API key if found, None otherwise
        """
        return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    def query(
        self, 
        prompt: str, 
        model: Optional[str] = "gemini-pro",
        max_tokens: Optional[int] = None, 
        temperature: float = 0.2,
        retry_count: int = 3,
        retry_delay: float = 1.0,
        **kwargs: Any
    ) -> str:
        """
        Send a query to the Gemini API.
        
        Args:
            prompt: The prompt to send
            model: The model to use (e.g., 'gemini-pro')
            max_tokens: Maximum number of tokens in the response (optional)
            temperature: Temperature for response generation
            retry_count: Number of retries on failure
            retry_delay: Delay between retries (in seconds)
            **kwargs: Additional parameters for the Gemini API
            
        Returns:
            The response from the Gemini API
        """
        # Configure generation parameters
        generation_config: Dict[str, Any] = {
            "temperature": temperature,
            **{k: v for k, v in kwargs.items() if k != "use_llm"}
        }
        
        # Add max_tokens if provided
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens
        
        # Use the provided model or default to gemini-2.0-flash
        model_name = model or "gemini-2.0-flash"
        
        # Try to send the request with retries
        for attempt in range(retry_count):
            try:
                # Initialize model
                model_instance = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
                
                # Generate response
                response = model_instance.generate_content(prompt)
                
                # Return the text
                return response.text
            except Exception as e:
                if attempt < retry_count - 1:
                    # Exponential backoff
                    sleep_time = retry_delay * (2 ** attempt)
                    time.sleep(sleep_time)
                else:
                    raise Exception(f"Failed to get response from Gemini API after {retry_count} attempts: {str(e)}")
        
        # This line should never be reached but is needed for mypy
        return ""