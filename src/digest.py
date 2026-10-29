"""Agent 3 — Publisher: matches alerts to subscribers and sends email / Telegram."""
from __future__ import annotations

import html
import os

import httpx

SITE_NAME = os.getenv("SITE_NAME") or "Trade Alerts India"
SITE_URL = (os.getenv("SITE_URL") or "https://example.github.io/trade-alerts").strip().rstrip("/")
ALL_SECTOR = "Services & Procedures (all exporters)"
IMPACT_ORDER = {"high": 0, "medium": 1, "low": 2}


def _cal_title(n: dict) -> str:
    s = n.get("summary") or {}
    return f"Deadline: {s.get('headline') or n['title']} ({n['authority']} {n.get('number') or ''})"[:180]


def gcal_url(n: dict) -> str:
    from datetime import date, timedelta
    from urllib.parse import urlencode
    d = date.fromisoformat(str((n.get("summary") or {})["deadline"])[:10])
    s = n.get("summary") or {}
    q = {"action": "TEMPLATE", "text": _cal_title(n),
         "dates": f"{d:%Y%m%d}/{d + timedelta(days=1):%Y%m%d}",
         "details": f"{s.get('action_required') or ''}\n\nDetails: {SITE_URL}/n/{n['id']}.html\nOfficial notice: {n.get('url') or ''}"}
    return "https://calendar.google.com/calendar/render?" + urlencode(q)


def ics_text(n: dict) -> str:
    from datetime import date, datetime, timedelta, timezone
    d = date.fromisoformat(str((n.get("summary") or {})["deadline"])[:10])
    s = n.get("summary") or {}
    esc = lambda t: str(t).replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
    return "\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//{SITE_NAME}//Alerts//EN", "BEGIN:VEVENT",
        f"UID:{n['id']}@{SITE_URL.split('//')[-1]}",
        f"DTSTAMP:{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}",
        f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}",
        f"SUMMARY:{esc(_cal_title(n))}",
        f"DESCRIPTION:{esc((s.get('action_required') or '') + ' Details: ' + SITE_URL + '/n/' + n['id'] + '.html')}",
        "BEGIN:VALARM", "TRIGGER:-P3D", "ACTION:DISPLAY", "DESCRIPTION:Deadline in 3 days", "END:VALARM",
        "END:VEVENT", "END:VCALENDAR", ""])


def calendar_links(n: dict) -> str:
    return (f' · <a href="{html.escape(gcal_url(n))}">Add to Google Calendar</a>'
            f' · <a href="{SITE_URL}/n/{n["id"]}.ics">Outlook / Apple (.ics)</a>')


def matches(notice: dict, sub: dict) -> bool:
    n_hs, s_hs = notice.get("hs_codes") or [], sub.get("hs_prefixes") or []
    n_sec, s_sec = set(notice.get("sectors") or []), set(sub.get("sectors") or [])
    if not s_hs and not s_sec:
        return True                                   # no filters → everything
    if ALL_SECTOR in n_sec and notice.get("impact") == "high":
        return True                                   # big procedural changes go to all
    if any(n.startswith(p) or p.startswith(n) for n in n_hs for p in s_hs):
        return True
    return bool(n_sec & s_sec)


def rank(notices: list[dict]) -> list[dict]:
    return sorted(notices, key=lambda n: (IMPACT_ORDER.get(n.get("impact"), 1),
                                          -(int((n.get("notice_date") or "0").replace("-", "")))))


def clients_for(n: dict, clients: list[dict]) -> list[str]:
    """Firm plan: names of the clients whose HS codes this notice touches (prefix match either way)."""
    n_hs = [str(x) for x in (n.get("hs_codes") or [])]
    return [c["name"] for c in clients or []
            if any(a.startswith(b) or b.startswith(a) for a in n_hs for b in (c.get("hs_prefixes") or []))]


