import sys
import os
import requests
import random
from datetime import datetime
# Ensure root path is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from scrapers.db_client import get_db_client

# free tier of the-odds-api allows 500 requests/month
ODDS_API_KEY = os.getenv("ODDS_API_KEY") 
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/tennis_atp/odds"

class ValueBetEngine:
    def __init__(self, db_client=None):
        self.db = db_client if db_client else get_db_client()

    def fetch_live_odds(self):
        """
        Fetches odds from API or simulates them if no key.
        """
        if not ODDS_API_KEY:
            print("  [Value] No Odds API Key found. Simulating odds data...")
            return self._simulate_odds()
        
        try:
            params = {
                'apiKey': ODDS_API_KEY,
                'regions': 'eu', # or us, uk, au
                'markets': 'h2h',
                'oddsFormat': 'decimal'
            }
            r = requests.get(ODDS_API_URL, params=params)
            if r.status_code == 200:
                return r.json()
            else:
                print(f"  [Value] API Error: {r.text}")
                return []
        except Exception as e:
            print(f"  [Value] Fetch connection error: {e}")
            return []

    def _simulate_odds(self):
        """
        Generates realistic odds for today's matches in DB.
        """
        odds_data = []
        # Get today's matches from DB to map odds to
        today = datetime.now().strftime("%Y-%m-%d")
        endpoint = f"{self.db.url}/rest/v1/matches?date=eq.{today}&select=id,player1_id,player2_id,winner_id"
        
        try:
            r = self.db._request_with_retry('get', endpoint)
            matches = r.json() if r and r.status_code == 200 else []
            
            for m in matches:
                # Random odds between 1.10 and 4.50
                # Ensure margin (vig)
                o1 = round(random.uniform(1.2, 3.0), 2)
                implied1 = 1 / o1
                vig = 0.05
                implied2 = 1 - implied1 + vig
                o2 = round(1 / implied2, 2)
                
                odds_data.append({
                    "match_id": m['id'], # Internal link
                    "bookmaker": "SimPinnacle",
                    "odds_p1": o1,
                    "odds_p2": o2
                })
        except:
            pass
        return odds_data

    def calculate_ev(self, ai_prob, bookmaker_odds):
        """
        EV = (Probability * Odds) - 1
        Returns EV percentage (e.g., 0.05 for 5%)
        """
        return (ai_prob * bookmaker_odds) - 1

    def process_value_bets(self):
        print("Starting Value Bet Analysis...")
        
        # 1. Fetch AI Predictions
        # Get matches with recent predictions
        today = datetime.now().strftime("%Y-%m-%d")
        endpoint = f"{self.db.url}/rest/v1/matches?date=gte.{today}&select=*,prediction"
        r = self.db._request_with_retry('get', endpoint)
        matches = r.json() if r else []
        
        # 2. Fetch/Simulate Odds
        market_odds = self.fetch_live_odds()
        
        value_bets = []
        
        for m in matches:
            if not m.get('prediction'): continue
            
            pred = m['prediction']
            ai_winner = pred['winner_id']
            ai_conf = pred['confidence']
            
            # Find market odds for this match
            # (In real app, fuzzy match names or map external IDs. Here using ID if simulated, or skip)
            
            # If simulated, we keyed by ID
            match_odds = next((o for o in market_odds if o.get('match_id') == m['id']), None)
            
            if match_odds:
                # Determine which odd corresponds to AI winner
                # Assuming p1/p2 mapping
                is_p1 = (ai_winner == m['player1_id'])
                decimal_odds = match_odds['odds_p1'] if is_p1 else match_odds['odds_p2']
                
                ev = self.calculate_ev(ai_conf, decimal_odds)
                
                if ev > 0.02: # 2% Edge threshold
                    print(f"  [VALUE] Match {m['id']}: AI {int(ai_conf*100)}% vs Odds {decimal_odds} => EV {round(ev*100, 1)}%")
                    
                    # Store logic here (e.g. insert to 'opportunities' table)
                    # For V1, we just return/print
                    value_bets.append({
                        "match_id": m['id'],
                        "odds": decimal_odds,
                        "ev": ev,
                        "bookmaker": match_odds['bookmaker']
                    })
                    
                    # Update DB with value data?
                    # Maybe patch prediction column or new 'value_analysis' column
                    
        return value_bets

if __name__ == "__main__":
    engine = ValueBetEngine()
    engine.process_value_bets()
