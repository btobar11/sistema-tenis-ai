# Architecture: Advanced Tennis Scraper (Scrapy + Playwright)

## Overview
This system is designed to scrape highly protected dynamic websites (ATP Tour, Flashscore) by simulating legitimate user behavior. It leverages **Scrapy** for orchestration and data pipelines, and **Playwright** for "Stealth" rendering and interaction.

## System Components

### 1. Scrapy Engine (Orchestrator)
- **Spider (`TennisSpider`)**: Defines the crawling logic (URLs, parsing rules). Yields `scrapy.Request`.
- **Scheduler**: Manages the queue of requests (Redis or Memory).
- **Item Pipeline**: Processes extracted data (Cleaning, Validation, DB Insertion).

### 2. Custom Downloader Middleware (`PlaywrightMiddleware`)
- Intercepts `process_request`.
- Instead of letting Scrapy downloader (Twisted) handle it, it passes the request to the `BrowserManager`.
- Receives the *rendered HTML* back from `BrowserManager`.
- Returns a `HtmlResponse` to Scrapy.

### 3. Browser Manager (`BrowserService`)
- Manages a pool of **Playwright** Pages/Contexts.
- **Stealth Injection**: 
  - Uses `playwright-stealth` to mask automation flags (`navigator.webdriver`).
  - Randomizes `User-Agent`, `Viewport`, `Locale`, `Timezone`.
  - Injects `Canvas` and `WebGL` noise.
- **Interaction**:
  - Handles `mouse_move`, `scroll`, and `click` to trigger lazy loading.
  - Solving simple puzzles if needed.

### 4. Proxy Manager (`ProxyService`)
- Interfaces with Proxy Providers (e.g., BrightData, SmartProxy).
- Rotates IP addresses on per-request or per-session basis.
- Handles Auth and headers.
- **Jitter/Backoff**: Implements wait times if blocked.

## Data Flow

```mermaid
graph TD
    A[Scrapy Spider] -->|Request URL| B(Scheduler)
    B -->|Next Request| C{Playwright Middleware}
    C -->|Get Page| D[Browser Manager]
    D -->|Get Proxy| E[Proxy Manager]
    E -->|Valid Proxy| D
    D -->|Render Page + Stealth| F[Target Site (ATP/Flashscore)]
    F -->|HTML Content| D
    D -->|HtmlResponse| C
    C -->|Response| A
    A -->|Items| G[Pipeline]
    G -->|JSON/DB| H[(Database)]
```

## Evasion Techniques
- **Browser Fingerprinting**: Randomizing font lists, screen resolution, and hardware concurrency.
- **Behavioral Analysis**: Non-linear mouse movements using Bezier curves before clicks.
- **Network**: consistent "Residential" IP geolocation matching the browser's timezone.
- **Header rotators**: Consistent `Sec-Ch-Ua`, `Sec-Fetch-Site` headers appropriate for Chrome/Firefox.

## Dependencies
- `scrapy`
- `playwright`
- `playwright-stealth`
- `fake-useragent`
