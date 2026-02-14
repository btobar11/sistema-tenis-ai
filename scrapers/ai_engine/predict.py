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
    # Try to download from Supabase Storage first (Cloud environment support)
    try:
        from supabase import create_client, Client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Attempting to download 'tennis_model.pkl' from Supabase Storage...")
        
        # Download returns bytes
        res = supabase.storage.from_("ai_models").download("tennis_model.pkl")
        
        # Save to local path so joblib can load it
        with open(MODEL_PATH, 'wb') as f:
            f.write(res)
        print("Model downloaded successfully.")
    except Exception as e:
        print(f"Info: Could not download model from cloud ({e}). Using local file if exists.")

    if not os.path.exists(MODEL_PATH):
        print("CRITICAL: Model not found locally or in cloud. Run training.py first.")
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

    return [] # Handled in logic below

def predict_matches(start_date=None, status_filter='scheduled'):
    print(f"[{datetime.now()}] AI Predictor (REST) Starting... Date: {start_date or 'Today'}, Status: {status_filter or 'All'}")
    
    artifact = load_ai_model()
    if not artifact: return
    
    model = artifact['model']
    le_surface = artifact['surface_encoder']
    
    # 1. Fetch Matches
    url = f"{SUPABASE_URL}/rest/v1/matches"
    
    # Default to today if not provided
    target_date = start_date or datetime.now().strftime("%Y-%m-%d")
    
    params = {
        "date": f"gte.{target_date}", 
        "select": "*"
    }
    
    # Apply status filter if provided (pass None to fetch all statuses)
    if status_filter:
        params['status'] = f"eq.{status_filter}"
        
    try:
        resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code == 200:
            matches = resp.json()
            if not matches:
                print(f"[DEBUG] Fetch successful but 0 matches found.")
        else:
            print(f"[ERROR] Fetch failed. Status: {resp.status_code}")
            matches = []
    except Exception as e:
        print(f"[ERROR] Exception fetching matches: {e}")
        return

    print(f"Found {len(matches)} matches to predict.")
    
    predictions_made = 0
    today_iso = datetime.now().isoformat()
    
    for m in matches:
        p1 = m.get('player1_id')
        p2 = m.get('player2_id')
        if not p1 or not p2: continue
        
        # Check if analysis already exists? 
        # For backfill, we might want to overwrite or skip.
        # Current logic upserts, which is fine.
        
        surface = m.get('surface', 'Hard')
        match_date = m.get('date').split('T')[0] # Extract YYYY-MM-DD for history filter
        
        # 2. Build Features
        
        # Fetch P1 history BEFORE this match
        hist_p1 = get_player_history_rest(p1, match_date)
        # Fetch P2 history BEFORE this match
        hist_p2 = get_player_history_rest(p2, match_date)
        
        # ... (rest of feature calc is same) ...
        # Copied helper function here to ensure scope access if not global
        def calculate_stats(history, player, opponent, surf):
            if not history: return 0.5, 0.5, 0.5
            
            # Helper to check if player won
            def did_win(match_row, pid):
                if match_row.get('winner_id') == pid: return True
                return False

            # Surface WR
            s_matches = [x for x in history if x.get('surface') == surf]
            wins = len([x for x in s_matches if did_win(x, player)])
            wr = wins / len(s_matches) if s_matches else 0.5
            
            # Form (Last 10)
            rec = history[:10]
            wins_rec = len([x for x in rec if did_win(x, player)])
            form = wins_rec / len(rec) if rec else 0.5
            
            # H2H 
            params_h2h = [
                x for x in history 
                if (x.get('player1_id') == opponent or x.get('player2_id') == opponent)
            ]
            wins_h2h = len([x for x in params_h2h if did_win(x, player)])
            h2h = wins_h2h / len(params_h2h) if params_h2h else 0.5
            
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
        try:
            prob_win_p1 = model.predict_proba(feats)[0][1] # Probability P1 wins
        except:
            prob_win_p1 = 0.5
        
        # Determine Pick & Confidence
        if prob_win_p1 > 0.5:
             pick_id = p1
             conf = prob_win_p1
        else:
             pick_id = p2
             conf = 1.0 - prob_win_p1
             
        if conf == 0.5: conf = 0.51 
             
        risk = "low" if conf > 0.75 else "medium" if conf > 0.6 else "high"
        
        payload = {
            "match_id": m['id'],
            "suggested_pick": pick_id, 
            "confidence_percent": round(conf * 100, 1),
            "risk_level": risk,
            "ai_model_version": "v2_rf_live",
            "trust_score": round(conf * 100, 1), 
            "created_at": today_iso
        }
        
        # Upsert Analysis
        u_url = f"{SUPABASE_URL}/rest/v1/analysis_results"
        requests.post(u_url, headers=HEADERS, json=payload) 
        
        predictions_made += 1
        # Debug helper
        p1_name = m.get('player1_name') or m.get('id')
        p2_name = m.get('player2_name') or m.get('id')
        print(f"Predicted: {p1_name} vs {p2_name} -> Pick: {pick_id} ({payload['confidence_percent']}%)")
        
    print(f"Done. Predicted {predictions_made} matches.")

if __name__ == "__main__":
    predict_matches()
