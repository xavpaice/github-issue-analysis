"""GitHub API client using PyGitHub."""

import os
import time

from github import Github
from github.GithubException import RateLimitExceededException, UnknownObjectException
from github.Issue import Issue
from github.IssueComment import IssueComment
from github.Label import Label
from github.NamedUser import NamedUser
from github.Repository import Repository
from rich.console import Console

from .models import GitHubComment, GitHubIssue, GitHubLabel, GitHubUser

console = Console()


class GitHubClient:
    """GitHub API client with rate limiting and authentication."""

    def __init__(self, token: str | None = None):
        """Initialize GitHub client with authentication.

        Args:
            token: GitHub personal access token. If None, reads from
                GITHUB_TOKEN env var.
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub token is required. Set GITHUB_TOKEN environment variable."
            )

        self.github = Github(self.token)
        self._check_rate_limit()

    def _check_rate_limit(self) -> None:
        """Check rate limit and sleep if necessary."""
        try:
            rate_limit = self.github.get_rate_limit()
            remaining = rate_limit.core.remaining

            console.print(f"GitHub API rate limit: {remaining} requests remaining")

            if remaining < 10:
                reset_time = rate_limit.core.reset.timestamp()
                sleep_time = reset_time - time.time() + 1
                console.print(
                    f"Rate limit low, sleeping for {sleep_time:.1f} seconds..."
                )
                time.sleep(sleep_time)

        except Exception as e:
            console.print(f"Warning: Could not check rate limit: {e}")

    def _convert_user(self, github_user: NamedUser) -> GitHubUser:
        """Convert PyGitHub user to our model."""
        return GitHubUser(login=github_user.login, id=github_user.id)

    def _convert_label(self, github_label: Label) -> GitHubLabel:
        """Convert PyGitHub label to our model."""
        return GitHubLabel(
            name=github_label.name,
            color=github_label.color,
            description=github_label.description,
        )

    def _convert_comment(self, github_comment: IssueComment) -> GitHubComment:
        """Convert PyGitHub comment to our model."""
        return GitHubComment(
            id=github_comment.id,
            user=self._convert_user(github_comment.user),
            body=github_comment.body,
            created_at=github_comment.created_at,
            updated_at=github_comment.updated_at,
        )

    def _convert_issue(self, github_issue: Issue) -> GitHubIssue:
        """Convert PyGitHub issue to our model."""
        labels = [self._convert_label(label) for label in github_issue.labels]

        # Fetch comments for the issue
        comments = []
        try:
            for comment in github_issue.get_comments():
                comments.append(self._convert_comment(comment))
        except Exception as e:
            console.print(
                f"Warning: Could not fetch comments for issue "
                f"#{github_issue.number}: {e}"
            )

        return GitHubIssue(
            number=github_issue.number,
            title=github_issue.title,
            body=github_issue.body,
            state=github_issue.state,
            labels=labels,
            user=self._convert_user(github_issue.user),
            comments=comments,
            created_at=github_issue.created_at,
            updated_at=github_issue.updated_at,
        )

    def get_repository(self, org: str, repo: str) -> Repository:
        """Get repository object."""
        try:
            return self.github.get_repo(f"{org}/{repo}")
        except UnknownObjectException:
            raise ValueError(f"Repository {org}/{repo} not found")

    def get_issue(self, org: str, repo: str, issue_number: int) -> GitHubIssue:
        """Get a specific issue with all its details."""
        self._check_rate_limit()

        repository = self.get_repository(org, repo)
        github_issue = repository.get_issue(issue_number)

        return self._convert_issue(github_issue)

    def search_issues(
        self,
        org: str,
        repo: str,
        labels: list[str] | None = None,
        state: str = "open",
        limit: int = 10,
    ) -> list[GitHubIssue]:
        """Search for issues in a repository.

        Args:
            org: Organization name
            repo: Repository name
            labels: List of label names to filter by
            state: Issue state (open, closed, all)
            limit: Maximum number of issues to return

        Returns:
            List of GitHubIssue objects
        """
        self._check_rate_limit()

        # Build search query
        query_parts = [f"repo:{org}/{repo}", "is:issue"]

        if state != "all":
            query_parts.append(f"state:{state}")

        if labels:
            for label in labels:
                query_parts.append(f"label:{label}")

        query = " ".join(query_parts)
        console.print(f"Searching with query: {query}")

        try:
            # Use GitHub search API
            issues = self.github.search_issues(query)

            # Convert to our models, limiting results
            result_issues = []
            for i, github_issue in enumerate(issues):
                if i >= limit:
                    break

                try:
                    result_issues.append(self._convert_issue(github_issue))
                    console.print(
                        f"Processed issue #{github_issue.number}: {github_issue.title}"
                    )
                except Exception as e:
                    console.print(f"Error processing issue #{github_issue.number}: {e}")
                    continue

            return result_issues

        except RateLimitExceededException:
            console.print("Rate limit exceeded, waiting...")
            time.sleep(60)
            return self.search_issues(org, repo, labels, state, limit)
        except Exception as e:
            console.print(f"Error searching issues: {e}")
            raise
