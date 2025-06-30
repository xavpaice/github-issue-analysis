# API Reference

## CLI Commands

### collect
Fetch issues from GitHub using advanced search.

```bash
uv run github-analysis collect [OPTIONS]
```

**Options:**
- `--org TEXT`: GitHub organization name
- `--repo TEXT`: Repository name  
- `--labels TEXT`: Comma-separated label names
- `--since DATE`: Issues created after date (ISO format)
- `--until DATE`: Issues created before date (ISO format)
- `--state [open|closed|all]`: Issue state filter (default: open)
- `--limit INT`: Maximum issues to collect
- `--download-attachments / --no-download-attachments`: Download issue attachments (default: true)

**Examples:**
```bash
# Collect all open bugs from microsoft/vscode
uv run github-analysis collect --org microsoft --repo vscode --labels bug

# Collect issues from last month
uv run github-analysis collect --org myorg --repo myrepo --since 2024-01-01 --until 2024-02-01
```

### process
Run AI analysis on collected issues.

```bash
uv run github-analysis process [OPTIONS]
```

**Options:**
- `--task TEXT`: Processing task name (required)
- `--model TEXT`: AI model to use (default: gpt-4o-mini)
- `--org TEXT`: Filter by organization
- `--repo TEXT`: Filter by repository
- `--issue INT`: Process specific issue number

**Examples:**
```bash
# Run product labeling on all collected issues
uv run github-analysis process --task product-labeling

# Process specific issue with Claude
uv run github-analysis process --task product-labeling --model claude-3-haiku --issue 123
```

## Development Commands

```bash
# Setup
uv sync --dev

# Code quality
uv run ruff check --fix
uv run black .
uv run mypy .

# Testing
uv run pytest
uv run pytest -v tests/specific_test.py
```