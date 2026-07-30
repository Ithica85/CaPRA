#!/usr/bin/env python3
"""
Customer Pain Research Agent — simple browser UI (Streamlit).

Launch:
  Double-click start_ui.command  (Mac)
  or:  streamlit run app.py
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import streamlit as st

from agent.config import (
    DEFAULT_KEYWORDS,
    DEFAULT_MAX_POSTS,
    DEFAULT_NICHE,
    DEFAULT_SUBREDDITS,
    DEFAULT_TIME_FILTER,
)
from agent.pipeline import ResearchRequest, run_research

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Customer Pain Research Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ui")

PROJECT_ROOT = Path(__file__).resolve().parent


def _split_list(raw: str) -> list[str]:
    """Accept commas, newlines, or spaces between items."""
    parts: list[str] = []
    for line in raw.replace(",", "\n").splitlines():
        for token in line.split():
            t = token.strip().lstrip("r/")
            if t:
                parts.append(t)
    # preserve order, drop dupes
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def _env_has(*keys: str) -> bool:
    return any(bool((os.getenv(k) or "").strip()) for k in keys)


def _mask_key(value: str | None) -> str:
    v = (value or "").strip()
    if not v:
        return "(none)"
    if len(v) <= 12:
        return v[:3] + "…"
    return f"{v[:7]}…{v[-4:]}"


def _intensity_color(score: int) -> str:
    if score >= 80:
        return "#dc2626"
    if score >= 60:
        return "#ea580c"
    if score >= 40:
        return "#ca8a04"
    return "#65a30d"


# ---------------------------------------------------------------------------
# Sidebar — API keys & mode
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.caption("Keys stay in this browser session (and optional .env on disk).")

    st.markdown("### Data source")
    data_mode = st.radio(
        "How should we get Reddit posts?",
        options=[
            "Demo (no Reddit keys — practice mode)",
            "Live Reddit (Apify or Reddit API)",
        ],
        index=0,
        help="Start with Demo to learn the app. Switch to Live when you have keys.",
    )
    dry_run = data_mode.startswith("Demo")

    with st.expander("🔑 API keys", expanded=True):
        # Show what the process currently has (often a bad key from the IDE/shell)
        st.markdown("**Currently loaded LLM keys**")
        st.caption(
            f"Anthropic: `{_mask_key(os.getenv('ANTHROPIC_API_KEY'))}`  ·  "
            f"OpenAI: `{_mask_key(os.getenv('OPENAI_API_KEY'))}`  ·  "
            f"Perplexity: `{_mask_key(os.getenv('PERPLEXITY_API_KEY'))}`"
        )
        if _env_has("OPENAI_API_KEY") and not _env_has("ANTHROPIC_API_KEY"):
            st.warning(
                "An OpenAI key is already loaded from your environment. "
                "If research fails with **401 / incorrect API key**, that key is invalid — "
                "clear it below and paste a fresh one."
            )

        if st.button("🧹 Clear LLM keys from this session", use_container_width=True):
            for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "PERPLEXITY_API_KEY"):
                os.environ.pop(k, None)
            st.session_state["keys_cleared"] = True
            st.success("Cleared Anthropic / OpenAI / Perplexity keys from this session.")
            st.rerun()

        st.markdown("**Paste a fresh key** (leave blank to use what’s already loaded):")
        # Don't pre-fill password boxes with ambient keys — that re-submits bad keys.
        # After clear, fields start empty so the user must paste a valid key.
        anthropic_key = st.text_input(
            "Anthropic API key (recommended)",
            value="",
            type="password",
            help="https://console.anthropic.com/ — paste a key starting with sk-ant-…",
            key="ui_anthropic_key",
        )
        openai_key = st.text_input(
            "OpenAI API key",
            value="",
            type="password",
            help="https://platform.openai.com/api-keys — paste a NEW key (old sk-proj ones often expire)",
            key="ui_openai_key",
        )
        perplexity_key = st.text_input(
            "Perplexity API key",
            value="",
            type="password",
            key="ui_perplexity_key",
        )

        llm_provider = st.selectbox(
            "Which LLM to use?",
            options=["auto", "anthropic", "openai", "perplexity"],
            index=0,
            help="auto = first available (Anthropic → OpenAI → Perplexity). "
            "Pick a specific provider after pasting that key.",
        )

        st.markdown("**Reddit (live mode only)** — pick one path:")
        apify_token = st.text_input(
            "Apify token (preferred)",
            value="",
            type="password",
            help="https://console.apify.com/account/integrations",
            key="ui_apify_token",
        )
        st.caption("— or Reddit official API —")
        reddit_client_id = st.text_input(
            "Reddit client ID",
            value="",
            type="password",
            key="ui_reddit_id",
        )
        reddit_client_secret = st.text_input(
            "Reddit client secret",
            value="",
            type="password",
            key="ui_reddit_secret",
        )
        reddit_user_agent = st.text_input(
            "Reddit user agent",
            value=os.getenv(
                "REDDIT_USER_AGENT", "CustomerPainResearchAgent/1.0 by your_username"
            ),
            key="ui_reddit_ua",
        )

        if st.button("💾 Save keys to .env file", use_container_width=True):
            env_path = PROJECT_ROOT / ".env"
            existing = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
            lines = existing.splitlines() if existing else []
            # Prefer newly pasted values; fall back to whatever is in the session env
            kv = {
                "APIFY_TOKEN": (apify_token or "").strip() or os.getenv("APIFY_TOKEN", ""),
                "REDDIT_CLIENT_ID": (reddit_client_id or "").strip()
                or os.getenv("REDDIT_CLIENT_ID", ""),
                "REDDIT_CLIENT_SECRET": (reddit_client_secret or "").strip()
                or os.getenv("REDDIT_CLIENT_SECRET", ""),
                "REDDIT_USER_AGENT": (reddit_user_agent or "").strip(),
                "ANTHROPIC_API_KEY": (anthropic_key or "").strip()
                or os.getenv("ANTHROPIC_API_KEY", ""),
                "OPENAI_API_KEY": (openai_key or "").strip()
                or os.getenv("OPENAI_API_KEY", ""),
                "PERPLEXITY_API_KEY": (perplexity_key or "").strip()
                or os.getenv("PERPLEXITY_API_KEY", ""),
            }
            kept = [
                ln
                for ln in lines
                if not any(ln.startswith(f"{k}=") or ln.startswith(f"{k} =") for k in kv)
            ]
            for k, v in kv.items():
                if v and str(v).strip():
                    kept.append(f"{k}={v.strip()}")
            env_path.write_text("\n".join(kept).rstrip() + "\n", encoding="utf-8")
            st.success(f"Saved to {env_path.name}")

    st.markdown("### Run options")
    collector = st.selectbox(
        "Collector",
        options=["auto", "apify", "praw", "demo"],
        index=3 if dry_run else 0,
        help="auto = Apify if token set, else Reddit API",
        disabled=dry_run,
    )
    if dry_run:
        collector = "demo"

    skip_llm = st.checkbox(
        "Skip LLM (quick plumbing test only)",
        value=False,
        help="Produces weak heuristic results — leave unchecked for real research.",
    )

    max_posts = st.slider("Max posts to analyze", 20, 300, DEFAULT_MAX_POSTS, 5)
    time_filter = st.selectbox(
        "Time window",
        options=["week", "month", "year", "all", "day"],
        index=["week", "month", "year", "all", "day"].index(DEFAULT_TIME_FILTER)
        if DEFAULT_TIME_FILTER in ["week", "month", "year", "all", "day"]
        else 1,
    )
    top_n = st.slider("Top pains to return", 3, 10, 5)

    st.divider()
    st.caption("Need help? See README.md for where to get free/trial API keys.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
st.title("🔍 Customer Pain Research Agent")
st.markdown(
    "Enter a **niche**, **subreddits**, and **keywords** — then run research. "
    "The agent scrapes Reddit conversations, finds real complaints, and ranks the top pains."
)

col_a, col_b = st.columns(2)
with col_a:
    niche = st.text_input(
        "Niche",
        value=DEFAULT_NICHE,
        help="Who are the customers you're researching?",
    )
    subreddits_raw = st.text_area(
        "Subreddits",
        value="\n".join(DEFAULT_SUBREDDITS),
        height=140,
        help="One per line (or comma-separated). No need for r/ prefix.",
    )
with col_b:
    keywords_raw = st.text_area(
        "Keywords / pain terms",
        value="\n".join(DEFAULT_KEYWORDS),
        height=140,
        help="Words that show up in complaints and product talk.",
    )
    st.info(
        "**WordPress demo is pre-filled** (from The Startup Ideas Podcast example). "
        "Change anything, or hit **Run research** as-is."
    )

# Status chips
c1, c2, c3 = st.columns(3)
with c1:
    if dry_run:
        st.success("Mode: Demo data")
    else:
        st.warning("Mode: Live Reddit")
with c2:
    has_llm = bool(
        (anthropic_key or "").strip()
        or (openai_key or "").strip()
        or (perplexity_key or "").strip()
        or _env_has("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "PERPLEXITY_API_KEY")
    )
    if skip_llm:
        st.info("LLM: skipped")
    elif (openai_key or "").strip() or (
        _env_has("OPENAI_API_KEY")
        and not (anthropic_key or "").strip()
        and not _env_has("ANTHROPIC_API_KEY")
    ):
        st.warning("LLM: OpenAI key present — must be valid")
    elif has_llm:
        st.success("LLM: key detected")
    else:
        st.error("LLM: add a key in the sidebar")
with c3:
    if dry_run:
        st.success("Reddit keys: not needed")
    elif (apify_token or "").strip() or _env_has("APIFY_TOKEN"):
        st.success("Reddit: Apify")
    elif (reddit_client_id or "").strip() or _env_has("REDDIT_CLIENT_ID"):
        st.success("Reddit: official API")
    else:
        st.error("Reddit: add Apify or Reddit keys")

st.divider()
run_clicked = st.button("🚀 Run research", type="primary", use_container_width=True)

if run_clicked:
    subreddits = _split_list(subreddits_raw)
    keywords = _split_list(keywords_raw)

    if not niche.strip():
        st.error("Please enter a niche.")
        st.stop()
    if not subreddits:
        st.error("Please enter at least one subreddit.")
        st.stop()
    if not keywords:
        st.error("Please enter at least one keyword.")
        st.stop()
    if not skip_llm and not has_llm:
        st.error(
            "Add at least one LLM API key in the sidebar (Anthropic recommended), "
            "or check “Skip LLM” for a rough test."
        )
        st.stop()
    if not dry_run:
        has_reddit = bool(
            (apify_token or "").strip()
            or (reddit_client_id or "").strip()
            or _env_has("APIFY_TOKEN", "REDDIT_CLIENT_ID")
        )
        if not has_reddit:
            st.error(
                "Live mode needs an Apify token or Reddit API keys in the sidebar. "
                "Or switch to **Demo** mode."
            )
            st.stop()

    status = st.empty()
    progress_bar = st.progress(0, text="Starting…")

    steps = {"n": 0}

    def on_progress(msg: str) -> None:
        steps["n"] += 1
        # Soft progress — we don't know exact total steps
        pct = min(0.95, 0.1 + steps["n"] * 0.15)
        progress_bar.progress(pct, text=msg)
        status.info(msg)

    # Only pass keys the user actually typed. Empty + clear_empty_keys means:
    # "don't force a value" unless they chose a specific provider that needs clearing.
    # If they pasted a new key, it overrides. Ambient env is used when fields are blank
    # UNLESS they clicked Clear (keys already popped) or they force a provider.
    req = ResearchRequest(
        niche=niche.strip(),
        subreddits=subreddits,
        keywords=keywords,
        max_posts=max_posts,
        time_filter=time_filter,
        top_n=top_n,
        collector=collector if not dry_run else "demo",
        dry_run=dry_run,
        skip_llm=skip_llm,
        apify_token=(apify_token or "").strip() or None,
        anthropic_api_key=(anthropic_key or "").strip() or None,
        openai_api_key=(openai_key or "").strip() or None,
        perplexity_api_key=(perplexity_key or "").strip() or None,
        reddit_client_id=(reddit_client_id or "").strip() or None,
        reddit_client_secret=(reddit_client_secret or "").strip() or None,
        reddit_user_agent=(reddit_user_agent or "").strip() or None,
        clear_empty_keys=False,
        llm_provider=llm_provider,
    )

    with st.spinner(
        "Research running… Demo ≈ 30–90s. Live Reddit (Apify) ≈ 2–6 minutes "
        "(scraping + AI ranking). Status updates appear above."
    ):
        response = run_research(req, progress=on_progress)

    if not response.ok:
        progress_bar.progress(1.0, text="Failed")
        status.empty()
        st.error(response.error or "Research failed.")
        if response.error and (
            "401" in response.error
            or "invalid" in response.error.lower()
            or "rejected" in response.error.lower()
        ):
            st.info(
                "**Quick fix:** Sidebar → **Clear LLM keys from this session** → "
                "paste a brand-new key from the provider → set **Which LLM to use?** "
                "to that provider → Run again."
            )
        st.stop()

    progress_bar.progress(1.0, text="Complete")
    status.success("Research complete.")
    st.session_state["last_result"] = response.result
    st.session_state["last_json_path"] = (
        str(response.json_path) if response.json_path else None
    )
    st.session_state["last_export"] = (
        response.result.to_export_dict() if response.result else None
    )

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
result = st.session_state.get("last_result")
export = st.session_state.get("last_export")
json_path = st.session_state.get("last_json_path")

if result and export:
    st.divider()
    st.header("Results")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Posts collected", result.posts_collected)
    m2.metric("Posts analyzed", result.posts_analyzed)
    m3.metric("Collector", result.collector_used)
    m4.metric("LLM", f"{result.llm_provider}")

    if result.summary:
        st.markdown("### Executive summary")
        st.write(result.summary)

    dl_col1, dl_col2 = st.columns([1, 3])
    with dl_col1:
        st.download_button(
            label="⬇️ Download JSON",
            data=json.dumps(export, indent=2, ensure_ascii=False),
            file_name=f"pains_{result.niche[:30].replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True,
        )
    with dl_col2:
        if json_path:
            st.caption(f"Also saved on disk: `{json_path}`")

    st.markdown("### Top customer pains")
    if not result.top_pains:
        st.warning("No pain points extracted. Try broader keywords or more subreddits.")
    else:
        for pain in result.top_pains:
            color = _intensity_color(pain.intensity_score)
            with st.container(border=True):
                st.markdown(
                    f"### #{pain.rank} · {pain.title}  \n"
                    f"<span style='color:{color};font-weight:700'>"
                    f"Intensity {pain.intensity_score}/100</span>"
                    f" · `{pain.category}`",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**Description**  \n{pain.description}")
                st.markdown(f"**Desired outcome**  \n{pain.desired_outcome}")

                s1, s2, s3, s4 = st.columns(4)
                s1.metric("Frequency", pain.frequency)
                s2.metric("Upvotes", pain.upvote_signal)
                s3.metric("Emotion", pain.emotional_language_score)
                s4.metric("Recency", pain.recency_score)

                if pain.evidence:
                    st.markdown("**Evidence**")
                    for ev in pain.evidence:
                        quote = ev.quote.strip()
                        if len(quote) > 320:
                            quote = quote[:317] + "..."
                        link = f" — [source]({ev.url})" if ev.url else ""
                        sub = f"r/{ev.subreddit}" if ev.subreddit else ""
                        st.markdown(
                            f"> {quote}  \n"
                            f"> <small>{sub} · ↑{ev.upvotes} · {ev.source_type}{link}</small>",
                            unsafe_allow_html=True,
                        )

elif not run_clicked:
    st.markdown("---")
    st.markdown(
        """
### How to use this (2 minutes)

1. **Leave Demo mode on** the first time (sidebar).
2. Paste an **LLM API key** in the sidebar (Anthropic is easiest).
3. Click **Run research** — the WordPress example is already filled in.
4. Read the top pains below, or **Download JSON**.

When you're ready for real Reddit data, switch to **Live Reddit**, add an **Apify token**
(or Reddit API keys), and run again.
"""
    )
