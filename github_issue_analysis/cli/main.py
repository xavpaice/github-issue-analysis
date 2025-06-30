"""Main CLI entry point."""

import typer
from rich.console import Console

app = typer.Typer(name="github-analysis", help="GitHub issue collection and AI analysis")
console = Console()

# Import subcommands when implemented
# from . import collect, process
# app.add_typer(collect.app, name="collect")
# app.add_typer(process.app, name="process")

@app.command()
def version() -> None:
    """Show version information."""
    from github_issue_analysis import __version__
    console.print(f"GitHub Issue Analysis v{__version__}")

if __name__ == "__main__":
    app()