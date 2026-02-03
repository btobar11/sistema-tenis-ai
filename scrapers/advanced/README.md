# Advanced Tennis Scraper

## Setup
1. Install dependencies:
   ```bash
   pip install -r ../requirements.txt
   playwright install chromium
   ```

2. Configure Proxies:
   - Set `ROTATING_PROXY_URL` environment variable (e.g., `http://user:pass@proxy.provider.com:port`).
   - Or edit `tennis_scraper/proxy_manager.py`.

## Running the Spider
To run the ATP Tour spider:

```bash
cd scrapers/advanced
scrapy crawl atp_tour
```

## Anti-Detection Features
- **Headless Browser**: Uses Playwright Chromium.
- **Stealth**: `playwright-stealth` masks WebDriver properties.
- **Fingerprint Randomization**:
  - Random User-Agents.
  - Random Viewports (1920x1080, 1366x768, etc).
  - WebGL/Canvas Noise Injection.
- **Human Behavior**:
  - Random mouse movements and scrolling before extracting data.
  - Variable delays.
