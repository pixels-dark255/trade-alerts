"""Policy pages: Privacy, Terms, Refunds, Cookies, Contact, Your data (DPDP Act 2023, IT Rules, Consumer
Protection (E-Commerce) Rules 2020, Razorpay requirements).
Plain-language templates written for this service. Have them reviewed by a lawyer/CA when revenue starts.
Business details come from environment variables (GitHub → Settings → Variables), with safe defaults."""
from __future__ import annotations

import html
import json
import os
from datetime import date

e = html.escape
UPDATED = "20 October 2026"          # change when the policy text changes (not on every build)


def cfg() -> dict:
    env = lambda k, d="": (os.getenv(k) or d).strip()
    return {
        "brand": env("SITE_NAME", "Sagarlekh"),
        "company": env("LEGAL_NAME", "DharaLabs"),
        "owner": env("OWNER_NAME"),                         # proprietor / founder name, shown on Contact
        "email": env("CONTACT_EMAIL", "dharalabs.co@gmail.com"),
        "phone": env("CONTACT_PHONE"),
        "address": env("BUSINESS_ADDRESS", "Jaipur, Rajasthan, India"),
        "city": env("JURISDICTION", "Jaipur"),
        "grievance": env("GRIEVANCE_OFFICER"),              # name + designation, e.g. "Yashika Singhal, Founder"
        "gstin": env("GSTIN"),
        "site": env("SITE_URL", "https://alerts.dharalabs.in").rstrip("/"),
    }


