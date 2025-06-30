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


class StoredIssue(BaseModel):
    """Model for issues as stored in JSON files."""

    org: str
    repo: str
    issue: GitHubIssue
    metadata: dict[str, Any]
