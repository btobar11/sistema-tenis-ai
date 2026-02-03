import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'scrapers'))
from scrapers.backfill_stats import scrape_detailed_stats
# Hardcoded known match (from H2H list)
target_url = "https://www.tennisexplorer.com/match-detail/?id=3010463"

if True:
    print(f"Testing URL: {target_url}")
    target = {'detail_url': target_url} # mock
    
    import requests
    # Headers mimicking standard browser but using standard lib
    h = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }
    
    # Standard requests
    print("Using standard requests...")
    r = requests.get(target_url, headers=h, timeout=10)
    
    with open("debug_page_std.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    print("Dumped HTML to debug_page_std.html")
    
    # We can't use the existing 'scrape_detailed_stats' easily because it imports 'requests' from curl_cffi inside correct?
    # No, scrape_detailed_stats imports requests at TOP of backfill_stats.
    # So I can't restart the scraping logic with standard requests unless I hack backfill_stats.
    # But I can just grep the output file for "Aces".
    if "Aces" in r.text or "Winning %" in r.text:
        print("SUCCESS! Found stats in standard response.")
    else:
        print("FAILURE. Stats unused in standard response.")
else:
    print("No matches found today.")
