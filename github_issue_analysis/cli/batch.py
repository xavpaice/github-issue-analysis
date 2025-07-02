"""Batch processing commands for cost-effective AI analysis."""

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from ..ai.batch.batch_manager import BatchManager
from ..ai.capabilities import validate_thinking_configuration
from ..ai.config import build_ai_config

app = typer.Typer(help="Batch processing commands")
console = Console()


@app.command()
def submit(
    processor_type: str = typer.Argument(
        help="Processor type (e.g., 'product-labeling')"
    ),
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
    thinking_effort: str | None = typer.Option(
        None,
        help="Reasoning effort level for thinking models (low, medium, high)",
    ),
    thinking_budget: int | None = typer.Option(
        None, help="Thinking token budget for Anthropic/Google models"
    ),
    include_images: bool = typer.Option(
        True, help="Include image analysis (use --no-include-images to disable)"
    ),
    dry_run: bool = typer.Option(
        False, help="Show what would be processed without submitting batch"
    ),
) -> None:
    """Submit a batch processing job for cost-effective AI analysis."""
    try:
        # Validate thinking configuration early
        if model and (thinking_effort or thinking_budget):
            validate_thinking_configuration(model, thinking_effort, thinking_budget)

        asyncio.run(
            _run_batch_submit(
                processor_type,
                org,
                repo,
                issue_number,
                model,
                thinking_effort,
                thinking_budget,
                include_images,
                dry_run,
            )
        )
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        raise typer.Exit(1)


async def _run_batch_submit(
    processor_type: str,
    org: str | None,
    repo: str | None,
    issue_number: int | None,
    model: str | None,
    thinking_effort: str | None,
    thinking_budget: int | None,
    include_images: bool,
    dry_run: bool,
) -> None:
    """Run batch submission."""

    # Validate processor type
    if processor_type != "product-labeling":
        console.print(f"[red]Unsupported processor type: {processor_type}[/red]")
        console.print("Currently supported: product-labeling")
        return

    # Validate CLI argument combinations
    if issue_number and (not org or not repo):
        console.print(
            "[red]Error: --org and --repo are required when "
            "specifying --issue-number[/red]"
        )
        return

    # Initialize batch manager
    batch_manager = BatchManager()

    # Check what issues would be processed
    try:
        issues = batch_manager.find_issues(org, repo, issue_number)

        if not issues:
            if issue_number:
                console.print(
                    f"[red]Issue #{issue_number} not found for {org}/{repo}[/red]"
                )
            elif org and repo:
                console.print(f"[red]No issues found for {org}/{repo}[/red]")
            elif org:
                console.print(f"[red]No issues found for organization {org}[/red]")
            else:
                console.print("[red]No issues found to process[/red]")
            return

    except Exception as e:
        console.print(f"[red]Error finding issues: {e}[/red]")
        return

    # Show what would be processed
    console.print(f"[blue]Found {len(issues)} issue(s) to process[/blue]")

    if len(issues) <= 10:
        # Show details for small batches
        for issue_data in issues:
            issue = issue_data["issue"]
            console.print(
                f"  - {org}/{repo}#{issue['number']}: {issue['title'][:60]}..."
            )
    else:
        # Show summary for large batches
        console.print(
            f"  Issues from {len(set(f'{i['org']}/{i['repo']}' for i in issues))} "
            "repositories"
        )

    if dry_run:
        console.print("[yellow]Dry run - no batch job submitted[/yellow]")
        return

    # Build AI configuration
    ai_config = build_ai_config(
        model_name=model,
        thinking_effort=thinking_effort,
        thinking_budget=thinking_budget,
    )
    # Set image processing flag
    ai_config.include_images = include_images

    console.print(f"[blue]Using model: {ai_config.model_name}[/blue]")

    # Display thinking configuration if present
    if ai_config.thinking:
        if ai_config.thinking.effort:
            console.print(f"[blue]Thinking effort: {ai_config.thinking.effort}[/blue]")
        if ai_config.thinking.budget_tokens:
            budget = ai_config.thinking.budget_tokens
            console.print(f"[blue]Thinking budget: {budget} tokens[/blue]")

    # Create and submit batch job
    try:
        console.print("[blue]Creating batch job...[/blue]")

        batch_job = await batch_manager.create_batch_job(
            processor_type=processor_type,
            org=org,
            repo=repo,
            issue_number=issue_number,
            model_config=ai_config,
        )

        console.print("[green]✓ Batch job submitted successfully![/green]")
        console.print(f"[green]Job ID: {batch_job.job_id}[/green]")
        console.print(f"[green]OpenAI Batch ID: {batch_job.openai_batch_id}[/green]")
        console.print(f"[blue]Status: {batch_job.status}[/blue]")
        console.print()
        console.print("[yellow]Check job status with:[/yellow]")
        console.print(f"  uv run github-analysis batch status {batch_job.job_id}")
        console.print()
        console.print("[yellow]Collect results when completed:[/yellow]")
        console.print(f"  uv run github-analysis batch collect {batch_job.job_id}")

    except Exception as e:
        console.print(f"[red]Failed to submit batch job: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status(job_id: str = typer.Argument(help="Batch job ID to check")) -> None:
    """Check the status of a batch processing job."""
    try:
        asyncio.run(_run_batch_status(job_id))
    except Exception as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)


