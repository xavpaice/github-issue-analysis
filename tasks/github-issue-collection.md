# Task: Basic GitHub Issue Collection

**Status:** ready

**Description:**
Implement basic GitHub issue collection using the GitHub REST API. Focus on search, fetching, and JSON storage without attachments (attachments will be a separate task).

**Files to Create:**
- `github_issue_analysis/github_client/models.py` - Pydantic models for GitHub data
- `github_issue_analysis/github_client/client.py` - HTTP client using httpx  
- `github_issue_analysis/github_client/search.py` - Search functionality
- `github_issue_analysis/cli/collect.py` - CLI collect command
- `github_issue_analysis/storage/manager.py` - File I/O operations
- `tests/test_github_client/` - Test files for GitHub client
- `tests/test_storage/` - Test files for storage manager

**Files to Modify:**
- `github_issue_analysis/cli/main.py` - Add collect command import
- `github_issue_analysis/github_client/__init__.py` - Package initialization
- `github_issue_analysis/storage/__init__.py` - Package initialization

**Implementation Details:**

**GitHub API Usage:**
- Use GitHub REST API v4: `https://api.github.com`
- Search endpoint: `GET /search/issues?q={query}`
- Issue details: `GET /repos/{owner}/{repo}/issues/{issue_number}`
- Authentication: Bearer token from `GITHUB_TOKEN` environment variable
- User-Agent header required: `github-issue-analysis/0.1.0`

**Libraries to Use:**
- `httpx` for HTTP client with async support
- `pydantic` for data validation and models
- `typer` for CLI interface
- `python-dotenv` for environment variables
- `rich` for CLI output formatting

**CLI Interface:**
```bash
uv run github-analysis collect --org microsoft --repo vscode --labels bug --limit 5
```

**Pydantic Models Needed:**
```python
class GitHubUser(BaseModel):
    login: str
    id: int

class GitHubLabel(BaseModel):  
    name: str
    color: str
    description: Optional[str] = None

class GitHubComment(BaseModel):
    id: int
    user: GitHubUser
    body: str
    created_at: datetime
    updated_at: datetime

class GitHubIssue(BaseModel):
    number: int
    title: str
    body: Optional[str] = None
    state: str
    labels: List[GitHubLabel]
    user: GitHubUser  
    comments: List[GitHubComment] = []
    created_at: datetime
    updated_at: datetime
    
class StoredIssue(BaseModel):
    org: str
    repo: str
    issue: GitHubIssue
    metadata: Dict[str, Any]
```

**Search Query Format:**
Build GitHub search queries like: `repo:microsoft/vscode is:issue label:bug created:>2024-01-01`

**Rate Limiting:**
- Check `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers
- Sleep when approaching limits (< 10 requests remaining)
- Handle 403 rate limit responses with exponential backoff

**File Storage:**
- Save as: `data/issues/microsoft_vscode_issue_12345.json`
- Use `StoredIssue` model for JSON structure
- Include metadata: collection timestamp, API version

**Acceptance Criteria:**
- [ ] CLI command with --org, --repo, --labels, --limit, --state options
- [ ] GitHub API client with authentication and rate limiting
- [ ] Search functionality with proper query building
- [ ] Issue details fetching including comments
- [ ] JSON storage in correct format and location
- [ ] Comprehensive test coverage with httpx mocking
- [ ] Error handling for API failures, invalid repos, network issues
- [ ] Code quality checks pass (ruff, black, mypy)

**Agent Notes:**
[Document your implementation decisions, testing approach, and any challenges encountered]

**Validation:**
- Run `uv run github-analysis collect --org microsoft --repo vscode --labels bug --limit 3`
- Verify 3 JSON files created in `data/issues/` with naming `microsoft_vscode_issue_*.json`
- Check JSON structure matches `StoredIssue` model
- Verify comments are included for each issue
- Test rate limiting by setting a high limit (--limit 50)
- Ensure all tests pass: `uv run pytest tests/test_github_client/ -v`
- Verify code quality: `uv run ruff check && uv run black . && uv run mypy .`