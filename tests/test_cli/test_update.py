"""Tests for CLI update functionality."""

import json
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from github_issue_analysis.ai.change_detector import IssueUpdatePlan, LabelChange
from github_issue_analysis.cli.main import app

runner = CliRunner()


@pytest.fixture
def mock_github_client() -> Generator[MagicMock, None, None]:
    """Mock GitHub client for testing."""
    with patch("github_issue_analysis.cli.update.GitHubClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock methods
        mock_client.get_issue_labels.return_value = ["bug", "product::kots"]
        mock_client.update_issue_labels.return_value = True
        mock_client.add_issue_comment.return_value = True

        yield mock_client


@pytest.fixture
def sample_data_dir(temp_data_dir: Path) -> Path:
    """Create sample data directory with test files."""
    # Create directory structure (flat structure)
    issues_dir = temp_data_dir / "issues"
    issues_dir.mkdir(parents=True, exist_ok=True)
    results_dir = temp_data_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Sample issue data
    issue_data = {
        "org": "test-org",
        "repo": "test-repo",
        "issue": {
            "number": 123,
            "title": "Test issue",
            "body": "Test issue body",
            "state": "open",
            "labels": [
                {
                    "name": "bug",
                    "color": "d73a4a",
                    "description": "Something isn't working",
                },
                {
                    "name": "product::kots",
                    "color": "0052cc",
                    "description": "KOTS related",
                },
            ],
            "user": {"login": "testuser", "id": 1},
            "comments": [],
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        },
        "metadata": {},
    }

    # Sample AI result data
    ai_result_data = {
        "confidence": 0.9,
        "recommended_labels": [
            {
                "label": "product::vendor",
                "confidence": 0.85,
                "reasoning": "Issue is about vendor portal functionality",
            }
        ],
        "current_labels_assessment": [
            {
                "label": "bug",
                "correct": True,
                "reasoning": "This is indeed a bug report",
            },
            {
                "label": "product::kots",
                "correct": False,
                "reasoning": "Issue is not KOTS-related",
            },
        ],
        "summary": "Issue about vendor portal",
        "reasoning": "Based on analysis of the issue content",
        "images_analyzed": [],
        "image_impact": "",
    }

    # Write test files using flat structure
    (issues_dir / "test-org_test-repo_issue_123.json").write_text(json.dumps(issue_data))
    (results_dir / "test-org_test-repo_issue_123_product-labeling.json").write_text(
        json.dumps(ai_result_data)
    )

    return temp_data_dir


class TestUpdateLabelsCommand:
    """Test the update-labels CLI command."""

    def test_update_labels_missing_org(self) -> None:
        """Test that command fails when --org is missing."""
        result = runner.invoke(app, ["update-labels"])
        assert result.exit_code == 1
        assert "Error: --org is required" in result.stdout

    def test_update_labels_repo_without_org(self) -> None:
        """Test that command fails when --repo is provided without --org."""
        result = runner.invoke(app, ["update-labels", "--repo", "test-repo"])
        assert result.exit_code == 1
        assert "Error: --org is required when --repo is specified" in result.stdout

    def test_update_labels_issue_number_without_repo(self) -> None:
        """Test that command fails when --issue-number is provided without --repo."""
        result = runner.invoke(
            app, ["update-labels", "--org", "test-org", "--issue-number", "123"]
        )
        assert result.exit_code == 1
        assert (
            "Error: --org and --repo are required when --issue-number is specified"
            in result.stdout
        )

    def test_update_labels_missing_data_dir(self) -> None:
        """Test that command fails when data directory doesn't exist."""
        result = runner.invoke(
            app,
            ["update-labels", "--org", "test-org", "--data-dir", "/nonexistent/path"],
        )
        assert result.exit_code == 1
        assert "Error: Data directory" in result.stdout

    def test_update_labels_no_matching_files(self, sample_data_dir: Path) -> None:
        """Test when no matching files are found."""
        result = runner.invoke(
            app,
            [
                "update-labels",
                "--org",
                "nonexistent-org",
                "--data-dir",
                str(sample_data_dir),
            ],
        )
        assert result.exit_code == 1
        assert "No matching issue/result files found" in result.stdout

    def test_update_labels_dry_run(self, sample_data_dir: Path) -> None:
        """Test dry run mode."""
        with patch.dict("os.environ", {"GITHUB_TOKEN": "fake-token"}):
            result = runner.invoke(
                app,
                [
                    "update-labels",
                    "--org",
                    "test-org",
                    "--repo",
                    "test-repo",
                    "--dry-run",
                    "--data-dir",
                    str(sample_data_dir),
                ],
            )

        assert result.exit_code == 0
        assert "Planned Changes:" in result.stdout
        assert "Issue #123" in result.stdout
        assert "Add:" in result.stdout
        assert "product::vendor" in result.stdout
        # Check that the enhanced dry run format includes reasoning and comment preview
        # Note: text may be split across lines due to formatting
        assert "Issue is about vendor portal" in result.stdout
        assert "functionality" in result.stdout
        assert "**GitHub Comment Preview:**" in result.stdout
        assert "🤖 **AI Label Update**" in result.stdout

    @patch.dict("os.environ", {"GITHUB_TOKEN": "fake-token"})
    def test_update_labels_force_mode(
        self, sample_data_dir: Path, mock_github_client: MagicMock
    ) -> None:
        """Test force mode."""
        with patch(
            "github_issue_analysis.cli.update.ChangeDetector"
        ) as mock_detector_class:
            # Mock detector
            mock_detector = MagicMock()
            mock_detector_class.return_value = mock_detector

            # Mock finding files
            mock_detector.find_matching_files.return_value = [
                (
                    sample_data_dir
                    / "issues"
                    / "test-org"
                    / "test-repo"
                    / "issue-123.json",
                    sample_data_dir
                    / "results"
                    / "test-org"
                    / "test-repo"
                    / "issue-123-product-labeling.json",
                )
            ]

            # Mock load and detect
            mock_plan = IssueUpdatePlan(
                org="test-org",
                repo="test-repo",
                issue_number=123,
                changes=[
                    LabelChange(
                        "add", "product::vendor", "Test reason", 0.5
                    )  # Low confidence
                ],
                overall_confidence=0.5,
                needs_update=True,
                comment_summary="Test summary",
            )
            mock_detector.load_and_detect_for_file.return_value = mock_plan

            result = runner.invoke(
                app,
                [
                    "update-labels",
                    "--org",
                    "test-org",
                    "--repo",
                    "test-repo",
                    "--force",
                    "--data-dir",
                    str(sample_data_dir),
                ],
                input="y\n",
            )

        assert result.exit_code == 0
        assert "Force mode enabled" in result.stdout

    @patch.dict("os.environ", {"GITHUB_TOKEN": "fake-token"})
    def test_update_labels_no_changes_needed(self, sample_data_dir: Path) -> None:
        """Test when no changes are needed."""
        with patch(
            "github_issue_analysis.cli.update.ChangeDetector"
        ) as mock_detector_class:
            # Mock detector that finds no changes
            mock_detector = MagicMock()
            mock_detector_class.return_value = mock_detector

            mock_detector.find_matching_files.return_value = [
                (
                    sample_data_dir
                    / "issues"
                    / "test-org"
                    / "test-repo"
                    / "issue-123.json",
                    sample_data_dir
                    / "results"
                    / "test-org"
                    / "test-repo"
                    / "issue-123-product-labeling.json",
                )
            ]
            mock_detector.load_and_detect_for_file.return_value = None  # No changes

            result = runner.invoke(
                app,
                [
                    "update-labels",
                    "--org",
                    "test-org",
                    "--repo",
                    "test-repo",
                    "--data-dir",
                    str(sample_data_dir),
                ],
            )

        assert result.exit_code == 0
        assert "No label changes needed" in result.stdout

    @patch.dict("os.environ", {"GITHUB_TOKEN": "fake-token"})
    def test_update_labels_successful_execution(
        self, sample_data_dir: Path, mock_github_client: MagicMock
    ) -> None:
        """Test successful label update execution."""
        with patch(
            "github_issue_analysis.cli.update.ChangeDetector"
        ) as mock_detector_class:
            # Mock detector
            mock_detector = MagicMock()
            mock_detector_class.return_value = mock_detector

            mock_detector.find_matching_files.return_value = [
                (
                    sample_data_dir
                    / "issues"
                    / "test-org"
                    / "test-repo"
                    / "issue-123.json",
                    sample_data_dir
                    / "results"
                    / "test-org"
                    / "test-repo"
                    / "issue-123-product-labeling.json",
                )
            ]

            mock_plan = IssueUpdatePlan(
                org="test-org",
                repo="test-repo",
                issue_number=123,
                changes=[LabelChange("add", "product::vendor", "Test reason", 0.9)],
                overall_confidence=0.9,
                needs_update=True,
                comment_summary="Test summary",
            )
            mock_detector.load_and_detect_for_file.return_value = mock_plan

            result = runner.invoke(
                app,
                [
                    "update-labels",
                    "--org",
                    "test-org",
                    "--repo",
                    "test-repo",
                    "--issue-number",
                    "123",
                    "--data-dir",
                    str(sample_data_dir),
                ],
            )

        assert result.exit_code == 0
        assert "Processing issue #123" in result.stdout
        assert "Execution Summary:" in result.stdout

    def test_update_labels_custom_confidence(self, sample_data_dir: Path) -> None:
        """Test custom confidence threshold."""
        result = runner.invoke(
            app,
            [
                "update-labels",
                "--org",
                "test-org",
                "--repo",
                "test-repo",
                "--min-confidence",
                "0.95",
                "--dry-run",
                "--data-dir",
                str(sample_data_dir),
            ],
        )

        # Should not find any changes with very high confidence threshold
        assert "confidence threshold: 0.95" in result.stdout

    def test_update_labels_max_issues_limit(self, sample_data_dir: Path) -> None:
        """Test max issues limit."""
        with patch(
            "github_issue_analysis.cli.update.ChangeDetector"
        ) as mock_detector_class:
            mock_detector = MagicMock()
            mock_detector_class.return_value = mock_detector

            # Mock multiple plans
            mock_plans = [
                IssueUpdatePlan(
                    org="test-org",
                    repo="test-repo",
                    issue_number=i,
                    changes=[LabelChange("add", "test", "reason", 0.9)],
                    overall_confidence=0.9,
                    needs_update=True,
                    comment_summary="test",
                )
                for i in range(5)
            ]

            mock_detector.find_matching_files.return_value = [
                (Path("fake"), Path("fake"))
            ] * 5
            mock_detector.load_and_detect_for_file.return_value = mock_plans[0]

            result = runner.invoke(
                app,
                [
                    "update-labels",
                    "--org",
                    "test-org",
                    "--max-issues",
                    "2",
                    "--dry-run",
                    "--data-dir",
                    str(sample_data_dir),
                ],
            )

        assert "Limited to 2 issues as requested" in result.stdout

    def test_update_labels_skip_comments(self, sample_data_dir: Path) -> None:
        """Test skipping comments."""
        with patch.dict("os.environ", {"GITHUB_TOKEN": "fake-token"}):
            result = runner.invoke(
                app,
                [
                    "update-labels",
                    "--org",
                    "test-org",
                    "--repo",
                    "test-repo",
                    "--skip-comments",
                    "--dry-run",
                    "--data-dir",
                    str(sample_data_dir),
                ],
            )

        # Command should still work, just won't post comments
        assert result.exit_code == 0
