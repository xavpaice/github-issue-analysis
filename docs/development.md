# Development Guide

## Setup

```bash
# Clone and setup
git clone <repo-url>
cd github-issue-analysis
uv sync --dev

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

## Project Structure

```
github_issue_analysis/     # Main package
├── cli/                   # Command-line interface
├── github_client/         # GitHub API integration  
├── ai/                   # AI processing
└── storage/              # Data persistence

data/                     # Runtime data
├── issues/              # Collected GitHub issues (JSON)
└── results/             # AI analysis results (JSON)

tasks/                   # Agent development tasks (markdown)
trees/                   # Git worktrees for development
docs/                    # Documentation
tests/                   # Test suite
```

## Dependency Management

**IMPORTANT:** All dependencies must be managed through pyproject.toml to ensure proper tracking and reproducible builds.

```bash
# Add new dependencies
uv add package-name              # Runtime dependency
uv add --dev package-name        # Development dependency

# Remove dependencies  
uv remove package-name           # Removes from pyproject.toml and environment

# Sync environment with pyproject.toml
uv sync                          # Production dependencies only
uv sync --dev                    # Include development dependencies
```

**Never use `pip install` or `pip uninstall` directly** - always use `uv add/remove` to maintain dependency tracking.

## Development Workflow

### Standard Development
```bash
# Make changes
# Run quality checks
uv run ruff check --fix && uv run black . && uv run mypy .
# Run tests  
uv run pytest
```

### Agent Development
```bash
# Create worktree for task
git worktree add trees/task-name -b feature/task-name
cd trees/task-name

# Develop feature
# Test and validate
# Document progress in tasks/task-name.md
```

## Testing

- Unit tests for core logic
- Integration tests for CLI commands
- Mock external APIs (GitHub, OpenAI, Anthropic)
- Test error conditions and edge cases

## Code Standards

- Python 3.12+
- Type hints required
- Pydantic models for data validation
- Comprehensive error handling
- Follow existing patterns and naming