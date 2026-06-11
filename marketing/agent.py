#!/usr/bin/env python3
"""
ScanDesk Marketing Agent
Automated marketing engine for ScanDesk Linux scanner app.
Generates platform-specific posts, manages campaigns, and logs results.
"""

import json
import random
import sys
import os
import argparse
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional

# ── Paths ──────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent.resolve()
MARKETING_DIR = Path(__file__).parent.resolve()
LOG_FILE = MARKETING_DIR / "campaigns.jsonl"
CONFIG_FILE = MARKETING_DIR / "agent_config.json"
TEMPLATES_FILE = MARKETING_DIR / "templates.json"

# ── Configuration ──────────────────────────────────────────────────────
DEFAULT_CONFIG = {
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

# ── Data Classes ───────────────────────────────────────────────────────
@dataclass
class Campaign:
    id: str
    platform: str
    title: str
    body: str
    hashtags: str
    created_at: str
    posted_at: Optional[str] = None
    status: str = "draft"
    url: Optional[str] = None
    engagement: Optional[dict] = None

# ── Template Engine ────────────────────────────────────────────────────
class TemplateEngine:
    """Generates platform-optimized marketing copy."""

    def __init__(self, config: dict):
        self.config = config
        self.product = config["product_name"]
        self.tagline = config["tagline"]
        self.landing = config["landing_page"]
        self.repo = config["github_repo"]
        self.buy = config["buy_link"]
        self.price = config["price"]
        self.author = config["author"]

    def _pick(self, items: list, n: int = 3) -> list:
        return random.sample(items, min(n, len(items)))

    # ── X/Twitter ──────────────────────────────────────────────────────
    def x_showcase(self) -> str:
        hooks = [
            f"I built {self.product} because scanning on Linux shouldn't require 3 terminals and a prayer.",
            f"Tired of fighting your scanner on Linux? I made {self.product}.",
            f"Linux finally has a scanner app that just works. Introducing {self.product}.",
        ]
        return random.choice(hooks) + f"\n\n{self.tagline}\n\n{self.landing}"

    def x_feature(self, feature: str) -> str:
        features = {
            "scan": f"One click. Any SANE scanner. PDF or PNG. {self.product} makes scanning on Linux actually enjoyable.",
            "email": f"Scan → hit Email → Gmail opens with your PDF attached. No exporting, no dragging. {self.product}",
            "dark_mode": f"Dark mode that respects your retinas. {self.product} matches your system theme automatically.",
            "session": f"Every scan gets a dated folder. Organized by default. {self.product}",
        }
        return features.get(feature, features["scan"]) + f"\n\n{self.landing}"

    def x_milestones(self) -> str:
        return (
            f"{self.product} milestones:\n"
            f"  - 0 stars, 0 forks, 0 issues\n"
            f"  - But it scans, emails, and looks clean\n"
            f"  - MIT licensed, $25 if you want to support\n"
            f"  - Built by one person with a scanner and a dream\n\n"
            f"{self.repo}"
        )

    def x_pain_point(self) -> str:
        pains = [
            f"xsane is powerful. It's also from 1998. {self.product} is the scanner app Linux deserves in 2026.",
            f"Nobody talks about how hard scanning is on Linux. {self.product} fixes that.",
            f"Your printer 'just works' on Linux. Why not your scanner? {self.product}.",
        ]
        return random.choice(pains) + f"\n\n{self.landing}"

    # ── Reddit ─────────────────────────────────────────────────────────
    def reddit_linux(self) -> str:
        return (
            f"**{self.product} — A modern scanner app for Linux**\n\n"
            f"Hey r/linux,\n\n"
            f"I've been using Linux daily for years, and scanning has always been the one thing "
            f"that still felt like 2005. xsane works, but it's... xsane.\n\n"
            f"So I built {self.product}. It's a clean desktop app that:\n\n"
            f"- Auto-detects your SANE scanner (USB or networked)\n"
            f"- Scans to PDF or PNG at 150/300/600 DPI\n"
            f"- Shows live thumbnails in a sidebar\n"
            f"- Organizes scans into dated session folders\n"
            f"- Opens Gmail with your scan attached in one click\n"
            f"- Light/dark mode that matches your system\n\n"
            f"It's MIT licensed, $25 if you want to support development.\n\n"
            f"**Landing page:** {self.landing}\n"
            f"**GitHub:** {self.repo}\n"
            f"**Buy:** {self.buy}\n\n"
            f"Would love feedback from the community."
        )

    def reddit_selfhosted(self) -> str:
        return (
            f"**{self.product} — Self-hosted document scanning for Linux desktops**\n\n"
            f"Hey r/selfhosted,\n\n"
            f"I know we love our server-side tools, but sometimes you just need to scan a document "
            f"at your desk without spinning up a Docker container.\n\n"
            f"{self.product} is a desktop scanner app for Linux that:\n\n"
            f"- Works with any SANE-compatible scanner (most Canon, Epson, HP, Brother)\n"
            f"- No web server, no database, no cloud — just a Python + Tkinter app\n"
            f"- Exports to PDF or PNG with selectable DPI\n"
            f"- Auto-organizes scans into session folders\n"
            f"- One-click email via Gmail compose\n"
            f"- Remembers your settings between sessions\n\n"
            f"One-time $25, MIT licensed, lifetime updates.\n\n"
            f"{self.landing}\n"
            f"{self.repo}"
        )

    def reddit_ubuntu(self) -> str:
        return (
            f"**{self.product} — Made for Ubuntu users who need to scan documents**\n\n"
            f"Hi r/Ubuntu,\n\n"
            f"If you've ever tried to scan on Ubuntu and ended up in dependency hell, this is for you.\n\n"
            f"{self.product} is a simple `sudo bash install.sh` away. It:\n\n"
            f"- Detects your scanner automatically\n"
            f"- Has a clean GUI (no terminal needed after install)\n"
            f"- Scans to PDF or PNG\n"
            f"- Emails directly from the app\n"
            f"- Remembers your preferences\n\n"
            f"Supports Ubuntu 20.04+ and all derivatives.\n\n"
            f"{self.landing} | {self.repo} | {self.price} one-time"
        )

    # ── Hacker News ──────────────────────────────────────────────────
    def hackernews_show(self) -> str:
        return (
            f"Show HN: {self.product} — A scanner app for Linux that just works\n\n"
            f"{self.landing}\n\n"
            f"I've used Linux as my daily driver for years, and scanning documents has always been "
            f"the one gap that never got fixed. xsane is powerful but ancient. Simple Scan is... simple. "
            f"Nothing in between for people who want a modern desktop experience.\n\n"
            f"So I built {self.product} — a clean Tkinter app that auto-detects SANE scanners, "
            f"scans to PDF/PNG at selectable DPI, shows live thumbnails, organizes by session, "
            f"and can open Gmail with your scan attached.\n\n"
            f"It's a single Python file (~700 lines) with install/uninstall scripts. "
            f"MIT licensed. $25 if you want to support it.\n\n"
            f"Tech stack: Python 3.9+, tkinter, PIL, sane-utils, img2pdf. No dependencies beyond "
            f"what's in your distro's repos.\n\n"
            f"Would love feedback from the HN crowd — especially on packaging and distribution."
        )

    # ── Product Hunt ───────────────────────────────────────────────────
    def producthunt(self) -> str:
        return (
            f"{self.product} — The scanner app Linux was missing\n\n"
            f"{self.tagline}\n\n"
            f"Linux users: your printer works. Your scanner should too.\n\n"
            f"{self.product} auto-detects any SANE scanner and gives you a clean, modern "
            f"interface to scan to PDF or PNG, preview thumbnails, organize sessions, and email "
            f"documents — all from one app.\n\n"
            f"- One-click scanning (no terminal required)\n"
            f"- PDF & PNG at 150/300/600 DPI\n"
            f"- Live thumbnail sidebar\n"
            f"- Session folders (organized by default)\n"
            f"- Built-in email to Gmail\n"
            f"- Light & dark themes\n\n"
            f"{self.price} one-time. MIT License. Lifetime updates.\n\n"
            f"Maker: {self.author} (@mrmoe28)"
        )

    # ── Email Newsletter ─────────────────────────────────────────────
    def email_launch(self) -> str:
        return (
            f"Subject: ScanDesk is here — scanning on Linux, finally solved\n\n"
            f"Hey there,\n\n"
            f"Quick one: I just shipped {self.product}, a scanner app for Linux that doesn't "
            f"require a CS degree to operate.\n\n"
            f"If you or your team scans documents on Linux machines, this saves you:\n\n"
            f"- The 20 minutes of googling 'how to scan ubuntu'\n"
            f"- The xsane interface from 1998\n"
            f"- The 'where did I save that scan?' problem\n\n"
            f"{self.landing}\n\n"
            f"It's {self.price}, one-time, MIT licensed. If it saves you one afternoon of frustration, "
            f"it's paid for itself.\n\n"
            f"Questions? Just reply.\n\n"
            f"— {self.author}\n"
            f"EKO Solar LLC"
        )

    # ── Indie Hackers ────────────────────────────────────────────────
    def indiehackers(self) -> str:
        return (
            f"I built {self.product} — a $25 scanner app for Linux\n\n"
            f"Launched last week. One sale so far (thanks Mom).\n\n"
            f"But here's why I'm excited: every Linux user I've shown it to says the same thing — "
            f"'Finally, someone fixed scanning.'\n\n"
            f"The market is tiny (Linux desktop share ~3%) but the problem is real and totally ignored. "
            f"xsane is powerful but unusable for normal humans. Simple Scan is too simple. "
            f"There's nothing in the sweet spot.\n\n"
            f"{self.product} is that sweet spot. Clean UI, one-click scanning, session folders, "
            f"email integration, dark mode.\n\n"
            f"Stack: Python + tkinter. No framework, no build step, no dependencies beyond what's "
            f"in apt/dnf/pacman.\n\n"
            f"Lessons so far:\n"
            f"- Distribution is harder than coding\n"
            f"- Linux users are loyal but hard to reach\n"
            f"- Pricing at $25 was scary but right\n\n"
            f"Happy to answer questions.\n\n"
            f"{self.landing}"
        )

    # ── Blog Post ────────────────────────────────────────────────────
    def blog_post(self) -> str:
        return (
            f"# Building {self.product}: The Scanner App Linux Deserved\n\n"
            f"## The Problem\n\n"
            f"Scanning on Linux in 2026 still feels like scanning on Linux in 2006.\n\n"
            f"xsane is powerful — it can do everything — but it's also unchanged since the Clinton administration. "
            f"Simple Scan exists but is too bare-bones for real workflows.\n\n"
            f"If you just want to scan a document, save it as PDF, and email it, you shouldn't need to:\n\n"
            f"- Memorize `scanimage` flags\n"
            f"- Manually convert PNM to PDF\n"
            f"- Dig through `~/Documents` to find the file you just created\n\n"
            f"## The Solution\n\n"
            f"{self.product} is a single-file Python app with a clean tkinter interface. It:\n\n"
            f"1. **Auto-detects scanners** — any SANE-compatible USB or network scanner\n"
            f"2. **Previews live thumbnails** — see what you've scanned in a sidebar\n"
            f"3. **Exports to PDF or PNG** — at your choice of DPI (150/300/600)\n"
            f"4. **Organizes automatically** — every session gets a dated folder\n"
            f"5. **Emails in one click** — opens Gmail compose with your scan attached\n"
            f"6. **Looks good** — light/dark mode, Inter font, no gradients or glassmorphism\n\n"
            f"## The Stack\n\n"
            f"- Python 3.9+ (stdlib + tkinter + PIL)\n"
            f"- sane-utils for scanner access\n"
            f"- img2pdf for PDF generation\n"
            f"- Single-file architecture: `scandesk.py` is the whole app\n\n"
            f"## The Business\n\n"
            f"MIT licensed. {self.price} one-time purchase if you want to support development. "
            f"GitHub repo has full source. No SaaS, no subscription, no data collection.\n\n"
            f"## Try It\n\n"
            f"```bash\n"
            f"git clone https://github.com/mrmoe28/scandesk.git\n"
            f"cd scandesk\n"
            f"sudo bash install.sh\n"
            f"scandesk\n"
            f"```\n\n"
            f"Or grab the release tarball from the GitHub releases page.\n\n"
            f"---\n\n"
            f"{self.landing} | {self.repo} | Built by {self.author}"
        )

    # ── LinkedIn ─────────────────────────────────────────────────────
    def linkedin(self) -> str:
        return (
            f"I just shipped {self.product} — a scanner app for Linux that finally makes document "
            f"scanning feel modern.\n\n"
            f"After years of using Linux as my daily driver, I got tired of the scanning workflow "
            f"being stuck in 1998. So I built something clean, fast, and actually enjoyable to use.\n\n"
            f"Key features:\n"
            f"- One-click scanning with any SANE-compatible scanner\n"
            f"- PDF & PNG export at selectable DPI\n"
            f"- Live thumbnail preview sidebar\n"
            f"- Auto-organized session folders\n"
            f"- Built-in email to Gmail\n"
            f"- Light & dark mode\n\n"
            f"It's MIT licensed, {self.price} one-time, and I'm offering lifetime updates.\n\n"
            f"If you or your team uses Linux and scans documents, I'd love your feedback.\n\n"
            f"{self.landing}\n\n"
            f"#{self.product} #Linux #OpenSource #Productivity #DesktopApp"
        )

    # ── Forum Signature / Bio ────────────────────────────────────────
    def forum_signature(self) -> str:
        return (
            f"ScanDesk — The scanner app Linux was missing. "
            f"One-click scanning, PDF export, session folders, email ready. "
            f"{self.price} one-time. {self.landing}"
        )

    # ── GitHub Release Notes (marketing-optimized) ─────────────────
    def github_release(self, version: str = "v1.0.0") -> str:
        return (
            f"## What's New in {version}\n\n"
            f"{self.product} is now available!\n\n"
            f"### Features\n"
            f"- One-click scanning for any SANE-compatible scanner\n"
            f"- PDF and PNG export with selectable DPI (150/300/600)\n"
            f"- Live thumbnail preview sidebar\n"
            f"- Auto-organized session folders\n"
            f"- One-click email to Gmail\n"
            f"- Light and dark themes\n"
            f"- Persistent settings\n\n"
            f"### Install\n"
            f"```bash\n"
            f"sudo bash install.sh\n"
            f"scandesk\n"
            f"```\n\n"
            f"### Get It\n"
            f"- [Landing Page]({self.landing})\n"
            f"- [Buy for {self.price}]({self.buy})\n"
            f"- Full source in this repo (MIT License)\n\n"
            f"### Feedback\n"
            f"Open an issue or email {self.config['email']}"
        )


# ── Campaign Manager ─────────────────────────────────────────────────────
class CampaignManager:
    """Creates, schedules, and tracks marketing campaigns."""

    def __init__(self, config: dict):
        self.config = config
        self.engine = TemplateEngine(config)
        self._ensure_files()

    def _ensure_files(self):
        for f in [LOG_FILE]:
            if not f.exists():
                f.touch()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _make_id(self, platform: str) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        rand = random.randint(100, 999)
        return f"{platform}_{ts}_{rand}"

    def create_campaign(self, platform: str, variant: str = "default") -> Campaign:
        """Generate a new campaign for a platform."""
        generators = {
            "x_showcase": self.engine.x_showcase,
            "x_feature": lambda: self.engine.x_feature(variant if variant != "default" else "scan"),
            "x_milestones": self.engine.x_milestones,
            "x_pain": self.engine.x_pain_point,
            "reddit_linux": self.engine.reddit_linux,
            "reddit_selfhosted": self.engine.reddit_selfhosted,
            "reddit_ubuntu": self.engine.reddit_ubuntu,
            "hackernews": self.engine.hackernews_show,
            "producthunt": self.engine.producthunt,
            "email": self.engine.email_launch,
            "indiehackers": self.engine.indiehackers,
            "blog": self.engine.blog_post,
            "linkedin": self.engine.linkedin,
            "signature": self.engine.forum_signature,
            "github_release": lambda: self.engine.github_release(variant if variant != "default" else "v1.0.0"),
        }

        key = f"{platform}_{variant}" if variant != "default" else platform
        if key not in generators:
            key = platform
        if key not in generators:
            raise ValueError(f"Unknown platform/variant: {platform}/{variant}")

        body = generators[key]()
        title = body.split('\n')[0][:80]
        hashtags = ' '.join(random.sample(self.config["hashtags"], 3))

        campaign = Campaign(
            id=self._make_id(platform),
            platform=platform,
            title=title,
            body=body,
            hashtags=hashtags,
            created_at=self._now(),
        )

        self._log_campaign(campaign)
        return campaign

    def _log_campaign(self, campaign: Campaign):
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(asdict(campaign)) + "\n")

    def get_campaigns(self, status: Optional[str] = None) -> List[Campaign]:
        """Read all campaigns, optionally filtered by status."""
        campaigns = []
        if not LOG_FILE.exists():
            return campaigns
        with open(LOG_FILE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    c = Campaign(**data)
                    if status is None or c.status == status:
                        campaigns.append(c)
                except json.JSONDecodeError:
                    continue
        return campaigns

    def mark_posted(self, campaign_id: str, url: Optional[str] = None):
        """Mark a campaign as posted."""
        campaigns = []
        updated = False
        if LOG_FILE.exists():
            with open(LOG_FILE) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    if data["id"] == campaign_id:
                        data["status"] = "posted"
                        data["posted_at"] = self._now()
                        if url:
                            data["url"] = url
                        updated = True
                    campaigns.append(data)

        if updated:
            with open(LOG_FILE, "w") as f:
                for c in campaigns:
                    f.write(json.dumps(c) + "\n")

    def stats(self) -> dict:
        """Return campaign statistics."""
        all_c = self.get_campaigns()
        drafted = len([c for c in all_c if c.status == "draft"])
        posted = len([c for c in all_c if c.status == "posted"])
        by_platform = {}
        for c in all_c:
            by_platform[c.platform] = by_platform.get(c.platform, 0) + 1
        return {
            "total": len(all_c),
            "drafts": drafted,
            "posted": posted,
            "by_platform": by_platform,
        }

    def generate_week(self) -> List[Campaign]:
        """Generate a full week's marketing content."""
        plan = [
            ("x_showcase", "default"),
            ("reddit_linux", "default"),
            ("x_feature", "email"),
            ("hackernews", "default"),
            ("reddit_selfhosted", "default"),
            ("linkedin", "default"),
            ("x_pain", "default"),
        ]
        campaigns = []
        for platform, variant in plan:
            try:
                c = self.create_campaign(platform, variant)
                campaigns.append(c)
            except ValueError:
                pass
        return campaigns


# ── CLI ──────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="ScanDesk Marketing Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent.py --generate x_showcase          Generate X showcase post
  python agent.py --generate reddit_linux         Generate Reddit r/linux post
  python agent.py --week                          Generate a week's campaigns
  python agent.py --list                          List all campaigns
  python agent.py --stats                         Show statistics
  python agent.py --mark-posted CAMPAIGN_ID       Mark campaign as posted
  python agent.py --all-platforms                 Generate for all platforms
        """
    )
    parser.add_argument("--generate", metavar="PLATFORM", help="Generate a campaign for PLATFORM")
    parser.add_argument("--variant", default="default", help="Variant for platform (default: default)")
    parser.add_argument("--week", action="store_true", help="Generate a full week of campaigns")
    parser.add_argument("--list", action="store_true", help="List all campaigns")
    parser.add_argument("--stats", action="store_true", help="Show campaign stats")
    parser.add_argument("--mark-posted", metavar="ID", help="Mark campaign as posted")
    parser.add_argument("--url", help="URL of the posted content")
    parser.add_argument("--all-platforms", action="store_true", help="Generate all platform variants")
    args = parser.parse_args()

    # Load or create config
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            config = json.load(f)
    else:
        config = DEFAULT_CONFIG.copy()
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)

    manager = CampaignManager(config)

    if args.generate:
        campaign = manager.create_campaign(args.generate, args.variant)
        print(f"\n{'='*60}")
        print(f"  Platform:  {campaign.platform}")
        print(f"  ID:        {campaign.id}")
        print(f"  Status:    {campaign.status}")
        print(f"{'='*60}\n")
        print(campaign.body)
        if campaign.hashtags:
            print(f"\n{'─'*60}")
            print(f"Hashtags: {campaign.hashtags}")
        print(f"\n{'='*60}")
        print(f"  Saved to: {LOG_FILE}")
        print(f"  Landing:  {config['landing_page']}")
        print(f"{'='*60}")
        return

    if args.week:
        campaigns = manager.generate_week()
        print(f"\nGenerated {len(campaigns)} campaigns for the week:\n")
        for c in campaigns:
            print(f"  [{c.platform:20s}] {c.id} — {c.title[:50]}...")
        print(f"\nAll saved to: {LOG_FILE}")
        return

    if args.all_platforms:
        platforms = [
            "x_showcase", "x_feature", "x_milestones", "x_pain",
            "reddit_linux", "reddit_selfhosted", "reddit_ubuntu",
            "hackernews", "producthunt", "email", "indiehackers",
            "blog", "linkedin", "signature", "github_release"
        ]
        print(f"\nGenerating {len(platforms)} campaigns...\n")
        for p in platforms:
            try:
                c = manager.create_campaign(p)
                print(f"  [OK] {p:25s} → {c.id}")
            except ValueError as e:
                print(f"  [SKIP] {p:25s} — {e}")
        print(f"\nAll saved to: {LOG_FILE}")
        return

    if args.list:
        campaigns = manager.get_campaigns()
        if not campaigns:
            print("No campaigns found.")
            return
        print(f"\n{'ID':<35s} {'Platform':<20s} {'Status':<10s} {'Title'}")
        print("─" * 100)
        for c in campaigns:
            print(f"{c.id:<35s} {c.platform:<20s} {c.status:<10s} {c.title[:50]}...")
        return

    if args.stats:
        stats = manager.stats()
        print(f"\n{'─'*50}")
        print(f"  Campaign Statistics")
        print(f"{'─'*50}")
        print(f"  Total campaigns: {stats['total']}")
        print(f"  Drafts:          {stats['drafts']}")
        print(f"  Posted:          {stats['posted']}")
        print(f"\n  By platform:")
        for platform, count in sorted(stats["by_platform"].items()):
            print(f"    {platform:<25s} {count}")
        print(f"{'─'*50}")
        return

    if args.mark_posted:
        manager.mark_posted(args.mark_posted, args.url)
        print(f"Marked {args.mark_posted} as posted.")
        if args.url:
            print(f"  URL: {args.url}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
