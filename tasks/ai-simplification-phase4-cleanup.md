# Task: AI Simplification - Phase 4: Legacy Cleanup

## Status
- **Created**: 2025-07-15
- **Status**: pending
- **Started**: [To be filled by agent]
- **Completed**: [To be filled by agent]
- **Depends On**: Phase 3 (Batch Processing)

## Overview
Remove legacy configuration classes and abstraction layers now that all systems use the new agent interface. This phase achieves the core goal of code simplification and line count reduction.

## Scope
- Remove legacy configuration classes (`AISettings`, `AIModelConfig`, `ThinkingConfig`)
- Remove or minimize `ai/processors.py` abstraction layer
- Clean up `ai/config.py` to minimal helpers only
- Update all imports throughout codebase
- Update existing tests affected by removals
- Verify 200+ line reduction goal

## Acceptance Criteria
- [ ] Legacy configuration classes completely removed
- [ ] Processor abstraction layer removed or minimized
- [ ] All imports updated throughout codebase
- [ ] No broken references or dead code
- [ ] Existing tests updated to use new patterns
- [ ] 200+ lines of code removed (verify with git diff)
- [ ] All functionality preserved
- [ ] Quality checks pass (black, ruff, mypy, pytest)

## Implementation Details

### Files to Delete or Heavily Modify
```
src/github_analysis/ai/config.py       # Keep minimal helpers only (~20 lines)
src/github_analysis/ai/processors.py   # Remove or reduce to minimal wrapper
```

### Classes/Functions to Remove
```python
# From ai/config.py
class AISettings              # Environment-based config - DELETE
class AIModelConfig          # Model configuration wrapper - DELETE
class ThinkingConfig         # Thinking configuration - DELETE
def build_ai_config()        # Config builder - DELETE
def build_provider_specific_settings()  # Provider settings - DELETE

# From ai/processors.py
class ProductLabelingProcessor  # Abstraction layer - DELETE or simplify
```

### Files to Update (Import Cleanup)
```
src/github_analysis/cli/process.py     # Remove old config imports
src/github_analysis/cli/batch.py       # Remove old config imports
tests/test_ai/test_config.py           # Update or remove tests
tests/test_ai/test_processors.py       # Update or remove tests
```

### What to Keep Minimal
```python
# ai/config.py - Keep only these helpers (~20 lines)
def validate_model_string(model: str) -> tuple[str, str]:
    """Validate and parse model string format."""

def supports_thinking(model: str) -> bool:
    """Check if model supports thinking/reasoning."""

# Optional: Simple constants
THINKING_MODELS = {
    "openai:o1", "openai:o1-mini", "anthropic:claude-3-5-sonnet"
}
```

### Testing Updates Required
- Remove tests for deleted configuration classes
- Update any tests that imported removed functions
- Ensure integration tests still pass with new patterns
- Add tests for any new minimal helper functions

### Manual Verification Commands
```bash
# Ensure nothing breaks after cleanup
uv run black . && uv run ruff check --fix --unsafe-fixes && uv run mypy . && uv run pytest -v

# Test core functionality still works
uv run github-analysis process product-labeling --org test --repo test --issue-number 1 --dry-run
uv run github-analysis batch submit product-labeling --org test --repo test --dry-run

# Verify line count reduction
git diff --stat HEAD~4  # Compare to before Phase 1
wc -l src/github_analysis/ai/*.py  # Check current line counts
```

## Agent Instructions

### During Implementation
1. Document discoveries and challenges in "Implementation Notes" section below
2. Note any deviations from planned approach and why
3. Record testing insights and effective strategies
4. List all files modified/deleted with brief description

### Learning from Previous Phases
[Read Phases 1-3 notes for insights about what dependencies exist, what can be safely removed]

### Before Marking Complete
1. Update status and completion timestamp
2. Add recommendations for next phase agent (documentation)
3. Include working verification commands
4. Note any technical debt or follow-up items
5. **Calculate and report line count reduction achieved**

### Handoff Requirements
- All tests passing
- Manual verification commands documented and working
- Clear notes on what the documentation agent should know
- Line count reduction verified and documented

## Implementation Notes
[Agent fills this in during work]

### Discoveries
[What did you learn about dependencies, what was safe to remove?]

### Challenges Encountered
[What problems did you face and how did you solve them?]

### Code Changes Made
[List of files deleted/modified and why]

### Testing Insights
[What cleanup testing strategies worked? What to avoid?]

### Line Count Reduction Achieved
[Before/after comparison - aim for 200+ lines removed]

### Recommendations for Next Phase
[What should the documentation agent know?]

### Files Modified/Deleted
[Detailed list with descriptions]

### Verification Commands That Worked
[Copy the exact commands that successfully verify this phase]

## Success Criteria
✅ Legacy configuration classes completely removed
✅ Code complexity significantly reduced
✅ All functionality preserved
✅ 200+ line reduction goal achieved
✅ No broken imports or references
✅ Full test suite passes