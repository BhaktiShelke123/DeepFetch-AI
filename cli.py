"""DeepFetch AI — CLI Interface.

Usage:
    python cli.py ingest              # Ingest documents from data/ folder
    python cli.py ask "your question" # Ask a question
    python cli.py status              # Check index status
    python cli.py clear               # Clear the index
"""

import logging
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from config import config

console = Console()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-30s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)


@click.group()
def cli():
    """DeepFetch AI — Document Intelligence Engine"""
    pass


@cli.command()
@click.option(
    "--directory", "-d",
    default=config.DATA_DIR,
    help="Directory containing documents to ingest",
)
def ingest(directory: str):
    """Ingest documents from the data/ folder."""
    from agents.ingestion import ingest_directory

    console.print(f"\n[bold]Ingesting documents from:[/bold] {directory}\n")

    try:
        results = ingest_directory(directory)
    except FileNotFoundError:
        console.print(f"[red]Directory not found: {directory}[/red]")
        console.print("Create the directory and add your PDF/DOCX/TXT files.")
        sys.exit(1)

    if not results:
        console.print("[yellow]No supported documents found.[/yellow]")
        console.print("Supported formats: .pdf, .docx, .txt, .md")
        return

    # Show results table
    table = Table(title="Ingested Documents")
    table.add_column("File", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Pages", justify="right")
    table.add_column("Chunks", justify="right", style="bold")

    total_chunks = 0
    for doc in results:
        table.add_row(
            doc.filename,
            doc.file_type,
            str(doc.total_pages or "—"),
            str(doc.total_chunks),
        )
        total_chunks += doc.total_chunks

    console.print(table)
    console.print(
        f"\n[green]✓[/green] {len(results)} documents → "
        f"{total_chunks} chunks indexed\n"
    )


@cli.command()
@click.argument("question")
def ask(question: str):
    """Ask a question about your documents."""
    from orchestrator.graph import run_query
    from vectorstore.faiss_store import get_faiss_store

    store = get_faiss_store()
    if store.size == 0:
        console.print(
            "[red]No documents ingested.[/red] "
            "Run [bold]python cli.py ingest[/bold] first."
        )
        sys.exit(1)

    console.print(f"\n[bold]Question:[/bold] {question}\n")

    with console.status("[bold green]Thinking..."):
        result = run_query(question)

    # ── Display answer ───────────────────────────────────────────────
    confidence_color = {
        "high": "green",
        "medium": "yellow",
        "low": "red",
    }.get(result.confidence_level.value if result.confidence_level else "low", "red")

    answer_panel = Panel(
        result.answer or "No answer generated.",
        title="[bold]Answer[/bold]",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(answer_panel)

    # ── Citations ────────────────────────────────────────────────────
    if result.citations:
        citation_table = Table(title="Citations")
        citation_table.add_column("#", style="bold", width=3)
        citation_table.add_column("Source", style="cyan")
        citation_table.add_column("Page", justify="right", width=6)
        citation_table.add_column("Quoted Text", style="dim")

        for c in result.citations:
            citation_table.add_row(
                str(c.citation_id),
                c.source_document,
                str(c.page_number or "—"),
                c.quoted_text[:80] + "..." if len(c.quoted_text) > 80 else c.quoted_text,
            )
        console.print(citation_table)

    # ── Metadata ─────────────────────────────────────────────────────
    meta = Text()
    meta.append(f"Intent: {result.intent.value if result.intent else '?'}  │  ")
    meta.append(f"Confidence: ")
    meta.append(
        f"{result.confidence_score:.0%}",
        style=f"bold {confidence_color}",
    )
    meta.append(f"  │  Latency: {result.latency_ms:.0f}ms")

    if result.hallucination_flags:
        meta.append(f"\n⚠ Flags: {', '.join(result.hallucination_flags)}")

    console.print(Panel(meta, title="Metadata", border_style="dim"))
    console.print()


@cli.command()
def status():
    """Check the current index status."""
    from vectorstore.faiss_store import get_faiss_store

    store = get_faiss_store()

    console.print(f"\n[bold]DeepFetch AI — Index Status[/bold]\n")
    console.print(f"  Index size:  [cyan]{store.size}[/cyan] vectors")
    console.print(f"  Documents:   [cyan]{len(store.document_names)}[/cyan]")

    if store.document_names:
        console.print(f"\n  [bold]Indexed documents:[/bold]")
        for name in sorted(store.document_names):
            console.print(f"    • {name}")

    console.print()


@cli.command()
@click.confirmation_option(prompt="This will delete the entire index. Continue?")
def clear():
    """Clear the FAISS index."""
    from vectorstore.faiss_store import get_faiss_store

    store = get_faiss_store()
    store.clear()
    store.save()
    console.print("[green]✓ Index cleared.[/green]\n")


if __name__ == "__main__":
    cli()
