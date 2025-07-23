# GitHub Issue Analysis

Collect GitHub issues and analyze them with AI to improve issue labeling and categorization.

## Quick Start

1. **Setup Environment**
   ```bash
   uv sync --all-extras
   cp .env.example .env
   # Edit .env with your API keys
   # Note: .env file is automatically loaded by all commands
   ```

2. **Collect Issues**
   ```bash
   uv run github-analysis collect --org YOUR_ORG --repo YOUR_REPO --labels bug --limit 5
   ```

3. **Process with AI (Batch Processing - Recommended)**
   ```bash
   # Submit batch job (50% cheaper than individual processing)
   uv run github-analysis batch submit product-labeling --org YOUR_ORG --repo YOUR_REPO
   uv run github-analysis batch submit issue-type-classification --org YOUR_ORG --repo YOUR_REPO
   
   # Check status
   uv run github-analysis batch list
   
   # Collect results when completed
   uv run github-analysis batch collect <job-id>
   ```

   **Individual Processing** (for single issues or custom models):
   ```bash
   # Product labeling analysis
   uv run github-analysis process product-labeling --org YOUR_ORG --repo YOUR_REPO --issue-number 123
   
   # Issue type classification
   uv run github-analysis process issue-type-classification --org YOUR_ORG --repo YOUR_REPO --issue-number 123
   
   # Use custom model with settings
   uv run github-analysis process product-labeling --org YOUR_ORG --repo YOUR_REPO \
     --model anthropic:claude-3-5-sonnet \
     --setting temperature=0.5 \
     --setting reasoning_effort=high
   
   # Show available model settings
   uv run github-analysis process show-settings
   ```

4. **Update Labels** (with GitHub write token)
   ```bash
   # Preview changes first
   uv run github-analysis update-labels --org YOUR_ORG --repo YOUR_REPO --dry-run
   
   # Apply changes
   uv run github-analysis update-labels --org YOUR_ORG --repo YOUR_REPO
   ```

## Analysis Types

This tool provides two types of AI analysis:

### 1. Product Labeling
Recommends appropriate product labels (e.g., `product::kots`, `product::vendor`) based on which Replicated product the issue affects.

**Results:** Saved as `{org}_{repo}_issue_{number}_product-labeling.json` in `data/results/`

### 2. Issue Type Classification
Classifies issues into four categories based on root cause:
- **`customer-environment`** - Problems with customer infrastructure, configuration, or environment
- **`usage-question`** - Questions about how to use products or clarification requests  
- **`product-bug`** - Defects or failures in Replicated products
- **`helm-chart-fix`** - Issues with vendor application code, Helm charts, or manifests

**Results:** Saved as `{org}_{repo}_issue_{number}_issue-type-classification.json` in `data/results/`

**Example result:**
```json
{
  "issue_type": "helm-chart-fix",
  "classification_confidence": 0.85,
  "reasoning": "Issue stems from invalid image references in vendor Helm chart...",
  "supporting_evidence": [
    "Error log: 'failed to parse docker ref \":\"'",
    "Support identified image refs in vendor Helm charts defaulting to ':'"
  ],
  "root_cause_analysis": "Vendor Helm chart templates have invalid image tag values",
  "resolution_indicators": "Vendor needs to fix their Helm chart templates"
}
```

For issues with confidence < 0.7, consider manual review or use "Other" if the classification is unclear.

## For AI Agents

**All agent instructions are in `CLAUDE.md`** - this is the single source of truth for development workflow, commands, and requirements.

## Documentation

See `docs/` directory for user documentation:
- `architecture.md` - System design overview
- `data-schemas.md` - JSON formats and data structures  
- `api-reference.md` - CLI commands and usage
