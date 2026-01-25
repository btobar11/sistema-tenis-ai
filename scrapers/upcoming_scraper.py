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
    url = "https://www.tennisexplorer.com/matches/"
    
    try:
        response = cffi_requests.get(url, impersonate="chrome110", timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        matches = []
        # Find match tables
        tables = soup.find_all('table', class_='result')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                if 'head' in row.get('class', []):
                    continue
                try:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        # Extract match info
                        player1 = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                        player2 = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                        tournament = cells[0].get_text(strip=True) if len(cells) > 0 else "Unknown"
                        
                        # Sanity Check: detailed rows often have scores in col 2/3
                        if player1.isdigit() or player2.isdigit() or len(player1) < 2 or len(player2) < 2:
                            continue
                        
                        if player1 and player2:
                            matches.append({
                                'player1': player1,
                                'player2': player2,
                                'tournament': tournament,
                                'date': datetime.now() + timedelta(days=1)  # Tomorrow
                            })
                except Exception as e:
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