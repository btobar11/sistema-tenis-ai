from .base import PredictionEngine
from metrics.elo import EloEngine

class HeuristicEngine(PredictionEngine):
    """
    Fallback Engine: Estimates P(Serve) from ELO.
    Formula: Avg Serve % + (ELO Diff * Factor)
    """
    
    def __init__(self, db_client):
        self.db = db_client
        self.elo_engine = EloEngine(db_client)
        
        # Calibration
        self.BASE_SERVE_PCT = 0.64 # ATP Average approx
        self.ELO_SCALE = 0.0004    # 100 points diff -> +4% serve win prob

    @property
    def name(self) -> str:
        return "Heuristic v2.1 (ELO-to-Serve)"

    def predict_params(self, match_data: dict):
        """
        Returns estimated (p_serve_p1, p_serve_p2) based on ELO.
        """
        p1 = match_data.get('player1_id')
        p2 = match_data.get('player2_id')
        surface = match_data.get('surface', 'HARD').upper()

        if not p1 or not p2:
            return 0.64, 0.64
            
        elo1 = self.elo_engine.get_player_elo(p1, surface)
        elo2 = self.elo_engine.get_player_elo(p2, surface)
        
        diff = elo1 - elo2
        
        # 3. Surface Adjustment
        # Clay: -0.02, Grass: +0.02, Indoor: +0.01
        p1_adj = 0.0
        p2_adj = 0.0
        
        if "CLAY" in surface:
            p1_adj = -0.02
            p2_adj = -0.02
        elif "GRASS" in surface:
            p1_adj = 0.02
            p2_adj = 0.02
        elif "INDOOR" in surface:
            p1_adj = 0.01
            p2_adj = 0.01

        # Estimate P1 Serve
        # Base + (Diff * Scale) + SurfaceAdj
        # User recommended scale: 0.02 per 100 pts -> 0.0002
        scale = 0.0002 # Updated from 0.0004
        
        p_serve_p1 = self.BASE_SERVE_PCT + (diff * scale) + p1_adj
        
        # Estimate P2 Serve
        p_serve_p2 = self.BASE_SERVE_PCT + (-diff * scale) + p2_adj
        
        # Clamp (0.52 to 0.75)
        p_serve_p1 = max(0.52, min(0.75, p_serve_p1))
        p_serve_p2 = max(0.52, min(0.75, p_serve_p2))
        
        return p_serve_p1, p_serve_p2
        
    def predict_proba(self, match_data: dict) -> float:
        # Not used in new sim architecture
        return 0.5
