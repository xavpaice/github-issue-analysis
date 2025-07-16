"""Tests for AI processors."""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

# Legacy config classes removed in simplification phase
from github_issue_analysis.ai.models import (
    LabelAssessment,
    ProductLabel,
    ProductLabelingResponse,
    RecommendedLabel,
)
from github_issue_analysis.ai.processors import ProductLabelingProcessor


@pytest.fixture
def sample_issue_data() -> dict[str, Any]:
    """Sample issue data for testing."""
    return {
        "org": "test-org",
        "repo": "test-repo",
        "issue": {
            "number": 1,
            "title": "KOTS admin console not loading",
            "body": "The kotsadm interface shows a blank screen after login",
            "labels": [{"name": "bug"}, {"name": "product::kots"}],
            "comments": [],
        },
    }


@pytest.fixture
def sample_kots_response() -> ProductLabelingResponse:
    """Sample ProductLabelingResponse for KOTS issue."""
    return ProductLabelingResponse(
        recommendation_confidence=0.9,
        recommended_labels=[
            RecommendedLabel(
                label=ProductLabel.KOTS,
                reasoning="Issue clearly mentions kotsadm admin interface",
            )
        ],
        current_labels_assessment=[
            LabelAssessment(
                label="bug", correct=True, reasoning="This is indeed a bug report"
            )
        ],
        summary="KOTS admin console loading issue",
        reasoning="The issue mentions kotsadm interface problems, "
        "which is the KOTS admin console",
    )


@pytest.mark.asyncio
async def test_product_labeling_basic(
    sample_issue_data: dict[str, Any], sample_kots_response: ProductLabelingResponse
) -> None:
    """Test basic product labeling functionality."""
    processor = ProductLabelingProcessor(model_name="openai:gpt-4o-mini")

    # Mock the agent property to avoid OpenAI client initialization
    mock_agent = AsyncMock()
    mock_agent.run.return_value.data = sample_kots_response

    with patch.object(
        ProductLabelingProcessor, "agent", new_callable=lambda: mock_agent
    ):
        result = await processor.analyze_issue(sample_issue_data)

        # Verify the response structure
        assert isinstance(result, ProductLabelingResponse)
        assert result.recommendation_confidence == 0.9
        assert len(result.recommended_labels) == 1
        assert result.recommended_labels[0].label == ProductLabel.KOTS
        assert "kotsadm" in result.recommended_labels[0].reasoning.lower()


@pytest.mark.asyncio
async def test_multiple_product_labels() -> None:
    """Test that AI can recommend multiple specific product labels."""
    processor = ProductLabelingProcessor()

    # Mock response for issue affecting both KOTS and embedded-cluster
    mock_response = ProductLabelingResponse(
        recommendation_confidence=0.85,
        recommended_labels=[
            RecommendedLabel(
                label=ProductLabel.EMBEDDED_CLUSTER,
                reasoning="Issue involves cluster installation and k0s setup",
            ),
            RecommendedLabel(
                label=ProductLabel.KOTS,
                reasoning="Issue also affects KOTS installation within the cluster",
            ),
        ],
        current_labels_assessment=[],
        summary="Installation issue affecting both embedded cluster setup "
        "and KOTS deployment",
        reasoning="This issue involves both cluster installation "
        "(embedded-cluster product) and KOTS deployment within that cluster "
        "(kots product). Both teams need to coordinate on the fix.",
    )

    sample_data = {
        "org": "test",
        "repo": "test",
        "issue": {
            "number": 1,
            "title": "embedded-cluster install fails to deploy KOTS",
            "body": "When running embedded-cluster install, the k0s cluster "
            "starts but KOTS fails to deploy",
            "labels": [],
            "comments": [],
        },
    }

    # Mock the agent property to avoid OpenAI client initialization
    mock_agent = AsyncMock()
    mock_agent.run.return_value.data = mock_response

    with patch.object(
        ProductLabelingProcessor, "agent", new_callable=lambda: mock_agent
    ):
        result = await processor.analyze_issue(sample_data)

        # Verify multiple specific labels recommended
        assert len(result.recommended_labels) == 2
        labels = [r.label for r in result.recommended_labels]
        assert ProductLabel.EMBEDDED_CLUSTER in labels
        assert ProductLabel.KOTS in labels
        assert "both" in result.reasoning.lower()


@pytest.mark.asyncio
async def test_processor_model_configuration() -> None:
    """Test processor model configuration."""
    # Test default model
    processor1 = ProductLabelingProcessor()
    assert processor1.model_name == "openai:o4-mini"

    # Test custom model
    processor2 = ProductLabelingProcessor(model_name="anthropic:claude-3-5-sonnet")
    assert processor2.model_name == "anthropic:claude-3-5-sonnet"


def test_format_issue_prompt(sample_issue_data: dict[str, Any]) -> None:
    """Test issue prompt formatting."""
    processor = ProductLabelingProcessor()
    prompt = processor._format_issue_prompt(sample_issue_data)

    # Verify prompt contains expected components
    assert "KOTS admin console not loading" in prompt
    assert "kotsadm interface shows a blank screen" in prompt
    assert "test-org/test-repo" in prompt
    assert "product::kots" in prompt
    assert "bug" not in prompt  # Non-product labels should be filtered out
    assert "No comments" in prompt


def test_format_issue_prompt_with_comments() -> None:
    """Test issue prompt formatting with comments."""
    processor = ProductLabelingProcessor()

    issue_data_with_comments = {
        "org": "test-org",
        "repo": "test-repo",
        "issue": {
            "number": 1,
            "title": "Test issue",
            "body": "Test body",
            "labels": [],
            "comments": [
                {
                    "user": {"login": "user1"},
                    "body": "This is a test comment with some details about the issue",
                },
                {
                    "user": {"login": "user2"},
                    "body": "Another comment with more information",
                },
            ],
        },
    }

    prompt = processor._format_issue_prompt(issue_data_with_comments)

    # Verify comments are included in prompt
    assert "user1: This is a test comment" in prompt
    assert "user2: Another comment" in prompt


# Legacy integration tests removed - these tested the old complex configuration system
# that has been simplified. The new agent interface is tested in test_agents.py
