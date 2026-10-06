"""Quality check: an independent AI auditor re-reads 10 random official PDFs and checks
each published summary against them. You only review the flagged ones.

Run on your PC (DGFT is reachable from India):  python qa.py   [or double-click run_qa.bat]
Output: qa_report.html in the project folder (opens in your browser).
"""
from __future__ import annotations

import base64
import html
import json
import os
import random
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

import envfile
envfile.load()
envfile.clean()

import scrape  # noqa: E402
from db import DB  # noqa: E402

QA_MODEL = os.getenv("QA_MODEL", "")   # blank = pick the strongest model your API key can use
SAMPLE = int(os.getenv("QA_SAMPLE", "10"))
OUT = Path(__file__).resolve().parents[1] / "qa_report.html"
e = html.escape

AUDIT_PROMPT = """You are auditing an AI-written summary of an Indian government trade notice.
Compare the SUMMARY below with the attached OFFICIAL DOCUMENT (or text). Check each field strictly against the document.

Return ONLY JSON:
{{"verdict": "ok" | "minor" | "wrong",
  "issues": [{{"field": "headline|summary|who_is_affected|action_required|deadline|hs_codes|impact|headline_hi",
               "problem": "what is wrong, one sentence",
               "correct": "what the document actually says, short"}}],
  "note": "one sentence overall"}}
- "wrong" = any factual error a reader could act on (wrong date, item, HS code, amount, direction of change, invented fact).
- "minor" = vague, incomplete or slightly off wording, but nothing misleading.
- "ok" = accurate. Empty issues list.
Do not flag style. If the document is unreadable, verdict "minor" and say so in note.

Notice: {authority} {kind} {number} dated {notice_date}
Title: {title}
SUMMARY:
{summary}
{text_block}"""


def pick_model(client) -> str:
    """Use QA_MODEL if set, else the best available Opus/Sonnet on this account, else the summariser's model."""
    if QA_MODEL:
        return QA_MODEL
    try:
        ids = [m.id for m in client.models.list(limit=100)]
    except Exception:
        ids = []
    for family in ("opus", "sonnet"):
        cands = [i for i in ids if family in i]
        if cands:
            return cands[0]          # the API lists newest first
    return os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")


def audit(n: dict, pdf: bytes | None, client, model: str) -> dict:
    text = scrape.pdf_text(pdf) if pdf else ""
    use_pdf = pdf is not None and len(text) < 300
    prompt = AUDIT_PROMPT.format(
        summary=json.dumps(n.get("summary") or {}, ensure_ascii=False, indent=1),
        text_block="" if use_pdf else f"OFFICIAL TEXT:\n{text or '(document unavailable)'}",
        **{k: n.get(k) or "" for k in ("authority", "kind", "number", "notice_date", "title")})
    content = [{"type": "text", "text": prompt}]
    if use_pdf:
        content.insert(0, {"type": "document", "source": {"type": "base64", "media_type": "application/pdf",
                                                         "data": base64.standard_b64encode(pdf).decode()}})
    msg = client.messages.create(model=model, max_tokens=1200, messages=[{"role": "user", "content": content}])
    m = re.search(r"\{.*\}", msg.content[0].text, re.S)
    res = json.loads(m.group(0)) if m else {"verdict": "minor", "issues": [], "note": "auditor gave no JSON"}
    if res.get("verdict") not in ("ok", "minor", "wrong"):
        res["verdict"] = "minor"
    return res


def render(rows: list[tuple[dict, dict]], model: str = "") -> str:
    colour = {"ok": "#1e8e3e", "minor": "#d68910", "wrong": "#c0392b", "error": "#7f8c8d"}
    order = {"wrong": 0, "minor": 1, "ok": 2, "error": 3}
    rows = sorted(rows, key=lambda r: order[r[1]["verdict"]])
    counts = {k: sum(1 for _, a in rows if a["verdict"] == k) for k in order}
    cards = []
    for n, a in rows:
        s = n.get("summary") or {}
        issues = "".join(f"<li><b>{e(i.get('field',''))}</b>: {e(i.get('problem',''))}"
                         f"<br><span style='color:#555'>Document says: {e(i.get('correct',''))}</span></li>"
                         for i in a.get("issues") or [])
        cards.append(f"""<div style="border:1px solid #ddd;border-left:6px solid {colour[a['verdict']]};border-radius:6px;padding:12px;margin:12px 0;background:#fff">
<b style="color:{colour[a['verdict']]}">{a['verdict'].upper()}</b> · {e(n['authority'])} {e(n['kind'])} {e(n.get('number') or '')} · {e(n.get('notice_date') or '')}
<div style="font-size:17px;font-weight:600;margin:6px 0">{e(s.get('headline') or n['title'])}</div>
<div>{e(s.get('summary') or '')}</div>
<div style="margin-top:4px"><b>Action:</b> {e(s.get('action_required') or '')} · <b>Deadline:</b> {e(str(s.get('deadline')))} · <b>HS:</b> {e(', '.join(n.get('hs_codes') or []))} · <b>Impact:</b> {e(n.get('impact') or '')}</div>
{'<ul>' + issues + '</ul>' if issues else ''}
<div style="color:#555;margin-top:4px">{e(a.get('note') or '')}</div>
<div style="margin-top:6px"><a href="{e(n.get('url') or '#')}">Official PDF</a> · id <code>{e(n['id'])}</code></div></div>""")
    return f"""<!doctype html><meta charset="utf-8"><title>Sagarlekh QA {datetime.now():%d %b %Y}</title>
<body style="font-family:system-ui,Arial;max-width:900px;margin:auto;padding:16px;background:#f6f7f9;color:#1d2433">
<h1>Summary quality check</h1><p>{len(rows)} random alerts audited by {e(model)} on {datetime.now():%d %b %Y %H:%M}.
<b style="color:#c0392b">{counts['wrong']} wrong</b> · <b style="color:#d68910">{counts['minor']} minor</b> · <b style="color:#1e8e3e">{counts['ok']} ok</b> · <b style="color:#7f8c8d">{counts['error']} not checked</b>.</p>
<p>Review the <b>wrong</b> ones against the PDF. If the auditor is right, delete that row in Supabase (table <code>notices</code>, by id) — it is re-summarised on the next collect run.</p>
{''.join(cards)}</body>"""


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    import anthropic
    client = anthropic.Anthropic()
    model = pick_model(client)
    print(f"Auditor model: {model}")
    notices = [n for n in DB().all_notices() if n.get("summary") and n.get("url")]
    sample = random.sample(notices, min(SAMPLE, len(notices)))
    rows = []
    for i, n in enumerate(sample, 1):
        print(f"[{i}/{len(sample)}] {n['authority']} {n['kind']} {n.get('number')} ...", flush=True)
        try:
            a = audit(n, scrape.fetch_pdf(n["url"]), client, model)
        except Exception as ex:
            a = {"verdict": "error", "issues": [], "note": f"audit failed: {ex!r}"}
        rows.append((n, a))
    OUT.write_text(render(rows, model), encoding="utf-8")
    bad = sum(1 for _, a in rows if a["verdict"] == "wrong")
    print(f"\nDone: {bad} wrong out of {len(rows)}. Report: {OUT}")
    try:
        webbrowser.open(OUT.as_uri())
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
