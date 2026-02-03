import os
import sys
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# Add root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.db_client import get_db_client
from ai_engine.score_inference import infer_p_serve

MODEL_PATH = "ml/models/xgb_service_v1.joblib"
os.makedirs("ml/models", exist_ok=True)

class ServiceProbTrainingPipeline:
    def __init__(self):
        self.db = get_db_client()

    def fetch_data(self):
        print("1. Fetching Match Data (Score-Based)...")
        cols = "id, date, surface, score_full, winner_id, player1_id, player2_id"
        res = self.db.from_('matches').select(cols).execute()
        matches_df = pd.DataFrame(res.data)
        
        if matches_df.empty: return None
        
        # Fetch Players for Rank
        print("   Fetching Players Ranks...")
        p_res = self.db.from_('players').select('id, rank').execute()
        
        if not p_res.data:
            print("   [WARN] No players returned. Using dummy ranks.")
            matches_df['p1_rank'] = 999
            matches_df['p2_rank'] = 999
        else:
            players_df = pd.DataFrame(p_res.data)
            
            # Ensure columns exist
            if 'id' not in players_df.columns:
                 # Should not happen if data is list of dicts
                 print("   [ERR] Player data missing 'id'.")
                 matches_df['p1_rank'] = 999
                 matches_df['p2_rank'] = 999
            else:
                if 'rank' not in players_df.columns: players_df['rank'] = 999
                
                players_df['rank'] = pd.to_numeric(players_df['rank'], errors='coerce').fillna(999)
                rank_map = players_df.set_index('id')['rank'].to_dict()
                matches_df['p1_rank'] = matches_df['player1_id'].map(rank_map).fillna(999)
                matches_df['p2_rank'] = matches_df['player2_id'].map(rank_map).fillna(999)
        
        # Date conversions
        matches_df['date'] = pd.to_datetime(matches_df['date'], format='ISO8601').dt.tz_localize(None)
        matches_df = matches_df.sort_values('date')
        
        return matches_df

    def engineer_features(self, df):
        print("2. Feature Engineering & Target Inference...")
        
        final_data = []
        skipped_count = 0
        
        for idx, row in df.iterrows():
            score = row.get('score_full')
            if not score:
                skipped_count += 1
                continue
                
            try:
                ps_w, ps_l = infer_p_serve(score)
            except:
                ps_w, ps_l = None, None
                
            if ps_w is None:
                skipped_count += 1
                continue
                
            surf = row.get('surface', 'HARD')
            if not surf: surf = 'HARD'
            surf_code = 1 if 'CLAY' in surf.upper() else (2 if 'GRASS' in surf.upper() else 0)
            
            weight = 1.0 if len(score) > 10 else 0.8
            
            # Ranks
            p_won = row['winner_id']
            p1_id = row['player1_id']
            p2_id = row['player2_id']
            
            r1 = row['p1_rank']
            r2 = row['p2_rank']
            
            # Winner Rank / Loser Rank logic
            if p_won == p1_id:
                winner_rank = r1
                loser_rank = r2
            else:
                winner_rank = r2
                loser_rank = r1
            
            # Log Rank Diff: log2(OppRank) - log2(MyRank)
            # Higher is better for 'Me'
            def get_log_diff(my_r, opp_r):
                # Clamp ranks to 1-1000
                mr = max(1, min(1000, my_r))
                or_ = max(1, min(1000, opp_r))
                return np.log2(or_) - np.log2(mr)
                
            diff_winner = get_log_diff(winner_rank, loser_rank)
            diff_loser = get_log_diff(loser_rank, winner_rank)
            
            # Row 1: Winner
            final_data.append({
                'surface_code': surf_code,
                'rank_diff': diff_winner,
                'target': ps_w,
                'weight': weight
            })
            
            # Row 2: Loser
            final_data.append({
                'surface_code': surf_code,
                'rank_diff': diff_loser,
                'target': ps_l,
                'weight': weight
            })
            
        print(f"   Generated {len(final_data)} training samples.")
        return pd.DataFrame(final_data)

    def train(self, df):
        print("3. Training XGB Regressor (Rank-Based)...")
        if df is None or df.empty: return

        split_idx = int(len(df) * 0.8)
        train_df = df.iloc[:split_idx]
        test_df = df.iloc[split_idx:]
        
        features = ['surface_code', 'rank_diff']
        target = 'target'
        
        # Check Feature Correlation
        corr = df[['rank_diff', 'target']].corr().iloc[0,1]
        print(f"   Correlation RankDiff vs P(Serve): {corr:.3f}")
        
        model = XGBRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=3,
            objective='reg:squarederror'
        )
        
        model.fit(train_df[features], train_df[target], sample_weight=train_df['weight'])
        
        preds = model.predict(test_df[features])
        mae = mean_absolute_error(test_df[target], preds)
        
        print(f"   MAE: {mae:.4f}")
        joblib.dump(model, MODEL_PATH)
        print("   Model V1 (Score+Rank) Saved.")

if __name__ == "__main__":
    pipeline = ServiceProbTrainingPipeline()
    raw = pipeline.fetch_data()
    if raw is not None:
        engineered = pipeline.engineer_features(raw)
        pipeline.train(engineered)
