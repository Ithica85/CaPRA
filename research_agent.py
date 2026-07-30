#!/usr/bin/env python3
"""
Customer Pain Research Agent — CLI entrypoint.

Prefer the browser UI for day-to-day use:
  double-click start_ui.command
  or: streamlit run app.py

CLI still works for cron / automation:
  python research_agent.py --dry-run
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

from agent.config import (
    DEFAULT_KEYWORDS,
    DEFAULT_MAX_POSTS,
    DEFAULT_NICHE,
    DEFAULT_SUBREDDITS,
    DEFAULT_TIME_FILTER,
    DEFAULT_TOP_N,
    Settings,
)
from agent.output import print_results
from agent.pipeline import ResearchRequest, run_research

console = Console()


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
    )
    for name in ("httpx", "httpcore", "urllib3", "openai", "anthropic"):
        logging.getLogger(name).setLevel(logging.WARNING)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Customer Pain Research Agent — Reddit → ranked top-5 pains",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--niche", type=str, default=DEFAULT_NICHE)
    p.add_argument("--subreddits", nargs="+", default=DEFAULT_SUBREDDITS)
    p.add_argument("--keywords", nargs="+", default=DEFAULT_KEYWORDS)
    p.add_argument("--max-posts", type=int, default=DEFAULT_MAX_POSTS)
    p.add_argument(
        "--time-filter",
        type=str,
        default=DEFAULT_TIME_FILTER,
        choices=["hour", "day", "week", "month", "year", "all"],
    )
    p.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    p.add_argument(
        "--collector",
        type=str,
        default="auto",
        choices=["auto", "apify", "praw", "demo"],
    )
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--skip-llm", action="store_true")
    p.add_argument("--output-dir", type=str, default=None)
    p.add_argument(
        "--log-level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return p.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    if args.log_level:
        settings.log_level = args.log_level
    setup_logging(settings.log_level)

    console.print(
        f"\n[bold cyan]Customer Pain Research Agent[/bold cyan]  "
        f"[dim]niche=[/dim]{args.niche}"
    )

    req = ResearchRequest(
        niche=args.niche,
        subreddits=list(args.subreddits),
        keywords=list(args.keywords),
        max_posts=args.max_posts,
        time_filter=args.time_filter,
        top_n=args.top_n,
        collector=args.collector,
        dry_run=args.dry_run or args.collector == "demo",
        skip_llm=args.skip_llm,
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )

    response = run_research(req)
    if not response.ok:
        console.print(f"[bold red]Error:[/bold red] {response.error}")
        if response.error_code == 2:
            console.print(
                "[dim]Tip: use the web UI (start_ui.command), or set keys in .env, "
                "or pass --dry-run.[/dim]"
            )
        return response.error_code or 1

    if response.result:
        if not response.result.top_pains:
            console.print(
                "[yellow]No pain points extracted. Broaden keywords or subreddits.[/yellow]"
            )
        print_results(response.result)

    console.print(
        "\n[bold green]Done.[/bold green] Feed the JSON into your creative/ad agent next."
    )
    return 0


def main() -> None:
    args = parse_args()
    try:
        code = run(args)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        code = 130
    sys.exit(code)


if __name__ == "__main__":
    main()
