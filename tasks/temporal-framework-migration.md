# Task: Migrate to Temporal Framework via Submodule

## Status
**Status:** Planning
**Assigned:** TBD
**Priority:** High
**Estimated Effort:** 3-4 days

## Overview

Migrate gh-analysis from vendored runner utilities to using the centralized Temporal PydanticAI Framework as a git submodule. This eliminates code duplication, provides a single source of truth for agent infrastructure, and enables easy updates when the framework evolves.

## Background

### Current Problem
The gh-analysis repository currently vendors runner utilities from context-experiments:
- `gh_analysis/runners/utils/` contains copied code from context-experiments
- `gh_analysis/runners/summary/utils/` contains another copy of similar utilities
- Manual synchronization required when utilities are updated
- Git history shows vendoring commits that are difficult to maintain
- Code duplication across multiple locations within the same repository

### Solution Pattern (Proven in exp05-temporal)
The exp05-temporal worktree in context-experiments demonstrates the successful pattern:
1. Add temporal framework as a git submodule in `framework/` directory
2. Import framework utilities directly from the submodule
3. Create local adapters only when gh-analysis-specific behavior is needed
4. Keep all agent definitions, prompts, and models in the application layer

### Temporal Framework Capabilities
The framework at `~/src/temporal` (branch: `pydantic-temporal-framework`) provides:
- **Tool-Level Durability**: Each agent tool call becomes a Temporal activity with individual retry policies
- **MCP Auto-Discovery**: Automatically discover and integrate MCP server tools as Temporal activities
- **Multi-Agent Orchestration**: Compose multiple specialized agents in workflows
- **Full Observability**: Every tool call visible in Temporal UI with detailed tracking
- **Standardized Infrastructure**: Common utilities for tracing, context management, and history trimming

## Acceptance Criteria

### Submodule Setup
- [ ] Temporal framework added as git submodule at `framework/` directory
- [ ] Submodule points to `~/src/temporal` on `pydantic-temporal-framework` branch
- [ ] Submodule can be initialized and updated via standard git commands
- [ ] Framework dependencies compatible with gh-analysis dependencies (Python 3.12+, PydanticAI 1.0.14+)

### Remove Vendored Code
- [ ] Delete `gh_analysis/runners/utils/` directory (currently vendored from context-experiments)
- [ ] Delete `gh_analysis/runners/summary/utils/` directory (duplicate utilities)
- [ ] Remove git history pollution from vendoring commits (squash/rewrite if needed)
- [ ] Clean up any references to old vendored paths in import statements

### Framework Integration
- [ ] Import `create_mcp_toolset` from framework for MCP server integration
- [ ] Use framework's standardized patterns for agent creation
- [ ] Leverage framework's tracing and observability utilities
- [ ] Apply framework's history trimming and context management

### Adapt Existing Runners
- [ ] Update all runners in `gh_analysis/runners/troubleshooting/` to import from framework
- [ ] Update all runners in `gh_analysis/runners/summary/` to import from framework
- [ ] Update all runners in `gh_analysis/runners/base/` to import from framework
- [ ] Create minimal adapter layer in `gh_analysis/runners/adapters/` for gh-analysis-specific customizations
- [ ] Preserve all existing functionality - no behavioral changes from user perspective

### Local Customizations (Adapters)
- [ ] Create `gh_analysis/runners/adapters/` directory for gh-analysis-specific wrappers
- [ ] Implement adapters only where gh-analysis behavior differs from framework defaults
- [ ] Document why each adapter exists and what it customizes
- [ ] Keep adapters minimal - prefer using framework utilities directly

### Testing and Validation
- [ ] All existing tests pass without modification
- [ ] CLI commands work identically to current implementation
- [ ] Agent behavior unchanged (same model settings, prompts, tools)
- [ ] MCP server integration works with framework's toolset creation
- [ ] Tracing and observability functions work with framework utilities

### Documentation
- [ ] Update `CLAUDE.md` with submodule initialization instructions
- [ ] Document the submodule update process for pulling framework changes
- [ ] Explain adapter pattern and when to create adapters vs using framework directly
- [ ] Update architecture documentation to reference framework usage

