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
uv run github-analysis process product-labeling --org myorg --repo myrepo --issue-number 123 --model openai:o4-mini

# Dry run to see what would be processed
uv run github-analysis process product-labeling --org myorg --repo myrepo --dry-run
```

### update-labels
Update GitHub issue labels based on AI recommendations from product-labeling analysis.

```bash
uv run github-analysis update-labels [OPTIONS]
```

**Required Setup:**
- Set `GITHUB_TOKEN` environment variable with a token that has write access to the repository
- Must have AI analysis results from `process product-labeling` command

**Options:**
- `--org TEXT`: GitHub organization name (required)
- `--repo TEXT`: GitHub repository name (required for single repo operations)
- `--issue-number INTEGER`: Specific issue number to update
- `--min-confidence FLOAT`: Minimum confidence threshold for applying changes (default: 0.8)
- `--dry-run / --no-dry-run`: Preview changes without applying them (default: false)
- `--skip-comments / --no-skip-comments`: Update labels but don't post explanatory comments (default: false)
- `--force / --no-force`: Apply even low-confidence changes (default: false)
- `--max-issues INTEGER`: Maximum number of issues to process
- `--delay FLOAT`: Delay between API calls in seconds (default: 0.0)
- `--data-dir TEXT`: Data directory path (defaults to ./data)

**Workflow:**
1. First collect issues: `uv run github-analysis collect --org myorg --repo myrepo`
2. Run AI analysis: `uv run github-analysis process product-labeling --org myorg --repo myrepo`
3. Update labels: `uv run github-analysis update-labels --org myorg --repo myrepo`

**Examples:**
```bash
# Preview changes for a specific issue (safe to run)
uv run github-analysis update-labels --org myorg --repo myrepo --issue-number 123 --dry-run

# Update all issues in a repository with high confidence threshold
uv run github-analysis update-labels --org myorg --repo myrepo --min-confidence 0.9

# Update specific issue with custom confidence threshold
uv run github-analysis update-labels --org myorg --repo myrepo --issue-number 123 --min-confidence 0.75

# Apply all changes regardless of confidence (use with caution)
uv run github-analysis update-labels --org myorg --repo myrepo --force

# Update labels without posting explanatory comments
uv run github-analysis update-labels --org myorg --repo myrepo --skip-comments

# Process up to 5 issues with 1 second delay between API calls
uv run github-analysis update-labels --org myorg --repo myrepo --max-issues 5 --delay 1.0
```

**Safety Features:**
- **Dry-run mode**: Always test with `--dry-run` first to preview changes, including exact GitHub comments that will be posted
- **Confidence thresholds**: Only applies changes above specified confidence level
- **User confirmation**: Prompts for confirmation before batch operations
- **Smart detection**: Only updates issues that actually need changes
- **Rate limiting**: Respects GitHub API limits and includes delay options
- **Error handling**: Continues processing other issues if one fails

**What It Does:**
1. **Analyzes AI recommendations** from product-labeling results
2. **Compares current labels** with AI recommendations
3. **Identifies needed changes** (additions/removals) above confidence threshold
4. **Updates GitHub labels** via API calls
5. **Posts explanatory comments** with AI reasoning (unless skipped)
6. **Provides detailed feedback** on what was changed and any failures

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