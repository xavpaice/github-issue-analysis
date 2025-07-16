"""Minimal processor wrapper for backward compatibility."""

import json
from typing import Any

from pydantic_ai.messages import ImageUrl

from .agents import create_product_labeling_agent
from .models import ProductLabelingResponse


class ProductLabelingProcessor:
    """Minimal wrapper around the new agent interface for backward compatibility."""

    def __init__(self, config: Any = None, model_name: str | None = None):
        """Initialize processor.

        Args:
            config: Ignored (for backward compatibility)
            model_name: Model identifier (e.g., 'openai:gpt-4o-mini')
        """
        self.model_name = model_name or "openai:o4-mini"
        self._agent: Any = None

    @property
    def agent(self) -> Any:
        """Lazy-loaded agent for product labeling."""
        if self._agent is None:
            self._agent = create_product_labeling_agent(self.model_name)
        return self._agent

    async def analyze_issue(
        self, issue_data: dict[str, Any], include_images: bool = True
    ) -> ProductLabelingResponse:
        """Analyze issue using new agent interface."""
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
                return result.data  # type: ignore[no-any-return]
            except Exception as e:
                # Fallback to text-only if multimodal fails
                print(f"Multimodal processing failed, falling back to text-only: {e}")
                # Rebuild prompt without image context for fallback
                fallback_prompt = self._format_issue_prompt(issue_data, 0)
                result = await self.agent.run(fallback_prompt)
                return result.data  # type: ignore[no-any-return]
        else:
            # Text-only processing
            try:
                result = await self.agent.run(text_prompt)
                return result.data  # type: ignore[no-any-return]
            except Exception as e:
                # Graceful error handling - log and re-raise with context
                print(f"Failed to analyze issue: {e}")
                raise

    def _format_issue_prompt(
        self, issue_data: dict[str, Any], image_count: int = 0
    ) -> str:
        """Format issue data for analysis prompt."""
        issue = issue_data["issue"]

        # Include all comments with full content
        comment_text = ""
        if issue.get("comments"):
            all_comments = issue["comments"]  # Include ALL comments
            comment_entries = []
            for comment in all_comments:
                user = comment["user"]["login"]
                body = comment["body"].replace("\n", " ").strip()  # Full content
                comment_entries.append(f"{user}: {body}")
            comment_text = " | ".join(comment_entries)

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

**Body:** {issue["body"]}

**Current Labels:** {json.dumps([
    label["name"] for label in issue["labels"]
    if label["name"].startswith("product::")
], separators=(',', ':'))}

**Repository:** {issue_data["org"]}/{issue_data["repo"]}

**Comments:** {comment_text or "No comments"}
{image_instruction}

Recommend the most appropriate product label(s) based on the issue content.
"""
