"""AI processing commands for GitHub issue analysis."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console

from ..ai.processors import ProductLabelingProcessor

app = typer.Typer(help="AI processing commands")
console = Console()


@app.command()
def product_labeling(
    org: str | None = typer.Option(
        None, "--org", "-o", help="GitHub organization name"
    ),
    repo: str | None = typer.Option(
        None, "--repo", "-r", help="GitHub repository name"
    ),
    issue_number: int | None = typer.Option(
        None, "--issue-number", help="Specific issue number to process"
    ),
    model: str | None = typer.Option(
        None, help="AI model to use (e.g., 'openai:gpt-4o-mini')"
    ),
    include_images: bool = typer.Option(
        True, help="Include image analysis (use --no-include-images to disable)"
    ),
    dry_run: bool = typer.Option(
        False, help="Show what would be processed without running AI"
    ),
) -> None:
    """Analyze GitHub issues for product labeling recommendations with optional
    image processing."""
    asyncio.run(
        _run_product_labeling(org, repo, issue_number, model, include_images, dry_run)
    )


async def _run_product_labeling(
    org: str | None,
    repo: str | None,
    issue_number: int | None,
    model: str | None,
    include_images: bool,
    dry_run: bool,
) -> None:
    """Run product labeling analysis."""

    # Find issue files to process
    data_dir = Path("data/issues")
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

    # Initialize processor
    processor = ProductLabelingProcessor(model_name=model)
    console.print(f"[blue]Using model: {processor.model_name}[/blue]")
    console.print(
        f"[blue]Image processing: {'enabled' if include_images else 'disabled'}[/blue]"
    )

    # Process each issue
    results_dir = Path("data/results")
    results_dir.mkdir(exist_ok=True)

    for file_path in issue_files:
        try:
            console.print(f"Processing {file_path.name}...")

            # Load issue data
            with open(file_path) as f:
                issue_data = json.load(f)

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
                    "version": "2.0.0",  # Phase 2 version
                    "model": processor.model_name,
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


if __name__ == "__main__":
    app()
