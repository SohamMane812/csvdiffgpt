"""Tests for explain_code functionality."""
import os
import pytest
from unittest.mock import patch, MagicMock

from csvdiffgpt import explain_code

# Sample code snippets for testing
PYTHON_CODE_SAMPLE = """
import pandas as pd
import numpy as np

def process_data(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Remove missing values
    df = df.dropna()
    
    # Calculate some statistics
    mean_value = df['value'].mean()
    std_value = df['value'].std()
    
    # Filter based on standard deviation
    filtered_df = df[df['value'] > mean_value + 2 * std_value]
    
    # Group by category
    result = filtered_df.groupby('category').agg({
        'value': ['count', 'mean', 'sum']
    })
    
    return result
"""

SQL_CODE_SAMPLE = """
-- Customer order analysis query
WITH customer_orders AS (
    SELECT 
        customer_id,
        COUNT(*) AS order_count,
        SUM(order_amount) AS total_spent,
        AVG(order_amount) AS avg_order_value,
        MIN(order_date) AS first_order_date,
        MAX(order_date) AS last_order_date
    FROM orders
    WHERE order_status = 'completed'
    GROUP BY customer_id
),
customer_segments AS (
    SELECT 
        customer_id,
        CASE 
            WHEN total_spent > 1000 THEN 'high_value'
            WHEN order_count > 10 THEN 'frequent'
            ELSE 'regular'
        END AS segment
    FROM customer_orders
)
SELECT 
    cs.segment,
    COUNT(*) AS customer_count,
    AVG(co.total_spent) AS avg_total_spent,
    AVG(co.order_count) AS avg_order_count
FROM customer_segments cs
JOIN customer_orders co ON cs.customer_id = co.customer_id
GROUP BY cs.segment
ORDER BY avg_total_spent DESC;
"""

def test_explain_code_with_string_python():
    """Test explain_code with Python code provided as a string."""
    with patch('csvdiffgpt.tasks.explain_code.get_provider') as mock_get_provider:
        # Set up the mock
        mock_provider = MagicMock()
        mock_provider.query.return_value = "Explanation of Python code"
        mock_provider.format_prompt.return_value = "Mocked prompt"
        mock_get_provider.return_value = mock_provider
        
        # Call explain_code
        result = explain_code(code=PYTHON_CODE_SAMPLE)
        
        # Check that the function called the LLM correctly
        assert result == "Explanation of Python code"
        assert mock_provider.query.called
        assert mock_provider.format_prompt.called
        
        # Check that the language was detected as python
        prompt_data = mock_provider.format_prompt.call_args[0][1]
        assert prompt_data["language"] == "python"

def test_explain_code_with_string_sql():
    """Test explain_code with SQL code provided as a string."""
    with patch('csvdiffgpt.tasks.explain_code.get_provider') as mock_get_provider:
        # Set up the mock
        mock_provider = MagicMock()
        mock_provider.query.return_value = "Explanation of SQL code"
        mock_provider.format_prompt.return_value = "Mocked prompt"
        mock_get_provider.return_value = mock_provider
        
        # Call explain_code
        result = explain_code(code=SQL_CODE_SAMPLE)
        
        # Check that the function called the LLM correctly
        assert result == "Explanation of SQL code"
        
        # Check that the language was detected as SQL
        prompt_data = mock_provider.format_prompt.call_args[0][1]
        assert prompt_data["language"] == "sql"

def test_explain_code_with_file(tmp_path):
    """Test explain_code with a code file."""
    # Create a temporary Python file
    file_path = tmp_path / "test_code.py"
    with open(file_path, 'w') as f:
        f.write(PYTHON_CODE_SAMPLE)
    
    with patch('csvdiffgpt.tasks.explain_code.get_provider') as mock_get_provider:
        # Set up the mock
        mock_provider = MagicMock()
        mock_provider.query.return_value = "Explanation of file code"
        mock_provider.format_prompt.return_value = "Mocked prompt"
        mock_get_provider.return_value = mock_provider
        
        # Call explain_code
        result = explain_code(file_path=str(file_path))
        
        # Check that the function called the LLM correctly
        assert result == "Explanation of file code"
        
        # Check that the code was read from the file
        prompt_data = mock_provider.format_prompt.call_args[0][1]
        assert "import pandas as pd" in prompt_data["code"]

def test_explain_code_with_function():
    """Test explain_code with a Python function object."""
    def sample_function(x, y):
        """Sample function that adds two numbers."""
        return x + y
    
    with patch('csvdiffgpt.tasks.explain_code.get_provider') as mock_get_provider:
        # Set up the mock
        mock_provider = MagicMock()
        mock_provider.query.return_value = "Explanation of function code"
        mock_provider.format_prompt.return_value = "Mocked prompt"
        mock_get_provider.return_value = mock_provider
        
        # Call explain_code
        result = explain_code(code_object=sample_function)
        
        # Check that the function called the LLM correctly
        assert result == "Explanation of function code"
        
        # Check that the code was extracted from the function
        prompt_data = mock_provider.format_prompt.call_args[0][1]
        assert "def sample_function" in prompt_data["code"]
        assert "return x + y" in prompt_data["code"]

def test_explain_code_with_custom_parameters():
    """Test explain_code with custom parameters."""
    with patch('csvdiffgpt.tasks.explain_code.get_provider') as mock_get_provider:
        # Set up the mock
        mock_provider = MagicMock()
        mock_provider.query.return_value = "Detailed explanation for beginners"
        mock_provider.format_prompt.return_value = "Mocked prompt"
        mock_get_provider.return_value = mock_provider
        
        # Call explain_code with custom parameters
        result = explain_code(
            code=PYTHON_CODE_SAMPLE,
            detail_level="high",
            audience="beginner",
            focus="dropna function",
            language="python"
        )
        
        # Check that the function called the LLM correctly
        assert result == "Detailed explanation for beginners"
        
        # Check that the parameters were passed to the prompt
        prompt_data = mock_provider.format_prompt.call_args[0][1]
        assert prompt_data["detail_level"] == "high"
        assert prompt_data["audience"] == "beginner"
        assert "dropna function" in prompt_data["focus"]

def test_explain_code_missing_code():
    """Test explain_code with no code provided."""
    with pytest.raises(ValueError, match="No code provided"):
        explain_code()

def test_detect_language():
    """Test the language detection function."""
    from csvdiffgpt.tasks.explain_code import detect_language
    
    # Test Python detection
    assert detect_language(PYTHON_CODE_SAMPLE) == "python"
    
    # Test SQL detection
    assert detect_language(SQL_CODE_SAMPLE) == "sql"
    
    # Test file extension-based detection
    assert detect_language("print('hello')", file_path="script.py") == "python"
    assert detect_language("SELECT * FROM table", file_path="query.sql") == "sql"