"""Pydantic models for AI processing responses."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ProductLabel(str, Enum):
    """Available product labels."""

    KOTS = "product::kots"
    TROUBLESHOOT = "product::troubleshoot"
    KURL = "product::kurl"
    EMBEDDED_CLUSTER = "product::embedded-cluster"
    SDK = "product::sdk"
    DOCS = "product::docs"
    VENDOR = "product::vendor"
    DOWNLOADPORTAL = "product::downloadportal"
    COMPATIBILITY_MATRIX = "product::compatibility-matrix"


class RecommendedLabel(BaseModel):
    """A recommended product label with reasoning (no individual confidence)."""

    label: ProductLabel
    reasoning: str = Field(description="Explanation for this recommendation")


class LabelAssessment(BaseModel):
    """Assessment of an existing label."""

    label: str
    correct: bool = Field(description="Whether this label is correctly applied")
    reasoning: str = Field(description="Explanation of the assessment")


class ImageAnalysis(BaseModel):
    """Analysis of an individual image."""

    filename: str
    source: str = Field(description="Source location: 'issue_body' or 'comment_{id}'")
    description: str = Field(
        description="What the image shows relevant to product classification"
    )
    relevance_score: float = Field(
        ge=0.0, le=1.0, description="How relevant this image is to classification"
    )


class ProductLabelingResponse(BaseModel):
    """Structured response for product labeling analysis."""

    root_cause_analysis: str = Field(
        default="Root cause unclear",
        description="Root cause analysis of the issue. "
        "State 'Root cause unclear' if unable to determine.",
    )
    root_cause_confidence: float | None = Field(
        default=None,
        description="Confidence in identified root cause (0-1). "
        "Only provide if a specific root cause is defined.",
    )
    recommendation_confidence: float = Field(
        description="Overall confidence in the complete label recommendation (0-1)"
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

    # Image-related fields for Phase 2
    images_analyzed: list[ImageAnalysis] = Field(
        default_factory=list,
        description="Analysis of images found in issue. "
        "MUST be empty if no images were provided.",
    )
    image_impact: str = Field(
        default="",
        description="How images influenced the classification decision. "
        "MUST be empty if no images were provided.",
    )

    @field_validator("images_analyzed")
    @classmethod
    def validate_images_analyzed(cls, v: list[ImageAnalysis]) -> list[ImageAnalysis]:
        """Validate that images_analyzed is only populated when images are present."""
        # Note: This validator will be enhanced with context in the processor
        return v

    @field_validator("image_impact")
    @classmethod
    def validate_image_impact(cls, v: str) -> str:
        """Validate that image_impact is only populated when images are present."""
        # Note: This validator will be enhanced with context in the processor
        return v


# Issue type classification models
class IssueType(str, Enum):
    """Available issue types for classification."""

    CUSTOMER_ENVIRONMENT = "customer-environment"
    USAGE_QUESTION = "usage-question"
    PRODUCT_BUG = "product-bug"
    HELM_CHART_FIX = "helm-chart-fix"


class IssueTypeResponse(BaseModel):
    """Structured response for issue type classification analysis."""

    issue_type: IssueType = Field(
        description="The primary classification of this issue"
    )
    root_cause_analysis: str = Field(
        description="Analysis of the root cause of the issue. "
        "State 'Root cause unclear' if unable to determine."
    )
    root_cause_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence in identified root cause (0-1). "
        "Only provide if a specific root cause is identified.",
    )
    classification_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall confidence in the issue type classification (0-1)"
    )
    reasoning: str = Field(
        description="Detailed reasoning for the issue type classification"
    )
    supporting_evidence: list[str] = Field(
        description="Key pieces of evidence that support the classification"
    )
    resolution_indicators: str = Field(
        description="How the issue was or should be resolved, if evident from the thread"
    )

    # Image-related fields for consistency with product labeling
    images_analyzed: list[ImageAnalysis] = Field(
        default_factory=list,
        description="Analysis of images found in issue. "
        "MUST be empty if no images were provided.",
    )
    image_impact: str = Field(
        default="",
        description="How images influenced the classification decision. "
        "MUST be empty if no images were provided.",
    )

    @field_validator("images_analyzed")
    @classmethod
    def validate_images_analyzed(cls, v: list[ImageAnalysis]) -> list[ImageAnalysis]:
        """Validate that images_analyzed is only populated when images are present."""
        return v

    @field_validator("image_impact")
    @classmethod
    def validate_image_impact(cls, v: str) -> str:
        """Validate that image_impact is only populated when images are present."""
        return v


# Legacy alias for backward compatibility
class IssueClassificationResponse(BaseModel):
    """Legacy alias - use IssueTypeResponse for new code."""

    pass
