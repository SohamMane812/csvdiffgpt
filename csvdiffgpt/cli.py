"""Command-line interface for csvdiffgpt."""
import argparse
import os
import sys
import re
from typing import Optional, List, Dict, Any, Sequence

from .tasks.summarize import summarize
from .tasks.compare import compare
from .tasks.validate import validate
from .tasks.clean import clean
from .tasks.generate_tests import generate_tests
from .tasks.restructure import restructure
from .tasks.explain_code import explain_code

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
    
    # Generate tests command
    tests_parser = subparsers.add_parser("generate-tests", help="Generate tests for a CSV file")
    tests_parser.add_argument("file", help="Path to the CSV file")
    tests_parser.add_argument("--ask", "--question", dest="question", 
                           default="Generate tests for this dataset to ensure data quality", 
                           help="Question to ask about test generation")
    tests_parser.add_argument("--api-key", dest="api_key", 
                           help="API key for the LLM provider")
    tests_parser.add_argument("--provider", default="gemini", 
                           choices=["openai", "gemini"], 
                           help="LLM provider to use")
    tests_parser.add_argument("--framework", default="pytest", 
                           choices=["pytest", "great_expectations", "dbt"], 
                           help="Test framework to use")
    tests_parser.add_argument("--sep", help="CSV separator (auto-detected if not provided)")
    tests_parser.add_argument("--max-rows", dest="max_rows_analyzed", type=int, default=150000,
                           help="Maximum number of rows to analyze")
    tests_parser.add_argument("--max-cols", dest="max_cols_analyzed", type=int,
                           help="Maximum number of columns to analyze")
    tests_parser.add_argument("--null-threshold", type=float, default=5.0,
                           help="Percentage threshold for flagging columns with missing values")
    tests_parser.add_argument("--cardinality-threshold", type=float, default=95.0,
                           help="Percentage threshold for high cardinality warning")
    tests_parser.add_argument("--outlier-threshold", type=float, default=3.0,
                           help="Z-score threshold for identifying outliers")
    tests_parser.add_argument("--model-name", dest="model_name",
                           help="Model name for dbt tests")
    tests_parser.add_argument("--model", help="Specific LLM model to use")
    tests_parser.add_argument("--no-llm", dest="use_llm", action="store_false", default=True,
                           help="Skip LLM and return raw test specifications (no API key needed)")
    tests_parser.add_argument("--output", "-o", help="Output file to save the generated tests")
    
    # Restructure command
    restructure_parser = subparsers.add_parser("restructure", help="Recommend schema restructuring for a CSV file")
    restructure_parser.add_argument("file", help="Path to the CSV file")
    restructure_parser.add_argument("--ask", "--question", dest="question", 
                                 default="Recommend schema improvements for this dataset", 
                                 help="Question to ask about schema restructuring")
    restructure_parser.add_argument("--api-key", dest="api_key", 
                                 help="API key for the LLM provider")
    restructure_parser.add_argument("--provider", default="gemini", 
                                 choices=["openai", "gemini"], 
                                 help="LLM provider to use")
    restructure_parser.add_argument("--format", default="sql", 
                                 choices=["sql", "mermaid", "python"], 
                                 help="Output format for recommendations")
    restructure_parser.add_argument("--sep", help="CSV separator (auto-detected if not provided)")
    restructure_parser.add_argument("--max-rows", dest="max_rows_analyzed", type=int, default=150000,
                                 help="Maximum number of rows to analyze")
    restructure_parser.add_argument("--max-cols", dest="max_cols_analyzed", type=int,
                                 help="Maximum number of columns to analyze")
    restructure_parser.add_argument("--null-threshold", type=float, default=5.0,
                                 help="Percentage threshold for flagging columns with missing values")
    restructure_parser.add_argument("--cardinality-threshold", type=float, default=95.0,
                                 help="Percentage threshold for high cardinality warning")
    restructure_parser.add_argument("--outlier-threshold", type=float, default=3.0,
                                 help="Z-score threshold for identifying outliers")
    restructure_parser.add_argument("--table-name", dest="table_name",
                                 help="Name for the database table")
    restructure_parser.add_argument("--model", help="Specific LLM model to use")
    restructure_parser.add_argument("--no-llm", dest="use_llm", action="store_false", default=True,
                                 help="Skip LLM and return raw restructuring recommendations (no API key needed)")
    restructure_parser.add_argument("--output", "-o", help="Output file to save the generated code")
    
    # Explain code command
    explain_parser = subparsers.add_parser("explain-code", help="Explain Python or SQL code")
    explain_parser.add_argument("file", nargs="?", help="Path to the code file to explain")
    explain_parser.add_argument("--code", help="Code string to explain (alternative to file)")
    explain_parser.add_argument("--language", choices=["python", "sql", "auto"], default="auto",
                              help="Programming language of the code (auto-detected if not specified)")
    explain_parser.add_argument("--detail-level", choices=["high", "medium", "low"], default="medium",
                              help="Level of detail in the explanation")
    explain_parser.add_argument("--focus", help="Specific part of the code to focus on")
    explain_parser.add_argument("--audience", default="data_analyst",
                              choices=["beginner", "data_analyst", "data_scientist", "developer", "technical", "non_technical"],
                              help="Target audience for the explanation")
    explain_parser.add_argument("--api-key", dest="api_key", 
                              help="API key for the LLM provider")
    explain_parser.add_argument("--provider", default="gemini", 
                              choices=["openai", "gemini"], 
                              help="LLM provider to use")
    explain_parser.add_argument("--model", help="Specific LLM model to use")
    explain_parser.add_argument("--output", "-o", help="Output file to save the explanation")
    
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
        
        # Handle output file if specified
        output_file = args_dict.pop("output", None) if "output" in args_dict else None
        
        # Execute the command
        if command == "summarize":
            # Create a clean copy of args without any None values
            clean_args = {k: v for k, v in args_dict.items() if v is not None}
            result = summarize(**clean_args)
            print_or_save_result(result, output_file)
            
        elif command == "compare":
            # Create a clean copy of args without any None values
            clean_args = {k: v for k, v in args_dict.items() if v is not None}
            result = compare(**clean_args)
            print_or_save_result(result, output_file)
            
        elif command == "validate":
            # Create a clean copy of args without any None values
            clean_args = {k: v for k, v in args_dict.items() if v is not None}
            result = validate(**clean_args)
            print_or_save_result(result, output_file)
            
        elif command == "clean":
            # Create a clean copy of args without any None values
            clean_args = {k: v for k, v in args_dict.items() if v is not None}
            result = clean(**clean_args)
            print_or_save_result(result, output_file)
            
        elif command == "generate-tests":
            # Create a clean copy of args without any None values
            clean_args = {k: v for k, v in args_dict.items() if v is not None}
            result = generate_tests(**clean_args)
            print_or_save_result(result, output_file)
            
        elif command == "restructure":
            # Create a clean copy of args without any None values
            clean_args = {k: v for k, v in args_dict.items() if v is not None}
            result = restructure(**clean_args)
            print_or_save_result(result, output_file)
            
        elif command == "explain-code":
            # Handle the explain-code command specifically
            if not args_dict.get("file") and not args_dict.get("code"):
                print("Error: Either a file path or code string must be provided.")
                sys.exit(1)
                
            # Set code or file_path parameter
            if args_dict.get("code"):
                clean_args = {"code": args_dict.pop("code")}
            else:
                clean_args = {"file_path": args_dict.pop("file")}
                
            # Handle language parameter
            if args_dict.get("language") == "auto":
                args_dict.pop("language", None)  # Let the function auto-detect
            
            # Add remaining arguments
            clean_args.update({k: v for k, v in args_dict.items() if v is not None})
            
            # Call explain_code
            result = explain_code(**clean_args)
            print_or_save_result(result, output_file)
            
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

def print_or_save_result(result, output_file: Optional[str] = None):
    """Print the result or save it to a file."""
    if output_file:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            if isinstance(result, str):
                f.write(result)
            else:
                import json
                # Check if it's code output (special handling)
                if isinstance(result, dict) and "code" in result:
                    f.write(result["code"])
                elif isinstance(result, dict) and "output_code" in result:
                    f.write(result["output_code"])
                elif isinstance(result, dict) and "test_code" in result:
                    f.write(result["test_code"])
                else:
                    f.write(json.dumps(result, indent=2, default=str))
        print(f"Result saved to {output_file}")
    else:
        # Print to console
        print(result)

if __name__ == "__main__":
    main()