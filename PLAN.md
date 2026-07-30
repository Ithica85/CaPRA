# Customer Pain Research Agent — Success Definition & Plan

Saved for continuation. Aligns this project with **The Startup Ideas Podcast / Cody Schneider “Build Marketing Agents”** system (Jul 2026), plus our addition: **business idea → market back to the community** before (or alongside) full paid-ad automation.

Last updated: 2026-07-30 (Steps A–D assets drafted; GTM execution in market)

**Source episode / article:** SIP — *Build Marketing Agents* (Cody Schneider).  
Full episode links in the article thread (Apple / Spotify / YouTube).

---

## Current status (as of save)

| Item | Status |
|------|--------|
| Demo mode (synthetic Reddit + LLM ranking) | Working (re-verified 2026-07-30) |
| Robust LLM JSON parse (`json-repair` + repair retry + demo fallback) | Working |
| Live Reddit via Apify + Anthropic | Ready (keys required) |
| Browser UI (`app.py` / `start_ui.command`) | Working |
| CLI (`research_agent.py`) | Working |
| JSON export to `output/` | Working |
| WordPress default niche | **Live Apify run done** (2026-07-30) |
| Step B — bet selection | **Done** — security recovery + tested updates |
| Step C — one-pager + creative brief | **Done** — `docs/offers/sitesafe-ops-one-pager.md` |
| Step D — market test assets | **Done** — landing + playbook; *execution* (publish, outreach) is on you |
| Scheduling (cron / Railway / Render) | Not built yet |
| Opportunity scoring / business idea packs | Manual (docs); not in-app yet |
| Creative / ad handoff agent | Not built yet |
| Meta Ads API + warehouse closed loop | Not built yet |

**How to run**

1. Open **http://localhost:8501** (or double-click `start_ui.command`)
2. Sidebar: Anthropic key + (for Live) Apify token
3. Demo = practice; **Live Reddit** = real research (Step 01)
4. Results: UI + `output/pains_*.json`

---

## Map to SIP article — marketing agent steps

Cody’s definition of a marketing agent (all three required for the *full* system):

1. **Unified data** across the pipeline  
2. **Decision loop** on a cadence  
3. **Code hosted in the cloud**, reading live business data  

Not a Zapier linear workflow. Not a chatbot with a personality. A **process that runs, reads its own results, and improves** — “like a virtual employee.”

### Article steps → our plan

| SIP step | What the article says | Our status | Plan home |
|----------|----------------------|------------|-----------|
| **01 — Research the pain** | Scrape Reddit for pains + desired outcomes; rank-stack; top pains. WordPress example themes: plugin layer, performance/speed, security & maintenance | **Built.** Demo + Live (Apify), LLM rank top **5** (article often says top **3** — same idea; we can shortlist to 3 in Step B) | Phase 0 done; this agent *is* Step 01 |
| **02 — Generate the creative** | Statics (e.g. Nano Banana), video (HeyGen / Seedance), vision check for brand | **Not built.** JSON handoff exists so a creative agent can consume pains without re-research | Phase 3 hooks + Phase 7 creative agent; **Next Step C** produces creative briefs first |
| **03 — Publish via Facebook Marketing API** | Writes only (publish / pause / promote); avoid abusive bulk reads | **Not built.** Mentioned as later paid channel after message works | Phase 3 (lightweight ads) → future Meta agent |
| **04 — Build the data layer** | Airbyte → ClickHouse; ads + analytics + CRM + Stripe; ad → revenue | **Not built.** Needed for the full closed loop and “ask the business questions” | Future; after first manual GTM tests |
| **05 — Host the agent** | Railway / Heroku / cloud; live data + LLM decision loop + one outcome to optimize | **Not built.** Local UI/CLI today | Phase 5 (schedule + cloud) |

### Full article loop (later system)

```text
Data warehouse → agent → Facebook Ads → data warehouse
  (kill losers, promote winners, store every creative’s prompts/scripts)
```

Entropy fixes from the article (when the agent gets stuck):

- Facebook Ads Library (competitor DNA)  
- YouTube / podcast transcripts → new angles  
- Trend scrapers (e.g. TikTok APIs) when relevant  

Those map to our **Phase 6** (expand sources) and a future creative-loop agent — **after** Step 01 is trustworthy.

### WordPress business context (from article)