def render_email(sub: dict, notices: list[dict], weekly: bool, clients: list[dict] | None = None) -> tuple[str, str]:
    e = html.escape
    items = []
    if clients:  # Firm: notices that touch a client first
        notices = sorted(notices, key=lambda n: not clients_for(n, clients))
    for n in notices:
        s = n.get("summary") or {}
        who = clients_for(n, clients) if clients else []
        who_html = (f'<div style="font-size:13px;margin:6px 0;background:#eef4ff;padding:4px 8px;border-radius:4px">'
                    f'<b>Affects your clients:</b> {e(", ".join(who))}</div>') if who else ""
        badge = {"high": "#c0392b", "medium": "#d68910", "low": "#7f8c8d"}.get(n.get("impact"), "#7f8c8d")
        deadline = f"<br><b>Deadline:</b> {e(s['deadline'])}{calendar_links(n)}" if s.get("deadline") else ""
        items.append(f"""
<tr><td style="padding:14px 0;border-bottom:1px solid #eee">
<span style="background:{badge};color:#fff;border-radius:3px;padding:1px 6px;font-size:11px">{e((n.get('impact') or '').upper())}</span>
<span style="color:#777;font-size:12px"> {e(n['authority'])} {e(n['kind'])} {e(n.get('number') or '')} · {e(n.get('notice_date') or '')}</span>
<div style="font-size:16px;font-weight:600;margin:6px 0">{e(s.get('headline') or n['title'])}</div>{who_html}
<div style="font-size:14px;color:#333">{e(s.get('summary') or '')}</div>
<div style="font-size:13px;color:#333;margin-top:6px"><b>Action:</b> {e(s.get('action_required') or '—')}{deadline}</div>
<div style="font-size:13px;color:#555;margin-top:4px">{e(s.get('headline_hi') or '')}</div>
<a href="{SITE_URL}/n/{n['id']}.html" style="font-size:13px">Details</a>
{' · <a href="' + e(n['url']) + '" style="font-size:13px">Official PDF</a>' if str(n.get('url') or '').startswith(('https://', 'http://')) else ''}
</td></tr>""")
    upsell = "" if not weekly else f"""
<p style="background:#f4f8ff;padding:12px;font-size:14px">This is the free weekly digest.
Paid plans send alerts matched to <i>your</i> HS codes the same day a notice touches them.
<a href="{SITE_URL}/#pricing">Upgrade</a></p>"""
    body = f"""<div style="font-family:Arial,sans-serif;max-width:620px;margin:auto">
<h2 style="margin-bottom:0">{e(SITE_NAME)}</h2>
<p style="color:#777;margin-top:4px">{'Weekly' if weekly else 'Daily'} EXIM regulatory alerts · {len(notices)} update(s)</p>
{upsell}<table width="100%" cellspacing="0">{''.join(items)}</table>
<p style="font-size:12px;color:#555;margin-top:20px">AI-generated summaries of official notices for information only.
Always check the official text before acting.</p>{email_footer(sub)}</div>"""
    top = (notices[0].get("summary") or {}).get("headline") or notices[0]["title"]
    subject = f"{'Weekly' if weekly else 'Today'}: {top[:70]}" + (f" (+{len(notices)-1} more)" if len(notices) > 1 else "")
    return subject, body


def contact_email() -> str:
    return (os.getenv("CONTACT_EMAIL") or "dharalabs.co@gmail.com").strip()


def email_footer(sub: dict) -> str:
    """Every email to a subscriber: why they get it, who we are, one-click unsubscribe and data deletion."""
    e = html.escape
    t = sub.get("unsubscribe_token", "")
    company = e((os.getenv("LEGAL_NAME") or "DharaLabs").strip())
    place = e((os.getenv("BUSINESS_ADDRESS") or os.getenv("JURISDICTION") or "Jaipur, Rajasthan, India").strip())
    return (f'<p style="font-size:12px;color:#555;border-top:1px solid #ddd;padding-top:10px">'
            f'You get this email because you subscribed to {e(SITE_NAME)} at {e(SITE_URL)}. '
            f'<a href="{SITE_URL}/unsubscribe.html?t={t}">Unsubscribe</a> · '
            f'<a href="{SITE_URL}/unsubscribe.html?t={t}&amp;delete=1">Delete my data</a> · '
            + (f'<a href="{SITE_URL}/clients.html?t={t}">Manage your clients</a> · ' if sub.get("plan") == "firm" else "")
            + f'<a href="{SITE_URL}/privacy.html">Privacy</a><br>{company}, {place} · {e(contact_email())}</p>')


