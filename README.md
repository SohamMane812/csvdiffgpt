# csvdiffgpt

A modular, production-grade package that enables data analysts to work with CSV files using natural language processed by LLMs.

## Features

- Compare two CSVs and summarize differences
- Validate CSVs for data quality issues
- Recommend cleaning steps for data preparation
- Summarize CSV content and structure
- Works with or without LLMs (no API key needed for basic functionality)

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
    use_llm=False  # Returns dictionary instead of string
)
print(f"Total rows: {metadata['total_rows']}")
print(f"Columns: {list(metadata['columns'].keys())}")
```

### Compare two CSV files

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
    use_llm=False  # Returns dictionary instead of string
)
print(f"Columns only in new file: {comparison_data['comparison']['structural_changes']['only_in_file2']}")
print(f"Row count change: {comparison_data['comparison']['structural_changes']['row_count_change']['difference']}")
```

### Validate a CSV file for data quality issues

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
    use_llm=False,  # Returns dictionary instead of string
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

## CLI Usage

The package provides a command-line interface for easy use:

```bash
# Summarize a CSV file
csvdiffgpt summarize data.csv --api-key your-api-key --provider gemini

# Summarize without using LLM (no API key needed)
csvdiffgpt summarize data.csv --no-llm

# Compare two CSV files
csvdiffgpt compare old.csv new.csv --api-key your-api-key --provider gemini

# Compare without using LLM (no API key needed)
csvdiffgpt compare old.csv new.csv --no-llm

# Validate a CSV file for data quality issues
csvdiffgpt validate data.csv --api-key your-api-key --provider gemini

# Validate without using LLM (no API key needed)
csvdiffgpt validate data.csv --no-llm --null-threshold 10.0 --outlier-threshold 2.5

# Get cleaning recommendations
csvdiffgpt clean data.csv --api-key your-api-key --provider gemini

# Get cleaning recommendations without LLM (no API key needed)
csvdiffgpt clean data.csv --no-llm
```

## Supported LLM Providers

- OpenAI (GPT-4, GPT-3.5)
- Google Gemini
- More coming soon!

## Development

Clone the repository and install the development dependencies:

```bash
git clone https://github.com/SohamMane812/csvdiffgpt.git
cd csvdiffgpt
pip install -e ".[dev]"
```

## License

This project is licensed under the APACHE Version 2.0 License - see the [LICENSE](LICENSE) file for details.
