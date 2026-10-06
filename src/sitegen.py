"""Agent 4 — SEO site builder: one public page per notice + landing/signup page.

Every notice page is indexable by Google, so the archive itself becomes the
free acquisition channel (people search for "DGFT notification 23/2025-26").
"""
from __future__ import annotations

import html
import json
import os
from pathlib import Path

import legal
from digest import SITE_NAME, SITE_URL, calendar_links, ics_text, rank

e = html.escape
CSS = """*{box-sizing:border-box}body{margin:0;font-family:system-ui,Arial,sans-serif;color:#1d2433;background:#fafbfc;line-height:1.55}
.w{max-width:820px;margin:auto;padding:0 16px}header{background:#0f2a4a;color:#fff;padding:28px 0}header a{color:#fff;text-decoration:none}
h1{margin:.2em 0;font-size:1.9em}.card{background:#fff;border:1px solid #e3e7ee;border-radius:8px;padding:16px;margin:14px 0}
.b{display:inline-block;font-size:11px;color:#fff;border-radius:3px;padding:1px 6px}.high{background:#c0392b}.medium{background:#d68910}.low{background:#7f8c8d}
.m{color:#6b7280;font-size:13px}input,select,button{font:inherit;padding:10px;border:1px solid #cbd2dc;border-radius:6px;width:100%;margin:5px 0}
button{background:#1f6feb;color:#fff;border:0;cursor:pointer;font-weight:600}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.price{font-size:1.6em;font-weight:700}a{color:#1f6feb}footer{padding:30px 0;color:#6b7280;font-size:13px}"""


def page(title: str, body: str, desc: str = "") -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}"><style>{CSS}</style></head><body>
<header><div class="w"><a href="{SITE_URL}/"><b>{e(SITE_NAME)}</b></a>
<div class="m" style="color:#b9c6d8">Plain-English DGFT alerts, matched to your HS codes</div></div></header>
<main class="w">{body}</main><footer class="w">Summaries are AI-generated from official notices for information only.
Always verify with the official text. Not legal advice.<br><br>{footer_links()}</footer></body></html>"""


def footer_links() -> str:
    tg = os.getenv("TELEGRAM_CHANNEL", "").strip().lstrip("@")
    links = [f'<a href="{SITE_URL}/{f}">{t}</a>' for f, t in
             (("privacy.html", "Privacy"), ("terms.html", "Terms"), ("refund.html", "Refunds"), ("contact.html", "Contact"))]
    if tg:
        links.append(f'<a href="https://t.me/{e(tg)}">Telegram</a>')
    company = e(os.getenv("LEGAL_NAME") or "DharaLabs")
    return " · ".join(links) + f"<br>© {company}"


def notice_card(n: dict, link: bool = True) -> str:
    s = n.get("summary") or {}
    head = e(s.get("headline") or n["title"])
    head = f'<a href="{SITE_URL}/n/{n["id"]}.html">{head}</a>' if link else head
    return f"""<div class="card"><span class="b {e(n.get('impact') or 'low')}">{e((n.get('impact') or '').upper())}</span>
<span class="m"> {e(n['authority'])} {e(n['kind'])} {e(n.get('number') or '')} · {e(n.get('notice_date') or '')}</span>
<h3 style="margin:.4em 0">{head}</h3><div>{e(s.get('summary') or '')}</div>
<div class="m" style="margin-top:6px"><b>Action:</b> {e(s.get('action_required') or '—')}</div></div>"""


def signup_form(sectors: list[str]) -> str:
    opts = "".join(f'<option>{e(s)}</option>' for s in sectors)
    cfg = json.dumps({"url": os.getenv("SUPABASE_URL", ""), "key": os.getenv("SUPABASE_ANON_KEY", "")})
    return f"""<div class="card" id="signup"><h2 style="margin-top:0">Get free weekly alerts</h2>
