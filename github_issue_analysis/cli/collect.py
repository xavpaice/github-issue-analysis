"""CLI command for collecting GitHub issues."""

import typer
from rich.console import Console
from rich.table import Table

from ..github_client.client import GitHubClient
from ..github_client.models import GitHubIssue
from ..github_client.search import GitHubSearcher
from ..storage.manager import StorageManager

console = Console()
app = typer.Typer(help="Collect GitHub issues and store them locally")


@app.command()
def collect(
    org: str = typer.Option(..., "--org", "-o", help="GitHub organization name"),
    repo: str | None = typer.Option(
        None,
        "--repo",
        "-r",
        help="GitHub repository name (optional for org-wide search)",
    ),
    issue_number: int | None = typer.Option(
        None, "--issue-number", help="Specific issue number to collect"
    ),
    labels: list[str] | None = typer.Option(
        None, "--labels", "-l", help="Filter by labels (can be used multiple times)"
    ),
    limit: int = typer.Option(
        10, "--limit", help="Maximum number of issues to collect"
    ),
    state: str = typer.Option(
        "closed", "--state", help="Issue state: open, closed, or all"
    ),
    token: str | None = typer.Option(
        None, "--token", help="GitHub API token (defaults to GITHUB_TOKEN env var)"
    ),
) -> None:
    """Collect GitHub issues and save them locally.

    Collection modes:
    - Single issue: --org ORGNAME --repo REPONAME --issue-number NUMBER
    - Organization-wide: --org ORGNAME (searches all repos in org)
    - Repository-specific: --org ORGNAME --repo REPONAME (existing behavior)

    Examples:
        github-analysis collect --org replicated-collab --repo pixee-replicated \\
            --issue-number 71
        github-analysis collect --org replicated-collab --limit 20
        github-analysis collect --org microsoft --repo vscode --labels bug --limit 5
    """
    # Parameter validation
    if issue_number is not None:
        # Single issue mode - requires both org and repo
        if repo is None:
            console.print(
                "❌ Error: --issue-number requires both --org and --repo parameters"
            )
            raise typer.Exit(1)
        collection_mode = "single_issue"
        console.print(f"🔍 Collecting single issue #{issue_number} from {org}/{repo}")
    elif repo is None:
        # Organization-wide mode - only org provided
        collection_mode = "organization"
        console.print(f"🔍 Collecting issues from organization {org}")
    else:
        # Repository-specific mode - both org and repo provided
        collection_mode = "repository"
        console.print(f"🔍 Collecting issues from {org}/{repo}")

    # Show collection parameters
    params_table = Table(title="Collection Parameters")
    params_table.add_column("Parameter", style="cyan")
    params_table.add_column("Value", style="green")

    params_table.add_row("Mode", collection_mode.replace("_", " ").title())
    params_table.add_row("Organization", org)
    if repo:
        params_table.add_row("Repository", repo)
    if issue_number is not None:
        params_table.add_row("Issue Number", str(issue_number))
    params_table.add_row("Labels", ", ".join(labels) if labels else "All")
    params_table.add_row("State", state)
    if collection_mode != "single_issue":
        params_table.add_row("Limit", str(limit))

    console.print(params_table)

    try:
        # Initialize GitHub client
        console.print("🔑 Initializing GitHub client...")
        client = GitHubClient(token=token)
        searcher = GitHubSearcher(client)

        # Collect issues based on mode
        console.print("🔎 Searching for issues...")
        if collection_mode == "single_issue":
            # Single issue collection
            assert repo is not None  # guaranteed by validation above
            assert issue_number is not None  # guaranteed by validation above
            issue = searcher.get_single_issue(org, repo, issue_number)
            issues = [issue]
        elif collection_mode == "organization":
            # Organization-wide search
            issues = searcher.search_organization_issues(
                org=org, labels=labels, state=state, limit=limit
            )
        else:
            # Repository-specific search
            assert repo is not None  # guaranteed by validation above
            issues = searcher.search_repository_issues(
                org=org, repo=repo, labels=labels, state=state, limit=limit
            )

        if not issues:
            console.print("❌ No issues found matching the criteria")
            return

        console.print(f"✅ Found {len(issues)} issues")

        # Initialize storage manager
        storage = StorageManager()

        # Save issues - for organization-wide search, group by repository
        console.print("💾 Saving issues to storage...")
        if collection_mode == "organization":
            # For organization-wide search, group issues by repository and save
            issues_by_repo: dict[str, list[GitHubIssue]] = {}
            for issue in issues:
                issue_repo = issue.repository_name or "unknown_repo"
                if issue_repo not in issues_by_repo:
                    issues_by_repo[issue_repo] = []
                issues_by_repo[issue_repo].append(issue)

            # Save issues grouped by repository
            saved_paths = []
            for repo_name, repo_issues in issues_by_repo.items():
                paths = storage.save_issues(org, repo_name, repo_issues)
                saved_paths.extend(paths)
        else:
            # Single issue or repository-specific - use the provided repo name
            assert repo is not None  # guaranteed by validation above
            saved_paths = storage.save_issues(org, repo, issues)

        # Show results
        results_table = Table(title="Collection Results")
        results_table.add_column("Issue #", style="cyan")
        if collection_mode == "organization":
            results_table.add_column("Repository", style="magenta")
        results_table.add_column("Title", style="white")
        results_table.add_column("State", style="green")
        results_table.add_column("Comments", justify="right", style="yellow")

        for issue in issues:
            row_data = [str(issue.number)]
            if collection_mode == "organization":
                row_data.append(issue.repository_name or "unknown")
            row_data.extend(
                [
                    issue.title[:50] + "..." if len(issue.title) > 50 else issue.title,
                    issue.state,
                    str(len(issue.comments)),
                ]
            )
            results_table.add_row(*row_data)

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
