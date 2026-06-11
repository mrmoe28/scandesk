# Resume Prompt for ScanDesk Project

**Where we left off:** June 10, 2026. ScanDesk v1.0.0 is packaged, has a GitHub repo with CI, a GitHub Release, and a self-built landing page in `docs/`.

## What's Been Done

1. **Core app**: `scandesk.py` (single-file customtkinter scanner GUI)
2. **Packaging**: `install.sh`, `uninstall.sh`, `scandesk.desktop`, `run-scandesk.sh`, `requirements.txt`, `pyproject.toml`
3. **Marketing**: `marketing/screenshot_main.png`, `marketing/screenshot_settings.png`, `marketing/banner_feature.png`
4. **Website**: `docs/index.html` (landing page), `docs/thanks.html` (post-purchase), `docs/style.css`
5. **GitHub repo**: `https://github.com/mrmoe28/scandesk` with CI workflow (tests + auto-release on tags)
6. **GitHub Release v1.0.0**: `https://github.com/mrmoe28/scandesk/releases/tag/v1.0.0` with tarball attached
7. **Released tarball**: `scandesk-v1.0.0-linux.tar.gz` (264KB, SHA256 known)

## Next Steps to Finish

### Option 1: Deploy Landing Page
- GitHub Pages: Enable Pages on the repo, point to `docs/` folder. URL becomes `https://mrmoe28.github.io/scandesk`
- Or Netlify Drop: Zip `docs/` folder and drag to netlify.com

### Option 2: Connect Payment
- **Stripe** (recommended): Go to stripe.com → Payment Links → create a $25 link → paste URL into `docs/index.html` buy button
- **Gumroad**: Create product manually, paste link into `docs/index.html`
- **PayPal.me**: Create link, paste into buy button

### Option 3: Record Demo Video
- Open ScanDesk on your laptop
- Show scanning a document, preview sidebar, settings, email button
- Upload to YouTube or host the MP4 in the repo
- Embed on landing page

### Option 4: Distribute
- Email the tarball directly to roofing company leads
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
