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
- `--exclude-repo, -x TEXT`: Repository to exclude from organization-wide search (can be used multiple times)
- `--exclude-repos TEXT`: Comma-separated list of repositories to exclude from organization-wide search

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

# Organization-wide collection excluding specific repositories
uv run github-analysis collect --org replicated-collab --exclude-repo private-repo --limit 15

# Exclude multiple repositories using multiple flags
uv run github-analysis collect --org replicated-collab --exclude-repo private-repo --exclude-repo test-repo --limit 10

# Exclude multiple repositories using comma-separated list
uv run github-analysis collect --org replicated-collab --exclude-repos "private-repo,test-repo,archived-repo" --limit 10

# Mix both exclusion approaches with additional filters
uv run github-analysis collect --org microsoft --exclude-repo private-repo --exclude-repos "test-repo,docs-repo" --labels bug --state open --limit 20
```

### batch (RECOMMENDED)
**Batch processing for cost-effective AI analysis (50% cheaper than individual processing).**

```bash
uv run github-analysis batch [COMMAND] [OPTIONS]
```

#### submit
Submit a batch processing job for multiple issues.

```bash
uv run github-analysis batch submit product-labeling [OPTIONS]
```

**Options:**
- `--org, -o TEXT`: GitHub organization name
- `--repo, -r TEXT`: GitHub repository name (optional for org-wide processing)
- `--issue-number INTEGER`: Specific issue number to process
- `--model TEXT`: AI model to use (e.g., 'openai:gpt-4o-mini', 'openai:o4-mini')
- `--thinking-effort TEXT`: Reasoning effort level for thinking models (low, medium, high)
- `--thinking-budget INTEGER`: Thinking token budget for Anthropic/Google models
- `--include-images / --no-include-images`: Include image analysis (default: true)

**Examples:**
```bash
# Batch process all collected issues for an organization (RECOMMENDED)
uv run github-analysis batch submit product-labeling --org myorg

# Batch process all issues for a specific repository
uv run github-analysis batch submit product-labeling --org myorg --repo myrepo

# Batch process with specific model
uv run github-analysis batch submit product-labeling --org myorg --model openai:gpt-4o-mini
```

#### status
Check the status of a batch processing job.

```bash
uv run github-analysis batch status <job-id>
```

#### collect
Collect and process results from a completed batch job.

```bash
uv run github-analysis batch collect <job-id>
```

#### list
List all batch processing jobs.

```bash
uv run github-analysis batch list
```

#### cancel
Cancel an active batch processing job.

```bash
uv run github-analysis batch cancel <job-id>
```

**Notes:**
- Only jobs in states `pending`, `validating`, `in_progress`, or `finalizing` can be cancelled
- Already completed, failed, or cancelled jobs will show their current status without error
- Cancelling a job prevents further API charges for that batch

#### remove
Remove a batch job record and associated files.

```bash
uv run github-analysis batch remove <job-id>
uv run github-analysis batch remove <job-id> --force
```

**Options:**
- `--force`: Skip confirmation prompts

**Notes:**
- Removes job metadata file and associated input/output files
- Warns if job is still active and requires confirmation (or `--force` flag)
- Cannot be undone - use with caution

**Typical Batch Workflow:**
```bash
# 1. Collect issues
uv run github-analysis collect --org myorg --limit 30

# 2. Submit batch job
uv run github-analysis batch submit product-labeling --org myorg

# 3. Check status periodically (shows real-time progress)
uv run github-analysis batch status <job-id>

# 4. Collect results when completed
uv run github-analysis batch collect <job-id>

# 5. Update labels with dry run first
uv run github-analysis update-labels --org myorg --dry-run
```

### process
**Individual AI processing commands (use only for single issues or testing).**

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
- `--model TEXT`: AI model to use (e.g., 'openai:gpt-4o-mini', 'openai:o4-mini')
- `--thinking-effort TEXT`: Reasoning effort level for thinking models (low, medium, high)
- `--thinking-budget INTEGER`: Thinking token budget for Anthropic/Google models
- `--include-images / --no-include-images`: Include image analysis (default: true)
- `--dry-run / --no-dry-run`: Show what would be processed without running AI (default: false)

**Examples:**
```bash
# Process all collected issues for a repository
uv run github-analysis process product-labeling --org myorg --repo myrepo

# Process a specific issue with custom model
uv run github-analysis process product-labeling --org myorg --repo myrepo --issue-number 123 --model openai:o4-mini

# Process with thinking model and reasoning effort
uv run github-analysis process product-labeling --org myorg --repo myrepo --issue-number 123 --model openai:o4-mini --thinking-effort medium

# Process with Anthropic thinking model and budget
uv run github-analysis process product-labeling --org myorg --repo myrepo --issue-number 123 --model anthropic:claude-3-5-sonnet-latest --thinking-budget 2048

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

**Recommended Workflow (Batch Processing):**
1. Collect issues: `uv run github-analysis collect --org myorg --limit 30`
2. Submit batch job: `uv run github-analysis batch submit product-labeling --org myorg`
3. Check status: `uv run github-analysis batch status <job-id>`
4. Collect results: `uv run github-analysis batch collect <job-id>`
5. Update labels: `uv run github-analysis update-labels --org myorg --dry-run`

**Alternative Workflow (Individual Processing - for single issues only):**
1. Collect single issue: `uv run github-analysis collect --org myorg --repo myrepo --issue-number 123`
2. Process individual issue: `uv run github-analysis process product-labeling --org myorg --repo myrepo --issue-number 123`
3. Update labels: `uv run github-analysis update-labels --org myorg --repo myrepo --issue-number 123 --dry-run`

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

## Thinking Models and Advanced Configuration

### Model Format
All models must be specified in the format `provider:model-name`:
- ✅ `openai:o4-mini`
- ✅ `anthropic:claude-3-5-sonnet-latest`
- ❌ `o4-mini` (missing provider)

### Thinking Capabilities
Different models support different thinking options:

**OpenAI Reasoning Models** (o4-mini, o3):
- `--thinking-effort`: Controls reasoning depth (low, medium, high)
- `--thinking-summary`: Provides reasoning summaries

**Anthropic Models** (claude-3-5-sonnet-latest):
- `--thinking-budget`: Token budget for thinking process

**Google Models** (gemini-2.0-flash):
- `--thinking-budget`: Token budget for thinking process

### Examples
```bash
# Use OpenAI reasoning model with medium effort
uv run github-analysis process product-labeling --model openai:o4-mini --thinking-effort medium

# Use Anthropic with thinking budget
uv run github-analysis process product-labeling --model anthropic:claude-3-5-sonnet-latest --thinking-budget 2048

# Invalid format will show helpful error
uv run github-analysis process product-labeling --model o4-mini --thinking-effort high
# Error: Invalid model format 'o4-mini'. Expected format: provider:model
```

## Development Commands

```bash
# Setup
uv sync --all-extras

# Code quality (run all four - required before commit)
uv run ruff check --fix --unsafe-fixes && uv run black . && uv run mypy . && uv run pytest

# Individual tools
uv run ruff check --fix --unsafe-fixes  # Code quality and imports
uv run black .                          # Code formatting (automatically applies fixes - DO NOT manually edit files for formatting)
uv run mypy .                           # Type checking
uv run pytest                          # Run tests
```

**IMPORTANT**: Black automatically applies formatting fixes. Agents should **NOT** manually make formatting changes. Only intervene if Black fails with actual errors (syntax errors, etc.).