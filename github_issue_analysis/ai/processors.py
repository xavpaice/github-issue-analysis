"""Product labeling processor using PydanticAI."""

import os
from typing import Any

from pydantic_ai import Agent

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

    async def analyze_issue(
        self, issue_data: dict[str, Any]
    ) -> ProductLabelingResponse:
        """Analyze issue and recommend product labels."""
        prompt = self._format_issue_prompt(issue_data)

        try:
            result = await self.agent.run(prompt)
            return result.data  # type: ignore[return-value]
        except Exception as e:
            # Graceful error handling - log and re-raise with context
            print(f"Failed to analyze issue: {e}")
            raise

    def _format_issue_prompt(self, issue_data: dict[str, Any]) -> str:
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

        return f"""
Analyze this GitHub issue for product labeling:

**Title:** {issue["title"]}

**Body:** {issue["body"][:1500]}

**Current Labels:** {[label["name"] for label in issue["labels"]]}

**Repository:** {issue_data["org"]}/{issue_data["repo"]}

**Recent Comments:** {comment_summary or "No comments"}

Recommend the most appropriate product label(s) based on the issue content.
"""


# Future: Easy to add new processor types
class IssueClassificationProcessor:
    """Future: General issue classification processor."""

    pass