def send_email(to: str, subject: str, body: str, unsub_url: str) -> None:
    r = httpx.post("https://api.resend.com/emails", timeout=30,
                   headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
                   json={"from": os.environ["MAIL_FROM"], "to": [to], "subject": subject, "html": body,
                         "reply_to": contact_email(),
                         "headers": {"List-Unsubscribe": f"<{unsub_url}>"}})
    r.raise_for_status()


def telegram_text(n: dict) -> str:
    e = html.escape
    s = n.get("summary") or {}
    lines = [f"<b>{e(s.get('headline') or n['title'])}</b>",
             f"{e(n['authority'])} {e(n['kind'])} {e(n.get('number') or '')} · {e(n.get('notice_date') or '')}",
             "", e(s.get("summary") or ""), "",
             f"<b>Action:</b> {e(s.get('action_required') or '—')}",
             f'<a href="{SITE_URL}/n/{n["id"]}.html">Details</a> · Free alerts for your HS codes: {SITE_URL}']
    return "\n".join(lines)


def post_telegram(text: str) -> None:
    r = httpx.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage",
                   timeout=30, json={"chat_id": os.environ["TELEGRAM_CHANNEL"], "text": text,
                                     "parse_mode": "HTML", "disable_web_page_preview": True})
    r.raise_for_status()


def plan_links(plan: str) -> dict:
    """Monthly / yearly payment links for a plan, from config/pricing.yaml."""
    import yaml
    from pathlib import Path
    f = Path(__file__).resolve().parents[1] / "config" / "pricing.yaml"
    cfg = yaml.safe_load(f.read_text(encoding="utf-8")) if f.exists() else {}
    for p in cfg.get("plans", []):
        if p.get("name", "").lower() == plan and p.get("monthly"):
            return {"monthly": p["monthly"], "yearly": p["yearly"]}
    return {}


def render_renewal(sub: dict, days_left: int) -> tuple[str, str]:
    e = html.escape
    plan = sub["plan"]
    links = plan_links(plan)
    when = "today" if days_left <= 0 else f"in {days_left} days"
    btns = "".join(
        f'<a href="{e(v["url"])}" style="display:inline-block;background:#0f2a4a;color:#fff;text-decoration:none;'
        f'padding:10px 16px;border-radius:8px;margin:4px 8px 4px 0">{k.title()} ₹{v["price"]:,}</a>'
        for k, v in links.items())
    body = f"""<div style="font-family:Arial,sans-serif;max-width:620px;margin:auto">
<h2 style="margin-bottom:0">{e(SITE_NAME)}</h2>
<p>Namaste{(' ' + e(sub['name'])) if sub.get('name') else ''},</p>
<p>Your {e(plan.title())} plan ends {when} ({e(str(sub.get('paid_until')))}). To keep getting same-day alerts for your
HS codes, renew with the same email address:</p>
<p>{btns}</p>
<p style="font-size:13px;color:#555">If you don't renew, you'll move to the free weekly digest. Nothing else changes.
Questions? Just reply to this email.</p>{email_footer(sub)}</div>"""
    return f"Your {SITE_NAME} {plan.title()} plan ends {when}", body


TRIAL_DAYS = 14


