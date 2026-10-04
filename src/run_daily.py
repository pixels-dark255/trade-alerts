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


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows console safety
    except Exception:
        pass
    cfg = yaml.safe_load(Path(__file__).resolve().parents[1].joinpath("config/sources.yaml").read_text(encoding="utf-8"))
    sectors = cfg["sectors"]
    db, report, errors = DB(), [], []
    now = datetime.now(IST)

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

    # 4. Publish — email
    day = [n for n in db.notices_since((now - timedelta(hours=26)).isoformat()) if n.get("summary")]
    week = [n for n in db.notices_since((now - timedelta(days=7)).isoformat())
            if n.get("summary") and n.get("impact") in ("high", "medium")]
    sent = 0
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
        subject, body = digest.render_email(sub, items, weekly=not paid)
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
    except Exception as ex:
        errors.append(f"site build: {ex!r}")

    # 6. Owner ops report (your 2-minute daily check)
    text = "\n".join(report + (["", "ERRORS:"] + errors if errors else ["", "No errors."]))
    print(text)
    owner = os.getenv("OWNER_EMAIL")
    if owner and not DRY and os.getenv("RESEND_API_KEY"):
        try:
            digest.send_email(owner, f"[ops] {'⚠ ' + str(len(errors)) + ' error(s)' if errors else 'OK'} — {now:%d %b}",
                              f"<pre>{text}</pre>", digest.SITE_URL)
        except Exception:
            traceback.print_exc()
    return 1 if errors and not new and not sent else 0


if __name__ == "__main__":
    sys.exit(main())
