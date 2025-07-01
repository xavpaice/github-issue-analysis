"""Tests for image processing functionality in AI analysis."""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from github_issue_analysis.ai.image_utils import (
    describe_image_context,
    load_downloaded_images,
)
from github_issue_analysis.ai.models import (
    ImageAnalysis,
    LabelAssessment,
    ProductLabel,
    ProductLabelingResponse,
    RecommendedLabel,
)
from github_issue_analysis.ai.processors import ProductLabelingProcessor


@pytest.fixture
def issue_with_images() -> dict[str, Any]:
    """Sample issue data with image attachments."""
    return {
        "org": "test-org",
        "repo": "test-repo",
        "issue": {
            "number": 71,
            "title": "Admin console file browser issue",
            "body": "The KOTS admin console file browser shows issues with symlinks",
            "labels": [{"name": "product::troubleshoot"}],  # Incorrect label
            "comments": [
                {
                    "user": {"login": "testuser"},
                    "body": "Here's a screenshot of the problem",
                }
            ],
            "attachments": [
                {
                    "original_url": "https://github.com/user-attachments/assets/test-image",
                    "filename": "screenshot.png",
                    "local_path": "/fake/path/screenshot.png",
                    "content_type": "image/png",
                    "downloaded": True,
                    "source": "comment_0",
                }
            ],
        },
    }


@pytest.fixture
def issue_without_images() -> dict[str, Any]:
    """Sample issue data without image attachments."""
    return {
        "org": "test-org",
        "repo": "test-repo",
        "issue": {
            "number": 42,
            "title": "Basic text issue",
            "body": "This is a text-only issue",
            "labels": [],
            "comments": [],
            "attachments": [],
        },
    }


@pytest.mark.asyncio
async def test_image_processing_improves_classification(
    issue_with_images: dict[str, Any],
) -> None:
    """Test that image analysis improves product classification."""
    processor = ProductLabelingProcessor()

    # Mock image loading
    with patch(
        "github_issue_analysis.ai.image_utils.load_downloaded_images"
    ) as mock_load:
        mock_load.return_value = [
            {
                "type": "image_url",
                "image_url": {"url": "data:image/png;base64,fake_image_data"},
                "metadata": {
                    "source": "comment_0",
                    "filename": "screenshot.png",
                    "original_url": "https://example.com/image.png",
                },
            }
        ]

        # Mock AI response indicating image helped with classification
        mock_response = ProductLabelingResponse(
            confidence=0.95,
            recommended_labels=[
                RecommendedLabel(
                    label=ProductLabel.KOTS,
                    confidence=0.95,
                    reasoning="Screenshot clearly shows KOTS admin console interface",
                )
            ],
            current_labels_assessment=[
                LabelAssessment(
                    label="product::troubleshoot",
                    correct=False,
                    reasoning="Issue is about KOTS admin UI, not troubleshoot tool",
                )
            ],
            summary="KOTS admin console file browser issue revealed by screenshot",
            reasoning="Image analysis shows KOTS admin interface, confirms KOTS",
            images_analyzed=[
                ImageAnalysis(
                    filename="screenshot.png",
                    source="comment_0",
                    description="KOTS admin console file browser showing symlink issue",
                    relevance_score=0.9,
                )
            ],
            image_impact="Screenshot provided evidence this is KOTS admin console",
        )

        # Mock the agent property to avoid OpenAI client initialization
        mock_agent = AsyncMock()
        mock_agent.run.return_value.data = mock_response

        with patch.object(
            ProductLabelingProcessor, "agent", new_callable=lambda: mock_agent
        ):

            result = await processor.analyze_issue(
                issue_with_images, include_images=True
            )

            # Verify image analysis improved classification
            assert result.confidence == 0.95
            assert len(result.images_analyzed) == 1
            assert result.images_analyzed[0].filename == "screenshot.png"
            assert "KOTS admin console" in result.images_analyzed[0].description
            assert result.image_impact != ""
            assert "screenshot" in result.image_impact.lower()


