"""Policy pages required by payment gateways (Razorpay) and India's DPDP Act.
Templates only — have them reviewed by a lawyer/CA when revenue starts."""
from __future__ import annotations

import html
import os
from datetime import date

e = html.escape


def _cfg() -> dict:
    return {
        "brand": (os.getenv("SITE_NAME") or "Trade Alerts India").strip(),
        "company": (os.getenv("LEGAL_NAME") or "DharaLabs").strip(),
        "email": (os.getenv("CONTACT_EMAIL") or "support@example.com").strip(),
        "phone": (os.getenv("CONTACT_PHONE") or "").strip(),
        "address": (os.getenv("BUSINESS_ADDRESS") or "").strip(),
        "city": (os.getenv("JURISDICTION") or "India").strip(),
        "updated": date.today().strftime("%d %B %Y"),
    }


def pages() -> dict[str, tuple[str, str]]:
    """Returns {filename: (title, body_html)}."""
    c = {k: e(v) for k, v in _cfg().items()}
    contact_line = f'<a href="mailto:{c["email"]}">{c["email"]}</a>'
    privacy = f"""<h1>Privacy Policy</h1><p class="m">Last updated: {c['updated']}</p>
<p>{c['brand']} is a service of <b>{c['company']}</b> ("we", "us"). This policy explains what personal data we collect and how we use it, in line with India's Digital Personal Data Protection Act, 2023.</p>
<h3>What we collect</h3><ul>
<li>Email address (required) and, if you provide them, company name, HS codes and sector.</li>
<li>The date and time you gave consent to receive alerts.</li>
<li>For paid plans: payment status and plan. Card/UPI/bank details are handled entirely by our payment partner (Razorpay); we never see or store them.</li></ul>
<h3>Why we use it</h3><ul><li>To send you the alerts and digests you signed up for, filtered to your HS codes/sector.</li>
<li>To manage your subscription and respond to your messages.</li></ul>
<p>We do not sell or rent your data, and we do not use it for advertising.</p>
<h3>Service providers</h3><p>We use trusted processors to run the service: Supabase (database), Resend (email delivery), Telegram (public channel), GitHub (website hosting) and Razorpay (payments). Our AI summarisation (Anthropic) processes only public government notices — never your personal data.</p>
<h3>Retention</h3><p>We keep your data while your subscription is active. If you unsubscribe or ask us to delete it, we erase it within 30 days, except where the law requires us to keep payment records.</p>
<h3>Your rights</h3><p>You can access, correct or erase your data, withdraw consent at any time (every email has a one-click unsubscribe link), and raise a grievance. Write to {contact_line}; we respond within 7 working days.</p>
<h3>Grievance officer</h3><p>{c['company']} — {contact_line}</p>"""

    terms = f"""<h1>Terms of Service</h1><p class="m">Last updated: {c['updated']}</p>
<p>By using {c['brand']} (a service of <b>{c['company']}</b>) you agree to these terms.</p>
<h3>The service</h3><p>We monitor public notices from Indian government sources (such as DGFT) and send plain-language, AI-generated summaries by email, Telegram and on this website.</p>
<h3>Not legal or professional advice</h3><p>Summaries are for information only and may contain errors or omissions. Always read the official notice and consult a qualified professional (CA, customs broker or lawyer) before acting. We are not liable for decisions made on the basis of our summaries.</p>
<h3>Accounts and plans</h3><ul><li>Free plan: weekly digest, at no cost.</li>
<li>Paid plans (Pro, Firm) are billed in advance, monthly or yearly, at the price shown on the website at the time of purchase.</li>
<li>You may cancel any time; access continues until the end of the paid period. See our <a href="refund.html">Refund Policy</a>.</li></ul>
<h3>Acceptable use</h3><p>Do not resell, republish in bulk or scrape our alerts, or misuse the service. We may suspend accounts that do.</p>
<h3>Availability</h3><p>We aim for daily delivery but do not guarantee uninterrupted service; government websites may be unavailable or change without notice.</p>
<h3>Liability</h3><p>To the extent permitted by law, our total liability is limited to the fees you paid us in the 3 months before the claim.</p>
<h3>Changes</h3><p>We may update these terms; the date above shows the latest version. Continued use means you accept the changes.</p>
<h3>Governing law</h3><p>These terms are governed by the laws of India; courts at {c['city']} have jurisdiction.</p>
<p>Questions: {contact_line}</p>"""

    refund = f"""<h1>Cancellation &amp; Refund Policy</h1><p class="m">Last updated: {c['updated']}</p>
<ul><li><b>Cancel anytime:</b> email {contact_line} or reply to any alert email. Your plan stays active until the end of the period you paid for; you will not be charged again.</li>
<li><b>7-day guarantee:</b> if you are not satisfied with your first paid month or year, ask within 7 days of payment for a full refund.</li>
<li>After 7 days, payments for the current period are non-refundable.</li>
<li>Duplicate or failed-but-charged payments are always refunded in full.</li>
<li>Approved refunds are processed within 5–7 working days to the original payment method.</li></ul>
<p>This is a digital service; nothing is shipped.</p>"""

    extra = "".join(x for x in (f"<p><b>Phone:</b> {c['phone']}</p>" if c["phone"] else "",
                                 f"<p><b>Address:</b> {c['address']}</p>" if c["address"] else ""))
    contact = f"""<h1>Contact us</h1><p>{c['brand']} is a service of <b>{c['company']}</b>.</p>
<p><b>Email:</b> {contact_line}</p>{extra}
<p>We reply within 1–2 working days. For billing, include the email you subscribed with.</p>"""
    return {"privacy.html": ("Privacy Policy", privacy), "terms.html": ("Terms of Service", terms),
            "refund.html": ("Cancellation & Refund Policy", refund), "contact.html": ("Contact", contact)}
