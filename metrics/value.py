import sys
import os
import requests
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Ensure root path is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

load_dotenv() # Load .env to get key

from scrapers.db_client import get_db_client

# free tier of the-odds-api allows 500 requests/month
ODDS_API_KEY = os.getenv("ODDS_API_KEY") 
# We need to handle multiple keys or specific ones. For now, let's target the active one.
# In production we might iterate over 'tennis_atp_...' keys.
SPORT_KEY = "tennis_atp_aus_open_singles"
ODDS_API_URL = f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/odds"

class ValueBetEngine:
    def __init__(self, db_client=None):
        self.db = db_client if db_client else get_db_client()

    def normalize_name(self, name):
        """
        Normalize name for comparison.
        "Novak Djokovic" -> "novak djokovic"
        "Djokovic N." -> "djokovic"
        """
        name = name.lower().strip()
        # Remove dots
        name = name.replace('.', '')
        return name

    def fuzzy_match(self, db_name, api_name):
        """
        Returns True if names likely match.
        """
        n1 = self.normalize_name(db_name)
        n2 = self.normalize_name(api_name)
        
        # Check strict substring (e.g. "djokovic" in "novak djokovic")
        if n1 in n2 or n2 in n1:
            return True
            
        # Check token intersection (e.g. "alcaraz" and "carlos alcaraz")
        t1 = set(n1.split(' '))
        t2 = set(n2.split(' '))
        if t1.intersection(t2):
            return True
            
        return False

    def fetch_active_tennis_sports(self):
        """
        Fetches list of active tennis sports/tournaments.
        """
        if not ODDS_API_KEY: return []
        try:
            url = "https://api.the-odds-api.com/v4/sports"
            params = {'apiKey': ODDS_API_KEY}
            r = requests.get(url, params=params)
            if r.status_code == 200:
                all_sports = r.json()
                # Filter for tennis keys (atp or wta)
                tennis_sports = [
                    s['key'] for s in all_sports 
                    if 'tennis' in s['key'] and s['active']
                ]
                print(f"  [Odds] Active Tennis Markets: {tennis_sports}")
                return tennis_sports
            return []
        except Exception as e:
            print(f"  [Odds] Error fetching sports: {e}")
            return []

    def fetch_live_odds(self):
        """
        Fetches odds for ALL active tennis tournaments.
        """
        if not ODDS_API_KEY:
            print("  [Value] No Odds API Key found in env.")
            return []
        
        active_sports = self.fetch_active_tennis_sports()
        if not active_sports:
            print("  [Odds] No active tennis tournaments found.")
            return []
            
        all_events = []
        
        for sport_key in active_sports:
            try:
                # Sleep briefly to avoid rate limit spikes if many tournaments
                # time.sleep(0.5) 
                
                url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
                print(f"  [Odds] Fetching: {sport_key}")
                params = {
                    'apiKey': ODDS_API_KEY,
                    'regions': 'eu,us', 
                    'markets': 'h2h',
                    'oddsFormat': 'decimal'
                }
                r = requests.get(url, params=params)
                
                # Check quota
                remaining = r.headers.get('x-requests-remaining', '?')
                # print(f"    Remaining Requests: {remaining}")
                
                if r.status_code == 200:
                    data = r.json()
                    print(f"    Found {len(data)} events.")
                    all_events.extend(data)
                else:
                    print(f"    API Error for {sport_key}: {r.text}")
                    
            except Exception as e:
                print(f"    Connection error for {sport_key}: {e}")
                
        return all_events

    def calculate_ev(self, ai_prob, bookmaker_odds):
        """
        EV = (Probability * Odds) - 1
        """
        return (ai_prob * bookmaker_odds) - 1

    def process_value_bets(self):
        print("Starting Value Bet Analysis (Real Odds)...")
        
        # 1. Fetch AI Predictions (Future matches only)
        today = datetime.now().strftime("%Y-%m-%d")
        # Fetch ID, Players, Date, Prediction
        # Also need player names joined? DB client makes this tricky with join syntax in one go if not defined.
        # But we can select logic.
        
        # Let's fetch matches with predictions
        print("  [DB] Fetching analyzed matches...")
        endpoint = f"{self.db.url}/rest/v1/matches?date=gte.{today}&select=*,prediction,player_a:player1_id(name),player_b:player2_id(name)"
        r = self.db._request_with_retry('get', endpoint)
        matches = r.json() if r and r.status_code == 200 else []
        
        if not matches:
            print("  No matches found in DB to analyze.")
            return

        print(f"  Found {len(matches)} matches to check.")

        # 2. Fetch Real Odds
        odds_events = self.fetch_live_odds()
        if not odds_events:
            print("  No odds data available.")
            return

        value_updates = 0

        for m in matches:
            if not m.get('prediction'): continue
            
            # Get Names from the JOINED columns (assuming db_client supported it or we manual fetch)
            # The query select was 'player_a:player1_id(name)'. JSON result key will be 'player_a'.
            p1_name = m.get('player_a', {}).get('name', '')
            p2_name = m.get('player_b', {}).get('name', '')
            
            if not p1_name: continue # Skip if bad data

            # Locate in Odds Data
            found_event = None
            for event in odds_events:
                # Event names: "Novak Djokovic vs. Casper Ruud" or arrays
                # The API returns 'home_team', 'away_team' usually
                # But tennis is individual.
                home = event.get('home_team')
                away = event.get('away_team')
                
                # Check match
                # p1 vs home AND p2 vs away 
                # OR p1 vs away AND p2 vs home
                # Use fuzzy match
                
                match_direct = self.fuzzy_match(p1_name, home) and self.fuzzy_match(p2_name, away)
                match_reverse = self.fuzzy_match(p1_name, away) and self.fuzzy_match(p2_name, home)
                
                if match_direct or match_reverse:
                    found_event = event
                    break
            
            if not found_event:
                # print(f"  [No Odds] Could not find odds for {p1_name} vs {p2_name}")
                continue

            # Process Bookmakers to find best odds
            rec_bet = None
            max_ev = -1
            
            ai_winner_id = m['prediction']['winner_id']
            ai_conf = m['prediction']['confidence']
            is_p1_winner = (ai_winner_id == m['player1_id'])
            
            # Determine which name matches the AI winner in the API event
            # (Does p1_name match home or away?)
            winner_in_api = None # 'home' or 'away'
            
            # Need to re-verify fuzzy match to know side
            if self.fuzzy_match(p1_name, found_event['home_team']):
                winner_in_api = 'home' if is_p1_winner else 'away'
            else:
                # p1 is away
                winner_in_api = 'away' if is_p1_winner else 'home'

            for bookmaker in found_event.get('bookmakers', []):
                # We prioritize reputable ones or just max? Let's take MAX for now.
                for market in bookmaker.get('markets', []):
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            # outcome['name'] matches home_team or away_team
                            
                            # Check if outcome is our winner
                            # outcome['name'] vs found_event['home_team']
                             
                            is_target = False
                            if winner_in_api == 'home' and outcome['name'] == found_event['home_team']:
                                is_target = True
                            elif winner_in_api == 'away' and outcome['name'] == found_event['away_team']:
                                is_target = True
                                
                            if is_target:
                                odds = outcome['price']
                                ev = self.calculate_ev(ai_conf, odds)
                                
                                # Is this the best EV so far?
                                if ev > max_ev and ev > 0.0:
                                    max_ev = ev
                                    rec_bet = {
                                        "selection": p1_name if is_p1_winner else p2_name,
                                        "odds": odds,
                                        "bookmaker": bookmaker['title'],
                                        "ev": ev,
                                        "timestamp": datetime.now().isoformat()
                                    }

            if rec_bet and max_ev > 0.01: # 1% threshold
                print(f"  [VALUE FOUND] {rec_bet['selection']} @ {rec_bet['odds']} ({rec_bet['bookmaker']}) | EV: {round(max_ev*100, 1)}%")
                
                # Update DB prediction JSON with value data
                current_pred = m['prediction']
                current_pred['value_bet'] = rec_bet # Inject
                
                # Patch DB
                self.db.from_('matches').update({
                    "prediction": current_pred
                }).eq('id', m['id']).execute()
                
                value_updates += 1

        print(f"Analysis complete. Updated {value_updates} matches with value data.")

if __name__ == "__main__":
    load_dotenv()
    engine = ValueBetEngine()
    engine.process_value_bets()
