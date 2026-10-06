"""Agent 4 — SEO site builder: one public page per notice + landing/signup page.

Every notice page is indexable by Google, so the archive itself becomes the
free acquisition channel (people search for "DGFT notification 23/2025-26").

UI: Sagarlekh brand kit v1 (Deep Ink / Sea Teal / Marigold, IBM Plex + Tiro Devanagari).
"""
from __future__ import annotations

import html
import json
import os
from pathlib import Path
from urllib.parse import quote

import legal
from digest import SITE_NAME, SITE_URL, rank

e = html.escape

# ---------- brand assets (inline, so no extra files to deploy) ----------
_MARK = ('<path d="M12 6h28l14 14v34a4 4 0 0 1-4 4H12a4 4 0 0 1-4-4V10a4 4 0 0 1 4-4z" fill="{doc}"/>'
         '<path d="M40 6v10a4 4 0 0 0 4 4h10z" fill="{fold}"/>'
         '<path d="M15 31c2.5-4 5-4 7.5 0s5 4 7.5 0 5-4 7.5 0 5 4 7.5 0" stroke="#E9A23B" stroke-width="{sw}" stroke-linecap="round"/>'
         '<path d="M15 41h30M15 50h19" stroke="{lines}" stroke-width="{sw}" stroke-linecap="round"/>')


def logo_svg(size: int = 40, dark: bool = False) -> str:
    c = dict(doc="#F5F7F6", fold="#8CC7C0", lines="#0B2536") if dark else dict(doc="#0B2536", fold="#0F6E6E", lines="#F5F7F6")
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 64 64" fill="none" aria-hidden="true">'
            + _MARK.format(sw="4", **c) + "</svg>")


_FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">'
            '<rect width="64" height="64" rx="14" fill="#0B2536"/><g transform="translate(6 6) scale(.82)">'
            + _MARK.format(sw="5", doc="#F5F7F6", fold="#8CC7C0", lines="#0B2536") + "</g></svg>")
FAVICON = "data:image/svg+xml," + quote(_FAVICON)

WAVE = ('<svg class="wave" viewBox="0 0 600 40" preserveAspectRatio="none" fill="none" aria-hidden="true">'
        '<path d="M0 14' + "".join(" c12.5-10 25-10 37.5 0 s25 10 37.5 0" for _ in range(8)) + '" stroke="#E9A23B" stroke-width="2.5"/>'
        '<path d="M0 30h600" stroke="#0B2536" stroke-width="1.5"/></svg>')

ICON = {
    "doc": '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/><path d="M10 13h6M10 17h4"/>',
    "plain": '<path d="M4 6h16M4 12h10M4 18h13"/>',
    "send": '<path d="M21 4L3 11l6 2.5L19 6l-8 9v5l3.5-4 4.5 3z"/>',
    "hash": '<path d="M5 9h14M5 15h14M10 4L8 20M16 4l-2 16"/>',
    "ext": '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
}


def icon(name: str, size: int = 22, color: str = "#0F6E6E") -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON[name]}</svg>')


def _brand_parts() -> tuple[str, str]:
    name = (SITE_NAME or "Sagarlekh").strip()
    if " by " in name:
        main, sub = name.split(" by ", 1)
        return main.strip(), "by " + sub.strip()
    return name, "by " + (os.getenv("LEGAL_NAME") or "DharaLabs").strip()


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500'
         '&family=IBM+Plex+Sans:wght@400;500;600&family=Tiro+Devanagari+Hindi&display=swap">')

