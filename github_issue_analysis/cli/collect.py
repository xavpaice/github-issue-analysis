"""CLI command for collecting GitHub issues."""

import typer
from rich.console import Console
from rich.table import Table

from ..github_client.client import GitHubClient
from ..github_client.search import GitHubSearcher
from ..storage.manager import StorageManager

console = Console()
app = typer.Typer(help="Collect GitHub issues and store them locally")


@app.command()
def collect(
    org: str = typer.Option(..., "--org", "-o", help="GitHub organization name"),
    repo: str = typer.Option(..., "--repo", "-r", help="GitHub repository name"),
    labels: list[str] | None = typer.Option(
        None, "--labels", "-l", help="Filter by labels (can be used multiple times)"
    ),
    limit: int = typer.Option(
        10, "--limit", help="Maximum number of issues to collect"
    ),
    state: str = typer.Option(
        "open", "--state", help="Issue state: open, closed, or all"
    ),
    token: str | None = typer.Option(
        None, "--token", help="GitHub API token (defaults to GITHUB_TOKEN env var)"
    ),
) -> None:
    """Collect GitHub issues from a repository and save them locally.

    Examples:
        github-analysis collect --org microsoft --repo vscode --labels bug --limit 5
        github-analysis collect --org pytorch --repo pytorch --state all --limit 20
    """
    console.print(f"🔍 Collecting issues from {org}/{repo}")

    # Show collection parameters
    params_table = Table(title="Collection Parameters")
    params_table.add_column("Parameter", style="cyan")
    params_table.add_column("Value", style="green")

    params_table.add_row("Organization", org)
    params_table.add_row("Repository", repo)
    params_table.add_row("Labels", ", ".join(labels) if labels else "All")
    params_table.add_row("State", state)
    params_table.add_row("Limit", str(limit))

    console.print(params_table)

    try:
        # Initialize GitHub client
        console.print("🔑 Initializing GitHub client...")
        client = GitHubClient(token=token)
        searcher = GitHubSearcher(client)

        # Search for issues
        console.print("🔎 Searching for issues...")
        issues = searcher.search_repository_issues(
            org=org, repo=repo, labels=labels, state=state, limit=limit
        )

        if not issues:
            console.print("❌ No issues found matching the criteria")
            return

        console.print(f"✅ Found {len(issues)} issues")

        # Initialize storage manager
        storage = StorageManager()

        # Save issues
        console.print("💾 Saving issues to storage...")
        saved_paths = storage.save_issues(org, repo, issues)

        # Show results
        results_table = Table(title="Collection Results")
        results_table.add_column("Issue #", style="cyan")
        results_table.add_column("Title", style="white")
        results_table.add_column("State", style="green")
        results_table.add_column("Comments", justify="right", style="yellow")

        for issue in issues:
            results_table.add_row(
                str(issue.number),
                issue.title[:50] + "..." if len(issue.title) > 50 else issue.title,
                issue.state,
                str(len(issue.comments)),
            )

        console.print(results_table)

        # Show storage info
        stats = storage.get_storage_stats()
        console.print(f"📊 Total issues in storage: {stats['total_issues']}")
        console.print(f"💿 Storage size: {stats['total_size_mb']} MB")
        console.print(f"📁 Storage location: {stats['storage_path']}")

        console.print(f"✨ Successfully collected and saved {len(saved_paths)} issues!")

    except ValueError as e:
        console.print(f"❌ Error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}")
        console.print("Please check your GitHub token and network connection.")
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """Show storage status and statistics."""
    console.print("📊 Storage Status")

    storage = StorageManager()
    stats = storage.get_storage_stats()

    # Overall stats
    stats_table = Table(title="Storage Statistics")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")

    stats_table.add_row("Total Issues", str(stats["total_issues"]))
    stats_table.add_row("Storage Size", f"{stats['total_size_mb']} MB")
    stats_table.add_row("Storage Path", stats["storage_path"])

    console.print(stats_table)

    # Repository breakdown
    if stats["repositories"]:
        repo_table = Table(title="Issues by Repository")
        repo_table.add_column("Repository", style="cyan")
        repo_table.add_column("Issue Count", justify="right", style="green")

        for repo, count in sorted(stats["repositories"].items()):
            repo_table.add_row(repo, str(count))

        console.print(repo_table)
    else:
        console.print("No issues found in storage.")


if __name__ == "__main__":
    app()