def render_welcome(sub: dict, notices: list[dict]) -> tuple[str, str]:
    """First email after sign-up: confirms the trial and shows the recent notices that match the subscriber's codes."""
    e = html.escape
    trial = bool(sub.get("trial"))
    codes = ", ".join(sub.get("hs_prefixes") or []) or "all DGFT changes"
    rows = "".join(
        f'<li style="margin:8px 0"><b>{e((n.get("summary") or {}).get("headline") or n["title"])}</b> '
        f'<span style="color:#555">({e(n.get("notice_date") or "")})</span><br>'
        f'{e((n.get("summary") or {}).get("action_required") or "")} '
        f'<a href="{SITE_URL}/n/{n["id"]}.html">Details</a></li>' for n in notices[:10])
    lead = (f"Here are the DGFT changes from the last 90 days that touch your codes ({e(codes)}):"
            if sub.get("hs_prefixes") else "Here are the most important DGFT changes from the last 90 days:")
    found = (f"<p>{lead}</p><ol>{rows}</ol>"
             if rows else f"<p>No DGFT notice in the last 90 days touched your codes ({e(codes)}). That is normal: DGFT "
                          "publishes irregularly. We will email you the same day one does.</p>")
    intro = (f"<p>Your <b>{TRIAL_DAYS}-day free trial</b> has started, until {e(str(sub.get('paid_until') or ''))}. "
             "During the trial you get an email the same day a DGFT notice touches your HS codes. "
             "No card, nothing is charged. After the trial you move to the free weekly digest unless you choose a paid plan.</p>"
             if trial else
             (f"<p>Your <b>{e(str(sub.get('plan')).title())} plan</b> is active until {e(str(sub.get('paid_until') or ''))}. "
              "You get an email the same day a DGFT notice touches your HS codes.</p>"
              + (f'<p><b>Firm plan:</b> add your clients and their products here (private link): '
                 f'<a href="{SITE_URL}/clients.html?t={sub.get("unsubscribe_token", "")}">Manage your clients</a></p>'
                 if sub.get("plan") == "firm" else "")
              if sub.get("plan") in ("pro", "firm") and sub.get("paid_until")
              else "<p>You are subscribed to the free weekly digest of important DGFT changes.</p>"))
    body = f"""<div style="font-family:Arial,sans-serif;max-width:620px;margin:auto">
<h2 style="margin-bottom:0">{e(SITE_NAME)}</h2><p>Namaste,</p>{intro}{found}
<p style="font-size:13px;color:#555">Want different products or codes? Just reply to this email.</p>{email_footer(sub)}</div>"""
    subj = (f"Your {TRIAL_DAYS}-day free trial has started" if trial
            else f"Your {str(sub.get('plan')).title()} plan is active" if sub.get("plan") in ("pro", "firm")
            else f"Welcome to {SITE_NAME}")
    return f"{subj}: {len(notices[:10])} recent notice(s) for your codes", body


def render_trial_end(sub: dict, days_left: int) -> tuple[str, str]:
    e = html.escape
    links = plan_links("pro")
    when = "today" if days_left <= 0 else f"in {days_left} days"
    btns = "".join(
        f'<a href="{e(v["url"])}" style="display:inline-block;background:#0f2a4a;color:#fff;text-decoration:none;'
        f'padding:10px 16px;border-radius:8px;margin:4px 8px 4px 0">Pro {k} Rs {v["price"]:,}</a>'
        for k, v in links.items())
    body = f"""<div style="font-family:Arial,sans-serif;max-width:620px;margin:auto">
<h2 style="margin-bottom:0">{e(SITE_NAME)}</h2><p>Namaste,</p>
<p>Your free trial ends {when}. Nothing will be charged. After it ends you move to the free weekly digest automatically.</p>
<p>If you want to keep same-day alerts for your HS codes, choose a plan with the same email address:</p><p>{btns}</p>
<p style="font-size:13px;color:#555">Advising many exporter clients? Reply and ask about the Firm plan.</p>{email_footer(sub)}</div>"""
    return f"Your {SITE_NAME} free trial ends {when}", body
