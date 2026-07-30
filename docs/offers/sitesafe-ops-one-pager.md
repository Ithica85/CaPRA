# Step C — Idea one-pager + creative brief

**Source research:** Live Apify run (2026-07-30)  
`pains_WordPress_site_owners_and_agen.json` / `output/pains_wordpress_LIVE_from_download.json`  
**Primary pains:** #1 Sites hacked despite security plugins · #2 Theme/plugin updates break live sites  
**Date:** 2026-07-30  
**Status:** Step C complete · Step D market test materials in `docs/offers/sitesafe-ops-step-d-market-test.md` and `landing/`

---

## 1. Job-to-be-done

> When I’m a **WordPress site owner or agency operator**,  
> I want **my sites to stay clean, ranked, and unbroken after updates and attacks**,  
> so I can **run the business without emergency cleanups, lost SEO, and unbillable firefighting**.

---

## 2. Current alternatives (status quo)

| Alternative | Why it fails (from Live research) |
|-------------|-------------------------------------|
| Free Wordfence / Sucuri | Clients still get malware; “very good plugins” don’t stop the breach |
| Hosting support | Often finds “nothing wrong” while SEO and malware persist |
| DIY cleanup | Manual backdoor hunting, file-by-file; REST/SQL zero-days (e.g. wp2shell) |
| Blind auto-updates | Astra / Elementor / LMS / cache updates silently break layouts & dashboards |
| “Purge All” workarounds | Temporary; not a system |
| Cheap $50 care plans | Don’t fund real incident response (from earlier demo themes; still true commercially) |

---

## 3. Solution wedges considered

| # | Wedge | Speed to $ | Fit | Notes |
|---|--------|------------|-----|-------|
| A | **Hack cleanup + harden (concierge)** | Fastest | Best | Fixed-fee incident response |
| B | **Monthly security + tested-update care** | Fast | Best | Retainer / white-label for agencies |
| C | Restore-verified backup product | Medium | Good | Product later |
| D | AI-slop plugin marketplace filter | Slow | Weak buyer | Skip for v1 |
| E | Bulk host migration tool | Slow | Niche | Only if agency inbound |

**Pick:** **A → B** (sell cleanup, convert to care). Productize only after 5–10 paid jobs.

---

## 4. The offer (one-pager)

### Name (working)

**SiteSafe Ops**  
*(alternates: CleanStack Care · Patch & Protect · WP Steady)*

### One-liner

**For WordPress owners and agencies tired of getting hacked *with* security plugins installed — and tired of updates breaking production — we clean breaches properly, restore trust/SEO, and run tested updates so it doesn’t happen again.**

### Positioning

> For **WordPress site owners and agencies** who are tired of **malware, lost rankings, and silent update breaks**,  
> we **recover the site and run a security + update care plan**  
> without **“disable all plugins” support theater or free tools that still leave you exposed**.

### Target customer

**Primary (pays in panic):**  
- Small–mid site owners hit by malware / deindexing / redirects  
- Agencies with client sites compromised (reputation + unbillable hours)

**Secondary (pays monthly):**  
- Agencies managing many WP sites who need a white-label SLA  
- Woo / content sites that can’t afford downtime after plugin updates

**Language they use (from Live):**  
“hacked,” “gone down the drain,” “doesn’t show up on Google,” “Wordfence did not stop the malware,” “sites break after theme update,” “stuck,” “exhausting to migrate”

### Core promise (desired outcome from research)

1. **Recovery:** Guided, thorough cleanup after REST/SQL-style compromises — not a superficial scan  
2. **Prevention ops:** Hardened baseline + monitoring mindset beyond “install free security plugin”  
3. **Safe change:** Updates tested / rolled carefully so Elementor/theme/LMS updates don’t nuke live UI  

### How it works (3 steps)

1. **Triage** — Confirm compromise vs update-break; inventory plugins/themes; SEO/GSC symptoms; backups  
2. **Recover & harden** — Full cleanup, patch/version hygiene, kill backdoors, baseline security config, document what failed  
3. **Steady care** — Monthly (or per-site) tested updates + security checks + short report agencies can send clients  

### Pricing hypothesis (start here — validate in conversations)

| Offer | Price band (hypothesis) | Notes |
|-------|-------------------------|--------|
| **Emergency cleanup** (1 site) | $400–$1,500 | Severity / # of sites / SEO recovery depth |
| **Harden-only audit** (not yet hacked) | $200–$500 | Funnel into care |
| **Care plan** (1 site) | $99–$249 / mo | Updates + security checks + priority incident discount |
| **Agency pack** (10–25 sites) | $799–$2,500 / mo | White-label reports; volume discount |
| **Incident add-on** for care clients | Included hours or 50% off cleanup | Improves retention |

Raise prices if Woo / revenue-critical or multi-site agency.

### Why we win vs status quo

| Them | Us |
|------|-----|
| Free plugin green checkmarks | Outcome: clean, ranked, updatable site |
| Host “nothing found” | Hands-on forensics + SEO path |
| Blind updates | Tested / staged change process |
| Generic freelancers | Repeatable runbook from real pain language |
| $50 “care” theater | Priced for real firefighting |

### Risks

