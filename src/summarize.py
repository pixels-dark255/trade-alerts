"""Agent 2 — Analyst: turns a raw notice into a plain-language, tagged alert."""
from __future__ import annotations

import base64
import json
import os
import re

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

PROMPT = """You are an Indian EXIM compliance analyst writing for small exporters/importers.
Read this {authority} {kind} and return ONLY a JSON object with these keys:
- "headline": max 12 words, plain English, what changed
- "summary": 2-3 short sentences, no jargon
- "who_is_affected": one sentence (products, HS chapters, importers/exporters)
- "action_required": one concrete sentence, or "No action needed"
- "deadline": "YYYY-MM-DD" if an effective/compliance date is stated, else null
- "hs_codes": list of HS codes/chapters mentioned, digits only (e.g. ["39","392310"]), [] if none
- "sectors": subset of {sectors}
- "impact": "high" (new ban/restriction/duty/deadline), "medium" (procedure change, allocation), or "low" (corrigendum, info)
- "headline_hi": the headline in simple Hindi
Never invent facts not in the text. If the text is only a title, say so in the summary.

Number: {number}
Date: {notice_date}
Title: {title}
Text:
{text}"""


def _extract_json(raw: str) -> dict:
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError("no JSON in model output")
    return json.loads(m.group(0))


def normalise(data: dict, sectors: list[str]) -> dict:
    data["hs_codes"] = [re.sub(r"\D", "", str(h)) for h in data.get("hs_codes") or []]
    data["hs_codes"] = [h for h in data["hs_codes"] if 2 <= len(h) <= 8]
    data["sectors"] = [s for s in data.get("sectors") or [] if s in sectors]
    if data.get("impact") not in {"high", "medium", "low"}:
        data["impact"] = "medium"
    return data


def summarize(notice: dict, sectors: list[str], client=None, pdf: bytes | None = None) -> dict:
    if client is None:
        import anthropic
        client = anthropic.Anthropic()
    text = notice.get("raw_text") or ""
    if pdf and len(text) < 300:
        text = "(see the attached official PDF)"
    elif not text:
        text = "(PDF text unavailable)"
    content = [{"type": "text", "text": PROMPT.format(
        sectors=json.dumps(sectors), text=text,
        **{k: notice.get(k) or "" for k in ("authority", "kind", "number", "notice_date", "title")},
    )}]
    if pdf and len(notice.get("raw_text") or "") < 300:
        content.insert(0, {"type": "document", "source": {
            "type": "base64", "media_type": "application/pdf",
            "data": base64.standard_b64encode(pdf).decode()}})
    msg = client.messages.create(model=MODEL, max_tokens=700,
                                 messages=[{"role": "user", "content": content}])
    return normalise(_extract_json(msg.content[0].text), sectors)
