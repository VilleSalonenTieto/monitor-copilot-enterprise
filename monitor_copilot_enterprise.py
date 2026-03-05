#!/usr/bin/env python3
import os
import sys
import time
import requests
from datetime import datetime
from html.parser import HTMLParser
from dotenv import load_dotenv

load_dotenv()

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
GITHUB_COOKIE = os.getenv("GITHUB_COOKIE")
if not GITHUB_COOKIE:
    print("ERROR: Set GITHUB_COOKIE as an environment variable")
    sys.exit(2)

# URL you saw in the settings page that contains your seat info
COPILOT_SETTINGS_URL = "https://github.com/settings/copilot/features"

# -----------------------------------------------------------------------------
# HTML Parsing
# -----------------------------------------------------------------------------
class ManagedByParser(HTMLParser):
    """
    Parses Copilot settings HTML for:
      managed by <a …>/OrgName</a>
    """
    def __init__(self):
        super().__init__()
        self.in_managed_link = False
        self.org_name = None

    def handle_starttag(self, tag, attrs):
        # Look for <a href="/OrgName"> inside copilot message text
        if tag == "a":
            href = dict(attrs).get("href", "")
            # Only consider relative GitHub org links (not the placeholder)
            if href.startswith("/") and "settings/copilot" not in href:
                self.in_managed_link = True

    def handle_data(self, data):
        if self.in_managed_link:
            self.org_name = data.strip()

    def handle_endtag(self, tag):
        if tag == "a":
            self.in_managed_link = False


# -----------------------------------------------------------------------------
# Main Logic
# -----------------------------------------------------------------------------
def fetch_copilot_settings():
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": GITHUB_COOKIE,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
    }
    response = requests.get(COPILOT_SETTINGS_URL, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code} fetching settings page")
    return response.text

def find_managed_org(html):
    parser = ManagedByParser()
    parser.feed(html)
    return parser.org_name

POLL_INTERVAL = 60  # seconds

def main():
    while True:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            html = fetch_copilot_settings()
            managed_org = find_managed_org(html)
            if managed_org:
                print(f"[{ts}] ✅ Copilot Enterprise managed by: {managed_org}")
            else:
                print(f"[{ts}] ⚠️  Copilot Enterprise managing org unresolved")
        except Exception as e:
            print(f"[{ts}] ❌ Error: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()