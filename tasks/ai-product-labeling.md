# Task: AI Product Labeling Processor

**Status:** ready

**Description:**
Implement AI-powered product labeling analysis using PydanticAI that reviews GitHub issues and suggests correct product labels. Focus on OpenAI GPT-4o-mini initially.

**Prerequisites:**
- `github-issue-collection.md` must be completed first
- Requires collected issues in `data/issues/` directory

**Files to Create:**
- `github_issue_analysis/ai/processors.py` - Product labeling processor using PydanticAI
- `github_issue_analysis/ai/prompts.py` - Modular prompt templates (see structure below)
- `github_issue_analysis/ai/models.py` - AI response models (Pydantic)
- `github_issue_analysis/ai/data_prep.py` - Data compression utilities for token efficiency
- `github_issue_analysis/cli/process.py` - CLI process command
- `tests/test_ai/` - AI processing tests

**Note:** No separate `providers.py` needed - PydanticAI handles model providers automatically.

**Files to Modify:**
- `github_issue_analysis/cli/main.py` - Add process command import
- `github_issue_analysis/ai/__init__.py` - Package initialization

**Implementation Details:**

**Libraries to Use:**
- `pydantic-ai` for AI integration with structured outputs (handles OpenAI and Anthropic clients)
- `rich` for CLI progress display

**Note:** PydanticAI manages the underlying `openai` and `anthropic` clients automatically based on model selection.

**AI Models with Vision Support:**
- Primary: `gpt-4o-mini` (fast, cost-effective, supports images)
- Alternative: `gpt-4o` (higher quality, supports images)
- Alternative: `o1-mini` (reasoning model, good for complex classification)
- Alternative: `o1` (high-quality reasoning model, supports images)
- Text-only fallback: `gpt-3.5-turbo` (no image support)
- Response format: JSON with Pydantic validation

**Model Selection Strategy:**
Models configurable via CLI `--model` flag or environment variable `AI_MODEL`:
```bash
# Test general purpose models (default approach)
uv run github-analysis process --task product-labeling --model gpt-4o-mini --issue 71
uv run github-analysis process --task product-labeling --model gpt-4o --issue 71

# Test reasoning models (for complex cases)
uv run github-analysis process --task product-labeling --model o1-mini --issue 71
uv run github-analysis process --task product-labeling --model o1 --issue 71

# Set default via environment
export AI_MODEL=gpt-4o-mini
uv run github-analysis process --task product-labeling --issue 71

# For o1 models, can also set reasoning effort
export AI_REASONING_EFFORT=high  # low, medium, high
```

**PydanticAI Setup:**
```python
from pydantic_ai import Agent
from pydantic import BaseModel
from typing import List

class ProductLabelingResponse(BaseModel):
    confidence: float  # 0.0 to 1.0
    recommended_labels: List[RecommendedLabel]
    current_labels_assessment: List[LabelAssessment]  
    summary: str
    reasoning: str

class RecommendedLabel(BaseModel):
    label: str
    confidence: float
    reasoning: str

class LabelAssessment(BaseModel):
    label: str
    correct: bool
    reasoning: str

# PydanticAI automatically handles OpenAI/Anthropic clients
agent = Agent(
    'openai:gpt-4o-mini',  # Can be changed to 'openai:o1-mini', 'anthropic:claude-3-5-sonnet', etc.
    result_type=ProductLabelingResponse,
)

# For models with reasoning effort (o1 series)
agent_with_reasoning = Agent(
    'openai:o1-mini',
    result_type=ProductLabelingResponse,
    model_settings={'reasoning_effort': 'medium'}  # low, medium, high
)
```

**Product Definitions:**
The following product labels are available, each starting with `product::`:

- **`product::kots`** - Kubernetes Off-The-Shelf (KOTS): Admin console for managing Kubernetes applications. Issues involve the KOTS admin interface, KOTS CLI for application management, application lifecycle within the console, license validation, configuration screens, and admin UI functionality. Look for: "kotsadm", admin console problems, KOTS runtime functionality.

- **`product::troubleshoot`** - Troubleshoot: Diagnostic and support bundle collection tool. Issues involve the troubleshoot tool itself, support bundle collection logic, analyzers, collectors, and diagnostic gathering functionality. Look for: "support-bundle" tool problems, "troubleshoot" CLI issues, collector/analyzer development.

