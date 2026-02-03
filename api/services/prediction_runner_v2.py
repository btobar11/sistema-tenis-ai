import sys
import os
sys.path.append(os.getcwd())

import pandas as pd
from datetime import datetime, timedelta
from scrapers.db_client import get_db_client
from api.services.inference_service import InferenceService

class PredictionRunner:
    def __init__(self):
        self.db = get_db_client()
        self.inference = InferenceService()

    def run_upcoming(self):
        print(f"[{datetime.now()}] Starting Prediction Cycle (V2)...")
        
        # 1. Fetch Upcoming Matches
        # Ensure we have matches to predict
        res = self.db.from_('upcoming_matches').select('*').execute()
        matches = res.data
        if not matches:
            print("No upcoming matches found.")
            return

        print(f"Processing {len(matches)} matches...")
        
        count = 0
        for match in matches:
            try:
                # 2. Check Deduplication
                # Avoid re-predicting if valid snapshot exists (< 6 hours)
                # (Simple check: query predictions for this ID created > now - 6h)
                
                # For now, simplistic approach: just predict.
                # In prod, we'd query DB.
                # existing = self.db.from_('predictions').select('id').eq('upcoming_match_id', match['id']).gt('created_at', (datetime.now() - timedelta(hours=6)).isoformat()).execute()
                # if existing.data: continue
                
                # 3. Validation
                if not match.get('player1_id') or not match.get('player2_id'):
                    # print(f"Skipping {match['player1_name']} vs {match['player2_name']} (No IDs)")
                    continue
                    
                # 4. Predict
                result = self.inference.predict_matchup(
                    p1_id=match['player1_id'],
                    p2_id=match['player2_id'],
                    surface=match.get('surface', 'HARD').upper()
                )
                
                # 5. Extract Data
                # Unpack result from InferenceService
                metrics = result['metrics']
                p_serve_p1 = metrics['p_serve_p1']
                p_serve_p2 = metrics['p_serve_p2']
                
                sim_win = metrics['simulated_p_win'] # P1 win prob
                
                markets = result.get('markets', {})
                sets = markets.get('sets', {})
                p_2_0 = sets.get('2-0', 0)
                p_2_1 = sets.get('2-1', 0)
                
                # Stats
                avg_games = markets.get('total_games', {}).get('mean', 0.0)
                
                # Trust Metrics
                confidence = result.get('confidence', 0.5)
                engine_reason = result.get('engine_reason', 'unknown')
                trust_details = result.get('trust_details', {})
                dq_score = trust_details.get('dq', 0)
                ss_score = trust_details.get('ss', 0)
                
                # 6. Sanity Checks (Pre-Insert)
                if not (0.52 <= p_serve_p1 <= 0.75) or not (0.52 <= p_serve_p2 <= 0.75):
                    print(f"  [WARN] Sanity check failed for {match['player1_name']}: {p_serve_p1:.2f}/{p_serve_p2:.2f}")
                    # Skip or flag? Skip for safety in V1.
                    continue
                    
                # 7. Insert Snapshot
                # MINIMAL PAYLOAD TEST (Step 1064)
                payload = {
                    "upcoming_match_id": match['id'],
                    "model_version": "xgb_service_v1", 
                    "p_match_p1": sim_win,
                    "p_match_p2": 1.0 - sim_win,
                }
                
                print(f"DEBUG PAYLOAD: {payload}")
                req = self.db.from_('predictions').insert(payload)
                # WORKAROUND: Force return=minimal to avoid Schema Cache error on response serialization
                req.headers['Prefer'] = 'return=minimal'
                res_ins = req.execute()
                
                if res_ins.error:
                    print(f"  [DB ERR] Insert failed: {res_ins.error}")
                else:
                    print(f"  [PREDICTED] {match['player1_name']} vs {match['player2_name']} | Win: {sim_win:.1%} | Trust: {confidence:.2f}")
                    count += 1
                
            except Exception as e:
                print(f"  [ERR] Prediction failed for match {match.get('id')}: {e}")
                
        print(f"Cycle Complete. Generated {count} predictions.")

if __name__ == "__main__":
    runner = PredictionRunner()
    runner.run_upcoming()
