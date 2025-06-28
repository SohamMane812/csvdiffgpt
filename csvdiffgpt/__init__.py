"""csvdiffgpt - A package for CSV analysis with LLMs."""

__version__ = "0.1.0"

# Import and expose main functions
from .tasks.summarize import summarize

__all__ = ["summarize"]