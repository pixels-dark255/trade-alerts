"""Agent 4 — SEO site builder: one public page per notice + landing/signup page.

Every notice page is indexable by Google, so the archive itself becomes the
free acquisition channel (people search for "DGFT notification 23/2025-26").

UI: Sagarlekh brand C1 'Shirorekha S' — navy #0f2a4a, blue #1f6feb. Logo files live in /assets.
"""
from __future__ import annotations

import html
import json
import os
import shutil
from pathlib import Path

import legal
from digest import SITE_NAME, SITE_URL, calendar_links, ics_text, rank

e = html.escape

# ---------- brand assets: logo + favicons are files in <repo>/assets, copied into the site on build ----------
ASSETS = Path(__file__).resolve().parents[1] / "assets"

WAVE = ('<svg class="wave" viewBox="0 0 600 40" preserveAspectRatio="none" fill="none" aria-hidden="true">'
        '<path d="M0 14' + "".join(" c12.5-10 25-10 37.5 0 s25 10 37.5 0" for _ in range(8)) + '" stroke="#1f6feb" stroke-width="2.5"/>'
        '<path d="M0 30h600" stroke="#0B2536" stroke-width="1.5"/></svg>')

ICON = {
    "doc": '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/><path d="M10 13h6M10 17h4"/>',
    "plain": '<path d="M4 6h16M4 12h10M4 18h13"/>',
    "send": '<path d="M21 4L3 11l6 2.5L19 6l-8 9v5l3.5-4 4.5 3z"/>',
    "hash": '<path d="M5 9h14M5 15h14M10 4L8 20M16 4l-2 16"/>',
    "ext": '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
}


def icon(name: str, size: int = 22, color: str = "#1f6feb") -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON[name]}</svg>')


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500'
         '&family=IBM+Plex+Sans:wght@400;500;600&family=Tiro+Devanagari+Hindi&display=swap">')

