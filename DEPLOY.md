# Server Deployment Notes (for Kiro)

## What this service does
Monitors Blocket for free listings every 2 minutes and posts them to a Telegram group with topic-based categorization. No AI needed.

---

## Deploy on server

### 1. Clone repo
```bash
git clone git@github.com:OfficialBabyboidaniel/blocket_bortsk-nkes_messenger.git
cd blocket_bortsk-nkes_messenger
```

### 2. Create .env
```bash
cp .env.example .env
nano .env
```

Set these values (get the real values from the owner):
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 3. Build
```bash
docker compose build
```

### 4. Test run once
```bash
docker compose run --rm blocket-monitor
```
Should see logs like `[möbler] kw=soffa | ...` and `✅ Done.`

### 5. Add cron job (runs every 2 min)
```bash
crontab -e
```
Add:
```
*/2 * * * * cd /path/to/blocket_bortsk-nkes_messenger && docker compose run --rm blocket-monitor >> /var/log/blocket-monitor.log 2>&1
```

---

## Files
| File | Purpose |
|------|---------|
| `blocket_monitor.py` | Main script |
| `Dockerfile` | Builds image (python:3.12-slim + httpx) |
| `docker-compose.yml` | Runs container, mounts ./data volume |
| `.env` | Your secrets (not in git) |
| `data/blocket_seen.json` | Tracks seen listings (auto-created) |
| `data/blocket_classify.log` | Classification log (auto-created) |

---

## Customization

- **Change areas**: edit `ALLOWED_AREAS` in `blocket_monitor.py`
- **Change Telegram topics**: edit `TOPICS` dict — keys are category names, values are thread IDs
- **Add keywords**: edit `KEYWORD_TOPIC` dict — items without keyword match go to `blandat` (thread 118)
- **Change searches**: edit `SEARCHES` list — adjust `query`, `max_price`, `filter_area`