CSS = """:root{--ink:#0B2536;--teal:#0F6E6E;--gold:#E9A23B;--shallow:#CFE6E3;--paper:#F5F7F6;--line:#DCE3E1;--slate:#4A5D66;
--sans:'IBM Plex Sans','Helvetica Neue',Arial,sans-serif;--mono:'IBM Plex Mono',ui-monospace,Consolas,monospace;--deva:'Tiro Devanagari Hindi','Noto Sans Devanagari',serif}
*{box-sizing:border-box}html{scroll-padding-top:84px}body{margin:0;font-family:var(--sans);color:var(--ink);background:var(--paper);line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:var(--teal)}a:hover{color:var(--ink)}
.w{max-width:1120px;margin:auto;padding:0 20px}
.nav{position:sticky;top:0;z-index:10;background:rgba(245,247,246,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.nav .w{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;padding-top:12px;padding-bottom:12px}
.brand{display:flex;align-items:center;gap:11px;text-decoration:none;color:var(--ink)}
.brand b{display:block;font-size:22px;font-weight:600;letter-spacing:-.03em;line-height:1}
.brand small{display:block;font-family:var(--mono);font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:var(--teal);margin-top:4px}
.nav nav{display:flex;flex-wrap:wrap;align-items:center;gap:20px;font-weight:500;font-size:15px}
.nav nav a{color:var(--ink);text-decoration:none}.nav nav a:hover{color:var(--teal)}
.btn{display:inline-block;background:var(--ink);color:#fff!important;text-decoration:none;font-weight:600;padding:11px 18px;border-radius:10px;border:0;cursor:pointer;font-family:inherit;font-size:15px}
.btn:hover{background:var(--teal)}.btn.ghost{background:transparent;color:var(--ink)!important;border:1.5px solid var(--ink)}.btn.ghost:hover{background:var(--shallow)}
.eyebrow{display:flex;align-items:center;gap:10px;font-family:var(--mono);font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--teal)}
.eyebrow i{width:8px;height:8px;border-radius:50%;background:var(--gold)}
.hero{display:flex;flex-wrap:wrap;gap:48px;align-items:flex-start;padding:56px 0 36px}
.hero>div{flex:1 1 440px;min-width:0}
.hero h1{margin:16px 0;font-size:clamp(36px,5.4vw,58px);line-height:1.04;font-weight:600;letter-spacing:-.035em}
.hero h1 span{color:var(--teal)}.hero p{font-size:19px;color:#33474F;max-width:540px;margin:0 0 18px}
.deva{font-family:var(--deva);color:var(--teal)}
.wave{display:block;width:100%;height:40px;margin:8px 0}
.trust{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px;padding:18px 0 8px}
.trust>div{display:flex;gap:12px;align-items:flex-start}.trust svg{flex-shrink:0;margin-top:2px}.trust b{display:block}.trust span{font-size:14px;color:var(--slate)}
h2{font-size:30px;font-weight:600;letter-spacing:-.02em;margin:48px 0 8px}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:22px;margin:14px 0}
.notice h3{margin:10px 0 6px;font-size:20px;font-weight:600;letter-spacing:-.01em;line-height:1.3}.notice h3 a{color:var(--ink);text-decoration:none}.notice h3 a:hover{color:var(--teal)}
.top{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px}
.chips{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.src{font-family:var(--mono);font-size:12px;font-weight:500;background:var(--ink);color:#fff;padding:5px 10px;border-radius:7px}
.b{font-size:12.5px;font-weight:600;padding:4px 11px;border-radius:999px}.high{background:#FBE3D2;color:#8A3B12}.medium{background:#FDEFD3;color:#7A4A06}.low{background:#ECEFEE;color:var(--slate)}
.m{color:var(--slate);font-size:13px}.num{font-family:var(--mono);font-size:12px;color:var(--slate)}
.rows{display:grid;grid-template-columns:130px minmax(0,1fr);gap:8px 14px;margin-top:12px;font-size:15px}
.rows>span:nth-child(odd){font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--slate);padding-top:3px}
.foot{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px;border-top:1px dashed var(--line);margin-top:14px;padding-top:12px}
.hs{font-family:var(--mono);font-size:12px;background:var(--shallow);padding:4px 9px;border-radius:6px}
#signup{box-shadow:0 18px 40px -26px rgba(11,37,54,.4)}#signup h2{margin:0 0 4px;font-size:24px}
label.l{display:block;font-size:14px;font-weight:600;margin-top:10px}
input,select{font:inherit;font-size:15px;padding:12px 14px;border:1.5px solid #B9C6C3;border-radius:10px;width:100%;margin:5px 0;background:#fff;color:var(--ink)}
input:focus,select:focus{outline:2px solid var(--teal);outline-offset:1px;border-color:var(--teal)}
input[type=checkbox]{width:auto;margin:0 8px 0 0;accent-color:var(--teal)}.agree{display:flex;align-items:flex-start;margin:10px 0}
form button{width:100%;margin-top:6px;padding:14px;font-size:16px}#msg{margin-top:8px;min-height:1.2em}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}.grid .card{margin:0;display:flex;flex-direction:column;gap:6px}
.plan{font-family:var(--mono);font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--teal)}
.price{font-size:38px;font-weight:600;letter-spacing:-.03em;line-height:1.1}.price .m{font-size:15px;letter-spacing:0}
.plans .btn{font-size:14px;padding:9px 14px;margin:6px 6px 0 0}
.page-h{padding:36px 0 4px}.page-h h1{font-size:clamp(28px,4vw,40px);letter-spacing:-.03em;line-height:1.15;margin:10px 0}
footer{background:var(--ink);color:#C6D3D7;margin-top:64px;padding:40px 0;font-size:14px}footer a{color:#fff}
footer .w{display:flex;flex-wrap:wrap;gap:28px;justify-content:space-between}footer .brand{color:#fff}footer .brand small{color:#8CC7C0}
footer p{max-width:520px;margin:12px 0 0}
@media(max-width:640px){.nav nav{gap:14px;font-size:14px}.nav .btn{padding:9px 14px}.rows{grid-template-columns:1fr}.hero{padding-top:32px}}
@media(max-width:560px){.nav nav a:not(.btn){display:none}.nav .w{flex-wrap:nowrap}}"""


