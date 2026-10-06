"""One-time, free (no AI): clears 'deadlines' that are on/before the notice date (they were effective dates).
Run on your PC: python fix_deadlines.py"""
import envfile
envfile.load()
envfile.clean()

from db import DB  # noqa: E402
from summarize import drop_past_deadline  # noqa: E402

db = DB()
fixed = 0
for n in db.all_notices():
    s = n.get("summary") or {}
    old = s.get("deadline")
    if old and drop_past_deadline(dict(s), n.get("notice_date")).get("deadline") is None:
        s["deadline"] = None
        db.c.patch("/notices", params={"id": f"eq.{n['id']}"}, json={"summary": s}).raise_for_status()
        fixed += 1
        print(f"cleared {old}  ->  {n['authority']} {n['kind']} {n.get('number')}")
print(f"Done: {fixed} deadline(s) cleared.")
