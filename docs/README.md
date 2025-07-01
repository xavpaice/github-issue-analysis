# GitHub Issue Analysis Documentation

User documentation for the GitHub issue collection and AI analysis tool.

## Documentation Structure

- [Architecture](architecture.md) - System design and component overview
- [API Reference](api-reference.md) - CLI commands and usage
- [Data Schemas](data-schemas.md) - JSON schemas for issues and results

## Quick Start

1. Set up environment: `uv sync --all-extras`
2. Configure `.env` file with API keys
3. Collect issues: `uv run github-analysis collect --org myorg --repo myrepo`
4. Process issues: `uv run github-analysis process --task product-labeling`

## For AI Agents

**See `CLAUDE.md` in the project root** - this contains all agent development instructions, workflow, and requirements.