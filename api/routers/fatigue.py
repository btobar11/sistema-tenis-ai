from fastapi import APIRouter, HTTPException
from metrics.fatigue import FatigueEngine

router = APIRouter(prefix="/fatigue", tags=["Fatigue Metrics"])
engine = FatigueEngine()

@router.get("/{player_id}")
def get_player_fatigue(player_id: str):
    """
    Get detailed fatigue breakdown for a player.
    Includes matches played, intensity metrics, and travel factor.
    """
    try:
        fatigue_data = engine.calculate_fatigue_index(player_id)
        
        if not fatigue_data:
            raise HTTPException(status_code=404, detail="Player not found or no data")
        
        return {
            "player_id": player_id,
            "fatigue": fatigue_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Fatigue API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/{player_a_id}/{player_b_id}")
def compare_fatigue(player_a_id: str, player_b_id: str):
    """
    Compare fatigue levels between two players.
    Useful for match analysis.
    """
    try:
        fatigue_a = engine.calculate_fatigue_index(player_a_id)
        fatigue_b = engine.calculate_fatigue_index(player_b_id)
        
        advantage = None
        diff = abs(fatigue_a['fatigue_index'] - fatigue_b['fatigue_index'])
        
        if diff > 0.15:  # Significant difference
            if fatigue_a['fatigue_index'] < fatigue_b['fatigue_index']:
                advantage = {"player": "a", "margin": round(diff, 2)}
            else:
                advantage = {"player": "b", "margin": round(diff, 2)}
        
        return {
            "player_a": {
                "id": player_a_id,
                "fatigue": fatigue_a
            },
            "player_b": {
                "id": player_b_id,
                "fatigue": fatigue_b
            },
            "freshness_advantage": advantage
        }
        
    except Exception as e:
        print(f"Fatigue Compare Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
