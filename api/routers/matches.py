from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime
from api.services.match_service import MatchService

router = APIRouter(prefix="/matches", tags=["Matches"])
service = MatchService()

@router.get("/", summary="Get list of matches")
def get_matches(
    date: Optional[str] = Query(None, description="Specific date (YYYY-MM-DD)"),
    limit: int = 50
):
    """
    Fetch matches. If no date provided, defaults to today + future.
    """
    today = datetime.now().strftime('%Y-%m-%d')
    date_from = date if date else today
    
    # If date is specific, we might want end of day logic or just equality.
    # The service handles GTE date_from. 
    # If user asks for specific date, we might want strictly that day?
    # For now, let's keep simple: ?date= means GTE that date.
    
    matches = service.get_matches(date_from=date_from, limit=limit)
    return matches

@router.get("/{match_id}", summary="Get detailed match info")
def get_match_detail(match_id: str):
    match = service.get_match_details(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match