## Implementation Plan

### Phase 1: Add Temporal Framework as Submodule

**Objective**: Integrate the framework without breaking existing code.

#### Step 1.1: Initialize Submodule
```bash
# From gh-analysis repository root
cd /Users/chris/src/github-issue-analysis

# Add temporal framework as submodule
git submodule add /Users/chris/src/temporal framework

# Configure submodule to track pydantic-temporal-framework branch
cd framework
git checkout pydantic-temporal-framework
cd ..

# Update .gitmodules to track the branch
git config -f .gitmodules submodule.framework.branch pydantic-temporal-framework

# Commit submodule addition
git add .gitmodules framework
git commit -m "Add temporal framework as submodule"
```

**Validation**:
```bash
# Verify submodule is properly configured
git submodule status
cat .gitmodules

# Test framework imports work
uv run python -c "from framework.temporal_framework import create_mcp_toolset; print('✓ Framework imports work')"
```

#### Step 1.2: Update Dependencies
Add framework dependencies to `pyproject.toml`:
```toml
[project]
dependencies = [
    # Existing dependencies...

    # Temporal framework requirements (align with framework/pyproject.toml)
    "temporalio[pydantic]>=1.18.0",
    "mcp>=1.16.0",
]
```

**Validation**:
```bash
# Sync dependencies
uv sync --all-extras

# Verify no conflicts
uv run pytest --collect-only
```

### Phase 2: Create Adapter Layer Structure

**Objective**: Establish clean separation between framework code and gh-analysis customizations.

#### Step 2.1: Create Adapter Directory
```bash
mkdir -p gh_analysis/runners/adapters
touch gh_analysis/runners/adapters/__init__.py
```

#### Step 2.2: Identify Customization Needs
Review current vendored code to determine what needs adaptation:
- **MCP Server Creation**: gh-analysis uses `uv run troubleshoot-mcp-server` locally (not podman)
- **GitHub Context Building**: May need gh-analysis-specific issue formatting
- **Snowflake Integration**: Memory-enhanced runners need Snowflake client wrappers
- **History Trimming**: May have gh-analysis-specific token limits

Create adapters ONLY for these customizations. Everything else imports from framework directly.

#### Step 2.3: Implement MCP Adapter
Create `gh_analysis/runners/adapters/mcp_adapter.py`:
```python
"""MCP adapter for gh-analysis-specific MCP server configuration."""

import os
import tempfile
import logging
from typing import Optional

# Import framework's MCP utilities
from framework.temporal_framework.mcp import create_mcp_toolset

logger = logging.getLogger(__name__)


def create_troubleshoot_mcp_server(
    bundle_storage: Optional[str] = None,
    preserve_bundles: bool = True,
) -> object:
    """
    Create troubleshoot-mcp-server using gh-analysis conventions.

    This adapter wraps the framework's create_mcp_toolset to use:
    - Local `uv run troubleshoot-mcp-server` command (not podman)
    - gh-analysis environment variable conventions
    - Isolated temporary directories for MCP workspaces

    Args:
        bundle_storage: Directory for persistent bundle storage (default: /tmp/mcp-bundles)
        preserve_bundles: Whether to preserve bundles across server restarts

    Returns:
        MCP toolset configured for gh-analysis usage
    """
    # Validate required environment variables
    sbctl_token = os.getenv("SBCTL_TOKEN")
    if not sbctl_token:
        raise ValueError("SBCTL_TOKEN environment variable is required for MCP server")

    # Optional GitHub token
    github_token = os.getenv("GITHUB_TOKEN")

    # Configure bundle storage
    if bundle_storage is None:
        bundle_storage = "/tmp/mcp-bundles"

    # Build environment for MCP server
    env = {
        "SBCTL_TOKEN": sbctl_token,
        "MCP_BUNDLE_STORAGE": bundle_storage,
        "MCP_SINGLE_BUNDLE_MODE": "true",
        "PRESERVE_BUNDLES": str(preserve_bundles).lower(),
    }

    if github_token:
        env["GITHUB_TOKEN"] = github_token
        logger.debug("GitHub token provided to MCP server")

    # Use framework's MCP toolset creation with gh-analysis command
    return create_mcp_toolset(
        "troubleshoot-mcp-server",
        command=["uv", "run", "troubleshoot-mcp-server"],
        env=env,
        toolset_id="troubleshoot-mcp",
    )
```

