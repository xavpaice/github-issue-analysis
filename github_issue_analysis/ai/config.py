"""Enhanced AI configuration system with thinking model support."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

from .capabilities import validate_thinking_configuration


class ThinkingConfig(BaseModel):
    """Configuration for AI thinking models."""

    effort: Literal["low", "medium", "high"] | None = Field(
        None, description="Reasoning effort level for OpenAI o1 models"
    )
    budget_tokens: int | None = Field(
        None, description="Thinking token budget for Anthropic/Google models", gt=0
    )
    summary: Literal["brief", "detailed"] | None = Field(
        None, description="Summary detail level for thinking output"
    )

    @field_validator("budget_tokens")
    @classmethod
    def validate_budget_tokens(cls, v: int | None) -> int | None:
        """Validate thinking budget tokens."""
        if v is not None and v <= 0:
            raise ValueError("Thinking budget must be a positive integer")
        return v


class AIModelConfig(BaseModel):
    """Enhanced AI model configuration with thinking support."""

    model_name: str = Field(description="Model identifier (e.g., 'openai:gpt-4o-mini')")
    thinking: ThinkingConfig | None = Field(
        None, description="Thinking model configuration"
    )
    temperature: float | None = Field(
        None, description="Model temperature", ge=0.0, le=2.0
    )

    def model_post_init(self, __context: Any) -> None:
        """Validate configuration after initialization."""
        if self.thinking:
            # Extract thinking parameters for validation
            thinking_effort = self.thinking.effort
            thinking_budget = self.thinking.budget_tokens

            # Validate against model capabilities
            validate_thinking_configuration(
                model=self.model_name,
                thinking_effort=thinking_effort,
                thinking_budget=thinking_budget,
            )


class AISettings(BaseSettings):
    """Settings for AI configuration with environment variable support."""

    model: str = Field(
        default="openai:gpt-4o",
        description="Default AI model",
        validation_alias="AI_MODEL",
    )
    thinking_effort: Literal["low", "medium", "high"] | None = Field(
        default=None,
        description="Default thinking effort level",
        validation_alias="AI_THINKING_EFFORT",
    )
    thinking_budget: int | None = Field(
        default=None,
        description="Default thinking budget in tokens",
        validation_alias="AI_THINKING_BUDGET",
        gt=0,
    )
    thinking_summary: Literal["brief", "detailed"] | None = Field(
        default=None,
        description="Default thinking summary level",
        validation_alias="AI_THINKING_SUMMARY",
    )
    temperature: float | None = Field(
        default=None,
        description="Default model temperature",
        validation_alias="AI_TEMPERATURE",
        ge=0.0,
        le=2.0,
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def build_ai_config(
    model_name: str | None = None,
    thinking_effort: str | None = None,
    thinking_budget: int | None = None,
    thinking_summary: str | None = None,
    temperature: float | None = None,
    settings: AISettings | None = None,
) -> AIModelConfig:
    """Build AI configuration from CLI options and environment variables.

    Args:
        model_name: CLI-provided model name
        thinking_effort: CLI-provided thinking effort
        thinking_budget: CLI-provided thinking budget
        thinking_summary: CLI-provided thinking summary
        temperature: CLI-provided temperature
        settings: Pre-loaded settings (will load from env if None)

    Returns:
        Configured AIModelConfig instance
    """
    if settings is None:
        settings = AISettings()

    # Use CLI values or fall back to environment/defaults
    final_model = model_name or settings.model
    final_effort = thinking_effort or settings.thinking_effort
    final_budget = thinking_budget or settings.thinking_budget
    final_summary = thinking_summary or settings.thinking_summary
    final_temperature = temperature or settings.temperature

    # Build thinking config if any thinking options are provided
    thinking_config = None
    has_thinking_options = (
        final_effort is not None
        or final_budget is not None
        or final_summary is not None
    )
    if has_thinking_options:
        thinking_config = ThinkingConfig(
            effort=final_effort,  # type: ignore[arg-type]
            budget_tokens=final_budget,
            summary=final_summary,  # type: ignore[arg-type]
        )

    return AIModelConfig(
        model_name=final_model, thinking=thinking_config, temperature=final_temperature
    )


def build_provider_specific_settings(config: AIModelConfig) -> dict[str, Any]:
    """Map generic thinking config to provider-specific settings.

    Args:
        config: The AI model configuration

    Returns:
        Dictionary of provider-specific settings for PydanticAI
    """
    if not config.thinking:
        # Return base settings without thinking
        base_settings = {}
        if config.temperature is not None:
            base_settings["temperature"] = config.temperature
        return base_settings

    provider = config.model_name.split(":")[0].lower()

    settings: dict[str, Any] = {}

    if provider == "openai":
        # OpenAI o1 models use reasoning_effort and reasoning_summary
        if config.thinking.effort:
            settings["reasoning_effort"] = config.thinking.effort
        if config.thinking.summary:
            settings["reasoning_summary"] = config.thinking.summary
        if config.temperature is not None:
            settings["temperature"] = config.temperature
        return settings

    elif provider == "anthropic":
        # Anthropic uses thinking configuration with budget
        if config.thinking.budget_tokens:
            settings["thinking"] = {
                "type": "enabled",
                "budget_tokens": config.thinking.budget_tokens,
            }
        if config.temperature is not None:
            settings["temperature"] = config.temperature
        return settings

    elif provider == "google":
        # Google Gemini uses thinking_config with budget
        if config.thinking.budget_tokens:
            settings["thinking_config"] = {
                "thinking_budget": config.thinking.budget_tokens
            }
        if config.temperature is not None:
            settings["temperature"] = config.temperature
        return settings

    else:
        # Unknown provider, return base settings
        if config.temperature is not None:
            settings["temperature"] = config.temperature
        return settings
