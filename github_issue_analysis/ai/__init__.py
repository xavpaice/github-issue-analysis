"""AI processing module for GitHub issue analysis."""

from .models import (
    IssueClassificationResponse,
    LabelAssessment,
    ProductLabel,
    ProductLabelingResponse,
    RecommendedLabel,
)
from .processors import IssueClassificationProcessor, ProductLabelingProcessor
from .prompts import build_product_labeling_prompt

__all__ = [
    "ProductLabel",
    "RecommendedLabel",
    "LabelAssessment",
    "ProductLabelingResponse",
    "IssueClassificationResponse",
    "ProductLabelingProcessor",
    "IssueClassificationProcessor",
    "build_product_labeling_prompt",
]