- **`product::sdk`** - Replicated SDK: Developer tools and libraries for integrating with Replicated platform. Issues involve API clients, SDK usage, developer tooling, and programmatic integrations.

- **`product::docs`** - Documentation: Issues with documentation, tutorials, guides, examples, or documentation website. Look for: documentation requests, unclear guides, missing examples, doc site issues.

- **`product::vendor`** - Vendor Portal: Web interface for vendors to manage applications, customers, and releases. Issues involve the vendor.replicated.com interface, application management, customer management, release management.

- **`product::downloadportal`** - Download Portal: Customer-facing download interface for air-gapped installations. Issues involve download.replicated.com, customer download experience, package downloads.

- **`product::embedded-cluster`** - Embedded Cluster: Single-node Kubernetes distribution with KOTS. Issues involve cluster setup, embedded cluster installation, single-node deployments, cluster lifecycle management, KOTS installation/upgrade within clusters.

- **`product::compatibility-matrix`** - Compatibility Matrix: Tool for testing application compatibility across Kubernetes versions. Issues involve compatibility testing, version matrices, test automation.

**Enhanced Prompt Template:**
```python
PRODUCT_LABELING_PROMPT = """
Analyze this GitHub issue to determine the correct product label(s).

**Issue Details:**
Title: {title}
Body: {body}
Current Labels: {current_labels}
Repository: {org}/{repo}

**Key Comments/Discussion:**
{comment_summary}

**Product Classification Guidelines:**

CRITICAL: Look for these key indicators and follow the decision tree:

1. **KOTS Issues** - Look for:
   - Admin console UI problems, interface bugs, display issues
   - Application lifecycle management within the console
   - License validation, preflight checks in admin UI
   - Configuration screens, settings management
   - KOTS CLI usage ("kubectl kots") for application management
   - Issues with KOTS core functionality (not installation/upgrades)

2. **Troubleshoot Issues** - Look for:
   - Support bundle collection, collectors, analyzers development
   - Diagnostic collection tool functionality
   - Troubleshoot CLI or library issues
   - Problems with diagnostic data gathering itself

3. **Embedded Cluster Issues** - Look for:
   - Cluster installation, setup, and infrastructure
   - KOTS installation/upgrade within embedded cluster
   - Cluster lifecycle management, node management
   - Infrastructure-level concerns and cluster operations

**Key Decision Principles:**

**Installation vs. Runtime:** 
- Installing KOTS via kubectl kots plugin → kots product
- Installing KOTS via kURL (kubeadm) or embedded-cluster (k0s) → cluster product
- Using KOTS after it's installed → kots product

**Root Cause Analysis:**
- Where would the bug need to be fixed?
- Which team owns the component that's actually broken?
- What's the primary product experiencing the failure?

**Symptom vs. Source:**
- A tool may surface an issue without being the source of the issue
- The location where you see a problem isn't always where the problem is
- Consider the entire system interaction

**Common Pitfalls to Avoid:**
- Don't assume the product mentioned first is the problem source
- Installation/upgrade issues often belong to cluster products
- UI display problems may indicate backend data issues
- Consider the full system context, not just isolated symptoms

Provide detailed reasoning explaining why you chose each label, especially for ambiguous cases.
"""
```

**Human-Editable Prompt Configuration:**
All prompt content should be easily editable in `github_issue_analysis/ai/prompts.py`:

