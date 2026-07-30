"""
Pain extraction & ranking via LLM.

The ranking prompt is the product: quality of top-5 pains depends on clear
instructions for distinctness, evidence, intensity formula, and desired outcomes.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from agent.filters import pack_posts_for_llm
from agent.llm import LLMClient, LLMError
from agent.models import Evidence, PainPoint, RedditPost

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expert customer research analyst and Jobs-to-be-Done interviewer.
Your job is to read real Reddit conversations and surface the most important
customer pain points for a defined niche — the kind a founder or marketer
could immediately turn into product ideas, landing-page copy, or ads.

You are rigorous, evidence-based, and allergic to vague fluff.
You never invent quotes or URLs. You only use evidence present in the data.
You merge near-duplicates into a single pain. You prefer specific pains
(e.g. "plugin updates silently break checkout") over generic ones
(e.g. "WordPress is hard").
"""


def build_ranking_prompt(
    niche: str,
    keywords: list[str],
    snippets: list[dict],
    top_n: int = 5,
) -> str:
    """
    Construct the user message for pain extraction + ranking.

    Design notes (why this prompt works):
    - Separates DESCRIPTION vs DESIRED OUTCOME (critical for ad creative later)
    - Forces real quotes + URLs (grounding / no hallucination)
    - Explicit intensity formula: frequency × upvotes × emotion × recency
    - Demands DISTINCT pains (anti-duplicate)
    - Asks for category tags for downstream filtering
    - JSON-only output for reliable parsing
    """
    payload = json.dumps(snippets, ensure_ascii=False, indent=None)
    keywords_str = ", ".join(keywords)

    return f"""\
# Mission
Analyze the Reddit posts/comments below for the niche:

**{niche}**

Research keywords used to gather this data: {keywords_str}

# What to extract
Identify the **top {top_n} distinct customer pain points**.

For each pain point provide:
1. **title** — short, sharp label (≤12 words), specific not vague
2. **description** — 2–4 sentences: who feels it, when it happens, why it hurts
3. **desired_outcome** — what the customer wants instead (the "job" / success state)
4. **category** — one of: performance, security, pricing, workflow, support, \
reliability, complexity, migration, integrations, other
5. **frequency** — integer count of distinct posts/comments that clearly support this pain
6. **upvote_signal** — sum of upvotes (scores) across supporting posts/comments you used
7. **emotional_language_score** — 0–100: intensity of frustration/anger/desperation language
8. **recency_score** — 0–100: how recent the evidence is (100 = very recent, 0 = old/unknown)
9. **intensity_score** — 0–100 overall priority score using this formula:

   intensity ≈ clamp(0–100,
       0.30 * frequency_norm
     + 0.25 * upvote_norm
     + 0.25 * emotional_language_score
     + 0.20 * recency_score
   )

   where frequency_norm and upvote_norm are your 0–100 normalizations across the set.
   Weight pains that are BOTH frequent AND emotionally charged highest.
   A single viral rant with weak frequency should not outrank a widespread chronic pain
   unless the viral post reveals a uniquely severe, underserved problem.

10. **evidence** — 2–4 items, each with:
    - quote: verbatim or lightly trimmed real quote from the data (never invent)
    - url: exact Reddit URL from the data (empty string only if truly missing)
    - subreddit: community name
    - upvotes: score if known else 0
    - source_type: "post" or "comment"
11. **keywords_matched** — which research keywords this pain relates to

# Quality bar (non-negotiable)
- Return EXACTLY {top_n} pains unless fewer truly exist (then return fewer — never pad).
- Pains MUST be distinct: merge "site is slow" + "poor Core Web Vitals" if same root cause.
- Prefer pains that imply a product or service opportunity.
- Ignore pure tech support trivia unless it signals a systemic product gap.
- Prefer first-person lived experience over abstract industry debate.
- Rank by intensity_score descending (rank 1 = worst / most urgent pain).
- If evidence is thin for a candidate, drop it rather than fabricate.

# Output format
Return a single JSON object only (no markdown fences, no commentary).

JSON rules (critical — invalid JSON fails the run):
- Escape every double quote inside strings as \\"
- No trailing commas
- No smart/curly quotes — use straight " only
- Keep each evidence quote ≤ 200 characters; trim with …
- Prefer single-line string values (no raw line breaks inside quotes)

{{
  "summary": "2–4 sentence executive brief of what customers in this niche are struggling with most right now.",
  "pains": [
    {{
      "rank": 1,
      "title": "...",
      "description": "...",
      "desired_outcome": "...",
      "category": "performance",
      "frequency": 12,
      "upvote_signal": 840,
      "emotional_language_score": 78,
      "recency_score": 70,
      "intensity_score": 82,
      "evidence": [
        {{
          "quote": "...",
          "url": "https://www.reddit.com/...",
          "subreddit": "Wordpress",
          "upvotes": 214,
          "source_type": "post"
        }}
      ],
      "keywords_matched": ["slow", "plugin", "performance"]
    }}
  ]
}}

# Reddit data (posts + top comments)
{payload}
"""


