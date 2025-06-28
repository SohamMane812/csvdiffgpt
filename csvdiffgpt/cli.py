"""Command-line interface for csvdiffgpt."""
import argparse
import os
import sys
from typing import Optional, List, Dict, Any

from .tasks.summarize import summarize

def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
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
    
    # Add more commands here as they are implemented
    
    return parser.parse_args()

def main() -> None:
    """
    Main entry point for the CLI.
    """
    args = parse_args()
    
    # If no command is provided, show help
    if not args.command:
        parse_args(['--help'])
        return
    
    # Convert arguments to dictionary
    args_dict = vars(args)
    command = args_dict.pop("command")
    
    # Execute the command
    if command == "summarize":
        result = summarize(**args_dict)
        print(result)
    # Add more commands here as they are implemented
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()