def brand_link(dark: bool = False) -> str:
    main, sub = _brand_parts()
    return f'<a class="brand" href="{SITE_URL}/">{logo_svg(40, dark)}<span><b>{e(main)}</b><small>{e(sub)}</small></span></a>'


def _tg() -> str:
    return os.getenv("TELEGRAM_CHANNEL", "").strip().lstrip("@")


def page(title: str, body: str, desc: str = "") -> str:
    tg = _tg()
    tg_link = f'<a href="https://t.me/{e(tg)}">Telegram</a>' if tg else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}"><meta name="theme-color" content="#0B2536">
<link rel="icon" href="{FAVICON}">{FONTS}<style>{CSS}</style></head><body>
<header class="nav"><div class="w">{brand_link()}
<nav><a href="{SITE_URL}/#latest">Latest notices</a><a href="{SITE_URL}/#pricing">Plans</a>{tg_link}
<a class="btn" href="{SITE_URL}/#signup">Subscribe free</a></nav></div></header>
<main class="w">{body}</main>
<footer><div class="w"><div>{brand_link(dark=True)}
<p>Summaries are AI-generated from official notices for information only. Always verify with the official text. Not legal advice.</p></div>
<div>{footer_links()}</div></div></footer></body></html>"""


def footer_links() -> str:
    tg = _tg()
    links = [f'<a href="{SITE_URL}/{f}">{t}</a>' for f, t in
             (("privacy.html", "Privacy"), ("terms.html", "Terms"), ("refund.html", "Refunds"), ("contact.html", "Contact"))]
    if tg:
        links.append(f'<a href="https://t.me/{e(tg)}">Telegram</a>')
    company = e(os.getenv("LEGAL_NAME") or "DharaLabs")
    return " · ".join(links) + f"<br><br>© {company}"


IMPACT_LABEL = {"high": "High impact", "medium": "Medium impact", "low": "Low impact"}


def notice_card(n: dict, link: bool = True) -> str:
    s = n.get("summary") or {}
    imp = n.get("impact") or "low"
    head = e(s.get("headline") or n["title"])
    url = f'{SITE_URL}/n/{n["id"]}.html'
    head = f'<a href="{url}">{head}</a>' if link else head
    meta = " · ".join(x for x in (e(n.get("number") or ""), e(n.get("notice_date") or "")) if x)
    action = e(s.get("action_required") or "—")
    more = f'<a href="{url}"><b>Read summary →</b></a>' if link else ""
    return f"""<article class="card notice"><div class="top"><div class="chips">
