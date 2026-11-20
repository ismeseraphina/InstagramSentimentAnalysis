import json
import time
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
from .core import normalize_username

class CollectionError(RuntimeError):
    pass

_RESERVED = {"accounts", "explore", "reels", "reel", "p", "direct", "stories", "about", "legal", "privacy", "terms", "developer", "challenge"}


def username_from_href(href):
    if not isinstance(href, str):
        return None
    try:
        parsed = urlparse(href)
        if parsed.scheme != "https" or parsed.hostname not in {"instagram.com", "www.instagram.com"} or parsed.username or parsed.password:
            return None
        parts = parsed.path.strip("/").split("/")
        if len(parts) != 1 or parts[0].lower() in _RESERVED:
            return None
        return normalize_username(parts[0]) if not parts[0].startswith("@") else None
    except ValueError:
        return None


def _dialog(driver):
    elements = [e for e in driver.find_elements("css selector", '[role="dialog"]') if e.is_displayed()]
    return elements[-1] if elements else False
