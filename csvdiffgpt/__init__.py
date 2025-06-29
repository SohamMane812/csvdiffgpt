"""csvdiffgpt - A package for CSV analysis with LLMs."""

__version__ = "0.1.0"

# Import and expose main functions
from .tasks.summarize import summarize, summarize_raw
from .tasks.compare import compare, compare_raw

__all__ = ["summarize", "summarize_raw", "compare", "compare_raw"]