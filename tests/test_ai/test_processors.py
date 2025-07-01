"""Tests for AI processors."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from github_issue_analysis.ai.config import AIModelConfig, ThinkingConfig
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
        confidence=0.9,
        recommended_labels=[
            RecommendedLabel(
                label=ProductLabel.KOTS,
                confidence=0.9,
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
        assert result.confidence == 0.9
        assert len(result.recommended_labels) == 1
        assert result.recommended_labels[0].label == ProductLabel.KOTS
        assert result.recommended_labels[0].confidence == 0.9
        assert "kotsadm" in result.recommended_labels[0].reasoning.lower()


@pytest.mark.asyncio
async def test_multiple_product_labels() -> None:
    """Test that AI can recommend multiple specific product labels."""
    processor = ProductLabelingProcessor()

    # Mock response for issue affecting both KOTS and embedded-cluster
    mock_response = ProductLabelingResponse(
        confidence=0.85,
        recommended_labels=[
            RecommendedLabel(
                label=ProductLabel.EMBEDDED_CLUSTER,
                confidence=0.9,
                reasoning="Issue involves cluster installation and k0s setup",
            ),
            RecommendedLabel(
                label=ProductLabel.KOTS,
                confidence=0.8,
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
    assert processor1.model_name == "openai:gpt-4o"

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


class TestPydanticAIIntegration:
    """Test PydanticAI integration with thinking models."""

    @patch("github_issue_analysis.ai.processors.Agent")
    def test_agent_creation_with_thinking_config(
        self, mock_agent_class: MagicMock
    ) -> None:
        """Test Agent creation with correct model_settings for thinking models."""
        # Mock the Agent constructor
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        # Create thinking config
        thinking_config = ThinkingConfig(
            effort="high", budget_tokens=None, summary="detailed"
        )
        ai_config = AIModelConfig(
            model_name="openai:o1-mini", thinking=thinking_config, temperature=None
        )

        # Create processor with thinking config
        processor = ProductLabelingProcessor(config=ai_config)

        # Access agent property to trigger creation
        _ = processor.agent

        # Verify Agent was called with correct parameters
        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]

        assert call_kwargs["model"] == "openai:o1-mini"
        assert call_kwargs["output_type"] == ProductLabelingResponse
        assert "model_settings" in call_kwargs

        # Verify model_settings contains thinking parameters
        model_settings = call_kwargs["model_settings"]
        assert model_settings["reasoning_effort"] == "high"
        assert model_settings["reasoning_summary"] == "detailed"

    @patch("github_issue_analysis.ai.processors.Agent")
    def test_agent_creation_with_anthropic_thinking(
        self, mock_agent_class: MagicMock
    ) -> None:
        """Test Agent creation with Anthropic thinking budget."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        thinking_config = ThinkingConfig(effort=None, budget_tokens=2048, summary=None)
        ai_config = AIModelConfig(
            model_name="anthropic:claude-3-5-sonnet-latest",
            thinking=thinking_config,
            temperature=0.7,
        )

        processor = ProductLabelingProcessor(config=ai_config)
        _ = processor.agent

        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]

        assert call_kwargs["model"] == "anthropic:claude-3-5-sonnet-latest"

        model_settings = call_kwargs["model_settings"]
        assert model_settings["thinking"]["type"] == "enabled"
        assert model_settings["thinking"]["budget_tokens"] == 2048
        assert model_settings["temperature"] == 0.7

    @patch("github_issue_analysis.ai.processors.Agent")
    def test_agent_creation_without_thinking(self, mock_agent_class: MagicMock) -> None:
        """Test Agent creation without thinking configuration."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        ai_config = AIModelConfig(
            model_name="openai:gpt-4o", thinking=None, temperature=0.5
        )

        processor = ProductLabelingProcessor(config=ai_config)
        _ = processor.agent

        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]

        assert call_kwargs["model"] == "openai:gpt-4o"

        model_settings = call_kwargs["model_settings"]
        assert model_settings == {"temperature": 0.5}

    @patch("github_issue_analysis.ai.processors.Agent")
    def test_agent_creation_legacy_model_name(
        self, mock_agent_class: MagicMock
    ) -> None:
        """Test backward compatibility with legacy model_name parameter."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        # Use legacy constructor
        processor = ProductLabelingProcessor(model_name="openai:gpt-4o")
        _ = processor.agent

        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]

        assert call_kwargs["model"] == "openai:gpt-4o"
        assert call_kwargs["model_settings"] is None

    @patch("github_issue_analysis.ai.processors.Agent")
    def test_agent_caching(self, mock_agent_class: MagicMock) -> None:
        """Test that agent is created only once and cached."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        processor = ProductLabelingProcessor(model_name="openai:gpt-4o")

        # Access agent multiple times
        agent1 = processor.agent
        agent2 = processor.agent
        agent3 = processor.agent

        # Verify Agent constructor was called only once
        mock_agent_class.assert_called_once()

        # Verify all returns are the same instance
        assert agent1 is agent2 is agent3 is mock_agent_instance

    @pytest.mark.asyncio
    @patch("github_issue_analysis.ai.processors.Agent")
    async def test_analyze_with_thinking_model_real_flow(
        self, mock_agent_class: MagicMock, sample_issue_data: dict[str, Any]
    ) -> None:
        """Test the full analysis flow with thinking model (mocking only API calls)."""
        # Mock the Agent and its run method
        mock_agent_instance = AsyncMock()
        mock_agent_class.return_value = mock_agent_instance

        # Mock the agent.run response
        mock_response = MagicMock()
        mock_response.data = ProductLabelingResponse(
            confidence=0.95,
            recommended_labels=[
                RecommendedLabel(
                    label=ProductLabel.KOTS,
                    confidence=0.95,
                    reasoning="Issue involves KOTS admin console with thinking",
                )
            ],
            current_labels_assessment=[],
            summary="Thinking model analysis of KOTS issue",
            reasoning="Used high thinking effort to analyze the admin console issue",
        )
        mock_agent_instance.run.return_value = mock_response

        # Create processor with thinking config
        thinking_config = ThinkingConfig(
            effort="high", budget_tokens=None, summary=None
        )
        ai_config = AIModelConfig(
            model_name="openai:o1-mini", thinking=thinking_config, temperature=None
        )
        processor = ProductLabelingProcessor(config=ai_config)

        # Run analysis
        result = await processor.analyze_issue(sample_issue_data, include_images=False)

        # Verify Agent was created with thinking settings
        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]
        model_settings = call_kwargs["model_settings"]
        assert model_settings["reasoning_effort"] == "high"

        # Verify analysis was called
        mock_agent_instance.run.assert_called_once()

        # Verify result
        assert isinstance(result, ProductLabelingResponse)
        assert result.confidence == 0.95
        assert "thinking" in result.reasoning.lower()

    @pytest.mark.asyncio
    @patch("github_issue_analysis.ai.processors.Agent")
    async def test_multimodal_with_thinking_models(
        self, mock_agent_class: MagicMock
    ) -> None:
        """Test multimodal processing with thinking models."""
        mock_agent_instance = AsyncMock()
        mock_agent_class.return_value = mock_agent_instance

        # Mock successful multimodal response
        mock_response = MagicMock()
        mock_response.data = ProductLabelingResponse(
            confidence=0.9,
            recommended_labels=[],
            current_labels_assessment=[],
            summary="Multimodal analysis with thinking",
            reasoning="Analyzed images with thinking model",
        )
        mock_agent_instance.run.return_value = mock_response

        # Create issue with images
        issue_with_images = {
            "org": "test",
            "repo": "test",
            "issue": {
                "number": 1,
                "title": "Visual bug",
                "body": "See attached screenshot",
                "labels": [],
                "comments": [],
                "attachments": [
                    {
                        "filename": "screenshot.png",
                        "content_type": "image/png",
                        "downloaded": True,
                        "local_path": "test_screenshot.png",
                    }
                ],
            },
        }

        thinking_config = ThinkingConfig(
            effort="medium", budget_tokens=None, summary=None
        )
        ai_config = AIModelConfig(
            model_name="openai:o1-mini", thinking=thinking_config, temperature=None
        )
        processor = ProductLabelingProcessor(config=ai_config)

        # Mock image loading to return fake image content
        with patch(
            "github_issue_analysis.ai.image_utils.load_downloaded_images"
        ) as mock_load:
            mock_load.return_value = [
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64,fake_image_data"},
                }
            ]

            result = await processor.analyze_issue(
                issue_with_images, include_images=True
            )

        # Verify Agent was created with thinking settings
        call_kwargs = mock_agent_class.call_args[1]
        model_settings = call_kwargs["model_settings"]
        assert model_settings["reasoning_effort"] == "medium"

        # Verify multimodal call was made
        mock_agent_instance.run.assert_called_once()
        call_args = mock_agent_instance.run.call_args[0]

        # Should have been called with list containing text and ImageUrl
        assert isinstance(call_args[0], list)
        assert len(call_args[0]) == 2  # text prompt + image

        assert isinstance(result, ProductLabelingResponse)
        assert "thinking" in result.reasoning.lower()
