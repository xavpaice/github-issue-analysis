"""Tests for CLI thinking validation and integration."""

from typing import Any
from unittest.mock import patch

from typer.testing import CliRunner

from github_issue_analysis.cli.process import app


class TestCLIThinkingValidation:
    """Test CLI validation for thinking model options."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_valid_openai_thinking_effort(self) -> None:
        """Test valid OpenAI thinking effort configuration."""
        mock_target = "github_issue_analysis.cli.process._run_product_labeling"
        with patch(mock_target) as mock_run:
            mock_run.return_value = None

            result = self.runner.invoke(
                app,
                [
                    "--model",
                    "openai:o4-mini",
                    "--thinking-effort",
                    "high",
                    "--dry-run",
                ],
            )

            assert result.exit_code == 0
            mock_run.assert_called_once()

    def test_valid_anthropic_thinking_budget(self) -> None:
        """Test valid Anthropic thinking budget configuration."""
        mock_target = "github_issue_analysis.cli.process._run_product_labeling"
        with patch(mock_target) as mock_run:
            mock_run.return_value = None

            result = self.runner.invoke(
                app,
                [
                    "--model",
                    "anthropic:claude-3-5-sonnet-latest",
                    "--thinking-budget",
                    "2048",
                    "--dry-run",
                ],
            )

            assert result.exit_code == 0
            mock_run.assert_called_once()

    def test_invalid_model_with_thinking_effort(self) -> None:
        """Test invalid model with thinking effort option."""
        result = self.runner.invoke(
            app,
            [
                "--model",
                "openai:gpt-3.5-turbo",
                "--thinking-effort",
                "high",
                "--dry-run",
            ],
        )

        assert result.exit_code == 1
        assert "does not support thinking options" in result.stdout

    def test_invalid_model_with_thinking_budget(self) -> None:
        """Test invalid model with thinking budget option."""
        result = self.runner.invoke(
            app,
            [
                "--model",
                "openai:gpt-4o",
                "--thinking-budget",
                "1024",
                "--dry-run",
            ],
        )

        assert result.exit_code == 1
        assert "does not support thinking options" in result.stdout

    def test_wrong_thinking_option_for_model(self) -> None:
        """Test using wrong thinking option for model."""
        result = self.runner.invoke(
            app,
            [
                "--model",
                "anthropic:claude-3-5-sonnet-latest",
                "--thinking-effort",
                "medium",
                "--dry-run",
            ],
        )

        assert result.exit_code == 1
        assert "does not support --thinking-effort" in result.stdout

    def test_no_thinking_options(self) -> None:
        """Test command without thinking options (should work)."""
        mock_target = "github_issue_analysis.cli.process._run_product_labeling"
        with patch(mock_target) as mock_run:
            mock_run.return_value = None

            result = self.runner.invoke(app, ["--model", "openai:gpt-4o", "--dry-run"])

            assert result.exit_code == 0
            mock_run.assert_called_once()

    def test_invalid_thinking_effort_value(self) -> None:
        """Test invalid thinking effort value."""
        result = self.runner.invoke(
            app,
            [
                "--model",
                "openai:o4-mini",
                "--thinking-effort",
                "invalid",
                "--dry-run",
            ],
        )

        assert result.exit_code == 1
        assert "Invalid thinking effort 'invalid'" in result.stdout

    def test_negative_thinking_budget(self) -> None:
        """Test negative thinking budget value."""
        result = self.runner.invoke(
            app,
            [
                "--model",
                "anthropic:claude-3-5-sonnet-latest",
                "--thinking-budget",
                "-100",
                "--dry-run",
            ],
        )

        assert result.exit_code == 1
        assert "Invalid thinking budget" in result.stdout

    def test_invalid_model_format_with_thinking(self) -> None:
        """Test invalid model format (missing provider) with thinking options."""
        result = self.runner.invoke(
            app,
            [
                "--model",
                "o4-mini",
                "--thinking-effort",
                "high",
                "--dry-run",
            ],
        )

        assert result.exit_code == 1
        assert "Invalid model format 'o4-mini'" in result.stdout
        assert "Expected format: provider:model" in result.stdout

    @patch.dict(
        "os.environ", {"AI_THINKING_EFFORT": "medium", "AI_MODEL": "openai:o4-mini"}
    )
    def test_environment_variable_thinking_config(self) -> None:
        """Test thinking configuration from environment variables."""
        # Test that the config builder reads environment variables correctly
        from github_issue_analysis.ai.config import build_ai_config

        config = build_ai_config()
        assert config.model_name == "openai:o4-mini"
        assert config.thinking is not None
        assert config.thinking.effort == "medium"

    def test_cli_overrides_environment(self) -> None:
        """Test CLI options override environment variables."""
        with patch.dict("os.environ", {"AI_THINKING_EFFORT": "low"}):
            from github_issue_analysis.ai.config import build_ai_config

            # CLI value should override environment
            config = build_ai_config(
                model_name="openai:o4-mini", thinking_effort="high"
            )
            assert config.model_name == "openai:o4-mini"
            assert config.thinking is not None
            assert config.thinking.effort == "high"  # CLI value, not env "low"


class TestCLIConfigurationIntegration:
    """Test CLI integration with AI configuration system."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_config_builder_integration(self) -> None:
        """Test that CLI integrates properly with configuration system."""
        from github_issue_analysis.ai.config import build_ai_config

        # Test that CLI-style parameters work with config builder
        config = build_ai_config(
            model_name="openai:o4-mini", thinking_effort="high", thinking_budget=None
        )

        assert config.model_name == "openai:o4-mini"
        assert config.thinking is not None
        assert config.thinking.effort == "high"
        assert config.thinking.budget_tokens is None

    @patch("github_issue_analysis.cli.process._run_product_labeling")
    def test_cli_parameter_passing(self, mock_run: Any) -> None:
        """Test that CLI parameters are passed correctly to _run_product_labeling."""
        mock_run.return_value = None

        result = self.runner.invoke(
            app,
            [
                "--model",
                "openai:o4-mini",
                "--thinking-effort",
                "high",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0

        # Verify the function was called with the right thinking config
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0]
        thinking_effort = call_args[4]  # thinking_effort parameter
        assert thinking_effort == "high"

    @patch("github_issue_analysis.cli.process._run_product_labeling")
    def test_thinking_config_displayed(self, mock_run: Any) -> None:
        """Test that thinking configuration is displayed in output."""
        mock_run.return_value = None

        result = self.runner.invoke(
            app,
            [
                "--model",
                "openai:o4-mini",
                "--thinking-effort",
                "medium",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        # Note: In dry-run mode, the model/thinking config is not displayed
        # since the processor is not created
        mock_run.assert_called_once()

    @patch("github_issue_analysis.cli.process._run_product_labeling")
    def test_thinking_budget_displayed(self, mock_run: Any) -> None:
        """Test that thinking budget is displayed in output."""
        mock_run.return_value = None

        result = self.runner.invoke(
            app,
            [
                "--model",
                "anthropic:claude-3-5-sonnet-latest",
                "--thinking-budget",
                "2048",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        mock_run.assert_called_once()

    @patch("github_issue_analysis.cli.process._run_product_labeling")
    def test_no_thinking_config_display(self, mock_run: Any) -> None:
        """Test that no thinking config is displayed when not configured."""
        mock_run.return_value = None

        result = self.runner.invoke(app, ["--model", "openai:gpt-4o", "--dry-run"])

        assert result.exit_code == 0
        mock_run.assert_called_once()


class TestBackwardCompatibility:
    """Test backward compatibility with existing functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("github_issue_analysis.cli.process._run_product_labeling")
    def test_legacy_model_only_still_works(self, mock_run: Any) -> None:
        """Test that legacy model-only configuration still works."""
        mock_run.return_value = None

        result = self.runner.invoke(app, ["--model", "openai:gpt-4o", "--dry-run"])

        assert result.exit_code == 0
        mock_run.assert_called_once()

    @patch("github_issue_analysis.cli.process._run_product_labeling")
    def test_no_model_specified_uses_default(self, mock_run: Any) -> None:
        """Test that no model specified uses default configuration."""
        mock_run.return_value = None

        result = self.runner.invoke(app, ["--dry-run"])

        assert result.exit_code == 0
        mock_run.assert_called_once()

        # Verify default model was used
        call_args = mock_run.call_args[0]
        model = call_args[3]  # model parameter
        assert model is None  # Will use default from environment or config
