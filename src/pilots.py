"""DharaLabs pilot pages (demand tests, Oct-Nov 2026): /pilot/eodc.html, /pilot/eudr.html, /pilot/cbam.html.

Honest "we're building this" pages with a short interest form (saved to Supabase table pilot_interest).
Edit the text in PILOTS below. Remove a pilot by deleting its entry.
"""
from __future__ import annotations

import html
import json
import os
from pathlib import Path

from sitegen import page

e = html.escape

PILOTS = {
    "eodc": {
        "title": "Export obligation watch for Advance Authorisation and EPCG",
        "tag": "For CAs, DGFT consultants, customs brokers and exporters with AA / EPCG licences",
        "problem": [
            "Every Advance Authorisation and EPCG licence carries an export obligation with a deadline. Miss it, or "
            "close it late, and the bank guarantee stays blocked, duty plus interest can be demanded, and the firm can "
            "be put on DGFT's watch list.",
            "DGFT's old online EODC monitoring system was withdrawn in 2023. Most firms now track obligations in "
            "Excel or from memory, licence by licence.",
        ],
        "offer": [
            "You send us your licence list (or a DGFT licence export). We set it up for you.",
            "One dashboard per client: obligation value, exports counted so far, shortfall, and days left.",
            "Email reminders at 180, 90, 30 and 7 days before each obligation or extension deadline.",
            "A ready checklist of documents for EODC / redemption when an obligation is met.",
            "Any DGFT notice that changes AA / EPCG rules, explained in plain English the same day.",
        ],
        "pilot": "Free for the first 5 firms until 31 Jan 2027, in return for feedback. Planned price after the pilot: "
                 "Rs 999/month for a practice (up to 50 licences), Rs 4,999/year for a single exporter.",
        "fields": ("How many AA / EPCG licences do you (or your clients) hold?", "e.g. 12 licences across 5 clients"),
        "limits": "We track and remind; filing with DGFT stays with you or your consultant.",
    },
    "eudr": {
        "title": "EUDR data pack for wood, furniture and handicraft exporters",
        "tag": "For exporters selling wooden furniture, handicrafts, paper, leather or coffee to the EU",
        "problem": [
            "The EU Deforestation Regulation (EUDR) applies from 30 December 2026 for medium and large EU buyers and "
            "30 June 2027 for small ones. Your EU buyer must show where the wood or raw material came from, with "
            "plot geolocation, and that it was legally produced.",
            "India is classed as low risk, so the checks are simpler, but buyers still need the geolocation and legality "
            "papers from you. Exporters who can't supply them early risk losing orders to suppliers who can.",
        ],
        "offer": [
            "A simple phone form for your wood suppliers / sawmills to record source location and upload papers.",
            "We collect transit permits, purchase bills and legality documents into one file per shipment.",
            "A buyer-ready EUDR data pack (geolocation file + documents + summary) your EU buyer can use for their "
            "due diligence statement.",
            "Plain-English updates whenever the EU or DGFT changes the rules.",
        ],
        "pilot": "Free for the first 5 exporters for one shipment, in return for feedback. Planned price after the pilot: "
                 "from Rs 14,999/year per exporter.",
        "fields": ("What do you export to the EU, and roughly how many shipments a year?", "e.g. sheesham furniture, 20 containers/year to Germany"),
        "limits": "The legal due diligence statement is filed by the EU operator (your buyer). We prepare the data and "
                  "documents they need from you. Not legal advice.",
    },
    "cbam": {
        "title": "CBAM emissions data pack for steel and aluminium exporters",
        "tag": "For MSMEs exporting iron, steel, aluminium or their articles (fasteners, fabrications, castings) to the EU",
        "problem": [
            "Since 1 January 2026 the EU's Carbon Border Adjustment Mechanism (CBAM) is in its definitive phase. EU "
            "importers must report the embedded emissions of every steel and aluminium product they buy and pay for them.",
            "If you can't give your buyer real emissions data, they must use EU default values, which are usually "
            "higher. Many small EU buyers are switching to suppliers who can send the data. Consultants quote lakhs.",
        ],
        "offer": [
            "You share electricity bills, fuel and raw-material purchase data, and production quantities.",
            "We calculate embedded emissions per product using the EU method and fill the EU supplier communication "
            "template your buyer asks for.",
            "A checklist and file ready for an accredited verifier, so verification is quicker and cheaper.",
            "Plain-English alerts when CBAM rules or default values change.",
        ],
        "pilot": "Free for the first 5 exporters for one product line, in return for feedback. Planned price after the "
                 "pilot: from Rs 24,999/year per site.",
        "fields": ("What do you make and export to the EU (product, HS code if known, tonnes/year)?", "e.g. steel fasteners HS 7318, 300 t/year to Italy"),
        "limits": "Verification must be done by an accredited verifier; we prepare the data. Not legal or tax advice.",
    },
}


