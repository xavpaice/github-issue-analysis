"""AI processing module for GitHub issue analysis."""

from .agents import create_product_labeling_agent
from .config import supports_thinking, validate_model_string
from .models import (
    IssueClassificationResponse,
    LabelAssessment,
    ProductLabel,
    ProductLabelingResponse,
    RecommendedLabel,
)
from .processors import ProductLabelingProcessor
from .prompts import build_product_labeling_prompt

__all__ = [
    "ProductLabel",
    "RecommendedLabel",
    "LabelAssessment",
    "ProductLabelingResponse",
    "IssueClassificationResponse",
    "ProductLabelingProcessor",
    "build_product_labeling_prompt",
    "create_product_labeling_agent",
    "validate_model_string",
    "supports_thinking",
]
