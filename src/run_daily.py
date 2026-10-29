"""Orchestrator — runs every morning (GitHub Actions cron). Owner gets one ops report email."""
from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

import envfile
envfile.load()
envfile.clean()

import digest
import scrape
import sitegen
import summarize
from db import DB

IST = timezone(timedelta(hours=5, minutes=30))
DRY = os.getenv("DRY_RUN") == "1"
MAX_NEW = int(os.getenv("MAX_NEW_PER_RUN", "60"))     # cost guard for the AI step
MAX_TG = int(os.getenv("MAX_TELEGRAM_PER_RUN", "5"))
MAX_EMAILS = int(os.getenv("MAX_EMAILS_PER_DAY", "95"))  # Resend free tier = 100/day
# collect = scrape + AI (must run from an Indian IP: DGFT blocks GitHub's US servers)
# publish = Telegram + email + website (runs on GitHub)
STAGES = {x.strip() for x in os.getenv("STAGES", "collect,publish").split(",")}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows console safety
    except Exception:
        pass
    cfg = yaml.safe_load(Path(__file__).resolve().parents[1].joinpath("config/sources.yaml").read_text(encoding="utf-8"))
    sectors = cfg["sectors"]
    db, report, errors = DB(), [], []
    now = datetime.now(IST)

    new, sent = [], 0
    if "collect" in STAGES:
        new = collect(cfg, sectors, db, report, errors)
    if "publish" in STAGES:
        sent = publish(sectors, db, now, report, errors)
    return finish(report, errors, now, new, sent)


def collect(cfg, sectors, db, report, errors) -> list:
    # 1. Watch
    found = []
    for src in cfg["sources"]:
        try:
            rows = scrape.scrape_source(src)
            report.append(f"{src['id']}: {len(rows)} rows on page")
            if not rows:
                errors.append(f"{src['id']}: page parsed but 0 rows — layout may have changed")
            found += rows
        except Exception as ex:
            errors.append(f"{src['id']}: {ex!r}")
    seen = db.existing_ids([n["id"] for n in found])
    new = [n for n in found if n["id"] not in seen][:MAX_NEW]
    report.append(f"new notices: {len(new)}")

    # 2. Analyse + store
    for n in new:
        try:
            pdf = scrape.fetch_pdf(n["url"]) if n.get("url") else None
            n["raw_text"] = scrape.pdf_text(pdf)
            s = summarize.summarize(n, sectors, pdf=pdf)
            n.update(summary=s, impact=s["impact"], hs_codes=s["hs_codes"], sectors=s["sectors"])
            db.insert_notice(n)
        except Exception as ex:
            errors.append(f"summarise {n['id']} ({n['title'][:50]}): {ex!r}")
    return new