```python
# ============================================================================
# EDIT THIS FILE TO MODIFY AI LABELING BEHAVIOR
# ============================================================================

# 1. TO UPDATE PRODUCT DESCRIPTIONS: Edit this dictionary
PRODUCT_DEFINITIONS = {
    "kots": "Kubernetes Off-The-Shelf (KOTS): Admin console for managing Kubernetes applications. Issues involve the KOTS admin interface, KOTS CLI for application management, application lifecycle within the console, license validation, configuration screens, and admin UI functionality. Look for: 'kotsadm', admin console problems, KOTS runtime functionality.",
    
    "troubleshoot": "Troubleshoot: Diagnostic and support bundle collection tool. Issues involve the troubleshoot tool itself, support bundle collection logic, analyzers, collectors, and diagnostic gathering functionality. Look for: 'support-bundle' tool problems, 'troubleshoot' CLI issues, collector/analyzer development.",
    
    "embedded-cluster": "Embedded Cluster: Single-node Kubernetes distribution with KOTS. Issues involve cluster setup, embedded cluster installation, single-node deployments, cluster lifecycle management, KOTS installation/upgrade within clusters.",
    
    "sdk": "Replicated SDK: Developer tools and libraries for integrating with Replicated platform. Issues involve API clients, SDK usage, developer tooling, and programmatic integrations.",
    
    "docs": "Documentation: Issues with documentation, tutorials, guides, examples, or documentation website. Look for: documentation requests, unclear guides, missing examples, doc site issues.",
    
    "vendor": "Vendor Portal: Web interface for vendors to manage applications, customers, and releases. Issues involve the vendor.replicated.com interface, application management, customer management, release management.",
    
    "downloadportal": "Download Portal: Customer-facing download interface for air-gapped installations. Issues involve download.replicated.com, customer download experience, package downloads.",
    
    "compatibility-matrix": "Compatibility Matrix: Tool for testing application compatibility across Kubernetes versions. Issues involve compatibility testing, version matrices, test automation."
}

# 2. TO UPDATE CLASSIFICATION LOGIC: Edit this section
CLASSIFICATION_GUIDELINES = """
CRITICAL: Look for these key indicators and follow the decision tree:

1. **KOTS Issues** - Look for:
   - Admin console UI problems, interface bugs, display issues
   - Application lifecycle management within the console
   - License validation, preflight checks in admin UI
   - Configuration screens, settings management
   - KOTS CLI usage ("kubectl kots") for application management
   - Issues with KOTS core functionality (not installation/upgrades of KOTS itself)

2. **Troubleshoot Issues** - Look for:
   - Support bundle collection, collectors, analyzers development
   - Diagnostic collection tool functionality
   - Troubleshoot CLI or library issues
   - Problems with diagnostic data gathering itself

3. **Embedded Cluster Issues** - Look for:
   - Cluster installation, setup, and infrastructure
   - KOTS installation/upgrade within embedded cluster
   - Cluster lifecycle management, node management
   - Infrastructure-level concerns and cluster operations

**Key Decision Principles:**

**Installation vs. Runtime:** 
- Installing KOTS via kubectl kots plugin → kots product
- Installing KOTS via kURL (kubeadm) or embedded-cluster (k0s) → cluster product
- Using KOTS after it's installed → kots product

**Root Cause Analysis:**
- Where would the bug need to be fixed?
- Which team owns the component that's actually broken?
- What's the primary product experiencing the failure?

**Symptom vs. Source:**
- A tool may surface an issue without being the source of the issue
- The location where you see a problem isn't always where the problem is
- Consider the entire system interaction
"""

# 3. TO ADD NEW COMMON MISTAKES: Edit this section
COMMON_PITFALLS = """
**Common Pitfalls to Avoid:**
- Don't assume the product mentioned first is the problem source
- Installation/upgrade issues often belong to cluster products
- UI display problems may indicate backend data issues
- Consider the full system context, not just isolated symptoms
"""

# DO NOT EDIT BELOW (auto-generated from above components)
def build_product_labeling_prompt() -> str:
    """Auto-builds prompt from editable components above."""
    product_list = "\n".join([f"- **`product::{k}`** - {v}" for k, v in PRODUCT_DEFINITIONS.items()])
    
    return f"""
Analyze this GitHub issue to determine the correct product label(s).

**Issue Details:**
Title: {{title}}
Body: {{body}}
Current Labels: {{current_labels}}
Repository: {{org}}/{{repo}}

**Key Comments/Discussion:**
{{comment_summary}}

**Product Classification Guidelines:**
{product_list}

{CLASSIFICATION_GUIDELINES}

{COMMON_PITFALLS}

Provide detailed reasoning explaining why you chose each label, especially for ambiguous cases.
"""

PRODUCT_LABELING_PROMPT = build_product_labeling_prompt()
```

**Fine-tuning Workflow:**
1. Modify specific sections in `PRODUCT_DEFINITIONS`, `CLASSIFICATION_GUIDELINES`, or `COMMON_PITFALLS`
2. The prompt auto-rebuilds from components
3. Test changes without editing the main prompt template
4. Version control individual components for easier tracking

**CLI Interface:**
```bash
uv run github-analysis process --task product-labeling
uv run github-analysis process --task product-labeling --org microsoft --repo vscode
uv run github-analysis process --task product-labeling --issue 12345
```

