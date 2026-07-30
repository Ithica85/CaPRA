"""Shared data models for Reddit items and ranked pain points."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class RedditComment(BaseModel):
    """A single Reddit comment attached to a post."""

    id: str = ""
    body: str = ""
    score: int = 0
    author: str = ""
    url: str = ""
    created_utc: float | None = None

    @property
    def created_iso(self) -> str | None:
        if self.created_utc is None:
            return None
        return datetime.fromtimestamp(self.created_utc, tz=timezone.utc).isoformat()


class RedditPost(BaseModel):
    """Normalized Reddit post used by both Apify and PRAW collectors."""

    id: str
    title: str = ""
    body: str = ""
    subreddit: str = ""
    author: str = ""
    url: str = ""
    score: int = 0
    num_comments: int = 0
    created_utc: float | None = None
    comments: list[RedditComment] = Field(default_factory=list)
    source: Literal["apify", "praw", "demo"] = "apify"

    @property
    def created_iso(self) -> str | None:
        if self.created_utc is None:
            return None
        return datetime.fromtimestamp(self.created_utc, tz=timezone.utc).isoformat()

    @property
    def text_blob(self) -> str:
        """Full searchable text for keyword / complaint filtering."""
        parts = [self.title or "", self.body or ""]
        for c in self.comments:
            if c.body:
                parts.append(c.body)
        return "\n".join(parts)

    def to_llm_snippet(self, max_comment_chars: int = 400) -> dict[str, Any]:
        """Compact representation for LLM prompts (keeps token usage in check)."""
        top_comments = sorted(self.comments, key=lambda c: c.score, reverse=True)[:5]
        return {
            "id": self.id,
            "subreddit": self.subreddit,
            "title": self.title[:300],
            "body": (self.body or "")[:800],
            "score": self.score,
            "num_comments": self.num_comments,
            "url": self.url,
            "created": self.created_iso,
            "top_comments": [
                {
                    "body": (c.body or "")[:max_comment_chars],
                    "score": c.score,
                    "url": c.url,
                }
                for c in top_comments
                if c.body and c.body not in ("[deleted]", "[removed]")
            ],
        }


class Evidence(BaseModel):
    """A real quote backing a pain point."""

    quote: str
    url: str = ""
    subreddit: str = ""
    upvotes: int = 0
    source_type: Literal["post", "comment"] = "post"


class PainPoint(BaseModel):
    """One ranked customer pain with evidence and scores."""

    rank: int = 0
    title: str
    description: str
    desired_outcome: str
    intensity_score: int = Field(ge=0, le=100)
    frequency: int = Field(
        default=1,
        description="How many distinct posts/comments support this pain",
    )
    emotional_language_score: int = Field(
        default=50,
        ge=0,
        le=100,
        description="How strong the emotional/frustrated language is (0–100)",
    )
    recency_score: int = Field(
        default=50,
        ge=0,
        le=100,
        description="How recent the supporting evidence is (0–100)",
    )
    upvote_signal: int = Field(
        default=0,
        description="Aggregate upvotes across supporting evidence",
    )
    category: str = Field(
        default="general",
        description="e.g. performance, security, pricing, workflow, support",
    )
    evidence: list[Evidence] = Field(default_factory=list)
    keywords_matched: list[str] = Field(default_factory=list)

    @field_validator("intensity_score", mode="before")
    @classmethod
    def clamp_intensity(cls, v: Any) -> int:
        try:
            return max(0, min(100, int(v)))
        except (TypeError, ValueError):
            return 50


class ResearchResult(BaseModel):
    """Full structured output of one research run — ready for ad/creative agents."""

    niche: str
    subreddits: list[str]
    keywords: list[str]
    time_filter: str
    posts_analyzed: int
    posts_collected: int
    collector_used: str
    llm_provider: str
    llm_model: str
    generated_at: str
    top_pains: list[PainPoint]
    summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_export_dict(self) -> dict[str, Any]:
        """JSON-serializable dict in the canonical output shape."""
        return {
            "niche": self.niche,
            "subreddits": self.subreddits,
            "keywords": self.keywords,
            "time_filter": self.time_filter,
            "posts_analyzed": self.posts_analyzed,
            "posts_collected": self.posts_collected,
            "collector_used": self.collector_used,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "generated_at": self.generated_at,
            "summary": self.summary,
            "top_pains": [p.model_dump() for p in self.top_pains],
            "metadata": self.metadata,
        }