async def _run_batch_status(job_id: str) -> None:
    """Run batch status check."""
    batch_manager = BatchManager()

    try:
        batch_job = await batch_manager.check_job_status(job_id)

        # Display job information
        console.print(f"[bold]Batch Job: {job_id}[/bold]")
        console.print(f"Processor: {batch_job.processor_type}")
        console.print(f"Organization: {batch_job.org}")
        if batch_job.repo:
            console.print(f"Repository: {batch_job.repo}")
        if batch_job.issue_number:
            console.print(f"Issue: #{batch_job.issue_number}")
        console.print(
            f"Created: {batch_job.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )

        if batch_job.submitted_at:
            console.print(
                f"Submitted: {batch_job.submitted_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )

        if batch_job.completed_at:
            console.print(
                f"Completed: {batch_job.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
            if batch_job.submitted_at:
                duration = batch_job.completed_at - batch_job.submitted_at
                console.print(f"Duration: {duration}")

        console.print()

        # Status with color coding
        status_color = {
            "pending": "yellow",
            "validating": "blue",
            "in_progress": "blue",
            "finalizing": "blue",
            "completed": "green",
            "failed": "red",
            "cancelled": "yellow",
        }.get(batch_job.status, "white")

        console.print(
            f"Status: [{status_color}]{batch_job.status.upper()}[/{status_color}]"
        )

        # Progress information
        console.print(f"Total items: {batch_job.total_items}")
        console.print(f"Processed: {batch_job.processed_items}")
        console.print(f"Failed: {batch_job.failed_items}")

        if batch_job.total_items > 0:
            progress_pct = (
                (batch_job.processed_items + batch_job.failed_items)
                / batch_job.total_items
                * 100
            )
            console.print(f"Progress: {progress_pct:.1f}%")

        # OpenAI information
        if batch_job.openai_batch_id:
            console.print(f"OpenAI Batch ID: {batch_job.openai_batch_id}")

        # Error information
        if batch_job.errors:
            console.print(f"\n[red]Errors ({len(batch_job.errors)}):[/red]")
            for error in batch_job.errors[:5]:  # Show first 5 errors
                console.print(f"  {error.custom_id}: {error.error_message}")
            if len(batch_job.errors) > 5:
                console.print(f"  ... and {len(batch_job.errors) - 5} more errors")

        # Next steps
        if batch_job.status == "completed":
            console.print("\n[green]✓ Job completed! Collect results with:[/green]")
            console.print(f"  uv run github-analysis batch collect {job_id}")
        elif batch_job.status in ["pending", "validating", "in_progress", "finalizing"]:
            console.print("\n[blue]Job is still processing. Check again later.[/blue]")
        elif batch_job.status == "failed":
            console.print(
                "\n[red]Job failed. Check the errors above for details.[/red]"
            )

    except ValueError as e:
        console.print(f"[red]Job not found: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def collect(
    job_id: str = typer.Argument(help="Batch job ID to collect results from"),
) -> None:
    """Collect and process results from a completed batch job."""
    try:
        asyncio.run(_run_batch_collect(job_id))
    except Exception as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)


async def _run_batch_collect(job_id: str) -> None:
    """Run batch result collection."""
    batch_manager = BatchManager()

    try:
        console.print(f"[blue]Collecting results for job {job_id}...[/blue]")

        batch_result = await batch_manager.collect_results(job_id)

        # Display results summary
        console.print("\n[bold]Batch Results Summary[/bold]")
        console.print(f"Job ID: {batch_result.job_id}")
        console.print(f"Processor: {batch_result.processor_type}")
        console.print(f"Total items: {batch_result.total_items}")
        console.print(f"Successful: [green]{batch_result.successful_items}[/green]")
        console.print(f"Failed: [red]{batch_result.failed_items}[/red]")

        if batch_result.processing_time:
            console.print(
                f"Processing time: {batch_result.processing_time:.1f} seconds"
            )

        success_rate = batch_result.successful_items / batch_result.total_items * 100
        console.print(f"Success rate: {success_rate:.1f}%")

        console.print(f"Results saved to: {batch_result.results_directory}")

        # Show errors if any
        if batch_result.errors:
            console.print(f"\n[red]Errors ({len(batch_result.errors)}):[/red]")
            for error in batch_result.errors[:5]:  # Show first 5 errors
                console.print(f"  {error.custom_id}: {error.error_message}")
            if len(batch_result.errors) > 5:
                console.print(f"  ... and {len(batch_result.errors) - 5} more errors")

        # Cost savings information (placeholder for future)
        if batch_result.cost_estimate:
            console.print(f"\nEstimated cost: ${batch_result.cost_estimate:.4f}")
            console.print("[green]50% savings vs real-time processing![/green]")

        console.print("\n[green]✓ Results collection completed![/green]")

    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@app.command(name="list")
def list_jobs() -> None:
    """List all batch processing jobs."""
    try:
        asyncio.run(_run_batch_list())
    except Exception as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)


async def _run_batch_list() -> None:
    """Run batch job listing."""
    batch_manager = BatchManager()

    try:
        jobs = await batch_manager.list_jobs()

        if not jobs:
            console.print("[yellow]No batch jobs found.[/yellow]")
            return

        # Create table
        table = Table(title=f"Batch Jobs ({len(jobs)} total)")
        table.add_column("Job ID", style="blue")
        table.add_column("Processor", style="cyan")
        table.add_column("Scope", style="magenta")
        table.add_column("Status", style="white")
        table.add_column("Items", justify="right")
        table.add_column("Success", justify="right", style="green")
        table.add_column("Failed", justify="right", style="red")
        table.add_column("Created", style="dim")

        for job in jobs:
            # Format scope
            if job.issue_number:
                scope = f"{job.org}/{job.repo}#{job.issue_number}"
            elif job.repo:
                scope = f"{job.org}/{job.repo}"
            elif job.org:
                scope = f"{job.org}/*"
            else:
                scope = "*/*"

            # Format status with color
            status_map = {
                "pending": "[yellow]PENDING[/yellow]",
                "validating": "[blue]VALIDATING[/blue]",
                "in_progress": "[blue]RUNNING[/blue]",
                "finalizing": "[blue]FINALIZING[/blue]",
                "completed": "[green]COMPLETED[/green]",
                "failed": "[red]FAILED[/red]",
                "cancelled": "[yellow]CANCELLED[/yellow]",
            }
            status_display = status_map.get(job.status, job.status.upper())

            # Format created time
            created_display = job.created_at.strftime("%m/%d %H:%M")

            table.add_row(
                job.job_id[:8] + "...",  # Truncated job ID
                job.processor_type,
                scope,
                status_display,
                str(job.total_items),
                str(job.processed_items),
                str(job.failed_items),
                created_display,
            )

        console.print(table)

        # Show helpful commands
        console.print("\n[dim]Commands:[/dim]")
        console.print(
            "  [dim]Check status:[/dim] uv run github-analysis batch status <job-id>"
        )
        console.print(
            "  [dim]Collect results:[/dim] "
            "uv run github-analysis batch collect <job-id>"
        )
        console.print(
            "  [dim]Cancel job:[/dim] uv run github-analysis batch cancel <job-id>"
        )
        console.print(
            "  [dim]Remove job:[/dim] uv run github-analysis batch remove <job-id>"
        )

    except Exception as e:
        console.print(f"[red]Failed to list jobs: {e}[/red]")
        raise


@app.command()
def cancel(job_id: str = typer.Argument(help="Batch job ID to cancel")) -> None:
    """Cancel an active batch processing job."""
    try:
        asyncio.run(_run_batch_cancel(job_id))
    except Exception as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)


async def _run_batch_cancel(job_id: str) -> None:
    """Run batch job cancellation."""
    batch_manager = BatchManager()

    try:
        console.print(f"[blue]Cancelling batch job {job_id}...[/blue]")

        batch_job = await batch_manager.cancel_job(job_id)

        console.print("[green]✓ Batch job cancelled successfully![/green]")
        console.print(f"[blue]Job ID: {batch_job.job_id}[/blue]")
        console.print(f"[blue]Status: {batch_job.status}[/blue]")

    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@app.command()
def remove(
    job_id: str = typer.Argument(help="Batch job ID to remove"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompts"),
) -> None:
    """Remove a batch job record and associated files."""
    try:
        _run_batch_remove(job_id, force)
    except Exception as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)


def _run_batch_remove(job_id: str, force: bool) -> None:
    """Run batch job removal."""
    batch_manager = BatchManager()

    try:
        console.print(f"[blue]Removing batch job {job_id}...[/blue]")

        removed = batch_manager.remove_job(job_id, force)

        if not removed:
            # User cancelled the operation
            raise typer.Exit(0)

    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
