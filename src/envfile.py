"""Loads KEY=value lines from trade-alerts/.env (local runs only; GitHub uses Secrets)."""
import os
from pathlib import Path


def load() -> None:
    f = Path(__file__).resolve().parents[1] / ".env"
    if not f.exists():
        return
    for line in f.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def clean() -> None:
    """Strip stray spaces/newlines from pasted secrets (GitHub Secrets keep them)."""
    for k, v in list(os.environ.items()):
        if k.startswith(("SUPABASE_", "ANTHROPIC_", "RESEND_", "TELEGRAM_", "MAIL_", "OWNER_", "SITE_", "PAY_")):
            os.environ[k] = v.strip()
