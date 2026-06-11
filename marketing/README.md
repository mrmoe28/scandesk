# ScanDesk Marketing Agent

Automated marketing engine for ScanDesk Linux scanner app.

## What's Included

| File | Purpose |
|------|---------|
| `agent.py` | Core marketing engine — generates platform-specific content, manages campaigns, tracks stats |
| `daily.py` | Daily scheduler — generates copy-ready content for today's platform and sends to Telegram |
| `postmark.py` | Mark a campaign as posted after you share the URL |
| `templates.json` | Platform metadata and audience info |
| `campaigns.jsonl` | Campaign log (auto-generated) |
| `agent_config.json` | Product config (auto-generated) |

## Quick Start

### Generate content for a specific platform

```bash
cd marketing/
python3 agent.py --generate x_showcase
python3 agent.py --generate reddit_linux
python3 agent.py --generate hackernews
python3 agent.py --generate linkedin
```

### Generate a full week of campaigns

```bash
python3 agent.py --week
```

### Generate ALL platform variants

```bash
python3 agent.py --all-platforms
```

### See stats

```bash
python3 agent.py --stats
```

### List all campaigns

```bash
python3 agent.py --list
```

### Mark a campaign as posted

```bash
python3 postmark.py x_showcase_20260611_143303_689 https://x.com/mrmoe28/status/123456
```

## Supported Platforms

- **X/Twitter** — showcase, feature highlight, milestones, pain-point
- **Reddit** — r/linux, r/selfhosted, r/Ubuntu
- **Hacker News** — Show HN format
- **Product Hunt** — product launch post
- **LinkedIn** — professional announcement
- **Indie Hackers** — transparent founder story
- **Email** — direct newsletter copy
- **Blog** — full technical blog post
- **GitHub** — release notes

## Daily Workflow

1. Run `daily.py` (or cron runs it) → get Telegram notification with copy-ready content
2. Copy content and post to the platform
3. Reply with the post URL
4. Run `postmark.py` to mark it done

## Config

Edit `agent_config.json` to change:

- Landing page URL
- Buy link
- Price
- Author info
- Hashtags

## Landing Page

Your splash page is live at: **https://mrmoe28.github.io/scandesk/**

Built from `docs/index.html` + `docs/style.css` on the `main` branch.
