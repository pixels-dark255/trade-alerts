"""Thin Supabase (PostgREST) client using the service-role key — server side only."""
from __future__ import annotations

import os

import httpx


class DB:
    def __init__(self, url: str | None = None, key: str | None = None):
        url = (url or os.environ["SUPABASE_URL"]).strip()
        key = (key or os.environ["SUPABASE_SERVICE_KEY"]).strip()  # pasted secrets often end in a newline
        self.c = httpx.Client(base_url=f"{url.rstrip('/')}/rest/v1", timeout=30, headers={
            "apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        })

    def existing_ids(self, ids: list[str]) -> set[str]:
        if not ids:
            return set()
        r = self.c.get("/notices", params={"select": "id", "id": f"in.({','.join(ids)})"})
        r.raise_for_status()
        return {row["id"] for row in r.json()}

    def insert_notice(self, n: dict) -> None:
        r = self.c.post("/notices", json=n, headers={"Prefer": "resolution=ignore-duplicates"})
        r.raise_for_status()

    def notices_since(self, iso_ts: str) -> list[dict]:
        r = self.c.get("/notices", params={"select": "*", "created_at": f"gte.{iso_ts}",
                                            "order": "notice_date.desc"})
        r.raise_for_status()
        return r.json()

    def all_notices(self, limit: int = 1000) -> list[dict]:
        r = self.c.get("/notices", params={"select": "*", "order": "notice_date.desc.nullslast",
                                            "limit": limit})
        r.raise_for_status()
        return r.json()

    def mark_posted(self, ids: list[str]) -> None:
        if ids:
            self.c.patch("/notices", params={"id": f"in.({','.join(ids)})"},
                         json={"posted_telegram": True}).raise_for_status()

    def active_subscribers(self) -> list[dict]:
        r = self.c.get("/subscribers", params={"select": "*", "status": "eq.active"})
        r.raise_for_status()
        return r.json()

    def log_delivery(self, subscriber_id: str, notice_ids: list[str]) -> None:
        self.c.post("/deliveries", json={"subscriber_id": subscriber_id,
                                         "notice_ids": notice_ids}).raise_for_status()
