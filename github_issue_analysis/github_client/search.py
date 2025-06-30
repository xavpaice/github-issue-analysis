"""GitHub search functionality and query building."""

from .client import GitHubClient
from .models import GitHubIssue


class GitHubSearcher:
    """High-level interface for searching GitHub issues."""

    def __init__(self, client: GitHubClient):
        """Initialize searcher with GitHub client.

        Args:
            client: Authenticated GitHubClient instance
        """
        self.client = client

    def search_repository_issues(
        self,
        org: str,
        repo: str,
        labels: list[str] | None = None,
        state: str = "open",
        limit: int = 10,
    ) -> list[GitHubIssue]:
        """Search for issues in a specific repository.

        Args:
            org: Organization name
            repo: Repository name
            labels: List of label names to filter by
            state: Issue state (open, closed, all)
            limit: Maximum number of issues to return

        Returns:
            List of GitHubIssue objects with full details including comments
        """
        return self.client.search_issues(
            org=org, repo=repo, labels=labels, state=state, limit=limit
        )

    def get_single_issue(self, org: str, repo: str, issue_number: int) -> GitHubIssue:
        """Get a single issue with all details.

        Args:
            org: Organization name
            repo: Repository name
            issue_number: Issue number

        Returns:
            GitHubIssue object with full details including comments
        """
        return self.client.get_issue(org, repo, issue_number)


def build_github_query(
    org: str,
    repo: str,
    labels: list[str] | None = None,
    state: str = "open",
    created_after: str | None = None,
) -> str:
    """Build a GitHub search query string.

    Args:
        org: Organization name
        repo: Repository name
        labels: List of label names to filter by
        state: Issue state (open, closed, all)
        created_after: ISO date string to filter issues created after this date

    Returns:
        GitHub search query string

    Example:
        >>> build_github_query("microsoft", "vscode", ["bug"], "open", "2024-01-01")
        "repo:microsoft/vscode is:issue state:open label:bug created:>2024-01-01"
    """
    query_parts = [f"repo:{org}/{repo}", "is:issue"]

    if state != "all":
        query_parts.append(f"state:{state}")

    if labels:
        for label in labels:
            query_parts.append(f"label:{label}")

    if created_after:
        query_parts.append(f"created:>{created_after}")

    return " ".join(query_parts)
