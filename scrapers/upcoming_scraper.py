"""
Upcoming Matches Scraper
Fetches scheduled matches for the next 7 days from tennis calendars
"""
import os
import time
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests as http_requests
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup
from db_client import get_db_client

load_dotenv()

def scrape_upcoming_matches():
    """Scrape upcoming matches from tennis calendar"""
    url = "https://www.tennisexplorer.com/next/"
    print(f"Fetching {url}...")
    
    try:
        response = cffi_requests.get(url, impersonate="chrome110", timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        matches = []
        # Find match tables
        tables = soup.find_all('table', class_='result')
        
        for table in tables:
            rows = table.find_all('tr')
            
            current_tournament = "Unknown Tournament"
            current_surface = "HARD" # Default
            
            buffer_player = None
            buffer_time = None
            
            for row in rows:
                row_classes = row.get('class', [])
                
                # HEADER ROW (Tournament info)
                if 'head' in row_classes:
                    # Parse Tournament
                    # <tr class="head flags"><td><a href="...">ATP Dallas</a>...</td></tr>
                    links = row.find_all('a')
                    if links:
                        current_tournament = links[0].get_text(strip=True)
                    else:
                        current_tournament = row.get_text(strip=True)
                        
                    # Infer Surface from Tournament Name
                    t_lower = current_tournament.lower()
                    if 'clay' in t_lower: current_surface = 'CLAY'
                    elif 'grass' in t_lower: current_surface = 'GRASS'
                    elif 'hard' in t_lower: current_surface = 'HARD'
                    elif 'indoor' in t_lower: current_surface = 'HARD' # Indoor Hard usually
                    else: current_surface = 'HARD' # Default
                    
                    # Reset buffer
                    buffer_player = None
                    continue
                
                # MATCH ROW
                try:
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue
                        
                    # Extract basics
                    t_text = cells[0].get_text(strip=True) # Time
                    p_name = cells[1].get_text(strip=True) # Player Name
                    
                    # Check for scores to exclude finished/live
                    c2 = cells[2].get_text(strip=True)
                    c3 = cells[3].get_text(strip=True)
                    has_score = (c2.isdigit() or c3.isdigit())
                    
                    if has_score:
                        buffer_player = None 
                        continue
                        
                    if not p_name:
                        continue

                    if buffer_player:
                        # We have a P1 waiting, this must be P2
                        p1 = buffer_player
                        p2 = p_name
                        match_time_str = buffer_time if buffer_time else t_text
                        
                        # Date Parsing Logic
                        # 1. Parsing Time (HH:MM)
                        hour = 12
                        minute = 0
                        try:
                            if ':' in match_time_str:
                                parts = match_time_str.split(':')
                                hour = int(parts[0])
                                minute = int(parts[1])
                        except:
                            pass
                        
                        # 2. Determining Day
                        # TennisExplorer usually groups by day in headers, or lists sequential.
                        # For /next/, it starts with Today's upcoming.
                        # We will assume Today for now, and check if time is in past -> Tomorrow
                        
                        now = datetime.now()
                        match_date = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        
                        # If parsed time < now - 2hours, assume it's tomorrow (simple heuristic)
                        # (Allowing 2 hours buffer for live/ongoing matches)
                        if match_date < now - timedelta(hours=2):
                            match_date = match_date + timedelta(days=1)
                        
                        # If the page header specifically said "Tomorrow", we should respect that (todo)
                        
                        print(f"   -> Found: {p1} vs {p2} @ {match_date}")
                        

                        matches.append({
                            'player1': p1,
                            'player2': p2,
                            'tournament': current_tournament,
                            'surface': current_surface,
                            'date': match_date
                        })
                        
                        buffer_player = None # Pair consumed
                        
                    else:
                        # Buffer this as Player 1
                        buffer_player = p_name
                        buffer_time = t_text
                        
                except Exception as e:
                    # print(f"Row Parse Error: {e}")
                    buffer_player = None
                    continue
        
        return matches
    except Exception as e:
        print(f"Error scraping upcoming matches: {e}")
        return []

def run_upcoming_scraper():
    print(f"[{datetime.now()}] Starting Upcoming Matches Scraper...")
    
    db = get_db_client()
    if not db:
        print("ERROR: Supabase credentials not configured")
        return
    
    # Import the helper function
    from db_client import get_or_create_player
    
    matches = scrape_upcoming_matches()
    print(f"Found {len(matches)} upcoming matches")
    
    # DEBUG OUTPUT
    if matches:
        print("\n--- SAMPLE DATA (First 3) ---")
        for m in matches[:3]:
            print(f"{m['player1']} vs {m['player2']} | {m['tournament']} ({m['surface']}) | {m['date']}")
        print("-----------------------------\n")
    
    saved_count = 0
    table_name = 'upcoming_matches'
    
    # Check if table exists by trying to select (cheap check) or just try insert
    # If fail, fallback to 'matches'
    use_fallback = False
    try:
        # Dry run select?
        # db.from_(table_name).select('id').limit(1).execute()
        pass 
    except:
        # use_fallback = True
        pass

    for m in matches:
        try:
            # Resolve Player IDs
            p1_id = get_or_create_player(db, m['player1'])
            p2_id = get_or_create_player(db, m['player2'])
            
            if not p1_id or not p2_id:
                continue

            # Payload for upcoming_matches
            upcoming_match = {
                "player1_name": m['player1'],
                "player2_name": m['player2'],
                "player1_id": p1_id,
                "player2_id": p2_id,
                "tournament": m['tournament'],
                "surface": m['surface'],
                "match_date": m['date'].isoformat(),
                "source": "TennisExplorer"
            }
            
            # Try insert into upcoming_matches
            try:
                # Upsert by unique constraint?
                # Need to use .upsert() or check existence. 
                # Simplest is insert and ignore error or check first.
                
                # Check exist
                q = db.from_(table_name).select('id') \
                    .eq('player1_name', m['player1']) \
                    .eq('player2_name', m['player2']) \
                    .eq('match_date', upcoming_match['match_date']) \
                    .limit(1).execute()
                
                if not q.data:
                    db.from_(table_name).insert(upcoming_match).execute()
                    print(f"  [SAVED UPCOMING] {m['player1']} vs {m['player2']}")
                    saved_count += 1
                else:
                    # print(f"  [SKIP] Exists")
                    pass
                    
            except Exception as e:
                # Fallback to 'matches' table logic if upcoming_matches fails (e.g. table not found)
                if "relation" in str(e) or "does not exist" in str(e) or "404" in str(e): 
                   # print(f"  [WARN] Table {table_name} error ({e}). Fallback to 'matches'.")
                   
                   # Fallback Logic
                   db_match = {
                       "tournament_name": m['tournament'],
                       "date": m['date'].isoformat(),
                       "player1_id": p1_id,
                       "player2_id": p2_id,
                       "surface": m['surface'], # Assuming 'matches' has surface
                       "round": "Upcoming"
                   }
                   
                   # Check exist legacy
                   ex = db.from_('matches').select('id').eq('date', db_match['date']).eq('player1_id', p1_id).eq('player2_id', p2_id).limit(1).execute()
                   if not ex.data:
                       db.from_('matches').insert(db_match).execute()
                       print(f"  [SAVED LEGACY] {m['player1']} vs {m['player2']}")
                       saved_count += 1
                else:
                    print(f"  [ERR] Insert failed: {e}")

        except Exception as e:
            print(f"  [ERR] Processing match {m.get('player1')} vs {m.get('player2')}: {e}")
    
    print(f"Scraper finished. {saved_count} matches saved.")

if __name__ == "__main__":
    run_upcoming_scraper()
import os
import time
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests as http_requests
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup
from db_client import get_db_client

load_dotenv()

def scrape_upcoming_matches():
    """Scrape upcoming matches from tennis calendar"""
    url = "https://www.tennisexplorer.com/next/"
    
    try:
        response = cffi_requests.get(url, impersonate="chrome110", timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        matches = []
        # Find match tables
        tables = soup.find_all('table', class_='result')
        
        matches = []
        # Find match tables
        tables = soup.find_all('table', class_='result')
        
        for table in tables:
            rows = table.find_all('tr')
            
            buffer_player = None
            buffer_time = None
            
            for row in rows:
                if 'head' in row.get('class', []):
                    # Inspect Header
                    print(f"DEBUG HEADER: {row}") 
                    # New section/tournament often clears buffer
                    buffer_player = None
                    continue
                try:
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue
                        
                    # Extract basics
                    t_text = cells[0].get_text(strip=True) # Time
                    p_name = cells[1].get_text(strip=True) # Player Name
                    
                    # Check for scores to exclude finished/live
                    # Columns 2, 3, 4 usually scores. If they have digits, it's likely started/done.
                    # Exception: Some rows have empty scores but are just 'not started'
                    c2 = cells[2].get_text(strip=True)
                    c3 = cells[3].get_text(strip=True)
                    has_score = (c2.isdigit() or c3.isdigit())
                    
                    if has_score:
                        buffer_player = None # Reset if we hit a finished match line
                        continue
                        
                    if not p_name:
                        continue

                    if buffer_player:
                        # We have a P1 waiting, this must be P2
                        p1 = buffer_player
                        p2 = p_name
                        match_time_str = buffer_time if buffer_time else t_text
                        
                        # Set proper date
                        # TennisExplorer /next/ lists matches for "tomorrow" usually, 
                        # but check if header indicates date... (Header check is complex).
                        # Assumption: /next/ is strictly tomorrow.
                        
                        # Better Logic:
                        # If time is < current_time, it might be tomorrow (wrapping).
                        # If time is > current_time, it might be today?
                        # Actually, /next/ is usually 1 day ahead of user timezone or server timezone.
                        # Safe bet: Today + 1 day, set hours/min.
                        
                        base_date = datetime.now().date() + timedelta(days=1) # Tomorrow Date Object
                        
                        match_date = datetime(
                            year=base_date.year, 
                            month=base_date.month, 
                            day=base_date.day,
                            hour=12, minute=0
                        ) # Default noon
                        
                        try:
                            # Try to parse time HH:MM
                            if ':' in match_time_str:
                                hh, mm = map(int, match_time_str.split(':'))
                                match_date = datetime(
                                    year=base_date.year, 
                                    month=base_date.month, 
                                    day=base_date.day,
                                    hour=hh, minute=mm
                                )
                        except Exception as e:
                            # print(f"Time Parse Error: {e}")
                            pass

                        matches.append({
                            'player1': p1,
                            'player2': p2,
                            'tournament': "Upcoming", 
                            'date': match_date
                        })
                        
                        buffer_player = None # Pair consumed
                        
                    else:
                        # Buffer this as Player 1
                        buffer_player = p_name
                        buffer_time = t_text
                        
                except Exception as e:
                    print(f"Row Parse Error: {e}")
                    buffer_player = None
                    continue
        
        return matches
        
        return matches
    except Exception as e:
        print(f"Error scraping upcoming matches: {e}")
        return []

def run_upcoming_scraper():
    print(f"[{datetime.now()}] Starting Upcoming Matches Scraper...")
    
    db = get_db_client()
    
    if not db:
        print("ERROR: Supabase credentials not configured")
        return
    
    # Import the helper function
    from db_client import get_or_create_player
    
    matches = scrape_upcoming_matches()
    matches = scrape_upcoming_matches()
    print(f"Found {len(matches)} upcoming matches")
    
    if matches:
        print("\n--- SAMPLE DATA (First 3 matches) ---")
        for m in matches[:3]:
            print(json.dumps(m, default=str, indent=2))
        print("-------------------------------------\n")
    
    saved_count = 0
    for m in matches:
        try:
            # Resolve Player IDs
            p1_id = get_or_create_player(db, m['player1'])
            p2_id = get_or_create_player(db, m['player2'])
            
            if not p1_id or not p2_id:
                continue

            db_match = {
                "tournament_name": m['tournament'],
                "date": m['date'].isoformat(),
                "player1_id": p1_id,
                "player2_id": p2_id,
                "round": "Upcoming"
            }
            
            # Check if match exists
            existing = db.from_('matches').select('id').eq('date', db_match['date']).eq('player1_id', p1_id).eq('player2_id', p2_id).limit(1).execute()
            
            if not existing.data:
                db.from_('matches').insert(db_match).execute()
                print(f"  [SAVED] {m['player1']} vs {m['player2']}")
                saved_count += 1
        except Exception as e:
            print(f"  [ERR] {m.get('player1', '?')} vs {m.get('player2', '?')}: {e}")
    
    print(f"Scraper finished. {saved_count} new upcoming matches saved.")

if __name__ == "__main__":
    run_upcoming_scraper()