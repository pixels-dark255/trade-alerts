# Trade Alerts India — automated EXIM alert business

Every morning, 4 small agents run on their own:

1. **Watcher** (`scrape.py`): reads new DGFT notifications, public notices and trade notices.
2. **Analyst** (`summarize.py`): Claude turns each notice into a plain-English summary with an action, deadline, HS codes, sector, impact and a Hindi line.
3. **Publisher** (`digest.py`): sends HS-matched emails (Pro/Firm daily; Free weekly, spread across the week) and posts top alerts to a Telegram channel.
4. **SEO builder** (`sitegen.py`): rebuilds the website. Every notice gets its own Google-indexable page with a signup form.

**Your job: about 10 minutes a day.** Read the `[ops]` email, glance at the Telegram posts, and reply to customers.

Stack (free tiers): **Supabase** (database) · **GitHub Actions** (daily schedule) · **GitHub Pages** (website) · **Resend** (email) · **Telegram** · **Claude API** (the only real running cost).

---

## Money

| Item | Cost |
|---|---|
| Claude API (Haiku, ~10–30 notices/day) | ~₹300–800/mo |
| Domain (optional, for email sending) | ~₹800/yr |
| Supabase, GitHub, Resend, Telegram | ₹0 on free tiers (Resend free = 100 emails/day, 3,000/month; Pro is $20/mo when you outgrow it) |
| Razorpay Payment Links | ~2% per payment, no setup fee |
| **Month-1 total** | **under ₹2,000 of your ₹5k** |

Target mix for ₹50k/month: **100 Pro × ₹299 + 10 Firm × ₹1,999 ≈ ₹50k.**

Competitor reference: Cusbuzz SME costs ₹3,499 for 6 months (duty search plus 5 alerts). Free weekly newsletters from consultancies also exist. Our edge: matched to your HS codes, plain language, Hindi line, covers more than one authority, and cheap.

---

## 7-day setup (about 1 hour a day)

**Day 1: accounts and source check**
- Create accounts: GitHub, Supabase, Resend, Anthropic Console (add ₹500 of credit), Telegram.
- On your laptop: `pip install -r requirements.txt`, then `cd src && python check_sources.py`.
  - All 3 sources should say `OK` with rows. If you see `FAIL` or 0 rows, send me the output and I'll fix the parser.

**Day 2: database**
- Supabase → New project → SQL Editor → paste `supabase/schema.sql` → Run.
- Copy the Project URL, `anon` key and `service_role` key from Settings → API.

**Day 3: email and Telegram**
- Resend: add and verify your domain, then create an API key. `MAIL_FROM` = `Alerts <alerts@yourdomain.in>`.
- Telegram: talk to @BotFather → `/newbot` → copy the token. Create a public channel and add the bot as admin. `TELEGRAM_CHANNEL` = `@yourchannel`.

**Day 4: deploy**
- Push this folder to a **public** GitHub repo. Pages is free for public repos, and secrets stay hidden.
- Repo → Settings → Pages → Source: **GitHub Actions**.
- Settings → Secrets → Actions. Add these secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_ANON_KEY`, `ANTHROPIC_API_KEY`, `RESEND_API_KEY`, `MAIL_FROM`, `OWNER_EMAIL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL`.
- Add these variables: `SITE_NAME`, `SITE_URL` (e.g. `https://<user>.github.io/<repo>`).
- Actions → daily-alerts → **Run workflow**. Check the site, the Telegram channel and the `[ops]` email.

**Day 5: quality check**
- Read 10 AI summaries against the official PDFs. If any are wrong, tell me and I'll tune the prompt.
- Subscribe yourself as Free. In Supabase, change your row's plan to `pro` and test the daily email.

**Day 6: payments**
- Razorpay → create Payment Links for Pro (₹299) and Firm (₹1,999). This needs PAN and bank KYC.
- Add them as repo variables `PAY_LINK_PRO` and `PAY_LINK_FIRM`.
- After someone pays, set their `plan` to `pro` or `firm` in Supabase. That's 1 minute; we can automate it later with a webhook.

**Day 7: distribution**
- Submit `SITE_URL/sitemap.xml` to Google Search Console.
- Share the Telegram channel in relevant communities, such as r/IndianExporters and exporter LinkedIn groups.

---

## Growth playbook (after setup, inside 15 minutes a day)
- **SEO (automatic):** people search for "DGFT notification 23/2025-26". Our page explains it and asks them to sign up.
- **Telegram (automatic):** top 5 alerts a day go to the channel, each with a signup link.
- **LinkedIn (5 min/day, manual):** repost the day's biggest alert as a short post.
- **Firm plan (10 min, twice a week):** message 5 CA, CHA or export consultants on LinkedIn and offer a free month. One firm customer is worth about 7 Pro customers.
- Market size: about 1.73 lakh exporting MSMEs in FY 2024-25.

## Phase 2 (once you have about 20 paying users)
- Add CBIC customs notifications and BIS QCOs in `config/sources.yaml`.
- Automate the Razorpay webhook, so a payment upgrades the plan by itself.
- WhatsApp delivery for Pro.
- Sell the same scraper and summariser as an Apify Actor (USD income).

## Safety notes
- Only email people who opted in through the form (it records consent). Never import scraped contact lists. India's DPDP rules are being phased in.
- Every email and page says the summaries are AI-generated and not legal advice. Keep it that way.
- If a government site changes its layout, the `[ops]` email will flag `0 rows`. Tell me and I'll fix the parser.

## Run tests
`pytest -q` runs offline tests with no keys needed.
