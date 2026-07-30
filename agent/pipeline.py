"""
Shared research pipeline used by the CLI and the web UI.

run_research() does collect → filter → LLM rank → ResearchResult.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from agent.analyzer import extract_and_rank_pains
from agent.collectors import get_collector
from agent.config import (
    DEFAULT_KEYWORDS,
    DEFAULT_MAX_POSTS,
    DEFAULT_NICHE,
    DEFAULT_SUBREDDITS,
    DEFAULT_TIME_FILTER,
    DEFAULT_TOP_N,
    Settings,
)
from agent.filters import filter_complaint_posts
from agent.llm import LLMClient, LLMError
from agent.models import ResearchResult
from agent.output import save_json

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str], None]


@dataclass
class ResearchRequest:
    niche: str = DEFAULT_NICHE
    subreddits: list[str] = field(default_factory=lambda: list(DEFAULT_SUBREDDITS))
    keywords: list[str] = field(default_factory=lambda: list(DEFAULT_KEYWORDS))
    max_posts: int = DEFAULT_MAX_POSTS
    time_filter: str = DEFAULT_TIME_FILTER
    top_n: int = DEFAULT_TOP_N
    collector: str = "auto"  # auto | apify | praw | demo
    dry_run: bool = False
    skip_llm: bool = False
    output_dir: Path | None = None
    # Optional API keys (override env for this run — handy from the UI)
    apify_token: str | None = None
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    perplexity_api_key: str | None = None
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str | None = None
    # When True, empty key fields CLEAR ambient env vars (so a bad system key
    # can't silently win). Used by the web UI.
    clear_empty_keys: bool = False
    # Force a provider: auto | anthropic | openai | perplexity
    llm_provider: str = "auto"


@dataclass
class ResearchResponse:
    ok: bool
    result: ResearchResult | None = None
    json_path: Path | None = None
    error: str | None = None
    error_code: int = 0


def _apply_key_overrides(req: ResearchRequest) -> None:
    """
    Push UI-provided keys into the process environment for this run.

    If clear_empty_keys is True, blank fields remove ambient env keys so a
    bad OPENAI_API_KEY from the shell/IDE cannot override a fresh paste.
    """
    mapping = {
        "APIFY_TOKEN": req.apify_token,
        "ANTHROPIC_API_KEY": req.anthropic_api_key,
        "OPENAI_API_KEY": req.openai_api_key,
        "PERPLEXITY_API_KEY": req.perplexity_api_key,
        "REDDIT_CLIENT_ID": req.reddit_client_id,
        "REDDIT_CLIENT_SECRET": req.reddit_client_secret,
        "REDDIT_USER_AGENT": req.reddit_user_agent,
    }
    for env_key, value in mapping.items():
        if value is None:
            continue
        stripped = str(value).strip()
        if stripped:
            os.environ[env_key] = stripped
        elif req.clear_empty_keys:
            os.environ.pop(env_key, None)

    # Optional provider pin — unset the other LLM keys so resolve_llm is unambiguous
    provider = (req.llm_provider or "auto").lower()
    if provider == "anthropic":
        # Keep only Anthropic for resolution
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "LLM provider set to Anthropic, but no ANTHROPIC_API_KEY was provided."
            )
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("PERPLEXITY_API_KEY", None)
    elif provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "LLM provider set to OpenAI, but no OPENAI_API_KEY was provided."
            )
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ.pop("PERPLEXITY_API_KEY", None)
    elif provider == "perplexity":
        if not os.getenv("PERPLEXITY_API_KEY"):
            raise RuntimeError(
                "LLM provider set to Perplexity, but no PERPLEXITY_API_KEY was provided."
            )
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY", None)


def _friendly_llm_error(message: str) -> str:
    """Turn provider 401/403 noise into actionable UI guidance."""
    lower = message.lower()
    if "401" in lower or "invalid_api_key" in lower or "incorrect api key" in lower:
        return (
            "Your LLM API key was rejected (invalid or expired).\n\n"
            "Fix it like this:\n"
            "1. Open the sidebar → API keys\n"
            "2. Click “Clear LLM keys from this session”\n"
            "3. Paste a fresh key from the provider dashboard\n"
            "   • OpenAI: https://platform.openai.com/api-keys\n"
            "   • Anthropic: https://console.anthropic.com/\n"
            "4. Choose that provider under “Which LLM to use?”\n"
            "5. Run research again\n\n"
            f"Technical detail: {message}"
        )
    if "403" in lower or "permission" in lower:
        return (
            "Your LLM API key does not have permission for this model. "
            "Check billing/access on the provider dashboard, or try another key.\n\n"
            f"Technical detail: {message}"
        )
    if "credit" in lower or "billing" in lower or "quota" in lower or "insufficient" in lower:
        return (
            "Your LLM account is out of credits or billing is not set up. "
            "Add billing/credits on the provider site, then retry.\n\n"
            f"Technical detail: {message}"
        )
    return f"LLM failed: {message}"


def _heuristic_pains(posts, top_n, keywords):
    from agent.filters import highlight_emotional_score
    from agent.models import Evidence, PainPoint

    ranked = sorted(posts, key=lambda p: p.score + p.num_comments, reverse=True)
    pains = []
    for i, post in enumerate(ranked[:top_n], start=1):
        emotion = highlight_emotional_score(post.text_blob)
        pains.append(
            PainPoint(
                rank=i,
                title=(post.title or "Untitled pain")[:120],
                description=(post.body or post.title or "")[:400],
                desired_outcome="(Heuristic mode — enable LLM for real outcomes)",
                intensity_score=min(100, max(10, int(post.score / 5) + emotion // 2)),
                frequency=1,
                emotional_language_score=emotion,
                recency_score=60,
                upvote_signal=post.score,
                category="other",
                evidence=[
                    Evidence(
                        quote=(post.body or post.title or "")[:300],
                        url=post.url,
                        subreddit=post.subreddit,
                        upvotes=post.score,
                        source_type="post",
                    )
                ],
                keywords_matched=[
                    k for k in keywords if k.lower() in post.text_blob.lower()
                ],
            )
        )
    summary = "Heuristic stub report (LLM skipped). Re-run with an LLM key for real analysis."
    return pains, summary


def run_research(
    req: ResearchRequest,
    progress: ProgressCallback | None = None,
) -> ResearchResponse:
    """
    Execute a full research job.

    progress: optional callback for UI status messages, e.g. progress("Collecting…")
    """

    def note(msg: str) -> None:
        logger.info(msg)
        if progress:
            progress(msg)

    try:
        _apply_key_overrides(req)
    except RuntimeError as exc:
        return ResearchResponse(ok=False, error=str(exc), error_code=5)

    settings = Settings.from_env()

    if req.dry_run or req.collector == "demo":
        settings.dry_run = True
    if req.collector in ("apify", "praw"):
        settings.prefer_collector = req.collector
    if req.output_dir is not None:
        settings.output_dir = Path(req.output_dir)

    niche = (req.niche or DEFAULT_NICHE).strip()
    subreddits = [s.lstrip("r/").strip() for s in req.subreddits if s.strip()]
    keywords = [k.strip() for k in req.keywords if k.strip()]
    max_posts = max(10, int(req.max_posts or DEFAULT_MAX_POSTS))
    time_filter = req.time_filter or DEFAULT_TIME_FILTER
    top_n = max(1, min(20, int(req.top_n or DEFAULT_TOP_N)))

    if not subreddits:
        return ResearchResponse(ok=False, error="Add at least one subreddit.", error_code=2)
    if not keywords:
        return ResearchResponse(ok=False, error="Add at least one keyword.", error_code=2)

    # ----- Collect -----
    try:
        collector = get_collector(settings)
        collector_name = settings.resolve_collector()
    except RuntimeError as exc:
        return ResearchResponse(
            ok=False,
            error=str(exc),
            error_code=2,
        )

    note(f"Collecting Reddit data via {collector_name}…")
    try:
        posts = collector.collect(subreddits, keywords, max_posts, time_filter)
    except Exception as exc:
        logger.exception("Collection failed")
        return ResearchResponse(
            ok=False,
            error=f"Collection failed: {exc}",
            error_code=3,
        )

    posts_collected = len(posts)
    if posts_collected == 0:
        return ResearchResponse(
            ok=False,
            error="No posts collected. Try different subreddits/keywords or a wider time filter.",
            error_code=4,
        )
    note(f"Collected {posts_collected} posts. Filtering for complaints…")

    # ----- Filter -----
    filtered = filter_complaint_posts(posts, keywords)
    if not filtered:
        note("Filter removed all posts — using top posts by score instead")
        filtered = sorted(posts, key=lambda p: p.score, reverse=True)[:max_posts]
    filtered = filtered[:max_posts]
    note(f"Analyzing {len(filtered)} posts…")

    # ----- LLM -----
    llm_provider, llm_model = "none", "none"
    summary = ""
    pains = []

    if req.skip_llm:
        note("Skipping LLM (heuristic mode)…")
        pains, summary = _heuristic_pains(filtered, top_n, keywords)
    else:
        try:
            llm = LLMClient(settings)
            llm_provider, llm_model = llm.provider, llm.model
            note(f"Ranking pains with {llm_provider}/{llm_model}…")
            pains, summary = extract_and_rank_pains(
                llm, filtered, niche, keywords, top_n=top_n
            )
        except RuntimeError as exc:
            return ResearchResponse(ok=False, error=str(exc), error_code=5)
        except LLMError as exc:
            # Demo / dry-run: fall back to heuristic so the product still delivers
            # a usable report when the model returns broken JSON or flaky output.
            if settings.dry_run or req.collector == "demo":
                logger.warning(
                    "LLM failed in demo mode (%s); falling back to heuristic ranking",
                    exc,
                )
                note(
                    "LLM ranking failed — using heuristic ranking for this demo run…"
                )
                pains, summary = _heuristic_pains(filtered, top_n, keywords)
                summary = (
                    f"(Demo fallback after LLM parse/API issue: {exc})\n\n{summary}"
                )
            else:
                return ResearchResponse(
                    ok=False, error=_friendly_llm_error(str(exc)), error_code=6
                )
        except Exception as exc:
            logger.exception("Unexpected LLM error")
            if settings.dry_run or req.collector == "demo":
                note(
                    "Unexpected LLM error — using heuristic ranking for this demo run…"
                )
                pains, summary = _heuristic_pains(filtered, top_n, keywords)
                summary = f"(Demo fallback after LLM error: {exc})\n\n{summary}"
            else:
                return ResearchResponse(
                    ok=False,
                    error=_friendly_llm_error(f"Unexpected LLM error: {exc}"),
                    error_code=6,
                )

    result = ResearchResult(
        niche=niche,
        subreddits=subreddits,
        keywords=keywords,
        time_filter=time_filter,
        posts_analyzed=len(filtered),
        posts_collected=posts_collected,
        collector_used=collector_name,
        llm_provider=llm_provider,
        llm_model=llm_model,
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        top_pains=pains,
        summary=summary,
        metadata={
            "max_posts_requested": max_posts,
            "top_n": top_n,
            "dry_run": settings.dry_run,
            "version": "1.0.0",
        },
    )

    note("Saving results…")
    json_path: Path | None = None
    try:
        json_path = save_json(result, settings.output_dir)
    except OSError as exc:
        return ResearchResponse(
            ok=False,
            result=result,
            error=f"Could not write JSON: {exc}",
            error_code=7,
        )

    note("Done.")
    return ResearchResponse(ok=True, result=result, json_path=json_path)
