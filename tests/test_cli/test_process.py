"""Test CLI process commands with new agent interface."""

import pytest
from typer.testing import CliRunner

from github_issue_analysis.cli.process import app


class TestProductLabelingBasic:
    """Basic tests for product-labeling CLI command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Provide CLI test runner."""
        return CliRunner()

    def test_help_display(self, runner: CliRunner) -> None:
        """Test that help displays correctly."""
        result = runner.invoke(app, ["product-labeling", "--help"])
        assert result.exit_code == 0
        assert "AI Configuration" in result.stdout
        assert "Target Selection" in result.stdout
        assert "Processing Options" in result.stdout

    def test_command_requires_org(self, runner: CliRunner) -> None:
        """Test that org parameter is required."""
        result = runner.invoke(app, ["product-labeling"])
        # Should fail because --org is required
        assert result.exit_code == 2  # Typer validation error
        assert "Missing option '--org'" in result.stderr
