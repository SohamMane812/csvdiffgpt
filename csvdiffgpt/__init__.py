"""csvdiffgpt - A package for CSV analysis with LLMs."""

__version__ = "0.1.0"

# Import and expose main functions
from .tasks.summarize import summarize, summarize_raw
from .tasks.compare import compare, compare_raw
from .tasks.validate import validate, validate_raw
from .tasks.clean import clean, clean_raw
from .tasks.generate_tests import generate_tests, generate_tests_raw
from .tasks.restructure import restructure, restructure_raw
from .tasks.explain_code import explain_code

__all__ = [
    "summarize", "summarize_raw", 
    "compare", "compare_raw", 
    "validate", "validate_raw", 
    "clean", "clean_raw",
    "generate_tests", "generate_tests_raw",
    "restructure", "restructure_raw",
    "explain_code"
]