CSS = """:root{--ink:#0f2a4a;--teal:#1f6feb;--gold:#1f6feb;--shallow:#E3EDFD;--paper:#F6F8FB;--line:#E3E8EF;--slate:#4F5F73;
--sans:'IBM Plex Sans','Helvetica Neue',Arial,sans-serif;--mono:'IBM Plex Mono',ui-monospace,Consolas,monospace;--deva:'Tiro Devanagari Hindi','Noto Sans Devanagari',serif}
*{box-sizing:border-box}html{scroll-padding-top:84px}body{margin:0;font-family:var(--sans);color:var(--ink);background:var(--paper);line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:var(--teal)}a:hover{color:var(--ink)}
.w{max-width:1120px;margin:auto;padding:0 20px}
.nav{position:sticky;top:0;z-index:10;background:var(--ink);border-bottom:1px solid #1d3d63}
.nav .w{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;padding-top:12px;padding-bottom:12px}
.brand{display:flex;align-items:center}.brand img{display:block;height:40px;width:auto}
.nav nav{display:flex;flex-wrap:wrap;align-items:center;gap:20px;font-weight:500;font-size:15px}
.nav nav a{color:#fff;text-decoration:none}.nav nav a:hover{color:#8DB8FF}.nav .btn{background:var(--teal)}.nav .btn:hover{background:#fff;color:var(--ink)!important}
.btn{display:inline-block;background:var(--ink);color:#fff!important;text-decoration:none;font-weight:600;padding:11px 18px;border-radius:10px;border:0;cursor:pointer;font-family:inherit;font-size:15px}
.btn:hover{background:var(--teal)}.btn.ghost{background:transparent;color:var(--ink)!important;border:1.5px solid var(--ink)}.btn.ghost:hover{background:var(--shallow)}
.eyebrow{display:flex;align-items:center;gap:10px;font-family:var(--mono);font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--teal)}
.eyebrow i{width:8px;height:8px;border-radius:50%;background:var(--gold)}
.hero{display:flex;flex-wrap:wrap;gap:48px;align-items:flex-start;padding:56px 0 36px}
.hero>div{flex:1 1 440px;min-width:0}
.hero h1{margin:16px 0;font-size:clamp(36px,5.4vw,58px);line-height:1.04;font-weight:600;letter-spacing:-.035em}
.hero h1 span{color:var(--teal)}.hero p{font-size:19px;color:#33475B;max-width:540px;margin:0 0 18px}
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
#signup{box-shadow:0 18px 40px -26px rgba(15,42,74,.4)}#signup h2{margin:0 0 4px;font-size:24px}
label.l{display:block;font-size:14px;font-weight:600;margin-top:10px}
input,select{font:inherit;font-size:15px;padding:12px 14px;border:1.5px solid #C3CEDB;border-radius:10px;width:100%;margin:5px 0;background:#fff;color:var(--ink)}
input:focus,select:focus{outline:2px solid var(--teal);outline-offset:1px;border-color:var(--teal)}
input[type=checkbox]{width:auto;margin:0 8px 0 0;accent-color:var(--teal)}.agree{display:flex;align-items:flex-start;margin:10px 0}
form button{width:100%;margin-top:6px;padding:14px;font-size:16px}#msg{margin-top:8px;min-height:1.2em}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}.grid .card{margin:0;display:flex;flex-direction:column;gap:6px}
.plan{font-family:var(--mono);font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--teal)}
.price{font-size:38px;font-weight:600;letter-spacing:-.03em;line-height:1.1}.price .m{font-size:15px;letter-spacing:0}
.plans .btn{font-size:14px;padding:9px 14px;margin:6px 6px 0 0}
.page-h{padding:36px 0 4px}.page-h h1{font-size:clamp(28px,4vw,40px);letter-spacing:-.03em;line-height:1.15;margin:10px 0}
footer{background:var(--ink);color:#C9D6E6;margin-top:64px;padding:40px 0;font-size:14px}footer a{color:#fff}
footer .w{display:flex;flex-wrap:wrap;gap:28px;justify-content:space-between}footer p{max-width:520px;margin:12px 0 0}
.lead{font-size:17px;color:#33475B;max-width:720px}
.feats{list-style:none;padding:0;margin:8px 0 10px;font-size:14.5px;flex:1}.feats li{display:flex;gap:8px;margin:7px 0}
.feats .tick{color:var(--teal);font-weight:600;flex-shrink:0}.feats li.later{color:var(--slate)}.feats li.later .tick{color:#9AA7B5}
.soon{font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;background:var(--shallow);color:var(--slate);padding:2px 6px;border-radius:5px;margin-left:6px;white-space:nowrap}
.perks ul{margin:8px 0 0;padding-left:20px;font-size:15px}.perks li{margin:5px 0}
.tbl{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:16px}
.cmp{width:100%;border-collapse:collapse;font-size:14.5px}.cmp th,.cmp td{text-align:left;padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:top}
.cmp th{font-family:var(--mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--teal)}.cmp td:first-child{font-weight:600}.cmp tr:last-child td{border-bottom:0}
.faq{padding:16px 20px;margin:10px 0}.faq summary{cursor:pointer;font-weight:600;font-size:16px}.faq p{margin:10px 0 0;color:#33475B}
.cal{font-size:14px}
.filters{display:grid;grid-template-columns:minmax(0,1fr) 180px 160px;gap:10px;padding:14px}.filters input,.filters select{margin:0}
@media(max-width:640px){.filters{grid-template-columns:1fr}}
@media(max-width:640px){.nav nav{gap:14px;font-size:14px}.nav .btn{padding:9px 14px}.rows{grid-template-columns:1fr}.hero{padding-top:32px}}
@media(max-width:560px){.nav nav a:not(.btn){display:none}.nav .w{flex-wrap:nowrap}}"""


