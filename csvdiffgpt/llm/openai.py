"""OpenAI API provider for LLM integration."""
import os
import time
from typing import Dict, Any, Optional, List, Union, cast, TypedDict, Iterable

try:
    import openai
    from openai import OpenAI
    from openai.types.chat import ChatCompletionUserMessageParam
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import LLMProvider

class OpenAIProvider(LLMProvider):
    """
    OpenAI API provider for LLM integration.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key: OpenAI API key (defaults to env var)
        """
        super().__init__(api_key)
        
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "The 'openai' package is required to use the OpenAI provider. "
                "Install it with: pip install openai"
            )
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
    
    def _get_api_key_from_env(self) -> Optional[str]:
        """
        Get API key from environment variables.
        
        Returns:
            API key if found, None otherwise
        """
        return os.environ.get("OPENAI_API_KEY")
    
    def query(
        self, 
        prompt: str, 
        model: Optional[str] = "gpt-4o",
        max_tokens: int = 2000, 
        temperature: float = 0.2,
        retry_count: int = 3,
        retry_delay: float = 1.0,
        **kwargs: Any
    ) -> str:
        """
        Send a query to the OpenAI API.
        
        Args:
            prompt: The prompt to send
            model: The model to use (e.g., 'gpt-4o', 'gpt-3.5-turbo')
            max_tokens: Maximum number of tokens in the response
            temperature: Temperature for response generation
            retry_count: Number of retries on failure
            retry_delay: Delay between retries (in seconds)
            **kwargs: Additional parameters for the OpenAI API
            
        Returns:
            The response from the OpenAI API
        """
        # Use the provided model or default to gpt-4o
        model_name = model or "gpt-4o"
        
        # Filter out use_llm from kwargs if present
        clean_kwargs = {k: v for k, v in kwargs.items() if k != "use_llm"}
        
        # Create the message using proper typing
        # Use the ChatCompletionUserMessageParam type for user messages
        message: ChatCompletionUserMessageParam = {"role": "user", "content": prompt}
        messages = [message]
        
        # Try to send the request with retries
        last_exception = None
        for attempt in range(retry_count):
            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **clean_kwargs
                )
                # The content property should always exist for a valid response
                if response.choices and response.choices[0].message.content is not None:
                    return str(response.choices[0].message.content)
                else:
                    raise ValueError("Received empty response from OpenAI API")
            except (openai.APIError, openai.APIConnectionError, openai.RateLimitError, ValueError) as e:
                last_exception = e
                if attempt < retry_count - 1:
                    # Exponential backoff
                    sleep_time = retry_delay * (2 ** attempt)
                    time.sleep(sleep_time)
                    
        # If we get here, all attempts failed
        if last_exception:
            raise Exception(f"Failed to get response from OpenAI API after {retry_count} attempts: {str(last_exception)}")
            
        # This should never happen, but to satisfy mypy:
        raise Exception("Failed to get response from OpenAI API with no specific error")