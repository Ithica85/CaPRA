"""Pretty console output + timestamped JSON export."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from agent.config import slugify_niche
from agent.models import ResearchResult

logger = logging.getLogger(__name__)
console = Console()


def print_results(result: ResearchResult) -> None:
    """Pretty-print the research run to the terminal."""
    console.print()
    console.rule("[bold cyan]Customer Pain Research Agent[/bold cyan]")
    header = Text()
    header.append("Niche: ", style="bold")
    header.append(f"{result.niche}\n")
    header.append("Subreddits: ", style="bold")
    header.append(f"{', '.join(result.subreddits)}\n")
    header.append("Collector: ", style="bold")
    header.append(f"{result.collector_used}  ")
    header.append("LLM: ", style="bold")
    header.append(f"{result.llm_provider}/{result.llm_model}\n")
    header.append("Posts collected/analyzed: ", style="bold")
    header.append(f"{result.posts_collected}/{result.posts_analyzed}  ")
    header.append("Time filter: ", style="bold")
    header.append(f"{result.time_filter}  ")
    header.append("Generated: ", style="bold")
    header.append(result.generated_at)
    console.print(Panel(header, title="Run metadata", border_style="cyan"))

    if result.summary:
        console.print(
            Panel(result.summary, title="Executive summary", border_style="green")
        )

    if not result.top_pains:
        console.print(
            "[yellow]No pain points extracted. Try broader keywords, more "
            "subreddits, or a wider time filter.[/yellow]"
        )
        return

    for pain in result.top_pains:
        title = f"#{pain.rank}  {pain.title}  [intensity {pain.intensity_score}/100]"
        body = Text()
        body.append("Category: ", style="bold dim")
        body.append(f"{pain.category}\n")
        body.append("Description: ", style="bold")
        body.append(f"{pain.description}\n\n")
        body.append("Desired outcome: ", style="bold green")
        body.append(f"{pain.desired_outcome}\n\n")

        scores = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
        scores.add_column("Frequency")
        scores.add_column("Upvotes")
        scores.add_column("Emotion")
        scores.add_column("Recency")
        scores.add_column("Intensity")
        scores.add_row(
            str(pain.frequency),
            str(pain.upvote_signal),
            str(pain.emotional_language_score),
            str(pain.recency_score),
            f"[bold]{pain.intensity_score}[/bold]",
        )
        console.print(Panel(body, title=title, border_style="magenta"))
        console.print(scores)

        if pain.evidence:
            console.print("[bold]Evidence:[/bold]")
            for ev in pain.evidence:
                quote = ev.quote.replace("\n", " ").strip()
                if len(quote) > 280:
                    quote = quote[:277] + "..."
                console.print(f'  • [italic]"{quote}"[/italic]')
                meta = f"    r/{ev.subreddit}" if ev.subreddit else "   "
                if ev.upvotes:
                    meta += f" · ↑{ev.upvotes}"
                meta += f" · {ev.source_type}"
                if ev.url:
                    meta += f"\n    {ev.url}"
                console.print(f"[dim]{meta}[/dim]")
        console.print()

    console.rule("[dim]end of report[/dim]")


def save_json(result: ResearchResult, output_dir: Path) -> Path:
    """
    Save structured results to output/pains_<niche>_<date>.json

    Filename uses niche slug + UTC date so scheduled runs don't clobber each other
    within a day we also append time if file exists.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify_niche(result.niche)
    day = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    path = output_dir / f"pains_{slug}_{day}.json"
    if path.exists():
        stamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        path = output_dir / f"pains_{slug}_{stamp}.json"

    payload = result.to_export_dict()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    logger.info("Wrote results → %s", path)
    console.print(f"[bold green]✓ Saved JSON:[/bold green] {path}")
    return path


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^\w\-.]+", "_", name).strip("_")
