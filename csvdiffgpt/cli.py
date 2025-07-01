"""Command-line interface for csvdiffgpt."""
import argparse
import os
import sys
from typing import Optional, List, Dict, Any, Sequence

from .tasks.summarize import summarize
from .tasks.compare import compare
from .tasks.validate import validate
from .tasks.clean import clean

def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Args:
        args: Command-line arguments to parse (defaults to sys.argv[1:])
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="CSV analysis with LLMs")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Summarize command
    summarize_parser = subparsers.add_parser("summarize", help="Summarize a CSV file")
    summarize_parser.add_argument("file", help="Path to the CSV file")
    summarize_parser.add_argument("--ask", "--question", dest="question", 
                                default="Summarize this dataset", 
                                help="Question to ask about the dataset")
    summarize_parser.add_argument("--api-key", dest="api_key", 
                                help="API key for the LLM provider")
    summarize_parser.add_argument("--provider", default="gemini", 
                                choices=["openai", "gemini"], 
                                help="LLM provider to use")
    summarize_parser.add_argument("--sep", help="CSV separator (auto-detected if not provided)")
    summarize_parser.add_argument("--max-rows", dest="max_rows_analyzed", type=int, default=150000,
                                help="Maximum number of rows to analyze")
    summarize_parser.add_argument("--max-cols", dest="max_cols_analyzed", type=int,
                                help="Maximum number of columns to analyze")
    summarize_parser.add_argument("--model", help="Specific model to use")
    summarize_parser.add_argument("--no-llm", dest="use_llm", action="store_false", default=True,
                                help="Skip LLM and return raw metadata (no API key needed)")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two CSV files")
    compare_parser.add_argument("file1", help="Path to the first CSV file")
    compare_parser.add_argument("file2", help="Path to the second CSV file")
    compare_parser.add_argument("--ask", "--question", dest="question", 
                              default="What are the key differences between these datasets?", 
                              help="Question to ask about the differences")
    compare_parser.add_argument("--api-key", dest="api_key", 
                              help="API key for the LLM provider")
    compare_parser.add_argument("--provider", default="gemini", 
                              choices=["openai", "gemini"], 
                              help="LLM provider to use")
    compare_parser.add_argument("--sep1", help="CSV separator for file1 (auto-detected if not provided)")
    compare_parser.add_argument("--sep2", help="CSV separator for file2 (auto-detected if not provided)")
    compare_parser.add_argument("--max-rows", dest="max_rows_analyzed", type=int, default=150000,
                              help="Maximum number of rows to analyze per file")
    compare_parser.add_argument("--max-cols", dest="max_cols_analyzed", type=int,
                              help="Maximum number of columns to analyze per file")
    compare_parser.add_argument("--model", help="Specific model to use")
    compare_parser.add_argument("--no-llm", dest="use_llm", action="store_false", default=True,
                              help="Skip LLM and return raw comparison data (no API key needed)")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a CSV file for data quality issues")
    validate_parser.add_argument("file", help="Path to the CSV file")
    validate_parser.add_argument("--ask", "--question", dest="question", 
                               default="Validate this dataset and identify data quality issues", 
                               help="Question to ask about data quality")
    validate_parser.add_argument("--api-key", dest="api_key", 
                               help="API key for the LLM provider")
    validate_parser.add_argument("--provider", default="gemini", 
                               choices=["openai", "gemini"], 
                               help="LLM provider to use")
    validate_parser.add_argument("--sep", help="CSV separator (auto-detected if not provided)")
    validate_parser.add_argument("--max-rows", dest="max_rows_analyzed", type=int, default=150000,
                               help="Maximum number of rows to analyze")
    validate_parser.add_argument("--max-cols", dest="max_cols_analyzed", type=int,
                               help="Maximum number of columns to analyze")
    validate_parser.add_argument("--null-threshold", type=float, default=5.0,
                               help="Percentage threshold for flagging columns with missing values")
    validate_parser.add_argument("--cardinality-threshold", type=float, default=95.0,
                               help="Percentage threshold for high cardinality warning")
    validate_parser.add_argument("--outlier-threshold", type=float, default=3.0,
                               help="Z-score threshold for identifying outliers")
    validate_parser.add_argument("--model", help="Specific model to use")
    validate_parser.add_argument("--no-llm", dest="use_llm", action="store_false", default=True,
                               help="Skip LLM and return raw validation results (no API key needed)")
    
    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Recommend cleaning steps for a CSV file")
    clean_parser.add_argument("file", help="Path to the CSV file")
    clean_parser.add_argument("--ask", "--question", dest="question", 
                            default="Recommend cleaning steps for this dataset", 
                            help="Question to ask about cleaning recommendations")
    clean_parser.add_argument("--api-key", dest="api_key", 
                            help="API key for the LLM provider")
    clean_parser.add_argument("--provider", default="gemini", 
                            choices=["openai", "gemini"], 
                            help="LLM provider to use")
    clean_parser.add_argument("--sep", help="CSV separator (auto-detected if not provided)")
    clean_parser.add_argument("--max-rows", dest="max_rows_analyzed", type=int, default=150000,
                            help="Maximum number of rows to analyze")
    clean_parser.add_argument("--max-cols", dest="max_cols_analyzed", type=int,
                            help="Maximum number of columns to analyze")
    clean_parser.add_argument("--null-threshold", type=float, default=5.0,
                            help="Percentage threshold for flagging columns with missing values")
    clean_parser.add_argument("--cardinality-threshold", type=float, default=95.0,
                            help="Percentage threshold for high cardinality warning")
    clean_parser.add_argument("--outlier-threshold", type=float, default=3.0,
                            help="Z-score threshold for identifying outliers")
    clean_parser.add_argument("--model", help="Specific model to use")
    clean_parser.add_argument("--no-llm", dest="use_llm", action="store_false", default=True,
                            help="Skip LLM and return raw cleaning recommendations (no API key needed)")
    
    # Add more commands here as they are implemented
    
    return parser.parse_args(args)

def main() -> None:
    """
    Main entry point for the CLI.
    """
    try:
        args = parse_args()
        
        # If no command is provided, show help
        if not args.command:
            parse_args(["--help"])
            return
        
        # Convert arguments to dictionary
        args_dict = vars(args)
        command = args_dict.pop("command")
        
        # Execute the command
        if command == "summarize":
            # Create a clean copy of args without any None values
            clean_args = {k: v for k, v in args_dict.items() if v is not None}
            result = summarize(**clean_args)
            print(result)
        elif command == "compare":
            # Create a clean copy of args without any None values
            clean_args = {k: v for k, v in args_dict.items() if v is not None}
            result = compare(**clean_args)
            print(result)
        elif command == "validate":
            # Create a clean copy of args without any None values
            clean_args = {k: v for k, v in args_dict.items() if v is not None}
            result = validate(**clean_args)
            print(result)
        elif command == "clean":
            # Create a clean copy of args without any None values
            clean_args = {k: v for k, v in args_dict.items() if v is not None}
            result = clean(**clean_args)
            print(result)
        # Add more commands here as they are implemented
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except SystemExit as e:
        # Re-raise system exits (like when --help is called)
        raise
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()