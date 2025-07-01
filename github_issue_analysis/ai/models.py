"""Pydantic models for AI processing responses."""

from enum import Enum

from pydantic import BaseModel, Field


class ProductLabel(str, Enum):
    """Available product labels."""

    KOTS = "product::kots"
    TROUBLESHOOT = "product::troubleshoot"
    EMBEDDED_CLUSTER = "product::embedded-cluster"
    SDK = "product::sdk"
    DOCS = "product::docs"
    VENDOR = "product::vendor"
    DOWNLOADPORTAL = "product::downloadportal"
    COMPATIBILITY_MATRIX = "product::compatibility-matrix"
    # Special case
    UNKNOWN = "product::unknown"


class RecommendedLabel(BaseModel):
    """A recommended product label with confidence and reasoning."""

    label: ProductLabel
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    reasoning: str = Field(description="Explanation for this recommendation")


class LabelAssessment(BaseModel):
    """Assessment of an existing label."""

    label: str
    correct: bool = Field(description="Whether this label is correctly applied")
    reasoning: str = Field(description="Explanation of the assessment")


class ProductLabelingResponse(BaseModel):
    """Structured response for product labeling analysis."""

    confidence: float = Field(
        ge=0.0, le=1.0, description="Overall confidence in analysis"
    )
    recommended_labels: list[RecommendedLabel] = Field(
        description="Suggested product labels"
    )
    current_labels_assessment: list[LabelAssessment] = Field(
        description="Assessment of existing labels"
    )
    summary: str = Field(
        description="Brief summary of the issue's product classification"
    )
    reasoning: str = Field(description="Detailed reasoning for label recommendations")


# Future: Easy to add new response types for different analysis tasks
class IssueClassificationResponse(BaseModel):
    """Future: General issue classification beyond just product labels."""

    pass
