#!/usr/bin/env python3
import os
import sys
import time
import requests
from datetime import datetime
from html.parser import HTMLParser
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# URL you saw in the settings page that contains your seat info
COPILOT_SETTINGS_URL = "https://github.com/settings/copilot/features"

POLL_INTERVAL = 60  # seconds

REQUEST_TIMEOUT = 30  # seconds

# -----------------------------------------------------------------------------
# HTML Parsing
# -----------------------------------------------------------------------------


class ManagedByParser(HTMLParser):
    """
    Parses Copilot settings HTML for:
      managed by <a …>/OrgName</a>
    """

    def __init__(self) -> None:
        super().__init__()
        self.in_managed_link = False
        self.org_name: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # Look for <a href="/OrgName"> inside copilot message text
        if tag == "a":
            href = dict(attrs).get("href")
            # Only consider relative GitHub org links (not the placeholder)
            if href is not None and href.startswith("/") and "settings/copilot" not in href:
                self.in_managed_link = True

    def handle_data(self, data: str) -> None:
        if self.in_managed_link:
            self.org_name = data.strip()

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self.in_managed_link = False


# -----------------------------------------------------------------------------
# Main Logic
# -----------------------------------------------------------------------------


def fetch_copilot_settings(cookie: str) -> str:
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
    }
    response = requests.get(COPILOT_SETTINGS_URL, headers=headers, timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code} fetching settings page")
    return response.text


def find_managed_org(html: str) -> str | None:
    parser = ManagedByParser()
    parser.feed(html)
    return parser.org_name


def main() -> None:
    load_dotenv()
    cookie = os.getenv("GITHUB_COOKIE")
    if not cookie:
        print("ERROR: GITHUB_COOKIE must be set in environment or .env file")
        sys.exit(2)

    try:
        while True:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                html = fetch_copilot_settings(cookie)
                managed_org = find_managed_org(html)
                if managed_org:
                    print(f"[{ts}] ✅ Copilot Enterprise managed by: {managed_org}", flush=True)
                else:
                    print(f"[{ts}] ⚠️  Copilot Enterprise managing org unresolved", flush=True)
            except Exception as e:
                print(f"[{ts}] ❌ Error: {e}", flush=True)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)


if __name__ == "__main__":
    main()