<span class="src">{e(n['authority'])} · {e(n['kind'])}</span><span class="b {e(imp)}">{IMPACT_LABEL.get(imp, e(imp.title()))}</span></div>
<span class="num">{meta}</span></div>
<h3>{head}</h3><div>{e(s.get('summary') or '')}</div>
<div class="rows"><span>Action</span><span>{action}</span></div>
{f'<div class="foot"><span></span>{more}</div>' if more else ''}</article>"""


def signup_form(sectors: list[str]) -> str:
    opts = "".join(f'<option>{e(s)}</option>' for s in sectors)
    cfg = json.dumps({"url": os.getenv("SUPABASE_URL", ""), "key": os.getenv("SUPABASE_ANON_KEY", "")})
    return f"""<div class="card" id="signup"><h2>Get free weekly alerts</h2>
<div class="m">Plain-English summaries in your inbox. Unsubscribe anytime.</div>
<form id="f"><label class="l" for="f-email">Work email</label><input id="f-email" name="email" type="email" required placeholder="you@yourfirm.in">
<label class="l" for="f-co">Company <span class="m">(optional)</span></label><input id="f-co" name="company" placeholder="Company name">
<label class="l" for="f-hs">Your HS codes <span class="m">(optional)</span></label><input id="f-hs" name="hs" placeholder="e.g. 3923, 7113">
<label class="l" for="f-sec">Main sector <span class="m">(optional)</span></label><select id="f-sec" name="sector"><option value="">Choose a sector</option>{opts}</select>
<label class="m agree"><input type="checkbox" required> I agree to receive alert emails and can unsubscribe anytime.</label>
<button class="btn">Subscribe free</button><div id="msg" class="m" aria-live="polite"></div></form></div>
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


def pricing() -> str:
    import yaml
    f = Path(__file__).resolve().parents[1] / "config" / "pricing.yaml"
    plans = yaml.safe_load(f.read_text(encoding="utf-8"))["plans"] if f.exists() else []
    cards = ['<div class="card"><span class="plan">Free</span><div class="price">₹0</div>'
             '<div class="m">Weekly digest of the most important changes.</div>'
             '<div><a class="btn ghost" href="#signup">Subscribe free</a></div></div>']
    for p in plans:
        m, y = p["monthly"], p["yearly"]
        save = m["price"] * 12 - y["price"]
        cards.append(f"""<div class="card"><span class="plan">{e(p['name'])}</span><div class="price">₹{_inr(m['price'])}<span class="m">/mo</span></div>
<div class="m">{e(p['blurb'])}</div>
<div><a class="btn" href="{e(m['url'])}">Monthly ₹{_inr(m['price'])}</a><a class="btn ghost" href="{e(y['url'])}">Yearly ₹{_inr(y['price'])}</a></div>
<div class="m">Yearly saves ₹{_inr(save)}. Use the same email you subscribed with.</div></div>""")
    return '<h2 id="pricing">Plans</h2><div class="grid plans">' + "".join(cards) + "</div>"


def trust() -> str:
    items = (("doc", "From official sources", "DGFT, Customs &amp; BIS notices, read every morning"),
             ("plain", "Written plainly", "What changed, who is affected, what to do"),
             ("hash", "Matched to your HS codes", "Only the changes that touch your products"),
             ("send", "Email or Telegram", "Wherever you read first"))
    return '<div class="trust">' + "".join(
        f'<div>{icon(i, 26)}<div><b>{t}</b><span>{d}</span></div></div>' for i, t, d in items) + "</div>"


