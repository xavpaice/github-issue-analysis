"""Tests for GitHub search functionality."""

from unittest.mock import Mock

from github_issue_analysis.github_client.client import GitHubClient
from github_issue_analysis.github_client.models import GitHubIssue
from github_issue_analysis.github_client.search import (
    GitHubSearcher,
    build_github_query,
)


class TestGitHubSearcher:
    """Test GitHubSearcher class."""

    def test_init(self):
        """Test searcher initialization."""
        mock_client = Mock(spec=GitHubClient)
        searcher = GitHubSearcher(mock_client)
        assert searcher.client == mock_client

    def test_search_repository_issues(self):
        """Test searching repository issues."""
        mock_client = Mock(spec=GitHubClient)
        mock_issues = [Mock(spec=GitHubIssue)]
        mock_client.search_issues.return_value = mock_issues

        searcher = GitHubSearcher(mock_client)

        results = searcher.search_repository_issues(
            org="testorg",
            repo="testrepo",
            labels=["bug", "enhancement"],
            state="open",
            limit=5,
        )

        assert results == mock_issues
        mock_client.search_issues.assert_called_once_with(
            org="testorg",
            repo="testrepo",
            labels=["bug", "enhancement"],
            state="open",
            limit=5,
        )

    def test_search_repository_issues_defaults(self):
        """Test searching with default parameters."""
        mock_client = Mock(spec=GitHubClient)
        mock_issues = [Mock(spec=GitHubIssue)]
        mock_client.search_issues.return_value = mock_issues

        searcher = GitHubSearcher(mock_client)

        results = searcher.search_repository_issues(org="testorg", repo="testrepo")

        assert results == mock_issues
        mock_client.search_issues.assert_called_once_with(
            org="testorg", repo="testrepo", labels=None, state="open", limit=10
        )

    def test_get_single_issue(self):
        """Test getting a single issue."""
        mock_client = Mock(spec=GitHubClient)
        mock_issue = Mock(spec=GitHubIssue)
        mock_client.get_issue.return_value = mock_issue

        searcher = GitHubSearcher(mock_client)

        result = searcher.get_single_issue("testorg", "testrepo", 42)

        assert result == mock_issue
        mock_client.get_issue.assert_called_once_with("testorg", "testrepo", 42)


class TestBuildGitHubQuery:
    """Test build_github_query function."""

    def test_basic_query(self):
        """Test building basic query."""
        query = build_github_query("microsoft", "vscode")
        expected = "repo:microsoft/vscode is:issue state:open"
        assert query == expected

    def test_query_with_labels(self):
        """Test query with labels."""
        query = build_github_query("microsoft", "vscode", labels=["bug", "enhancement"])
        expected = (
            "repo:microsoft/vscode is:issue state:open label:bug label:enhancement"
        )
        assert query == expected

    def test_query_with_state_all(self):
        """Test query with state 'all'."""
        query = build_github_query("microsoft", "vscode", state="all")
        expected = "repo:microsoft/vscode is:issue"
        assert query == expected

    def test_query_with_closed_state(self):
        """Test query with closed state."""
        query = build_github_query("microsoft", "vscode", state="closed")
        expected = "repo:microsoft/vscode is:issue state:closed"
        assert query == expected

    def test_query_with_created_after(self):
        """Test query with created_after filter."""
        query = build_github_query("microsoft", "vscode", created_after="2024-01-01")
        expected = "repo:microsoft/vscode is:issue state:open created:>2024-01-01"
        assert query == expected

    def test_complex_query(self):
        """Test complex query with all parameters."""
        query = build_github_query(
            org="microsoft",
            repo="vscode",
            labels=["bug", "priority:high"],
            state="closed",
            created_after="2024-01-01",
        )
        expected = (
            "repo:microsoft/vscode is:issue state:closed label:bug "
            "label:priority:high created:>2024-01-01"
        )
        assert query == expected

    def test_query_with_empty_labels(self):
        """Test query with empty labels list."""
        query = build_github_query("microsoft", "vscode", labels=[])
        expected = "repo:microsoft/vscode is:issue state:open"
        assert query == expected

    def test_query_with_single_label(self):
        """Test query with single label."""
        query = build_github_query("microsoft", "vscode", labels=["bug"])
        expected = "repo:microsoft/vscode is:issue state:open label:bug"
        assert query == expected
