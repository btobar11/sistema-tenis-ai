class EnginePolicy:
    """
    Decides which engine to use based on input quality.
    """
    @staticmethod
    def evaluate(context):
        rank1 = context.get('rank_p1', 999)
        rank2 = context.get('rank_p2', 999)
        surface = context.get('surface', 'HARD').upper()
        
        # Logic: 
        # If any rank is > 500 or missing (999), ML might be poor (training data bias).
        # We can be stricter: if rank > 400?
        # For V1: Use 500.
        
        ranks_valid = (rank1 < 500) and (rank2 < 500)
        
        if ranks_valid:
            return {"engine": "ml", "reason": "optimized_quality"}
        else:
            return {"engine": "heuristic", "reason": "low_rank_fallback"}

class ConfidenceCalculator:
    """
    Calculates Trust Score (0.0 - 1.0)
    Form: DQ * SS * ET
    """
    def calculate(self, context, sim_stats, engine_used):
        # 1. Data Quality (DQ)
        has_elo = 1 if context.get('elo_p1') and context.get('elo_p2') else 0
        has_rank = 1 if context.get('rank_p1') < 999 and context.get('rank_p2') < 999 else 0
        has_surf = 1 if context.get('surface') else 0
        has_tourn = 1 if context.get('tournament') else 0 # Upcoming scraper has this
        
        dq = (0.4 * has_elo) + (0.3 * has_rank) + (0.2 * has_surf) + (0.1 * has_tourn)
        
        # 2. Simulation Stability (SS)
        # CV = std / mean
        mean_g = sim_stats['total_games'].get('mean', 22.0)
        std_g = sim_stats['total_games'].get('std', 3.0)
        
        if mean_g > 0:
            cv = std_g / mean_g
            # normalize: lower CV is better. 
            # typical tennis CV ~ 0.15 (3/22). High var > 0.3?
            # Let's map CV 0.0 -> 1.0, CV 0.3 -> 0.0
            ss = max(0.0, 1.0 - (cv / 0.3))
        else:
            ss = 0.5
            
        # 3. Engine Trust (ET)
        trust_map = {
            "XGBoost Service Regressor v1": 1.0,
            "Heuristic v2.1": 0.75,
            "heuristic": 0.75,
            "fallback": 0.65
        }
        et = trust_map.get(engine_used, 0.70)
        
        # Composite
        confidence = dq * ss * et
        
        # Detail Log
        details = {
            "dq": round(dq, 2),
            "ss": round(ss, 2),
            "et": round(et, 2),
            "cv": round(cv, 2)
        }
        
        return round(confidence, 2), details