def publish(sectors, db, now, report, errors) -> int:
    # Health check: has the collector (your PC / Indian server) run recently?
    if not db.notices_since((now - timedelta(days=3)).isoformat()):
        errors.append("no new notices stored in 3 days — is the collector on your PC running?")

    # 3. Publish — Telegram (free channel = marketing)
    fresh = [n for n in db.notices_since((now - timedelta(days=2)).isoformat())
             if n.get("summary") and not n.get("posted_telegram") and n.get("impact") != "low"]
    if os.getenv("TELEGRAM_BOT_TOKEN") and not DRY:
        posted = []
        for n in digest.rank(fresh)[:MAX_TG]:
            try:
                digest.post_telegram(digest.telegram_text(n))
                posted.append(n["id"])
            except Exception as ex:
                errors.append(f"telegram: {ex!r}")
        db.mark_posted(posted)
        report.append(f"telegram posts: {len(posted)}")

    # 4a. Paid plans: renewal reminders (3 days before + on the day), back to free 3 days after
    try:
        renew_paid(db, now, report, errors)
    except Exception as ex:
        errors.append(f"renewals: {ex!r}")

    # 4b. Welcome email for new sign-ups: trial start + matching notices from the last 90 days
    sent = 0
    try:
        recent = [n for n in db.all_notices()
                  if n.get("summary") and str(n.get("notice_date") or "") >= (now - timedelta(days=90)).date().isoformat()]
        for sub in db.active_subscribers():
            if sub.get("welcome_sent_at") or sent >= MAX_EMAILS:
                continue
            if sub.get("hs_prefixes") or sub.get("sectors"):
                items = digest.rank([n for n in recent if digest.matches(n, sub)])
            else:
                items = digest.rank([n for n in recent if n.get("impact") in ("high", "medium")])[:5]
            subject, body = digest.render_welcome(sub, items)
            if not DRY:
                digest.send_email(sub["email"], subject, body,
                                  f"{digest.SITE_URL}/unsubscribe.html?t={sub['unsubscribe_token']}")
                db.mark_welcomed(sub["id"])
            sent += 1
        report.append(f"welcome emails: {sent}")
    except Exception as ex:
        errors.append(f"welcome emails: {ex!r}")

    # 4. Publish — email
    day = [n for n in db.notices_since((now - timedelta(hours=26)).isoformat()) if n.get("summary")]
    week = [n for n in db.notices_since((now - timedelta(days=7)).isoformat())
            if n.get("summary") and n.get("impact") in ("high", "medium")]
    subs = sorted(db.active_subscribers(), key=lambda s: s["plan"] == "free")  # paid first
    for sub in subs:
        if sent >= MAX_EMAILS:
            errors.append(f"daily email cap {MAX_EMAILS} reached — upgrade Resend or raise MAX_EMAILS_PER_DAY")
            break
        paid = sub["plan"] in ("pro", "firm")
        if paid:
            items = digest.rank([n for n in day if digest.matches(n, sub)])
        elif int(sub["id"].replace("-", ""), 16) % 7 == now.weekday():  # free digests spread over the week
            items = digest.rank(week)[:5]
        else:
            continue
        if not items:
            continue
        clients = []
        if sub["plan"] == "firm":
            try:
                r = db.c.get("/firm_clients", params={"select": "name,hs_prefixes", "subscriber_id": f"eq.{sub['id']}",
                                                      "order": "position"})
                clients = r.json() if r.status_code == 200 else []
            except Exception as ex:
                errors.append(f"firm clients {sub['id']}: {ex!r}")
        subject, body = digest.render_email(sub, items, weekly=not paid, clients=clients)
        if DRY:
            sent += 1
            continue
        try:
            digest.send_email(sub["email"], subject, body,
                              f"{digest.SITE_URL}/unsubscribe.html?t={sub['unsubscribe_token']}")
            db.log_delivery(sub["id"], [n["id"] for n in items])
            sent += 1
        except Exception as ex:
            errors.append(f"email {sub['email']}: {ex!r}")
    report.append(f"emails sent: {sent}{' (dry run)' if DRY else ''}")

    # 5. Rebuild SEO site
    try:
        report.append(f"site pages: {sitegen.build(db.all_notices(), sectors)}")
        import pilots
        report.append(f"pilot pages: {len(pilots.build('public'))}")
        import extras
        report.append(f"extra pages: {len(extras.build('public'))}")
        since = (now - timedelta(hours=26)).isoformat()
        r = db.c.get("/pilot_interest", params={"select": "offer,name,company,email,phone,details", "created_at": f"gte.{since}"})
        if r.status_code == 200:
            for x in r.json():
                report.append(f"PILOT SIGN-UP ({x['offer']}): {x.get('name')}, {x.get('company')}, {x.get('email')}, "
                              f"{x.get('phone') or ''} - {x.get('details') or ''}")
        r = db.c.get("/data_requests", params={"select": "kind,email,details,created_at", "done_at": "is.null"})
        if r.status_code == 200:
            for x in r.json():
                errors.append(f"DATA REQUEST to handle within 30 days ({x['kind']}): {x['email']} - {x.get('details') or ''} "
                              f"(received {str(x['created_at'])[:10]}; mark done_at in Supabase when finished)")
        # retention (privacy policy): unsubscribed > 90 days, pilot interest and data requests > 12 months
        cut90 = (now - timedelta(days=90)).isoformat()
        cut365 = (now - timedelta(days=365)).isoformat()
        if not DRY:
            db.c.delete("/subscribers", params={"status": "eq.unsubscribed", "unsubscribed_at": f"lt.{cut90}"})
            db.c.delete("/pilot_interest", params={"created_at": f"lt.{cut365}"})
            db.c.delete("/data_requests", params={"created_at": f"lt.{cut365}"})
    except Exception as ex:
        errors.append(f"site build: {ex!r}")
    return sent


