"""Payment thank-you page (/thanks.html) and Firm client setup page (/clients.html?t=<private link>)."""
from __future__ import annotations

import json
import os
from pathlib import Path

import legal
from sitegen import SITE_URL, _product_groups, e, page


def thanks_body() -> str:
    c = legal.cfg()
    return f"""<div class="page-h"><div class="eyebrow"><i></i>Payment received</div><h1>Thank you</h1></div>
<div class="card"><p><b>Your plan switches on automatically within a few minutes.</b> We email you a confirmation at the
address you entered on the payment page, with your plan's end date.</p>
<p><b>Firm plan:</b> the confirmation email has a private link where you add your clients and their products
(up to 25). Your alerts then show which client each notice affects.</p>
<p>Didn't get the email within an hour? Check spam, then write to <a href="mailto:{e(c['email'])}">{e(c['email'])}</a>
with your payment ID from Razorpay's receipt.</p>
<p class="m">Plans never renew automatically. 7-day refund on your first payment: <a href="{SITE_URL}/refund.html">Refund Policy</a>.</p>
<p><a class="btn" href="{SITE_URL}/alerts.html">See recent alerts</a></p></div>"""


def clients_body() -> str:
    cfg = json.dumps({"url": os.getenv("SUPABASE_URL", ""), "key": os.getenv("SUPABASE_ANON_KEY", "")})
    groups = json.dumps([{"n": g["name"], "k": [k.lower() for k in g.get("keywords", [])], "c": [str(x) for x in g["codes"]]}
                         for g in _product_groups()], ensure_ascii=False).replace("</", "<\\/")
    mail = e(legal.cfg()["email"])
    return f"""<div class="page-h"><div class="eyebrow"><i></i>Firm plan</div><h1>Your clients</h1>
<p class="m" style="font-size:15px">Add up to 25 clients. For each, type what they ship (we fill in the HS codes) or the codes
themselves. Your alerts show which clients each DGFT notice affects. This page opens only from the private link in your
email; don't share it.</p></div>
<div class="card" id="cl-wrap"><p id="cl-msg" role="status" aria-live="polite">Loading…</p>
<form id="cl" hidden><div id="rows"></div>
<p><button class="btn ghost" type="button" id="add">+ Add a client</button></p>
<button class="btn" id="save">Save clients</button><p id="cl-done" class="m" role="status" aria-live="polite"></p></form></div>
<script>const C={cfg},G={groups};
const t=new URLSearchParams(location.search).get('t'),msg=document.getElementById('cl-msg'),rows=document.getElementById('rows');
const rpc=(fn,b)=>fetch(C.url+'/rest/v1/rpc/'+fn,{{method:'POST',headers:{{apikey:C.key,Authorization:'Bearer '+C.key,'Content-Type':'application/json'}},body:JSON.stringify(b)}}).then(r=>r.ok?r.json():null).catch(()=>null);
function codesFor(text){{const out=new Set();(text||'').toLowerCase().split(/[,;\\n]+/).map(s=>s.trim()).filter(Boolean).forEach(q=>{{
 const d=q.replace(/\\s/g,'');if(/^[0-9]{{2,8}}$/.test(d)){{out.add(d);return;}}
 G.forEach(g=>{{if(g.n.toLowerCase().includes(q)||g.k.some(k=>new RegExp('\\\\b'+k.replace(/[.*+?^${{}}()|[\\]\\\\]/g,'\\\\$&')+'s?\\\\b').test(q)))g.c.forEach(c=>out.add(c));}});}});
 return [...out].slice(0,60);}}
function row(c,i){{const d=document.createElement('div');d.className='grp';d.innerHTML=
 '<label class="l" for="n'+i+'">Client '+(i+1)+' name</label><input id="n'+i+'" class="cn" maxlength="80" value="">'+
 '<label class="l" for="p'+i+'">What they ship <span class="m">(products and/or HS codes, comma separated)</span></label>'+
 '<input id="p'+i+'" class="cp" maxlength="300" placeholder="e.g. carpets, 7113, cotton bedsheets">'+
 '<div class="m cc"></div><button type="button" class="x" aria-label="Remove client '+(i+1)+'">Remove</button>';
 d.querySelector('.cn').value=c.name||'';d.querySelector('.cp').value=c.products||(c.hs||[]).join(', ');
 const show=()=>{{const k=codesFor(d.querySelector('.cp').value);d.querySelector('.cc').textContent=k.length?('HS codes: '+k.join(', ')):'No HS codes recognised yet: type a product or a code.';}};
 d.querySelector('.cp').addEventListener('input',show);show();d.querySelector('.x').onclick=()=>{{d.remove();}};return d;}}
function add(c){{if(rows.children.length>=25){{msg.textContent='The Firm plan covers up to 25 clients.';return;}}rows.appendChild(row(c||{{}},rows.children.length));}}
document.getElementById('add').onclick=()=>add();
(async()=>{{if(!t){{msg.textContent='Please open this page from the link in your Firm plan email.';return;}}
 const d=await rpc('get_firm_clients',{{token:t}});
 if(!d){{msg.textContent='This link is invalid or expired. Write to {mail} for a new one.';return;}}
 if(d.plan!=='firm'){{msg.textContent='Client setup is part of the Firm plan. Your account ('+d.email+') is on '+d.plan+'.';return;}}
 msg.textContent='Account: '+d.email+' · Firm plan until '+(d.paid_until||'');document.getElementById('cl').hidden=false;
 (d.clients.length?d.clients:[{{}}]).forEach(c=>add(c));}})();
document.getElementById('cl').onsubmit=async ev=>{{ev.preventDefault();const done=document.getElementById('cl-done');done.textContent='Saving…';
 const list=[...rows.children].map(r=>({{name:r.querySelector('.cn').value.trim(),products:r.querySelector('.cp').value.trim(),hs:codesFor(r.querySelector('.cp').value)}})).filter(c=>c.name);
 const r=await rpc('save_firm_clients',{{token:t,clients:list}});
 done.textContent=r&&r.ok?('Saved '+r.clients+' client(s). Alerts from tomorrow use these codes.'):('Could not save: '+((r&&r.error)||'please try again')+'.');}};</script>"""


def _noindex(h: str) -> str:
    return h.replace('<meta name="description"', '<meta name="robots" content="noindex,nofollow"><meta name="description"', 1)


def build(root: str | Path = "public") -> list[str]:
    root = Path(root)
    (root / "thanks.html").write_text(_noindex(page("Thank you | Sagarlekh", thanks_body())), encoding="utf-8")
    (root / "clients.html").write_text(_noindex(page("Your clients | Sagarlekh Firm", clients_body())), encoding="utf-8")
    return ["thanks.html", "clients.html"]
