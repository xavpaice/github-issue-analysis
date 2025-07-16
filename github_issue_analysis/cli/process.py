"""AI processing commands for GitHub issue analysis."""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from ..ai.agents import create_product_labeling_agent
from ..ai.capabilities import validate_thinking_configuration
from ..recommendation.manager import RecommendationManager

app = typer.Typer(
    help="AI processing commands",
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


@app.command()
def product_labeling(
    org: str = typer.Option(
        ...,
        "--org",
        "-o",
        help="GitHub organization name",
        rich_help_panel="Target Selection",
    ),
    repo: str | None = typer.Option(
        None,
        "--repo",
        "-r",
        help="GitHub repository name",
        rich_help_panel="Target Selection",
    ),
    issue_number: int | None = typer.Option(
        None,
        "--issue-number",
        "-i",
        help="Specific issue number",
        rich_help_panel="Target Selection",
    ),
    model: str = typer.Option(
        "openai:gpt-4o",
        "--model",
        "-m",
        help="AI model in format provider:name (e.g., openai:gpt-4o)",
        rich_help_panel="AI Configuration",
    ),
    thinking_effort: str | None = typer.Option(
        None,
        "--thinking-effort",
        help="Reasoning effort level: low, medium, high (for thinking models)",
        rich_help_panel="AI Configuration",
    ),
    temperature: float = typer.Option(
        0.0,
        "--temperature",
        help="Model temperature (0.0-2.0)",
        rich_help_panel="AI Configuration",
    ),
    retry_count: int = typer.Option(
        2,
        "--retry-count",
        help="Number of retries on failure",
        rich_help_panel="AI Configuration",
    ),
    thinking_budget: int | None = typer.Option(
        None,
        "--thinking-budget",
        help="Thinking token budget for models (legacy option)",
        rich_help_panel="AI Configuration",
    ),
    include_images: bool = typer.Option(
        True,
        "--include-images/--no-include-images",
        help="Include image analysis",
        rich_help_panel="Processing Options",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Preview changes without applying them",
        rich_help_panel="Processing Options",
    ),
    reprocess: bool = typer.Option(
        False,
        "--reprocess",
        help="Force reprocessing of items already processed",
        rich_help_panel="Processing Options",
    ),
) -> None:
    """Analyze GitHub issues for product labeling recommendations.

    This command processes GitHub issues using AI to generate product labeling
    recommendations. You can target specific issues, repositories, or entire
    organizations.

    Examples:

        # Process a specific issue
        github-analysis process product-labeling --org myorg --repo myrepo \\
            --issue-number 123

        # Process all issues in a repository
        github-analysis process product-labeling --org myorg --repo myrepo

        # Use a thinking model with high effort
        github-analysis process product-labeling --org myorg --repo myrepo \\
            --model openai:o4-mini --thinking-effort high

        # Preview changes without processing
        github-analysis process product-labeling --org myorg --repo myrepo --dry-run
    """
    try:
        # Validate thinking configuration early
        if model and (thinking_effort or thinking_budget):
            validate_thinking_configuration(model, thinking_effort, thinking_budget)

        asyncio.run(
            _run_product_labeling(
                org,
                repo,
                issue_number,
                model,
                thinking_effort,
                thinking_budget,
                temperature,
                retry_count,
                include_images,
                dry_run,
                reprocess,
            )
        )
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)


