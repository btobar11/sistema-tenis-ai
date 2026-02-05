#!/usr/bin/env python3
"""
Top-Down History Scraper Orchestrator
Scrapes historical match data for Top 100 ATP players from TennisExplorer.

Best Practices Applied:
- User-Agent rotation
- Random delays (3-7 seconds) between requests  
- Exponential backoff on errors
- Real-time logging with flush
"""

import sys
import time
import random
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup
from db_client import get_db_client
from history_scraper import scrape_player_history_from_url

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# User-Agent rotation pool
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
]

# Chrome version for impersonation (use only supported versions)
CHROME_VERSION = "chrome110"

def log(msg):
    """Print with immediate flush for real-time output."""
    print(msg, flush=True)

def get_random_headers():
    """Get randomized headers for each request."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://www.tennisexplorer.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

def fetch_with_retry(url, max_retries=3):
    """Fetch URL with exponential backoff on failure."""
    for attempt in range(max_retries):
        try:
            headers = get_random_headers()
            resp = cffi_requests.get(url, headers=headers, impersonate=CHROME_VERSION, timeout=30)
            
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 403:
                log(f"  ⚠️ 403 Blocked - waiting longer...")
                wait = (2 ** attempt) * 10  # 10s, 20s, 40s
                time.sleep(wait)
            else:
                log(f"  ⚠️ Status {resp.status_code} - retrying...")
                time.sleep(2 ** attempt)
                
        except Exception as e:
            log(f"  ❌ Error: {e}")
            wait = (2 ** attempt) * 5
            time.sleep(wait)
    
    return None

def get_top_players(limit=100):
    """Scrapes the ATP rankings page to get Name and URL of top players."""
    url = "https://www.tennisexplorer.com/ranking/atp-men/"
    log(f"📊 Fetching Rankings from: {url}")
    
    resp = fetch_with_retry(url)
    if not resp:
        log("❌ Failed to fetch rankings")
        return []
    
    soup = BeautifulSoup(resp.content, 'html.parser')
    players = []
    
    tables = soup.find_all('table', class_='result')
    rankings_table = None
    
    for t in tables:
        if len(t.find_all('tr')) > 20: 
            rankings_table = t
            break
    
    if not rankings_table:
        log("❌ Could not find rankings table.")
        return []
        
    rows = rankings_table.find_all('tr')
    for row in rows:
        name_cell = row.find('td', class_='t-name')
        if name_cell:
            link = name_cell.find('a')
            if link:
                name = link.get_text(strip=True)
                href = link['href']
                full_url = "https://www.tennisexplorer.com" + href
                players.append((name, full_url))
                
        if len(players) >= limit:
            break
    
    log(f"✅ Found {len(players)} players in rankings")
    return players

def run_orchestrator():
    """Main orchestrator function."""
    db = get_db_client()
    log("=" * 50)
    log("🎾 TOP-DOWN HISTORY SCRAPER")
    log("=" * 50)
    
    # 1. Get Top 100
    top_players = get_top_players(100)
    
    if not top_players:
        log("❌ No players found. Exiting.")
        return
    
    # Stats
    success_count = 0
    error_count = 0
    
    # 2. Iterate and Scrape
    for idx, (name, url) in enumerate(top_players):
        log(f"\n[{idx+1}/{len(top_players)}] 🎾 Processing: {name}")
        log(f"    URL: {url}")
        
        try:
            result = scrape_player_history_from_url(url, name, db)
            if result:
                success_count += 1
                log(f"    ✅ Success")
            else:
                log(f"    ⚠️ No history data found")
        except Exception as e:
            error_count += 1
            log(f"    ❌ Error: {e}")
        
        # Random delay (3-7 seconds as recommended)
        sleep_time = random.uniform(3.0, 7.0)
        log(f"    ⏱️ Sleeping {sleep_time:.1f}s...")
        time.sleep(sleep_time)
    
    # Summary
    log("\n" + "=" * 50)
    log("📊 SCRAPING COMPLETE")
    log(f"   ✅ Success: {success_count}")
    log(f"   ❌ Errors: {error_count}")
    log("=" * 50)

if __name__ == "__main__":
    run_orchestrator()
