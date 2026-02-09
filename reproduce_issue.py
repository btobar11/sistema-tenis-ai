import sys
import os

# Ensure we can import from current directory
sys.path.append(os.getcwd())

try:
    from scrapers.match_scraper import scrape_today_results
    print("Import successful from scrapers.match_scraper")
    try:
        results = scrape_today_results()
        print(f"Scraped {len(results)} matches.")
        if len(results) > 0:
            print("First match sample:", results[0])
    except Exception as e:
        print(f"Scrape failed: {e}")
        import traceback
        traceback.print_exc()

except ImportError:
    # Fallback if running from inside scrapers/
    try:
        from match_scraper import scrape_today_results
        print("Import successful from match_scraper")
        results = scrape_today_results()
        print(f"Scraped {len(results)} matches.")
    except Exception as e:
        print(f"Import/Scrape failed: {e}")
