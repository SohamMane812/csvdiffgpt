# csvdiffgpt

A modular, production-grade package that enables data analysts to work with CSV files using natural language processed by LLMs.

## Features

- Compares two CSV and summarizes the difference
- Validates CSV for data quality issues
- Recommends cleaning steps for data preparation
- Generates automated tests for data quality assurance
- Recommends schema improvements
- Explains data analysis code in natural language
- Summarizes CSV content and structure
- Works with or without LLMs (no API key needed for basic functionality, except for code explanations)

## Installation

```bash
# Basic installation
pip install csvdiffgpt

# With OpenAI support
pip install csvdiffgpt[openai]

# With Gemini support
pip install csvdiffgpt[gemini]

# With all LLM providers
pip install csvdiffgpt[all]
```

## Usage

### Summarize a CSV file
<h3>Parameters</h3>

```python
summarize(
    file: str,
    prompt: Optional[str],
    llm: Optional[LLMProvider] = None,
    model: str = "openai/gemini",
    sep: str = ",",
    max_rows_analyzed: int = 150000,
    max_cols_analyzed: int = 30,
    output: Optional[str] = None,
    api_key: str = "api-key"
)
```
<h3>E.g.: </h3>

```python
from csvdiffgpt import summarize

# Using LLM for insights
result = summarize(
    "path/to/data.csv",
    question="What insights can you give me about this dataset?",
    api_key="your-api-key",
    provider="openai/gemini",
    model="your-desired-model"
)
print(result)

# Without LLM (returns raw metadata)
metadata = summarize(
    "path/to/data.csv",
    use_llm=False  # Returns dictionary
)
print(f"Total rows: {metadata['total_rows']}")
print(f"Columns: {list(metadata['columns'].keys())}")
```

### Compare two CSV files
<h3>Parameters</h3>

```python
compare(
    file_old: str,
    file_new: str,
    prompt: Optional[str] = None,
    llm: Optional[LLMProvider] = None,
    model: str = "gemini/openai",
    sep: str = ",",
    max_rows_analyzed: int = 150000,
    max_cols_analyzed: int = 30,
    output: Optional[str] = None,
    focus_columns: Optional[List[str]] = None,
    api_key: str = "api-key"
)
```
<h3>E.g.:</h3>

```python
from csvdiffgpt import compare

# Using LLM for insights
result = compare(
    file1="path/to/old_data.csv",
    file2="path/to/new_data.csv",
    question="What changed between these versions?",
    api_key="your-api-key",
    provider="openai/gemini",
    model="your-desired-model"
)
print(result)

# Without LLM (returns raw structured data)
comparison_data = compare(
    file1="path/to/old_data.csv",
    file2="path/to/new_data.csv",
    use_llm=False  # Returns dictionary 
)
print(f"Columns only in new file: {comparison_data['comparison']['structural_changes']['only_in_file2']}")
print(f"Row count change: {comparison_data['comparison']['structural_changes']['row_count_change']['difference']}")
```

### Validate a CSV file for data quality issues

<h3>Parameters</h3>

```python
validate(
    file: str,
    prompt: str,
    llm: LLMProvider,
    model: str = "openai/gemini",
    sep: str = ",",
    max_rows_analyzed: int = 150000,
    output: Optional[str] = None,
    api_key: str = "api-key"
)
```
<h3>E.g.:</h3>

```python
from csvdiffgpt import validate

# Using LLM for insights
result = validate(
    "path/to/data.csv",
    question="What data quality issues exist in this file?",
    api_key="your-api-key",
    provider="openai/gemini",
    model="your-desired-model"
)
print(result)

# Without LLM (returns raw validation data)
validation_data = validate(
    "path/to/data.csv",
    use_llm=False,  # Returns dictionary 
    null_threshold=5.0,  # Percentage threshold for missing values
    cardinality_threshold=95.0,  # Threshold for high cardinality warning
    outlier_threshold=3.0  # Z-score threshold for outliers
)

# Check for issues
if validation_data["summary"]["total_issues"] > 0:
    print("Data quality issues found:")
    
    # Print missing value issues
    for issue in validation_data["issues"]["missing_values"]:
        print(f"Column '{issue['column']}' has {issue['null_percentage']}% missing values")
    
    # Print outlier issues
    for issue in validation_data["issues"]["outliers"]:
        print(f"Column '{issue['column']}' has {issue['outlier_count']} outliers")
```

