# Task: AI Simplification - Phase 1: New Agent Interface

## Status
- **Created**: 2025-07-15
- **Status**: pending
- **Started**: [To be filled by agent]
- **Completed**: [To be filled by agent]

## Overview
Create a new simplified agent interface using direct PydanticAI usage. This is the foundation layer that subsequent phases will build upon.

## Scope
- Create `ai/agents.py` with PydanticAI wrapper functions
- Add model validation helpers in minimal `ai/config.py`
- Comprehensive testing of new agent interface
- Keep all existing code untouched (backward compatibility)

## Acceptance Criteria
- [ ] `create_product_labeling_agent()` function works with all model types
- [ ] Model string validation handles edge cases
- [ ] Provider-specific settings (OpenAI, Anthropic) work correctly
- [ ] Thinking effort and temperature parameters supported
- [ ] Full unit test coverage for new functions
- [ ] All existing functionality unchanged
- [ ] Quality checks pass (black, ruff, mypy, pytest)

## Implementation Details

### Files to Create
```
src/github_analysis/ai/agents.py       # Main agent creation functions
tests/test_ai/test_agents.py           # Comprehensive test suite
```

### Files to Modify
```
src/github_analysis/ai/config.py       # Reduce to minimal helpers only
src/github_analysis/ai/__init__.py     # Update exports if needed
```

### Core Functions Needed
```python
# ai/agents.py
def create_product_labeling_agent(
    model: str,
    thinking_effort: str | None = None,
    temperature: float = 0.0,
    retry_count: int = 2
) -> Agent[None, ProductLabelingResponse]:
    """Create a PydanticAI agent with the specified configuration."""

# ai/config.py (minimal helpers)
def validate_model_string(model: str) -> tuple[str, str]:
    """Validate and parse model string format."""

def supports_thinking(model: str) -> bool:
    """Check if model supports thinking/reasoning."""
```

### Testing Requirements
- Test agent creation with various model combinations
- Test provider-specific settings (OpenAI vs Anthropic)
- Test thinking effort validation
- Test temperature bounds checking
- Mock PydanticAI agent.run() for integration tests
- Test error handling for invalid model strings

### Manual Verification Commands
```bash
# Test new agent creation works
uv run python -c "from src.github_analysis.ai.agents import create_product_labeling_agent; agent = create_product_labeling_agent('openai:gpt-4'); print('Agent created successfully')"

# Test with thinking model
uv run python -c "from src.github_analysis.ai.agents import create_product_labeling_agent; agent = create_product_labeling_agent('openai:o1-mini', thinking_effort='high'); print('Thinking agent created')"

# Quality checks
uv run black . && uv run ruff check --fix --unsafe-fixes && uv run mypy . && uv run pytest tests/test_ai/test_agents.py -v
```

## Agent Instructions

### During Implementation
1. Document discoveries and challenges in "Implementation Notes" section below
2. Note any deviations from planned approach and why
3. Record testing insights and effective strategies
4. List all files modified with brief description

### Before Marking Complete
1. Update status and completion timestamp
2. Add recommendations for next phase agent
3. Include working verification commands
4. Note any technical debt or follow-up items

### Handoff Requirements
- All tests passing
- Manual verification commands documented and working
- Clear notes on what the next agent should know
- Any blockers or dependencies clearly stated

## Implementation Notes
[Agent fills this in during work]

### Discoveries
[What did you learn about PydanticAI, model configuration, etc.?]

### Challenges Encountered
[What problems did you face and how did you solve them?]

### Code Changes Made
[List of files created/modified and why]

### Testing Insights
[What testing strategies worked? What to avoid?]

### Recommendations for Next Phase
[What should the CLI integration agent know?]

### Files Modified
[Detailed list with descriptions]

### Verification Commands That Worked
[Copy the exact commands that successfully verify this phase]

## Success Criteria
✅ New agent interface works with all supported models
✅ Backward compatibility maintained (no existing code broken)
✅ Full test coverage with meaningful assertions
✅ Quality tools pass without errors
✅ Clear documentation for next phase handoff