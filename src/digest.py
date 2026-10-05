"""Agent 3 — Publisher: matches alerts to subscribers and sends email / Telegram."""
from __future__ import annotations

import html
import os

import httpx

SITE_NAME = os.getenv("SITE_NAME") or "Trade Alerts India"
SITE_URL = (os.getenv("SITE_URL") or "https://example.github.io/trade-alerts").strip().rstrip("/")
ALL_SECTOR = "Services & Procedures (all exporters)"
IMPACT_ORDER = {"high": 0, "medium": 1, "low": 2}


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


def render_email(sub: dict, notices: list[dict], weekly: bool) -> tuple[str, str]:
    e = html.escape
    items = []
    for n in notices:
        s = n.get("summary") or {}
        badge = {"high": "#c0392b", "medium": "#d68910", "low": "#7f8c8d"}.get(n.get("impact"), "#7f8c8d")
        deadline = f"<br><b>Deadline:</b> {e(s['deadline'])}" if s.get("deadline") else ""
        items.append(f"""
<tr><td style="padding:14px 0;border-bottom:1px solid #eee">
<span style="background:{badge};color:#fff;border-radius:3px;padding:1px 6px;font-size:11px">{e((n.get('impact') or '').upper())}</span>
<span style="color:#777;font-size:12px"> {e(n['authority'])} {e(n['kind'])} {e(n.get('number') or '')} · {e(n.get('notice_date') or '')}</span>
<div style="font-size:16px;font-weight:600;margin:6px 0">{e(s.get('headline') or n['title'])}</div>
<div style="font-size:14px;color:#333">{e(s.get('summary') or '')}</div>
<div style="font-size:13px;color:#333;margin-top:6px"><b>Action:</b> {e(s.get('action_required') or '—')}{deadline}</div>
<div style="font-size:13px;color:#555;margin-top:4px">{e(s.get('headline_hi') or '')}</div>
<a href="{SITE_URL}/n/{n['id']}.html" style="font-size:13px">Details</a>
{' · <a href="' + e(n['url']) + '" style="font-size:13px">Official PDF</a>' if n.get('url') else ''}
</td></tr>""")
    upsell = "" if not weekly else f"""
<p style="background:#f4f8ff;padding:12px;font-size:14px">This is the free weekly digest.
<b>Pro</b> sends alerts matched to <i>your</i> HS codes every morning.
<a href="{SITE_URL}/#pricing">Upgrade</a></p>"""
    unsub = f"{SITE_URL}/unsubscribe.html?t={sub['unsubscribe_token']}"
    body = f"""<div style="font-family:Arial,sans-serif;max-width:620px;margin:auto">
<h2 style="margin-bottom:0">{e(SITE_NAME)}</h2>
<p style="color:#777;margin-top:4px">{'Weekly' if weekly else 'Daily'} EXIM regulatory alerts · {len(notices)} update(s)</p>
{upsell}<table width="100%" cellspacing="0">{''.join(items)}</table>
<p style="font-size:11px;color:#999;margin-top:20px">AI-generated summaries of official notices for information only —
always check the official text before acting. <a href="{unsub}">Unsubscribe</a></p></div>"""
    top = (notices[0].get("summary") or {}).get("headline") or notices[0]["title"]
    subject = f"{'Weekly' if weekly else 'Today'}: {top[:70]}" + (f" (+{len(notices)-1} more)" if len(notices) > 1 else "")
    return subject, body


def send_email(to: str, subject: str, body: str, unsub_url: str) -> None:
    r = httpx.post("https://api.resend.com/emails", timeout=30,
                   headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
                   json={"from": os.environ["MAIL_FROM"], "to": [to], "subject": subject, "html": body,
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
