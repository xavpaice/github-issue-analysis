# GitHub Issue Analysis

Collect GitHub issues and analyze them with AI to improve issue labeling and categorization.

## Quick Start

1. **Setup Environment**
   ```bash
   uv sync --dev
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

**Start Here:**
1. Read `docs/agent-guide.md` for development workflow
2. Pick a task from `tasks/` directory
3. Create worktree: `git worktree add trees/task-name -b feature/task-name`
4. Follow task specifications exactly

**Current Available Tasks:**
- `github-issue-collection.md` - Core GitHub API integration (start here)
- `ai-product-labeling.md` - AI analysis system
- `github-attachment-collection.md` - Download issue attachments
- `storage-querying-system.md` - Data management utilities

## Architecture

See `docs/` directory for complete documentation:
- `architecture.md` - System design overview
- `data-schemas.md` - JSON formats and data structures  
- `api-reference.md` - CLI commands and usage
- `development.md` - Setup and development workflow