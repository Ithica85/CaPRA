"""
Pre-LLM filtering: keep only posts that look like real complaints.

Why filter before the LLM?
  - Cuts token cost dramatically (150–200 posts → lean pain-focused set)
  - Improves ranking quality by removing pure how-tos / show-and-tell noise
  - Still keeps high-engagement threads even without explicit complaint words
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from agent.config import COMPLAINT_MARKERS
from agent.models import RedditPost

logger = logging.getLogger(__name__)


def filter_complaint_posts(
    posts: list[RedditPost],
    keywords: list[str],
    *,
    min_score: int = -5,
    keep_high_engagement: bool = True,
    engagement_threshold: int = 20,
) -> list[RedditPost]:
    """
    Return posts that match niche keywords and/or complaint language.

    A post is kept if:
      1. Text matches at least one keyword OR complaint marker, AND score >= min_score
      OR
      2. keep_high_engagement and (score + num_comments) >= engagement_threshold
         and at least a weak keyword/topic hit
    """
    if not posts:
        return []

    keywords_l = [k.lower() for k in keywords if k.strip()]
    markers_l = [m.lower() for m in COMPLAINT_MARKERS]

    kept: list[RedditPost] = []
    for post in posts:
        text = post.text_blob.lower()
        if not text.strip():
            continue
        if post.score < min_score and post.num_comments < 3:
            continue

        kw_hits = [k for k in keywords_l if k in text]
        marker_hits = [m for m in markers_l if m in text]
        engagement = post.score + post.num_comments

        is_complaint = bool(marker_hits)
        is_on_topic = bool(kw_hits)
        is_hot = keep_high_engagement and engagement >= engagement_threshold

        # Prefer true complaints on-topic; allow hot on-topic threads without markers
        if (is_complaint and (is_on_topic or len(marker_hits) >= 2)) or (
            is_on_topic and (is_complaint or is_hot)
        ):
            kept.append(post)
            continue

        # Pure complaint language even without keyword (broader net for discovery)
        if is_complaint and engagement >= 5:
            kept.append(post)

    # Deduplicate by id (should already be unique) and sort by signal
    by_id = {p.id: p for p in kept}
    ranked = sorted(
        by_id.values(),
        key=lambda p: (
            _complaint_density(p, markers_l),
            p.score,
            p.num_comments,
            p.created_utc or 0,
        ),
        reverse=True,
    )
    logger.info(
        "Filter: %d → %d posts (complaint/keyword signal)",
        len(posts),
        len(ranked),
    )
    return ranked


def _complaint_density(post: RedditPost, markers: list[str]) -> int:
    text = post.text_blob.lower()
    return sum(1 for m in markers if m in text)


def recency_boost(created_utc: float | None, half_life_days: float = 14.0) -> float:
    """
    Exponential recency weight in (0, 1].
    Posts from today ≈ 1.0; older posts decay with half_life_days.
    """
    if not created_utc:
        return 0.5
    age_days = max(
        0.0, (datetime.now(tz=timezone.utc).timestamp() - created_utc) / 86400.0
    )
    # score = 0.5 ** (age / half_life)
    return 0.5 ** (age_days / half_life_days)


def pack_posts_for_llm(
    posts: list[RedditPost],
    *,
    max_posts: int = 80,
    max_chars_budget: int = 100_000,
) -> list[dict]:
    """
    Convert posts to compact LLM snippets under a rough character budget.

    Decision: send the highest-signal posts first; truncate body/comments
    in the model layer via to_llm_snippet(). Avoids blowing context windows
    on 200 full threads.
    """
    snippets: list[dict] = []
    used = 0
    for post in posts[: max_posts * 2]:  # scan a bit extra if some are tiny
        snip = post.to_llm_snippet()
        # Rough size estimate
        size = len(str(snip))
        if used + size > max_chars_budget and snippets:
            break
        snippets.append(snip)
        used += size
        if len(snippets) >= max_posts:
            break
    logger.info(
        "Packed %d posts for LLM (~%d chars)",
        len(snippets),
        used,
    )
    return snippets


def extract_matched_keywords(text: str, keywords: list[str]) -> list[str]:
    text_l = text.lower()
    return [k for k in keywords if k.lower() in text_l]


def highlight_emotional_score(text: str) -> int:
    """Simple 0–100 heuristic for emotional intensity (used as a hint, not final rank)."""
    if not text:
        return 0
    text_l = text.lower()
    strong = [
        "hate",
        "nightmare",
        "ruined",
        "furious",
        "terrible",
        "awful",
        "worst",
        "scam",
        "fed up",
        "never again",
        "garbage",
        "useless",
    ]
    medium = [
        "frustrating",
        "annoyed",
        "broken",
        "struggle",
        "wish",
        "tired of",
        "so hard",
        "pain",
        "issue",
        "problem",
    ]
    score = 20
    for w in strong:
        if w in text_l:
            score += 12
    for w in medium:
        if w in text_l:
            score += 6
    # Exclamation / caps as weak signals
    score += min(15, text.count("!") * 3)
    if re.search(r"\b[A-Z]{4,}\b", text):
        score += 5
    return max(0, min(100, score))
