"""Model capability mapping for thinking features and validation.

This module provides smart validation using provider patterns and known model
families to determine which thinking features are supported by different AI models.
"""

try:
    # Test if PydanticAI is available for future extensibility
    import pydantic_ai  # noqa: F401

    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    PYDANTIC_AI_AVAILABLE = False


def get_model_capabilities(model_name: str) -> set[str]:
    """Get the thinking capabilities for a given model.

    Uses provider patterns and known model families to determine capabilities
    rather than trying to query PydanticAI directly, as the settings classes
    accept any model name without validation.

    Args:
        model_name: The model identifier (e.g., 'openai:gpt-4o-mini')

    Returns:
        Set of capability strings supported by the model
    """
    if not PYDANTIC_AI_AVAILABLE:
        return set()

    provider = model_name.split(":")[0].lower()
    model_part = model_name.split(":", 1)[1].lower() if ":" in model_name else ""
    capabilities = set()

    if provider == "openai":
        # Only specific OpenAI reasoning model families support thinking
        reasoning_families = ["o1", "o3", "o4"]
        if any(family in model_part for family in reasoning_families):
            capabilities.add("thinking_effort")
            capabilities.add("thinking_summary")

    elif provider == "anthropic":
        # Anthropic Claude models support thinking budget
        # Most modern Claude models support thinking
        if "claude" in model_part:
            capabilities.add("thinking_budget")

    elif provider == "google":
        # Google Gemini thinking models
        thinking_models = ["gemini-2.0-flash", "gemini-thinking"]
        if any(thinking_model in model_part for thinking_model in thinking_models):
            capabilities.add("thinking_budget")

    elif provider == "groq":
        # Groq reasoning models
        reasoning_models = ["qwen-qwq", "deepseek-r1"]
        if any(reasoning_model in model_part for reasoning_model in reasoning_models):
            capabilities.add("thinking_format")

    return capabilities


def supports_thinking_effort(model_name: str) -> bool:
    """Check if model supports thinking effort configuration.

    Args:
        model_name: The model identifier

    Returns:
        True if model supports thinking_effort parameter
    """
    return "thinking_effort" in get_model_capabilities(model_name)


def supports_thinking_budget(model_name: str) -> bool:
    """Check if model supports thinking budget configuration.

    Args:
        model_name: The model identifier

    Returns:
        True if model supports thinking_budget parameter
    """
    return "thinking_budget" in get_model_capabilities(model_name)


def supports_thinking_summary(model_name: str) -> bool:
    """Check if model supports thinking summary configuration.

    Args:
        model_name: The model identifier

    Returns:
        True if model supports thinking_summary parameter
    """
    return "thinking_summary" in get_model_capabilities(model_name)


def get_models_with_capability(capability: str) -> list[str]:
    """Get example models that support a specific capability.

    Args:
        capability: The capability to search for

    Returns:
        List of example model names that support the capability
    """
    # Return examples rather than trying to enumerate all models
    if capability == "thinking_effort":
        return ["openai:o1-mini", "openai:o4-mini", "openai:o3"]
    elif capability == "thinking_budget":
        return ["anthropic:claude-3-5-sonnet-latest", "google:gemini-2.0-flash"]
    elif capability == "thinking_summary":
        return ["openai:o1-mini", "openai:o4-mini"]
    elif capability == "thinking_format":
        return ["groq:qwen-qwq-32b"]
    else:
        return []


def validate_thinking_configuration(
    model: str, thinking_effort: str | None = None, thinking_budget: int | None = None
) -> None:
    """Validate thinking configuration against model capabilities.

    Args:
        model: The model identifier
        thinking_effort: Effort level for OpenAI o1 models
        thinking_budget: Token budget for Anthropic/Google models

    Raises:
        ValueError: If configuration is invalid for the model
    """
    capabilities = get_model_capabilities(model)

    # Check if any thinking options are provided
    if thinking_effort is None and thinking_budget is None:
        return  # No thinking options provided, nothing to validate

    # If no thinking capabilities, reject any thinking options
    if not capabilities:
        provided_options = []
        if thinking_effort is not None:
            provided_options.append("--thinking-effort")
        if thinking_budget is not None:
            provided_options.append("--thinking-budget")

        options_str = ", ".join(provided_options)
        raise ValueError(
            f"Model '{model}' does not support thinking options: {options_str}\n\n"
            f"💡 For thinking support, try these models:\n"
            f"   OpenAI o1 models: o1-mini, o1-preview\n"
            f"   Available options: --thinking-effort {{low,medium,high}}\n\n"
            f"   Anthropic models: claude-3-5-sonnet-latest\n"
            f"   Available options: --thinking-budget <tokens>\n\n"
            f"   Google models: gemini-2.0-flash\n"
            f"   Available options: --thinking-budget <tokens>"
        )

    # Validate specific options
    if thinking_effort is not None and not supports_thinking_effort(model):
        effort_models = get_models_with_capability("thinking_effort")
        raise ValueError(
            f"Model '{model}' does not support --thinking-effort\n\n"
            f"💡 Models that support --thinking-effort: {', '.join(effort_models)}"
        )

    if thinking_budget is not None and not supports_thinking_budget(model):
        budget_models = get_models_with_capability("thinking_budget")
        raise ValueError(
            f"Model '{model}' does not support --thinking-budget\n\n"
            f"💡 Models that support --thinking-budget: {', '.join(budget_models)}"
        )

    # Validate effort values
    if thinking_effort is not None and thinking_effort not in ["low", "medium", "high"]:
        raise ValueError(
            f"Invalid thinking effort '{thinking_effort}'. "
            f"Must be one of: low, medium, high"
        )

    # Validate budget values
    if thinking_budget is not None and thinking_budget <= 0:
        raise ValueError(
            f"Invalid thinking budget '{thinking_budget}'. "
            f"Must be a positive integer"
        )
