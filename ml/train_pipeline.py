import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, log_loss
from sklearn.calibration import CalibratedClassifierCV, calibration_curve

# Add root to system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.db_client import get_db_client

MODEL_PATH = "ml/models/xgb_v1.joblib"
os.makedirs("ml/models", exist_ok=True)

class MLPipeline:
    def __init__(self):
        self.db = get_db_client()
        if not self.db:
            raise Exception("DB Client failed")

    def fetch_data(self):
        print("1. Fetching Match History...")
        endpoint = f"{self.db.url}/rest/v1/matches?select=*,player_a:player1_id(name,rank_single),player_b:player2_id(name,rank_single)&order=date.asc"
        r = self.db._request_with_retry('get', endpoint)
        if not r or r.status_code != 200:
            raise Exception("Failed to fetch data")
        
        df = pd.DataFrame(r.json())
        # Handle various date formats from different scrapers
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        # Drop rows with invalid dates if any
        df = df.dropna(subset=['date']).sort_values('date')
        print(f"   Loaded {len(df)} matches.")
        return df

    def feature_engineering(self, df):
        print("2. Feature Engineering (Rolling Window)...")
        # Initialize containers for calculated features
        # We must iterate chronologically to avoid leakage
        
        # State trackers
        elo_state = {} 
        form_state = {} # {player_id: [last_5_results]}
        
        features = []
        
        for idx, row in df.iterrows():
            p1 = row['player1_id']
            p2 = row['player2_id']
            winner = row['winner_id']
            date = row['date']
            
            # --- Get Pre-Match Features (Snapshot) ---
            
            # ELO (Default 1500 if new)
            elo1 = elo_state.get(p1, 1500)
            elo2 = elo_state.get(p2, 1500)
            
            # Form (Win % last 5)
            # Calculate from list
            f1_hist = form_state.get(p1, [])
            f2_hist = form_state.get(p2, [])
            
            form1 = sum(f1_hist)/len(f1_hist) if f1_hist else 0.5
            form2 = sum(f2_hist)/len(f2_hist) if f2_hist else 0.5
            
            # Rank
            # Usually we assume rank is in the row from scraper, if not found use 999
            rank1 = 999 
            rank2 = 999
            # Try to parse rank if available in player_a object (joined)
            if 'player_a' in row and isinstance(row['player_a'], dict):
                rank1 = row['player_a'].get('rank_single') or 999
            if 'player_b' in row and isinstance(row['player_b'], dict):
                rank2 = row['player_b'].get('rank_single') or 999
            
            # Target
            # We predict if Player 1 wins.
            label = 1 if winner == p1 else 0
            
            # Store Feature Row
            features.append({
                'elo_diff': elo1 - elo2,
                'form_diff': form1 - form2,
                'rank_diff': (rank2 - rank1), # Higher rank is lower number, so (20 - 10) = +10 diff for P1? No.
                                              # If P1 is #10 and P2 is #50. P1 is better.
                                              # Diff = 50 - 10 = 40. Positive Rank Diff means P1 is better.
                'elo_p1': elo1,
                'elo_p2': elo2,
                'target': label
            })
            
            # --- Post-Match State Update (Learning) ---
            
            # ELO Update
            expected1 = 1 / (1 + 10 ** ((elo2 - elo1) / 400))
            score1 = 1 if label == 1 else 0
            k = 32
            
            new_elo1 = elo1 + k * (score1 - expected1)
            new_elo2 = elo2 + k * ((1-score1) - (1-expected1))
            
            elo_state[p1] = new_elo1
            elo_state[p2] = new_elo2
            
            # Form Update
            f1_hist.append(1 if label == 1 else 0)
            f2_hist.append(1 if label == 0 else 0)
            
            # Keep only last 5
            form_state[p1] = f1_hist[-5:]
            form_state[p2] = f2_hist[-5:]
            
        feat_df = pd.DataFrame(features)
        print(f"   Generated {len(feat_df)} training rows.")
        return feat_df

    def train_model(self, df):
        print("3. Training XGBoost Model with Probability Calibration (Platt Scaling)...")
        if df.empty:
            print("   No data to train.")
            return

        X = df.drop(columns=['target'])
        y = df['target']
        
        # Split: Train (60%), Calibration (20%), Test (20%)
        # Or simpler: Cross-Validation Calibration (method='sigmoid' aka Platt)
        # Using 5-fold CV for calibration uses all data more efficiently.
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        base_model = XGBClassifier(
            n_estimators=200, 
            learning_rate=0.05, 
            max_depth=6,
            eval_metric='logloss'
        )
        
        # Fit base model first (needed if not using CV inside CalibratedClassifier, 
        # but CalibratedClassifierCV(cv=5) handles it)
        # Note: XGBoost early stopping requires eval set. Simplest way with Calibration is:
        # 1. Fit Base
        # 2. Calibrate on separate set OR use CalibratedClassifierCV(cv=5) which fits 5 models.
        
        # Let's use CalibratedClassifierCV with prefit=False (Default) and cv=3
        print("   Fitting Calibrated Classifier (CV=3)...")
        calibrated_model = CalibratedClassifierCV(base_model, method='sigmoid', cv=3)
        calibrated_model.fit(X_train, y_train)
        
        # Eval
        preds = calibrated_model.predict(X_test)
        probs = calibrated_model.predict_proba(X_test)[:, 1]
        acc = accuracy_score(y_test, preds)
        loss = log_loss(y_test, probs)
        
        print(f"   Calibrated Accuracy: {acc:.4f}")
        print(f"   Calibrated Log Loss: {loss:.4f}")
        
        # Feature importance is tricky with Wrapper. We can inspect one of the estimators.
        try:
            base_est = calibrated_model.calibrated_classifiers_[0].estimator
            print("   Feature Importance (from Fold 1):")
            imps = dict(zip(X.columns, base_est.feature_importances_))
            for k, v in sorted(imps.items(), key=lambda x: x[1], reverse=True):
                print(f"     - {k}: {v:.4f}")
        except:
            pass
            
        # Save
        joblib.dump(calibrated_model, MODEL_PATH)
        print(f"   Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    pipeline = MLPipeline()
    raw_df = pipeline.fetch_data()
    train_df = pipeline.feature_engineering(raw_df)
    pipeline.train_model(train_df)
