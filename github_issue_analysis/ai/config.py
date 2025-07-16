"""Minimal AI configuration helpers."""

from typing import Any

from pydantic import BaseModel

from .capabilities import get_model_capabilities

# Thinking model constants
THINKING_MODELS = {
    "openai:o1",
    "openai:o1-mini",
    "anthropic:claude-3-5-sonnet",
}


def validate_model_string(model: str) -> tuple[str, str]:
    """Validate and parse model string format.

    Args:
        model: Model identifier (e.g., 'openai:gpt-4o-mini')

    Returns:
        Tuple of (provider, model_name)

    Raises:
        ValueError: If model string format is invalid
    """
    if ":" not in model:
        raise ValueError(
            f"Invalid model format '{model}'. Expected format: provider:model\n\n"
            f"💡 Examples of valid model formats:\n"
            f"   openai:o4-mini\n"
            f"   openai:gpt-4o-mini\n"
            f"   anthropic:claude-3-5-sonnet-latest\n"
            f"   google:gemini-2.0-flash"
        )

    parts = model.split(":", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"Invalid model format '{model}'. Both provider and model name must be "
            f"non-empty."
        )

    provider = parts[0].lower()
    model_name = parts[1]
    return provider, model_name


def supports_thinking(model: str) -> bool:
    """Check if model supports thinking/reasoning.

    Args:
        model: Model identifier (e.g., 'openai:o4-mini')

    Returns:
        True if model supports any thinking capabilities

    Raises:
        ValueError: If model string format is invalid
    """
    # Validate model format first
    validate_model_string(model)

    # Check if model has any thinking capabilities
    capabilities = get_model_capabilities(model)
    thinking_capabilities = {
        "thinking_effort",
        "thinking_budget",
        "thinking_summary",
        "thinking_format",
    }
    return bool(capabilities & thinking_capabilities)


# Minimal compatibility classes for batch system
class AIModelConfig(BaseModel):
    """Minimal compatibility class for batch system."""

    model: str = "openai:gpt-4o"
    model_name: str = "openai:gpt-4o"  # Alias for compatibility
    thinking_effort: str | None = None
    thinking_budget: int | None = None
    temperature: float = 0.0
    include_images: bool = True

    def __init__(self, **kwargs: Any) -> None:
        # Ensure model_name and model are synchronized
        if "model" in kwargs and "model_name" not in kwargs:
            kwargs["model_name"] = kwargs["model"]
        elif "model_name" in kwargs and "model" not in kwargs:
            kwargs["model"] = kwargs["model_name"]
        super().__init__(**kwargs)


def build_ai_config(
    model_name: str = "openai:gpt-4o",
    thinking_effort: str | None = None,
    thinking_budget: int | None = None,
    temperature: float = 0.0,
) -> AIModelConfig:
    """Minimal compatibility function for batch system."""
    return AIModelConfig(
        model=model_name,
        thinking_effort=thinking_effort,
        thinking_budget=thinking_budget,
        temperature=temperature,
    )


def build_provider_specific_settings(config: AIModelConfig) -> dict[str, Any]:
    """Minimal compatibility function for batch system."""
    settings: dict[str, Any] = {
        "temperature": config.temperature,
    }

    # Add thinking-related settings if available
    if config.thinking_effort and "o1" in config.model:
        settings["reasoning_effort"] = config.thinking_effort

    return settings
