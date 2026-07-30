# Step D — Market test: SiteSafe Ops

**Offer:** WordPress breach recovery + harden + tested-update care  
**Research:** Live Apify CaPRA run (2026-07-30)  
**One-pager:** [sitesafe-ops-one-pager.md](./sitesafe-ops-one-pager.md)  
**Landing page (static):** [`landing/index.html`](../../landing/index.html)

**Goal (14 days):** 1 paid cleanup **or** 3 triage calls that ask for a proposal.  
**Kill criteria:** No replies / no “what’s your price?” after ~20 honest touches → re-run research or tighten niche.

---

## 1. What you ship this week

| Asset | Location | Action |
|-------|----------|--------|
| One-pager | `docs/offers/sitesafe-ops-one-pager.md` | Internal truth |
| Landing copy + HTML | `landing/index.html` | Host or open locally; swap CTA URL |
| Triage form fields | Below (+ optional Google Form / Tally / Typeform) | Collect leads |
| Reddit-safe checklist post | Below | Post when relevant; value first |
| Agency outreach script | Below | 10 messages |
| Tracking sheet | Section 7 | Log every touch |

---

## 2. Landing page — copy (also in HTML)

### SEO / browser title
SiteSafe Ops — WordPress breach recovery & update care

### Hero
**Your free security plugin said you were fine.**  
**Google and the malware disagreed.**

Subhead:  
We recover compromised WordPress sites, clean what free tools miss, and run tested updates so the next plugin release doesn’t take production down.

**Primary CTA:** Book a free 15-minute triage  
**Secondary CTA:** Request a cleanup quote

### Three pillars
1. **Recover** — Full cleanup after malware, redirects, and SEO collapse — not a superficial scan.  
2. **Harden** — Baseline that assumes free Wordfence/Sucuri alone is not enough.  
3. **Steady updates** — Theme/plugin updates checked so Elementor/Astra/LMS surprises don’t become unbillable emergencies.

### Who it’s for
- Site owners who were hacked *with* security plugins installed  
- Sites deindexed or “gone down the drain” in Google after a breach  
- Agencies tired of client fires and $50 care plans that can’t fund real response  

### Who it’s not for
- Enterprise MSSP / 24-7 SOC contracts  
- “Install one more free plugin” DIY only  
- Non-WordPress stacks  

### How it works
1. Triage (15 min) — hack vs update-break, host, backups, symptoms  
2. Recover & harden — cleanup + baseline + written notes on what failed  
3. Optional care — monthly tested updates + security checks + short report  

### Pricing signal (honest ranges)
- Emergency cleanup: typically **$400–$1,500** / site (scope-dependent)  
- Care plans: from **$99/mo** / site · agency packs available  
Exact quote after triage — no scare-pricing in the form.

### Trust / process
- Scope in writing before work  
- We don’t claim “unhackable forever”  
- Care clients get priority / discounted incident work  

### Final CTA
Same as hero — one calendar or form link.