def brand_link(dark: bool = True) -> str:
    logo = "sagarlekh-lockup-on-navy.svg" if dark else "sagarlekh-lockup.svg"
    return (f'<a class="brand" href="{SITE_URL}/" aria-label="Sagarlekh home">'
            f'<img src="{SITE_URL}/assets/{logo}" alt="Sagarlekh by DharaLabs" width="165" height="40"></a>')


def _tg() -> str:
    return os.getenv("TELEGRAM_CHANNEL", "").strip().lstrip("@")


def page(title: str, body: str, desc: str = "") -> str:
    tg = _tg()
    tg_link = f'<a href="https://t.me/{e(tg)}">Telegram</a>' if tg else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}"><meta name="theme-color" content="#0f2a4a">
<link rel="icon" href="{SITE_URL}/assets/favicon.svg" type="image/svg+xml"><link rel="icon" href="{SITE_URL}/assets/favicon.ico" sizes="any"><link rel="apple-touch-icon" href="{SITE_URL}/assets/apple-touch-icon.png">{FONTS}<style>{CSS}</style></head><body>
<header class="nav"><div class="w">{brand_link()}
<nav><a href="{SITE_URL}/alerts.html">All alerts</a><a href="{SITE_URL}/#pricing">Plans</a><a href="{SITE_URL}/#faq">FAQ</a>{tg_link}
<a class="btn" href="{SITE_URL}/#signup">Subscribe free</a></nav></div></header>
<main class="w">{body}</main>
<footer><div class="w"><div>{brand_link()}
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


def _cfg_pricing() -> dict:
    import yaml
    f = Path(__file__).resolve().parents[1] / "config" / "pricing.yaml"
    return yaml.safe_load(f.read_text(encoding="utf-8")) if f.exists() else {"plans": []}


SOON = '<span class="soon">Coming soon</span>'


def pricing() -> str:
    cfg = _cfg_pricing()
    cards = []
    for p in cfg.get("plans", []):
        feats = "".join(
            f'<li class="{"later" if f.get("soon") else ""}"><span class="tick">{"○" if f.get("soon") else "✓"}</span>'
            f'<span>{e(f["text"])}{SOON if f.get("soon") else ""}</span></li>'
            for f in p.get("features", []))
        if p.get("monthly"):
            m, y = p["monthly"], p["yearly"]
            save = m["price"] * 12 - y["price"]
            price = f'₹{_inr(m["price"])}<span class="m">/month</span>'
            ctas = (f'<div><a class="btn" href="{e(m["url"])}">Monthly ₹{_inr(m["price"])}</a>'
                    f'<a class="btn ghost" href="{e(y["url"])}">Yearly ₹{_inr(y["price"])}</a></div>'
                    f'<div class="m">Yearly saves ₹{_inr(save)}. Pay with the email you subscribed with.</div>')
        else:
            price = "₹0"
            ctas = '<div><a class="btn ghost" href="#signup">Subscribe free</a></div>'
        cards.append(f"""<div class="card"><span class="plan">{e(p['name'])}</span><div class="m">{e(p.get('for', ''))}</div>
<div class="price">{price}</div><ul class="feats">{feats}</ul>{ctas}</div>""")
    perks = "".join(f"<li>{e(x)}</li>" for x in cfg.get("perks", []))
    cmp = cfg.get("compare") or {}
    th = "".join(f"<th>{e(h)}</th>" for h in cmp.get("header", []))
    trs = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in cmp.get("rows", []))
    faq = "".join(f'<details class="card faq"><summary>{e(x["q"])}</summary><p>{e(x["a"])}</p></details>'
                  for x in cfg.get("faq", []))
    return f"""<h2 id="pricing">Plans</h2><p class="lead">{e(cfg.get('intro', ''))}</p>
<div class="grid plans">{''.join(cards)}</div>
<div class="card perks"><b>For paid plans</b><ul>{perks}</ul></div>
<h2 id="compare" style="font-size:24px">Compare plans</h2><div class="tbl"><table class="cmp"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>
<h2 id="faq" style="font-size:24px">Questions</h2>{faq}
<p class="m">{e(cfg.get('disclaimer', ''))}</p>"""


