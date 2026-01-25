import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from db_client import get_db_client

load_dotenv()

# We still need headers for TennisExplorer scraping, but we can reuse the user-agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    # DB headers are handled by db_client
}

def search_player_profile(player_name):
    """
    """
    # Clean name: remove suffixes like (2) or [WC]
    import re
    clean_name = re.sub(r'\s*\(\d+\).*', '', player_name).strip()
    search_url = f"https://www.tennisexplorer.com/search/?query={clean_name.replace(' ', '+')}"
    
    parts = clean_name.split(' ')
    first_name = parts[0].lower()
    last_name = parts[-1].lower() if len(parts) > 1 else parts[0].lower()
    
    # 1. Try Direct URL Guessing
    guesses = [
        f"https://www.tennisexplorer.com/player/{last_name}/",
        f"https://www.tennisexplorer.com/player/{last_name}-{first_name}/",
        f"https://www.tennisexplorer.com/player/{player_name.replace(' ', '-').lower()}/"
    ]
    
    for url in guesses:
        try:
            # print(f"  Trying direct URL: {url}")
            r = requests.get(url, headers=HEADERS, timeout=5)
            if r.status_code == 200 and "Identity" in r.text: 
                return url
        except:
            pass

    # 2. Fallback to Search
    try:
        # print(f"  Searching URL: {search_url}")
        r = requests.get(search_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Look for ANY link with /player/ in href
        links = soup.find_all('a', href=True)
        for link in links:
            if "/player/" in link['href'] and last_name in link['href'] and first_name in link.text.lower():
                return "https://www.tennisexplorer.com" + link['href']
                
        # Look for result table specifically
        table = soup.find('table', class_='result')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) > 0:
                    link = cols[0].find('a')
                    if link:
                         href = link['href']
                         if "/player/" in href and last_name in href:
                             return "https://www.tennisexplorer.com" + href

    except Exception as e:
        print(f"Search failed for {player_name}: {e}")
    return None

def scrape_player_details(profile_url):
    """
    Scrape Age, Country, Height, etc. from profile page.
    """
    details = {}
    try:
        r = requests.get(profile_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Look for table with player info
        table = soup.find('table', class_='plDetail')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                txt = row.get_text()
                if "Country:" in txt:
                    details['country'] = txt.replace("Country:", "").strip()
                if "Height / Weight:" in txt:
                    details['height'] = txt.replace("Height / Weight:", "").strip()
                if "Age:" in txt:
                     # "Age: 24 (16.08.2001)"
                     if "(" in txt and ")" in txt:
                         try:
                             date_str = txt.split('(')[1].split(')')[0]
                             # Format DD.MM.YYYY to YYYY-MM-DD
                             d, m, y = date_str.split('.')
                             details['birth_date'] = f"{y}-{m}-{d}"
                         except:
                             pass
                if "Sex:" in txt:
                     details['hand'] = "R" # Placeholder/Check actual text
        
    except Exception as e:
        print(f"Details scrape failed: {e}")
        
    return details

def run_enrichment():
    print("Starting player enrichment...")
    
    db = get_db_client()
    if not db:
        print("DB Connection failed")
        return
    
    # Fetch players with missing metadata
    # We use db client to fetch
    endpoint = f"{db.url}/rest/v1/players?select=id,name,country,birth_date&order=id"
    
    try:
        print(f"Fetching players...")
        r = db._request_with_retry('get', endpoint)
        if not r or r.status_code != 200:
            print("Failed to fetch players from DB")
            return
            
        all_players = r.json()
        print(f"Total players in DB: {len(all_players)}")
        
        # Filter: missing country OR missing birth_date
        players = [p for p in all_players if not p.get('country') or not p.get('birth_date')]
        # Limit to 50 for this run to avoid banning
        players = players[:50]
        
    except Exception as e:
        print(f"Failed to fetch players: {e}")
        return

    print(f"Found {len(players)} players to enrich.")
    
    for p in players:
        print(f"Enriching {p['name']}...")
        url = search_player_profile(p['name'])
        
        if url:
            # print(f"  Profile: {url}")
            details = scrape_player_details(url)
            # print(f"  Data: {details}")
            
            if details:
                # Update DB
                patch_endpoint = f"{db.url}/rest/v1/players?id=eq.{p['id']}"
                r_update = db._request_with_retry('patch', patch_endpoint, json=details)
                if r_update and r_update.status_code in [200, 204]:
                    print(f"  [SUCCESS] Updated {p['name']}")
                else:
                    print(f"  [FAIL] Update DB for {p['name']}")
        else:
            print("  [SKIP] Profile not found.")

if __name__ == "__main__":
    run_enrichment()

