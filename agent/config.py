"""Configuration, defaults, and environment loading."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (cwd or parent of this package)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv()  # also allow cwd override

# ---------------------------------------------------------------------------
# Default demo: WordPress use-case from The Startup Ideas Podcast (Cody Schneider)
# ---------------------------------------------------------------------------
DEFAULT_NICHE = "WordPress site owners and agency owners"

DEFAULT_SUBREDDITS = [
    "Wordpress",
    "webdev",
    "SEO",
    "webhosting",
    "WooCommerce",
]

DEFAULT_KEYWORDS = [
    "plugin",
    "slow",
    "performance",
    "security",
    "maintenance",
    "Yoast",
    "frustrating",
    "hate",
    "broken",
    "wish",
]

# Language that strongly signals a complaint (used for pre-filtering before LLM)
COMPLAINT_MARKERS = [
    "frustrating",
    "frustrated",
    "hate",
    "hates",
    "wish there was",
    "wish i could",
    "so hard",
    "broken",
    "doesn't work",
    "doesnt work",
    "not working",
    "nightmare",
    "awful",
    "terrible",
    "useless",
    "waste of",
    "fed up",
    "sick of",
    "can't stand",
    "cant stand",
    "annoying",
    "annoyance",
    "pain in",
    "struggle",
    "struggling",
    "help me",
    "how do i",
    "anyone else",
    "is it just me",
    "ruined",
    "regret",
    "scam",
    "overpriced",
    "slow as",
    "keeps breaking",
    "constantly",
    "tired of",
    "looking for alternative",
    "switching from",
    "migrating away",
    "sucks",
    "garbage",
    "buggy",
    "bug",
    "crash",
    "crashes",
    "down again",
    "support is",
    "no support",
    "customer service",
]

DEFAULT_MAX_POSTS = 175
DEFAULT_TIME_FILTER = "month"  # hour | day | week | month | year | all
DEFAULT_TOP_N = 5
DEFAULT_MAX_COMMENTS_PER_POST = 15

# Apify actor — Reddit Scraper Lite (pay-per-result, reliable community actor)
DEFAULT_APIFY_ACTOR = "trudax/reddit-scraper-lite"

# Default / fallback Anthropic model IDs (Sonnet 4 dated ID retired June 2026)
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5"
RETIRED_ANTHROPIC_MODELS = {
    "claude-sonnet-4-20250514": "claude-sonnet-5",
    "claude-sonnet-4-0": "claude-sonnet-5",
    "claude-3-7-sonnet-20250219": "claude-sonnet-5",
    "claude-3-5-sonnet-20241022": "claude-sonnet-5",
    "claude-3-5-sonnet-latest": "claude-sonnet-5",
    "claude-3-opus-20240229": "claude-opus-5",
}


@dataclass
class Settings:
    """Runtime settings resolved from env + CLI."""

    # Reddit
    apify_token: str | None = None
    apify_actor: str = DEFAULT_APIFY_ACTOR
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str = "CustomerPainResearchAgent/1.0"

    # LLM
    anthropic_api_key: str | None = None
    anthropic_model: str = DEFAULT_ANTHROPIC_MODEL
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"
    perplexity_api_key: str | None = None
    perplexity_model: str = "sonar-pro"

    # Run
    max_posts: int = DEFAULT_MAX_POSTS
    time_filter: str = DEFAULT_TIME_FILTER
    top_n: int = DEFAULT_TOP_N
    max_comments_per_post: int = DEFAULT_MAX_COMMENTS_PER_POST
    output_dir: Path = field(default_factory=lambda: _PROJECT_ROOT / "output")
    log_level: str = "INFO"
    prefer_collector: str | None = None  # "apify" | "praw" | "auto"
    dry_run: bool = False  # use demo data, skip live APIs

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            apify_token=os.getenv("APIFY_TOKEN") or None,
            apify_actor=os.getenv("APIFY_REDDIT_ACTOR", DEFAULT_APIFY_ACTOR),
            reddit_client_id=os.getenv("REDDIT_CLIENT_ID") or None,
            reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET") or None,
            reddit_user_agent=os.getenv(
                "REDDIT_USER_AGENT", "CustomerPainResearchAgent/1.0"
            ),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
            anthropic_model=_normalize_anthropic_model(
                os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
            ),
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            perplexity_api_key=os.getenv("PERPLEXITY_API_KEY") or None,
            perplexity_model=os.getenv("PERPLEXITY_MODEL", "sonar-pro"),
            output_dir=Path(os.getenv("OUTPUT_DIR", str(_PROJECT_ROOT / "output"))),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )

    def has_apify(self) -> bool:
        return bool(self.apify_token)

    def has_praw(self) -> bool:
        return bool(self.reddit_client_id and self.reddit_client_secret)

    def has_any_reddit_source(self) -> bool:
        return self.has_apify() or self.has_praw() or self.dry_run

    def has_llm(self) -> bool:
        return bool(
            self.anthropic_api_key or self.openai_api_key or self.perplexity_api_key
        )

    def resolve_collector(self) -> str:
        """Pick collector: apify (preferred) → praw → demo."""
        if self.dry_run:
            return "demo"
        prefer = (self.prefer_collector or "auto").lower()
        if prefer == "apify":
            if not self.has_apify():
                raise RuntimeError(
                    "Collector forced to 'apify' but APIFY_TOKEN is missing."
                )
            return "apify"
        if prefer == "praw":
            if not self.has_praw():
                raise RuntimeError(
                    "Collector forced to 'praw' but Reddit API credentials are missing."
                )
            return "praw"
        # auto
        if self.has_apify():
            return "apify"
        if self.has_praw():
            return "praw"
        raise RuntimeError(
            "No Reddit data source configured. Set APIFY_TOKEN (preferred) or "
            "REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET + REDDIT_USER_AGENT. "
            "See .env.example and README.md."
        )

    def resolve_llm(self) -> tuple[str, str, str]:
        """
        Return (provider, model, api_key).
        Preference: Anthropic → OpenAI → Perplexity.
        """
        if self.anthropic_api_key:
            return (
                "anthropic",
                _normalize_anthropic_model(self.anthropic_model),
                self.anthropic_api_key,
            )
        if self.openai_api_key:
            return "openai", self.openai_model, self.openai_api_key
        if self.perplexity_api_key:
            return "perplexity", self.perplexity_model, self.perplexity_api_key
        raise RuntimeError(
            "No LLM API key found. Set ANTHROPIC_API_KEY (recommended), "
            "OPENAI_API_KEY, or PERPLEXITY_API_KEY. See .env.example."
        )


def _normalize_anthropic_model(model: str | None) -> str:
    """Rewrite retired/dated model IDs to a currently available alias."""
    m = (model or DEFAULT_ANTHROPIC_MODEL).strip()
    if not m:
        return DEFAULT_ANTHROPIC_MODEL
    return RETIRED_ANTHROPIC_MODELS.get(m, m)


def slugify_niche(niche: str, max_len: int = 40) -> str:
    """Turn a niche string into a safe filename fragment."""
    slug = "".join(c.lower() if c.isalnum() else "_" for c in niche.strip())
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")[:max_len] or "niche"