def renew_paid(db, now, report, errors) -> None:
    from datetime import date
    today = now.date()
    for sub in db.active_subscribers():
        if sub["plan"] not in ("pro", "firm"):
            continue
        if sub.get("trial"):                                  # automatic 14-day trial for every new sign-up
            if not sub.get("paid_until"):
                continue
            left = (date.fromisoformat(str(sub["paid_until"])[:10]) - today).days
            if left < 0:
                if not DRY:
                    db.downgrade(sub["id"])
                sub["plan"] = "free"
                report.append(f"trial ended, moved to free: {sub['email']}")
            elif left in (3, 0):
                report.append(f"trial ends in {left} day(s): {sub['email']}")
                if not DRY and os.getenv("RESEND_API_KEY"):
                    subject, body = digest.render_trial_end(sub, left)
                    digest.send_email(sub["email"], subject, body,
                                      f"{digest.SITE_URL}/unsubscribe.html?t={sub['unsubscribe_token']}")
            continue
        if not sub.get("paid_until"):
            errors.append(f"{sub['email']} is on {sub['plan']} with no paid_until date — set it in Supabase")
            continue
        left = (date.fromisoformat(str(sub["paid_until"])[:10]) - today).days
        if left < -3:
            if not DRY:
                db.downgrade(sub["id"])
            sub["plan"] = "free"
            report.append(f"moved to free (not renewed): {sub['email']}")
        elif left in (3, 0):
            report.append(f"renewal due in {left} day(s): {sub['email']} ({sub['plan']})")
            if not DRY and os.getenv("RESEND_API_KEY"):
                subject, body = digest.render_renewal(sub, left)
                digest.send_email(sub["email"], subject, body,
                                  f"{digest.SITE_URL}/unsubscribe.html?t={sub['unsubscribe_token']}")


def redact(text: str) -> str:
    import re
    text = re.sub(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", "[email]", text)
    text = re.sub(r"(?<!\d)(\+?91[ -]?)?[6-9]\d{9}(?!\d)", "[phone]", text)
    text = re.sub(r"(sk-ant-|re_|eyJ)[A-Za-z0-9_.-]{8,}", "[secret]", text)
    return text


def finish(report, errors, now, new, sent) -> int:
    # 6. Owner ops report (your 2-minute daily check)
    text = "\n".join(report + (["", "ERRORS:"] + errors if errors else ["", "No errors."]))
    # GitHub Actions logs of a public repo are public: print no personal lines and no emails/phones/keys
    private = ("PILOT SIGN-UP", "DATA REQUEST", "renewal due", "moved to free", "email ", "no paid_until")
    print(redact("\n".join(l for l in text.split("\n") if not any(k in l for k in private))))
    owner = os.getenv("OWNER_EMAIL")
    if owner and not DRY and os.getenv("RESEND_API_KEY") and "publish" in STAGES:
        try:
            digest.send_email(owner, f"[ops] {'⚠ ' + str(len(errors)) + ' error(s)' if errors else 'OK'} — {now:%d %b}",
                              f"<pre>{text}</pre>", digest.SITE_URL)
        except Exception:
            traceback.print_exc()
    return 0  # problems are reported in the ops email; never block the website deploy


if __name__ == "__main__":
    sys.exit(main())
