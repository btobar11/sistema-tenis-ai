import sys
import os

# Ensure we can import from current directory
sys.path.append(os.getcwd())

try:
    from scrapers.match_scraper import scrape_match_details
    print("Testing match details scraping...")
    
    # Use a known finished match URL (or one found from recent results)
    # Example URL from tennisexplorer (need a real one or finding one dynamically)
    # Let's try to find one first using scrape_today_results
    from scrapers.match_scraper import scrape_today_results
    res = scrape_today_results()
    if res:
        target_match = res[0] # Pick the first one
        if target_match.get('detail_url'):
            print(f"Scraping details for: {target_match['detail_url']}")
            stats = scrape_match_details(target_match['detail_url'])
            print("Stats found:", stats)
        else:
            print("First match has no detail URL")
    else:
        print("No matches found today to test.")

except Exception as e:
    print(f"Error: {e}")