### Get cleaning recommendations for a CSV file

<h3>Parameters</h3>

```python
clean(
    file: str,
    prompt: str,
    llm: LLMProvider,
    model: str = "openai/gemini",
    sep: str = ",",
    output_file: Optional[str] = None,
    preview_changes: bool = True,
    api_key: str = "api-key"
)
```
<h3>E.g.:</h3>

```python
from csvdiffgpt import clean

# Using LLM for detailed cleaning recommendations
result = clean(
    "path/to/data.csv",
    question="How should I clean this dataset for machine learning?",
    api_key="your-api-key",
    provider="openai/gemini",
    model="your-desired-model"
)
print(result)

# Without LLM (returns structured cleaning recommendations with sample code)
cleaning_data = clean(
    "path/to/data.csv",
    use_llm=False
)

# Get cleaning recommendations
for step in cleaning_data["cleaning_recommendations"]:
    print(f"Step {step['priority']}: {step['action']} for column '{step['column']}'")
    print(f"  Reason: {step['reason']}")
    print(f"  Severity: {step['severity']}")
    print()

# Get sample cleaning code
print("Sample cleaning code:")
print(cleaning_data["sample_code"])

# Check potential impact
print(f"Potential impact: {cleaning_data['potential_impact']['rows_affected']} rows affected")
print(f"Data preserved: {cleaning_data['potential_impact']['percentage_data_preserved']}%")
```

### Generate automated tests for a CSV file
<h3>Parameters</h3>

```python
generate_tests(
    file: str,
    prompt: Optional[str],
    llm: LLMProvider,
    model: str = "openai/gemini",
    sep: str = ",",
    output: Optional[str] = None,
    api_key: str = "api-key"
)
```

<h3>E.g.:</h3>

```python
from csvdiffgpt import generate_tests

# Using LLM for detailed test recommendations
result = generate_tests(
    "path/to/data.csv",
    question="What tests should I implement to ensure data quality?",
    api_key="your-api-key",
    provider="openai/gemini",
    model="your-desired-model",
    framework="pytest"  # Options: pytest, great_expectations, dbt
)
print(result)

# Without LLM (returns structured test specifications with code)
test_data = generate_tests(
    "path/to/data.csv",
    use_llm=False,
    framework="pytest"  # Options: pytest, great_expectations, dbt
)

# Get test summary
print(f"Generated {test_data['test_count']} tests:")
for test_type, count in test_data['tests_by_type'].items():
    print(f"- {test_type}: {count} tests")

print(f"Tests by severity:")
for severity, count in test_data['tests_by_severity'].items():
    print(f"- {severity}: {count} tests")

# Save test code to a file
with open("test_data_quality.py", "w") as f:
    f.write(test_data["test_code"])
print("Test code saved to test_data_quality.py")
```

### Get schema restructuring recommendations for a CSV file

<h3>Parameters</h3>

```python
restructure(
    file: str,
    prompt: str,
    llm: LLMProvider,
    model: str = "openai/gemini", 
    sep: str = ",",
    output_file: Optional[str] = None,
    preview_changes: bool = True,
    api_key: str = "api-key"
)
```

<h3>E.g.:</h3>

```python
from csvdiffgpt import restructure

# Using LLM for detailed schema recommendations
result = restructure(
    "path/to/data.csv",
    question="How should I improve the database schema for this dataset?",
    api_key="your-api-key",
    provider="openai/gemini",
    model="your-desired-model",
    format="sql"  # Options: sql, mermaid, python
)
print(result)

# Without LLM (returns structured schema recommendations with code)
restructure_data = restructure(
    "path/to/data.csv",
    use_llm=False,
    format="sql",  # Options: sql, mermaid, python
    table_name="my_table"  # Optional name for the database table
)

# Get restructuring summary
print(f"Generated {restructure_data['recommendation_count']} recommendations:")
for rec_type, count in restructure_data['recommendations_by_type'].items():
    print(f"- {rec_type}: {count} recommendations")

print(f"Recommendations by severity:")
for severity, count in restructure_data['recommendations_by_severity'].items():
    print(f"- {severity}: {count} recommendations")

# Save SQL code to a file
with open("restructure_schema.sql", "w") as f:
    f.write(restructure_data["output_code"])
print("SQL schema saved to restructure_schema.sql")
```

