"""Pydantic models for batch processing operations."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BatchJobStatus(str, Enum):
    """Status of a batch processing job."""

    PENDING = "pending"
    VALIDATING = "validating"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchJobError(BaseModel):
    """Error information for failed batch items."""

    custom_id: str = Field(description="Custom ID of the failed item")
    error_code: str = Field(description="Error code from the API")
    error_message: str = Field(description="Human-readable error message")


class BatchJob(BaseModel):
    """A batch processing job configuration."""

    job_id: str = Field(description="Unique identifier for the batch job")
    processor_type: str = Field(
        description="Type of processor (e.g., 'product-labeling')"
    )
    org: str = Field(description="GitHub organization name")
    repo: str | None = Field(None, description="GitHub repository name (optional)")
    issue_number: int | None = Field(
        None, description="Specific issue number (optional)"
    )
    ai_model_config: dict[str, Any] = Field(description="AI model configuration")

    # OpenAI Batch API fields
    openai_batch_id: str | None = Field(None, description="OpenAI batch ID")
    input_file_id: str | None = Field(None, description="OpenAI input file ID")
    output_file_id: str | None = Field(None, description="OpenAI output file ID")

    # Job metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: datetime | None = Field(
        None, description="When job was submitted to OpenAI"
    )
    completed_at: datetime | None = Field(None, description="When job completed")

    # Status and results
    status: BatchJobStatus = Field(default=BatchJobStatus.PENDING)
    total_items: int = Field(0, description="Total number of items in the batch")
    processed_items: int = Field(
        0, description="Number of successfully processed items"
    )
    failed_items: int = Field(0, description="Number of failed items")
    errors: list[BatchJobError] = Field(
        default_factory=list, description="Failed item errors"
    )

    # File paths
    input_file_path: str | None = Field(
        None, description="Local path to JSONL input file"
    )
    output_file_path: str | None = Field(
        None, description="Local path to downloaded output file"
    )


class BatchResult(BaseModel):
    """Results from a completed batch job."""

    job_id: str = Field(description="Batch job identifier")
    processor_type: str = Field(description="Type of processor used")
    total_items: int = Field(description="Total number of items processed")
    successful_items: int = Field(description="Number of successfully processed items")
    failed_items: int = Field(description="Number of failed items")
    cost_estimate: float | None = Field(None, description="Estimated cost in USD")
    processing_time: float | None = Field(
        None, description="Processing time in seconds"
    )
    results_directory: str = Field(description="Directory containing result files")
    errors: list[BatchJobError] = Field(
        default_factory=list, description="Failed item details"
    )


class BatchJobSummary(BaseModel):
    """Summary information for listing batch jobs."""

    job_id: str
    processor_type: str
    org: str
    repo: str | None
    issue_number: int | None
    status: BatchJobStatus
    created_at: datetime
    total_items: int
    processed_items: int
    failed_items: int