def pages() -> dict[str, tuple[str, str]]:
    """Returns {filename: (title, body_html)}."""
    c = {k: e(v) for k, v in cfg().items()}
    mail = f'<a href="mailto:{c["email"]}">{c["email"]}</a>'
    officer = c["grievance"] or f"Grievance Officer, {c['company']}"
    upd = f'<p class="m">Last updated: {UPDATED}</p>'

    privacy = f"""<h1>Privacy Policy</h1>{upd}
<p>{c['brand']} is a service of <b>{c['company']}</b>, {c['address']} ("we", "us"). This policy explains what personal
data we collect, why, and your rights under India's Digital Personal Data Protection Act, 2023 (DPDP Act).</p>
<h2>What we collect, and why</h2>
<ul>
<li><b>Alert sign-up:</b> your email address (required), and if you choose to give them, company name, HS codes / products
and sector. We use these only to send the alerts you asked for, matched to your products. We also record when you gave consent.</li>
<li><b>Paid plans:</b> your plan and the date it runs until. Payments are made on Razorpay's pages; we never see or store
card, UPI or bank details.</li>
<li><b>Pilot interest forms</b> (pages under /pilot/): name, work email, company, and optionally city, phone and a short
description, only to contact you about that pilot.</li>
<li><b>Requests about your data</b> (the "Your data" page): your email and your request, only to act on it.</li>
<li><b>Emails you send us:</b> kept in our mailbox to reply and keep a record of our conversation.</li>
<li><b>Business outreach:</b> we may email businesses using contact details that the business itself publishes (for
example on its website or an association directory). We send at most three short emails and stop at once if you reply "no";
we then keep only your address on a do-not-contact list so we never email you again.</li>
</ul>
<p>We do <b>not</b> collect more than this, we do not sell or rent personal data, we do not use it for advertising, and we do
not build profiles. The website sets <b>no cookies</b> and uses <b>no analytics or tracking</b> (see the
<a href="cookies.html">Cookie Policy</a>).</p>
<h2>Who processes it for us</h2>
<p>We use these service providers, only to run the service: Supabase (database), Resend (sending alert emails),
Google (Gmail, our mailbox), GitHub (website hosting; GitHub keeps standard server logs such as IP addresses),
Razorpay (payments), ImprovMX (email forwarding) and Anthropic (AI). The AI turns public government notices into
summaries; when you reply to one of our emails, the text of your reply may also be processed by Anthropic's API to help us
draft an answer, under terms that do not allow it to be used to train AI models. Some providers store data outside India,
which the DPDP Act permits except for countries the Government restricts.</p>
<h2>How long we keep it</h2>
<ul><li>Subscribers: while you are subscribed. After you unsubscribe we delete your record within 90 days.
"Delete my data" (in every email) deletes it straight away.</li>
<li>Pilot interest and data requests: up to 12 months, then deleted.</li>
<li>Payment records: as long as tax law requires (usually 8 years).</li></ul>
<h2>Children</h2><p>{c['brand']} is a business service for people aged 18 or over. We do not knowingly collect data of
anyone under 18. If you believe a child has given us data, write to us and we will delete it.</p>
<h2>Your rights</h2>
<p>You can ask to access, correct, update or erase your data, withdraw your consent at any time (as easily as you gave it:
every alert email has one-click <b>Unsubscribe</b> and <b>Delete my data</b> links), nominate another person to exercise
these rights, and raise a grievance. Use the <a href="your-data.html">Your data</a> page or write to {mail}. We reply within
7 days and complete requests within 30 days.</p>
<h2>Security</h2><p>Data is stored in a database that only our server can read; the public website can only add new
sign-ups. Connections are encrypted (HTTPS). No system is perfectly secure; if a breach affects you we will tell you and
the Data Protection Board as the law requires.</p>
<h2>Grievance Officer</h2><p>{officer} · {mail} · {c['address']}. If you are not satisfied with our answer, you may
complain to the Data Protection Board of India.</p>
<h2>Changes</h2><p>If we change this policy we update the date above; for important changes we will email subscribers.</p>"""

    terms = f"""<h1>Terms of Service</h1>{upd}
<p>These terms apply when you use {c['brand']}, a service of <b>{c['company']}</b>, {c['address']}.
By subscribing or paying you agree to them.</p>
<h2>Who can use it</h2><p>The service is for businesses and professionals. You must be 18 or older.</p>
<h2>The service</h2><p>We read public notices from Indian government sources (currently DGFT notifications, public notices and
trade notices) and send short, plain-language, AI-generated summaries by email, on our Telegram channel and on this website.
Notices are published irregularly, so the number of alerts you receive varies.</p>
<h2>Not legal or professional advice</h2><p>Summaries are for information only and can contain errors or omissions. Always
read the official notice (linked on every alert) and consult a qualified professional before acting. We are not liable for
decisions made on the basis of our summaries.</p>
<h2>Plans and prices</h2><ul>
<li>The free plan costs nothing.</li>
<li>Paid plans are paid in advance for a month or a year at the price shown on the website when you pay. The price shown is
the full price; we add no hidden charges.{(' Our GSTIN is ' + c['gstin'] + '.') if c['gstin'] else ' We are not currently registered for GST, so no GST is added.'}</li>
<li>Plans do not renew automatically. We email you before your plan ends; if you don't renew, you move to the free plan.</li>
<li>Free trials, when offered, end on the date we tell you and never turn into a paid plan without your payment.</li>
<li>Cancellations and refunds: see the <a href="refund.html">Refund Policy</a>.</li></ul>
<h2>Acceptable use</h2><p>Don't resell or republish our alerts in bulk, scrape the site, or try to break or overload the
service. We may suspend accounts that do.</p>
<h2>Availability</h2><p>We aim to check sources every day but cannot guarantee uninterrupted service; government websites can
be unavailable or change without notice.</p>
<h2>Liability</h2><p>To the extent the law allows, our total liability is limited to the fees you paid us in the 3 months
before the claim.</p>
<h2>Changes</h2><p>We may update these terms; the date above shows the latest version. We will email paid subscribers about
important changes.</p>
<h2>Law and disputes</h2><p>These terms are governed by the laws of India; courts at {c['city']} have jurisdiction.
Questions or complaints: {mail} ({officer}).</p>"""

    refund = f"""<h1>Cancellation &amp; Refund Policy</h1>{upd}
<ul><li><b>Cancel anytime:</b> email {mail} or reply to any alert email. Your plan stays active until the end of the period
you paid for. Plans do not renew automatically, so you will never be charged again without paying yourself.</li>
<li><b>7-day refund:</b> if you are not happy, ask within 7 days of your first payment for a full refund. No questions asked.</li>
<li>After 7 days, payments for the current period are not refundable.</li>
<li>Duplicate payments, or payments charged but failed, are always refunded in full.</li>
<li>Approved refunds go back to the original payment method within 5–7 working days (timing then depends on your bank).</li></ul>
<p>This is a digital service; nothing is shipped.</p>"""

    cookies = f"""<h1>Cookie Policy</h1>{upd}
<p><b>This website does not use cookies</b>, local storage for tracking, analytics, advertising pixels or any third-party
tracking scripts. Fonts and images are served from our own site. That is why there is no cookie banner: there is nothing
to accept or refuse.</p>
<p>When you submit a form (alert sign-up, pilot interest, data request), the information goes directly to our database over
an encrypted connection; no cookie is set.</p>
<p>Links to other sites (Razorpay for payments, Telegram, Google Calendar, government websites) take you to services with
their own cookie and privacy policies.</p>
<p>If we ever add analytics or other cookies, we will update this page first and ask for your consent where the law
requires it. Questions: {mail}.</p>"""

    lines = [f"<p><b>Business:</b> {c['company']}{(' (proprietor: ' + c['owner'] + ')') if c['owner'] else ''}</p>",
             f"<p><b>Address:</b> {c['address']}</p>", f"<p><b>Email:</b> {mail}</p>"]
    if c["phone"]:
        lines.append(f"<p><b>Phone:</b> {c['phone']}</p>")
    if c["gstin"]:
        lines.append(f"<p><b>GSTIN:</b> {c['gstin']}</p>")
    contact = f"""<h1>Contact us</h1><p>{c['brand']} is a service of <b>{c['company']}</b>.</p>{''.join(lines)}
<p><b>Grievance Officer:</b> {officer}, {mail}. We acknowledge complaints within 48 hours and resolve them within 30 days.</p>
<p>We reply within 1–2 working days. For billing, include the email you subscribed with.</p>"""

    sb = json.dumps({"url": os.getenv("SUPABASE_URL", ""), "key": os.getenv("SUPABASE_ANON_KEY", "")})
    your_data = f"""<h1>Your data</h1>
<p>Subscribers can delete everything we hold about them at once with the <b>Delete my data</b> link at the bottom of any
alert email, or stop emails with <b>Unsubscribe</b>.</p>
<p>For anything else (see what we hold, correct it, delete pilot or outreach data, withdraw consent), send a request below or
write to {mail}. We reply within 7 days and finish within 30 days. We may ask you to confirm from the same email address.</p>
<form id="dr" autocomplete="on"><label class="l" for="dr-email">Your email</label>
<input id="dr-email" name="email" type="email" required maxlength="254">
<label class="l" for="dr-type">What do you want us to do?</label>
<select id="dr-type" name="kind" required><option value="delete">Delete my data</option><option value="access">Show me my data</option>
<option value="correct">Correct my data</option><option value="withdraw">Stop all contact (withdraw consent)</option></select>
<label class="l" for="dr-det">Details <span class="m">(optional)</span></label><textarea id="dr-det" name="details" rows="3" maxlength="1000"></textarea>
<div class="hp" aria-hidden="true"><label for="dr-web">Leave empty</label><input id="dr-web" name="website" tabindex="-1" autocomplete="off"></div>
<button class="btn">Send request</button><div id="drm" class="m" role="status" aria-live="polite"></div></form>
<script>const DR={sb};document.getElementById('dr').onsubmit=async ev=>{{ev.preventDefault();
const d=new FormData(ev.target),m=document.getElementById('drm');if(d.get('website')){{m.textContent='Thank you.';return;}}
m.textContent='Sending…';try{{const r=await fetch(DR.url+'/rest/v1/data_requests',{{method:'POST',headers:{{apikey:DR.key,
Authorization:'Bearer '+DR.key,'Content-Type':'application/json',Prefer:'return=minimal'}},body:JSON.stringify({{
email:(d.get('email')||'').trim().toLowerCase(),kind:d.get('kind'),details:(d.get('details')||'').slice(0,1000)||null}})}});
m.textContent=r.ok?'Request received. We will reply to this email within 7 days.':'Something went wrong. Please email {c['email']}.';
if(r.ok)ev.target.reset();}}catch(_){{m.textContent='Network error. Please email {c['email']}.'}}}};</script>"""

    return {"privacy.html": ("Privacy Policy", privacy), "terms.html": ("Terms of Service", terms),
            "refund.html": ("Cancellation & Refund Policy", refund), "cookies.html": ("Cookie Policy", cookies),
            "contact.html": ("Contact", contact), "your-data.html": ("Your data", your_data)}
