# API Reference

## CLI Commands

### collect
Collect GitHub issues and save them locally.

```bash
uv run github-analysis collect [OPTIONS]
```

**Options:**
- `--org, -o TEXT`: GitHub organization name (required)
- `--repo, -r TEXT`: GitHub repository name (optional for org-wide search)
- `--issue-number INTEGER`: Specific issue number to collect
- `--labels, -l TEXT`: Filter by labels (can be used multiple times)
- `--state TEXT`: Issue state: open, closed, or all (default: closed)
- `--limit INTEGER`: Maximum number of issues to collect (default: 10)
- `--token TEXT`: GitHub API token (defaults to GITHUB_TOKEN env var)
- `--download-attachments / --no-download-attachments`: Download issue and comment attachments (default: true)
- `--max-attachment-size INTEGER`: Maximum attachment size in MB (default: 10)

**Collection Modes:**
- **Single issue:** `--org ORGNAME --repo REPONAME --issue-number NUMBER`
- **Organization-wide:** `--org ORGNAME` (searches all repos in org)
- **Repository-specific:** `--org ORGNAME --repo REPONAME`

**Examples:**
```bash
# Collect single issue
uv run github-analysis collect --org replicated-collab --repo pixee-replicated --issue-number 71

# Collect from entire organization (20 most recent closed issues)
uv run github-analysis collect --org replicated-collab --limit 20

# Collect bugs from specific repository
uv run github-analysis collect --org microsoft --repo vscode --labels bug --limit 5
```

### process
AI processing commands for collected issues.

```bash
uv run github-analysis process [COMMAND] [OPTIONS]
```

#### product-labeling
Analyze GitHub issues for product labeling recommendations with optional image processing.

```bash
uv run github-analysis process product-labeling [OPTIONS]
```

**Options:**
- `--org, -o TEXT`: GitHub organization name
- `--repo, -r TEXT`: GitHub repository name
- `--issue-number INTEGER`: Specific issue number to process
- `--model TEXT`: AI model to use (e.g., 'openai:gpt-4o-mini')
- `--include-images / --no-include-images`: Include image analysis (default: true)
- `--dry-run / --no-dry-run`: Show what would be processed without running AI (default: false)

**Examples:**
```bash
# Process all collected issues for a repository
uv run github-analysis process product-labeling --org myorg --repo myrepo

# Process a specific issue with custom model
uv run github-analysis process product-labeling --org myorg --repo myrepo --issue-number 123 --model openai:gpt-4o

# Dry run to see what would be processed
uv run github-analysis process product-labeling --org myorg --repo myrepo --dry-run
```

### status
Show storage status and statistics.

```bash
uv run github-analysis status
```

Displays:
- Total number of issues in storage
- Storage size and location
- Issues breakdown by repository

### version
Show version information.

```bash
uv run github-analysis version
```

## Development Commands

```bash
# Setup
uv sync --all-extras

# Code quality (run all four - required before commit)
uv run ruff check --fix --unsafe-fixes && uv run black . && uv run mypy . && uv run pytest

# Individual tools
uv run ruff check --fix --unsafe-fixes  # Code quality and imports
uv run black .                          # Code formatting
uv run mypy .                           # Type checking
uv run pytest                          # Run tests
```