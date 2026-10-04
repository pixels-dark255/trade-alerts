"""Day-1 check: can we read each source? No keys needed. Run: python check_sources.py"""
from pathlib import Path

import yaml

import scrape

cfg = yaml.safe_load(Path(__file__).resolve().parents[1].joinpath("config/sources.yaml").read_text(encoding="utf-8"))
for src in cfg["sources"]:
    try:
        rows = scrape.scrape_source(src)
        print(f"OK   {src['id']}: {len(rows)} rows")
        for r in rows[:3]:
            print(f"     {r['notice_date']} {r['number']:<12} {r['title'][:70]}  pdf={'yes' if r['url'] else 'no'}")
        if rows and rows[0]["url"]:
            pdf = scrape.fetch_pdf(rows[0]["url"])
            txt = scrape.pdf_text(pdf)
            mode = "text layer" if len(txt) >= 300 else "scanned -> Claude reads the PDF"
            print(f"     first PDF: {len(pdf or b'')} bytes, {len(txt)} text chars ({mode if pdf else 'DOWNLOAD FAILED'})")
    except Exception as ex:
        print(f"FAIL {src['id']}: {ex!r}")
