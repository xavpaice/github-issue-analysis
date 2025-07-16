"""Model capability validation using PydanticAI.

This module uses PydanticAI's built-in model validation and settings
to determine valid model configurations.
"""

try:
    from pydantic_ai import Agent

    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    PYDANTIC_AI_AVAILABLE = False


def validate_model_with_thinking(
    model_name: str,
    thinking_effort: str | None = None,
    thinking_budget: int | None = None,
) -> None:
    """Validate model and thinking configuration using PydanticAI.

    Let PydanticAI handle all validation - just pass through any errors.

    Args:
        model_name: The model identifier (e.g., 'openai:gpt-4o-mini')
        thinking_effort: Effort level for reasoning models
        thinking_budget: Token budget for thinking models

    Raises:
        ValueError: If basic format is invalid
        Exception: Any PydanticAI validation errors (passed through)
    """
    if not PYDANTIC_AI_AVAILABLE:
        raise ValueError("PydanticAI is required for model validation")

    # Only validate basic format, let PydanticAI handle the rest
    if ":" not in model_name:
        raise ValueError(
            f"Invalid model format '{model_name}'. Expected format: provider:model"
        )

    # Create settings with thinking parameters if provided
    settings: dict[str, object] = {}
    provider = model_name.split(":")[0].lower()

    if thinking_effort is not None and provider == "openai":
        settings["reasoning_effort"] = thinking_effort
    elif thinking_budget is not None and provider == "anthropic":
        settings["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
    elif thinking_budget is not None and provider == "google":
        settings["thinking_config"] = {"thinking_budget": thinking_budget}

    # Let PydanticAI validate everything - don't intercept errors
    Agent(model=model_name, model_settings=settings if settings else None)  # type: ignore


# For backward compatibility, alias the new function
validate_thinking_configuration = validate_model_with_thinking


def supports_thinking_effort(model_name: str) -> bool:
    """Check if model supports thinking effort configuration using PydanticAI."""
    if not PYDANTIC_AI_AVAILABLE:
        return False
    try:
        validate_model_with_thinking(model_name, thinking_effort="medium")
        return True
    except ValueError:
        return False


def supports_thinking_budget(model_name: str) -> bool:
    """Check if model supports thinking budget configuration using PydanticAI."""
    if not PYDANTIC_AI_AVAILABLE:
        return False
    try:
        validate_model_with_thinking(model_name, thinking_budget=1000)
        return True
    except ValueError:
        return False


def supports_thinking_summary(model_name: str) -> bool:
    """Check if model supports thinking summary (same as effort) using PydanticAI."""
    return supports_thinking_effort(model_name)


def get_model_capabilities(model_name: str) -> set[str]:
    """Get model capabilities by testing with PydanticAI."""
    if not PYDANTIC_AI_AVAILABLE:
        return set()

    capabilities = set()
    if supports_thinking_effort(model_name):
        capabilities.add("thinking_effort")
        capabilities.add("thinking_summary")
    if supports_thinking_budget(model_name):
        capabilities.add("thinking_budget")

    return capabilities


def get_models_with_capability(capability: str) -> list[str]:
    """Get example models that support a specific capability."""
    # Return examples based on common patterns
    if capability == "thinking_effort":
        return ["openai:o4-mini", "openai:o3"]
    elif capability == "thinking_budget":
        return ["anthropic:claude-3-5-sonnet-latest", "google:gemini-2.0-flash"]
    elif capability == "thinking_summary":
        return ["openai:o4-mini"]
    elif capability == "thinking_format":
        return ["groq:qwen-qwq-32b"]
    else:
        return []