def trust() -> str:
    items = (("doc", "From official sources", "DGFT notices read every morning; Customs &amp; BIS coming soon"),
             ("plain", "Written plainly", "What changed, who is affected, what to do"),
             ("hash", "Matched to your HS codes", "Only the changes that touch your products"),
             ("send", "Email or Telegram", "Wherever you read first"))
    return '<div class="trust">' + "".join(
        f'<div>{icon(i, 26)}<div><b>{t}</b><span>{d}</span></div></div>' for i, t, d in items) + "</div>"


def alerts_page(notices: list[dict]) -> str:
    """Separate page with every alert, newest first, plus instant search and filters (no server needed)."""
    kinds = sorted({n["kind"] for n in notices})
    cards = []
    for n in notices:
        s = n.get("summary") or {}
        hay = " ".join(str(x) for x in (s.get("headline"), s.get("summary"), n.get("title"), n.get("number"),
                                         " ".join(n.get("hs_codes") or []))).lower()
        cards.append(f'<div class="item" data-k="{e(n["kind"])}" data-i="{e(n.get("impact") or "low")}" '
                     f'data-t="{e(hay)}">{notice_card(n)}</div>')
    kopts = "".join(f'<option>{e(k)}</option>' for k in kinds)
    return f"""<div class="page-h"><div class="eyebrow"><i></i>Archive</div><h1>All alerts</h1>
<p class="m" style="font-size:15px">Every DGFT notification, public notice and trade notice we have summarised, newest first.
Want only the ones for your HS codes? <a href="{SITE_URL}/#signup">Subscribe free</a>.</p></div>
<div class="card filters"><input id="q" type="search" placeholder="Search by word, notice number or HS code (e.g. 3923)">
<select id="fk"><option value="">All types</option>{kopts}</select>
<select id="fi"><option value="">All impact</option><option value="high">High impact</option><option value="medium">Medium impact</option><option value="low">Low impact</option></select></div>
<div class="m" id="count">{len(notices)} alerts</div>
<div id="list">{''.join(cards)}</div>
<script>(function(){{var q=document.getElementById('q'),fk=document.getElementById('fk'),fi=document.getElementById('fi'),
c=document.getElementById('count'),items=[].slice.call(document.querySelectorAll('#list .item'));
function run(){{var t=q.value.trim().toLowerCase(),k=fk.value,i=fi.value,n=0;
items.forEach(function(el){{var ok=(!t||el.dataset.t.indexOf(t)>-1)&&(!k||el.dataset.k===k)&&(!i||el.dataset.i===i);
el.style.display=ok?'':'none';if(ok)n++;}});c.textContent=n+' alert'+(n===1?'':'s');}}
q.addEventListener('input',run);fk.addEventListener('change',run);fi.addEventListener('change',run);}})();</script>"""


