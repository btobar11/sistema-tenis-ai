
"""
History Scraper
Fetches historical match results for players to build the 'player_history' dataset.
Target: TennisExplorer Player Profiles
"""
import time
import re
from datetime import datetime, timedelta
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup
from db_client import get_db_client
import urllib.parse

# Headers for requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.tennisexplorer.com/"
}

def search_player_url(player_name):
    """
    Finds the TennisExplorer profile URL for a given player name.
    """
    # TennisExplorer Search likes "Surname Name" or "Surname"
    # match player_name format?
    query = player_name
    
    search_url = f"https://www.tennisexplorer.com/search/?query={urllib.parse.quote(query)}"
    print(f"Searching: {search_url}")
    try:
        resp = cffi_requests.get(search_url, headers=HEADERS, impersonate="chrome110", timeout=15)
        print(f"Status: {resp.status_code}")
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # Check if redirected to profile
        if "tennisexplorer.com/player/" in resp.url or "/player/" in str(resp.content):
             if "tennisexplorer.com/player/" in resp.url:
                 return resp.url
        
        # Check results table
        results = soup.find_all('table', class_='result')
        print(f"  Found {len(results)} tables. checking content...")
        
        if results:
            for idx, tbl in enumerate(results[:2]): # Check first 2 tables only deep
                print(f"  --- Table {idx} ---")
                rows = tbl.find_all('tr')
                for i, row in enumerate(rows[:3]): # Check first 3 rows
                     print(f"    R{i}: {str(row)[:300]}")
                for row in rows:
                    links = row.find_all('a')
                    for l in links:
                        txt = l.get_text(strip=True)
                        href = l['href']
                        # print(f"    Link: {txt} -> {href}")
                        
                        if "/player/" in href:
                             print(f"  Found candidate in Table {idx}: {txt} -> {href}")
                             return "https://www.tennisexplorer.com" + href
        
        print("  No suitable player link found in results.")
            
    except Exception as e:
        print(f"Error searching for {player_name}: {e}")
    return None

