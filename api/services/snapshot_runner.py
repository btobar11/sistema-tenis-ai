import sys
import os
import json
from datetime import datetime, timedelta

# Add parent dir to path to find scrapers modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from scrapers.db_client import get_db_client

ODDS_FILE = 'snapshot_data/odds_input.json'
MISSING_FILE = 'snapshot_data/missing_odds.json'

def ensure_dirs():
    if not os.path.exists('snapshot_data'):
        os.makedirs('snapshot_data')

def load_odds():
    if os.path.exists(ODDS_FILE):
        try:
            with open(ODDS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def normalize_name(name):
    """Normalize player name for robust matching (e.g., 'Nadal R.' -> 'nadal r')"""
    if not name: return ""
    return name.lower().replace('.', '').strip()

def run_snapshot_process():
    print(f"[{datetime.now()}] --- Starting Snapshot Process ---")
    
    db = get_db_client()
    if not db:
        print("[ERR] Database connection failed.")
        return

    # 1. Fetch Recent Predictions
    # Using UTC window + Limit for safety as recommended
    # one_day_ago = (datetime.utcnow() - timedelta(hours=48)).isoformat()
    # print(f"Querying predictions since (UTC): {one_day_ago}")
    
    # Limit to 200 for V1 as recommended
    res_preds = db.from_('predictions').select('*').order('created_at', desc=True).limit(200).execute()
    
    if res_preds.error:
        print(f"[ERR] Failed to fetch predictions: {res_preds.error}")
        return
        
    predictions = res_preds.data
    print(f"Found {len(predictions)} recent predictions.")
    
    if not predictions:
        print("No predictions found to process.")
        return

    # 2. Get existing snapshots to avoid dupes
    # We can check by prediction_id
    # Fetching recent snapshots is safe
    one_week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    res_snaps = db.from_('prediction_snapshots').select('prediction_id').gte('created_at', one_week_ago).execute()
    existing_pred_ids = set()
    if res_snaps.data:
        existing_pred_ids = {s['prediction_id'] for s in res_snaps.data}

    # 3. Load Market Odds
    ensure_dirs()
    market_odds = load_odds()
    missing_odds = {}
    
    snaps_created = 0
    
    for p in predictions:
        pid = p['id']
        if pid in existing_pred_ids:
            continue
            
        upc_id = p.get('upcoming_match_id')
        if not upc_id:
            print(f"[WARN] Prediction {pid} has no upcoming_match_id")
            continue
            
        # Optimization: cache upcoming matches
        match_info = None
        if upc_id in upcoming_cache:
            match_info = upcoming_cache[upc_id]
        else:
            res_upc = db.from_('upcoming_matches').select('player1_name, player2_name, match_date').eq('id', upc_id).single().execute()
            if res_upc.error:
                 if "PGRST116" not in str(res_upc.error):
                     print(f"[WARN] Upcoming match {upc_id} fetch error: {res_upc.error}")
            
            if res_upc.data:
                upcoming_cache[upc_id] = res_upc.data
                match_info = res_upc.data
        
        if not match_info:
            continue
            
        p1_name = match_info['player1_name']
        p2_name = match_info['player2_name']
        
        # Robust Matching Key
        p1_norm = normalize_name(p1_name)
        p2_norm = normalize_name(p2_name)
        match_key = f"{p1_norm}__{p2_norm}" 
        
        # Check Odds
        # Also check original key for backward compatibility if needed, but simplified to normalized here
        # We might need to permit fuzzy matching or manual input key variation later.
        # Ideally, odds_input.json should use this key format.
        
        if match_key not in market_odds:
            # Fallback check for user readability or if they pasted names directly
            readable_key = f"{p1_name} vs {p2_name}"
            missing_odds[match_key] = {
                "readable": readable_key,
                "prediction_id": pid,
                "date": match_info['match_date'],
                "odds_p1": None,
                "odds_p2": None
            }
            continue
            
        odds_data = market_odds[match_key]
        odds_p1_raw = odds_data.get('odds_p1')
        odds_p2_raw = odds_data.get('odds_p2')
        
        if not odds_p1_raw:
            print(f"[SKIP] No odds values for {match_key}")
            continue

        odds_p1 = float(odds_p1_raw)
        odds_p2 = float(odds_p2_raw) if odds_p2_raw else None

        # Prepare Snapshot
        sim_p1 = float(p.get('p_match_p1') or 0)
        sim_p2 = float(p.get('p_match_p2') or 0)
        
        # Sanity Check: Probabilities
        if abs((sim_p1 + sim_p2) - 1.0) > 0.05:
            print(f"[WARN] Probabilities sum weird for {pid}: {sim_p1:.2f} + {sim_p2:.2f}")
            # Continue anyway, but logged.
            
        # Calculate Edge explicitly
        edge_p1 = (sim_p1 * odds_p1) - 1.0
        edge_p2 = (sim_p2 * odds_p2) - 1.0 if odds_p2 else -1.0
        
        # Policy: Side Taken
        side = None
        # Simple policy: > 5% edge
        if edge_p1 > 0.05: 
            side = 'P1'
        elif edge_p2 > 0.05: 
            side = 'P2'
            
        # Best Edge (Store always for analysis)
        best_edge = max(edge_p1, edge_p2)
        
        # Trust Score Clamp
        trust = p.get('confidence') 
        if trust is not None:
            try:
                trust = max(0.0, min(1.0, float(trust)))
            except:
                trust = None
        
        snapshot = {
            "upcoming_match_id": upc_id,
            "prediction_id": pid,
            "player_1": p1_name, # Store human readable in DB
            "player_2": p2_name,
            "tournament": p.get('tournament'),
            "surface": p.get('surface'),
            "match_date": match_info['match_date'],
            "model_version": p.get('model_version') or "v1",
            "engine_used": p.get('engine_used') or "unknown",
            "trust_score": trust, 
            "p_match_p1": sim_p1,
            "p_match_p2": sim_p2,
            "odds_p1": odds_p1,
            "odds_p2": odds_p2,
            "side_taken": side,
            "edge": round(best_edge, 4)
        }
        
        try:
            res_ins = db.from_('prediction_snapshots').insert(snapshot).execute()
            if not res_ins.error:
                print(f"[SNAPSHOT] Saved {p1_name} vs {p2_name} | Edge: {best_edge:.1%} (Taken: {side})")
                snaps_created += 1
            else:
                 print(f"[ERR] Snapshot insert failed: {res_ins.error}")
        except Exception as e:
            print(f"[ERR] Exception inserting snapshot: {e}")

    # Write missing file
    if missing_odds:
        print(f"\n[ATTENTION] {len(missing_odds)} matches missing odds. Writing to {MISSING_FILE}")
        with open(MISSING_FILE, 'w') as f:
            json.dump(missing_odds, f, indent=2, default=str)
        print("Please fill 'odds_p1' and 'odds_p2' in odds_input.json (copy from missing_odds.json) and re-run.")

    print(f"[{datetime.now()}] Process Complete. {snaps_created} snapshots created.")

if __name__ == "__main__":
    run_snapshot_process()
