"""Main CLI entry point."""

import typer
from rich.console import Console

from . import batch, process
from .collect import collect, status

app = typer.Typer(
    name="github-analysis", help="GitHub issue collection and AI analysis"
)
console = Console()

app.command()(collect)
app.command()(status)
app.add_typer(process.app, name="process")
app.add_typer(batch.app, name="batch")


@app.command()
def version() -> None:
    """Show version information."""
    from github_issue_analysis import __version__

    console.print(f"GitHub Issue Analysis v{__version__}")


if __name__ == "__main__":
    app()
