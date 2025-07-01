# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

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
**IMPORTANT:** Always use `uv add/remove` instead of `pip install/uninstall` to maintain dependency tracking in pyproject.toml.

**Quality Checks (All Required Before Commit):**
```bash
# Complete linting suite - all must pass:
uv run ruff check --fix --unsafe-fixes  # Code linting and formatting fixes (with unsafe fixes)
uv run black .                          # Code formatting (auto-applies fixes)  
uv run mypy .                           # Type checking (REQUIRED)
uv run pytest                          # Run test suite (REQUIRED)
```

**CRITICAL: "Linting" includes ALL of the above tools:**
- **Ruff**: Code quality, imports, style violations
- **Black**: Code formatting consistency  
- **MyPy**: Type checking and type annotations
- **Pytest**: All tests must pass

**IMPORTANT Pre-Commit Requirements:**
- ALL quality checks MUST pass before commit
- Run the complete command: `uv run ruff check --fix --unsafe-fixes && uv run black . && uv run mypy . && uv run pytest`
- Let automated tools fix linting errors - don't fix manually
- No exceptions - mypy is REQUIRED, not optional

**CRITICAL REQUIREMENTS FOR AGENTS:**
- **NEVER use `python` directly** - Always use `uv run python` or `uv run <command>`
- **ALWAYS add type annotations during development** - Don't wait for mypy to fail, add proper typing as you write code
- **ALWAYS run type checking** - `mypy .` is mandatory for all code changes
- **Use specific types, not `Any`** - Import proper types from typing module
- **Run full quality checks** - All three commands (ruff, black, mypy) must pass

**IMPORTANT: Type annotations should be added DURING development, not after mypy fails. This reduces rework and catches issues early:**
- Add return type annotations to all functions: `def func() -> RetType:`
- Add parameter type annotations: `def func(param: ParamType) -> RetType:`
- Use proper type hints from `typing` module: `List[str]`, `Dict[str, Any]`, `Optional[int]`
- Annotate complex variables: `data: Dict[str, Any] = {...}`

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

**CRITICAL: Always create worktree BEFORE starting any work!**

1. **FIRST:** Read task specification from `tasks/task-name.md` to understand requirements and determine appropriate branch naming
2. **IMMEDIATELY:** Create worktree: `git worktree add trees/task-name -b feature/task-name`
3. **CHANGE DIRECTORY:** `cd trees/task-name` - All work must be done in the worktree
4. Implement feature with full test coverage in the worktree
5. Document progress in the task markdown file
6. **BEFORE committing:** Verify all tests pass and linting passes
7. Commit changes and push branch
8. Create pull request with detailed description and test plan
9. **IMMEDIATELY mark task status as "complete"** in `tasks/task-name.md`
10. Commit and push the status update

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

## Git Practices

- **NEVER credit yourself in git commit messages**

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
