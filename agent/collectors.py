"""
Reddit data collectors.

Priority:
  1. Apify (trudax/reddit-scraper-lite) — preferred for reliability, no Reddit app needed
  2. PRAW — official Reddit API fallback
  3. Demo — offline sample conversations for dry-run / first-time smoke test
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Protocol

from agent.config import Settings
from agent.models import RedditComment, RedditPost

logger = logging.getLogger(__name__)


class Collector(Protocol):
    def collect(
        self,
        subreddits: list[str],
        keywords: list[str],
        max_posts: int,
        time_filter: str,
    ) -> list[RedditPost]:
        ...


# ---------------------------------------------------------------------------
# Apify collector
# ---------------------------------------------------------------------------


class ApifyCollector:
    """
    Uses Apify's Reddit Scraper Lite actor.

    Strategy (optimized for runtime — was too slow with N×M actor runs):
    - Prefer 1–2 Apify actor runs total, not one per subreddit×keyword.
    - Run A: scrape recent posts from all target subreddit URLs.
    - Run B: a small set of keyword searches (pain language + topics).
    - Normalize into RedditPost; attach comments when present.

    Why fewer runs: each Apify actor start costs ~1–2+ minutes. Old code could
    fire 30+ sequential runs and hang the UI for half an hour.
    """

    # Hard cap on sequential actor launches per research job
    MAX_ACTOR_RUNS = 2

    def __init__(self, settings: Settings) -> None:
        if not settings.apify_token:
            raise RuntimeError("APIFY_TOKEN is required for ApifyCollector")
        self.settings = settings
        self.actor_id = settings.apify_actor

    def collect(
        self,
        subreddits: list[str],
        keywords: list[str],
        max_posts: int,
        time_filter: str,
    ) -> list[RedditPost]:
        from apify_client import ApifyClient

        client = ApifyClient(self.settings.apify_token)
        posts_by_id: dict[str, RedditPost] = {}
        comments_by_parent: dict[str, list[RedditComment]] = {}

        clean_subs = [s.lstrip("r/").strip() for s in subreddits if s.strip()]
        if not clean_subs:
            return []

        # Budget items per community in the feed scrape
        per_sub = max(15, min(40, max_posts // max(len(clean_subs), 1)))
        max_comments = min(10, self.settings.max_comments_per_post)
        search_terms = self._build_search_terms(keywords)

        logger.info(
            "Apify: actor=%s | subreddits=%s | max_posts=%s | time=%s | "
            "searches=%s | max_actor_runs=%s",
            self.actor_id,
            clean_subs,
            max_posts,
            time_filter,
            search_terms,
            self.MAX_ACTOR_RUNS,
        )

        runs_used = 0

        # ---- Run 1: recent posts from all subreddits in ONE actor call ----
        if runs_used < self.MAX_ACTOR_RUNS:
            start_urls = [
                {"url": f"https://www.reddit.com/r/{sub}/new/"} for sub in clean_subs
            ]
            # Also include "hot" for higher-signal threads
            start_urls += [
                {"url": f"https://www.reddit.com/r/{sub}/hot/"} for sub in clean_subs[:3]
            ]
            run_input = {
                "startUrls": start_urls,
                "maxItems": min(max_posts, per_sub * len(clean_subs)),
                "maxPostCount": per_sub,
                "maxComments": max_comments,
                "skipComments": False,
                "skipCommunity": True,
                "skipUserPosts": True,
                "includeNSFW": False,
                "includeMediaLinks": True,
                "scrollTimeout": 30,
                "proxy": {"useApifyProxy": True},
            }
            logger.info(
                "Apify run 1/%s: subreddit feeds (%s URLs)…",
                self.MAX_ACTOR_RUNS,
                len(start_urls),
            )
            try:
                items = self._run_actor(client, run_input)
                self._ingest_items(items, posts_by_id, comments_by_parent, source="apify")
                runs_used += 1
                logger.info(
                    "After feed scrape: %s unique posts", len(posts_by_id)
                )
            except Exception as exc:
                logger.warning("Apify feed scrape failed: %s", exc)
                runs_used += 1  # still count a failed attempt to avoid infinite loops

        # ---- Run 2: keyword search (pain signal) — one call, few queries ----
        if runs_used < self.MAX_ACTOR_RUNS and len(posts_by_id) < max_posts:
            # Prefer searching inside the first/primary subreddit + a global-ish OR
            primary = clean_subs[0]
            queries = search_terms[:3]  # hard cap queries inside one run
            run_input = {
                "searches": queries,
                "searchCommunityName": primary,
                "searchPosts": True,
                "searchComments": False,
                "searchCommunities": False,
                "searchUsers": False,
                "sort": "relevance",
                "time": self._map_time_filter(time_filter),
                "maxItems": min(80, max_posts),
                "maxPostCount": min(40, max_posts),
                "maxComments": max_comments,
                "skipComments": False,
                "includeNSFW": False,
                "includeMediaLinks": True,
                "scrollTimeout": 30,
                "proxy": {"useApifyProxy": True},
            }
            logger.info(
                "Apify run 2/%s: keyword search in r/%s terms=%s…",
                self.MAX_ACTOR_RUNS,
                primary,
                queries,
            )
            try:
                items = self._run_actor(client, run_input)
                self._ingest_items(items, posts_by_id, comments_by_parent, source="apify")
                runs_used += 1
            except Exception as exc:
                logger.warning("Apify keyword search failed: %s", exc)

        # Attach comments that arrived as separate dataset rows
        for post_id, post in posts_by_id.items():
            extras = comments_by_parent.get(post_id, [])
            if extras:
                existing = {c.id for c in post.comments if c.id}
                for c in extras:
                    if c.id not in existing:
                        post.comments.append(c)

        posts = list(posts_by_id.values())
        posts.sort(key=lambda p: (p.score, p.num_comments), reverse=True)
        logger.info(
            "Apify: collected %d unique posts in %d actor run(s)",
            len(posts),
            runs_used,
        )
        return posts[:max_posts]

    def _run_actor(self, client, run_input: dict) -> list[dict]:
        """
        Call Apify actor and return dataset items.

        apify-client v3 returns a Pydantic Run model (not a dict), so we read
        default_dataset_id via attribute access with dict fallback.
        """
        logger.info("Starting Apify actor %s …", self.actor_id)
        run = client.actor(self.actor_id).call(run_input=run_input)
        if not run:
            logger.warning("Apify actor returned empty run")
            return []

        dataset_id = self._dataset_id_from_run(run)
        if not dataset_id:
            logger.warning("Apify run finished but no dataset id found: %r", run)
            return []

        items = list(client.dataset(dataset_id).iterate_items())
        logger.info("Apify run finished: %d items (dataset=%s)", len(items), dataset_id)
        return items

    @staticmethod
    def _dataset_id_from_run(run: object) -> str | None:
        """Support apify-client v2 dicts and v3 Run models."""
        if run is None:
            return None
        # Pydantic model / object with attributes
        for attr in ("default_dataset_id", "defaultDatasetId"):
            val = getattr(run, attr, None)
            if val:
                return str(val)
        # Dict-like
        if isinstance(run, dict):
            return run.get("defaultDatasetId") or run.get("default_dataset_id")
        # model_dump() if available
        dump = getattr(run, "model_dump", None)
        if callable(dump):
            data = dump(by_alias=True)
            if isinstance(data, dict):
                return data.get("defaultDatasetId") or data.get("default_dataset_id")
        # Mapping protocol via []
        try:
            return run["defaultDatasetId"]  # type: ignore[index]
        except Exception:
            pass
        return None

    def _ingest_items(
        self,
        items: list[dict],
        posts_by_id: dict[str, RedditPost],
        comments_by_parent: dict[str, list[RedditComment]],
        source: str,
    ) -> None:
        for item in items:
            data_type = (item.get("dataType") or item.get("type") or "").lower()
            if data_type == "comment" or item.get("parentId"):
                comment = self._parse_comment(item)
                parent = self._normalize_id(item.get("parentId") or "")
                # parentId may be t3_xxx or bare id
                parent_key = parent.replace("t3_", "").replace("t1_", "")
                if parent_key and comment.body:
                    comments_by_parent.setdefault(parent_key, []).append(comment)
                continue

            # Treat as post (including rows without explicit dataType)
            if data_type in ("community", "user"):
                continue
            post = self._parse_post(item, source=source)
            if not post.id or (not post.title and not post.body):
                continue
            if post.id not in posts_by_id:
                posts_by_id[post.id] = post
            else:
                # Merge comments / higher score if we re-see the same post
                existing = posts_by_id[post.id]
                if post.score > existing.score:
                    existing.score = post.score
                if len(post.comments) > len(existing.comments):
                    existing.comments = post.comments

    def _parse_post(self, item: dict, source: str) -> RedditPost:
        raw_id = item.get("parsedId") or item.get("id") or ""
        post_id = self._normalize_id(str(raw_id)).replace("t3_", "")
        sub = (
            item.get("parsedCommunityName")
            or item.get("communityName")
            or item.get("subreddit")
            or ""
        )
        sub = str(sub).replace("r/", "").strip()
        body = item.get("body") or item.get("selftext") or item.get("text") or ""
        title = item.get("title") or ""
        url = item.get("url") or item.get("postUrl") or ""
        if url and url.startswith("/"):
            url = f"https://www.reddit.com{url}"
        score = int(item.get("upVotes") or item.get("score") or item.get("ups") or 0)
        n_comments = int(
            item.get("numberOfComments") or item.get("num_comments") or 0
        )
        created = self._parse_created(item)
        # Nested comments if actor embeds them
        comments: list[RedditComment] = []
        for c in item.get("comments") or []:
            if isinstance(c, dict):
                comments.append(self._parse_comment(c))

        return RedditPost(
            id=post_id or f"unknown_{hash(title + body) % 10**8}",
            title=str(title),
            body=str(body),
            subreddit=sub,
            author=str(item.get("username") or item.get("author") or ""),
            url=str(url),
            score=score,
            num_comments=n_comments,
            created_utc=created,
            comments=comments,
            source=source,  # type: ignore[arg-type]
        )

    def _parse_comment(self, item: dict) -> RedditComment:
        raw_id = item.get("parsedId") or item.get("id") or ""
        cid = self._normalize_id(str(raw_id)).replace("t1_", "")
        body = item.get("body") or item.get("text") or ""
        url = item.get("url") or ""
        if url and url.startswith("/"):
            url = f"https://www.reddit.com{url}"
        return RedditComment(
            id=cid,
            body=str(body),
            score=int(item.get("upVotes") or item.get("score") or 0),
            author=str(item.get("username") or item.get("author") or ""),
            url=str(url),
            created_utc=self._parse_created(item),
        )

    @staticmethod
    def _normalize_id(value: str) -> str:
        return value.strip()

    @staticmethod
    def _parse_created(item: dict) -> float | None:
        for key in ("createdAt", "created_utc", "created", "date"):
            val = item.get(key)
            if val is None:
                continue
            if isinstance(val, (int, float)):
                # Reddit sometimes returns seconds; Apify often ISO strings
                return float(val) if val > 1e9 else float(val)
            if isinstance(val, str):
                try:
                    # ISO 8601
                    dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
                    return dt.timestamp()
                except ValueError:
                    continue
        return None

    @staticmethod
    def _map_time_filter(time_filter: str) -> str:
        allowed = {"hour", "day", "week", "month", "year", "all"}
        t = (time_filter or "month").lower()
        return t if t in allowed else "month"

    @staticmethod
    def _build_search_terms(keywords: list[str]) -> list[str]:
        """
        Collapse many keywords into a few search queries to control Apify cost.

        Decision: Reddit search works better with short phrases than huge OR chains.
        We keep high-signal complaint words as standalone searches and group
        product/topic keywords into one OR query.
        """
        complaint_hits = {
            "frustrating",
            "hate",
            "broken",
            "wish",
            "slow",
            "nightmare",
            "useless",
            "sucks",
        }
        complaint_terms = [k for k in keywords if k.lower() in complaint_hits]
        topic_terms = [k for k in keywords if k.lower() not in complaint_hits]

        terms: list[str] = []
        # One topic OR-query (keeps actor runs small)
        if topic_terms:
            terms.append(" OR ".join(topic_terms[:6]))
        # One complaint-language query
        complaints = complaint_terms[:4] or ["frustrating", "broken", "hate", "wish"]
        terms.append(" OR ".join(complaints))
        # Always useful JTBD phrase
        terms.append("wish there was OR so hard OR nightmare")
        # Cap — each search multiplies scrape time inside a single actor run
        return terms[:3]


# ---------------------------------------------------------------------------
# PRAW collector (official Reddit API fallback)
# ---------------------------------------------------------------------------


class PrawCollector:
    """
    Official Reddit API via PRAW.

    Requires a Reddit "script" app (client id + secret). Free for moderate use;
    subject to Reddit rate limits — we sleep politely between subreddit queries.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.reddit_client_id or not settings.reddit_client_secret:
            raise RuntimeError(
                "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are required for PRAW"
            )
        self.settings = settings

    def collect(
        self,
        subreddits: list[str],
        keywords: list[str],
        max_posts: int,
        time_filter: str,
    ) -> list[RedditPost]:
        import praw
        from praw.models import MoreComments

        reddit = praw.Reddit(
            client_id=self.settings.reddit_client_id,
            client_secret=self.settings.reddit_client_secret,
            user_agent=self.settings.reddit_user_agent,
        )
        # Read-only is fine for public data
        reddit.read_only = True

        posts_by_id: dict[str, RedditPost] = {}
        time_filter = (time_filter or "month").lower()
        per_sub = max(15, max_posts // max(len(subreddits), 1))
        search_query = self._build_query(keywords)

        logger.info(
            "PRAW: subreddits=%s | query=%r | max_posts=%s | time=%s",
            subreddits,
            search_query,
            max_posts,
            time_filter,
        )

        for sub_name in subreddits:
            if len(posts_by_id) >= max_posts:
                break
            try:
                subreddit = reddit.subreddit(sub_name.lstrip("r/"))
            except Exception as exc:
                logger.warning("Could not open r/%s: %s", sub_name, exc)
                continue

            # Search with keyword query
            try:
                search_iter = subreddit.search(
                    search_query,
                    sort="relevance",
                    time_filter=time_filter if time_filter != "all" else "all",
                    limit=per_sub,
                )
                for submission in search_iter:
                    if len(posts_by_id) >= max_posts:
                        break
                    post = self._submission_to_post(submission, MoreComments)
                    posts_by_id[post.id] = post
            except Exception as exc:
                logger.warning("PRAW search failed for r/%s: %s", sub_name, exc)

            # Also pull new posts (broader net)
            try:
                for submission in subreddit.new(limit=min(25, per_sub // 2)):
                    if len(posts_by_id) >= max_posts:
                        break
                    if submission.id in posts_by_id:
                        continue
                    # Lightweight recency check for time_filter=month
                    if not self._within_time(submission.created_utc, time_filter):
                        continue
                    post = self._submission_to_post(submission, MoreComments)
                    posts_by_id[post.id] = post
            except Exception as exc:
                logger.warning("PRAW new-feed failed for r/%s: %s", sub_name, exc)

            # Be kind to Reddit rate limits
            time.sleep(1.0)

        posts = list(posts_by_id.values())
        posts.sort(key=lambda p: (p.score, p.num_comments), reverse=True)
        logger.info("PRAW: collected %d unique posts", len(posts))
        return posts[:max_posts]

    def _submission_to_post(self, submission, MoreComments) -> RedditPost:
        comments: list[RedditComment] = []
        try:
            submission.comment_sort = "top"
            submission.comments.replace_more(limit=0)
            for c in submission.comments[: self.settings.max_comments_per_post]:
                if isinstance(c, MoreComments):
                    continue
                body = getattr(c, "body", "") or ""
                if body in ("[deleted]", "[removed]"):
                    continue
                comments.append(
                    RedditComment(
                        id=str(c.id),
                        body=body,
                        score=int(getattr(c, "score", 0) or 0),
                        author=str(c.author) if c.author else "",
                        url=f"https://www.reddit.com{c.permalink}",
                        created_utc=float(c.created_utc)
                        if getattr(c, "created_utc", None)
                        else None,
                    )
                )
        except Exception as exc:
            logger.debug("Could not load comments for %s: %s", submission.id, exc)

        return RedditPost(
            id=str(submission.id),
            title=submission.title or "",
            body=submission.selftext or "",
            subreddit=str(submission.subreddit),
            author=str(submission.author) if submission.author else "",
            url=f"https://www.reddit.com{submission.permalink}",
            score=int(submission.score or 0),
            num_comments=int(submission.num_comments or 0),
            created_utc=float(submission.created_utc),
            comments=comments,
            source="praw",
        )

    @staticmethod
    def _build_query(keywords: list[str]) -> str:
        # Reddit search: OR is supported; keep query reasonably short
        cleaned = [k.strip() for k in keywords if k.strip()]
        if not cleaned:
            return "frustrating OR broken OR hate OR wish"
        # Prefer a mix — full OR of all can be too broad; use first 8
        return " OR ".join(cleaned[:8])

    @staticmethod
    def _within_time(created_utc: float, time_filter: str) -> bool:
        now = datetime.now(tz=timezone.utc).timestamp()
        windows = {
            "hour": 3600,
            "day": 86400,
            "week": 7 * 86400,
            "month": 30 * 86400,
            "year": 365 * 86400,
            "all": None,
        }
        window = windows.get(time_filter)
        if window is None:
            return True
        return (now - created_utc) <= window


# ---------------------------------------------------------------------------
# Demo collector (offline)
# ---------------------------------------------------------------------------


class DemoCollector:
    """
    Offline sample conversations for dry-run mode.

    Lets a non-technical user verify the pipeline (filter → LLM → JSON)
    without any Reddit credentials. Content is synthetic but realistic
    WordPress pain language inspired by common public complaints.
    """

    def collect(
        self,
        subreddits: list[str],
        keywords: list[str],
        max_posts: int,
        time_filter: str,
    ) -> list[RedditPost]:
        logger.info("Demo collector: returning synthetic WordPress complaint posts")
        now = datetime.now(tz=timezone.utc).timestamp()
        samples = _DEMO_POSTS
        # Stamp recent created_utc
        posts: list[RedditPost] = []
        for i, p in enumerate(samples):
            data = p.copy()
            data["created_utc"] = now - (i * 86400 * 2)  # every ~2 days
            posts.append(RedditPost(**data))
        return posts[:max_posts]


def get_collector(settings: Settings) -> Collector:
    name = settings.resolve_collector()
    logger.info("Using Reddit collector: %s", name)
    if name == "apify":
        return ApifyCollector(settings)
    if name == "praw":
        return PrawCollector(settings)
    return DemoCollector()


# Synthetic demo data — realistic complaint shape for the WordPress niche
_DEMO_POSTS: list[dict] = [
    {
        "id": "demo001",
        "title": "Site is so slow after adding one more plugin — this is frustrating",
        "body": (
            "I run a small agency and every client WordPress site eventually becomes a "
            "nightmare. We added one SEO plugin and now TTFB is 3+ seconds. Caching plugins "
            "conflict with each other. I wish there was a simple performance stack that "
            "just worked without me babysitting it every week."
        ),
        "subreddit": "Wordpress",
        "author": "agency_dev_42",
        "url": "https://www.reddit.com/r/Wordpress/comments/demo001/site_is_so_slow/",
        "score": 214,
        "num_comments": 67,
        "source": "demo",
        "comments": [
            {
                "id": "c001",
                "body": "Same. I hate how every 'must-have' plugin adds 200ms. Maintenance is half my job now.",
                "score": 89,
                "author": "freelance_wp",
                "url": "https://www.reddit.com/r/Wordpress/comments/demo001/c001/",
            },
            {
                "id": "c002",
                "body": "Autoptimize + WP Rocket still broke my checkout last month. So hard to trust any of them.",
                "score": 41,
                "author": "woo_owner",
                "url": "https://www.reddit.com/r/Wordpress/comments/demo001/c002/",
            },
        ],
    },
    {
        "id": "demo002",
        "title": "Security plugins are useless if I still get hacked through an abandoned plugin",
        "body": (
            "Wordfence alerts me all day but the real problem is plugin graveyard. Clients "
            "have 40 plugins, half unmaintained. I hate telling them their site is broken "
            "again because of some free slider from 2019. Wish there was automatic dead-plugin "
            "detection and safe replacement suggestions."
        ),
        "subreddit": "webhosting",
        "author": "sec_conscious",
        "url": "https://www.reddit.com/r/webhosting/comments/demo002/security_plugins/",
        "score": 178,
        "num_comments": 52,
        "source": "demo",
        "comments": [
            {
                "id": "c003",
                "body": "This. Security theater. The frustrating part is clients blame hosting when it's their plugin stack.",
                "score": 55,
                "author": "host_ops",
                "url": "https://www.reddit.com/r/webhosting/comments/demo002/c003/",
            }
        ],
    },
    {
        "id": "demo003",
        "title": "Yoast vs RankMath vs… I'm tired of SEO plugin upsells",
        "body": (
            "Every SEO plugin is free-until-you-need-the-basics. It's so hard to explain to "
            "clients why they need a $99/year plan just for redirects. Broken schema, "
            "conflicting sitemaps — maintenance hell. Wish there was a boring, paid-once SEO toolkit."
        ),
        "subreddit": "SEO",
        "author": "seo_freelancer",
        "url": "https://www.reddit.com/r/SEO/comments/demo003/yoast_upsells/",
        "score": 156,
        "num_comments": 88,
        "source": "demo",
        "comments": [
            {
                "id": "c004",
                "body": "Hate the green light gamification. Clients obsess over Yoast scores that don't matter.",
                "score": 102,
                "author": "content_ops",
                "url": "https://www.reddit.com/r/SEO/comments/demo003/c004/",
            }
        ],
    },
    {
        "id": "demo004",
        "title": "WooCommerce updates broke my checkout three times this year",
        "body": (
            "Honestly frustrating. Payment gateway plugin + WooCommerce core update = blank "
            "checkout. I run a store, not a software company. Support is forums and 'please "
            "disable all plugins'. Wish there was a managed Woo stack that tested updates for me."
        ),
        "subreddit": "WooCommerce",
        "author": "store_owner_jen",
        "url": "https://www.reddit.com/r/WooCommerce/comments/demo004/updates_broke/",
        "score": 241,
        "num_comments": 93,
        "source": "demo",
        "comments": [
            {
                "id": "c005",
                "body": "Same nightmare every quarter. Staging sites help but clients won't pay for proper maintenance.",
                "score": 67,
                "author": "agency_sam",
                "url": "https://www.reddit.com/r/WooCommerce/comments/demo004/c005/",
            }
        ],
    },
    {
        "id": "demo005",
        "title": "Page builders make sites look good and impossible to maintain",
        "body": (
            "Inherited an Elementor site with 200 templates and inline CSS everywhere. "
            "Editing one section breaks three others. So hard to hand off. I wish clients "
            "understood the long-term cost. Hate rebuilding from scratch but that's cheaper than fixing this."
        ),
        "subreddit": "webdev",
        "author": "dev_rescue",
        "url": "https://www.reddit.com/r/webdev/comments/demo005/page_builders/",
        "score": 320,
        "num_comments": 140,
        "source": "demo",
        "comments": [
            {
                "id": "c006",
                "body": "Page builder lock-in is the real pain. Migrating away is a full rewrite.",
                "score": 120,
                "author": "stack_escape",
                "url": "https://www.reddit.com/r/webdev/comments/demo005/c006/",
            }
        ],
    },
    {
        "id": "demo006",
        "title": "Monthly maintenance retainers don't cover the actual firefighting",
        "body": (
            "Clients want $50/mo care plans. Reality: plugin conflicts, phishing, failed backups, "
            "PHP version bumps. It's broken economics. Wish there was a productized maintenance "
            "service with clear SLAs that agencies could white-label without losing money."
        ),
        "subreddit": "Wordpress",
        "author": "agency_owner_mike",
        "url": "https://www.reddit.com/r/Wordpress/comments/demo006/maintenance_retainers/",
        "score": 198,
        "num_comments": 74,
        "source": "demo",
        "comments": [
            {
                "id": "c007",
                "body": "We raised to $150/mo and still undercharge for security incidents. Frustrating.",
                "score": 44,
                "author": "wp_biz",
                "url": "https://www.reddit.com/r/Wordpress/comments/demo006/c007/",
            }
        ],
    },
    {
        "id": "demo007",
        "title": "Hosting 'optimized for WordPress' still needs 10 caching layers",
        "body": (
            "Marketing says optimized. Reality: I still install Redis, object cache, CDN, "
            "image optimization. Site is slow on mobile. Hate the gap between promise and "
            "delivery. Is it just me or is managed WP hosting mostly a dashboard skin?"
        ),
        "subreddit": "webhosting",
        "author": "perf_nerd",
        "url": "https://www.reddit.com/r/webhosting/comments/demo007/optimized_hosting/",
        "score": 133,
        "num_comments": 61,
        "source": "demo",
        "comments": [
            {
                "id": "c008",
                "body": "Shared 'managed' plans are the worst. You pay more for less control and still debug yourself.",
                "score": 38,
                "author": "sysadmin_lite",
                "url": "https://www.reddit.com/r/webhosting/comments/demo007/c008/",
            }
        ],
    },
    {
        "id": "demo008",
        "title": "Client wants me to 'just fix Core Web Vitals' — easier said than done on WP",
        "body": (
            "LCP is destroyed by hero sliders and unoptimized theme code. CLS from ads and fonts. "
            "It's so hard to hit green without gutting the design they paid for. Wish themes "
            "shipped performance-first by default."
        ),
        "subreddit": "SEO",
        "author": "vitals_guy",
        "url": "https://www.reddit.com/r/SEO/comments/demo008/core_web_vitals/",
        "score": 167,
        "num_comments": 49,
        "source": "demo",
        "comments": [
            {
                "id": "c009",
                "body": "Theme bloat + plugins = death by a thousand requests. Frustrating for agencies selling SEO.",
                "score": 51,
                "author": "agency_seo",
                "url": "https://www.reddit.com/r/SEO/comments/demo008/c009/",
            }
        ],
    },
    {
        "id": "demo009",
        "title": "Backups failed silently for 3 months — found out after a hack",
        "body": (
            "Updraft 'succeeded' but restore was empty. Absolute nightmare. Security is broken "
            "if backups aren't restore-tested. Wish there was automated restore verification "
            "that emails a real screenshot of the restored site."
        ),
        "subreddit": "Wordpress",
        "author": "burned_once",
        "url": "https://www.reddit.com/r/Wordpress/comments/demo009/backups_failed/",
        "score": 289,
        "num_comments": 101,
        "source": "demo",
        "comments": [
            {
                "id": "c010",
                "body": "Same. Hate that green checkmarks lie. Offsite + periodic restore tests should be default.",
                "score": 77,
                "author": "ops_person",
                "url": "https://www.reddit.com/r/Wordpress/comments/demo009/c010/",
            }
        ],
    },
    {
        "id": "demo010",
        "title": "Multilingual + WooCommerce + page builder = permanent broken state",
        "body": (
            "WPML or TranslatePress plus Woo plus Elementor. Something is always broken after updates. "
            "So hard to quote projects accurately. I wish there was a supported reference stack "
            "for multilingual stores that vendors actually tested together."
        ),
        "subreddit": "WooCommerce",
        "author": "eu_store",
        "url": "https://www.reddit.com/r/WooCommerce/comments/demo010/multilingual/",
        "score": 94,
        "num_comments": 33,
        "source": "demo",
        "comments": [
            {
                "id": "c011",
                "body": "Compatibility matrix is a fantasy. Every update is a dice roll. Exhausting.",
                "score": 29,
                "author": "polyglot_dev",
                "url": "https://www.reddit.com/r/WooCommerce/comments/demo010/c011/",
            }
        ],
    },
]
