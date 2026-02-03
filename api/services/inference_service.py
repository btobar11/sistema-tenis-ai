from datetime import datetime
from ai_engine.ml_engine import XGBoostEngine
from ai_engine.heuristic import HeuristicEngine
from ai_engine.simulator import Simulator
from scrapers.db_client import get_db_client
from ai_engine.trust_model import EnginePolicy, ConfidenceCalculator

class InferenceService:
    def __init__(self):
        self.db = get_db_client()
        self.ml_engine = XGBoostEngine()
        self.heuristic_engine = HeuristicEngine(self.db)
        self.simulator = Simulator(num_simulations=5000)
        self.trust_model = ConfidenceCalculator()

    def predict_matchup(self, p1_id: str, p2_id: str, surface="HARD"):
        match_context = {
            "player1_id": p1_id,
            "player2_id": p2_id,
            "surface": surface,
            # Defaults for DQ calcs
            "rank_p1": 999, "rank_p2": 999,
            "elo_p1": 1500, "elo_p2": 1500
        }
        
        # Enrich with ELO and Rank
        try:
            res = self.db.from_('players').select('id, rank, elo_rating').in_('id', [p1_id, p2_id]).execute()
            if res.data:
                for p in res.data:
                    rk = p.get('rank')
                    elo = p.get('elo_rating')
                    
                    try:
                        rk = int(rk) if rk else 999
                    except:
                        rk = 999
                    
                    # Store
                    if p['id'] == p1_id:
                        match_context['rank_p1'] = rk
                        if elo: match_context['elo_p1'] = elo
                    elif p['id'] == p2_id:
                        match_context['rank_p2'] = rk
                        if elo: match_context['elo_p2'] = elo
        except Exception as e:
            print(f"[AI] Failed to fetch player stats: {e}")
        
        # 1. Engine Selection (Policy)
        policy = EnginePolicy.evaluate(match_context)
        target_engine = policy['engine']
        engine_reason = policy['reason']
        
        engine_used = "Unknown"
        p_serve_p1, p_serve_p2 = (0.64, 0.64)

        try:
            # Try Selected Engine
            if target_engine == 'ml' and self.ml_engine.is_ready():
                p_serve_p1, p_serve_p2 = self.ml_engine.predict_params(match_context)
                engine_used = self.ml_engine.name
            else:
                p_serve_p1, p_serve_p2 = self.heuristic_engine.predict_params(match_context)
                engine_used = self.heuristic_engine.name
                
        except Exception as e:
            print(f"[AI] Engine Error ({target_engine}): {e}. Fallback.")
            p_serve_p1, p_serve_p2 = self.heuristic_engine.predict_params(match_context)
            engine_used = self.heuristic_engine.name
            engine_reason = "error_fallback"

        # 2. Run Simulator
        markets = self.simulator.simulate_match(p_serve_p1, p_serve_p2, best_of=3)
        
        # 3. Trust Calculation
        trust_score, trust_details = self.trust_model.calculate(match_context, markets, engine_used)
        
        # 4. Format Output
        p_win = markets['p1_win_prob']
        predicted_winner = p1_id if p_win >= 0.5 else p2_id
        
        result = {
            "winner_id": predicted_winner,
            "confidence": trust_score, # Now using Trust Score!
            "raw_win_prob": round(p_win, 3), # Keep raw Prob
            
            "model_version": engine_used,
            "engine_reason": engine_reason,
            "trust_details": trust_details,
            
            "timestamp": datetime.now().isoformat(),
            "reasoning": f"Simulated {p_serve_p1:.2f} vs {p_serve_p2:.2f}. Trust: {trust_score*100:.0f}% ({engine_reason})",
            "metrics": {
                "p_serve_p1": round(p_serve_p1, 3),
                "p_serve_p2": round(p_serve_p2, 3),
                "simulated_p_win": round(p_win, 3)
            },
            "markets": markets
        }
        
        return result

    def _most_likely_score(self, sets_dist):
        return max(sets_dist, key=sets_dist.get)
