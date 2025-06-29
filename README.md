# csvdiffgpt

A modular, production-grade package that enables data analysts to work with CSV files using natural language processed by LLMs.

## Features

- Compare two CSVs and summarize differences
- Validate, clean, and restructure CSVs
- Generate tests, charts, or code explanations using LLMs

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
    question="e.g. What insights can you give me about this dataset?",
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

```python
from csvdiffgpt import compare

# Using LLM for insights
result = compare(
    file1="path/to/old_data.csv",
    file2="path/to/new_data.csv",
    question="e.g. What changed between these versions?",
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

## CLI Usage

The package provides a command-line interface for easy use:

```bash
# Summarize a CSV file
csvdiffgpt summarize data.csv --api-key <your-api-key> --provider <openai/gemini>

# Summarize without using LLM (no API key needed)
csvdiffgpt summarize data.csv --no-llm

# Compare two CSV files
csvdiffgpt compare old.csv new.csv --api-key <your-api-key> --provider <openai/gemini>

# Compare without using LLM (no API key needed)
csvdiffgpt compare old.csv new.csv --no-llm
```

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

This project is licensed under the APACHE Version 2.0 License - see the [LICENSE](LICENSE) file for details.
