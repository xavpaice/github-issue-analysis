"""Simplified PydanticAI agent creation interface."""

from typing import Any

from pydantic_ai import Agent

from .models import ProductLabelingResponse
from .prompts import build_product_labeling_prompt


def create_product_labeling_agent(
    model: str,
    thinking_effort: str | None = None,
    thinking_budget: int | None = None,
    temperature: float = 0.0,
    retry_count: int = 2,
) -> Any:
    """Create a PydanticAI agent with user inputs - let PydanticAI handle validation.

    Args:
        model: Model identifier (e.g., 'openai:gpt-4o-mini')
        thinking_effort: Reasoning effort level for OpenAI models
        thinking_budget: Token budget for Anthropic/Google thinking models
        temperature: Model temperature (0.0-2.0)
        retry_count: Number of retries for failed requests

    Returns:
        Configured PydanticAI Agent for product labeling

    Raises:
        Any PydanticAI validation errors (passed through)
    """
    # Basic format check only
    if ":" not in model:
        raise ValueError(
            f"Invalid model format '{model}'. Expected format: provider:model"
        )

    # Create model settings - let PydanticAI validate everything
    settings: dict[str, Any] = {"temperature": temperature}
    provider = model.split(":")[0].lower()

    # Add thinking parameters based on provider
    if thinking_effort is not None and provider == "openai":
        settings["reasoning_effort"] = thinking_effort
    elif thinking_budget is not None and provider == "anthropic":
        settings["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
    elif thinking_budget is not None and provider == "google":
        settings["thinking_config"] = {"thinking_budget": thinking_budget}

    # Let PydanticAI handle all validation - pass through any errors
    return Agent(  # type: ignore
        model=model,
        model_settings=settings,
        output_type=ProductLabelingResponse,
        instructions=build_product_labeling_prompt(),
        retries=retry_count,
    )
