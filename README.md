# Customer Pain Research Agent

A marketing research agent inspired by **Cody Schneider’s system** on *The Startup Ideas Podcast*.

**What it does:** take a target niche + subreddits + keywords → scrape real Reddit conversations → extract and rank the **top 5 customer pain points** by frequency, intensity, and recency → output clean JSON (with real quotes + sources) ready for a creative/ad generation agent.

Think of it as a **virtual research employee** you can run on demand or on a schedule.

---

## Roadmap & success plan

Product success criteria, phases (research → business ideas → market back to the community), and “pick up here next” notes live in **[PLAN.md](PLAN.md)**.

## Quick start — browser UI (recommended)

You do **not** need to learn the terminal. Use the web interface.

### Mac (easiest)

1. Install **Python 3.12+** once from [python.org/downloads](https://www.python.org/downloads/) if you don’t have it (check “Add to PATH” / allow installer defaults).
2. In Finder, open the project folder **Customer Pain Research Agent**.
3. **Double-click** `start_ui.command`.
   - First launch may take 1–2 minutes (it installs dependencies automatically).
   - If macOS says the file can’t be opened: right-click → **Open** → confirm.
4. Your browser opens at **http://localhost:8501**.
5. In the sidebar:
   - Leave **Demo** mode on for the first try.
   - Paste an **LLM API key** (Anthropic recommended) under **API keys**.
6. Click **🚀 Run research** (WordPress example is pre-filled).
7. Read the top pains on the page, or click **Download JSON**.

Leave the black Terminal window open while you use the app. Close it (or press Ctrl+C) to stop the server.

### From Terminal (alternative)

```bash
cd "Customer Pain Research Agent"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### What the UI gives you

| Feature | Details |
|---------|---------|
| Form fields | Niche, subreddits, keywords |
| Demo mode | Practice with sample Reddit-style data (no Reddit keys) |
| Live mode | Real Reddit via Apify or official Reddit API |
| API keys | Paste in the sidebar; optional “Save to .env” |
| Results | Top pains, quotes, scores, downloadable JSON |

### Defaults (WordPress podcast example)

| Input | Default |
|-------|---------|
| Niche | WordPress site owners and agency owners |
| Subreddits | `Wordpress`, `webdev`, `SEO`, `webhosting`, `WooCommerce` |
| Keywords | plugin, slow, performance, security, maintenance, Yoast, frustrating, hate, broken, wish |
| Posts | ~175 |
| Time window | last month |
| Output | top **5** pains |

**Sample schema:** [`sample_output/pains_wordpress_2026-07-29.json`](sample_output/pains_wordpress_2026-07-29.json)

### CLI (optional — automation / cron)

```bash
python research_agent.py --dry-run
python research_agent.py
```

---

## How to get API keys

### Apify (preferred Reddit source)

1. Create a free account at [apify.com](https://apify.com)
2. Open [Console → Integrations](https://console.apify.com/account/integrations)
3. Copy your **API token** into `.env` as `APIFY_TOKEN=`
4. Free tier includes monthly platform credits — enough to prototype

The agent uses the community actor **`trudax/reddit-scraper-lite`** (posts + comments, pay-per-result). Override with `APIFY_REDDIT_ACTOR` if you prefer another Reddit actor.

### Reddit API / PRAW (fallback)

1. Log into Reddit → [prefs/apps](https://www.reddit.com/prefs/apps)
2. **Create app** → type **script**
3. Note the client ID (under the app name) and secret
4. Set in `.env`:

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=CustomerPainResearchAgent/1.0 by your_reddit_username
```

### Anthropic Claude (recommended LLM)

1. [console.anthropic.com](https://console.anthropic.com/)
2. Create an API key → `ANTHROPIC_API_KEY=`
3. Optional model override: `ANTHROPIC_MODEL=claude-sonnet-5` (or `claude-sonnet-4-6`)

### OpenAI

1. [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. `OPENAI_API_KEY=`
3. Optional: `OPENAI_MODEL=gpt-4o`

### Perplexity (optional web-grounded alternative)

1. [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api)
2. `PERPLEXITY_API_KEY=`
3. Optional: `PERPLEXITY_MODEL=sonar-pro`

**Provider preference when multiple keys are set:** Anthropic → OpenAI → Perplexity.

---

## Example commands

```bash
# Defaults = WordPress podcast example
python research_agent.py

# Explicit WordPress run
python research_agent.py \
  --niche "WordPress site owners and agency owners" \
  --subreddits Wordpress webdev SEO webhosting WooCommerce \
  --keywords plugin slow performance security maintenance Yoast frustrating hate broken wish \
  --max-posts 175 \
  --time-filter month

# Different niche
python research_agent.py \
  --niche "solo e-commerce founders on Shopify" \
  --subreddits shopify ecommerce entrepreneurial \
  --keywords shipping refunds apps slow checkout frustrating chargeback \
  --max-posts 150

# Force PRAW instead of Apify
python research_agent.py --collector praw

# Force Apify
python research_agent.py --collector apify

# Offline demo corpus + LLM ranking
python research_agent.py --dry-run

# Plumbing test without any LLM (heuristic stub — not for real research)
python research_agent.py --dry-run --skip-llm

# Debug logging
python research_agent.py --dry-run --log-level DEBUG
```

---

## Project structure

```
Customer Pain Research Agent/
├── start_ui.command           # Mac: double-click to open the web UI
├── app.py                     # Browser UI (Streamlit)
├── research_agent.py          # CLI entrypoint (cron / automation)
├── requirements.txt
├── .env.example
├── README.md
├── sample_output/
│   └── pains_wordpress_2026-07-29.json
└── agent/
    ├── config.py              # Defaults, env loading, WordPress demo config
    ├── models.py              # Pydantic models (posts, pains, export schema)
    ├── collectors.py          # Apify + PRAW + demo collectors
    ├── filters.py             # Complaint pre-filter + token-budget packing
    ├── llm.py                 # Anthropic / OpenAI / Perplexity client
    ├── analyzer.py            # Ranking prompt + JSON hydration
    ├── pipeline.py            # Shared run_research() for UI + CLI
    └── output.py              # Rich console + timestamped JSON files
```

---

## How the agent works

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  Collect    │ →  │  Filter      │ →  │  LLM rank   │ →  │  Output      │
│  Apify/PRAW │    │  complaints  │    │  top 5      │    │  console+JSON│
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

1. **Collect** posts + top comments from target subreddits (keyword search + recent feed), last month by default.
2. **Filter** for complaint language (`frustrating`, `hate`, `wish there was`, `broken`, …) and keyword relevance — keeps LLM cost down and signal high.
3. **Analyze** with a carefully designed ranking prompt:
   - Distinct pain points only (near-duplicates merged)
   - Real quotes + Reddit URLs (no invented evidence)
   - **Desired outcome** (Jobs-to-be-Done) for each pain
   - **Intensity 0–100** ≈ frequency × upvotes × emotional language × recency
4. **Emit** top 5 to the terminal and `output/pains_<niche>_<date>.json`.

### Intensity scoring (what the model optimizes)

```
intensity ≈ 0.30·frequency + 0.25·upvotes + 0.25·emotion + 0.20·recency
```

(all components normalized 0–100 before weighting)

---

## Output schema (for creative/ad agents)

```json
{
  "niche": "...",
  "subreddits": ["..."],
  "keywords": ["..."],
  "top_pains": [
    {
      "rank": 1,
      "title": "...",
      "description": "...",
      "desired_outcome": "...",
      "intensity_score": 88,
      "frequency": 14,
      "emotional_language_score": 82,
      "recency_score": 74,
      "upvote_signal": 1240,
      "category": "performance",
      "evidence": [
        {
          "quote": "...",
          "url": "https://www.reddit.com/...",
          "subreddit": "Wordpress",
          "upvotes": 214,
          "source_type": "post"
        }
      ],
      "keywords_matched": ["slow", "plugin"]
    }
  ],
  "summary": "...",
  "generated_at": "..."
}
```

See the full example in [`sample_output/`](sample_output/).

---

## Scheduling (cron / Railway / Render)

The CLI is **stateless** and exits with meaningful codes — ideal for cron or a worker.

| Exit code | Meaning |
|-----------|---------|
| 0 | Success |
| 2 | Missing Reddit config |
| 3 | Collection failure |
| 4 | Empty results |
| 5 | Missing LLM config |
| 6 | LLM failure |
| 7 | Could not write JSON |

### Cron example (weekly Monday 9:00)

```cron
0 9 * * 1 cd /path/to/Customer\ Pain\ Research\ Agent && .venv/bin/python research_agent.py >> logs/agent.log 2>&1
```

### Railway / Render

1. Deploy the repo as a **worker** or **cron job**
2. Set the same env vars as `.env` in the host dashboard
3. Command: `python research_agent.py`
4. Persist or download the `output/` folder (volume, S3, or email the JSON)

---

## Extending later

| Idea | How to approach |
|------|-----------------|
| **Facebook Ads Library** | Add `agent/collectors_meta.py` using Apify’s Facebook Ads Library actors; map creatives → competitor pain claims; merge into the same `PainPoint` schema |
| **YouTube transcripts** | Apify YouTube scrapers or unofficial transcript APIs; chunk comments/transcripts; reuse `analyzer.py` prompt with a `source: youtube` field |
| **G2 / Capterra reviews** | Review scrapers → same filter + rank pipeline |
| **Multi-niche batch** | Wrap CLI in a small loop over a `niches.yaml` file; write one JSON per niche |
| **Creative agent handoff** | Point your ad-copy agent at `output/*.json` → use `title`, `desired_outcome`, and `evidence.quote` as hooks |
| **Slack / email report** | After `save_json`, post summary via webhook |
| **Better Apify actors** | Set `APIFY_REDDIT_ACTOR` to a pain-specific actor if one is maintained in the Apify Store |
| **Embeddings cluster** | Pre-cluster posts with embeddings before LLM to scale past ~200 posts |

The `ResearchResult` / `PainPoint` models in `agent/models.py` are the integration contract — keep them stable and add optional fields carefully.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No Reddit data source configured` | Set `APIFY_TOKEN` or Reddit PRAW vars, or use `--dry-run` |
| `No LLM API key found` | Set `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `PERPLEXITY_API_KEY` |
| Apify run fails / empty | Check token, account credits, and actor name; try `--collector praw` |
| PRAW 401 / 403 | Verify client id/secret and user agent; app type must be **script** |
| Rate limits | Agent retries LLM calls; for Reddit, lower `--max-posts` or space out scheduled runs |
| Weak / generic pains | Add more complaint keywords; tighten subreddits; increase `--max-posts` |
| Token / context errors | Filter already packs ≤ ~80 posts; reduce `--max-posts` further if needed |

---

## Design decisions (short)

- **Apify first:** more reliable for production prototypes than managing Reddit OAuth edge cases; PRAW remains a free fallback.
- **Pre-filter before LLM:** complaint markers + keywords cut noise and cost.
- **Strict evidence rules in the prompt:** quotes and URLs must come from the payload — reduces hallucination.
- **Desired outcome field:** makes the JSON directly useful for ads and landing pages (JTBD-style).
- **`--dry-run` demo corpus:** non-technical users can verify install + LLM path without Reddit setup.

---

## License

MIT — use it, schedule it, fork it, feed it into your ad engine.

---

## Credits

Research workflow inspired by **Cody Schneider** / *The Startup Ideas Podcast* — systematizing Reddit pain mining for idea validation and marketing angles.
