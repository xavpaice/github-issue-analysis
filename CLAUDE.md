# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Required Commands

**Setup:**
```bash
uv sync --all-extras             # Install all dependencies including dev tools
cp .env.example .env            # Set up environment (edit with API keys)
```

**Dependency Management:**
```bash
uv add package-name              # Add new dependency (updates pyproject.toml)
uv add --dev package-name        # Add development dependency
uv remove package-name           # Remove dependency (updates pyproject.toml)
uv sync                          # Sync environment with pyproject.toml
```
Always use `uv add/remove` instead of `pip install/uninstall` to maintain dependency tracking in pyproject.toml.

**Quality Checks (Required Before Every Commit):**
```bash
uv run ruff check --fix --unsafe-fixes && uv run black . && uv run mypy . && uv run pytest
```

All four tools must pass:
- **Ruff**: Code quality, imports, style violations
- **Black**: Code formatting consistency  
- **MyPy**: Type checking and type annotations
- **Pytest**: All tests must pass

**Runtime Requirements:**
- Never use `python` directly - Always use `uv run python` or `uv run <command>`
- Add type annotations during development, not after mypy fails
- Use specific types from `typing` module, avoid `Any`

**Type Annotation Examples:**
```python
from typing import List, Dict, Optional

def process_issues(issues: List[Dict[str, Any]]) -> Optional[str]:
    """Process GitHub issues and return summary."""
    data: Dict[str, Any] = {...}
    return result
```

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

### Reference Documentation
When implementing features, consult these docs for detailed specifications:
- `docs/architecture.md` - Component details and design principles
- `docs/data-schemas.md` - JSON schemas for issues, results, and tasks
- `docs/api-reference.md` - CLI commands and options

## Agent Development Workflow

**Step-by-Step Process:**

1. Read task specification from `tasks/task-name.md`
2. Create worktree: `git worktree add trees/task-name -b feature/task-name`
3. Change directory: `cd trees/task-name`
4. Install dependencies: `uv sync --all-extras`
5. Implement feature with full test coverage following existing patterns
6. Run quality checks: `uv run ruff check --fix --unsafe-fixes && uv run black . && uv run mypy . && uv run pytest`
7. Commit changes and push branch (follow git commit requirements above)
8. Create pull request with detailed description and test plan
9. Mark task status as "complete" in `tasks/task-name.md`
10. Commit and push the status update

**Implementation Requirements:**
- Deliver complete functionality, not partial implementation
- Add CLI interface for new features
- Use Pydantic models for data validation
- Follow existing code structure and naming conventions
- Write comprehensive tests (unit and integration)
- Add type hints throughout
- Implement proper error handling

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

## Git Commit Requirements

**NEVER credit yourself in git commit messages** - this is a critical requirement that agents frequently violate.

Standard commit messages should focus on the change, not the author:
- ✅ Good: "Add user authentication validation"
- ❌ Bad: "Add user authentication validation 🤖 Generated with Claude Code"

Only use the standard co-author format when explicitly requested by the user.

## GitHub CLI Usage

**IMPORTANT Token Configuration:**
- For **testing the program** (collecting issues): Use `GITHUB_TOKEN` (required for accessing test repositories)
- For **GitHub CLI operations** (creating PRs, viewing repos): Use `GITHUB_PERSONAL_ACCESS_TOKEN`

**GitHub CLI Commands:**
```bash
# Create pull requests (use GITHUB_PERSONAL_ACCESS_TOKEN)
GITHUB_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN gh pr create --title "Title" --body "Body"

# View repository information (use GITHUB_PERSONAL_ACCESS_TOKEN) 
GITHUB_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN gh repo view

# Testing the CLI tool (use GITHUB_TOKEN for test repo access)
uv run github-analysis collect --org replicated-collab --repo pixee-replicated --issue-number 71
```

**Why Two Tokens:**
- `GITHUB_TOKEN`: Has access to test repositories but limited GitHub API permissions
- `GITHUB_PERSONAL_ACCESS_TOKEN`: Has full GitHub API permissions for repository operations