def build(notices: list[dict], sectors: list[str], out: str = "public") -> int:
    root = Path(out)
    (root / "n").mkdir(parents=True, exist_ok=True)
    ranked = rank([n for n in notices if n.get("summary")])
    for n in ranked:
        s = n["summary"]
        hs = ", ".join(n.get("hs_codes") or [])
        official = (f'<a class="btn" href="{e(n["url"])}" rel="noopener">{icon("ext", 16, "#fff")} Read official document</a>'
                    if n.get("url") else "")
        detail = f"""<div class="card"><div class="rows">
<span>Who is affected</span><span>{e(s.get('who_is_affected') or '—')}</span>
<span>Deadline</span><span>{e(s.get('deadline') or 'Not stated')}</span>
<span>HS codes</span><span>{f'<span class="hs"># {e(hs)}</span>' if hs else '—'}</span>
<span>हिंदी</span><span class="deva" style="font-size:18px">{e(s.get('headline_hi') or '')}</span>
<span>Original title</span><span>{e(n['title'])}</span></div>
{f'<div class="foot"><span class="m">Always verify with the official text.</span>{official}</div>' if official else ''}</div>"""
        body = (f'<div class="page-h"><a href="{SITE_URL}/#latest" class="m">← All notices</a></div>'
                + notice_card(n, link=False) + detail + signup_form(sectors))
        title = f"{n['authority']} {n['kind']} {n.get('number') or ''}: {s.get('headline') or n['title']}"
        (root / "n" / f"{n['id']}.html").write_text(page(title[:110], body, s.get("summary", "")[:155]), encoding="utf-8")
    latest = "".join(notice_card(n) for n in sorted(ranked, key=lambda n: n.get("notice_date") or "", reverse=True)[:40])
    tg = _tg()
    tg_btn = f' <a class="btn ghost" href="https://t.me/{e(tg)}">Join on Telegram</a>' if tg else ""
    home = f"""<section class="hero"><div>
<div class="eyebrow"><i></i>DGFT · Customs · BIS alerts</div>
<h1>India’s trade rules, written plainly. <span>Every morning.</span></h1>
<p>Our system reads new government notices every day, explains them in plain English (with a Hindi line)
and tells you what to do — filtered to your HS codes.</p>
<div><a class="btn" href="#latest">See latest notices</a>{tg_btn}</div>
<p class="deva" style="margin-top:28px;font-size:20px">सागरलेख — सरल भाषा में व्यापार नियम</p></div>
<div>{signup_form(sectors)}</div></section>
{WAVE}{trust()}{pricing()}<h2 id="latest">Latest updates</h2>{latest}"""
    (root / "index.html").write_text(page(f"{SITE_NAME} — DGFT, Customs & BIS alerts", home,
                                          "Free plain-English alerts on DGFT notifications, public notices and customs changes for Indian exporters."), encoding="utf-8")
    cfg = json.dumps({"url": os.getenv("SUPABASE_URL", ""), "key": os.getenv("SUPABASE_ANON_KEY", "")})
    (root / "unsubscribe.html").write_text(page("Unsubscribe", f"""<div class="page-h"><h1>Unsubscribe</h1></div><div class="card" id="u">Unsubscribing…</div>
<script>const C={cfg};const t=new URLSearchParams(location.search).get('t');
fetch(C.url+'/rest/v1/rpc/unsubscribe',{{method:'POST',headers:{{apikey:C.key,Authorization:'Bearer '+C.key,'Content-Type':'application/json'}},
body:JSON.stringify({{token:t}})}}).then(r=>document.getElementById('u').textContent=r.ok?'You have been unsubscribed.':'Link invalid or expired.');</script>"""), encoding="utf-8")
    urls = [f"{SITE_URL}/"] + [f"{SITE_URL}/{f}" for f in legal.pages()] + [f"{SITE_URL}/n/{n['id']}.html" for n in ranked]
    (root / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                      + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>", encoding="utf-8")
    for fname, (title, body) in legal.pages().items():
        (root / fname).write_text(page(f"{title} — {SITE_NAME}", f'<div class="page-h"></div><div class="card">{body}</div>'), encoding="utf-8")
    (root / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    return len(ranked)
