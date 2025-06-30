"""Pydantic models for GitHub data structures."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class GitHubUser(BaseModel):
    """GitHub user model."""

    login: str
    id: int


class GitHubLabel(BaseModel):
    """GitHub label model."""

    name: str
    color: str
    description: str | None = None


class GitHubComment(BaseModel):
    """GitHub comment model."""

    id: int
    user: GitHubUser
    body: str
    created_at: datetime
    updated_at: datetime


class GitHubAttachment(BaseModel):
    """GitHub attachment model for issue and comment attachments."""

    original_url: str
    filename: str
    local_path: str | None = None
    content_type: str | None = None
    size: int | None = None
    downloaded: bool = False
    source: str  # "issue_body" or "comment_{id}"


class GitHubIssue(BaseModel):
    """GitHub issue model."""

    number: int
    title: str
    body: str | None = None
    state: str
    labels: list[GitHubLabel]
    user: GitHubUser
    comments: list[GitHubComment] = []
    created_at: datetime
    updated_at: datetime
    repository_name: str | None = None  # Repository name for organization-wide searches
    attachments: list[GitHubAttachment] = []  # Issue and comment attachments


class AttachmentMetadata(BaseModel):
    """Metadata for downloaded attachments."""

    issue_reference: dict[str, Any]
    downloaded_at: datetime
    attachments: list[GitHubAttachment]


class StoredIssue(BaseModel):
    """Model for issues as stored in JSON files."""

    org: str
    repo: str
    issue: GitHubIssue
    metadata: dict[str, Any]
