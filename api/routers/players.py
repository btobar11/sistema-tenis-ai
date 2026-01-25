from fastapi import APIRouter, HTTPException
from api.services.player_service import PlayerService

router = APIRouter(prefix="/players", tags=["Players"])
service = PlayerService()

@router.get("/{player_id}/elo-history")
def get_elo_history(player_id: str, surface: str = "OVERALL"):
    return service.get_player_elo_history(player_id, surface)
