# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Setup:**
```bash
uv sync --dev                    # Install dependencies with dev tools
cp .env.example .env            # Set up environment (edit with API keys)
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
uv run ruff check --fix && uv run black . && uv run mypy .  # Format, lint, type check
uv run pytest                   # Run test suite
```

**CRITICAL REQUIREMENTS FOR AGENTS:**
- **NEVER use `python` directly** - Always use `uv run python` or `uv run <command>`
- **ALWAYS run type checking** - `mypy .` is mandatory for all code changes
- **Use specific types, not `Any`** - Import proper types from typing module
- **Run full quality checks** - All three commands (ruff, black, mypy) must pass

**CLI Usage:**
```bash
uv run github-analysis collect --org myorg --repo myrepo     # Collect GitHub issues
uv run github-analysis process --task product-labeling      # Process with AI
uv run github-analysis version                              # Check version
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

### Typing Guidelines
- Use specific types from `typing` module: `List[str]`, `Dict[str, Any]`, `Optional[int]`
- For complex types, define Pydantic models or TypedDict classes
- Use `Union[X, Y]` or `X | Y` (Python 3.10+) instead of `Any`
- Example good typing:
  ```python
  from typing import List, Dict, Optional
  
  def process_issues(issues: List[Dict[str, Any]]) -> Optional[str]:
      """Process GitHub issues and return summary."""
      ...
  ```

### Configuration
- Environment variables defined in `.env` (copy from `.env.example`)
- Required: `GITHUB_TOKEN`, `OPENAI_API_KEY`
- Optional: `ANTHROPIC_API_KEY`, `GITHUB_API_BASE_URL`, `LOG_LEVEL`