def build(notices: list[dict], sectors: list[str], out: str = "public") -> int:
    root = Path(out)
    (root / "n").mkdir(parents=True, exist_ok=True)
    if ASSETS.is_dir():
        shutil.copytree(ASSETS, root / "assets", dirs_exist_ok=True)
    ranked = rank([n for n in notices if n.get("summary")])
    for n in ranked:
        s = n["summary"]
        hs = ", ".join(n.get("hs_codes") or [])
        official = (f'<a class="btn" href="{e(n["url"])}" rel="noopener">{icon("ext", 16, "#fff")} Read official document</a>'
                    if n.get("url") else "")
        cal = ('<br><span class="cal">' + calendar_links(n).lstrip(' ·') + '</span>') if s.get('deadline') else ''
        detail = f"""<div class="card"><div class="rows">
<span>Who is affected</span><span>{e(s.get('who_is_affected') or '—')}</span>
<span>Deadline</span><span>{e(s.get('deadline') or 'Not stated')}{cal}</span>
<span>HS codes</span><span>{f'<span class="hs"># {e(hs)}</span>' if hs else '—'}</span>
<span>हिंदी</span><span class="deva" style="font-size:18px">{e(s.get('headline_hi') or '')}</span>
<span>Original title</span><span>{e(n['title'])}</span></div>
{f'<div class="foot"><span class="m">Always verify with the official text.</span>{official}</div>' if official else ''}</div>"""
        body = (f'<div class="page-h"><a href="{SITE_URL}/alerts.html" class="m">← All alerts</a></div>'
                + notice_card(n, link=False) + detail + signup_form(sectors))
        if s.get("deadline"):
            (root / "n" / f"{n['id']}.ics").write_text(ics_text(n), encoding="utf-8")
        title = f"{n['authority']} {n['kind']} {n.get('number') or ''}: {s.get('headline') or n['title']}"
        (root / "n" / f"{n['id']}.html").write_text(page(title[:110], body, s.get("summary", "")[:155]), encoding="utf-8")
    by_date = sorted(ranked, key=lambda n: n.get("notice_date") or "", reverse=True)
    (root / "alerts.html").write_text(page(f"All DGFT alerts — {SITE_NAME}", alerts_page(by_date),
                                           "Every DGFT notification, public notice and trade notice, explained in plain English."),
                                      encoding="utf-8")
    tg = _tg()
    tg_btn = f' <a class="btn ghost" href="https://t.me/{e(tg)}">Join on Telegram</a>' if tg else ""
    home = f"""<section class="hero"><div>
<div class="eyebrow"><i></i>DGFT notices · explained daily</div>
<h1>India’s trade rules, written plainly. <span>Every morning.</span></h1>
<p>Every morning we read new DGFT notifications, public notices and trade notices, explain them in plain English
(with a Hindi line) and tell you what to do and by when — filtered to your HS codes.</p>
<div><a class="btn" href="{SITE_URL}/alerts.html">See all alerts</a>{tg_btn}</div>
<p class="deva" style="margin-top:28px;font-size:20px">सागरलेख — सरल भाषा में व्यापार नियम</p></div>
<div>{signup_form(sectors)}</div></section>
{WAVE}{trust()}{pricing()}"""
    (root / "index.html").write_text(page(f"{SITE_NAME} — DGFT alerts for exporters", home,
                                          "Plain-English alerts on DGFT notifications, public notices and trade notices for Indian exporters, matched to your HS codes."), encoding="utf-8")
    cfg = json.dumps({"url": os.getenv("SUPABASE_URL", ""), "key": os.getenv("SUPABASE_ANON_KEY", "")})
    (root / "unsubscribe.html").write_text(page("Unsubscribe", f"""<div class="page-h"><h1>Unsubscribe</h1></div><div class="card" id="u">Unsubscribing…</div>
<script>const C={cfg};const t=new URLSearchParams(location.search).get('t');
fetch(C.url+'/rest/v1/rpc/unsubscribe',{{method:'POST',headers:{{apikey:C.key,Authorization:'Bearer '+C.key,'Content-Type':'application/json'}},
body:JSON.stringify({{token:t}})}}).then(r=>document.getElementById('u').textContent=r.ok?'You have been unsubscribed.':'Link invalid or expired.');</script>"""), encoding="utf-8")
    urls = [f"{SITE_URL}/", f"{SITE_URL}/alerts.html"] + [f"{SITE_URL}/{f}" for f in legal.pages()] + [f"{SITE_URL}/n/{n['id']}.html" for n in ranked]
    (root / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                      + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>", encoding="utf-8")
    for fname, (title, body) in legal.pages().items():
        (root / fname).write_text(page(f"{title} — {SITE_NAME}", f'<div class="page-h"></div><div class="card">{body}</div>'), encoding="utf-8")
    (root / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    return len(ranked)
