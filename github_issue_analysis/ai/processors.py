"""Product labeling processor using PydanticAI."""

import os
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.messages import ImageUrl

from .models import ProductLabelingResponse
from .prompts import build_product_labeling_prompt


class ProductLabelingProcessor:
    """Product labeling processor with configurable AI models."""

    def __init__(self, model_name: str | None = None):
        """Initialize processor with configurable model.

        Args:
            model_name: Model identifier (e.g., 'openai:gpt-4o-mini',
                       'anthropic:claude-3-5-sonnet'). If None, uses AI_MODEL
                       environment variable or default
        """
        self.model_name = model_name or os.getenv("AI_MODEL", "openai:gpt-4o")
        self._agent: Agent | None = None

    @property
    def agent(self) -> Agent:
        """Lazy-loaded agent for product labeling."""
        if self._agent is None:
            self._agent = Agent(
                model=self.model_name,
                output_type=ProductLabelingResponse,  # type: ignore[arg-type]
                system_prompt=self._build_system_prompt(),
            )
        return self._agent

    def _build_system_prompt(self) -> str:
        """Build system prompt from modular components."""
        return build_product_labeling_prompt()

    def _enhance_system_prompt_for_images(self) -> str:
        """Enhanced system prompt when images are present."""
        base_prompt = self._build_system_prompt()

        image_guidance = """

**IMAGE ANALYSIS GUIDANCE:**
When images are provided, analyze them carefully for:
1. **Product Interface Screenshots**: Look for specific UI elements, branding, or
   interface patterns
2. **Error Messages**: Read error text that might indicate which product is failing
3. **File Paths and Logs**: Check for product-specific file paths or log entries
4. **Admin Console Views**: Identify KOTS admin interface, file browsers, or
   configuration screens

Include your image analysis in the reasoning field and populate the images_analyzed
array with descriptions of what each image shows.
"""

        return base_prompt + image_guidance

    async def analyze_issue(
        self, issue_data: dict[str, Any], include_images: bool = True
    ) -> ProductLabelingResponse:
        """Analyze issue and recommend product labels with optional image processing.

        Args:
            issue_data: Issue data dictionary
            include_images: Whether to include image analysis

        Returns:
            ProductLabelingResponse with analysis results
        """
        from .image_utils import load_downloaded_images

        # Load images if requested
        image_contents = load_downloaded_images(issue_data, include_images)

        # Build prompt with explicit image context
        text_prompt = self._format_issue_prompt(issue_data, len(image_contents))

        # Handle image processing
        if image_contents:
            # Build multimodal content using PydanticAI message types
            message_parts: list[str | ImageUrl] = [text_prompt]

            # Add images as ImageUrl messages
            for img_content in image_contents:
                if img_content.get("type") == "image_url":
                    image_url = img_content["image_url"]["url"]
                    message_parts.append(ImageUrl(url=image_url))

            try:
                result = await self.agent.run(message_parts)
                return result.data  # type: ignore[return-value]
            except Exception as e:
                # Fallback to text-only if multimodal fails
                print(f"Multimodal processing failed, falling back to text-only: {e}")
                # Rebuild prompt without image context for fallback
                fallback_prompt = self._format_issue_prompt(issue_data, 0)
                result = await self.agent.run(fallback_prompt)
                return result.data  # type: ignore[return-value]
        else:
            # Text-only processing
            try:
                result = await self.agent.run(text_prompt)
                return result.data  # type: ignore[return-value]
            except Exception as e:
                # Graceful error handling - log and re-raise with context
                print(f"Failed to analyze issue: {e}")
                raise

    def _format_issue_prompt(
        self, issue_data: dict[str, Any], image_count: int = 0
    ) -> str:
        """Format issue data for analysis prompt."""
        issue = issue_data["issue"]

        # Simple comment summary (no truncation for phase 1)
        comment_summary = ""
        if issue.get("comments"):
            recent_comments = issue["comments"][-3:]  # Last 3 comments
            summaries = []
            for comment in recent_comments:
                user = comment["user"]["login"]
                body = comment["body"][:200].replace("\n", " ").strip()
                summaries.append(f"{user}: {body}")
            comment_summary = " | ".join(summaries)

        # Add explicit image context instructions
        if image_count > 0:
            image_instruction = f"""

**IMAGES PROVIDED:** This issue contains {image_count} image(s) that you should analyze.
When analyzing the images, look for:
- UI screenshots showing specific product interfaces
- Error messages or logs that indicate which product is failing
- File browser views, admin consoles, or diagnostic outputs
- Any visual indicators of the affected product

IMPORTANT: Fill in the images_analyzed array with descriptions of what each image
shows and how it influences your classification. Fill in image_impact with how
the images affected your decision.
"""
        else:
            image_instruction = """

**NO IMAGES PROVIDED:** This issue contains no images to analyze.
IMPORTANT: Leave images_analyzed as an empty array and image_impact as an empty
string since no images were provided.
"""

        return f"""
Analyze this GitHub issue for product labeling:

**Title:** {issue["title"]}

**Body:** {issue["body"][:1500]}

**Current Labels:** {[label["name"] for label in issue["labels"]]}

**Repository:** {issue_data["org"]}/{issue_data["repo"]}

**Recent Comments:** {comment_summary or "No comments"}
{image_instruction}

Recommend the most appropriate product label(s) based on the issue content.
"""


# Future: Easy to add new processor types
class IssueClassificationProcessor:
    """Future: General issue classification processor."""

    pass
