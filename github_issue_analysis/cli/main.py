"""Main CLI entry point."""

import typer
from rich.console import Console

from . import batch, process, recommendations
from .collect import collect, status
from .update import update_labels

app = typer.Typer(
    name="github-analysis", help="GitHub issue collection and AI analysis"
)
console = Console()

app.command()(collect)
app.command()(status)
app.command(name="update-labels")(update_labels)
app.add_typer(process.app, name="process")
app.add_typer(batch.app, name="batch")
app.add_typer(recommendations.app, name="recommendations")


@app.command()
def version() -> None:
    """Show version information."""
    from github_issue_analysis import __version__

    console.print(f"GitHub Issue Analysis v{__version__}")


if __name__ == "__main__":
    app()
