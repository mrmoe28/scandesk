#!/usr/bin/env python3
"""
ScanDesk Postmark Tool
Mark a campaign as posted after the user shares the URL.

Usage:
    python3 postmark.py CAMPAIGN_ID [POST_URL]
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

MARKETING_DIR = Path(__file__).parent.resolve()
LOG_FILE = MARKETING_DIR / "campaigns.jsonl"

def mark_posted(campaign_id: str, url: str = None):
    campaigns = []
    updated = False
    
    if not LOG_FILE.exists():
        print(f"[ERROR] No campaigns found at {LOG_FILE}")
        return False
    
    with open(LOG_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            if data["id"] == campaign_id:
                data["status"] = "posted"
                data["posted_at"] = datetime.now(timezone.utc).isoformat()
                if url:
                    data["url"] = url
                updated = True
            campaigns.append(data)
    
    if updated:
        with open(LOG_FILE, "w") as f:
            for c in campaigns:
                f.write(json.dumps(c) + "\n")
        print(f"[OK] Marked {campaign_id} as posted")
        if url:
            print(f"     URL: {url}")
        return True
    else:
        print(f"[ERROR] Campaign {campaign_id} not found")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 postmark.py CAMPAIGN_ID [POST_URL]")
        print("\nExample:")
        print("  python3 postmark.py x_showcase_20260611_143303_689 https://x.com/mrmoe28/status/123")
        sys.exit(1)
    
    campaign_id = sys.argv[1]
    url = sys.argv[2] if len(sys.argv) > 2 else None
    
    mark_posted(campaign_id, url)

if __name__ == "__main__":
    main()
