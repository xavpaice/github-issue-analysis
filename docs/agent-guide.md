# Agent Development Guide

## Getting Started

### 1. Task Assignment
- Read your assigned task from `tasks/task-name.md`
- Understand acceptance criteria and validation requirements
- Update task status to "active"

### 2. Environment Setup
```bash
# Create worktree for isolated development
git worktree add trees/task-name -b feature/task-name
cd trees/task-name

# Install dependencies
uv sync --dev
```

### 3. Development Workflow
- Implement feature following existing patterns
- Write comprehensive tests
- Document your progress in the task file
- Validate implementation matches acceptance criteria

### 4. Code Quality
```bash
# Run linting and formatting
uv run ruff check --fix
uv run black .
uv run mypy .

# Run tests
uv run pytest -v
```

## Task Documentation Requirements

### Progress Updates
Document in your task file:
- What you implemented
- How you tested it
- Any decisions or trade-offs made
- Validation steps performed

### Handoff Notes
If another agent needs to continue your work:
- Current status and what's complete
- Next steps or blockers
- Key implementation details
- How to test/validate current state

## Implementation Guidelines

### Full-Stack Features
Each task should deliver:
- Complete functionality (not partial implementation)
- CLI interface for the feature
- Comprehensive test coverage
- Error handling and validation
- Documentation updates if needed

### Code Patterns
- Follow existing code structure and naming conventions
- Use Pydantic models for data validation
- Implement proper error handling
- Add type hints throughout
- Write docstrings for public APIs

### Testing Strategy
- Unit tests for core logic
- Integration tests for CLI commands
- Mock external API calls in tests
- Test error conditions and edge cases

## Common Tasks

### Adding New AI Processors
1. Create processor class in `ai/processors.py`
2. Add prompt templates in `ai/prompts.py`
3. Integrate with CLI in `cli/process.py`
4. Add comprehensive tests

### GitHub API Extensions
1. Add new search parameters in `github_client/search.py`
2. Update data models in `github_client/models.py`
3. Add CLI options in `cli/collect.py`
4. Test with actual GitHub API

### Storage Enhancements
1. Update storage manager in `storage/manager.py`
2. Maintain backward compatibility with existing data
3. Add migration logic if needed
4. Test with existing data files