**Validation**:
```python
# Test adapter creates functional MCP server
from gh_analysis.runners.adapters.mcp_adapter import create_troubleshoot_mcp_server

mcp_server = create_troubleshoot_mcp_server()
print(f"✓ MCP server created: {mcp_server}")
```

### Phase 3: Migrate Existing Runners

**Objective**: Update all runner implementations to use framework instead of vendored code.

#### Step 3.1: Update Import Statements
For each runner file, replace vendored imports with framework imports:

**Before** (using vendored code):
```python
from ..utils.github_runner import GitHubIssueRunner
from ..utils.history import create_history_trimmer
from ..utils.mcp import create_troubleshoot_mcp_server
```

**After** (using framework):
```python
# Import from framework submodule
from framework.temporal_framework.agents import create_temporal_agent
from framework.temporal_framework.mcp import create_mcp_toolset

# Import from local adapters only when needed
from ..adapters.mcp_adapter import create_troubleshoot_mcp_server
```

#### Step 3.2: Update Runner Implementations

**Example: Product Labeling Runner**
```python
"""Product labeling runner using Temporal framework."""

from typing import Any
from pydantic_ai import Agent

from framework.temporal_framework.agents import register_agent_activities
from gh_analysis.ai.models import ProductLabelingResponse
from gh_analysis.ai.prompts import PRODUCT_LABELING_PROMPT


class ProductLabelingRunner:
    """Product labeling analysis using Temporal framework patterns."""

    def __init__(
        self,
        model_name: str = "openai:o4-mini",
        model_settings: dict[str, Any] | None = None,
    ) -> None:
        # Create agent using PydanticAI directly (framework provides infrastructure)
        self.agent = Agent(
            model=model_name,
            output_type=ProductLabelingResponse,
            instructions=PRODUCT_LABELING_PROMPT,
            retries=2,
            instrument=True,
            model_settings=model_settings or {},
        )
        self.runner_name = "product-labeling"

    async def analyze(self, issue_data: dict) -> ProductLabelingResponse:
        """Run product labeling analysis."""
        # Framework handles tracing and instrumentation via agent.instrument=True
        result = await self.agent.run(issue_data)
        return result.output
```

**Example: GPT-5 Troubleshooting Runner**
```python
"""GPT-5 Medium reasoning troubleshooting runner using Temporal framework."""

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel

from framework.temporal_framework.mcp import create_mcp_toolset
from gh_analysis.ai.models import TechnicalAnalysis
from gh_analysis.ai.prompts import TROUBLESHOOTING_PROMPT
from gh_analysis.runners.adapters.mcp_adapter import create_troubleshoot_mcp_server


class GPT5MediumTroubleshootRunner:
    """GPT-5 Medium reasoning troubleshooting using Temporal framework."""

    def __init__(self) -> None:
        # Use adapter for gh-analysis-specific MCP configuration
        mcp_tools = create_troubleshoot_mcp_server()

        # Create agent with framework-compatible configuration
        self.agent = Agent(
            model=OpenAIResponsesModel("gpt-5"),
            output_type=TechnicalAnalysis,
            instructions=TROUBLESHOOTING_PROMPT,
            toolsets=[mcp_tools],
            instrument=True,
            retries=2,
            model_settings={
                "timeout": 1800.0,
                "openai_reasoning_effort": "medium",
                "stream": False,
                "parallel_tool_calls": True,
            },
        )
        self.runner_name = "gpt5-medium"

    async def analyze(self, issue_data: dict) -> TechnicalAnalysis:
        """Run troubleshooting analysis."""
        result = await self.agent.run(issue_data)
        return result.output
```

