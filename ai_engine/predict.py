
import os
import sys
import json
from datetime import datetime

# Ensure root path is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from scrapers.db_client import get_db_client

import os
import sys
import json
from datetime import datetime

# Ensure root path is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from scrapers.db_client import get_db_client

class StatsEngine:
    def __init__(self, db):
        self.db = db

    def get_player_recent_form(self, player_id, limit=5):
        """
        Fetch last N matches for a player to calculate win rate.
        """
        try:
            # We need to query matches where player was p1 OR p2 involved. 
            # Supabase REST doesn't support thorough OR queries easily in one GET param 
            # without complex syntax or RPC.
            # Simplified: Query where player1_id = X, then player2_id = X, separate calls or complex filter.
            # "or=(player1_id.eq.X,player2_id.eq.X)" is supported in postgrest syntax.
            
            query = f"or=(player1_id.eq.{player_id},player2_id.eq.{player_id})"
            # We want completed matches (winner_id not null)
            # order by date desc
            endpoint = f"{self.db.url}/rest/v1/matches?select=*&{query}&winner_id=not.is.null&order=date.desc&limit={limit}"
            
            r = self.db._request_with_retry('get', endpoint)
            if r and r.status_code == 200:
                matches = r.json()
                wins = 0
                for m in matches:
                    if m.get('winner_id') == player_id:
                        wins += 1
                return {
                    "matches_played": len(matches),
                    "wins": wins,
                    "win_rate": (wins / len(matches)) if matches else 0.0,
                    "streak_data": [1 if m.get('winner_id') == player_id else 0 for m in matches]
                }
        except Exception as e:
            print(f"  [Stats] Form error for {player_id}: {e}")
        return {"matches_played": 0, "wins": 0, "win_rate": 0.0, "streak_data": []}

    def get_h2h_stats(self, p1_id, p2_id):
        """
        Fetch past matches between p1 and p2.
        """
        try:
            # (p1=A AND p2=B) OR (p1=B AND p2=A)
            # Syntax: or=(and(player1_id.eq.A,player2_id.eq.B),and(player1_id.eq.B,player2_id.eq.A))
            # Escaping might be tricky via raw string. 
            # Simplified check: just fetch matches with p1_id=A and filter in python for p2=B? 
            # DB side is better.
            
            complex_filter = f"or=(and(player1_id.eq.{p1_id},player2_id.eq.{p2_id}),and(player1_id.eq.{p2_id},player2_id.eq.{p1_id}))"
            endpoint = f"{self.db.url}/rest/v1/matches?select=*&{complex_filter}&winner_id=not.is.null"
            
            r = self.db._request_with_retry('get', endpoint)
            if r and r.status_code == 200:
                matches = r.json()
                p1_wins = 0
                for m in matches:
                    if m.get('winner_id') == p1_id:
                        p1_wins += 1
                return {
                    "total": len(matches),
                    "p1_wins": p1_wins,
                    "p2_wins": len(matches) - p1_wins
                }
        except Exception as e:
            print(f"  [Stats] H2H error: {e}")
        return {"total": 0, "p1_wins": 0, "p2_wins": 0}

    def predict_match(self, match):
        p1 = match['player1_id']
        p2 = match['player2_id']
        
        # 1. H2H
        h2h = self.get_h2h_stats(p1, p2)
        
        # 2. Form
        form_p1 = self.get_player_recent_form(p1)
        form_p2 = self.get_player_recent_form(p2)
        
        # 3. Scoring
        score_p1 = 0.5 # start even
        
        reasoning = []
        
        # Weight: H2H (30%)
        if h2h['total'] > 0:
            h2h_rate = h2h['p1_wins'] / h2h['total']
            diff = h2h_rate - 0.5
            score_p1 += (diff * 0.3)
            reasoning.append(f"H2H: P1 has {h2h['p1_wins']} wins in {h2h['total']} matches.")
        else:
            reasoning.append("H2H: No past matches.")
            
        # Weight: Recent Form (40%)
        # Compare win rates
        form_diff = form_p1['win_rate'] - form_p2['win_rate']
        score_p1 += (form_diff * 0.4)
        
        reasoning.append(f"Form: P1 {int(form_p1['win_rate']*100)}% ({form_p1['wins']}/{form_p1['matches_played']}) vs P2 {int(form_p2['win_rate']*100)}% ({form_p2['wins']}/{form_p2['matches_played']}).")
        
        # Clamp
        score_p1 = max(0.1, min(0.9, score_p1))
        
        predicted_winner = p1 if score_p1 >= 0.5 else p2
        confidence = score_p1 if score_p1 >= 0.5 else (1.0 - score_p1)
        
        return {
            "winner_id": predicted_winner,
            "confidence": round(confidence, 2),
            "model_version": "v1.0-stats-engine",
            "timestamp": datetime.now().isoformat(),
            "reasoning": " | ".join(reasoning),
            "metrics": {
                "h2h": h2h,
                "form_p1": form_p1,
                "form_p2": form_p2
            }
        }

def predict_upcoming_matches():
    print(f"[{datetime.now()}] AI Engine: Starting advanced prediction cycle...")
    
    db = get_db_client()
    if not db:
        print("  [AI] DB Connection failed.")
        return
    
    engine = StatsEngine(db)

    try:
        # Fetch matches where prediction is NULL
        # And date >= today
        today = datetime.now().strftime("%Y-%m-%d")
        endpoint = f"{db.url}/rest/v1/matches?date=gte.{today}&select=id,player1_id,player2_id,prediction&prediction=is.null"
        
        r = db._request_with_retry('get', endpoint)
        if not r or r.status_code != 200:
            print(f"  [AI] Could not fetch matches: {r.text if r else 'No response'}")
            return
            
        matches = r.json()
        print(f"  [AI] Found {len(matches)} matches needing prediction.")
        
        for m in matches:
            print(f"  Predicting Match {m['id']}...")
            prediction = engine.predict_match(m)
            
            # Save Prediction
            patch_endpoint = f"{db.url}/rest/v1/matches?id=eq.{m['id']}"
            r_patch = db._request_with_retry('patch', patch_endpoint, json={"prediction": prediction})
            
            if r_patch and r_patch.status_code in [200, 204]:
                print(f"    -> Predicted Winner: {prediction['winner_id']} (Conf: {prediction['confidence']})")
            else:
                print(f"    -> Update Failed: {r_patch.text if r_patch else 'No resp'}")
                
    except Exception as e:
        print(f"  [AI] Critical Error: {e}")

if __name__ == "__main__":
    predict_upcoming_matches()