| Risk | Mitigation |
|------|------------|
| Crowded security market | Lead with **“plugins failed, we recover + operate”** not another firewall brand |
| Liability of “secure forever” claims | Promise **ops + best-effort care**, not insurance; clear scope |
| Thin Live sample (17 posts) | More Live runs; 10 customer interviews before product build |
| Hard to scale concierge | Productize runbooks; only then tools |
| Agencies want white-label overnight | Start with 1–2 pilot agencies |

---

## 5. Creative brief (feeds SIP Step 02 later)

### Primary angle

**False confidence.**  
Security plugins were on. Site still got owned. Rankings died. You’re left hunting files.

### Supporting angles

1. **Update roulette** — Astra/Elementor/LMS update → layout/dashboard broken; unbillable emergency  
2. **SEO afterlife** — Sitemap/GSC issues, deindexed, “site has gone down the drain”  
3. **Agency tax** — 100 sites, host declined, migration “borderline impossible” (secondary)  
4. **Anti-DIY** — Patching core isn’t enough after RCE; cleanup must be complete  

### Positioning line (ads / landing hero)

**Your free security plugin said you were fine. Google and the malware disagreed.**

### Hooks (from Live language — paraphrase ethically; don’t dox)

1. “They had free Sucuri and Wordfence. That did not stop the malware.”  
2. “The site doesn’t show up on Google. Sitemap issues in Search Console.”  
3. “Patching WordPress alone is not enough — you must completely clean the compromise.”  
4. “Hosting found nothing wrong. The site was still owned.”  
5. “Sites breaking after the latest theme update — Elementor looks broken too.”  
6. “One plugin update can take a business offline.”  
7. “I’m tired of all the issues one plugin can cause to a business.”  
8. “UI breaks until someone logs in and hits Purge All.” (symptom of fragile stacks)  
9. “I host 100+ sites and feel stuck.” (agency variant)  
10. “Security plugins alert all day — still not safe.” (if using adjacent demo language carefully)

### Ad / post concepts (static first)

| Concept | Visual idea | Headline | CTA |
|---------|-------------|----------|-----|
| A | Green “protected” badge cracked | Protected isn’t cleaned | Get a breach triage |
| B | Google search with no brand result | Still online. Invisible to Google. | SEO + malware recovery |
| C | Calendar: “Auto-updated 3am” / broken homepage | Updates shouldn’t be a coin flip | Safe update care |
| D | Agency owner with 100 tabs | One hacked client = a week of free work | White-label care |

### Landing page (one screen)

- **Hero:** False-confidence line + CTA “Book free 15-min triage” or “Request cleanup quote”  
- **3 bullets:** Recover · Harden · Steady updates  
- **Proof plan:** anonymized before/after (GSC, malware gone), process checklist  
- **Who it’s for / not for:** WP/Woo/agencies — not enterprise MSSP replacement  
- **Single CTA:** Calendly / form / Stripe deposit for cleanup  

### Community GTM (Step D — Reddit-native)

**Do:**  
- Answer recovery threads with a clear checklist (value first)  
- Offer “I’ll review your case” only when asked or via profile/landing  
- Share a free 1-pager: “After wp2shell-style incidents: cleanup order of operations”

**Don’t:**  
- Spam r/Wordpress with “DM me for security”  
- Fear-monger without a useful checklist  

### First creative test plan (manual, pre-Meta agent)

1. Landing live with one promise + one CTA  
2. 5–10 helpful Reddit/community answers this week  
3. 10 DMs or email to agencies (LinkedIn/Facebook groups OK)  
4. Optional: $50–100/day Meta test with Concept A or B once landing converts clicks → bookings  

---

## 6. First 14-day action list (Step D kickoff)

| Day | Action |
|-----|--------|
| 1–2 | Buy domain or use Carrd/Framer one-pager; Calendly CTA |
| 1–2 | Write triage form: URL, host, plugins, symptoms, last good backup |
| 3–5 | Post 3 genuinely helpful comments/threads using checklist (no hard sell) |
| 3–7 | Outreach 10 agencies: “white-label cleanup + care pilot” |
| 7–14 | Deliver 1–2 paid cleanups OR 3 paid audits even at pilot pricing |
| 14 | Decide: double down care plan vs iterate message |

**Kill criteria:** No replies, no calls, no “what’s your price?” after 20 honest touches → re-run Live research or tighten niche (e.g. Woo-only).

**Win criteria:** 1 paid cleanup or 3 triage calls that ask for a proposal.

---

## 7. What we are not building yet

- Full “Lovable for WordPress” product  
- Another free security plugin  
- Meta Ads API agent / warehouse loop  
- AI plugin marketplace  

Those wait until cash and message are proven.

---

## 8. Handoff fields for future creative agent (from JSON)

```text
niche: WordPress site owners and agency owners
bet_pain: Sites get hacked despite running security plugins
secondary: Theme/plugin updates silently break live sites
promise: Recover breach + harden + tested updates
tone: Direct, operator-to-operator, anti-theater, not corporate MSSP
evidence_themes: Wordfence/Sucuri fail, SEO death, wp2shell/RCE cleanup, update breaks (Astra/Elementor/LMS)
cta: Book triage / cleanup quote
```

---

## North star for this offer

**pain found (Live) → bet locked (security + safe updates) → offer in market → learning → only then productize.**