#### Step 3.3: Update All Runners
Apply the pattern above to all runners:
- `gh_analysis/runners/base/product_labeling.py` ✓
- `gh_analysis/runners/troubleshooting/gpt5_mini_medium.py`
- `gh_analysis/runners/troubleshooting/gpt5_mini_high.py`
- `gh_analysis/runners/troubleshooting/gpt5_medium.py`
- `gh_analysis/runners/troubleshooting/gpt5_high.py`
- `gh_analysis/runners/troubleshooting/memory_tool/*.py` (6 runners)
- `gh_analysis/runners/summary/multi_summary.py`
- `gh_analysis/runners/summary/specialized/*.py` (6 specialized agents)

**Critical**: Preserve all existing model settings, prompts, and configurations. Only change imports and use framework utilities.

### Phase 4: Remove Vendored Code

**Objective**: Clean up duplicated code now that framework provides the utilities.

#### Step 4.1: Remove Vendored Directories
```bash
# Delete vendored utils (now provided by framework submodule)
git rm -r gh_analysis/runners/utils/
git rm -r gh_analysis/runners/summary/utils/

# Commit removal
git commit -m "Remove vendored runner utilities (now using framework submodule)"
```

#### Step 4.2: Update Import References
Search for any remaining references to deleted paths:
```bash
# Find any imports still referencing old vendored code
rg "from.*runners\.utils" gh_analysis/
rg "from.*summary\.utils" gh_analysis/

# Update any found references to use framework or adapters
```

### Phase 5: Testing and Validation

**Objective**: Ensure all functionality works identically with framework.

#### Step 5.1: Run Test Suite
```bash
# Format and lint
uv run ruff format . && uv run ruff check --fix --unsafe-fixes

# Type checking
uv run mypy .

# Run all tests
uv run pytest -v
```

#### Step 5.2: Integration Testing
**IMPORTANT**: User must provide test repository information (never hardcode).

```bash
# Product labeling test (ask user for org/repo/issue)
uv run gh-analysis process product-labeling \
  --org [USER-ORG] --repo [USER-REPO] --issue-number [USER-ISSUE] \
  --dry-run

# Troubleshooting test with MCP tools (ask user for org/repo/issue)
uv run gh-analysis process troubleshoot \
  --org [USER-ORG] --repo [USER-REPO] --issue-number [USER-ISSUE] \
  --agent gpt5_medium --dry-run
```

#### Step 5.3: Verify MCP Integration
```bash
# Test MCP server creation from adapter
uv run python -c "
from gh_analysis.runners.adapters.mcp_adapter import create_troubleshoot_mcp_server
import os
os.environ['SBCTL_TOKEN'] = 'test-token'
server = create_troubleshoot_mcp_server()
print('✓ MCP server created successfully')
"

# Test framework toolset creation
uv run python -c "
from framework.temporal_framework.mcp import create_mcp_toolset
import os
os.environ['SBCTL_TOKEN'] = 'test-token'
toolset = create_mcp_toolset('troubleshoot-mcp-server', env={'SBCTL_TOKEN': 'test-token'})
print('✓ Framework MCP toolset created successfully')
"
```

### Phase 6: Documentation

**Objective**: Document the framework integration for future developers.

#### Step 6.1: Update CLAUDE.md
Add section on framework submodule usage:
```markdown
## Temporal Framework Integration

This repository uses the Temporal PydanticAI Framework as a git submodule to provide
standardized agent infrastructure.

### First-Time Setup
```bash
# Clone repository with submodules
git clone --recurse-submodules <repo-url>

# Or initialize submodules after cloning
git submodule init
git submodule update
```

### Updating Framework
```bash
# Pull latest framework changes
cd framework
git pull origin pydantic-temporal-framework
cd ..

# Commit submodule update
git add framework
git commit -m "Update temporal framework to latest version"
```

### Framework Usage Patterns

**Direct Import** (when using framework utilities as-is):
```python
from framework.temporal_framework.mcp import create_mcp_toolset
from framework.temporal_framework.agents import create_temporal_agent
```

**Adapter Pattern** (when gh-analysis needs custom behavior):
```python
from gh_analysis.runners.adapters.mcp_adapter import create_troubleshoot_mcp_server
```

### When to Create Adapters

Create adapters in `gh_analysis/runners/adapters/` only when:
1. gh-analysis has different environment variable conventions than framework
2. gh-analysis uses different command patterns (e.g., `uv run` vs podman)
3. gh-analysis needs Snowflake integration or other app-specific features

For everything else, import framework utilities directly.
```