<form id="f"><input name="email" type="email" required placeholder="Work email">
<input name="company" placeholder="Company (optional)">
<input name="hs" placeholder="Your HS codes, comma separated — e.g. 3923, 7113 (optional)">
<select name="sector"><option value="">Your main sector (optional)</option>{opts}</select>
<label class="m"><input type="checkbox" required style="width:auto"> I agree to receive alert emails and can unsubscribe anytime.</label>
<button>Subscribe free</button><div id="msg" class="m"></div></form></div>
<script>const C={cfg};document.getElementById('f').onsubmit=async ev=>{{ev.preventDefault();
const d=new FormData(ev.target),m=document.getElementById('msg');m.textContent='Saving…';
const body={{email:d.get('email').trim().toLowerCase(),company:d.get('company')||null,
hs_prefixes:(d.get('hs')||'').split(',').map(x=>x.replace(/\\D/g,'')).filter(x=>x.length>=2&&x.length<=8),
sectors:d.get('sector')?[d.get('sector')]:[]}};
try{{const r=await fetch(C.url+'/rest/v1/subscribers',{{method:'POST',headers:{{apikey:C.key,Authorization:'Bearer '+C.key,
'Content-Type':'application/json',Prefer:'return=minimal'}},body:JSON.stringify(body)}});
m.textContent=r.ok?'Done! Your first weekly digest arrives within 7 days.':(r.status===409?'You are already subscribed.':'Something went wrong — try again.');
if(r.ok)ev.target.reset();}}catch(_){{m.textContent='Network error — try again.'}}}};</script>"""


def _inr(n: int) -> str:
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:]); head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts) + "," + tail


def _cfg_pricing() -> dict:
    import yaml
    f = Path(__file__).resolve().parents[1] / "config" / "pricing.yaml"
    return yaml.safe_load(f.read_text(encoding="utf-8")) if f.exists() else {"plans": []}


SOON = ('<span style="font-size:11px;background:#eef2f7;color:#6b7280;border-radius:3px;'
        'padding:1px 5px;margin-left:4px;white-space:nowrap">Coming soon</span>')


def pricing() -> str:
    cfg = _cfg_pricing()
    btn = ('display:inline-block;padding:8px 12px;margin:6px 6px 0 0;border-radius:6px;'
           'text-decoration:none;font-weight:600;font-size:14px')
    cards = []
    for p in cfg.get("plans", []):
        feats = "".join(
            f'<li style="margin:5px 0;{"color:#6b7280" if f.get("soon") else ""}">'
            f'{"○" if f.get("soon") else "✓"} {e(f["text"])}{SOON if f.get("soon") else ""}</li>'
            for f in p.get("features", []))
        if p.get("monthly"):
            m, y = p["monthly"], p["yearly"]
            save = m["price"] * 12 - y["price"]
            price = f'₹{_inr(m["price"])}<span class="m">/month</span>'
            ctas = (f'<a href="{e(m["url"])}" style="{btn};background:#1f6feb;color:#fff">Monthly ₹{_inr(m["price"])}</a>'
                    f'<a href="{e(y["url"])}" style="{btn};background:#0f2a4a;color:#fff">Yearly ₹{_inr(y["price"])}</a>'
                    f'<div class="m" style="margin-top:6px">Yearly saves ₹{_inr(save)}. Pay with the email you subscribed with.</div>')
        else:
            price = "₹0"
            ctas = f'<a href="#signup" style="{btn};background:#eef2f7;color:#1d2433">Subscribe free</a>'
        cards.append(f"""<div class="card" style="display:flex;flex-direction:column"><b style="font-size:1.1em">{e(p['name'])}</b>
<div class="m">{e(p.get('for', ''))}</div><div class="price" style="margin:6px 0">{price}</div>
<ul style="list-style:none;padding:0;margin:4px 0 10px;font-size:14px;flex:1">{feats}</ul><div>{ctas}</div></div>""")
    perks = "".join(f"<li style='margin:4px 0'>{e(x)}</li>" for x in cfg.get("perks", []))
    cmp = cfg.get("compare") or {}
    th = "".join(f"<th style='text-align:left;padding:8px;border-bottom:2px solid #e3e7ee'>{e(h)}</th>" for h in cmp.get("header", []))
    trs = "".join("<tr>" + "".join(
        f"<td style='padding:8px;border-bottom:1px solid #eef0f4;{'font-weight:600' if k == 0 else ''}'>{e(c)}</td>"
        for k, c in enumerate(r)) + "</tr>" for r in cmp.get("rows", []))
    faq = "".join(f"""<details style="background:#fff;border:1px solid #e3e7ee;border-radius:8px;padding:12px 14px;margin:8px 0">
