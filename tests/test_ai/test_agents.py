"""Tests for simplified PydanticAI agent creation interface."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from github_issue_analysis.ai.agents import create_product_labeling_agent
from github_issue_analysis.ai.config import supports_thinking, validate_model_string
from github_issue_analysis.ai.models import ProductLabelingResponse


class TestValidateModelString:
    """Tests for validate_model_string helper function."""

    def test_valid_model_strings(self) -> None:
        """Test validation of valid model string formats."""
        valid_models = [
            ("openai:gpt-4o-mini", ("openai", "gpt-4o-mini")),
            (
                "anthropic:claude-3-5-sonnet-latest",
                ("anthropic", "claude-3-5-sonnet-latest"),
            ),
            ("google:gemini-2.0-flash", ("google", "gemini-2.0-flash")),
            ("groq:qwen-qwq-32b", ("groq", "qwen-qwq-32b")),
            ("OPENAI:O4-MINI", ("openai", "O4-MINI")),  # Case handling
        ]

        for model_string, expected in valid_models:
            provider, model_name = validate_model_string(model_string)
            assert provider == expected[0]
            assert model_name == expected[1]

    def test_invalid_model_strings(self) -> None:
        """Test validation errors for invalid model string formats."""
        invalid_models = [
            "openai-gpt-4o-mini",  # Missing colon
            "gpt-4o-mini",  # No provider
            "openai:",  # Empty model name
            ":gpt-4o-mini",  # Empty provider
            "",  # Empty string
            ":",  # Just colon
        ]

        for invalid_model in invalid_models:
            with pytest.raises(ValueError) as exc_info:
                validate_model_string(invalid_model)

            error_msg = str(exc_info.value)
            assert "Invalid model format" in error_msg

    def test_model_string_with_multiple_colons(self) -> None:
        """Test that model strings with multiple colons are handled correctly."""
        # This should work - only split on first colon
        provider, model_name = validate_model_string("openai:gpt-4o:latest")
        assert provider == "openai"
        assert model_name == "gpt-4o:latest"


class TestSupportsThinking:
    """Tests for supports_thinking helper function."""

    def test_models_with_thinking_support(self) -> None:
        """Test models that support thinking capabilities."""
        thinking_models = [
            "openai:o4-mini",
            "openai:o1-preview",
            "openai:o3-mini",
            "anthropic:claude-3-5-sonnet-latest",
            "google:gemini-2.0-flash",
            "google:gemini-thinking",
            "groq:qwen-qwq-32b",
            "groq:deepseek-r1",
        ]

        for model in thinking_models:
            assert supports_thinking(model), f"Model {model} should support thinking"

    def test_models_without_thinking_support(self) -> None:
        """Test models that do not support thinking capabilities."""
        non_thinking_models = [
            "openai:gpt-4o-mini",
            "openai:gpt-4o",
            "google:gemini-1.5-pro",
            "unknown:model",
        ]

        for model in non_thinking_models:
            assert not supports_thinking(
                model
            ), f"Model {model} should not support thinking"

    def test_supports_thinking_invalid_model(self) -> None:
        """Test that supports_thinking validates model format."""
        with pytest.raises(ValueError) as exc_info:
            supports_thinking("invalid-model")

        error_msg = str(exc_info.value)
        assert "Invalid model format" in error_msg


class TestCreateProductLabelingAgent:
    """Tests for create_product_labeling_agent function."""

    @patch("github_issue_analysis.ai.agents.Agent")
    def test_basic_agent_creation(self, mock_agent_class: MagicMock) -> None:
        """Test basic agent creation without thinking configuration."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        agent = create_product_labeling_agent("openai:gpt-4o-mini")

        # Verify Agent was created with correct parameters
        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]

        assert call_kwargs["model"] == "openai:gpt-4o-mini"
        assert call_kwargs["output_type"] == ProductLabelingResponse
        assert "system_prompt" in call_kwargs
        assert call_kwargs["retries"] == 2
        assert call_kwargs["model_settings"] == {"temperature": 0.0}

        # Verify returned agent is the mock instance
        assert agent is mock_agent_instance

    @patch("github_issue_analysis.ai.agents.Agent")
    def test_agent_with_temperature(self, mock_agent_class: MagicMock) -> None:
        """Test agent creation with custom temperature."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        create_product_labeling_agent(model="openai:gpt-4o", temperature=0.7)

        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]

        assert call_kwargs["model"] == "openai:gpt-4o"
        model_settings = call_kwargs["model_settings"]
        assert model_settings["temperature"] == 0.7

    @patch("github_issue_analysis.ai.agents.Agent")
    def test_agent_with_retry_count(self, mock_agent_class: MagicMock) -> None:
        """Test agent creation with custom retry count."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        create_product_labeling_agent(model="openai:gpt-4o", retry_count=5)

        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]

        assert call_kwargs["retries"] == 5

    @patch("github_issue_analysis.ai.agents.Agent")
    def test_openai_thinking_agent(self, mock_agent_class: MagicMock) -> None:
        """Test agent creation with OpenAI thinking model configuration."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        create_product_labeling_agent(
            model="openai:o4-mini", thinking_effort="high", temperature=0.2
        )

        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]

        assert call_kwargs["model"] == "openai:o4-mini"
        model_settings = call_kwargs["model_settings"]
        assert model_settings["reasoning_effort"] == "high"
        assert model_settings["temperature"] == 0.2

    @patch("github_issue_analysis.ai.agents.Agent")
    def test_anthropic_thinking_agent(self, mock_agent_class: MagicMock) -> None:
        """Test agent creation with Anthropic model without thinking configuration."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        # Anthropic models don't support thinking_effort parameter
        create_product_labeling_agent(model="anthropic:claude-3-5-sonnet-latest")

        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]

        assert call_kwargs["model"] == "anthropic:claude-3-5-sonnet-latest"
        assert call_kwargs["model_settings"] == {"temperature": 0.0}

    @patch("github_issue_analysis.ai.agents.Agent")
    def test_google_thinking_agent(self, mock_agent_class: MagicMock) -> None:
        """Test agent creation with Google model without thinking configuration."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        # Google models don't support thinking_effort parameter
        create_product_labeling_agent(model="google:gemini-2.0-flash")

        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]

        assert call_kwargs["model"] == "google:gemini-2.0-flash"
        assert call_kwargs["model_settings"] == {"temperature": 0.0}

    def test_invalid_model_format(self) -> None:
        """Test error handling for invalid model string format."""
        with pytest.raises(ValueError) as exc_info:
            create_product_labeling_agent("invalid-model")

        error_msg = str(exc_info.value)
        assert "Invalid model format" in error_msg

    def test_invalid_thinking_effort(self) -> None:
        """Test error handling for invalid thinking effort values."""
        with pytest.raises(ValueError) as exc_info:
            create_product_labeling_agent(
                model="openai:o4-mini",
                thinking_effort="invalid",
            )

        error_msg = str(exc_info.value)
        assert "effort" in error_msg.lower()

    def test_temperature_bounds(self) -> None:
        """Test temperature validation bounds."""
        # Test valid temperatures
        valid_temps = [0.0, 0.5, 1.0, 1.5, 2.0]
        for temp in valid_temps:
            # Should not raise an error
            with patch("github_issue_analysis.ai.agents.Agent"):
                create_product_labeling_agent(model="openai:gpt-4o", temperature=temp)

        # Test invalid temperatures
        invalid_temps = [-0.1, 2.1, -1.0, 3.0]
        for temp in invalid_temps:
            with pytest.raises(ValueError):
                create_product_labeling_agent(model="openai:gpt-4o", temperature=temp)


class TestAgentIntegration:
    """Integration tests for the agent creation and usage."""

    @pytest.mark.asyncio
    @patch("github_issue_analysis.ai.agents.Agent")
    async def test_agent_usage_flow(self, mock_agent_class: MagicMock) -> None:
        """Test complete flow of creating and using an agent."""
        # Mock the Agent and its run method
        mock_agent_instance = AsyncMock()
        mock_agent_class.return_value = mock_agent_instance

        # Mock a successful response
        mock_response = MagicMock()
        mock_response.data = ProductLabelingResponse(
            recommendation_confidence=0.9,
            recommended_labels=[],
            current_labels_assessment=[],
            summary="Test analysis",
            reasoning="Mock reasoning",
        )
        mock_agent_instance.run.return_value = mock_response

        # Create agent
        agent = create_product_labeling_agent(
            model="openai:gpt-4o-mini", temperature=0.3, retry_count=3
        )

        # Use the agent
        result = await agent.run("Test prompt")

        # Verify agent creation
        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]
        assert call_kwargs["model"] == "openai:gpt-4o-mini"
        assert call_kwargs["retries"] == 3
        assert call_kwargs["model_settings"]["temperature"] == 0.3

        # Verify agent usage
        mock_agent_instance.run.assert_called_once_with("Test prompt")
        assert result.data.recommendation_confidence == 0.9

    @pytest.mark.asyncio
    @patch("github_issue_analysis.ai.agents.Agent")
    async def test_thinking_agent_integration(
        self, mock_agent_class: MagicMock
    ) -> None:
        """Test integration with thinking models."""
        mock_agent_instance = AsyncMock()
        mock_agent_class.return_value = mock_agent_instance

        mock_response = MagicMock()
        mock_response.data = ProductLabelingResponse(
            recommendation_confidence=0.95,
            recommended_labels=[],
            current_labels_assessment=[],
            summary="Thinking analysis",
            reasoning="Deep reasoning with thinking model",
        )
        mock_agent_instance.run.return_value = mock_response

        # Create thinking agent
        agent = create_product_labeling_agent(
            model="openai:o4-mini", thinking_effort="high", temperature=0.1
        )

        # Use the agent
        result = await agent.run("Complex analysis prompt")

        # Verify thinking configuration was applied
        call_kwargs = mock_agent_class.call_args[1]
        model_settings = call_kwargs["model_settings"]
        assert model_settings["reasoning_effort"] == "high"
        assert model_settings["temperature"] == 0.1

        # Verify result
        assert result.data.recommendation_confidence == 0.95
        assert "thinking" in result.data.reasoning.lower()

    def test_multiple_agent_creation(self) -> None:
        """Test creating multiple agents with different configurations."""
        with patch("github_issue_analysis.ai.agents.Agent") as mock_agent_class:
            mock_agent_class.return_value = MagicMock()

            # Create multiple agents
            create_product_labeling_agent("openai:gpt-4o")
            create_product_labeling_agent("anthropic:claude-3-5-sonnet")
            create_product_labeling_agent("openai:o4-mini", thinking_effort="medium")

            # Verify separate agent instances were created
            assert mock_agent_class.call_count == 3

            # Verify different configurations
            calls = mock_agent_class.call_args_list
            assert calls[0][1]["model"] == "openai:gpt-4o"
            assert calls[1][1]["model"] == "anthropic:claude-3-5-sonnet"
            assert calls[2][1]["model"] == "openai:o4-mini"

            # Third agent should have thinking settings
            thinking_settings = calls[2][1]["model_settings"]
            assert thinking_settings["reasoning_effort"] == "medium"

    @patch("github_issue_analysis.ai.agents.Agent")
    def test_edge_case_configurations(self, mock_agent_class: MagicMock) -> None:
        """Test edge case configurations."""
        mock_agent_class.return_value = MagicMock()

        # Test with zero temperature
        create_product_labeling_agent(model="openai:gpt-4o", temperature=0.0)

        # Test with max temperature
        create_product_labeling_agent(model="openai:gpt-4o", temperature=2.0)

        # Test with max retry count
        create_product_labeling_agent(model="openai:gpt-4o", retry_count=10)

        # Verify all configurations were accepted
        assert mock_agent_class.call_count == 3

        calls = mock_agent_class.call_args_list
        assert calls[0][1]["model_settings"]["temperature"] == 0.0
        assert calls[1][1]["model_settings"]["temperature"] == 2.0
        assert calls[2][1]["retries"] == 10
