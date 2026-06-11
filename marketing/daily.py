#!/usr/bin/env python3
"""
ScanDesk Marketing Scheduler
Daily notification to Telegram with the day's marketing task.

Usage:
    TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_chat_id" python3 daily.py
"""

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

MARKETING_DIR = Path(__file__).parent.resolve()
LOG_FILE = MARKETING_DIR / "campaigns.jsonl"
CONFIG_FILE = MARKETING_DIR / "agent_config.json"

# Telegram config from environment
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

DAILY_TASKS = [
    ("x_showcase", "default", "X/Twitter: Showcase post about ScanDesk"),
    ("reddit_linux", "default", "Reddit r/linux: Share ScanDesk with the Linux community"),
    ("x_feature", "scan", "X/Twitter: Feature highlight (scanning capability)"),
    ("hackernews", "default", "Hacker News: Post Show HN thread"),
    ("reddit_selfhosted", "default", "Reddit r/selfhosted: Target self-hosted community"),
    ("linkedin", "default", "LinkedIn: Professional post about ScanDesk launch"),
    ("x_pain", "default", "X/Twitter: Pain-point post about Linux scanning frustrations"),
]

def get_day_of_week():
    return datetime.now(timezone.utc).weekday()

def get_todays_task():
    day = get_day_of_week()
    return DAILY_TASKS[day % len(DAILY_TASKS)]

def generate_daily_briefing():
    platform, variant, description = get_todays_task()
    
    sys.path.insert(0, str(MARKETING_DIR))
    from agent import CampaignManager
    
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            config = json.load(f)
    else:
        config = {
            "product_name": "ScanDesk",
            "tagline": "The scanner app Linux was missing.",
            "landing_page": "https://mrmoe28.github.io/scandesk/",
            "github_repo": "https://github.com/mrmoe28/scandesk",
            "buy_link": "https://square.link/u/UHhHKwVw",
            "price": "$25",
            "author": "Edward",
            "author_handle": "@mrmoe28",
            "company": "EKO Solar LLC",
            "email": "support@ekosolarllc.com",
            "hashtags": ["#Linux", "#Scanner", "#OpenSource", "#DesktopApp", "#SANE", "#LinuxApps", "#Productivity", "#PDFTools"],
        }
    
    manager = CampaignManager(config)
    campaign = manager.create_campaign(platform, variant)
    
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    msg = f"""[DATE] {date_str}
[JOB] ScanDesk Marketing — Day {get_day_of_week() + 1}/7
[TASK] {description}
[ID] {campaign.id}

--- COPY-READY CONTENT ---

{campaign.body}

--- END CONTENT ---

[LINK] Landing: {config['landing_page']}
[LINK] Buy:    {config['buy_link']}
[LINK] GitHub: {config['github_repo']}

[INSTRUCTION]
1. Copy the content above
2. Post to the platform
3. Reply to this message with the post URL
4. I'll mark it as done in the campaign log

[HASHTAGS] {campaign.hashtags}
"""
    return msg

def send_telegram(message: str):
    import urllib.request
    import urllib.parse
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[WARN] Telegram credentials not set. Skipping notification.")
        print("       Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": "false"
    }).encode()
    
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            if result.get("ok"):
                print(f"[OK] Message sent to Telegram (message_id: {result['result']['message_id']})")
                return True
            else:
                print(f"[ERROR] Telegram API: {result}")
                return False
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram: {e}")
        return False

def main():
    print("ScanDesk Daily Marketing Briefing")
    print("=" * 50)
    
    msg = generate_daily_briefing()
    print(msg)
    print("=" * 50)
    
    send_telegram(msg)
    
    daily_file = MARKETING_DIR / f"daily_{datetime.now(timezone.utc).strftime('%Y%m%d')}.txt"
    with open(daily_file, "w") as f:
        f.write(msg)
    print(f"[OK] Saved to {daily_file}")

if __name__ == "__main__":
    main()
