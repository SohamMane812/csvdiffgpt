# Contributing to csvdiffgpt

Thank you for your interest in contributing to csvdiffgpt!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/csvdiffgpt.git
   cd csvdiffgpt
   ```

2. Create a virtual environment and install development dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. Install the specific LLM provider dependencies you need:
   ```bash
   pip install -e ".[openai]"  # For OpenAI
   pip install -e ".[gemini]"  # For Google Gemini
   pip install -e ".[claude]"  # For Anthropic Claude
   # Or install all providers:
   pip install -e ".[all]"
   ```

## Development Workflow

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and add tests if applicable

3. Run tests:
   ```bash
   pytest
   ```

4. Format your code:
   ```bash
   black csvdiffgpt
   isort csvdiffgpt
   ```

5. Commit your changes:
   ```bash
   git add .
   git commit -m "Add your meaningful commit message here"
   ```

6. Push your branch to GitHub:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Create a Pull Request on GitHub

## Adding New Features

### New LLM Provider

To add a new LLM provider:

1. Create a new file in `csvdiffgpt/llm/` (e.g., `yourprovider.py`)
2. Implement the provider class extending `LLMProvider`
3. Add the provider to the `LLM_PROVIDERS` dictionary in each task file
4. Update optional dependencies in `pyproject.toml`

### New Task

To add a new task:

1. Create a new file in `csvdiffgpt/tasks/` (e.g., `yourtask.py`)
2. Implement the task function
3. Create a prompt template in `csvdiffgpt/llm/prompts/yourtask.txt`
4. Add the task to `csvdiffgpt/__init__.py`
5. Add the task to the CLI in `csvdiffgpt/cli.py`

## Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for all functions and classes
- Keep code modular and testable