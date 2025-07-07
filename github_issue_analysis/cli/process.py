"""AI processing commands for GitHub issue analysis."""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console

from ..ai.capabilities import validate_thinking_configuration
from ..ai.config import build_ai_config
from ..ai.processors import ProductLabelingProcessor
from ..recommendation.manager import RecommendationManager
from .options import (
    DRY_RUN_OPTION,
    INCLUDE_IMAGES_OPTION,
    ISSUE_NUMBER_OPTION,
    MODEL_OPTION,
    REPO_OPTION,
    REPROCESS_OPTION,
    THINKING_BUDGET_OPTION,
    THINKING_EFFORT_OPTION,
)

app = typer.Typer(
    help="AI processing commands",
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


@app.command()
def product_labeling(
    org: str | None = typer.Option(
        None, "--org", "-o", help="GitHub organization name"
    ),
    repo: str | None = REPO_OPTION,
    issue_number: int | None = ISSUE_NUMBER_OPTION,
    model: str | None = MODEL_OPTION,
    thinking_effort: str | None = THINKING_EFFORT_OPTION,
    thinking_budget: int | None = THINKING_BUDGET_OPTION,
    include_images: bool = INCLUDE_IMAGES_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    reprocess: bool = REPROCESS_OPTION,
) -> None:
    """Analyze GitHub issues for product labeling recommendations with optional
    image processing."""
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
                include_images,
                dry_run,
                reprocess,
            )
        )
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)


async def _run_product_labeling(
    org: str | None,
    repo: str | None,
    issue_number: int | None,
    model: str | None,
    thinking_effort: str | None,
    thinking_budget: int | None,
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
        # Validate that org and repo are provided for specific issue
        if not org or not repo:
            console.print(
                "[red]Error: --org and --repo are required when specifying "
                "--issue-number[/red]"
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

    # Build AI configuration
    ai_config = build_ai_config(
        model_name=model,
        thinking_effort=thinking_effort,
        thinking_budget=thinking_budget,
    )

    # Initialize processor with enhanced configuration
    processor = ProductLabelingProcessor(config=ai_config)
    console.print(f"[blue]Using model: {ai_config.model_name}[/blue]")

    # Display thinking configuration if present
    if ai_config.thinking:
        if ai_config.thinking.effort:
            console.print(f"[blue]Thinking effort: {ai_config.thinking.effort}[/blue]")
        if ai_config.thinking.budget_tokens:
            budget = ai_config.thinking.budget_tokens
            console.print(f"[blue]Thinking budget: {budget} tokens[/blue]")

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

            # Analyze with AI
            result = await processor.analyze_issue(issue_data, include_images)

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
                    "version": "2.1.0",  # Thinking models support version
                    "model": ai_config.model_name,
                    "thinking_config": (
                        ai_config.thinking.model_dump() if ai_config.thinking else None
                    ),
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


if __name__ == "__main__":
    app()