def _form(key: str, p: dict) -> str:
    cfg = json.dumps({"url": os.getenv("SUPABASE_URL", ""), "key": os.getenv("SUPABASE_ANON_KEY", "")})
    q, ph = p["fields"]
    return f"""<div class="card" id="join"><h2 style="margin-top:0">Join the pilot</h2>
<form id="pf" autocomplete="on">
<label class="l" for="p-name">Your name</label><input id="p-name" name="name" required>
<label class="l" for="p-email">Work email</label><input id="p-email" name="email" type="email" required placeholder="you@yourfirm.in">
<label class="l" for="p-co">Company</label><input id="p-co" name="company" required>
<label class="l" for="p-city">City</label><input id="p-city" name="city">
<label class="l" for="p-phone">Phone / WhatsApp <span class="m">(optional, only if you want a call)</span></label><input id="p-phone" name="phone">
<label class="l" for="p-q">{e(q)}</label><textarea id="p-q" name="details" rows="3" placeholder="{e(ph)}"></textarea>
<label class="m agree"><input type="checkbox" required> I agree to be contacted about this pilot.</label>
<button class="btn">Request a pilot spot</button><div id="pm" class="m" aria-live="polite"></div></form></div>
<script>const PC={cfg};document.getElementById('pf').onsubmit=async ev=>{{ev.preventDefault();
const d=new FormData(ev.target),m=document.getElementById('pm');m.textContent='Sending…';
const body={{offer:'{key}',name:d.get('name'),email:(d.get('email')||'').trim().toLowerCase(),company:d.get('company'),
city:d.get('city')||null,phone:d.get('phone')||null,details:d.get('details')||null,page:location.pathname}};
try{{const r=await fetch(PC.url+'/rest/v1/pilot_interest',{{method:'POST',headers:{{apikey:PC.key,Authorization:'Bearer '+PC.key,
'Content-Type':'application/json',Prefer:'return=minimal'}},body:JSON.stringify(body)}});
m.textContent=r.ok?'Thank you. We will email you within 2 working days.':'Something went wrong. Please email dharalabs.co@gmail.com.';
if(r.ok)ev.target.reset();}}catch(_){{m.textContent='Network error. Please email dharalabs.co@gmail.com.'}}}};</script>"""


def _body(key: str, p: dict) -> str:
    li = lambda xs: "".join(f"<li>{e(x)}</li>" for x in xs)
    return f"""<div class="page-h"><div class="eyebrow"><i></i>DharaLabs pilot · building now</div>
<h1>{e(p['title'])}</h1><p class="m" style="font-size:16px">{e(p['tag'])}</p></div>
<div class="card"><h2 style="margin-top:0">The problem</h2>{''.join(f'<p>{e(x)}</p>' for x in p['problem'])}</div>
<div class="card"><h2 style="margin-top:0">What we are building</h2><ul>{li(p['offer'])}</ul></div>
<div class="card"><h2 style="margin-top:0">The pilot</h2><p>{e(p['pilot'])}</p><p class="m">{e(p['limits'])}</p>
<p class="m">Built by DharaLabs, Jaipur, the team behind <a href="/">Sagarlekh</a> plain-English DGFT alerts.
Questions: dharalabs.co@gmail.com</p></div>
{_form(key, p)}"""


def build(root: str | Path = "public") -> list[str]:
    out = Path(root) / "pilot"
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for key, p in PILOTS.items():
        (out / f"{key}.html").write_text(page(f"{p['title']} — DharaLabs pilot", _body(key, p), p["tag"]), encoding="utf-8")
        made.append(f"pilot/{key}.html")
    return made
