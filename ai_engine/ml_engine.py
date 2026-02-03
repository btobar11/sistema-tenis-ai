import os
import joblib
import pandas as pd
from .base import PredictionEngine

class XGBoostEngine(PredictionEngine):
    """
    ML Engine wrapping XGBoost model.
    Target: P(Serve Point Win) - Regressor.
    """
    
    def __init__(self, model_path="ml/models/xgb_service_v1.joblib"):
        self.model = None
        self.model_path = model_path
        self._load_model()
        
    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print(f"  [AI] Loaded XGBoost Regressor: {self.model_path}")
            except Exception as e:
                print(f"  [AI] Failed to load model: {e}")
        else:
            print(f"  [AI] Model not found at {self.model_path}")

    @property
    def name(self) -> str:
        return "XGBoost Service Regressor v1"

    def is_ready(self):
        return self.model is not None

    def predict_params(self, match_data: dict):
        """
        Returns (p_serve_p1, p_serve_p2)
        """
        if not self.model:
            raise RuntimeError("Model not loaded")

        # Extract features (Must match V1 Training: 'surface_code', 'rank_diff')
        # surface_code: 0=HARD, 1=CLAY, 2=GRASS
        surface = match_data.get('surface', 'HARD').upper()
        surf_code = 1 if 'CLAY' in surface else (2 if 'GRASS' in surface else 0)
        
        # Rank Diff: log2(OppRank) - log2(MyRank)
        r1 = match_data.get('rank_p1', 999)
        r2 = match_data.get('rank_p2', 999)
        
        # Safety for None
        if r1 is None: r1 = 999
        if r2 is None: r2 = 999
        
        import numpy as np
        def get_log_diff(my_r, opp_r):
            mr = max(1, min(1000, my_r))
            or_ = max(1, min(1000, opp_r))
            return np.log2(or_) - np.log2(mr)
            
        diff_p1 = get_log_diff(r1, r2)
        diff_p2 = get_log_diff(r2, r1)
        
        # Feature Matrix
        # P1 Perspective
        X_p1 = pd.DataFrame([{
            'surface_code': surf_code,
            'rank_diff': diff_p1
        }])
        
        # P2 Perspective
        X_p2 = pd.DataFrame([{
            'surface_code': surf_code,
            'rank_diff': diff_p2
        }])
        
        try:
            # Predict
            raw_p1 = self.model.predict(X_p1)[0]
            raw_p2 = self.model.predict(X_p2)[0]
            
            # Sanity Bounds (0.52 - 0.75)
            # ATP Average is ~0.64. Isner ~0.75. Schwartzman ~0.55.
            p_serve_p1 = max(0.52, min(0.75, float(raw_p1)))
            p_serve_p2 = max(0.52, min(0.75, float(raw_p2)))
            
            return p_serve_p1, p_serve_p2
            
        except Exception as e:
            print(f"  [AI] Prediction failed: {e}")
            raise e

    def predict_proba(self, match_data: dict) -> float:
        # This engine is designed to feed the Simulator, not output P(win) directly.
        # But if enforced by interface, we could return a proxy.
        # Ideally, InferenceService calls predict_params.
        pass