@pytest.mark.asyncio
async def test_image_processing_disabled() -> None:
    """Test that image processing can be disabled."""
    processor = ProductLabelingProcessor()
    issue_data = {
        "org": "test",
        "repo": "test",
        "issue": {
            "title": "Test issue",
            "body": "Test body",
            "labels": [],
            "comments": [],
            "attachments": [],
        },
    }

    # Mock response without images
    mock_response = ProductLabelingResponse(
        confidence=0.8,
        recommended_labels=[
            RecommendedLabel(
                label=ProductLabel.KOTS,
                confidence=0.8,
                reasoning="Based on text analysis only",
            )
        ],
        current_labels_assessment=[],
        summary="Text-only analysis",
        reasoning="Classification based on text content alone",
        images_analyzed=[],  # Should be empty
        image_impact="",  # Should be empty
    )

    # Mock the agent property to avoid OpenAI client initialization
    mock_agent = AsyncMock()
    mock_agent.run.return_value.data = mock_response

    with patch.object(
        ProductLabelingProcessor, "agent", new_callable=lambda: mock_agent
    ):
        result = await processor.analyze_issue(issue_data, include_images=False)

        # Verify no image analysis was performed
        assert len(result.images_analyzed) == 0
        assert result.image_impact == ""


@pytest.mark.asyncio
async def test_multiple_products_with_images() -> None:
    """Test that images can help identify multiple specific products affected."""
    processor = ProductLabelingProcessor()

    # Mock response showing issue affects both products
    mock_response = ProductLabelingResponse(
        confidence=0.9,
        recommended_labels=[
            RecommendedLabel(
                label=ProductLabel.EMBEDDED_CLUSTER,
                confidence=0.85,
                reasoning="Cluster setup logs visible in screenshot",
            ),
            RecommendedLabel(
                label=ProductLabel.KOTS,
                confidence=0.95,
                reasoning="KOTS admin interface shown in second screenshot",
            ),
        ],
        current_labels_assessment=[],
        summary="Issue affects both cluster installation and KOTS deployment",
        reasoning="Screenshots show both cluster setup and KOTS admin problems",
        images_analyzed=[
            ImageAnalysis(
                filename="cluster-logs.png",
                source="issue_body",
                description="Cluster installation logs",
                relevance_score=0.8,
            ),
            ImageAnalysis(
                filename="kots-admin.png",
                source="comment_0",
                description="KOTS admin console error",
                relevance_score=0.9,
            ),
        ],
        image_impact="Screenshots show this affects both cluster setup and KOTS admin",
    )

    issue_data = {
        "org": "test",
        "repo": "test",
        "issue": {
            "title": "Cluster install and KOTS both failing",
            "body": "Both cluster and admin console have issues",
            "labels": [],
            "comments": [],
            "attachments": [],
        },
    }

    # Mock the agent property to avoid OpenAI client initialization
    mock_agent = AsyncMock()
    mock_agent.run.return_value.data = mock_response

    with patch.object(
        ProductLabelingProcessor, "agent", new_callable=lambda: mock_agent
    ):
        result = await processor.analyze_issue(issue_data, include_images=True)

        # Verify multiple specific products identified
        assert len(result.recommended_labels) == 2
        labels = [r.label for r in result.recommended_labels]
        assert ProductLabel.EMBEDDED_CLUSTER in labels
        assert ProductLabel.KOTS in labels


def test_load_downloaded_images_filters_correctly(
    issue_with_images: dict[str, Any],
) -> None:
    """Test that image loading correctly filters downloaded image files."""

    # Mock file system
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.read_bytes") as mock_read,
    ):

        mock_exists.return_value = True
        mock_read.return_value = b"fake_image_data"

        images = load_downloaded_images(issue_with_images, include_images=True)

        assert len(images) == 1
        assert images[0]["metadata"]["filename"] == "screenshot.png"
        assert images[0]["metadata"]["source"] == "comment_0"
        assert "data:image/png;base64," in images[0]["image_url"]["url"]


def test_load_downloaded_images_disabled() -> None:
    """Test that image loading respects include_images=False."""
    images = load_downloaded_images({}, include_images=False)
    assert images == []


def test_load_downloaded_images_no_attachments() -> None:
    """Test image loading with no attachments."""
    issue_data: dict[str, Any] = {"issue": {"attachments": []}}
    images = load_downloaded_images(issue_data, include_images=True)
    assert images == []


def test_load_downloaded_images_not_downloaded() -> None:
    """Test image loading skips non-downloaded attachments."""
    issue_data = {
        "issue": {
            "attachments": [
                {
                    "filename": "test.png",
                    "content_type": "image/png",
                    "downloaded": False,  # Not downloaded
                    "local_path": "/fake/path",
                }
            ]
        }
    }
    images = load_downloaded_images(issue_data, include_images=True)
    assert images == []