**Storage Format:**
Results saved as: `data/results/microsoft_vscode_issue_12345_product-labeling.json`
```json
{
  "issue_reference": {
    "org": "microsoft",
    "repo": "vscode",
    "issue_number": 12345,
    "file_path": "data/issues/microsoft_vscode_issue_12345.json"
  },
  "processor": {
    "name": "product-labeling",
    "version": "1.0.0", 
    "model": "gpt-4o-mini",
    "timestamp": "2024-01-01T21:00:00Z"
  },
  "analysis": {
    "confidence": 0.85,
    "recommended_labels": [...],
    "current_labels_assessment": [...],
    "summary": "...",
    "reasoning": "..."
  }
}
```

**Processing Logic:**
1. Load issue JSON from `data/issues/`
2. **Extract and compress data for AI efficiency:**
   - Parse JSON and extract only needed fields (title, body, labels, comments)
   - Truncate/summarize long content (comments first 500 chars each)
   - Remove metadata not needed for classification
   - Serialize extracted data as compact JSON (no whitespace)
3. Build prompt with compressed issue data
4. Call PydanticAI agent with structured output
5. Validate response and save to `data/results/`
6. Handle API errors with retries and fallbacks

**Data Compression Strategy with Image Handling:**
```python
import re
from typing import List, Dict, Any

def extract_image_urls(text: str) -> List[str]:
    """Extract GitHub image URLs from markdown and HTML."""
    patterns = [
        r'!\[.*?\]\((https://github\.com/user-attachments/assets/[^)]+)\)',  # Markdown
        r'<img[^>]+src="(https://github\.com/user-attachments/assets/[^"]+)"',  # HTML
    ]
    urls = []
    for pattern in patterns:
        urls.extend(re.findall(pattern, text))
    return urls

def prepare_issue_for_ai(issue_data: dict, include_images: bool = True) -> Dict[str, Any]:
    """Extract and compress issue data for AI processing to minimize tokens."""
    issue = issue_data["issue"]
    
    # Extract images from body and comments
    images = []
    if include_images:
        images.extend(extract_image_urls(issue["body"]))
        for comment in issue["comments"][-10:]:  # Last 10 comments
            images.extend(extract_image_urls(comment["body"]))
    
    # Extract only classification-relevant fields
    extracted = {
        "title": issue["title"],
        "body": issue["body"][:2000],  # Truncate long bodies
        "labels": [label["name"] for label in issue["labels"]],
        "comments": [
            {
                "user": comment["user"]["login"],
                "body": comment["body"][:500]  # Truncate long comments
            }
            for comment in issue["comments"][-10:]  # Last 10 comments only
        ],
        "org": issue_data["org"],
        "repo": issue_data["repo"],
        "images": images[:5] if include_images else []  # Limit to 5 images max
    }
    
    return extracted

def format_issue_for_prompt(issue_data: dict) -> dict:
    """Format issue data for prompt template variables."""
    issue = issue_data["issue"]
    
    # Compact comment summary
    comment_summary = ""
    if issue.get("comments"):
        recent_comments = issue["comments"][-5:]  # Last 5 comments
        summaries = []
        for comment in recent_comments:
            user = comment["user"]["login"]
            body = comment["body"][:300].replace('\n', ' ').strip()
            summaries.append(f"{user}: {body}")
        comment_summary = " | ".join(summaries)
    
    return {
        "title": issue["title"],
        "body": issue["body"][:1500],  # Truncate for prompt
        "current_labels": [label["name"] for label in issue["labels"]],
        "org": issue_data["org"],
        "repo": issue_data["repo"],
        "comment_summary": comment_summary or "No comments"
    }
```

