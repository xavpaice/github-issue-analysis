# GitHub Issue Analysis

Collect GitHub issues and analyze them with AI to improve issue labeling and categorization.

## Quick Start

1. **Setup Environment**
   ```bash
   uv sync --all-extras
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Collect Issues**
   ```bash
   uv run github-analysis collect --org microsoft --repo vscode --labels bug --limit 5
   ```

3. **Process with AI**
   ```bash
   uv run github-analysis process --task product-labeling
   ```

## For AI Agents

**All agent instructions are in `CLAUDE.md`** - this is the single source of truth for development workflow, commands, and requirements.

## Documentation

See `docs/` directory for user documentation:
- `architecture.md` - System design overview
- `data-schemas.md` - JSON formats and data structures  
- `api-reference.md` - CLI commands and usage