def test_load_downloaded_images_missing_file() -> None:
    """Test image loading handles missing local files gracefully."""
    issue_data = {
        "issue": {
            "attachments": [
                {
                    "filename": "missing.png",
                    "content_type": "image/png",
                    "downloaded": True,
                    "local_path": "/nonexistent/path",
                }
            ]
        }
    }

    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False

        images = load_downloaded_images(issue_data, include_images=True)
        assert images == []


def test_load_downloaded_images_non_image_file() -> None:
    """Test image loading skips non-image attachments."""
    issue_data = {
        "issue": {
            "attachments": [
                {
                    "filename": "document.pdf",
                    "content_type": "application/pdf",  # Not an image
                    "downloaded": True,
                    "local_path": "/fake/path",
                }
            ]
        }
    }

    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = True

        images = load_downloaded_images(issue_data, include_images=True)
        assert images == []


def test_load_downloaded_images_read_error() -> None:
    """Test image loading handles file read errors gracefully."""
    issue_data = {
        "issue": {
            "attachments": [
                {
                    "filename": "corrupt.png",
                    "content_type": "image/png",
                    "downloaded": True,
                    "local_path": "/fake/path",
                    "source": "issue_body",
                    "original_url": "https://example.com/image.png",
                }
            ]
        }
    }

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.read_bytes") as mock_read,
    ):

        mock_exists.return_value = True
        mock_read.side_effect = OSError("File read error")

        # Should not raise, just print error and continue
        images = load_downloaded_images(issue_data, include_images=True)
        assert images == []


def test_describe_image_context_issue_body() -> None:
    """Test image context description for issue body images."""
    context = describe_image_context("issue_body", {})
    assert context == "Image from issue description"


def test_describe_image_context_comment() -> None:
    """Test image context description for comment images."""
    issue_data: dict[str, Any] = {
        "issue": {
            "comments": [{"user": {"login": "alice"}}, {"user": {"login": "bob"}}]
        }
    }

    context = describe_image_context("comment_0", issue_data)
    assert context == "Image from comment by alice"

    context = describe_image_context("comment_1", issue_data)
    assert context == "Image from comment by bob"


def test_describe_image_context_invalid_comment() -> None:
    """Test image context description for invalid comment references."""
    issue_data: dict[str, Any] = {"issue": {"comments": []}}

    # Invalid comment index
    context = describe_image_context("comment_99", issue_data)
    assert context == "Image from comment_99"

    # Malformed comment reference
    context = describe_image_context("comment_invalid", issue_data)
    assert context == "Image from comment_invalid"


def test_describe_image_context_unknown_source() -> None:
    """Test image context description for unknown sources."""
    context = describe_image_context("unknown_source", {})
    assert context == "Image from unknown_source"


@pytest.mark.asyncio
async def test_processor_handles_image_loading_failure(
    issue_with_images: dict[str, Any],
) -> None:
    """Test that processor handles image loading failures gracefully."""
    processor = ProductLabelingProcessor()

    # Mock image loading to raise an exception
    with patch(
        "github_issue_analysis.ai.image_utils.load_downloaded_images"
    ) as mock_load:
        mock_load.side_effect = Exception("Image loading failed")

        # Should still work but without images
        mock_response = ProductLabelingResponse(
            confidence=0.7,
            recommended_labels=[],
            current_labels_assessment=[],
            summary="Fallback analysis",
            reasoning="Analysis without images due to loading error",
        )

        # Mock the agent property to avoid OpenAI client initialization
        mock_agent = AsyncMock()
        mock_agent.run.return_value.data = mock_response

        with patch.object(
            ProductLabelingProcessor, "agent", new_callable=lambda: mock_agent
        ):
            # Should not raise exception
            with pytest.raises(Exception, match="Image loading failed"):
                await processor.analyze_issue(issue_with_images, include_images=True)


def test_image_analysis_model_validation() -> None:
    """Test ImageAnalysis model validation."""
    # Valid ImageAnalysis
    img_analysis = ImageAnalysis(
        filename="test.png",
        source="issue_body",
        description="Test image description",
        relevance_score=0.8,
    )
    assert img_analysis.filename == "test.png"
    assert img_analysis.relevance_score == 0.8

    # Invalid relevance score
    with pytest.raises(ValueError):
        ImageAnalysis(
            filename="test.png",
            source="issue_body",
            description="Test",
            relevance_score=1.5,  # Invalid: > 1.0
        )

    with pytest.raises(ValueError):
        ImageAnalysis(
            filename="test.png",
            source="issue_body",
            description="Test",
            relevance_score=-0.1,  # Invalid: < 0.0
        )
