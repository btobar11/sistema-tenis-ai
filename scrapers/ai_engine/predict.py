import os
import requests
import pandas as pd
import joblib
from datetime import datetime
from dotenv import load_dotenv

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_path, '.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates" # For upsert
}

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tennis_model.pkl')

def load_ai_model():
    if not os.path.exists(MODEL_PATH):
        print("Model not found. Run training.py first.")
        return None
    return joblib.load(MODEL_PATH)

def get_player_history_rest(player_id, before_date):
    # Fetch recent history via REST
    # or=(player1_id.eq.ID,player2_id.eq.ID)
    url = f"{SUPABASE_URL}/rest/v1/matches"
    params = {
        "select": "*",
        "or": f"(player1_id.eq.{player_id},player2_id.eq.{player_id})",
        "date": f"lt.{before_date}",
        "order": "date.desc",
        "limit": 50
    }
    try:
        r = requests.get(url, headers=HEADERS, params=params)
        return r.json() if r.status_code == 200 else []
    except:
        return []

def get_h2h_rest(p1, p2, before_date):
    # or=(and(winner...loser),and(winner...loser))
    # Syntax is tricky in URL query params for complex ORs.
    # Simplify: Fetch all matches for P1 and filter in Python (since we fetch 50 anyway)
    # The get_player_history_rest already fetches P1 matches. We can just check OPPONENT in that list.
    return [] # Handled in logic below

def predict_upcoming_matches():
    print(f"[{datetime.now()}] AI Predictor (REST) Starting...")
    
    artifact = load_ai_model()
    if not artifact: return
    
    model = artifact['model']
    le_surface = artifact['surface_encoder']
    
    # 1. Fetch Scheduled Matches
    url = f"{SUPABASE_URL}/rest/v1/matches?status=eq.scheduled&select=*"
    try:
        resp = requests.get(url, headers=HEADERS)
        matches = resp.json() if resp.status_code == 200 else []
    except Exception as e:
        print(f"Error fetching matches: {e}")
        return

    print(f"Found {len(matches)} matches to predict.")
    
    predictions_made = 0
    today_iso = datetime.now().isoformat()
    
    for m in matches:
        p1 = m.get('player1_id')
        p2 = m.get('player2_id')
        if not p1 or not p2: continue
        
        surface = m.get('surface', 'Hard')
        
        # 2. Build Features
        
        # Fetch P1 history
        hist_p1 = get_player_history_rest(p1, today_iso)
        # Fetch P2 history
        hist_p2 = get_player_history_rest(p2, today_iso)
        
        def calculate_stats(history, player, opponent, surf):
            if not history: return 0.5, 0.5, 0.5
            
            # Surface WR
            s_matches = [x for x in history if x.get('surface') == surf]
            wins = len([x for x in s_matches if x.get('winner_id') == player])
            wr = wins / len(s_matches) if s_matches else 0.5
            
            # Form
            rec = history[:10]
            wins_rec = len([x for x in rec if x.get('winner_id') == player])
            form = wins_rec / len(rec) if rec else 0.5
            
            # H2H - Filter from history where opponent is opponent
            # In history, 'opponent' is not explicitly stored in matches table rows, 
            # we must infer it. A match has p1_id, p2_id.
            # If we are 'player', 'opponent' is the other one.
            # But get_player_history_rest returns row dicts.
            
            # Refine H2H logic for ID schema:
            h2h_matches = [
                x for x in history 
                if (x.get('player1_id') == opponent or x.get('player2_id') == opponent)
            ]
            wins_h2h = len([x for x in h2h_matches if x.get('winner_id') == player])
            h2h = wins_h2h / len(h2h_matches) if h2h_matches else 0.5
            
            return wr, form, h2h

        wr_a, form_a, h2h_a = calculate_stats(hist_p1, p1, p2, surface)
        wr_b, form_b, h2h_b = calculate_stats(hist_p2, p2, p1, surface)
        
        # Encode surface
        try:
            surf_enc = le_surface.transform([str(surface)])[0]
        except:
            surf_enc = 0
            
        # Feature Vector
        feats = pd.DataFrame([{
            'wr_diff': wr_a - wr_b,
            'form_diff': form_a - form_b,
            'h2h': h2h_a,
            'surface_encoded': surf_enc
        }])
        
        # Predict
        prob_win = model.predict_proba(feats)[0][1] # P1 wins
        
        # Save
        if prob_win > 0.5:
             pick = p1 # Pick ID
             # Ideally we want pick NAME. We might need to fetch it or store ID.
             # analysis_results usually stores Pick Name? 
             # Let's check schema/previous usage. "suggested_pick" usually string.
             # We can store ID for now or fetch name.
             # For speed, store ID. Or fetch.
             conf = prob_win
        else:
             pick = p2
             conf = 1 - prob_win
             
        risk = "low" if conf > 0.75 else "medium" if conf > 0.6 else "high"
        
        payload = {
            "match_id": m['id'],
            "suggested_pick": pick, # storing ID for now
            "confidence_percent": round(conf * 100, 1),
            "risk_level": risk,
            "ai_model_version": "v1_rfc_rest_syn",
            "created_at": today_iso
        }
        
        # Upsert
        u_url = f"{SUPABASE_URL}/rest/v1/analysis_results"
        requests.post(u_url, headers=HEADERS, json=payload) 
        
        predictions_made += 1
        print(f"Predicted: {pick} ({payload['confidence_percent']}%)")
        
    print(f"Done. Predicted {predictions_made} matches.")

if __name__ == "__main__":
    predict_upcoming_matches()
