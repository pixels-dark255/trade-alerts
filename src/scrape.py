"""Agent 1 — Watcher: pulls new notices from government listing pages."""
from __future__ import annotations

import hashlib
import io
import re
from datetime import datetime
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (TradeAlerts bot; contact via website)"}
DATE_RE = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b")
NUM_RE = re.compile(r"\b\d{1,3}\s*/\s*\d{4}(?:-\d{2,4})?\b")


def _parse_date(text: str) -> str | None:
    m = DATE_RE.search(text)
    if not m:
        return None
    d, mth, y = map(int, m.groups())
    try:
        return datetime(y, mth, d).date().isoformat()
    except ValueError:
        return None


def notice_id(source: str, number: str, date: str | None, title: str) -> str:
    key = f"{source}|{number}|{date}|{title[:120]}".lower()
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def _row_link(row, base_url: str) -> str | None:
    for a in row.find_all("a"):
        href = a.get("href") or ""
        onclick = a.get("onclick") or ""
        if href and not href.startswith(("javascript", "#")):
            return urljoin(base_url, href)
        m = re.search(r"['\"]([^'\"]+\.pdf[^'\"]*)['\"]", onclick, re.I)
        if m:
            return urljoin(base_url, m.group(1))
    return None


def parse_table_page(html: str, source: dict, limit: int = 30) -> list[dict]:
    """Generic parser: any <tr> with a date + a descriptive cell is a notice."""
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for row in soup.find_all("tr"):
        cells = [" ".join(c.get_text(" ", strip=True).split()) for c in row.find_all(["td", "th"])]
        if len(cells) < 2 or row.find("th") and not row.find("td"):
            continue
        joined = " | ".join(cells)
        date = _parse_date(joined)
        if not date:
            continue
        title = max(cells, key=len)
        if len(title) < 15:
            continue
        num_match = NUM_RE.search(joined)
        number = num_match.group(0).replace(" ", "") if num_match else ""
        out.append({
            "id": notice_id(source["id"], number, date, title),
            "source": source["id"],
            "authority": source["authority"],
            "kind": source["kind"],
            "number": number,
            "title": title,
            "notice_date": date,
            "url": _row_link(row, source["url"]),
        })
        if len(out) >= limit:
            break
    return out


def fetch(url: str, timeout: float = 45) -> httpx.Response:
    with httpx.Client(headers=UA, timeout=timeout, follow_redirects=True) as c:
        r = c.get(url)
        r.raise_for_status()
        return r


def scrape_source(source: dict) -> list[dict]:
    if source["type"] == "html_table":
        return parse_table_page(fetch(source["url"]).text, source)
    raise ValueError(f"unknown source type {source['type']}")


def fetch_pdf(url: str, max_bytes: int = 15_000_000) -> bytes | None:
    """Download a notice PDF (spaces in DGFT file names are URL-encoded)."""
    try:
        r = fetch(url.replace(" ", "%20"))
        if b"%PDF" not in r.content[:1024] or len(r.content) > max_bytes:
            return None
        return r.content
    except Exception:
        return None


def pdf_text(pdf: bytes | None, max_chars: int = 8000) -> str:
    """Text layer of the PDF. Scanned/signed PDFs return little or nothing —
    then the summariser sends the PDF itself to Claude, which can read scans."""
    if not pdf:
        return ""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf)) as doc:
            text = "\n".join((p.extract_text() or "") for p in doc.pages[:6])
        return " ".join(text.split())[:max_chars]
    except Exception:
        return ""
