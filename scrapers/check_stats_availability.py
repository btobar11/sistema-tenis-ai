from curl_cffi import requests
from bs4 import BeautifulSoup
import time

def check_match_stats(player_url):
    print(f"checking stats from player page: {player_url}")
    try:
        response = requests.get(
            player_url,
            impersonate="chrome110"
        )
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the first match link
        matches_table = soup.find('table', class_='result')
        if matches_table:
            match_link_tag = matches_table.find('a', href=True, title=lambda x: x and 'match detail' in x)
            # Sometimes the score link is the detail link
            
            # Use basic row finding
            rows = matches_table.find_all('tr')
            print(f"Found {len(rows)} rows in result table.")
            for i, row in enumerate(rows[:5]): # Check first 5 rows
                links = row.find_all('a', href=True)
                for l in links:
                    print(f"Row {i} link: {l['href']}")
                    if "match-detail" in l['href']:
                        detail_url = "https://www.tennisexplorer.com" + l['href']
                        print(f"Found match detail: {detail_url}")
                        
                        # Fetch the detail page
                        time.sleep(2) # be nice
                        resp_detail = requests.get(detail_url, impersonate="chrome110")
                        soup_detail = BeautifulSoup(resp_detail.content, 'html.parser')
                        
                        # Look for stats table
                        # It is usually a table with class "center" or similar inside the content
                        center_tables = soup_detail.find_all('table', class_='center')
                        found_stats = False
                        for tbl in center_tables:
                            if "1st Serve" in tbl.get_text():
                                print("[SUCCESS] Found Detailed Stats Table!")
                                print(tbl.get_text()[:200]) # Print snippet
                                found_stats = True
                                break
                        
                        if not found_stats:
                             print("[INFO] Detail page loaded, but specific stats table not found (might be absent for this match).")

                        return # Checking one is enough
            print("[WARN] No match detail links found.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test with a known Match Detail URL (e.g., Alcaraz recent match)
    # Finding one manually to test extraction logic first.
    # example: https://www.tennisexplorer.com/match-detail/?id=2769438 (This is a guess/placeholder ID, will use a real scraped one if I can find one)
    # Let's try to 'search' for a match or just iterate the search results.
    
    # Actually, let's just use the main page to find a valid match ID.
    print("Fetching main page to find a valid match ID...")
    try:
        r = requests.get("https://www.tennisexplorer.com", impersonate="chrome110")
        soup = BeautifulSoup(r.content, 'html.parser')
        # Find any match detail link
        link = soup.find('a', href=lambda x: x and 'match-detail' in x)
        if link:
            full_url = "https://www.tennisexplorer.com" + link['href']
            print(f"Found random match: {full_url}")
            # Now extract stats from it
            resp_detail = requests.get(full_url, impersonate="chrome110")
            detail_soup = BeautifulSoup(resp_detail.content, 'html.parser')
            print("Page Title:", detail_soup.title.text)
            
            # Look for stats
            stats_tables = detail_soup.find_all('table', class_='center') # They often use this class
            found = False
            for tbl in stats_tables:
                 if "Winning % on 1st Serve" in tbl.get_text() or "ACES" in tbl.get_text().upper():
                     print("[SUCCESS] Found Stats Table!")
                     print(tbl.get_text()[:300])
                     found = True
                     break
            if not found:
                print("[INFO] Stats table not found in this match (might be minor match).")
                print("Content snippet:", detail_soup.get_text()[:500])
        else:
            print("[FAIL] Could not find any match detail link on homepage.")
            
    except Exception as e:
        print(f"Error: {e}")