**Token Optimization Benefits:**
- **Storage**: Pretty-printed JSON (~15KB for issue #71)
- **AI Input**: Compact extraction (~3-5KB after compression)
- **Savings**: 60-70% token reduction per issue
- **Reusable**: Same compression logic works for all AI processing tasks

**Error Handling:**
- API rate limiting with exponential backoff
- Invalid JSON responses (retry once with different prompt)
- Missing issue files (skip with warning)
- AI refusal/safety responses (log and continue)

**CLI Options:**
- `--task TEXT`: Processing task name (required)
- `--model TEXT`: AI model (default: gpt-4o-mini, options: gpt-4o, gpt-4o-mini, o1, o1-mini, gpt-3.5-turbo)
- `--reasoning-effort TEXT`: For o1 models only (default: medium, options: low, medium, high)
- `--org TEXT`: Filter by organization  
- `--repo TEXT`: Filter by repository
- `--issue INT`: Process specific issue number
- `--include-images / --no-images`: Include/exclude screenshots (default: include)
- `--dry-run`: Show what would be processed without running AI

**Acceptance Criteria:**
- [ ] PydanticAI agent with structured output for product labeling
- [ ] CLI process command with filtering options  
- [ ] Model switching via PydanticAI (gpt-4o-mini, o1-mini, etc.)
- [ ] Modular prompt template system for easy fine-tuning
- [ ] Data compression utilities for token efficiency (60-70% reduction)
- [ ] Image processing for screenshots in issues
- [ ] Results storage in JSON format with metadata
- [ ] Progress display for batch processing
- [ ] Comprehensive test coverage with AI response mocking
- [ ] Error handling for API failures (PydanticAI manages retries)
- [ ] **Token optimization**: Compact JSON serialization for AI input
- [ ] **Test case validation**: Issue #71 correctly classified as `product::kots`
- [ ] **Image impact testing**: Compare results with/without screenshots
- [ ] Code quality checks pass (ruff, black, mypy)

**Agent Notes:**
[Document your prompt engineering decisions, model selection rationale, and testing strategy for AI responses]

**Test Cases for Prompt Fine-tuning:**

**Primary Test Case - Issue #71 (Tricky Classification with Screenshots):**
```bash
# Collect the test issue (already done)
uv run github-analysis collect --org replicated-collab --repo pixee-replicated --issue-number 71

# Test with images (default) - should help with classification
uv run github-analysis process --task product-labeling --org replicated-collab --repo pixee-replicated --issue 71

# Test without images - to compare difference
uv run github-analysis process --task product-labeling --org replicated-collab --repo pixee-replicated --issue 71 --no-images

# Test different models with images
uv run github-analysis process --task product-labeling --issue 71 --model gpt-4o-mini
uv run github-analysis process --task product-labeling --issue 71 --model gpt-4o
uv run github-analysis process --task product-labeling --issue 71 --model o1-mini --reasoning-effort medium
```

**Image Content in Issue #71:**
- Issue body: 1 screenshot showing RunPods output directory
- Comments: 4 additional screenshots showing admin console file browser
- Key visual evidence: Screenshots clearly show KOTS admin console interface struggling with symlinked files

**Expected Behavior:**
- Current label: `product::troubleshoot` (incorrect)
- Correct label: `product::kots` 
- **Why this is tricky:** Issue initially appears to be about troubleshoot/support bundles, but root cause is KOTS admin console unable to handle symlinks. Key indicator: "kotsadm's file tree is unable to handle symbolic links"
- **Test success:** AI should recommend changing from `troubleshoot` to `kots` with reasoning about admin console UI bug

**Additional Test Cases to Add:**
Create more test cases by collecting issues and documenting expected vs. actual labeling:

```bash
# Template for adding new test cases
uv run github-analysis collect --org [ORG] --repo [REPO] --issue-number [NUM]
uv run github-analysis process --task product-labeling --org [ORG] --repo [REPO] --issue [NUM]
```

**Fine-tuning Process:**
1. Run AI labeling on test cases
2. Compare AI recommendations with human expert labeling
3. For mismatches, analyze why AI got it wrong
4. Update product descriptions or prompt guidelines
5. Re-test with updated prompt
6. Document successful prompt changes

**Prompt Iteration Log:**
- Version 1.0: Initial prompt with basic product descriptions
- Version 1.1: Added specific KOTS vs troubleshoot distinction after issue #71
- [Future versions documented here]

**Validation:**
- Ensure issues collected first: `uv run github-analysis collect --org microsoft --repo vscode --limit 3`
- Run processing: `uv run github-analysis process --task product-labeling`
- Verify results files created in `data/results/` directory
- Test specific issue: `uv run github-analysis process --task product-labeling --issue 12345`
- Test dry-run mode: `uv run github-analysis process --task product-labeling --dry-run`
- Check structured output validates against Pydantic models
- **Test primary case:** `uv run github-analysis process --task product-labeling --org replicated-collab --repo pixee-replicated --issue 71`
- Ensure all tests pass: `uv run pytest tests/test_ai/ -v`
- Verify code quality: `uv run ruff check && uv run black . && uv run mypy .`
