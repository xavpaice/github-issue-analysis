# GitHub Issue Analysis Documentation

This project provides GitHub issue collection and AI-powered analysis capabilities.

## Documentation Structure

- [Architecture](architecture.md) - System design and component overview
- [Development Guide](development.md) - How to set up and develop the project
- [Agent Guide](agent-guide.md) - Instructions for AI agents working on tasks
- [API Reference](api-reference.md) - CLI commands and usage
- [Data Schemas](data-schemas.md) - JSON schemas for issues and results

## Quick Start

1. Set up environment: `uv sync --dev`
2. Configure `.env` file with API keys
3. Collect issues: `uv run github-analysis collect --org myorg --repo myrepo`
4. Process issues: `uv run github-analysis process --task product-labeling`

## Agent Development

Agents should:
1. Read task from `tasks/` folder
2. Create worktree in `trees/` with task-based branch
3. Implement full-stack feature with tests
4. Document progress in task markdown file