#### Step 6.2: Update Architecture Documentation
Update `docs/architecture.md`:
```markdown
### Framework Integration

gh-analysis uses the Temporal PydanticAI Framework (via git submodule) for:
- **MCP Tool Integration**: Auto-discovery and registration of MCP server tools
- **Agent Infrastructure**: Standardized agent creation and configuration patterns
- **Observability**: Tracing and instrumentation utilities
- **Context Management**: History trimming and context length management

The framework is located in the `framework/` submodule and provides reusable
infrastructure shared across multiple projects (context-experiments, gh-analysis, etc.).

#### Adapter Layer

gh-analysis maintains a minimal adapter layer in `gh_analysis/runners/adapters/`
for application-specific customizations:
- MCP server configuration using local `uv run` commands
- Snowflake client integration for memory-enhanced runners
- GitHub issue context formatting specific to gh-analysis

All other utilities are imported directly from the framework submodule.
```

#### Step 6.3: Create Migration Guide
Document this migration for reference:
```markdown
# Framework Migration Guide

## What Changed

**Before**: Vendored utilities in `gh_analysis/runners/utils/`
**After**: Framework submodule in `framework/` with adapters in `gh_analysis/runners/adapters/`

## Benefits

1. **Single Source of Truth**: Framework updates automatically available
2. **No Code Duplication**: Shared infrastructure across projects
3. **Clear Separation**: Framework code vs application code
4. **Easy Updates**: `git submodule update` pulls latest framework

## For Developers

### Adding New Runners

1. Import framework utilities directly when possible
2. Create adapters only for gh-analysis-specific behavior
3. Follow existing runner patterns in `gh_analysis/runners/`

### Updating Framework

```bash
cd framework && git pull && cd ..
git add framework && git commit -m "Update framework"
```
```

## Testing Strategy

### Unit Tests
- [ ] Test adapter layer functionality (MCP server creation, env setup)
- [ ] Test runner instantiation with framework imports
- [ ] Test framework submodule imports work correctly
- [ ] Test backward compatibility with existing runner interfaces

### Integration Tests
**CRITICAL**: Never hardcode repository information. Always ask user for test repos.

```bash
# Test product labeling (user provides org/repo/issue)
uv run gh-analysis collect --org [USER-ORG] --repo [USER-REPO] --issue-number [USER-ISSUE]
uv run gh-analysis process product-labeling --org [USER-ORG] --repo [USER-REPO] --issue-number [USER-ISSUE] --dry-run

# Test troubleshooting with MCP (user provides org/repo/issue)
uv run gh-analysis process troubleshoot --org [USER-ORG] --repo [USER-REPO] --issue-number [USER-ISSUE] --agent gpt5_medium --dry-run

# Test memory-enhanced runner (user provides org/repo/issue)
uv run gh-analysis process troubleshoot --org [USER-ORG] --repo [USER-REPO] --issue-number [USER-ISSUE] --agent claude_sonnet_mt --dry-run
```

### Validation Checklist
- [ ] All existing CLI commands work identically
- [ ] MCP server integration works via adapter
- [ ] Agent behavior unchanged (same outputs for same inputs)
- [ ] Tracing and observability functions work
- [ ] Framework submodule initializes correctly on fresh clone
- [ ] Quality checks pass: `uv run ruff format . && uv run ruff check --fix && uv run mypy . && uv run pytest`

## Dependencies

### Framework Requirements
The framework has these core dependencies (from framework/pyproject.toml):
```toml
temporalio[pydantic]>=1.18.0
pydantic-ai>=1.0.14
mcp>=1.16.0
pydantic>=2.11.9
httpx>=0.28.1
```

These should be compatible with gh-analysis's existing dependencies.

