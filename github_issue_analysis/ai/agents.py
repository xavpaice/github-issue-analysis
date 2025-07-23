"""PydanticAI agents for GitHub issue analysis."""

from pydantic_ai import Agent

from .models import IssueTypeResponse, ProductLabelingResponse
from .prompts import ISSUE_TYPE_CLASSIFICATION_PROMPT, PRODUCT_LABELING_PROMPT

# Product labeling agent - direct definition
product_labeling_agent = Agent(
    output_type=ProductLabelingResponse,
    instructions=PRODUCT_LABELING_PROMPT,
    retries=2,
)

# Issue type classification agent - direct definition
issue_type_agent = Agent(
    output_type=IssueTypeResponse,
    instructions=ISSUE_TYPE_CLASSIFICATION_PROMPT,
    retries=2,
)
