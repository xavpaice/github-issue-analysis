"""Tests for thinking models configuration and functionality."""

import pytest

from github_issue_analysis.ai.capabilities import (
    get_model_capabilities,
    get_models_with_capability,
    supports_thinking_budget,
    supports_thinking_effort,
    supports_thinking_summary,
    validate_thinking_configuration,
)

# Legacy configuration classes removed in simplification phase
# Testing now focuses on the simplified agent interface and capabilities


class TestThinkingCapabilities:
    """Test thinking model capabilities and validation."""

    def test_get_model_capabilities(self) -> None:
        """Test getting capabilities for different models."""
        # OpenAI reasoning models
        assert "thinking_effort" in get_model_capabilities("openai:o4-mini")
        assert "thinking_summary" in get_model_capabilities("openai:o4-mini")

        # Anthropic models
        assert "thinking_budget" in get_model_capabilities(
            "anthropic:claude-3-5-sonnet"
        )

        # Google models
        assert "thinking_budget" in get_model_capabilities("google:gemini-2.0-flash")

        # Regular models without thinking
        assert get_model_capabilities("openai:gpt-4o") == set()

    def test_supports_thinking_effort(self) -> None:
        """Test thinking effort support detection."""
        assert supports_thinking_effort("openai:o4-mini")
        assert supports_thinking_effort("openai:o1")
        assert not supports_thinking_effort("openai:gpt-4o")
        assert not supports_thinking_effort("anthropic:claude-3-5-sonnet")

    def test_supports_thinking_budget(self) -> None:
        """Test thinking budget support detection."""
        assert supports_thinking_budget("anthropic:claude-3-5-sonnet")
        assert supports_thinking_budget("google:gemini-2.0-flash")
        assert not supports_thinking_budget("openai:o4-mini")
        assert not supports_thinking_budget("openai:gpt-4o")

    def test_supports_thinking_summary(self) -> None:
        """Test thinking summary support detection."""
        assert supports_thinking_summary("openai:o4-mini")
        assert supports_thinking_summary("openai:o1")
        assert not supports_thinking_summary("anthropic:claude-3-5-sonnet")
        assert not supports_thinking_summary("openai:gpt-4o")

    def test_get_models_with_capability(self) -> None:
        """Test filtering models by capability."""
        thinking_effort_models = get_models_with_capability("thinking_effort")
        assert "openai:o4-mini" in thinking_effort_models
        assert "openai:o3" in thinking_effort_models
        assert "openai:gpt-4o" not in thinking_effort_models

        thinking_budget_models = get_models_with_capability("thinking_budget")
        assert "anthropic:claude-3-5-sonnet-latest" in thinking_budget_models
        assert "google:gemini-2.0-flash" in thinking_budget_models
        assert "openai:o4-mini" not in thinking_budget_models


class TestThinkingValidation:
    """Test thinking configuration validation."""

    def test_validate_thinking_configuration_success(self) -> None:
        """Test successful thinking configuration validation."""
        # OpenAI with effort
        validate_thinking_configuration("openai:o4-mini", thinking_effort="high")
        validate_thinking_configuration("openai:o1", thinking_effort="medium")

        # Anthropic with budget
        validate_thinking_configuration(
            "anthropic:claude-3-5-sonnet", thinking_budget=5000
        )

        # Google with budget
        validate_thinking_configuration("google:gemini-2.0-flash", thinking_budget=8000)

        # No thinking config (always valid)
        validate_thinking_configuration("openai:gpt-4o")

    def test_validate_thinking_configuration_invalid_model(self) -> None:
        """Test validation with invalid model format."""
        with pytest.raises(ValueError, match="Invalid model format"):
            validate_thinking_configuration("invalid-model")

    def test_validate_thinking_configuration_unsupported_effort(self) -> None:
        """Test validation with unsupported thinking effort."""
        with pytest.raises(ValueError, match="does not support --thinking-effort"):
            validate_thinking_configuration(
                "anthropic:claude-3-5-sonnet", thinking_effort="high"
            )

        with pytest.raises(ValueError, match="does not support thinking options"):
            validate_thinking_configuration("openai:gpt-4o", thinking_effort="medium")

    def test_validate_thinking_configuration_unsupported_budget(self) -> None:
        """Test validation with unsupported thinking budget."""
        with pytest.raises(ValueError, match="does not support --thinking-budget"):
            validate_thinking_configuration("openai:o4-mini", thinking_budget=5000)

        with pytest.raises(ValueError, match="does not support thinking options"):
            validate_thinking_configuration("openai:gpt-4o", thinking_budget=3000)

    def test_validate_thinking_configuration_invalid_effort(self) -> None:
        """Test validation with invalid effort values."""
        with pytest.raises(ValueError, match="Invalid thinking effort"):
            validate_thinking_configuration("openai:o4-mini", thinking_effort="invalid")

    def test_validate_thinking_configuration_invalid_budget(self) -> None:
        """Test validation with invalid budget values."""
        with pytest.raises(ValueError, match="Invalid thinking budget"):
            validate_thinking_configuration(
                "anthropic:claude-3-5-sonnet", thinking_budget=0
            )

        with pytest.raises(ValueError, match="Invalid thinking budget"):
            validate_thinking_configuration(
                "anthropic:claude-3-5-sonnet", thinking_budget=-100
            )

    def test_validate_thinking_configuration_mixed_valid(self) -> None:
        """Test validation with mixed parameters - should fail with unsupported."""
        # Should fail because o4-mini doesn't support budget
        with pytest.raises(ValueError, match="does not support --thinking-budget"):
            validate_thinking_configuration(
                "openai:o4-mini", thinking_effort="high", thinking_budget=5000
            )

        # Should fail because claude doesn't support effort
        with pytest.raises(ValueError, match="does not support --thinking-effort"):
            validate_thinking_configuration(
                "anthropic:claude-3-5-sonnet-latest",
                thinking_effort="high",
                thinking_budget=5000,
            )