### Explain data analysis code

<h3>Parameters</h3>

```python
explain_code(
    code: str,
    llm: LLMProvider,
    model: str = "openai/gemini",
    language: Literal["pandas", "sql"] = "pandas",
    output: Optional[str] = None,
    detail_level: Optional[str],  # Options: "high", "medium", "low"
    audience: Optional[str],  # Target audience for explanation: "beginner", "data_analyst", "data_scientist", "developer", "technical", "non_technical"
    api_key: str = "api-key"
)
```

<h3>E.g.:</h3>

```python
from csvdiffgpt import explain_code

# Explain code from a string
code = """
import pandas as pd
df = pd.read_csv('data.csv')
result = df.groupby('category').agg({
    'value': ['mean', 'sum', 'count']
}).reset_index()
"""

explanation = explain_code(
    code=code,
    detail_level="medium",  # Options: "high", "medium", "low"
    audience="data_analyst",  # Target audience for explanation: "beginner", "data_analyst", "data_scientist", "developer", "technical", "non_technical"
    api_key="your-api-key",
    provider="openai/gemini",
    model="your-desired-model"
)
print(explanation)

# Explain code from a file
explanation = explain_code(
    file_path="path/to/analysis_script.py",
    focus="data cleaning section",  # Optional focus on specific part
    audience="beginner"  # Simpler explanations for beginners
)
print(explanation)

# Explain a function object
def process_data(df):
    # Clean data
    df = df.dropna()
    # Transform data
    df['new_col'] = df['col1'] / df['col2']
    # Return result
    return df.groupby('category').mean()

explanation = explain_code(
    code_object=process_data,  # Pass the function directly
    detail_level="high"  # Detailed explanation
)
print(explanation)
```

## CLI Usage

The package provides a command-line interface for easy use:

```bash
# Summarize a CSV file
csvdiffgpt summarize data.csv --api-key your-api-key --provider openai/gemini --model desired-model

# Compare two CSV files
csvdiffgpt compare old.csv new.csv --api-key your-api-key --provider openai/gemini --model desired-model

# Validate a CSV file for data quality issues
csvdiffgpt validate data.csv --api-key your-api-key --provider openai/gemini --model desired-model

# Get cleaning recommendations
csvdiffgpt clean data.csv --api-key your-api-key --provider openai/gemini --model desired-model

# Generate tests for data quality
csvdiffgpt generate-tests data.csv --api-key your-api-key --provider openai/gemini --model desired-model --framework pytest --output tests/test_data.py

# Get schema restructuring recommendations
csvdiffgpt restructure data.csv --api-key your-api-key --provider openai/gemini --model desired-model --format sql --output schema.sql

# Explain code from a file
csvdiffgpt explain-code script.py --api-key your-api-key --provider openai/gemini --model desired-model --detail-level high --output explanation.md

# Explain code snippet directly
csvdiffgpt explain-code --code "import pandas as pd; df = pd.read_csv('data.csv')" --api-key your-api-key --provider openai/gemini --model desired-model
```

## Supported Test Frameworks

The `generate_tests` function supports multiple testing frameworks:

- **pytest**: Standard Python testing framework
- **Great Expectations**: Data validation framework with rich expectations
- **dbt**: Data build tool with YAML-based tests

## Supported Output Formats for Restructure

The `restructure` function supports multiple output formats:

- **sql**: SQL DDL statements for creating optimized tables
- **mermaid**: Mermaid ER diagram code for visualizing the data model
- **python**: Python code using pandas to transform the data structure

## Supported Languages for Code Explanation

The `explain_code` function supports:

- **Python**: Data analysis scripts, functions, classes
- **SQL**: Queries, stored procedures, DDL statements

## Supported LLM Providers

- OpenAI
- Google Gemini
- More coming soon!

## Development

Clone the repository and install the development dependencies:

```bash
git clone https://github.com/yourusername/csvdiffgpt.git
cd csvdiffgpt
pip install -e ".[dev]"
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.