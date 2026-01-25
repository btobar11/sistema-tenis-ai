from fastapi import APIRouter, HTTPException, Depends
from scrapers.db_client import get_db_client
from api.services.auth_service import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerts"])
db = get_db_client()

@router.get("/value")
def get_value_alerts(user_id: str = Depends(get_current_user)):
    # 1. Check Subscription
    # For MVP Demo, we allow "mock_user_id" to pass if we want, or fail.
    # To demonstrate Paywall, let's enforce it.
    
    # Lazy import to avoid circular dependency
    from api.services.stripe_service import stripe_service
    
    sub = stripe_service.get_user_subscription(user_id)
    if not sub['is_premium']:
        # Return limited or blurred data for Free users?
        # Strategy: Return 403 Payment Required to trigger Frontend "Upgrade Now" modal
        raise HTTPException(status_code=402, detail="Premium Subscription Required")

    # Return active alerts sorted by EV
    try:
        r = db.from_('value_alerts') \
            .select('*, match:matches(tournament, surface, player_a:player_a_id(name), player_b:player_b_id(name))') \
            .eq('status', 'active') \
            .order('ev_percentage', desc=True) \
            .limit(20) \
            .execute()
        return r.data
    except Exception as e:
        return []