def extract_and_rank_pains(
    llm: LLMClient,
    posts: list[RedditPost],
    niche: str,
    keywords: list[str],
    top_n: int = 5,
) -> tuple[list[PainPoint], str]:
    """
    Run the LLM ranking pipeline.

    Returns (pain_points, executive_summary).
    Raises LLMError if the model fails after retries / unparseable output.
    """
    if not posts:
        logger.warning("No posts to analyze — returning empty pain list")
        return [], "No Reddit posts were available to analyze."

    snippets = pack_posts_for_llm(posts, max_posts=min(80, max(20, len(posts))))
    if not snippets:
        return [], "Posts were empty after packing for the LLM."

    user_prompt = build_ranking_prompt(niche, keywords, snippets, top_n=top_n)
    logger.info(
        "Sending %d post snippets to %s/%s for pain ranking…",
        len(snippets),
        llm.provider,
        llm.model,
    )

    raw = llm.complete(SYSTEM_PROMPT, user_prompt, temperature=0.2, max_tokens=8192)
    try:
        data = _parse_json_response(raw)
    except LLMError as first_err:
        # One repair pass: models often emit unescaped quotes in evidence strings.
        logger.warning("Primary JSON parse failed (%s); requesting repair…", first_err)
        repair_prompt = (
            "The following text was meant to be a single JSON object with keys "
            '"summary" and "pains", but it is invalid JSON.\n'
            "Return ONLY corrected valid JSON (no markdown, no commentary). "
            "Preserve the same content. Escape all double quotes inside strings.\n\n"
            f"BROKEN OUTPUT:\n{raw[:12000]}"
        )
        try:
            repaired_raw = llm.complete(
                "You fix broken JSON. Output valid JSON only.",
                repair_prompt,
                temperature=0.0,
                max_tokens=8192,
            )
            data = _parse_json_response(repaired_raw)
        except Exception as repair_err:
            logger.error("JSON repair also failed: %s", repair_err)
            raise first_err from repair_err

    pains = _hydrate_pains(data.get("pains") or data.get("top_pains") or [], top_n)
    summary = str(data.get("summary") or "").strip()
    if not summary and pains:
        summary = f"Top pain themes for {niche}: " + "; ".join(
            p.title for p in pains[:3]
        )

    logger.info("Extracted %d ranked pain points", len(pains))
    return pains, summary


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        return fence.group(1).strip()
    return text


def _light_json_cleanup(text: str) -> str:
    """Cheap mechanical fixes before / alongside json-repair."""
    # Smart / curly quotes → straight
    text = (
        text.replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
    )
    # Trailing commas before } or ]
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    # Missing commas between adjacent objects/arrays: }{ ][ }[
    text = re.sub(r"\}\s*\{", "},{", text)
    text = re.sub(r"\]\s*\[", "],[", text)
    text = re.sub(r"\}\s*\[", "},[", text)
    text = re.sub(r"\]\s*\{", "],{", text)
    # Python-ish literals
    text = re.sub(r"\bTrue\b", "true", text)
    text = re.sub(r"\bFalse\b", "false", text)
    text = re.sub(r"\bNone\b", "null", text)
    return text


def _as_result_dict(data: Any) -> dict[str, Any] | None:
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return {"pains": data, "summary": ""}
    return None


