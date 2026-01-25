from ai_engine.predict import StatsEngine # We can reuse the class or extract logic
from scrapers.db_client import get_db_client
from fastapi import HTTPException

# Refactor Predict to be usable here
# straightforward way: Instantiate StatsEngine and use predict_match
# But predict_match expects a 'match' dict with ID.
# We need `predict_hypothetical(p1, p2)`

class InferenceService:
    def __init__(self):
        self.db = get_db_client()
        self.engine = StatsEngine(self.db) # Reuse the existing engine logic

    def predict_matchup(self, p1_id: str, p2_id: str):
        # Construct a synthetic match object
        match_synth = {
            "player1_id": p1_id,
            "player2_id": p2_id,
            "id": "hypothetical",
            "date": None
        }
        
        # Call the existing engine logic
        # Note: StatsEngine might fail if it tries to fetch something expecting a real match ID
        # Let's verify `ai_engine/predict.py`.
        # It uses: get_h2h_stats(p1, p2) -> OK (DB access)
        # get_player_recent_form(p1) -> OK (DB access)
        # It needs model. 
        
        result = self.engine.predict_match(match_synth)
        
        # Enrich reasoning for frontend display if needed
        return result
