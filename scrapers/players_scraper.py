import json
import time
from curl_cffi import requests
from bs4 import BeautifulSoup

def fetch_live_rankings(url):
    print(f"Fetching {url}...")
    try:
        # User-Agent matching chrome110 to bypass Cloudflare
        r = requests.get(url, impersonate="chrome110", timeout=30)
        if r.status_code != 200:
            print(f"Failed to fetch {url}: Status {r.status_code}")
            return []
        return parse_live_table(r.content)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def parse_live_table(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    players = []
    
    # live-tennis.eu usually has a main table. We look for tr elements.
    # The structure is often: Rank | CH | Name | Age | Country | Points ...
    
    rows = soup.find_all('tr')
    
    for row in rows:
        cols = row.find_all('td')
        if not cols:
            continue
            
        try:
            # We look for rows where the first column is a specific rank integer
            # Note: live-tennis sometimes nests tables. 
            # Valid row usually has: Rank (int), Name (link or text), Country (text), Points (int)
            
            # Simple heuristic: Col 0 is Rank, Col 2 or 3 is Name?
            # Let's inspect based on typical live-tennis structure:
            # Col 0: Rank (e.g. "1")
            # Col 1: CH (Career High)
            # Col 2: Name (e.g. "Jannik Sinner")
            # Col 3: Age
            # Col 4: Country (e.g. "ITA")
            # Col 5: Points
            
            # Filter headers/ads
            txt_0 = cols[0].get_text(strip=True)
            if not txt_0.isdigit():
                continue
                
            rank = int(txt_0)
            
            # Limit to top 400 as requested
            if rank > 400:
                continue

            # Correct Indices based on debug:
            # Col 0: Rank
            # Col 3: Name
            # Col 5: Country
            # Col 6: Points

            # Parsing Name (Col 3)
            name_col = cols[3]
            name = name_col.get_text(strip=True)
            
            # Parsing Country (Col 5)
            country = cols[5].get_text(strip=True)
            if not country: 
                country = "UNK"
                
            # Parsing Points (Col 6)
            points_txt = cols[6].get_text(strip=True).replace(',', '')
            if points_txt.isdigit():
                points = int(points_txt)
            else:
                points = 0
            
            players.append({
                "name": name,
                "rank_single": rank,
                "country": country,
                "plays_hand": "U", # Not available in standard view
                "points": points
            })
            
        except Exception:
            # Skip malformed rows
            continue
            
    return players

def main():
    print("--- Tennis System: Live Scraper (Top 400) ---")
    
    all_players = []
    
    # 1. ATP Live Rankings
    atp_url = "https://live-tennis.eu/en/atp-live-ranking"
    atp_players = fetch_live_rankings(atp_url)
    print(f"Scraped {len(atp_players)} ATP players.")
    all_players.extend(atp_players)
    
    # 2. WTA Live Rankings
    wta_url = "https://live-tennis.eu/en/wta-live-ranking"
    # Be polite
    time.sleep(2)
    wta_players = fetch_live_rankings(wta_url)
    print(f"Scraped {len(wta_players)} WTA players.")
    all_players.extend(wta_players)
    
    # Output to JSON
    # We output to a file so we can run the json_to_sql script independently
    with open('scrapers/data.json', 'w', encoding='utf-8') as f:
        json.dump(all_players, f, indent=2)
        
    print(f"Total {len(all_players)} players saved to scrapers/data.json")

if __name__ == "__main__":
    main()
