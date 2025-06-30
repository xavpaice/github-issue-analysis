# Task: GitHub Issue Attachment Collection

**Status:** ready

**Description:**
Extend the basic issue collection to detect, download, and store GitHub issue attachments (images, files, etc.) from issue bodies and comments.

**Prerequisites:**
- `github-issue-collection.md` must be completed first
- Requires working GitHub API client and storage manager

**Files to Create:**
- `github_issue_analysis/github_client/attachments.py` - Attachment detection and download
- `tests/test_github_client/test_attachments.py` - Attachment tests

**Files to Modify:**
- `github_issue_analysis/github_client/models.py` - Add attachment models
- `github_issue_analysis/github_client/client.py` - Add attachment download methods
- `github_issue_analysis/storage/manager.py` - Add attachment storage methods
- `github_issue_analysis/cli/collect.py` - Add --download-attachments option

**Implementation Details:**

**Attachment Detection:**
Parse issue body and comment text for:
- GitHub-hosted files: `https://github.com/{org}/{repo}/files/{id}/{filename}`
- GitHub user content: `https://user-images.githubusercontent.com/{user_id}/{filename}`
- GitHub assets: `https://github.com/{org}/{repo}/assets/{asset_id}`

**Regex Patterns:**
```python
GITHUB_FILE_PATTERN = r'https://github\.com/[\w-]+/[\w-]+/files/\d+/[\w.-]+\??[\w=&]*'
GITHUB_IMAGE_PATTERN = r'https://user-images\.githubusercontent\.com/\d+/[\w.-]+\??[\w=&]*'  
GITHUB_ASSET_PATTERN = r'https://github\.com/[\w-]+/[\w-]+/assets/\d+'
```

**Pydantic Models to Add:**
```python
class GitHubAttachment(BaseModel):
    original_url: str
    filename: str
    local_path: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None
    downloaded: bool = False
    source: str  # "issue_body" or "comment_{id}"

class AttachmentMetadata(BaseModel):
    issue_reference: Dict[str, Any]
    downloaded_at: datetime
    attachments: List[GitHubAttachment]
```

**Storage Structure:**
```
data/attachments/microsoft_vscode_issue_12345/
├── screenshot.png
├── error_log.txt  
└── attachment_metadata.json
```

**Download Strategy:**
- Use httpx to download files with proper headers
- Detect content-type from response headers
- Handle redirects and authentication
- Respect file size limits (default 10MB max)
- Generate safe local filenames

**CLI Integration:**
Add options to collect command:
- `--download-attachments / --no-download-attachments` (default: true)
- `--max-attachment-size MB` (default: 10)

**Acceptance Criteria:**
- [ ] Detect attachments in issue bodies and comments using regex patterns
- [ ] Download attachments to organized directory structure
- [ ] Store attachment metadata as JSON
- [ ] Update issue JSON to include attachment references
- [ ] Handle download failures gracefully (log and continue)
- [ ] Respect file size limits and content-type restrictions
- [ ] Comprehensive test coverage with mocked downloads
- [ ] CLI option to disable attachment downloading
- [ ] Code quality checks pass (ruff, black, mypy)

**Agent Notes:**
[Document your attachment detection strategy, download implementation, and error handling approach]

**Validation:**
- Collect issues with known attachments: `uv run github-analysis collect --org microsoft --repo vscode --labels bug --limit 2`
- Verify attachment directories created in `data/attachments/`
- Check attachment metadata JSON files exist and are valid
- Test with --no-download-attachments flag
- Verify issue JSON includes attachment references
- Test with various attachment types (images, text files, etc.)
- Ensure all tests pass: `uv run pytest tests/test_github_client/test_attachments.py -v`