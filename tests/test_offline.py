"""Offline tests — no network, no keys. Run: pytest -q"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import digest  # noqa: E402
import scrape  # noqa: E402
import sitegen  # noqa: E402
import summarize  # noqa: E402

SRC = {"id": "dgft_notification", "authority": "DGFT", "kind": "Notification",
       "type": "html_table", "url": "https://www.dgft.gov.in/CP/?opt=notification"}
HTML = """<table><tr><th>Sl.No.</th><th>Number</th><th>Year</th><th>Description</th><th>Date</th><th>Attachment</th></tr>
<tr><td>1</td><td>22/2025-26</td><td>2025-26</td><td>Continuation of Imposition of Quantitative Restriction on import of Low Ash Metallurgical Coke under Chapter 27 of ITC (HS) 2022</td><td>30/06/2025</td><td><a href="/CP/download/abc.pdf">Download</a></td></tr>
<tr><td>2</td><td>23/2025-26</td><td>2025-26</td><td>Extension in Minimum Import Price (MIP) Condition on Soda Ash covered under Chapter 28</td><td>30/06/2025</td><td><a href="javascript:void(0)" onclick="openPdf('/files/xyz.pdf')">Download</a></td></tr>
</table>"""
SECTORS = ["Chemicals & Pharma", "Energy & Minerals", "Services & Procedures (all exporters)"]


def test_parse_table():
    rows = scrape.parse_table_page(HTML, SRC)
    assert len(rows) == 2
    assert rows[0]["number"] == "22/2025-26" and rows[0]["notice_date"] == "2025-06-30"
    assert rows[0]["url"] == "https://www.dgft.gov.in/CP/download/abc.pdf"
    assert rows[1]["url"] == "https://www.dgft.gov.in/files/xyz.pdf"
    assert rows[0]["id"] != rows[1]["id"]
    assert scrape.parse_table_page(HTML, SRC)[0]["id"] == rows[0]["id"]  # stable ids


class FakeClient:
    class messages:
        @staticmethod
        def create(**kw):
            out = {"headline": "Coke import limits continue", "summary": "Import caps stay.",
                   "who_is_affected": "Importers of met coke", "action_required": "Check quota",
                   "deadline": "2025-12-31", "hs_codes": ["27", "2704.00"], "impact": "high",
                   "sectors": ["Energy & Minerals", "Made up"], "headline_hi": "कोक आयात सीमा जारी"}
            return type("M", (), {"content": [type("C", (), {"text": "Here:\n" + json.dumps(out)})]})


def _notice():
    n = scrape.parse_table_page(HTML, SRC)[0]
    s = summarize.summarize(n, SECTORS, client=FakeClient())
    n.update(summary=s, impact=s["impact"], hs_codes=s["hs_codes"], sectors=s["sectors"],
             created_at="2025-06-30T10:00:00")
    return n


def test_summarize_normalises():
    n = _notice()
    assert n["hs_codes"] == ["27", "270400"]
    assert n["sectors"] == ["Energy & Minerals"]


def test_matching():
    n = _notice()
    assert digest.matches(n, {"hs_prefixes": ["2704"], "sectors": []})
    assert digest.matches(n, {"hs_prefixes": [], "sectors": ["Energy & Minerals"]})
    assert not digest.matches(n, {"hs_prefixes": ["39"], "sectors": ["Chemicals & Pharma"]})
    assert digest.matches(n, {"hs_prefixes": [], "sectors": []})


def test_email_and_site(tmp_path):
    n = _notice()
    subj, body = digest.render_email({"unsubscribe_token": "t0k"}, [n], weekly=True)
    assert "Coke import limits continue" in subj and "Unsubscribe" in body and "Upgrade" in body
    assert "<b>" in digest.telegram_text(n)
    assert sitegen.build([n], SECTORS, out=str(tmp_path)) == 1
    assert (tmp_path / "n" / f"{n['id']}.html").exists()
    assert "subscribers" in (tmp_path / "index.html").read_text()
