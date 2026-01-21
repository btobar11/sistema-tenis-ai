from curl_cffi import requests
from bs4 import BeautifulSoup

def check_player_deep_data(player_url):
    print(f"Checking deep data for: {player_url}")
    try:
        response = requests.get(
            player_url,
            impersonate="chrome110",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }
        )
        print(f"Status Code: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Check Matches/Results
        matches_table = soup.find('table', class_='result')
        if matches_table:
            print("[OK] Matches table found.")
            # Inspect first row
            rows = matches_table.find_all('tr')
            if len(rows) > 0:
                print(f"     Found {len(rows)} match rows.")
        else:
            print("[FAIL] No matches table found.")

        # 2. Check Surface Stats
        # Usually in a separate table or massive summary
        # Looking for "Current year" or "Career" stats
        # text filter for "Clay", "Hard"
        if "Clay" in response.text and "Hard" in response.text:
             print("[OK] Surface text found (likely stats available).")
        else:
             print("[WARN] Surface keywords not prominent.")

        # 3. Check for specific Injury indications?
        # TennisExplorer marks injuries often with 'ret.' in matches or news.
        if "retired" in response.text or "ret." in response.text:
            print("[INFO] Found 'retired'/'ret.' keyword (Injury proxy potential).")
        else:
            print("[INFO] No injury keywords found (Player might be healthy or data distinct).")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Example: Jannik Sinner
    # Need to find his URL format first, usually /player/sinner/
    # For now, searching implies we know the URL. I'll guess a standard one or search.
    # Actually, let's search first.
    
    search_url = "https://www.tennisexplorer.com/search/?query=sinner"
    print(f"Searching for Sinner... {search_url}")
    # (Simple search - skipping for this test, hardcoding a known-ish URL format to test)
    # TennisExplorer format: https://www.tennisexplorer.com/player/sinner/
    
    target_url = "https://www.tennisexplorer.com/player/sinner/"
    check_player_deep_data(target_url)