- **Surface area:** ~43% of the web on WordPress; thin AI competition  
- **v1 product idea (Cody):** “Lovable for WordPress” — chat to build site; forms/CRM/plugins bundled; ~$29/mo tokens  
- **Bigger play (Greg):** AI-first versions of proven plugins — Yoast → SEO agent; WPForms → qualifying agent; WooCommerce → storekeeper; Akismet → spam  

**Our stance:** research first, product second. Live Reddit pains decide *which* wedge (plugin pain, performance, security, maintenance, etc.) is worth a one-pager and a market test — not the other way around.

### What we deliberately add (not a contradiction)

The article jumps **pains → ads → measure → iterate**.

We insert, before heavy ad spend:

- Opportunity / **bet selection**  
- **Business idea one-pager**  
- **Market back to the same communities** (organic + landing) using their language  

Fuel is the same: ranked pains + quotes + desired outcomes. Path is slightly more validation-heavy before Meta scale.

---

## What success looks like

Not only “a scraper.” A **virtual research employee** that turns real conversations into **ranked, evidence-backed pains**, then into **ideas marketed back to those communities** (and later into the full ad loop).

### Full loop (our version)

```text
Niche communities (Reddit, later Ads Library / YouTube / reviews)
    → ranked pains (quotes + URLs + desired outcomes)
    → pick a pain worth solving (bet)
    → business / product concept (one-pager)
    → positioning + offer + messaging (creative brief)
    → market back into those communities (and later Meta/Google ads)
    → learn → next niche or next pain
```

### Outcome checklist

| Layer | Success looks like |
|--------|-------------------|
| **Research (SIP 01)** | Live run → distinct pains, real quotes + Reddit URLs |
| **Ranking** | Intensity from frequency × upvotes × emotion × recency; clear desired outcome per pain |
| **Handoff** | Timestamped JSON a creative/ad agent can consume without cleanup |
| **Employee feel** | Single command or UI; progress logging; graceful errors |
| **Schedule-ready (SIP 05)** | Weekly unattended run → new files in `output/` |
| **Non-technical use** | UI path works without terminal fluency |
| **WordPress proof** | Live niche run produces actionable pains (plugin / speed / security / maintenance class) |
| **Selection** | After each run: “Pain #N is the one we’d bet on” with clear why |
| **Business idea** | Named concept: who, what, outcome, why now |
| **Offer** | Product shape + pricing hypothesis |
| **Go-to-market** | Same communities + later paid; message from real quotes |
| **Validation** | Soft test before heavy build |
| **Closed loop (SIP 03–04)** | Eventually: creatives in market, losers killed, winners scaled, ad→revenue in a warehouse |

### Simple scoreboard

| Metric | Target |
|--------|--------|
| Live run success rate | ≥ 9/10 completes with ≥ 3 solid pains |
| Evidence | Every top pain has ≥ 2 real quotes + URLs |
| Runtime (Live, ~100 posts) | Usually under ~6–8 min |
| Scheduled | Weekly unattended for 2+ weeks |
| Downstream | Creative brief / idea pack from JSON without re-research |
| Business loop | At least one pain → idea → public test in market |

---

## Immediate next work — four steps (start here)

This is the active sequence. Do them in order.

### Step A — Live WordPress research run *(SIP 01)* ✅

**Do**

1. UI → **Live Reddit** (not Demo)  
2. Keys: **Apify** + **Anthropic** (pin Anthropic if multiple LLM keys exist)  
3. Keep WordPress defaults unless you have a reason to change them:

| Input | Default |
|-------|---------|
| Niche | WordPress site owners and agency owners |
| Subreddits | `Wordpress`, `webdev`, `SEO`, `webhosting`, `WooCommerce` |
| Keywords | plugin, slow, performance, security, maintenance, Yoast, frustrating, hate, broken, wish |
| Posts / window | ~175 / last month |
| Output | top 5 pains → `output/pains_*.json` |

**Done when**

- Run completes without error  
- File in `output/` with `collector_used` = live source (`apify` or `praw`, not `demo`)  
- ≥ 3 pains with real quotes + Reddit URLs  
- Executive summary readable in one minute  

**Article check:** top themes should feel in-family with plugin layer, performance, security/maintenance (wording will differ; that’s fine).

---

### Step B — Phase 1: score pains → pick a bet ✅

**Locked bet (Live data):** Sites get hacked despite security plugins (+ package tested updates). Offer working name: **SiteSafe Ops**.

