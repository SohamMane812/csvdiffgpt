"""Tests for CLI interface."""
import os
import sys
import pytest
from unittest.mock import patch

from csvdiffgpt.cli import main, parse_args


def test_parse_args_summarize():
    """Test parsing summarize command arguments."""
    with patch.object(sys, 'argv', ['csvdiffgpt', 'summarize', 'test.csv']):
        args = parse_args()
        assert args.command == 'summarize'
        assert args.file == 'test.csv'
        assert args.question == 'Summarize this dataset'  # Default
        assert args.provider == 'gemini'  # Default


def test_parse_args_summarize_with_options():
    """Test parsing summarize command with options."""
    with patch.object(sys, 'argv', [
        'csvdiffgpt', 'summarize', 'test.csv',
        '--ask', 'What is this data?',
        '--provider', 'openai',
        '--api-key', 'test-key',
        '--no-llm'
    ]):
        args = parse_args()
        assert args.command == 'summarize'
        assert args.file == 'test.csv'
        assert args.question == 'What is this data?'
        assert args.provider == 'openai'
        assert args.api_key == 'test-key'
        assert args.use_llm is False


def test_parse_args_compare():
    """Test parsing compare command arguments."""
    with patch.object(sys, 'argv', ['csvdiffgpt', 'compare', 'file1.csv', 'file2.csv']):
        args = parse_args()
        assert args.command == 'compare'
        assert args.file1 == 'file1.csv'
        assert args.file2 == 'file2.csv'
        assert args.question == 'What are the key differences between these datasets?'  # Default
        assert args.provider == 'gemini'  # Default


def test_parse_args_compare_with_options():
    """Test parsing compare command with options."""
    with patch.object(sys, 'argv', [
        'csvdiffgpt', 'compare', 'file1.csv', 'file2.csv',
        '--ask', 'What changed?',
        '--provider', 'openai',
        '--api-key', 'test-key',
        '--sep1', ';',
        '--no-llm'
    ]):
        args = parse_args()
        assert args.command == 'compare'
        assert args.file1 == 'file1.csv'
        assert args.file2 == 'file2.csv'
        assert args.question == 'What changed?'
        assert args.provider == 'openai'
        assert args.api_key == 'test-key'
        assert args.sep1 == ';'
        assert args.use_llm is False


@patch('csvdiffgpt.cli.summarize')
def test_main_summarize(mock_summarize):
    """Test main function with summarize command."""
    # Set up mock
    mock_summarize.return_value = "Summarize result"
    
    # Call main with summarize command
    with patch.object(sys, 'argv', ['csvdiffgpt', 'summarize', 'test.csv']):
        with patch('builtins.print') as mock_print:
            main()
            
            # Check that summarize was called with correct args
            mock_summarize.assert_called_once()
            assert mock_summarize.call_args[1]['file'] == 'test.csv'
            
            # Check that result was printed
            mock_print.assert_called_with("Summarize result")


@patch('csvdiffgpt.cli.compare')
def test_main_compare(mock_compare):
    """Test main function with compare command."""
    # Set up mock
    mock_compare.return_value = "Compare result"
    
    # Call main with compare command
    with patch.object(sys, 'argv', ['csvdiffgpt', 'compare', 'file1.csv', 'file2.csv']):
        with patch('builtins.print') as mock_print:
            main()
            
            # Check that compare was called with correct args
            mock_compare.assert_called_once()
            assert mock_compare.call_args[1]['file1'] == 'file1.csv'
            assert mock_compare.call_args[1]['file2'] == 'file2.csv'
            
            # Check that result was printed
            mock_print.assert_called_with("Compare result")


def test_main_unknown_command():
    """Test main function with unknown command."""
    # Call main with unknown command
    with patch.object(sys, 'argv', ['csvdiffgpt', 'unknown']):
        with patch('builtins.print') as mock_print:
            with pytest.raises(SystemExit) as excinfo:
                main()
            
            # Exit code may be 2 for argparse error
            assert excinfo.value.code in [1, 2]


def test_main_no_command():
    """Test main function with no command."""
    # When no command is provided, parse_args will show help and exit
    with patch.object(sys, 'argv', ['csvdiffgpt']):
        with patch('csvdiffgpt.cli.parse_args') as mock_parse_args:
            # Simulate argparse behavior - when no args, it prints help and exits
            mock_parse_args.side_effect = SystemExit(0)
            
            with pytest.raises(SystemExit):
                main()