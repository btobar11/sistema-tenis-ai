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
from bs4 import BeautifulSoup

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class SupabaseRestClient:
    def __init__(self, url, key):
        self.url = url
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def insert_match(self, match_data):
        endpoint = f"{self.url}/rest/v1/matches"
        try:
            # Check if match already exists
            check_endpoint = f"{self.url}/rest/v1/matches?winner_name=eq.{match_data.get('winner_name', '')}&loser_name=eq.{match_data.get('loser_name', '')}&tournament_name=eq.{match_data.get('tournament')}&select=id"
            check_response = http_requests.get(check_endpoint, headers=self.headers)
            
            if check_response.status_code == 200 and len(check_response.json()) > 0:
                return False  # Already exists
            
            r = http_requests.post(endpoint, headers=self.headers, json=match_data)
            if r.status_code in [200, 201]:
                return True
            print(f"DB Insert Error: {r.text}")
        except Exception as e:
            print(f"DB Insert Failed: {e}")
        return False

def scrape_upcoming_matches():
    """Scrape upcoming matches from tennis calendar"""
    url = "https://www.tennisexplorer.com/matches/"
    
    try:
        response = http_requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        matches = []
        # Find match tables
        tables = soup.find_all('table', class_='result')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        # Extract match info
                        player1 = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                        player2 = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                        tournament = cells[0].get_text(strip=True) if len(cells) > 0 else "Unknown"
                        
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
    
    db = SupabaseRestClient(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
    
    if not db:
        print("ERROR: Supabase credentials not configured")
        return
    
    matches = scrape_upcoming_matches()
    print(f"Found {len(matches)} upcoming matches")
    
    saved_count = 0
    for m in matches:
        db_match = {
            "tournament_name": m['tournament'],
            "date": m['date'].isoformat(),
            "player1_name": m['player1'],
            "player2_name": m['player2'],
        }
        
        if db.insert_match(db_match):
            print(f"  [SAVED] {m['player1']} vs {m['player2']}")
            saved_count += 1
    
    print(f"Scraper finished. {saved_count} new upcoming matches saved.")

if __name__ == "__main__":
    run_upcoming_scraper()