### Dependency Verification
```bash
# Check for conflicts
uv sync --all-extras
uv run pytest --collect-only

# Verify no version conflicts
uv tree | grep -E "(pydantic|temporal|mcp)"
```

## Migration Checklist

### Preparation
- [ ] Review current vendored code in `gh_analysis/runners/utils/`
- [ ] Review framework capabilities in `~/src/temporal`
- [ ] Identify customizations that need adapters
- [ ] Plan import statement changes for all runners

### Implementation
- [ ] Add temporal framework as submodule at `framework/`
- [ ] Configure submodule to track `pydantic-temporal-framework` branch
- [ ] Update `pyproject.toml` with framework dependencies
- [ ] Create adapter directory structure in `gh_analysis/runners/adapters/`
- [ ] Implement MCP adapter for gh-analysis conventions
- [ ] Update all runner imports to use framework
- [ ] Remove vendored `gh_analysis/runners/utils/` directory
- [ ] Remove vendored `gh_analysis/runners/summary/utils/` directory
- [ ] Update all import references throughout codebase

### Testing
- [ ] Run full test suite and fix any failures
- [ ] Test product labeling runner with framework imports
- [ ] Test troubleshooting runners with MCP integration
- [ ] Test memory-enhanced runners with Snowflake
- [ ] Verify summary runners work with framework
- [ ] Test on fresh clone with submodule initialization

### Documentation
- [ ] Update `CLAUDE.md` with submodule instructions
- [ ] Update `docs/architecture.md` with framework integration
- [ ] Document adapter pattern and usage
- [ ] Create migration guide for reference

### Cleanup
- [ ] Remove any remaining references to vendored code
- [ ] Clean up import statements
- [ ] Run quality checks and fix issues
- [ ] Update git history if needed (squash vendoring commits)

## Success Metrics

### Functional Requirements
- [ ] 100% feature parity with current implementation
- [ ] All existing CLI commands work identically
- [ ] All tests pass without modification
- [ ] MCP integration works via adapter
- [ ] Agent behavior unchanged

### Code Quality
- [ ] Passes formatting: `uv run ruff format .`
- [ ] Passes linting: `uv run ruff check --fix`
- [ ] Passes type checking: `uv run mypy .`
- [ ] Passes tests: `uv run pytest`

### Architecture Benefits
- [ ] No more vendored code duplication
- [ ] Framework updates via git submodule update
- [ ] Clear separation between framework and application
- [ ] Minimal adapter layer for customizations
- [ ] Shared infrastructure with context-experiments

## Notes

- **Submodule Pattern**: Proven successful in exp05-temporal worktree
- **No Breaking Changes**: Users see identical CLI behavior
- **Framework Evolution**: Easy to pull framework updates
- **Adapter Minimalism**: Keep adapters small and focused
- **Documentation Critical**: Clear instructions for submodule workflow

## Future Enhancements Enabled

Once migration is complete:

### Framework Updates
- Pull framework improvements automatically via `git submodule update`
- Benefit from framework bug fixes and new features
- Contribute framework improvements back to benefit all projects

### Temporal Workflows
- Use framework's workflow patterns for distributed orchestration
- Tool-level durability for long-running agent interactions
- Multi-agent workflows with Temporal coordination

### Observability
- Framework's built-in tracing and instrumentation
- Integration with Temporal UI for workflow visibility
- Standardized logging and monitoring patterns

## Risk Mitigation

- **Gradual Migration**: Test each runner after updating imports
- **Adapter Safety**: Adapters provide fallback for customizations
- **Test Coverage**: Comprehensive testing before removing vendored code
- **Rollback Plan**: Git makes it easy to revert if issues arise
- **User Transparency**: No visible changes to CLI or behavior

## Related Files

- Framework: `~/src/temporal` (branch: pydantic-temporal-framework)
- Reference: `~/src/context-experiments/trees/exp05-temporal` (proven pattern)
- Task History: `tasks/migrate-to-runner-pattern.md` (previous migration)
- Git History: Commits `8d9eb8d`, `9dbf697` (vendoring to be replaced)
