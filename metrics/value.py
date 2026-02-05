
# Rewritten ValueBetEngine
import sys
import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

load_dotenv()
from scrapers.db_client import get_db_client

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

class ValueBetEngine:
    def __init__(self, db_client=None):
        self.db = db_client if db_client else get_db_client()
        self.players_map = {}

    def get_player_name(self, p_id):
        if not self.players_map:
            # Cache all players for speed
            try:
                r = self.db._request_with_retry('get', f"{self.db.url}/rest/v1/players?select=id,name")
                if r and r.json():
                    self.players_map = {p['id']: p['name'] for p in r.json()}
            except:
                pass
        return self.players_map.get(p_id, "Unknown")

    def fetch_active_tennis_sports(self):
        if not ODDS_API_KEY: return []
        try:
            url = "https://api.the-odds-api.com/v4/sports"
            params = {'apiKey': ODDS_API_KEY}
            r = requests.get(url, params=params)
            if r.status_code == 200:
                all = r.json()
                return [s['key'] for s in all if 'tennis' in s['key'] and s['active']]
        except Exception as e:
            print(f"[Odds] Error: {e}")
        return []

    def fetch_live_odds(self):
        if not ODDS_API_KEY:
            print("[Value] Missing ODDS_API_KEY")
            return []
        
        sports = self.fetch_active_tennis_sports()
        all_events = []
        for s in sports:
            try:
                url = f"https://api.the-odds-api.com/v4/sports/{s}/odds"
                params = {'apiKey': ODDS_API_KEY, 'regions': 'eu,us', 'markets': 'h2h', 'oddsFormat': 'decimal'}
                r = requests.get(url, params=params)
                if r.status_code == 200:
                    events = r.json()
                    print(f"  [Odds] {s}: Found {len(events)} events.")
                    all_events.extend(events)
            except:
                pass
        return all_events
        
    def normalize(self, name):
        return name.lower().replace('.', '').strip()

    def fuzzy_match(self, db_name, api_name):
        n1 = self.normalize(db_name)
        n2 = self.normalize(api_name)
        if n1 in n2 or n2 in n1: return True
        t1 = set(n1.split())
        t2 = set(n2.split())
        if t1.intersection(t2): return True
        return False

    def process_value_bets(self):
        print("Starting Value Bet Analysis...")
        
        # 1. Get recent Predictions from analysis_results
        # Join with matches to get Match Info? Or Matches -> JOIN analysis_results?
        # Let's get Matches JOIN analysis_results because we need match date/players
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # We need matches that have a prediction
        # Query: matches?select=*,analysis_results(*)&status=eq.scheduled
        
        endpoint = f"{self.db.url}/rest/v1/matches"
        params = {
            "date": f"gte.{today}",
            "select": "*,analysis_results(*)"
        }
        
        try:
            r = self.db._request_with_retry('get', endpoint, params=params)
            matches = r.json() if r and r.status_code == 200 else []
        except Exception as e:
            print(f"[Value] DB Error: {e}")
            return

        matches_with_preds = [m for m in matches if m.get('analysis_results')]
        print(f"  Found {len(matches_with_preds)} scheduled matches with predictions.")
        
        if not matches_with_preds:
            return

        # 2. Fetch Odds
        odds_events = self.fetch_live_odds()
        if not odds_events:
            print("  No odds data found.")
            return
            
        updates = 0
        
        for m in matches_with_preds:
            # m['analysis_results'] is likely a list (one-to-many) or dict (one-to-one) depending on schema
            # Assuming list, take latest
            preds = m['analysis_results']
            if isinstance(preds, list):
                if not preds: continue
                pred = preds[0] # Take first/latest
            else:
                pred = preds
                
            p1_name = self.get_player_name(m['player1_id'])
            p2_name = self.get_player_name(m['player2_id'])
            
            # Find in Odds
            found = None
            for ev in odds_events:
                home = ev.get('home_team')
                away = ev.get('away_team')
                
                # Check direct
                if (self.fuzzy_match(p1_name, home) and self.fuzzy_match(p2_name, away)) or \
                   (self.fuzzy_match(p1_name, away) and self.fuzzy_match(p2_name, home)):
                    found = ev
                    break
            
            if found:
                # Calculate EV
                ai_pick_id = pred.get('suggested_pick')
                ai_conf = pred.get('confidence_percent', 50) / 100.0
                
                is_p1_pick = (ai_pick_id == m['player1_id'])
                pick_name = p1_name if is_p1_pick else p2_name
                
                # Determine side in API
                # Basic check: if p1 matches home, then home is p1
                p1_is_home = self.fuzzy_match(p1_name, found['home_team'])
                
                target_outcome_name = found['home_team'] if (is_p1_pick and p1_is_home) or (not is_p1_pick and not p1_is_home) else found['away_team']
                
                best_ev = -1
                best_bet = None
                
                for bookie in found.get('bookmakers', []):
                    for market in bookie.get('markets', []):
                        if market['key'] == 'h2h':
                            for out in market['outcomes']:
                                if out['name'] == target_outcome_name:
                                    decimal_odds = out['price']
                                    ev = (ai_conf * decimal_odds) - 1
                                    
                                    if ev > 0 and ev > best_ev:
                                        best_ev = ev
                                        best_bet = {
                                            "bookmaker": bookie['title'],
                                            "odds": decimal_odds,
                                            "ev": round(ev, 3),
                                            "pick": pick_name
                                        }
                
                if best_bet:
                    print(f"  [VALUE] {pick_name} vs {p2_name if is_p1_pick else p1_name} | {best_bet['bookmaker']} @ {best_bet['odds']} (EV: {best_bet['ev']})")
                    
                    # Update analysis_results with value bet
                    # We need to PATCH analysis_results
                    try:
                        patch_url = f"{self.db.url}/rest/v1/analysis_results"
                        self.db._request_with_retry('patch', patch_url, 
                            params={'id': f"eq.{pred['id']}"},
                            json={"value_bet_data": best_bet}
                        )
                        updates += 1
                    except Exception as e:
                        print(f"Error saving value bet: {e}")

        print(f"Value Analysis Done. {updates} value bets recorded.")

if __name__ == "__main__":
    engine = ValueBetEngine()
    engine.process_value_bets()