Score each of the top 5 (or shortlist to **top 3** like the article):

| Filter | Question |
|--------|----------|
| **Intensity** | Angry/desperate vs mildly annoyed? |
| **Frequency** | Many threads vs one loud rant? |
| **Willingness to pay** | Already paying for broken tools/agencies? |
| **Urgency** | Revenue/security/breakage vs nice-to-have? |
| **Audience access** | Can we reach them (Reddit, SEO, ads, agencies)? |
| **Buildability** | Wedge in weeks, not years? |
| **Competition** | Crowded giants vs underserved gap? (e.g. anti-Yoast angle is allowed) |

**Done when:** one clear **“bet”** (or explicit skip + re-run with different keywords/subs).

Optional later tooling: opportunity scorer in the app.

---

### Step C — Phase 2: idea workshop + one-pager *(feeds SIP 02)* ✅

**Artifact:** [`docs/offers/sitesafe-ops-one-pager.md`](docs/offers/sitesafe-ops-one-pager.md)

For the bet pain:

1. Restate the job — “When I’m [role], I want ___ so I can ___.”  
2. Current alternatives — plugins, freelancers, workarounds, ignore  
3. Solution wedges (3–5) — productized service, SaaS, playbook, white-label, AI-first plugin, etc.  
4. Pick one wedge  
5. **One-pager:** name, customer language, promise (from `desired_outcome`), 3-step how it works, pricing hypothesis, why win, risks  

Also produce a **creative brief** (handoff to SIP 02):

- Positioning line  
- 5–10 hooks from real quotes (paraphrase ethically; no doxxing)  
- 2–3 angle variants (including “competitor makes you work; we do the work”)  
- Landing promise + single CTA  

**Done when:** one-pager + brief are strong enough to show a smart friend / feed a creative tool.

---

### Step D — Phase 3: market test *(before full SIP 03–04)* ⬅️ **you are here (execution)**

**Assets ready:**

| Asset | Path |
|-------|------|
| Market-test playbook | [`docs/offers/sitesafe-ops-step-d-market-test.md`](docs/offers/sitesafe-ops-step-d-market-test.md) |
| Landing page | [`landing/index.html`](landing/index.html) |

Ship the smallest public test using community language:

1. Set `YOUR_BOOKING_LINK` + `YOUR_EMAIL` in the landing HTML; publish (Carrd / domain / GitHub Pages)  
2. Organic value-first checklist answers in the communities that produced the pain  
3. 10 agency outreaches (white-label pilot)  
4. Only then lightweight paid (Meta/Google) once message shows signal  

**Done when:** real replies, signups, or calls — or a clear kill and return to Step A on another pain.

**14-day win:** 1 paid cleanup **or** 3 triage calls that ask for a proposal.

---

### After the four steps (full SIP system)

| Priority | Work | SIP |
|----------|------|-----|
| Next | Creative generation agent from JSON (images/video prompts) | 02 |
| Later | Meta Marketing API publish/pause/promote agent | 03 |
| Later | Airbyte + ClickHouse (or equivalent) ad→revenue warehouse | 04 |
| Later | Railway/Render schedule + always-on decision loop | 05 |
| As needed | Ads Library, transcripts, extra sources (entropy) | article “entropy” + Phase 6 |

Article operating rhythm (when ad agent exists): ~2 ad sets/day × 5 ads; 2–3 days signal; kill worst; winners compete for budget; store every creative’s generation JSON for learning.

---

## Plan by phase (reference)

### Phase 0 — Stabilize the research employee *(mostly done — SIP 01)*

- UI + Live Reddit (Apify) + Anthropic  
- WordPress (and other niches) on demand  
- JSON export + resilient JSON parsing  

**Done when:** Anyone can run Live from the UI with keys and get a report.

---

### Phase 1 — Pain quality & “bet selection”

See **Step B**. Output: top 5 + opportunity shortlist (1–2 bets).

---

### Phase 2 — Business idea workshop (human + AI)

See **Step C**. Optional build: idea-pack generator from selected pain JSON.

---

### Phase 3 — Market back to the community

See **Step D**. Assets: positioning, hooks, landing, community GTM, proof plan.

Channel order: organic communities → landing → lightweight ads → partners/agencies.

---

### Phase 4 — Validate cheap, then build

```text
Idea one-pager
  → landing + CTA (or concierge MVP)
  → 10–20 conversations / signups
  → yes: build thin wedge
  → no: next pain from next research run
```

