"""Comment generation system for GitHub issue label updates."""

from .change_detector import IssueUpdatePlan


class CommentGenerator:
    """Generates GitHub comments explaining AI-driven label changes."""

    def __init__(self) -> None:
        """Initialize the comment generator."""
        pass

    def generate_update_comment(self, plan: IssueUpdatePlan) -> str:
        """Generate a comment explaining label changes.

        Args:
            plan: The issue update plan with changes to explain

        Returns:
            Formatted comment text ready for posting to GitHub
        """
        if not plan.changes:
            return ""

        additions = [c for c in plan.changes if c.action == "add"]
        removals = [c for c in plan.changes if c.action == "remove"]

        lines = []
        lines.append("🤖 **AI Label Update**")
        lines.append("")
        lines.append(
            "The following label changes have been applied based on AI analysis:"
        )
        lines.append("")

        if additions:
            lines.append("**Added Labels:**")
            for change in additions:
                confidence_text = f"confidence: {change.confidence:.2f}"
                lines.append(
                    f"- `{change.label}` ({confidence_text}) - {change.reason}"
                )
            lines.append("")

        if removals:
            lines.append("**Removed Labels:**")
            for change in removals:
                confidence_text = f"confidence: {change.confidence:.2f}"
                lines.append(
                    f"- `{change.label}` ({confidence_text}) - {change.reason}"
                )
            lines.append("")

        if plan.comment_summary:
            lines.append(f"**Reasoning:** {plan.comment_summary}")
            lines.append("")

        lines.append("---")
        lines.append(
            "*This update was automated based on AI analysis of issue content.*"
        )

        return "\n".join(lines)

    def generate_dry_run_summary(self, plans: list[IssueUpdatePlan]) -> str:
        """Generate a summary of planned changes for dry-run mode.

        Shows detailed information including reasoning for each change and
        the exact GitHub comment that would be posted.

        Args:
            plans: List of issue update plans

        Returns:
            Formatted summary text for console output
        """
        if not plans:
            return "No changes needed based on current confidence threshold."

        lines = []
        lines.append(f"Found {len(plans)} issue(s) that need label updates:")
        lines.append("")

        for plan in plans:
            lines.append(f"**Issue #{plan.issue_number} ({plan.org}/{plan.repo})**")
            lines.append(f"Overall confidence: {plan.overall_confidence:.2f}")

            additions = [c for c in plan.changes if c.action == "add"]
            removals = [c for c in plan.changes if c.action == "remove"]

            if additions:
                lines.append("  Add:")
                for change in additions:
                    lines.append(
                        f"    + {change.label} (confidence: {change.confidence:.2f}) - "
                        f"{change.reason}"
                    )

            if removals:
                lines.append("  Remove:")
                for change in removals:
                    lines.append(
                        f"    - {change.label} (confidence: {change.confidence:.2f}) - "
                        f"{change.reason}"
                    )

            # Add GitHub comment preview
            comment = self.generate_update_comment(plan)
            if comment:
                lines.append("")
                lines.append("**GitHub Comment Preview:**")
                lines.append("---")
                lines.append(comment)
                lines.append("---")

            lines.append("")

        return "\n".join(lines)

    def generate_execution_summary(
        self,
        successful: list[IssueUpdatePlan],
        failed: list[tuple[IssueUpdatePlan, str]],
    ) -> str:
        """Generate a summary of execution results.

        Args:
            successful: List of successfully updated plans
            failed: List of (plan, error_message) tuples for failed updates

        Returns:
            Formatted summary text for console output
        """
        lines = []

        if successful:
            lines.append(f"✅ Successfully updated {len(successful)} issue(s):")
            for plan in successful:
                change_count = len(plan.changes)
                lines.append(
                    f"  - Issue #{plan.issue_number}: {change_count} change(s)"
                )
            lines.append("")

        if failed:
            lines.append(f"❌ Failed to update {len(failed)} issue(s):")
            for plan, error in failed:
                lines.append(f"  - Issue #{plan.issue_number}: {error}")
            lines.append("")

        if not successful and not failed:
            lines.append("No issues processed.")

        return "\n".join(lines)
