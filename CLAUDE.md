# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Setup:**
```bash
uv sync --dev                    # Install dependencies with dev tools
cp .env.example .env            # Set up environment (edit with API keys)
```

**If dev dependencies aren't installed properly:**
```bash
uv add --dev pytest pytest-asyncio pytest-mock ruff black mypy  # Explicitly install dev tools
uv run pytest --version        # Verify pytest is available
```

**Dependency Management:**
```bash
uv add package-name              # Add new dependency (updates pyproject.toml)
uv add --dev package-name        # Add development dependency
uv remove package-name           # Remove dependency (updates pyproject.toml)
uv sync                          # Sync environment with pyproject.toml
```
**IMPORTANT:** Always use `uv add/remove` instead of `pip install/uninstall` to maintain dependency tracking in pyproject.toml.

**Quality Checks:**
```bash
uv run pytest                   # Run test suite (MUST PASS before commit)
uv run ruff check --fix          # Format and lint (MUST PASS before commit)  
uv run black .                   # Code formatting (auto-applies fixes)
uv run mypy .                    # Type checking (ideal but not required for commit)
```

**IMPORTANT Pre-Commit Requirements:**
- All tests MUST pass: `uv run pytest tests/ -v`
- Ruff linting MUST pass: `uv run ruff check`
- Black formatting should be applied: `uv run black .`
- MyPy type checking is recommended but not required for commit

**CLI Usage:**
```bash
uv run github-analysis collect --org myorg --repo myrepo     # Collect GitHub issues
uv run github-analysis status                               # Show storage statistics  
uv run github-analysis version                              # Check version
# uv run github-analysis process --task product-labeling    # Process with AI (future)
```

## Architecture

This is a Python CLI tool for GitHub issue collection and AI-powered analysis using a modular architecture:

### Core Structure
- **CLI Layer** (`cli/`): Typer-based command interface
- **GitHub Client** (`github_client/`): API integration with rate limiting and pagination
- **AI Processing** (`ai/`): OpenAI and Anthropic analysis capabilities
- **Storage** (`storage/`): JSON-based data persistence

### Data Flow
GitHub API → Issue Collection → JSON Storage (`data/issues/`) → AI Processing → Results (`data/results/`)

### Agent Development Workflow
This project uses a worktree-based development model for agents:

1. Read task specification from `tasks/task-name.md`
2. Create worktree: `git worktree add trees/task-name -b feature/task-name`
3. Implement feature with full test coverage in the worktree
4. Document progress in the task markdown file
5. Create pull request when complete

### Key Technologies
- **Python 3.12+** with strict typing
- **Pydantic** for data validation and models
- **Typer + Rich** for CLI interface
- **httpx** for HTTP requests
- **pytest** for testing with asyncio support

### Configuration
- Environment variables defined in `.env` (copy from `.env.example`)
- Required: `GITHUB_TOKEN`, `OPENAI_API_KEY`
- Optional: `ANTHROPIC_API_KEY`, `GITHUB_API_BASE_URL`, `LOG_LEVEL`