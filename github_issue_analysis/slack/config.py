"""Configuration for Slack integration."""

import os
from typing import Optional


class SlackConfig:
    """Configuration class for Slack API integration."""

    def __init__(self) -> None:
        """Initialize Slack configuration from environment variables."""
        self.bot_token: Optional[str] = os.getenv("SLACK_BOT_TOKEN")
        self.channel: str = os.getenv("SLACK_CHANNEL", "#support-chat")

    def is_configured(self) -> bool:
        """Check if Slack is properly configured."""
        return self.bot_token is not None

    def validate(self) -> None:
        """Validate configuration and raise error if invalid."""
        if not self.bot_token:
            raise ValueError(
                "SLACK_BOT_TOKEN environment variable is required for Slack notifications"
            )
