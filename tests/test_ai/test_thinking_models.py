"""Tests for thinking models configuration and functionality."""

from unittest.mock import patch

import pytest

from github_issue_analysis.ai.capabilities import (
    get_model_capabilities,
    get_models_with_capability,
    supports_thinking_budget,
    supports_thinking_effort,
    supports_thinking_summary,
    validate_thinking_configuration,
)
from github_issue_analysis.ai.config import (
    AIModelConfig,
    AISettings,
    ThinkingConfig,
    build_ai_config,
    build_provider_specific_settings,
)


class TestThinkingCapabilities:
    """Test thinking model capabilities and validation."""

    def test_get_model_capabilities(self) -> None:
        """Test getting capabilities for different models."""
        # OpenAI o1 models
        assert "thinking_effort" in get_model_capabilities("openai:o1-mini")
        assert "thinking_summary" in get_model_capabilities("openai:o1-mini")

        # Anthropic models
        anthropic_model = "anthropic:claude-3-5-sonnet-latest"
        assert "thinking_budget" in get_model_capabilities(anthropic_model)

        # Google models
        assert "thinking_budget" in get_model_capabilities("google:gemini-2.0-flash")

        # Unknown model
        assert get_model_capabilities("unknown:model") == set()

    def test_supports_thinking_effort(self) -> None:
        """Test thinking effort support detection."""
        assert supports_thinking_effort("openai:o1-mini") is True
        assert supports_thinking_effort("openai:o4-mini") is True
        assert supports_thinking_effort("openai:gpt-4o-mini") is False
        assert supports_thinking_effort("anthropic:claude-3-5-sonnet-latest") is False

    def test_supports_thinking_budget(self) -> None:
        """Test thinking budget support detection."""
        assert supports_thinking_budget("anthropic:claude-3-5-sonnet-latest") is True
        assert supports_thinking_budget("google:gemini-2.0-flash") is True
        assert supports_thinking_budget("openai:o1-mini") is False

    def test_supports_thinking_summary(self) -> None:
        """Test thinking summary support detection."""
        assert supports_thinking_summary("openai:o1-mini") is True
        assert supports_thinking_summary("openai:o1-preview") is True
        assert supports_thinking_summary("anthropic:claude-3-5-sonnet-latest") is False

    def test_get_models_with_capability(self) -> None:
        """Test getting models by capability."""
        effort_models = get_models_with_capability("thinking_effort")
        assert "openai:o1-mini" in effort_models
        assert "openai:o4-mini" in effort_models

        budget_models = get_models_with_capability("thinking_budget")
        assert "anthropic:claude-3-5-sonnet-latest" in budget_models
        assert "google:gemini-2.0-flash" in budget_models

    def test_validate_thinking_configuration_success(self) -> None:
        """Test successful thinking configuration validation."""
        # Valid OpenAI o1 configuration
        validate_thinking_configuration("openai:o1-mini", thinking_effort="high")

        # Valid Anthropic configuration
        anthropic_model = "anthropic:claude-3-5-sonnet-latest"
        validate_thinking_configuration(anthropic_model, thinking_budget=2048)

        # No thinking options provided (should pass)
        validate_thinking_configuration("openai:gpt-4o")

    def test_validate_thinking_configuration_invalid_model(self) -> None:
        """Test validation with model that doesn't support thinking."""
        with pytest.raises(ValueError) as exc_info:
            validate_thinking_configuration(
                "openai:gpt-3.5-turbo", thinking_effort="high"
            )

        assert "does not support thinking options" in str(exc_info.value)
        assert "💡 For thinking support, try these models:" in str(exc_info.value)

    def test_validate_thinking_configuration_invalid_option(self) -> None:
        """Test validation with invalid option for model."""
        with pytest.raises(ValueError) as exc_info:
            anthropic_model = "anthropic:claude-3-5-sonnet-latest"
            validate_thinking_configuration(anthropic_model, thinking_effort="high")

        assert "does not support --thinking-effort" in str(exc_info.value)

    def test_validate_thinking_configuration_invalid_effort_value(self) -> None:
        """Test validation with invalid effort value."""
        with pytest.raises(ValueError) as exc_info:
            validate_thinking_configuration("openai:o1-mini", thinking_effort="invalid")

        assert "Invalid thinking effort 'invalid'" in str(exc_info.value)

    def test_validate_thinking_configuration_invalid_budget_value(self) -> None:
        """Test validation with invalid budget value."""
        with pytest.raises(ValueError) as exc_info:
            anthropic_model = "anthropic:claude-3-5-sonnet-latest"
            validate_thinking_configuration(anthropic_model, thinking_budget=0)

        assert "Invalid thinking budget '0'" in str(exc_info.value)


class TestThinkingConfig:
    """Test ThinkingConfig model."""

    def test_thinking_config_creation(self) -> None:
        """Test creating ThinkingConfig with valid values."""
        config = ThinkingConfig(effort="high", budget_tokens=2048, summary="detailed")
        assert config.effort == "high"
        assert config.budget_tokens == 2048
        assert config.summary == "detailed"

    def test_thinking_config_invalid_budget(self) -> None:
        """Test ThinkingConfig with invalid budget."""
        with pytest.raises(ValueError):
            ThinkingConfig(effort=None, budget_tokens=0, summary=None)

    def test_thinking_config_partial(self) -> None:
        """Test ThinkingConfig with partial configuration."""
        config = ThinkingConfig(effort="medium", budget_tokens=None, summary=None)
        assert config.effort == "medium"
        assert config.budget_tokens is None
        assert config.summary is None


