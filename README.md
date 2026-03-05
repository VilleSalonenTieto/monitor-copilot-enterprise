# monitor-copilot-enterprise

Polls the GitHub Copilot settings page at a regular interval and reports whether your Copilot seat is managed by an Enterprise organisation. Useful for monitoring that Copilot Enterprise assignment is active and has not unexpectedly changed.

## Setup

### 1. Install dependencies

```sh
uv sync
```

### 2. Configure credentials

Copy `.env.example` to `.env` and fill in the cookie value:

```sh
cp .env.example .env
```

`.env.example`:

```
# Paste the full value of the Cookie: header from a browser request to github.com/settings/copilot/features
GITHUB_COOKIE=_device_id=...; user_session=...; _gh_sess=...
```

To get the cookie value:

1. Open Chrome or Edge and navigate to `https://github.com/settings/copilot/features` while logged in.
2. Open DevTools (F12) → **Network** tab.
3. Reload the page and click the `features` request.
4. In the **Headers** panel, find the `Cookie:` request header.
5. Copy the entire value and paste it as `GITHUB_COOKIE` in your `.env`.

> **Note:** The `_gh_sess` cookie is session-scoped and will expire. When the script starts reporting errors or warnings unexpectedly, refresh the cookie value in `.env`.

### 3. Run

**bash/zsh/fish:**
```sh
uv run python monitor_copilot_enterprise.py | tee $(date +%Y%m%d).log
```

**PowerShell:**
```powershell
uv run python monitor_copilot_enterprise.py | Tee-Object -FilePath "$(Get-Date -Format 'yyyyMMdd').log"
```

## Output

```
[2026-03-05 10:00:00] ✅ Copilot Enterprise managed by: my-org
[2026-03-05 10:01:00] ⚠️  Copilot Enterprise managing org unresolved
[2026-03-05 10:02:00] ❌ Error: HTTP 401 fetching settings page
```

The script polls every 60 seconds (`POLL_INTERVAL` in the script).