### Hosting the landing (pick one)
1. **Fastest:** Open `landing/index.html` locally to review; paste copy into [Carrd](https://carrd.co) / Framer / Notion public page  
2. **GitHub Pages:** enable Pages on this repo, publish `/landing` (or root)  
3. **Your domain:** point to any static host; set `BOOKING_URL` in the HTML  

Replace `YOUR_BOOKING_LINK` and `YOUR_EMAIL` in `landing/index.html` before sharing publicly.

---

## 3. Triage form — fields

Use Google Form, Tally, Typeform, or Calendly intake questions.

### Required
| Field | Type | Why |
|-------|------|-----|
| Full name | text | Contact |
| Email | email | Contact |
| Site URL(s) | url / long text | Scope |
| Role | select: Site owner / Agency / Other | Messaging |
| What’s wrong? | multi: Hacked/malware · SEO/Google issues · Redirects · Broken after update · Not sure · Want prevention only | Route to offer |
| When did you notice? | text | Urgency |
| Security plugins installed? | text (e.g. Wordfence free/pro, Sucuri…) | Live pain #1 |
| Hosting provider | text | Context |
| Do you have a recent backup you’re confident in? | select: Yes / No / Not sure | Recovery path |
| Anything else we should know? | long text | — |
| Permission to reply by email | checkbox | Compliance hygiene |

### Optional (high value)
| Field | Type |
|-------|------|
| Approx. monthly revenue at risk (stores) | select bands |
| Number of sites (agencies) | number |
| Last WordPress / plugin update date | text |
| Google Search Console issues? | yes/no + notes |
| Preferred start | ASAP / This week / Just exploring |
| Budget comfort | select: Under $500 / $500–1.5k / $1.5k+ / Prefer monthly care |

### After submit (you do)
1. Reply within 4 business hours  
2. 15-min call or async questions  
3. Written quote: cleanup fixed fee **or** harden audit **or** care plan  

### Quote email skeleton

```text
Subject: Triage notes + quote for [site]

Hi [name],

From what you shared:
- Symptoms: …
- Likely track: [breach recovery / update-break / harden-only]

Proposed next step:
1) [Cleanup / audit] — $[X] — includes […]
2) Optional ongoing care — $[Y]/mo — tested updates + checks

Not included: …
Timeline: …
If you want to proceed, reply YES and we’ll send a simple agreement + start checklist.

— [You]
```

---

## 4. Reddit-safe checklist post (value first)

**Rules:** Help first. No “DM me for security.” Link to landing **only** if relevant and allowed; prefer profile/website field. Paraphrase research; don’t paste private client data.

### Title options
- After a WordPress hack: cleanup order of operations (checklist)  
- Free security plugins didn’t stop malware — what to do next (field notes)  
- Theme/plugin update broke production — triage before you roll more updates  

### Body (copy/paste, edit lightly)

```markdown
**Field notes from cleaning WP messes** (not a host/plugin promo).

If you’re dealing with malware, weird redirects, or GSC freefall — especially *with* Wordfence/Sucuri free installed — a useful order of operations:

### 1. Assume “scan clean” is not “site clean”
Hosting “nothing found” and a green plugin badge can both be wrong. Look for:
- unexpected admin users
- modified `wp-config.php`, `.htaccess`, `mu-plugins`, theme `functions.php`
- outbound redirects / spam injections
- scheduled tasks you didn’t create

### 2. Take the site off the open web if you can
Maintenance mode / restrict access. Rotate all salts/passwords (WP admin, host, DB, FTP/SFTP, related emails).

### 3. Patch is necessary but not sufficient
If you were hit by something like a REST/API RCE class issue: updating core alone is not enough. You still need a full artifact cleanup (files + DB), not just a version bump.

### 4. Prefer restore-from-known-good + re-apply content when possible
If you have a **verified** pre-compromise backup, restore + re-secure often beats endless file whack-a-mole. If the backup was never restore-tested, treat it as untrusted until proven.

### 5. Re-crawl SEO reality
Search Console: sitemap errors, manual actions, sudden deindex. Cleanup without SEO follow-through still feels like “the site is dead.”

### 6. Only then: updates on a leash
After you’re clean, stop blind auto-updates on fragile stacks (page builders, LMS, cache). Stage or spot-check production paths (home, checkout, login, key templates).

### 7. Write down what failed
Plugin X free didn’t stop Y. Host said Z. That’s how you avoid the same week next quarter.

Happy to answer questions on the checklist in-thread. I’m not going to spam DMs — fix the process first.
```

### If someone asks “who can do this for me?”
Short reply:

```text
I run a small recovery + care practice (cleanup, harden, tested updates). 
Happy to do a free 15-min triage — link in profile / [landing]. 
If you’d rather DIY, the checklist above is the path.
```

---

## 5. Agency outreach (10 messages)

### Where
LinkedIn, email, WP Facebook groups (follow group rules), existing network. Avoid cold spammy Reddit DMs.

### Script (short)

```text
Subject: White-label WP cleanup when free security plugins fail

Hi [name],

Quick question for agencies managing client WordPress sites:

When a client gets hacked *with* Wordfence/Sucuri free on — or an Elementor/theme update breaks production — do you handle that in-house or refer out?

I’m piloting a white-label recovery + monthly “tested updates + security checks” pack (you keep the client relationship; I do the ops). Pilot pricing for the first few agencies.

If useful, I can send a one-pager or do a 15-min call. If not, no worries.

[You]
```

### Follow-up (day 4)

```text
Circling back once — even a “we handle in-house” is helpful so I don’t nudge again.
```

---

## 6. Meta / ads (optional, only after landing works)

- Don’t buy ads until the page loads and CTA works.  
- Start with static Concept A: cracked “protected” badge + hero line.  
- $20–50/day max for a few days; optimize for **triage bookings**, not vanity clicks.  
- Full Meta API agent is later (SIP 03) — manual Boost/Ads Manager is fine.

---

## 7. Tracking sheet (copy to Notion/Sheets)

| Date | Channel | Asset | Who/where | Outcome | Next step |
|------|---------|-------|-----------|---------|-----------|
| | Reddit / LinkedIn / Email / Ad | checklist / landing / DM | | no reply / reply / call / paid | |

**Weekly review**
- Touches  
- Replies  
- Calls  
- Quotes sent  
- Revenue  

---

## 8. 14-day calendar

| Days | Focus |
|------|--------|
| 1–2 | Fill `YOUR_BOOKING_LINK` + email in `landing/index.html`; publish page; create form |
| 1–2 | Soft-launch: 3 friends/colleagues review clarity |
| 3–5 | 3 helpful Reddit/community comments using checklist (no spam) |
| 3–7 | 10 agency outreaches |
| 7–14 | Deliver pilot cleanup/audit even at discount if needed |
| 14 | Keep / kill / pivot message using tracking sheet |

---

## 9. Success definition (from PLAN)

**Done when:** offer is in front of the same audience type and you get replies, signups, or calls.

Then: productize runbooks → optional tools → only later full ad automation loop.