def _parse_json_response(raw: str) -> dict[str, Any]:
    """
    Robust JSON extraction for LLM output.

    Handles markdown fences, leading prose, trailing commas, missing commas,
    and (via json-repair) unescaped quotes inside strings — a common failure mode
    when models copy Reddit quotes into JSON.
    """
    text = _strip_code_fence(raw)
    candidates: list[str] = [text]
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        blob = text[start : end + 1]
        if blob not in candidates:
            candidates.append(blob)

    last_err: Exception | None = None
    for cand in candidates:
        for variant in (cand, _light_json_cleanup(cand)):
            try:
                data = _as_result_dict(json.loads(variant))
                if data is not None:
                    return data
            except json.JSONDecodeError as exc:
                last_err = exc

            # Aggressive repair for broken LLM JSON (unescaped quotes, etc.)
            try:
                from json_repair import repair_json

                repaired = repair_json(variant, return_objects=True)
                data = _as_result_dict(repaired)
                if data is not None:
                    logger.info("Recovered LLM JSON via json-repair")
                    return data
            except Exception as exc:
                last_err = exc
                logger.debug("json-repair failed on candidate: %s", exc)

    # Last resort: pull any complete pain-like objects we can still salvage
    partial = _recover_partial_pains(text)
    if partial is not None:
        logger.warning(
            "Using partial JSON recovery (%d pains)",
            len(partial.get("pains") or []),
        )
        return partial

    logger.error(
        "Failed to parse LLM JSON: %s\nRaw (trunc): %s",
        last_err,
        raw[:500],
    )
    raise LLMError(
        f"Could not parse LLM JSON response: {last_err or 'invalid JSON'}"
    )


def _recover_partial_pains(text: str) -> dict[str, Any] | None:
    """
    Scan for brace-balanced objects that look like pain entries.
    Works when the full document is corrupt but individual objects are valid.
    """
    pains: list[dict[str, Any]] = []
    i = 0
    while i < len(text):
        if text[i] != "{":
            i += 1
            continue
        obj_str, next_i = _extract_balanced_brace(text, i)
        if not obj_str:
            i += 1
            continue
        i = next_i
        for variant in (obj_str, _light_json_cleanup(obj_str)):
            try:
                obj = json.loads(variant)
            except json.JSONDecodeError:
                try:
                    from json_repair import repair_json

                    obj = repair_json(variant, return_objects=True)
                except Exception:
                    continue
            if isinstance(obj, dict) and obj.get("title") and obj.get("description"):
                pains.append(obj)
                break

    if not pains:
        return None

    summary = ""
    m = re.search(r'"summary"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
    if m:
        try:
            summary = json.loads(f'"{m.group(1)}"')
        except json.JSONDecodeError:
            summary = m.group(1)

    return {"summary": summary, "pains": pains}


def _extract_balanced_brace(s: str, start: int) -> tuple[str | None, int]:
    """Return (substring, index_after) for a {...} region, respecting strings."""
    if start >= len(s) or s[start] != "{":
        return None, start
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(s)):
        c = s[i]
        if in_str:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1], i + 1
    return None, start


def _hydrate_pains(raw_pains: list[Any], top_n: int) -> list[PainPoint]:
    pains: list[PainPoint] = []
    for i, item in enumerate(raw_pains):
        if not isinstance(item, dict):
            continue
        try:
            evidence_raw = item.get("evidence") or []
            evidence: list[Evidence] = []
            for e in evidence_raw:
                if not isinstance(e, dict):
                    continue
                quote = str(e.get("quote") or "").strip()
                if not quote:
                    continue
                evidence.append(
                    Evidence(
                        quote=quote[:500],
                        url=str(e.get("url") or ""),
                        subreddit=str(e.get("subreddit") or ""),
                        upvotes=int(e.get("upvotes") or 0),
                        source_type=(
                            "comment"
                            if str(e.get("source_type", "post")).lower() == "comment"
                            else "post"
                        ),
                    )
                )

            title = str(item.get("title") or "").strip()
            description = str(item.get("description") or "").strip()
            if not title or not description:
                continue

            pain = PainPoint(
                rank=int(item.get("rank") or (i + 1)),
                title=title[:200],
                description=description,
                desired_outcome=str(item.get("desired_outcome") or "").strip()
                or "Not specified",
                intensity_score=int(item.get("intensity_score") or 50),
                frequency=int(item.get("frequency") or len(evidence) or 1),
                emotional_language_score=int(
                    item.get("emotional_language_score") or 50
                ),
                recency_score=int(item.get("recency_score") or 50),
                upvote_signal=int(item.get("upvote_signal") or 0),
                category=str(item.get("category") or "general"),
                evidence=evidence,
                keywords_matched=[
                    str(k) for k in (item.get("keywords_matched") or []) if k
                ],
            )
            pains.append(pain)
        except Exception as exc:
            logger.warning("Skipping malformed pain item: %s (%s)", item, exc)

    # Sort by intensity, re-rank 1..N
    pains.sort(key=lambda p: p.intensity_score, reverse=True)
    for idx, p in enumerate(pains[:top_n], start=1):
        p.rank = idx
    return pains[:top_n]
