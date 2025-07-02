"""GitHub search functionality and query building."""

from .client import GitHubClient
from .models import GitHubIssue


def build_exclusion_list(
    exclude_repo: list[str] | None, exclude_repos: str | None
) -> list[str]:
    """Build combined list of repositories to exclude.

    Args:
        exclude_repo: List of individual repository names to exclude
        exclude_repos: Comma-separated string of repository names to exclude

    Returns:
        List of unique repository names to exclude, with empty strings filtered out

    Example:
        >>> build_exclusion_list(["repo1", "repo2"], "repo3,repo4")
        ["repo1", "repo2", "repo3", "repo4"]
    """
    exclusions = []

    # Add individual exclusions
    if exclude_repo:
        exclusions.extend(exclude_repo)

    # Add comma-separated exclusions
    if exclude_repos:
        exclusions.extend([repo.strip() for repo in exclude_repos.split(",")])

    # Remove duplicates and empty strings
    return list(set(filter(None, exclusions)))


def build_organization_query(
    org: str,
    labels: list[str] | None = None,
    state: str = "open",
    excluded_repos: list[str] | None = None,
) -> str:
    """Build GitHub search query for organization with exclusions.

    Args:
        org: Organization name
        labels: List of label names to filter by
        state: Issue state (open, closed, all)
        excluded_repos: List of repository names to exclude

    Returns:
        GitHub search query string with exclusions

    Example:
        >>> build_organization_query("myorg", ["bug"], "closed", ["private-repo"])
        "org:myorg is:issue state:closed label:bug -repo:myorg/private-repo"
    """
    query_parts = [f"org:{org}", "is:issue"]

    if state != "all":
        query_parts.append(f"state:{state}")

    if labels:
        for label in labels:
            query_parts.append(f"label:{label}")

    # Add repository exclusions
    if excluded_repos:
        for repo in excluded_repos:
            query_parts.append(f"-repo:{org}/{repo}")

    return " ".join(query_parts)


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

    def search_organization_issues(
        self,
        org: str,
        labels: list[str] | None = None,
        state: str = "open",
        limit: int = 10,
        excluded_repos: list[str] | None = None,
    ) -> list[GitHubIssue]:
        """Search for issues across all repositories in an organization.

        Args:
            org: Organization name
            labels: List of label names to filter by
            state: Issue state (open, closed, all)
            limit: Maximum number of issues to return
            excluded_repos: List of repository names to exclude

        Returns:
            List of GitHubIssue objects with full details including comments
        """
        return self.client.search_organization_issues(
            org=org,
            labels=labels,
            state=state,
            limit=limit,
            excluded_repos=excluded_repos,
        )


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