class TestAIModelConfig:
    """Test AIModelConfig with thinking support."""

    def test_ai_model_config_without_thinking(self) -> None:
        """Test AIModelConfig without thinking configuration."""
        config = AIModelConfig(
            model_name="openai:gpt-4o",
            thinking=None,
            temperature=None,
            include_images=True,
        )
        assert config.model_name == "openai:gpt-4o"
        assert config.thinking is None

    def test_ai_model_config_with_thinking(self) -> None:
        """Test AIModelConfig with valid thinking configuration."""
        thinking = ThinkingConfig(effort="high", budget_tokens=None, summary=None)
        config = AIModelConfig(
            model_name="openai:o1-mini",
            thinking=thinking,
            temperature=None,
            include_images=True,
        )
        assert config.model_name == "openai:o1-mini"
        assert config.thinking is not None
        assert config.thinking.effort == "high"

    def test_ai_model_config_validation_failure(self) -> None:
        """Test AIModelConfig validation with incompatible thinking."""
        thinking = ThinkingConfig(effort="high", budget_tokens=None, summary=None)
        with pytest.raises(ValueError):
            AIModelConfig(
                model_name="anthropic:claude-3-5-sonnet-latest",
                thinking=thinking,
                temperature=None,
                include_images=True,
            )


class TestAISettings:
    """Test AI settings with environment variables."""

    def test_ai_settings_defaults(self) -> None:
        """Test AI settings with default values."""
        settings = AISettings()
        assert settings.model == "openai:o4-mini"
        assert settings.thinking_effort is None
        assert settings.thinking_budget is None

    @patch.dict(
        "os.environ",
        {
            "AI_MODEL": "openai:o1-mini",
            "AI_THINKING_EFFORT": "high",
            "AI_THINKING_BUDGET": "2048",
        },
    )
    def test_ai_settings_from_env(self) -> None:
        """Test AI settings from environment variables."""
        settings = AISettings()
        assert settings.model == "openai:o1-mini"
        assert settings.thinking_effort == "high"
        assert settings.thinking_budget == 2048


class TestBuildAIConfig:
    """Test building AI configuration."""

    def test_build_ai_config_with_thinking(self) -> None:
        """Test building AI config with thinking options."""
        config = build_ai_config(
            model_name="openai:o1-mini", thinking_effort="high", thinking_budget=None
        )
        assert config.model_name == "openai:o1-mini"
        assert config.thinking is not None
        assert config.thinking.effort == "high"
        assert config.thinking.budget_tokens is None

    def test_build_ai_config_no_thinking(self) -> None:
        """Test building AI config without thinking options."""
        config = build_ai_config(model_name="openai:gpt-4o")
        assert config.model_name == "openai:gpt-4o"
        assert config.thinking is None

    @patch.dict("os.environ", {"AI_MODEL": "anthropic:claude-3-5-sonnet-latest"})
    def test_build_ai_config_from_env(self) -> None:
        """Test building AI config from environment."""
        config = build_ai_config()
        assert config.model_name == "anthropic:claude-3-5-sonnet-latest"


class TestProviderSpecificSettings:
    """Test provider-specific settings mapping."""

    def test_openai_provider_settings(self) -> None:
        """Test OpenAI provider-specific settings."""
        thinking = ThinkingConfig(effort="high", budget_tokens=None, summary="detailed")
        config = AIModelConfig(
            model_name="openai:o1-mini",
            thinking=thinking,
            temperature=0.7,
            include_images=True,
        )
        settings = build_provider_specific_settings(config)

        assert settings["reasoning_effort"] == "high"
        assert settings["reasoning_summary"] == "detailed"
        assert settings["temperature"] == 0.7

    def test_anthropic_provider_settings(self) -> None:
        """Test Anthropic provider-specific settings."""
        thinking = ThinkingConfig(effort=None, budget_tokens=2048, summary=None)
        config = AIModelConfig(
            model_name="anthropic:claude-3-5-sonnet-latest",
            thinking=thinking,
            temperature=0.5,
            include_images=True,
        )
        settings = build_provider_specific_settings(config)

        assert settings["thinking"]["type"] == "enabled"
        assert settings["thinking"]["budget_tokens"] == 2048
        assert settings["temperature"] == 0.5

    def test_google_provider_settings(self) -> None:
        """Test Google provider-specific settings."""
        thinking = ThinkingConfig(effort=None, budget_tokens=1024, summary=None)
        config = AIModelConfig(
            model_name="google:gemini-2.0-flash",
            thinking=thinking,
            temperature=None,
            include_images=True,
        )
        settings = build_provider_specific_settings(config)

        assert settings["thinking_config"]["thinking_budget"] == 1024

    def test_no_thinking_settings(self) -> None:
        """Test settings without thinking configuration."""
        config = AIModelConfig(
            model_name="openai:gpt-4o",
            thinking=None,
            temperature=0.8,
            include_images=True,
        )
        settings = build_provider_specific_settings(config)

        assert "reasoning_effort" not in settings
        assert "thinking" not in settings
        assert settings["temperature"] == 0.8

    def test_unknown_provider_settings(self) -> None:
        """Test settings for unknown provider."""
        config = AIModelConfig(
            model_name="unknown:model",
            thinking=None,
            temperature=0.3,
            include_images=True,
        )
        settings = build_provider_specific_settings(config)

        assert settings == {"temperature": 0.3}
