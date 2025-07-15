# Task: AI Simplification - Phase 2: CLI Integration

## Status
- **Created**: 2025-07-15
- **Status**: pending
- **Started**: [To be filled by agent]
- **Completed**: [To be filled by agent]
- **Depends On**: Phase 1 (New Agent Interface)

## Overview
Update the CLI to use the new agent interface while adding comprehensive AI configuration options. This phase makes the new agent interface accessible to users.

## Scope
- Update `cli/process.py` to use new agent creation functions
- Add missing CLI options (thinking-effort, temperature, retry-count)
- Improve CLI help text with rich panels and examples
- Maintain backward compatibility during transition
- Comprehensive CLI testing

## Acceptance Criteria
- [ ] `product-labeling` command uses new agent interface
- [ ] All AI configuration available via CLI options
- [ ] Rich help text with organized panels and examples
- [ ] Backward compatibility maintained (existing commands work)
- [ ] CLI integration tests cover all new options
- [ ] Manual testing confirms end-to-end functionality
- [ ] Quality checks pass (black, ruff, mypy, pytest)

## Implementation Details

### Files to Modify
```
src/github_analysis/cli/process.py     # Main command updates
src/github_analysis/cli/options.py    # Shared option definitions
tests/test_cli/test_process.py         # CLI integration tests
```

### New CLI Options to Add
```python
@app.command()
async def product_labeling(
    # Existing options
    org: str = Option(..., help="GitHub organization"),
    repo: str = Option(None, help="Repository name"),
    issue_number: int = Option(None, help="Specific issue number"),
    
    # New AI configuration options
    model: str = Option("openai:gpt-4", help="AI model (provider:name)"),
    thinking_effort: str = Option(None, help="Thinking effort: low, medium, high"),
    temperature: float = Option(0.0, help="Model temperature (0.0-2.0)"),
    retry_count: int = Option(2, help="Number of retries on failure"),
    
    # Processing options
    include_images: bool = Option(True, help="Include image analysis"),
    dry_run: bool = Option(False, help="Preview without applying changes"),
    verbose: bool = Option(False, help="Show detailed output"),
):
```

### Rich Help Text Structure
```python
from typer import Option
from typing import Annotated

# Use rich help panels to organize options
model: Annotated[str, Option(
    "openai:gpt-4",
    "--model", "-m",
    help="AI model in format provider:name (e.g., openai:gpt-4, anthropic:claude-3)",
    rich_help_panel="AI Configuration"
)]
```

### Testing Requirements
- Test all new CLI options individually and in combination
- Test help text rendering and organization
- Test model validation at CLI level
- Test integration with new agent interface
- Test error handling for invalid configurations
- Test dry-run mode functionality

### Manual Verification Commands
```bash
# Basic functionality
uv run github-analysis process product-labeling --org test --repo test --issue-number 1 --dry-run

# With new options
uv run github-analysis process product-labeling \
    --org test --repo test --issue-number 1 \
    --model anthropic:claude-3-haiku-20241022 \
    --thinking-effort high \
    --temperature 0.5 \
    --retry-count 3 \
    --dry-run

# Help text quality
uv run github-analysis process product-labeling --help

# Quality checks
uv run pytest tests/test_cli/test_process.py -v
```

## Agent Instructions

### During Implementation
1. Document discoveries and challenges in "Implementation Notes" section below
2. Note any deviations from planned approach and why
3. Record testing insights and effective strategies
4. List all files modified with brief description

### Learning from Phase 1
[Read Phase 1 notes for insights about agent creation, model validation, etc.]

### Before Marking Complete
1. Update status and completion timestamp
2. Add recommendations for next phase agent (batch processing)
3. Include working verification commands
4. Note any technical debt or follow-up items

### Handoff Requirements
- All tests passing
- Manual verification commands documented and working
- Clear notes on what the batch processing agent should know
- Any blockers or dependencies clearly stated

## Implementation Notes
[Agent fills this in during work]

### Discoveries
[What did you learn about CLI integration, option handling, etc.?]

### Challenges Encountered
[What problems did you face and how did you solve them?]

### Code Changes Made
[List of files created/modified and why]

### Testing Insights
[What CLI testing strategies worked? What to avoid?]

### Recommendations for Next Phase
[What should the batch processing agent know?]

### Files Modified
[Detailed list with descriptions]

### Verification Commands That Worked
[Copy the exact commands that successfully verify this phase]

## Success Criteria
✅ CLI provides full access to new agent interface
✅ Help text is well-organized and informative
✅ All configuration options work as expected
✅ Backward compatibility maintained
✅ Comprehensive test coverage
✅ End-to-end manual testing passes