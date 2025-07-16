"""Simplified PydanticAI agent creation interface."""

from typing import Any

from pydantic_ai import Agent

from .config import supports_thinking, validate_model_string
from .models import ProductLabelingResponse
from .prompts import build_product_labeling_prompt


def create_product_labeling_agent(
    model: str,
    thinking_effort: str | None = None,
    temperature: float = 0.0,
    retry_count: int = 2,
) -> Agent[None, ProductLabelingResponse]:
    """Create a PydanticAI agent with the specified configuration.

    Args:
        model: Model identifier (e.g., 'openai:gpt-4o-mini',
            'anthropic:claude-3-5-sonnet')
        thinking_effort: Reasoning effort level for thinking models
            ('low', 'medium', 'high')
        temperature: Model temperature (0.0-2.0)
        retry_count: Number of retries for failed requests

    Returns:
        Configured PydanticAI Agent for product labeling

    Raises:
        ValueError: If model string is invalid or configuration is incompatible
    """
    # Validate model format
    provider, model_name = validate_model_string(model)

    # Validate thinking configuration if provided
    if thinking_effort is not None:
        if not supports_thinking(model):
            raise ValueError(
                f"Model '{model}' does not support thinking/reasoning features"
            )
        if thinking_effort not in ("low", "medium", "high"):
            raise ValueError(
                f"Invalid thinking effort '{thinking_effort}'. "
                f"Must be 'low', 'medium', or 'high'"
            )

    # Validate temperature
    if not (0.0 <= temperature <= 2.0):
        raise ValueError(f"Temperature must be between 0.0 and 2.0, got {temperature}")

    # Build provider-specific model settings
    model_settings: dict[str, Any] = {}

    if thinking_effort is not None:
        if provider == "openai":
            # OpenAI o1 models use reasoning_effort
            model_settings["reasoning_effort"] = thinking_effort
        elif provider == "anthropic":
            # Anthropic uses thinking configuration with fixed budget
            model_settings["thinking"] = {
                "type": "enabled",
                "budget_tokens": 10000,  # Default budget for thinking
            }
        elif provider == "google":
            # Google Gemini uses thinking_config with budget
            model_settings["thinking_config"] = {
                "thinking_budget": 10000  # Default budget for thinking
            }

    # Always add temperature (including 0.0)
    model_settings["temperature"] = temperature

    # Create and return the PydanticAI agent
    return Agent(
        model=model,
        output_type=ProductLabelingResponse,
        system_prompt=build_product_labeling_prompt(),
        model_settings=model_settings if model_settings else None,  # type: ignore[arg-type]
        retries=retry_count,
    )
