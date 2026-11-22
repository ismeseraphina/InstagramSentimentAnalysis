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


_SCROLL = """
const d=arguments[0];
const nodes=[d,...d.querySelectorAll('*')].filter(e => e.clientHeight>0 &&
 e.scrollHeight>e.clientHeight+2 && ['auto','scroll'].includes(getComputedStyle(e).overflowY));
if (!nodes.length) return null;
nodes.sort((a,b)=>b.clientHeight-a.clientHeight);
const e=nodes[0]; e.scrollTop+=Math.max(1,e.clientHeight*0.65);
return {top:e.scrollTop,height:e.scrollHeight};
"""


def _read_dialog(driver, wait, *, max_scrolls, pause):
    names, stable, previous, reason = set(), 0, None, "scroll_limit"
    def harvest(dialog):
        for anchor in dialog.find_elements("css selector", 'a[href]'):
            name = username_from_href(anchor.get_attribute("href"))
            if name:
                names.add(name)
    for _ in range(max_scrolls):
        dialog = wait.until(_dialog)
        harvest(dialog)
        state = driver.execute_script(_SCROLL, dialog)
        signature = (len(names), None) if state is None else (len(names), state["top"], state["height"])
        stable = stable + 1 if signature == previous else 0
        previous = signature
        if stable >= 5:
            reason = "no_observed_progress"
            break
        time.sleep(pause)
    harvest(wait.until(_dialog))
    if not names:
        raise CollectionError("No profiles collected: empty list, wrong dialog, page changes or loading failure. Nothing saved.")
    return sorted(names), reason


def collect_live(username, output_dir, *, max_scrolls=200, pause=1.5,
                 expected_followers=None, expected_following=None, prompt=input):
    username = normalize_username(username)
    if not 1 <= max_scrolls <= 2000 or not 1.5 <= pause <= 60:
        raise ValueError("max_scrolls must be 1..2000 and pause must be 1.5..60 seconds")
    if any(c is not None and c < 0 for c in (expected_followers, expected_following)):
        raise ValueError("Expected counts cannot be negative")
    output = Path(output_dir)
    if output.exists():
        raise ValueError("Choose a NEW output directory")
    try:
        from selenium import webdriver
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.common.exceptions import WebDriverException
    except ImportError as exc:
        raise CollectionError('Install the live extra: python -m pip install -e ".[live]"') from exc
    driver = None
    try:
        driver = webdriver.Chrome()
        driver.set_page_load_timeout(45)
        wait = WebDriverWait(driver, 20)
        driver.get("https://www.instagram.com/")
        prompt("Log in yourself in Chrome and complete verification manually. Press Enter here when ready; Ctrl+C cancels: ")
        lists, details = {}, {}
        for kind, expected in (("followers", expected_followers), ("following", expected_following)):
            driver.get(f"https://www.instagram.com/{username}/")
            prompt(f"Open @{username}'s {kind} list in Chrome. Confirm the correct list, then press Enter here: ")
            print(f"Collecting {kind}; do not interact with Chrome during collection.")
            users, reason = _read_dialog(driver, wait, max_scrolls=max_scrolls, pause=pause)
            if expected is not None and len(users) != expected:
                raise CollectionError(f"{kind}: collected {len(users)}, expected {expected}. Nothing saved.")
            lists[kind] = users
            details[kind] = {"collected": len(users), "expected_count": expected,
                             "count_matches": None if expected is None else len(users) == expected,
                             "stop_reason": reason}
            print(f"Collected {len(users)} {kind}; completeness unverified.")
        if prompt("Confirm correct lists. Type SAVE to store them locally, anything else to cancel: ").strip() != "SAVE":
            raise CollectionError("Cancelled; no data saved")
        output.mkdir(parents=True, exist_ok=False)
        for kind, users in lists.items():
            with (output / f"{kind}.json").open("x", encoding="utf-8") as stream:
                json.dump(users, stream, indent=2)
        metadata = {"schema_version": 1, "username": username,
                    "captured_at_utc": datetime.now(timezone.utc).isoformat(),
                    "source": "visible_browser_best_effort", "completeness": "unverified",
                    "warning": "Counts and scroll stability do not prove completeness; review before analysis.", "lists": details}
        with (output / "metadata.json").open("x", encoding="utf-8") as stream:
            json.dump(metadata, stream, indent=2)
        return metadata
    except WebDriverException as exc:
        raise CollectionError("Browser collection failed. Check Chrome, login, access and correct list selection; no bypass is attempted.") from exc
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass

