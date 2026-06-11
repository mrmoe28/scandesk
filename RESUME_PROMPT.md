# Resume Prompt for ScanDesk Project

**Where we left off:** June 10, 2026. ScanDesk v1.0.0 is packaged, has a GitHub repo with CI, a GitHub Release, and a self-built landing page in `docs/`.

## What's Been Done

1. **Core app**: `scandesk.py` (single-file customtkinter scanner GUI)
2. **Packaging**: `install.sh`, `uninstall.sh`, `scandesk.desktop`, `run-scandesk.sh`, `requirements.txt`, `pyproject.toml`
3. **Marketing**: `marketing/screenshot_main.png`, `marketing/screenshot_settings.png`, `marketing/banner_feature.png`
4. **Website**: `docs/index.html` (landing page), `docs/thanks.html` (post-purchase), `docs/style.css`
5. **GitHub repo**: `https://github.com/mrmoe28/scandesk` with CI workflow (tests + auto-release on tags)
6. **GitHub Pages LIVE**: `https://mrmoe28.github.io/scandesk/` (deployed from `docs/` folder)
7. **GitHub Release v1.0.0**: `https://github.com/mrmoe28/scandesk/releases/tag/v1.0.0` with tarball attached
8. **Released tarball**: `scandesk-v1.0.0-linux.tar.gz` (264KB, SHA256 known)

## Quick Links

| Resource | URL |
|----------|-----|
| GitHub Repo | `https://github.com/mrmoe28/scandesk` |
| Live Website | `https://mrmoe28.github.io/scandesk/` |
| Download | `https://github.com/mrmoe28/scandesk/releases/download/v1.0.0/scandesk-v1.0.0-linux.tar.gz` |
| Support | `https://github.com/mrmoe28/scandesk/issues` |

## Next Steps to Finish

### Option 1: Connect Payment (Pick one)
- **Square** (RECOMMENDED — your choice): Go to `squareup.com` → Items & Orders → Create Item "ScanDesk v1.0.0" → Price $25 → Save → Share → Payment Link → copy URL → give it to me → I paste it into `docs/index.html` → push to GitHub → Pages auto-updates
- **Stripe**: Go to stripe.com → Payment Links → create $25 link → paste URL into `docs/index.html` buy button → push to GitHub
- **Gumroad**: Create product, paste link into `docs/index.html`
- **PayPal.me**: Create link, paste into buy button

### Option 2: Record Demo Video
- Open ScanDesk on your laptop
- Show scanning, preview sidebar, settings, email button
- Upload to YouTube or host MP4 in repo
- Embed on landing page

### Option 3: Distribute
- Email tarball to roofing company leads
- Post on r/linux, r/selfhosted, Hacker News
- Add to awesome-linux-apps lists

## Known Issues

- Startup `TclError` sometimes appears in `app.log` (root bind race condition). Does not block functionality.
- `canon_scanner_ui.py.bak*` files cleaned from repo via `.gitignore` but may exist locally.

## Pick Up This Project

1. `git clone https://github.com/mrmoe28/scandesk.git`
2. `cd scandesk`
3. `sudo bash install.sh` to test locally
4. Edit `docs/index.html` to add your payment link
5. Push changes back to GitHub
6. Enable GitHub Pages or deploy to Netlify
7. Share the URL
