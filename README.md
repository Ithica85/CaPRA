# CaPRA — Customer Pain Research Agent

**Repo:** [github.com/Ithica85/CaPRA](https://github.com/Ithica85/CaPRA)

A **virtual research employee** inspired by **Cody Schneider** on *The Startup Ideas Podcast* (“Build Marketing Agents”).

**What it does today (SIP Step 01 — Research the pain):**

1. Take a **niche + subreddits + keywords**
2. Pull real **Reddit** conversations (Live via Apify, or Demo offline)
3. Extract and rank the **top 5 customer pain points** (frequency × intensity × recency + emotion)
4. Export clean **JSON** (quotes, URLs, desired outcomes) ready for idea selection and later creative/ad agents

```text
Reddit communities → ranked pains → pick a bet → idea one-pager
  → market test (same communities + later ads) → learn → repeat
```

---

## What we’re doing right now

We’re not building the full marketing-agent stack yet (creative gen, Meta Ads API, warehouse, always-on cloud loop). We’re **proving Step 01** on the **WordPress** niche from the podcast, then walking a short human-in-the-loop path before paid ads at scale.

| Focus | Detail |
|-------|--------|
| **Niche** | WordPress site owners and agency owners |
| **Why WordPress** | Large market, real plugin/performance/security/maintenance pain, thin AI competition (podcast context) |
| **This agent’s job** | Rank real pains with evidence — not invent product ideas alone |
| **Our extra loop** | Bet selection → business one-pager → market back to the same communities *before* full Meta automation |

### Current status

| Item | Status |
|------|--------|
| Demo mode (practice, no Reddit keys) | Working |
| Live Reddit (Apify) + LLM ranking | Ready |
| Browser UI + CLI | Working |
| JSON export to `output/` | Working |
| WordPress defaults | Live Apify research done (2026-07-30) |
| First offer (GTM) | **SiteSafe Ops** — breach recovery + tested-update care |
| Opportunity scoring / idea packs | Manual docs (not in-app yet) |
| Creative / Meta / warehouse / schedule | Roadmap — see [PLAN.md](PLAN.md) |

### Four steps (A–D)

| Step | Status | Where |
|------|--------|--------|
| **A** Live WordPress research | Done | Local `output/` / your download |
| **B** Pick a bet | Done | Security + safe updates |
| **C** One-pager + creative brief | Done | [docs/offers/sitesafe-ops-one-pager.md](docs/offers/sitesafe-ops-one-pager.md) |
| **D** Market test | **Assets ready — execute** | [docs/offers/sitesafe-ops-step-d-market-test.md](docs/offers/sitesafe-ops-step-d-market-test.md) · [landing/index.html](landing/index.html) |

**Your next actions:** set booking link + email in the landing page, publish it, run outreach (playbook).

Full success criteria and SIP map: **[PLAN.md](PLAN.md)**. More docs: **[docs/README.md](docs/README.md)**.

### How this maps to the podcast “marketing agent”

Cody’s full agent needs: unified data, a decision loop on a cadence, and cloud-hosted code reading live business data.

| SIP step | Article | CaPRA |
|----------|---------|--------|
| **01 Research** | Reddit pains + outcomes, rank-stack | **This repo (built)** |
| **02 Creative** | Image/video ads from angles | Later (JSON handoff ready) |
| **03 Publish** | Meta Marketing API writes | Later |
| **04 Data layer** | Warehouse, ad → revenue | Later |
| **05 Host** | Railway / cloud cadence | Later |

---

## Quick start — browser UI (recommended)

### Mac

1. Install **Python 3.12+** from [python.org/downloads](https://www.python.org/downloads/) if needed.
2. Open this project folder in Finder.
3. **Double-click** `start_ui.command`.
   - First launch may take 1–2 minutes (installs dependencies).
   - If macOS blocks it: right-click → **Open** → confirm.
4. Browser opens at **http://localhost:8501**.
5. Sidebar:
   - **Demo** first (no Reddit keys).
   - Paste an **LLM API key** (Anthropic recommended).
   - For **Live**: also paste **Apify** token.
6. Click **Run research** (WordPress defaults are pre-filled).
7. Read top pains on the page, or **Download JSON**.

Leave the Terminal window open while the app runs. Ctrl+C stops the server.

### From Terminal

```bash
git clone https://github.com/Ithica85/CaPRA.git
cd CaPRA
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add keys
streamlit run app.py
```

### Demo vs Live

| Mode | Needs | Use for |
|------|--------|---------|
| **Demo** | LLM key only (optional: skip LLM for heuristic stub) | Practice UI + pipeline |
| **Live Reddit** | Apify **or** Reddit API + LLM key | Real research (Step A) |

### Defaults (WordPress / podcast example)

| Input | Default |
|-------|---------|
| Niche | WordPress site owners and agency owners |
| Subreddits | `Wordpress`, `webdev`, `SEO`, `webhosting`, `WooCommerce` |
| Keywords | plugin, slow, performance, security, maintenance, Yoast, frustrating, hate, broken, wish |
| Posts | ~175 |
| Time window | last month |
| Output | top **5** pains → `output/pains_*.json` |

**Sample schema:** [`sample_output/pains_wordpress_2026-07-29.json`](sample_output/pains_wordpress_2026-07-29.json)

### CLI (automation / cron later)

```bash
python research_agent.py --dry-run              # demo data + LLM
python research_agent.py --dry-run --skip-llm   # offline plumbing only
python research_agent.py                        # Live (needs keys in .env)
python research_agent.py --collector apify
python research_agent.py --collector praw
```

---

## API keys

Copy `.env.example` → `.env`, or paste keys in the UI sidebar.

### Apify (preferred for Live Reddit)

1. [apify.com](https://apify.com) → free account  
2. [Console → Integrations](https://console.apify.com/settings/integrations) (or Account → Integrations)  
3. `APIFY_TOKEN=...`  

Uses community actor **`trudax/reddit-scraper-lite`**. Override with `APIFY_REDDIT_ACTOR` if needed.

### Reddit API / PRAW (fallback)

```env
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=CustomerPainResearchAgent/1.0 by your_reddit_username
```

Create a **script** app at [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps).

### LLM (at least one)

| Provider | Env | Notes |
|----------|-----|--------|
| **Anthropic** (recommended) | `ANTHROPIC_API_KEY` | Default model `claude-sonnet-5` |
| OpenAI | `OPENAI_API_KEY` | Optional `OPENAI_MODEL` |
| Perplexity | `PERPLEXITY_API_KEY` | Optional web-grounded path |

**Preference when multiple are set:** Anthropic → OpenAI → Perplexity.  
In the UI, pin a provider if a stale system key is hijacking selection.

---

## How the agent works

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  Collect    │ →  │  Filter      │ →  │  LLM rank   │ →  │  Output      │
│  Apify/PRAW │    │  complaints  │    │  top 5      │    │  console+JSON│
│  or Demo    │    │              │    │             │    │              │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

1. **Collect** posts + top comments (keyword + recent feed).
2. **Filter** complaint language + keyword relevance (cost + signal).
3. **Analyze** with a ranking prompt:
   - Distinct pains (near-duplicates merged)
   - Real quotes + Reddit URLs only
   - **Desired outcome** (JTBD) per pain
   - **Intensity 0–100** ≈ frequency × upvotes × emotion × recency
4. **Emit** to the UI/CLI and `output/pains_<niche>_<date>.json`.

LLM JSON is repaired automatically when models emit messy quotes; Demo can fall back to heuristic ranking if the model still fails.

### Intensity (what the model optimizes)

```
intensity ≈ 0.30·frequency + 0.25·upvotes + 0.25·emotion + 0.20·recency
```

---

## Output schema (handoff for later creative agents)

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

Full example: [`sample_output/`](sample_output/). Live results land in `output/` (gitignored).

---

## Project structure

```
CaPRA/
├── start_ui.command           # Mac double-click launcher
├── app.py                     # Streamlit UI
├── research_agent.py          # CLI (future cron)
├── requirements.txt
├── .env.example
├── PLAN.md                    # Success plan, SIP map, next steps
├── README.md
├── sample_output/             # Example JSON schema
├── output/                    # Live/demo run results (gitignored)
└── agent/
    ├── config.py              # Defaults, env, WordPress demo config
    ├── models.py              # Posts, pains, export schema
    ├── collectors.py          # Apify + PRAW + demo
    ├── filters.py             # Complaint filter + packing
    ├── llm.py                 # Anthropic / OpenAI / Perplexity
    ├── analyzer.py            # Ranking prompt + JSON hydration
    ├── pipeline.py            # Shared run_research() for UI + CLI
    └── output.py              # Console + timestamped JSON
```

---

## Example commands

```bash
# WordPress Live (defaults)
python research_agent.py

python research_agent.py \
  --niche "WordPress site owners and agency owners" \
  --subreddits Wordpress webdev SEO webhosting WooCommerce \
  --keywords plugin slow performance security maintenance Yoast frustrating hate broken wish \
  --max-posts 175 \
  --time-filter month

# Another niche
python research_agent.py \
  --niche "solo e-commerce founders on Shopify" \
  --subreddits shopify ecommerce entrepreneurial \
  --keywords shipping refunds apps slow checkout frustrating chargeback \
  --max-posts 150

python research_agent.py --collector apify
python research_agent.py --collector praw
python research_agent.py --dry-run
python research_agent.py --dry-run --skip-llm
python research_agent.py --dry-run --log-level DEBUG
```

---

## Scheduling (planned — Phase 5)

CLI is stateless with exit codes for cron / Railway / Render later.

| Exit code | Meaning |
|-----------|---------|
| 0 | Success |
| 2 | Missing Reddit config |
| 3 | Collection failure |
| 4 | Empty results |
| 5 | Missing LLM config |
| 6 | LLM failure |
| 7 | Could not write JSON |

```cron
0 9 * * 1 cd /path/to/CaPRA && .venv/bin/python research_agent.py >> logs/agent.log 2>&1
```

---

## Roadmap (summary)

Details and checklists live in **[PLAN.md](PLAN.md)**.

| Horizon | Work |
|---------|------|
| **Now** | Steps A–D: Live WP research → bet → one-pager → market test |
| **Next** | Creative brief / idea-pack tooling; optional opportunity scorer |
| **Later** | Creative generation (SIP 02), Meta publish (03), warehouse (04), cloud schedule (05) |
| **As needed** | Ads Library, YouTube/transcripts, reviews (entropy + thin Reddit) |

Integration contract: keep `ResearchResult` / `PainPoint` in `agent/models.py` stable.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No Reddit data source configured` | Set `APIFY_TOKEN` or PRAW vars, or use Demo / `--dry-run` |
| `No LLM API key found` | Set Anthropic / OpenAI / Perplexity key |
| API key 401 | Clear bad keys in UI/session; paste a fresh key; pin provider |
| Apify empty / fail | Check token + credits; try `--collector praw` |
| PRAW 401 / 403 | Script app type; correct id/secret/user agent |
| JSON parse errors | Parser repairs most LLM messiness; re-run; check model |
| Weak / generic pains | More complaint keywords; tighter subs; higher `--max-posts` |
| Stale UI | Restart Streamlit / free port 8501 |

---

## Design decisions (short)

- **Apify first** for Live Reddit reliability; PRAW as free fallback.
- **Pre-filter before LLM** for signal and cost.
- **Strict evidence rules** — quotes/URLs from the payload only.
- **Desired outcome** field for ads and landing pages (JTBD).
- **Demo corpus** so the pipeline can be verified without Reddit.
- **Research first, product second** — Live pains choose the WordPress wedge, not the reverse.

---

## License

MIT — use it, schedule it, fork it, feed it into your ad engine.

---

## Credits

Workflow inspired by **Cody Schneider** / *The Startup Ideas Podcast* — Reddit pain mining as the research step of a marketing agent (“virtual employee”), plus community-first validation before full ad automation.
