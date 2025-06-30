# Architecture Overview

## System Components

### Core Application
```
github_issue_analysis/
├── cli/              # Command-line interface
├── github_client/    # GitHub API integration
├── ai/              # AI processing layer
└── storage/         # Data persistence
```

### Data Flow
```
GitHub API → Issue Collection → JSON Storage → AI Processing → Results
```

### CLI Commands
- `collect`: Fetch issues from GitHub using advanced search
- `process`: Run AI analysis on collected issues

## Component Details

### GitHub Client Layer
- **search.py**: Wrapper around GitHub advanced search API
- **fetcher.py**: Issue fetching with rate limiting and pagination
- **models.py**: Pydantic models for GitHub data structures

### AI Processing Layer  
- **providers.py**: OpenAI and Anthropic client abstractions
- **processors.py**: Issue analysis implementations
- **prompts.py**: Prompt templates and management

### Storage Layer
- **Issues**: JSON files in `data/issues/` named `org_repo_issue_<number>.json`
- **Results**: AI analysis results in `data/results/`
- **Attachments**: Files in `data/attachments/org_repo_issue_<number>/` directories
- **manager.py**: File I/O operations and data management

## Development Workflow

### Agent Development Process
1. Agent reads task specification from `tasks/task-name.md`
2. Creates git worktree: `git worktree add trees/task-name -b feature/task-name`
3. Implements feature with full test coverage
4. Documents progress and validation in task file
5. Creates pull request when complete

### Task Structure
Each task should deliver a complete, testable feature that can be used independently.

## Design Principles

- **Separation of Concerns**: Clear boundaries between GitHub API, AI processing, and storage
- **Extensibility**: Easy to add new AI processors and data sources
- **Testability**: Each component can be tested in isolation
- **Agent-Friendly**: Clear documentation and minimal boilerplate for rapid development