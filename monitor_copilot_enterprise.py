#!/usr/bin/env python3
import os
import subprocess
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

STATE_GOOD = "good"
STATE_BAD = "bad"

# -----------------------------------------------------------------------------
# HTML Parsing
# -----------------------------------------------------------------------------


class ManagedByParser(HTMLParser):
    """
    Parses Copilot settings HTML to identify the good state:
    an org link (not the /settings/copilot placeholder) that follows
    the text "managed by" in the page.
    """

    def __init__(self) -> None:
        super().__init__()
        self._seen_managed_by = False
        self._capture_link = False
        self._link_parts: list[str] = []
        self.managed_by: str | None = None

    def handle_data(self, data: str) -> None:
        if self._capture_link:
            self._link_parts.append(data)
        elif "managed by" in data:
            self._seen_managed_by = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a" and self._seen_managed_by and not self._capture_link:
            href = dict(attrs).get("href", "")
            if href != "/settings/copilot":
                self._capture_link = True
                self._link_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._capture_link:
            link_text = "".join(self._link_parts).strip()
            if link_text:
                self.managed_by = link_text
            self._capture_link = False
            self._link_parts = []
        elif tag == "p":
            # Reset paragraph-level state so a "managed by" match in one
            # paragraph can't accidentally capture a link from a later paragraph.
            self._seen_managed_by = False
            self._capture_link = False
            self._link_parts = []


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
    return parser.managed_by


def main() -> None:
    load_dotenv()
    cookie = os.getenv("GITHUB_COOKIE")
    if not cookie:
        print("ERROR: GITHUB_COOKIE must be set in environment or .env file")
        sys.exit(2)

    previous_state: str | None = None

    try:
        while True:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_state = STATE_BAD
            try:
                html = fetch_copilot_settings(cookie)
                managed_org = find_managed_org(html)
                if managed_org:
                    current_state = STATE_GOOD
                    print(f"[{ts}] ✅ Copilot Enterprise managed by: {managed_org}", flush=True)
                else:
                    print(f"[{ts}] ❌ Copilot Enterprise in bad state", flush=True)
            except Exception as e:
                print(f"[{ts}] ❌ Error: {e}", flush=True)

            if previous_state == STATE_GOOD and current_state == STATE_BAD:
                try:
                    result = subprocess.run(
                        ["copilot", "--model", "claude-haiku-4.5", "--prompt", "Reply with Aye aye, sir if you are there."],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    probe_output = (result.stdout + result.stderr).strip()
                    print(f"[{ts}] 🔍 CLI probe output:\n{probe_output}", flush=True)
                except Exception as e:
                    print(f"[{ts}] ⚠️ CLI probe failed: {e}", flush=True)

            previous_state = current_state
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)


if __name__ == "__main__":
    main()
