from fastapi import APIRouter, HTTPException, Depends
from scrapers.db_client import get_db_client
from api.services.auth_service import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/daily-edge", tags=["Daily Edge"])
db = get_db_client()

@router.get("/picks")
def get_daily_edge_picks(
    min_ev: float = 3.0,
    user_id: str = Depends(get_current_user)
):
    """
    Get today's value picks ordered by EV%.
    Premium users only.
    """
    # Lazy import to avoid circular dependency
    from api.services.stripe_service import stripe_service
    
    sub = stripe_service.get_user_subscription(user_id)
    if not sub['is_premium']:
        raise HTTPException(status_code=402, detail="Premium Subscription Required")

    try:
        # Fetch active value alerts with high EV
        r = db.client.from_('value_alerts') \
            .select('*, match:matches(id, tournament, surface, date, player_a:player_a_id(id, name, country), player_b:player_b_id(id, name, country))') \
            .eq('status', 'active') \
            .gte('ev_percentage', min_ev) \
            .order('ev_percentage', desc=True) \
            .limit(20) \
            .execute()
        
        picks = r.data or []
        
        # Format response for frontend
        formatted_picks = []
        for pick in picks:
            match_info = pick.get('match') or {}
            player_a = match_info.get('player_a') or {}
            player_b = match_info.get('player_b') or {}
            
            formatted_picks.append({
                "id": pick.get("id"),
                "selection": pick.get("selection"),
                "ev_percentage": pick.get("ev_percentage"),
                "kelly_stake": pick.get("kelly_stake"),
                "market_price": pick.get("market_price"),
                "model_probability": pick.get("model_probability"),
                "bookmaker": pick.get("bookmaker"),
                "player_home": pick.get("player_home"),
                "player_away": pick.get("player_away"),
                "match": {
                    "id": match_info.get("id"),
                    "tournament": match_info.get("tournament"),
                    "surface": match_info.get("surface"),
                    "date": match_info.get("date"),
                    "player_a_name": player_a.get("name"),
                    "player_a_country": player_a.get("country"),
                    "player_b_name": player_b.get("name"),
                    "player_b_country": player_b.get("country"),
                }
            })
        
        return {
            "picks": formatted_picks,
            "count": len(formatted_picks),
            "min_ev_filter": min_ev,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Daily Edge Error: {e}")
        return {"picks": [], "count": 0, "error": str(e)}


@router.get("/summary")
def get_daily_summary(user_id: str = Depends(get_current_user)):
    """
    Get summary statistics for today's edge opportunities.
    """
    from api.services.stripe_service import stripe_service
    
    sub = stripe_service.get_user_subscription(user_id)
    if not sub['is_premium']:
        raise HTTPException(status_code=402, detail="Premium Subscription Required")
    
    try:
        r = db.client.from_('value_alerts') \
            .select('ev_percentage, kelly_stake') \
            .eq('status', 'active') \
            .execute()
        
        alerts = r.data or []
        
        if not alerts:
            return {
                "total_opportunities": 0,
                "avg_ev": 0,
                "max_ev": 0,
                "high_confidence_count": 0
            }
        
        ev_values = [a['ev_percentage'] for a in alerts if a.get('ev_percentage')]
        kelly_values = [a['kelly_stake'] for a in alerts if a.get('kelly_stake')]
        
        return {
            "total_opportunities": len(alerts),
            "avg_ev": round(sum(ev_values) / len(ev_values), 2) if ev_values else 0,
            "max_ev": max(ev_values) if ev_values else 0,
            "high_confidence_count": len([k for k in kelly_values if k and k > 2.0])
        }
        
    except Exception as e:
        return {"error": str(e)}