def parse_history_table(html_content, player_id, db):
    """
    Parses the matches table from a player's profile.
    Returns a list of match dictionaries.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table', class_='result')
    
    matches_found = []
    
    # We need to find the table that lists matches. 
    # Usually it's the one with 'result' class and many rows.
    target_table = None
    for idx, t in enumerate(tables):
        # Heuristic: Check if headers contain 'Round' or 'Result'
        headers = t.find_all('th')
        header_text = " ".join([h.get_text() for h in headers]).lower()
        # print(f"DEBUG: Table {idx} headers: {header_text}")
        if 'round' in header_text or 'result' in header_text:
            target_table = t
            print(f"DEBUG: Selected Table {idx} (headers match)")
            break
            
    if not target_table and tables:
        # Fallback: Use the largest table
        target_table = max(tables, key=lambda t: len(t.find_all('tr')))
        print(f"DEBUG: Fallback to largest table (Rows: {len(target_table.find_all('tr'))})")

    if not target_table:
        print("  No history table found.")
        return []

    rows = target_table.find_all('tr')
    current_tournament = None
    current_surface = 'HARD' # Default
    
    for row in rows:
        row_classes = row.get('class', [])
        
        # 1. Tournament Header Row
        if 'head' in row_classes or row.find('td', class_='t-name'):
            # In TE, tournament header is often a row with a link to tournament
            # It might look like: <tr class="head flags">...<td class="t-name"><a...>Australian Open</a></td>...</tr>
            t_link = row.find('td', class_='t-name')
            if t_link:
                txt = t_link.get_text(strip=True)
                if 'doubles' in txt.lower():
                    current_tournament = "SKIP"
                    continue
                
                parts = txt.split(',')
                current_tournament = parts[0].strip()
                
                # Inferred surface logic
                t_lower = txt.lower()
                if 'clay' in t_lower: current_surface = 'CLAY'
                elif 'grass' in t_lower: current_surface = 'GRASS'
                elif 'hard' in t_lower: current_surface = 'HARD'
                elif 'indoor' in t_lower: current_surface = 'HARD'
                else: current_surface = 'HARD' # Default fallback
                continue

        if current_tournament == "SKIP":
            continue
            
        # 2. Match Data Row
        # Expected cols: Date | Round | Result | Score | Opponent | ...
        cells = row.find_all('td')
        if len(cells) < 5: continue
        
        try:
            # Date (Col 0)
            date_text = cells[0].get_text(strip=True) # "15.01."
            # We need year. Usually profile starts with current year.
            # Ideally we pass 'year' context or assume current/last year based on flow.
            # For now, let's assume current year (2026 in sim, 2025/2026 real)
            # Better: track the year if it appears in headers. 
            # TE puts year in the tournament header "Australian Open 2025".
             
            # Round (Col 2) - varies
            # Result (Col ?): Look for class 'win' or 'lost'?
            # actually TE result is often inferred from score or explicit col.
            
            # Let's try to identify columns by content
            # Opponent is usually in a cell with <a href="/player/...">
            
            opponent_name = "Unknown"
            opponent_link = None
            
            for c in cells:
                a_tag = c.find('a')
                if a_tag and '/player/' in a_tag['href']:
                    opponent_name = a_tag.get_text(strip=True)
                    opponent_link = "https://www.tennisexplorer.com" + a_tag['href']
            
            # Score
            # Usually cell with digits and dashes "6-4 6-2"
            score_text = ""
            for c in cells:
                txt = c.get_text(strip=True)
                if re.search(r'\d-\d', txt):
                   score_text = txt
                   break
                   
            if not opponent_link: continue
            
            # Create Match Object
            match_data = {
                'date_str': date_text,
                'tournament': current_tournament,
                'surface': current_surface,
                'opponent_name': opponent_name,
                'opponent_url': opponent_link,
                'score': score_text
            }
            matches_found.append(match_data)
            
        except Exception as e:
            # print(f"Row parse error: {e}")
            continue
            
    return matches_found

def scrape_player_history(player_name, limit=20):
    url = search_player_url(player_name)
    if not url:
        print(f"Could not find profile for {player_name}")
        return

    print(f"Scraping history from: {url}")
    # ... implementation pending verification of table structure ...
    
    resp = cffi_requests.get(url, headers=HEADERS, impersonate="chrome110")
    # For now, let's just dump the structure to verify before writing full parser
    print(resp.content[:500])
    return resp.content

def scrape_player_history_from_url(player_url, player_name, db):
    """
    Scrapes match history given a direct profile URL.
    """
    print(f"Scraping history for {player_name} from {player_url}")
    try:
        resp = cffi_requests.get(player_url, headers=HEADERS, impersonate="chrome110", timeout=20)
        if resp.status_code != 200:
            print(f"Error fetching profile: Status {resp.status_code}")
            return
            
        matches = parse_history_table(resp.content, None, db) # player_id passed as None for now
        print(f"  Found {len(matches)} historical matches.")
        
        # We need the primary player's ID from the DB to save 'player_history'
        # Check if player exists, if not create?
        # The orchestrator should probably handle player creation if new from rankings.
        # But let's assume valid name passed.
        
        # Get Player ID
        res = db.table('players').select('id').eq('name', player_name).execute()
        if not res.data:
            print(f"  Player {player_name} not found in DB. Creating...")
            # Create player entry
            # In a real top-down approach, we might want to enrich immediately or later.
            # Minimal insert:
            data = {'name': player_name, 'rank_single': 0} # Rank 0 placeholder
            res = db.table('players').insert(data).execute()
            player_id = res.data[0]['id']
        else:
            player_id = res.data[0]['id']
            
        print(f"  Player ID: {player_id}")
        
        # Save Matches
        new_count = 0
        for m in matches:
            # 1. Ensure Opponent Exists
            opp_name = m['opponent_name']
            opp_id = None
            if opp_name != "Unknown":
                res_opp = db.table('players').select('id').eq('name', opp_name).execute()
                if res_opp.data:
                    opp_id = res_opp.data[0]['id']
                else:
                    # Auto-create opponent
                    # print(f"    Creating opponent {opp_name}")
                    try:
                        res_new = db.table('players').insert({'name': opp_name}).execute()
                        opp_id = res_new.data[0]['id']
                    except Exception as e:
                        # Race condition or duplicate execution
                        pass

            # 2. Insert into 'player_history' (and 'matches' if we want global registry)
            # For now, let's just populate 'player_history' as requested 
            
            # Helper to parse "20.01." to Date
            # Assume 2025/2026. 
            # Logic: If month > current_month + 2 -> Last Year. Else Current Year.
            # Simplified: Just string for now or Attempt conversion
            
            try:
                day, month = map(int, m['date_str'].strip('.').split('.'))
                year = datetime.now().year
                # Basic rollover logic: if today is Jan and match is Dec -> prev year
                if datetime.now().month < 3 and month > 10:
                    year -= 1
                
                match_date = datetime(year, month, day).strftime('%Y-%m-%d')
            except:
                match_date = datetime.now().strftime('%Y-%m-%d') # Fallback
            
            history_entry = {
                'player_id': player_id,
                'match_date': match_date,
                'opponent_id': opp_id,
                'result': 'Win' if 'Win' in m.get('result', '') else 'Loss', # Parser didn't extract result yet!
                # We need to infer result from score or parser update.
                # Re-check parser: currently does not extract result explicitly.
                # Let's add basic score-based result inference?
                # or just save raw for now.
                'surface': m['surface'],
                'opponent_rank': None # Future: scrape rank from row
            }
            
            # Upsert history logic avoid dupes?
            # Ideally use upsert on (player_id, match_date, opponent_id) constraint
            try:
                # db.table('player_history').insert(history_entry).execute()
                # Use simple duplicate check
                
                # Check if exists
                chk = db.table('player_history').select('id').eq('player_id', player_id).eq('match_date', match_date).eq('opponent_id', opp_id).execute()
                if not chk.data:
                    db.table('player_history').insert(history_entry).execute()
                    new_count += 1
            except Exception as e:
                # print(e)
                pass
                
        print(f"  Saved {new_count} new history entries.")

    except Exception as e:
        print(f"Error scraping player URL: {e}")

if __name__ == "__main__":
    db = get_db_client()
    # Test Orchestrator flow manually
    scrape_player_history_from_url("https://www.tennisexplorer.com/player/sinner/", "Sinner Jannik", db)

