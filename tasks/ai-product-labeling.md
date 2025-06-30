# Task: AI Product Labeling Processor

**Status:** ready

**Description:**
Implement AI-powered product labeling analysis using PydanticAI that reviews GitHub issues and suggests correct product labels. Focus on OpenAI GPT-4o-mini initially.

**Prerequisites:**
- `github-issue-collection.md` must be completed first
- Requires collected issues in `data/issues/` directory

**Files to Create:**
- `github_issue_analysis/ai/providers.py` - AI client implementations
- `github_issue_analysis/ai/processors.py` - Product labeling processor
- `github_issue_analysis/ai/prompts.py` - Prompt templates
- `github_issue_analysis/ai/models.py` - AI response models
- `github_issue_analysis/cli/process.py` - CLI process command
- `tests/test_ai/` - AI processing tests

**Files to Modify:**
- `github_issue_analysis/cli/main.py` - Add process command import
- `github_issue_analysis/ai/__init__.py` - Package initialization

**Implementation Details:**

**Libraries to Use:**
- `pydantic-ai` for AI integration with structured outputs
- `openai` for OpenAI API client
- `anthropic` for future Anthropic support (stub for now)
- `rich` for CLI progress display

**AI Models:**
- Primary: `gpt-4o-mini` (fast, cost-effective)
- Fallback: `gpt-4o` (if mini fails)
- Response format: JSON with Pydantic validation

**PydanticAI Setup:**
```python
from pydantic_ai import Agent
from pydantic import BaseModel

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

agent = Agent(
    'openai:gpt-4o-mini',
    result_type=ProductLabelingResponse,
)
```

**Prompt Template:**
```python
PRODUCT_LABELING_PROMPT = """
Analyze this GitHub issue and assess whether the product labels are correct.

Issue Title: {title}
Issue Body: {body}
Current Labels: {current_labels}
Repository: {org}/{repo}

Comment Summary: {comment_summary}

Your task:
1. Assess if current product-related labels are correct
2. Suggest better product labels if needed
3. Focus on labels that indicate which product/component the issue affects
4. Consider the issue content, not just the title

Provide specific reasoning for each assessment and recommendation.
"""
```

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
2. Extract title, body, labels, and summarize comments (first 500 chars each)
3. Build prompt with issue data
4. Call PydanticAI agent with structured output
5. Validate response and save to `data/results/`
6. Handle API errors with retries and fallbacks

**Error Handling:**
- API rate limiting with exponential backoff
- Invalid JSON responses (retry once with different prompt)
- Missing issue files (skip with warning)
- AI refusal/safety responses (log and continue)

**CLI Options:**
- `--task TEXT`: Processing task name (required)
- `--model TEXT`: AI model (default: gpt-4o-mini)
- `--org TEXT`: Filter by organization  
- `--repo TEXT`: Filter by repository
- `--issue INT`: Process specific issue number
- `--dry-run`: Show what would be processed without running AI

**Acceptance Criteria:**
- [ ] PydanticAI agent with structured output for product labeling
- [ ] CLI process command with filtering options
- [ ] OpenAI client integration with proper error handling
- [ ] Prompt template for product label analysis
- [ ] Results storage in JSON format with metadata
- [ ] Progress display for batch processing
- [ ] Comprehensive test coverage with AI response mocking
- [ ] Rate limiting and retry logic for API failures
- [ ] Code quality checks pass (ruff, black, mypy)

**Agent Notes:**
[Document your prompt engineering decisions, model selection rationale, and testing strategy for AI responses]

**Validation:**
- Ensure issues collected first: `uv run github-analysis collect --org microsoft --repo vscode --limit 3`
- Run processing: `uv run github-analysis process --task product-labeling`
- Verify results files created in `data/results/` directory
- Test specific issue: `uv run github-analysis process --task product-labeling --issue 12345`
- Test dry-run mode: `uv run github-analysis process --task product-labeling --dry-run`
- Check structured output validates against Pydantic models
- Ensure all tests pass: `uv run pytest tests/test_ai/ -v`
- Verify code quality: `uv run ruff check && uv run black . && uv run mypy .`