<summary style="cursor:pointer;font-weight:600">{e(x['q'])}</summary><p style="margin:8px 0 0">{e(x['a'])}</p></details>"""
                  for x in cfg.get("faq", []))
    return f"""<h2 id="pricing">Plans</h2><p>{e(cfg.get('intro', ''))}</p>
<div class="grid">{''.join(cards)}</div>
<div class="card"><b>For paid plans</b><ul style="margin:6px 0 0;padding-left:18px;font-size:14px">{perks}</ul></div>
<h3>Compare plans</h3><div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:14px;background:#fff">
<thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>
<h3 id="faq">Questions</h3>{faq}
<p class="m">{e(cfg.get('disclaimer', ''))}</p>"""


def build(notices: list[dict], sectors: list[str], out: str = "public") -> int:
    root = Path(out)
    (root / "n").mkdir(parents=True, exist_ok=True)
    ranked = rank([n for n in notices if n.get("summary")])
    for n in ranked:
        s = n["summary"]
        body = notice_card(n, link=False) + f"""<div class="card"><b>Who is affected:</b> {e(s.get('who_is_affected') or '—')}<br>
<b>Deadline:</b> {e(s.get('deadline') or 'Not stated')}{calendar_links(n) if s.get('deadline') else ''}<br><b>HS codes:</b> {e(', '.join(n.get('hs_codes') or []) or '—')}<br>
<b>हिंदी:</b> {e(s.get('headline_hi') or '')}<br><b>Original title:</b> {e(n['title'])}<br>
{f'<a href="{e(n["url"])}">Official document</a>' if n.get('url') else ''}</div>""" + signup_form(sectors)
        title = f"{n['authority']} {n['kind']} {n.get('number') or ''}: {s.get('headline') or n['title']}"
        if s.get("deadline"):
            (root / "n" / f"{n['id']}.ics").write_text(ics_text(n), encoding="utf-8")
        (root / "n" / f"{n['id']}.html").write_text(page(title[:110], body, s.get("summary", "")[:155]), encoding="utf-8")
    latest = "".join(notice_card(n) for n in sorted(ranked, key=lambda n: n.get("notice_date") or "", reverse=True)[:40])
    home = f"""<h1 style="font-size:1.5em;margin-top:24px">Never miss a DGFT change that affects your products</h1>
<p>Every morning we read new DGFT notifications, public notices and trade notices, explain them in plain English (with a Hindi line) and tell you what to do and by when — filtered to your HS codes. Customs and BIS coverage is coming soon.</p>
{signup_form(sectors)}{pricing()}<h2>Latest updates</h2>{latest}"""
    (root / "index.html").write_text(page(f"{SITE_NAME} — DGFT alerts for exporters", home,
                                          "Free plain-English alerts on DGFT notifications, public notices and customs changes for Indian exporters."), encoding="utf-8")
    cfg = json.dumps({"url": os.getenv("SUPABASE_URL", ""), "key": os.getenv("SUPABASE_ANON_KEY", "")})
    (root / "unsubscribe.html").write_text(page("Unsubscribe", f"""<div class="card" id="u">Unsubscribing…</div>
<script>const C={cfg};const t=new URLSearchParams(location.search).get('t');
fetch(C.url+'/rest/v1/rpc/unsubscribe',{{method:'POST',headers:{{apikey:C.key,Authorization:'Bearer '+C.key,'Content-Type':'application/json'}},
body:JSON.stringify({{token:t}})}}).then(r=>document.getElementById('u').textContent=r.ok?'You have been unsubscribed.':'Link invalid or expired.');</script>"""), encoding="utf-8")
    urls = [f"{SITE_URL}/"] + [f"{SITE_URL}/{f}" for f in legal.pages()] + [f"{SITE_URL}/n/{n['id']}.html" for n in ranked]
    (root / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                      + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>", encoding="utf-8")
    for fname, (title, body) in legal.pages().items():
        (root / fname).write_text(page(f"{title} — {SITE_NAME}", f'<div class="card">{body}</div>'), encoding="utf-8")
    (root / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    return len(ranked)