Prefer **concierge / manual** first when the pain is service-shaped (common for WordPress). Productize after people pay.

---

### Phase 5 — Systemize the loop *(SIP 05)*

| Cadence | Activity |
|---------|----------|
| **Weekly** | 1 Live research job |
| **Weekly** | Pick 0–1 pain to explore (or kill) |
| **Biweekly** | Idea one-pager + landing experiment if pain is strong |
| **Monthly** | Double down on what’s converting; archive the rest |

**Ops build:** Cron / Railway / Render scheduled `research_agent.py`; env keys; optional Slack/email summary.

---

### Phase 6 — Expand sources *(article entropy + thin Reddit)*

1. Facebook Ads Library  
2. YouTube / podcast transcripts  
3. Review sites (G2, etc.)  

**Done when:** multi-source data merges into the **same** pain schema.

---

### Phase 7 — Product polish & SIP 02–03 tooling

- Niche templates  
- Run history in the UI  
- Cost estimator (Apify + LLM)  
- Multi-niche batch  
- **Creative/ad generator** wired to JSON (SIP 02)  
- Later: Meta publish agent (SIP 03)  

---

## How we work together on each hot pain

1. **You run** Live research (Step A)  
2. **We review** top 5 → pick a bet (Step B)  
3. **We co-create** wedges + one-pager + creative brief (Step C)  
4. **We draft** community/landing test; **you ship** (Step D)  
5. **We read** response → build, pivot, or next pain  

---

## Map to original product brief

| Brief theme | Plan coverage |
|-------------|----------------|
| Cody-style Reddit pain mining | Live Apify + rank top 5 (SIP 01) |
| Virtual employee | UI/CLI today; schedule/cloud in Phase 5 (SIP 05) |
| Structured JSON for creative agents | `output/` + Step C brief + Phase 7 creative agent (SIP 02) |
| Graceful errors, env keys, schedule-ready | Largely done; schedule still open |
| Full ad + warehouse loop | SIP 03–04 — future after first market tests |
| **Our addition: ideas + market to community** | Steps B–D / Phases 1–4 |

**North star:**  
pain found → idea chosen → offer in market → learning (and eventually revenue)  
—not just a JSON file.

When the full SIP stack exists:  
**one dollar in, five dollars out — keep feeding it.**

---

## Key project paths

| Path | Role |
|------|------|
| `app.py` | Browser UI |
| `start_ui.command` | Mac launcher |
| `research_agent.py` | CLI / future cron |
| `agent/` | Collectors, LLM, ranking, pipeline |
| `output/` | Research JSON results |
| `sample_output/` | Example schema |
| `README.md` | Setup & usage |
| `PLAN.md` | This document |

---

## Notes from build (gotchas worth remembering)

- Anthropic model: use `claude-sonnet-5` (old dated Sonnet 4 IDs retired)  
- Do **not** send `temperature` to Claude Sonnet 5+ (deprecated → 400)  
- Stale Streamlit processes can serve old code — kill port 8501 / restart if bugs “won’t die”  
- Live Apify is capped for speed; Demo needs no Reddit keys  
- Invalid/ambient `OPENAI_API_KEY` can hijack provider selection — pin Anthropic in the UI  
- LLM may emit broken JSON (unescaped quotes in Reddit quotes) — parser repairs + demo heuristic fallback; Live still needs a successful parse or a clear error  
- Broken venv `pip` (metadata only) can break `start_ui.command` — reinstall with `get-pip.py` if `python -m pip` fails  

---

## Pick-up checklist (next session)

- [x] **Step A:** Live WordPress run (Apify) — download + `output/pains_wordpress_LIVE_from_download.json` (local)  
- [x] **Step B:** Bet locked — security recovery + tested updates (SiteSafe Ops)  
- [x] **Step C:** One-pager — `docs/offers/sitesafe-ops-one-pager.md`  
- [x] **Step D assets:** Playbook + `landing/index.html`  
- [ ] **Step D execution:** Publish landing, replace CTA placeholders, triage form live  
- [ ] **Step D execution:** 3 helpful community posts + 10 agency outreaches  
- [ ] **Step D outcome:** 1 paid cleanup or 3 proposal-stage calls (or kill/pivot)

Then: creative agent (SIP 02) → paid + warehouse (SIP 03–04) → cloud cadence (SIP 05).
