"""
Upcoming Matches Scraper
Fetches scheduled matches for the next 7 days from tennis calendars.
"""
import os
import time
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup
try:
    from db_client import get_db_client
except ImportError:
    from scrapers.db_client import get_db_client

load_dotenv()

def scrape_date(date_obj):
    """Scrape matches for a specific date"""
    date_str = date_obj.strftime("%Y-%m-%d")
    y, m, d = date_str.split('-')
    url = f"https://www.tennisexplorer.com/matches/?type=upcoming&year={y}&month={m}&day={d}"
    print(f"Fetching {url}...")
    
    matches = []
    try:
        response = cffi_requests.get(url, impersonate="chrome110", timeout=20)
        print(f"  Status: {response.status_code}")
        soup = BeautifulSoup(response.content, 'html.parser')
        print(f"  Title: {soup.title.string if soup.title else 'No Title'}")
        
        print(f"  Response Size: {len(response.content)} bytes")
        
        tables = soup.find_all('table', class_='result')
        print(f"  Found {len(tables)} result tables.")
        
        for table in tables:
            rows = table.find_all('tr')
            current_tournament = "Unknown"
            current_surface = "HARD"
            
            # Two-row match parsing: P1 has time, P2 follows
            pending_player = None
            pending_time = None
            
            for row in rows:
                row_classes = row.get('class', [])
                cells = row.find_all('td')
                
                # Header row - extract tournament info
                if 'head' in row_classes:
                    full_text = row.get_text(strip=True)
                    if 'doubles' in full_text.lower() or 'juniors' in full_text.lower():
                        current_tournament = "SKIP"
                        continue
                        
                    links = row.find_all('a')
                    current_tournament = full_text.split(',')[0]
                    
                    for link in links:
                        link_text = link.get_text(strip=True)
                        if link_text and 'h2h' not in link_text.lower():
                            current_tournament = link_text
                            break
                    
                    # Infer Surface
                    t_lower = current_tournament.lower()
                    if 'clay' in t_lower: current_surface = 'CLAY'
                    elif 'grass' in t_lower: current_surface = 'GRASS'
                    else: current_surface = 'HARD'
                    
                    pending_player = None  # Reset on new tournament
                    continue
                    
                if current_tournament == "SKIP":
                    continue
                
                if not cells:
                    continue
                
                # Look for player link in this row
                links = row.find_all('a')
                player_links = [a for a in links if '/player/' in str(a.get('href', ''))]
                
                if not player_links:
                    continue
                    
                player_name = player_links[0].get_text(strip=True)
                if not player_name:
                    continue
                
                # Check for time in first cell  
                time_cell = cells[0].get_text(strip=True)
                time_match = re.search(r'(\d{1,2}:\d{2})', time_cell)
                
                # Check for score (completed match - skip)
                has_score = False
                for cell in cells:
                    cell_text = cell.get_text(strip=True)
                    if re.search(r'^\d+-\d+$', cell_text):
                        has_score = True
                        break
                
                if has_score:
                    pending_player = None
                    continue
                
                if time_match:
                    # This is Player 1 (row with time)
                    pending_player = player_name
                    pending_time = time_match.group(1)
                elif pending_player:
                    # This is Player 2 - complete the match
                    p1 = pending_player
                    p2 = player_name
                    
                    match_date_final = date_obj
                    if pending_time and ':' in pending_time:
                        try:
                            hh, mm = map(int, pending_time.split(':'))
                            match_date_final = date_obj.replace(hour=hh, minute=mm)
                        except: pass
                    
                    matches.append({
                        'player1': p1,
                        'player2': p2,
                        'tournament': current_tournament,
                        'surface': current_surface,
                        'date': match_date_final
                    })
                    pending_player = None
                    pending_time = None

    except Exception as e:
        print(f"Failed to scrape {date_str}: {e}")
        
    return matches

def run_upcoming_scraper():
    print(f"[{datetime.now()}] Starting Upcoming Matches Scraper...")
    
    db = get_db_client()
    if not db: return

    from db_client import get_or_create_player
    
    # Scrape Today and Tomorrow
    target_dates = [datetime.now(), datetime.now() + timedelta(days=1)]
    
    matches = []
    for d in target_dates:
        matches.extend(scrape_date(d))
        
    print(f"Found {len(matches)} upcoming matches")
    
    saved_count = 0
    
    for m in matches:
        try:
            p1_id = get_or_create_player(db, m['player1'])
            p2_id = get_or_create_player(db, m['player2'])
            
            if not p1_id or not p2_id:
                continue

            # Upsert into 'matches' table with status='scheduled'
            db_match = {
                "date": m['date'].isoformat(),
                "tournament_name": m['tournament'],
                "surface": m['surface'],
                "player1_id": p1_id,
                "player2_id": p2_id,
                "status": "scheduled",
                "round": "Upcoming"
            }
            
            # Check existing match (same players, roughly same time)
            # Use a day range or exact query?
            # We'll check for match on same day with same players
            day_str = m['date'].strftime("%Y-%m-%d")
            day_start = day_str + "T00:00:00"
            day_end = day_str + "T23:59:59"
            
            existing = db.from_('matches').select('id') \
                .eq('player1_id', p1_id) \
                .eq('player2_id', p2_id) \
                .gte('date', day_start) \
                .lte('date', day_end) \
                .limit(1).execute()
                
            if existing.data:
                # Update info if needed (e.g. time change)
                db.from_('matches').update({
                    "date": db_match['date'],
                    "status": "scheduled"
                }).eq('id', existing.data[0]['id']).execute()
            else:
                db.from_('matches').insert(db_match).execute()
                print(f"  [NEW] {m['player1']} vs {m['player2']}")
                saved_count += 1
                
        except Exception as e:
            print(f"  [ERR] {m['player1']} vs {m['player2']}: {e}")
            
    print(f"Scraper finished. {saved_count} new upcoming matches saved to 'matches'.")

if __name__ == "__main__":
    run_upcoming_scraper()