async def _run_product_labeling(
    org: str,
    repo: str | None,
    issue_number: int | None,
    model: str,
    thinking_effort: str | None,
    thinking_budget: int | None,
    temperature: float,
    retry_count: int,
    include_images: bool,
    dry_run: bool,
    reprocess: bool,
) -> None:
    """Run product labeling analysis."""

    # Find issue files to process
    # Allow override via environment variable for testing
    base_data_dir = Path(os.environ.get("GITHUB_ANALYSIS_DATA_DIR", "data"))
    data_dir = base_data_dir / "issues"
    if not data_dir.exists():
        console.print(
            "[red]No issues directory found. Run collect command first.[/red]"
        )
        return

    issue_files = []
    if issue_number:
        # Validate that repo is provided for specific issue
        if not repo:
            console.print(
                "[red]Error: --repo is required when specifying " "--issue-number[/red]"
            )
            return

        # Find specific issue file with org/repo/issue pattern
        expected_filename = f"{org}_{repo}_issue_{issue_number}.json"
        expected_path = data_dir / expected_filename

        if not expected_path.exists():
            console.print(
                f"[red]Issue #{issue_number} not found for {org}/{repo}.[/red]"
            )
            console.print(f"[red]Expected file: {expected_filename}[/red]")
            return
        issue_files = [expected_path]
    elif org and repo:
        # Process all issues for specific org/repo
        pattern = f"{org}_{repo}_issue_*.json"
        issue_files = list(data_dir.glob(pattern))
        if not issue_files:
            console.print(f"[red]No issues found for {org}/{repo}.[/red]")
            return
    elif org:
        # Process all issues for specific org (across all repos)
        pattern = f"{org}_*_issue_*.json"
        issue_files = list(data_dir.glob(pattern))
        if not issue_files:
            console.print(f"[red]No issues found for organization {org}.[/red]")
            return
    else:
        # Process all issues
        issue_files = list(data_dir.glob("*_issue_*.json"))

    if not issue_files:
        console.print("[yellow]No issue files found to process.[/yellow]")
        return

    console.print(f"[blue]Found {len(issue_files)} issue(s) to process[/blue]")

    if dry_run:
        for file_path in issue_files:
            console.print(f"Would process: {file_path.name}")
        return

    # Create agent using new simplified interface
    try:
        agent = create_product_labeling_agent(
            model=model,
            thinking_effort=thinking_effort,
            temperature=temperature,
            retry_count=retry_count,
        )
        console.print(f"[blue]Using model: {model}[/blue]")
        console.print(
            f"[blue]Temperature: {temperature}, Retry count: {retry_count}[/blue]"
        )
        if thinking_effort:
            console.print(f"[blue]Thinking effort: {thinking_effort}[/blue]")

    except Exception as e:
        console.print(f"[red]Failed to create agent: {e}[/red]")
        return

    console.print(
        f"[blue]Image processing: {'enabled' if include_images else 'disabled'}[/blue]"
    )

    # Initialize recommendation manager for filtering
    recommendation_manager = RecommendationManager(base_data_dir)

    # Process each issue
    results_dir = base_data_dir / "results"
    results_dir.mkdir(exist_ok=True)

    skipped_count = 0
    for file_path in issue_files:
        try:
            # Load issue data to check if we should process it
            with open(file_path) as f:
                issue_data = json.load(f)

            # Check if issue should be reprocessed
            issue_org = issue_data["org"]
            issue_repo = issue_data["repo"]
            issue_num = issue_data["issue"]["number"]

            if not recommendation_manager.should_reprocess_issue(
                issue_org, issue_repo, issue_num, reprocess
            ):
                console.print(
                    f"[yellow]Skipping {file_path.name} - already reviewed "
                    "(use --reprocess to override)[/yellow]"
                )
                skipped_count += 1
                continue

            console.print(f"Processing {file_path.name}...")

            # Check for images if enabled
            if include_images:
                attachment_count = len(
                    [
                        att
                        for att in issue_data["issue"].get("attachments", [])
                        if att.get("downloaded")
                        and att.get("content_type", "").startswith("image/")
                    ]
                )
                if attachment_count > 0:
                    console.print(f"  Found {attachment_count} image(s) to analyze")

            # Analyze with AI using new agent interface
            result = await _analyze_issue_with_agent(agent, issue_data, include_images)

            # Save result
            result_file = results_dir / f"{file_path.stem}_product-labeling.json"
            result_data = {
                "issue_reference": {
                    "file_path": str(file_path),
                    "org": issue_data["org"],
                    "repo": issue_data["repo"],
                    "issue_number": issue_data["issue"]["number"],
                },
                "processor": {
                    "name": "product-labeling",
                    "version": "3.0.0",  # Simplified agent interface version
                    "model": model,
                    "thinking_effort": thinking_effort,
                    "temperature": temperature,
                    "include_images": include_images,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                },
                "analysis": result.model_dump(),
            }

            with open(result_file, "w") as f:
                json.dump(result_data, f, indent=2)

            console.print(f"[green]✓ Saved results to {result_file.name}[/green]")

        except Exception as e:
            console.print(f"[red]✗ Failed to process {file_path.name}: {e}[/red]")
            continue

    # Show summary if any were skipped
    if skipped_count > 0:
        total_count = len(issue_files)
        processed_count = total_count - skipped_count
        console.print(
            f"\n[blue]Summary: Processed {processed_count}/{total_count} issues "
            f"({skipped_count} skipped due to existing reviews)[/blue]"
        )


async def _analyze_issue_with_agent(
    agent: Any, issue_data: dict[str, Any], include_images: bool = True
) -> Any:
    """Analyze issue using the new agent interface.

    Args:
        agent: PydanticAI agent instance
        issue_data: Issue data dictionary
        include_images: Whether to include image analysis

    Returns:
        ProductLabelingResponse with analysis results
    """
    from pydantic_ai.messages import ImageUrl

    from ..ai.image_utils import load_downloaded_images

    # Load images if requested
    image_contents = load_downloaded_images(issue_data, include_images)

    # Build prompt with explicit image context
    text_prompt = _format_issue_prompt(issue_data, len(image_contents))

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
            result = await agent.run(message_parts)
            return result.data
        except Exception as e:
            # Fallback to text-only if multimodal fails
            console.print(
                f"[yellow]Multimodal processing failed, "
                f"falling back to text-only: {e}[/yellow]"
            )
            # Rebuild prompt without image context for fallback
            fallback_prompt = _format_issue_prompt(issue_data, 0)
            result = await agent.run(fallback_prompt)
            return result.data
    else:
        # Text-only processing
        try:
            result = await agent.run(text_prompt)
            return result.data
        except Exception as e:
            # Graceful error handling - log and re-raise with context
            console.print(f"[red]Failed to analyze issue: {e}[/red]")
            raise


def _format_issue_prompt(issue_data: dict[str, Any], image_count: int = 0) -> str:
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


if __name__ == "__main__":
    app()
